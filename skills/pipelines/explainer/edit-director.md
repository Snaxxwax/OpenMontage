# Edit Director — Explainer Pipeline

## When to Use

You are the Editor for a generated explainer video. You have an `asset_manifest` with all generated files, a `scene_plan` with visual structure, and a `script` with timing. Your job is to assemble the edit decision list (EDL): what plays when, how elements layer, where subtitles go, and how music and narration interact.

This is where raw assets become a coherent video. Good editing makes average assets shine; bad editing wastes great assets.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/edit_decisions.schema.json` | Artifact validation |
| Prior artifacts | `state.artifacts["assets"]["asset_manifest"]`, `state.artifacts["scene_plan"]["scene_plan"]`, `state.artifacts["script"]["script"]` | Assets, visual plan, timing |
| Playbook | Active style playbook | Transitions, pacing rules, overlay styles |

## Process

### Step 1: Map Assets to Timeline

For each scene in the scene plan:
1. Find the matching assets from the asset manifest (by `scene_id`)
2. Find the matching narration audio (by script section)
3. Note the scene's timing (`start_seconds`, `end_seconds`)

Build a timeline map:
```
0s-10s: scene-1 (talking_head) | narration-s1 | img-intro.png
10s-18s: scene-2 (diagram) | narration-s2 | diagram-flow.svg
18s-22s: scene-3 (text_card) | narration-s3 | [text overlay]
...
```

### Step 2: Define Cuts

Each cut defines what visual is shown and when:

```json
{
  "id": "cut-1",
  "source": "img-scene-1",
  "in_seconds": 0,
  "out_seconds": 10,
  "layer": "primary",
  "transform": {
    "scale": 1.0,
    "position": "center",
    "animation": "ken-burns-slow-zoom"
  },
  "transition_in": "fade",
  "transition_out": "dissolve",
  "transition_duration": 0.4
}
```

**Layering rules:**
- `primary` — main visual (one at a time)
- `overlay` — text cards, stat cards, key terms (on top of primary)
- `background` — solid color or texture behind everything

### Step 2b: Word-Timestamp-Driven Beat Assembly

If `artifacts/word_timestamps.json` exists in the project, use it to resolve `visual_beats` from the scene plan into precise overlay timing.

**If `word_timestamps.json` is missing:** Log a warning and skip beat assembly — beats will be omitted from this render. Do not fail the stage.

**Process:**

1. Load `{project}/artifacts/word_timestamps.json`. Extract `words` array (format: `[{word, startMs, endMs}]`).

2. For each scene in the `scene_plan` that has `visual_beats[]`:
   - For each beat in `visual_beats[]`:
     - **If `word_trigger` is present:** resolve `start_seconds = words[word_trigger.word_index].startMs / 1000 + (word_trigger.offset_seconds || 0)`. Validate that `word_trigger.word_index` is within `[0, words.length - 1]` — if out of range, skip the beat and log a warning.
     - **If no `word_trigger`:** use `beat.start_seconds` directly from the scene plan.
     - `end_seconds = start_seconds + (beat.end_seconds - beat.start_seconds)` — preserve the beat's planned duration.

3. For each resolved beat, produce an overlay entry in `edit_decisions.overlays[]`:
   ```json
   {
     "asset_id": "beat-{beat.id}",
     "type": "{beat.micro_component_type}",
     "start_seconds": 22.47,
     "end_seconds": 24.97,
     "position": { "x": 0, "y": 0, "width": 1920, "height": 1080 },
     "word_trigger": { "word_index": 48, "offset_seconds": 0 },
     "micro_component_props": { "from": 0, "to": 73, "suffix": "%", "color": "#F59E0B" }
   }
   ```

4. Also set `continuous_camera: true` on cuts whose corresponding scene has `hero_moment: true` or whose duration exceeds 8 seconds. This instructs the Remotion compositor to wrap the cut in the `ContinuousCamera` component.

**Beat assembly validation checklist (add to Step 6):**
- [ ] Every `word_trigger.word_index` is within range of the `words` array
- [ ] No two beat overlays of the same type have overlapping `start_seconds`/`end_seconds`
- [ ] `data_counter` beats have `micro_component_props.to` defined and non-null
- [ ] `kinetic_highlight` beats have `micro_component_props.text` defined
- [ ] `connecting_line` beats have `x1`, `y1`, `x2`, `y2` all defined

**Overlay positioning rules — MANDATORY:**

The video is 1920×1080. Captions render at the bottom (y ≈ 920–1000). Overlays must not collide with captions or with each other.

**Caption safe zone**: Keep all overlay text within `y: 100` to `y: 820`. Never place overlay text below y=820 — it will overlap the caption strip.

**Simultaneous overlays must use distinct y positions.** If multiple overlays are active at the same time (staggered reveals, build-up lists), assign them to different vertical slots:

| Slot | y position | Use |
|------|-----------|-----|
| top | 180 | First item in a build-up sequence |
| mid-top | 350 | Second item |
| mid | 520 | Third item |
| mid-low | 650 | Fourth item (rare) |
| center | 440 | Solo emphasis overlay (nothing else active) |

**Staggered reveal pattern** (e.g., "EQUIFAX. / EXPERIAN. / TRANSUNION." appearing in sequence):
- Each word gets its own overlay entry
- Start times may overlap briefly (0.5–1s stagger) to create a "build-up" feel
- **Each must have a distinct `y` position** so they stack vertically instead of colliding
- Set `width` to the actual text width estimate (not full canvas): ~600–900px centered horizontally (`x: 510–660`)

**Full-canvas position `{x:0, y:0, width:1920, height:1080}`** is only valid for:
- Overlays with no text (pure SVG shapes/lines)
- `hero_title` type (intentionally fills the frame)

Do not use full-canvas position for any `kinetic_highlight` or `data_counter` with text — it defaults to center and causes stacking collisions when multiple overlays fire simultaneously.

**Critical: `word_index` is GLOBAL.** It is a position in the merged word list across ALL narration sections (produced by Asset Director Step 3b). It is NOT a per-section index. Off-by-one errors from treating section-local indices as global are the #1 failure mode in beat assembly.

### Step 3: Configure Subtitles

Subtitles are mandatory for all explainer content:

```json
{
  "subtitles": {
    "enabled": true,
    "style": "word-by-word",
    "font": "Inter",
    "font_size": 48,
    "color": "#FFFFFF",
    "background": "#00000088",
    "position": "bottom-center",
    "max_words_per_line": 8
  }
}
```

**Subtitle timing**: Derive from narration audio timestamps. Each word should highlight as it's spoken (word-by-word style) or display in phrase chunks (phrase style).

Use the playbook's typography for font choices.

### Step 4: Configure Audio Layers

Music should be **per-scene targeted cues**, not a single long background track. Map each music cue and SFX asset from the asset manifest to its timeline position.

```json
{
  "audio": {
    "narration": {
      "segments": [
        { "asset_id": "narration-s1", "start_seconds": 0 },
        { "asset_id": "narration-s2", "start_seconds": 10 }
      ]
    },
    "music_cues": [
      {
        "asset_id": "music-cue-intro",
        "start_seconds": 0,
        "end_seconds": 8,
        "volume": 0.28,
        "fade_in_seconds": 1.0,
        "fade_out_seconds": 1.5,
        "label": "intro-swell"
      },
      {
        "asset_id": "music-cue-tension",
        "start_seconds": 22,
        "end_seconds": 40,
        "volume": 0.18,
        "fade_in_seconds": 1.5,
        "fade_out_seconds": 2.0,
        "label": "tension-pulse"
      }
    ],
    "sfx": [
      { "asset_id": "sfx-typewriter", "start_seconds": 1.2, "volume": 0.7, "label": "typewriter-click" },
      { "asset_id": "sfx-paper", "start_seconds": 14.0, "volume": 0.5, "label": "paper-rustle" }
    ]
  }
}
```

**Volume guidance**:
- Music cues under narration: 0.15–0.25 (narration must always be intelligible)
- Music cues in silence/transition: 0.3–0.45
- SFX punctuation: 0.5–0.8
- SFX ambient beds: 0.2–0.35

**Do not** use a single long music track for the whole video. Silence between cues is intentional and creates rhythm — not every second needs music.

### Step 5: Apply Pacing Rules

Check the playbook's `motion.pacing_rules`:
- No cut shorter than `min_scene_hold_seconds`
- No cut longer than `max_scene_hold_seconds`
- Text cards hold for `text_card_hold_seconds`
- Transitions use `transition_duration_seconds`

Adjust cut timing if any violates these rules.

### Step 6: Verify Edit Completeness

**Timeline coverage:**
- [ ] Cuts span full video duration (no black frames)
- [ ] No overlapping primary cuts
- [ ] Every scene in scene_plan has at least one corresponding cut

**Asset references:**
- [ ] Every cut's `source` references a valid asset_id from the manifest
- [ ] Every narration segment references a valid audio asset
- [ ] Every `music_cues[].asset_id` references a valid asset in the manifest
- [ ] Every `sfx[].asset_id` references a valid asset in the manifest

**Audio sync:**
- [ ] Narration segments are ordered and non-overlapping
- [ ] Narration timing aligns with corresponding visual cuts
- [ ] Music cue `end_seconds > start_seconds` for every cue
- [ ] No two music cues overlap in time (they may butt-join but not overlap)

**Overlay positioning:**
- [ ] No two simultaneous overlays share the same `y` position
- [ ] No overlay text positioned below y=820 (caption safe zone)
- [ ] Full-canvas `{x:0,y:0,w:1920,h:1080}` only used for text-free SVG overlays or hero_title

**Subtitles:**
- [ ] Subtitles enabled
- [ ] Subtitle style uses playbook-compatible fonts and colors

### Step 7: Self-Evaluate

Score (1-5):

| Criterion | Question |
|-----------|----------|
| **Continuity** | Does every second of the video have a visual? |
| **Pacing** | Do cuts follow the playbook's timing rules? |
| **Audio-visual sync** | Does what you see match what you hear at every moment? |
| **Subtitle quality** | Are subtitles readable and correctly timed? |
| **Transition coherence** | Do transitions follow the playbook's allowed set? |

If any dimension scores below 3, revise.

### Step 8: Submit

Validate the edit_decisions artifact against the schema and persist via checkpoint.

## Common Pitfalls

- **Forgetting gaps**: If scene-1 ends at 10s and scene-2 starts at 10.5s, there's a 0.5s black frame. Check for gaps.
- **Audio drift**: Narration audio may be slightly longer/shorter than planned. Adjust visual cuts to match actual narration durations, not planned durations.
- **No ducking**: Music playing at full volume under narration makes the video unwatchable. Always configure ducking.
- **Same transition everywhere**: Varying transitions creates rhythm. Use the playbook's allowed set, but don't use the same one for every cut.
- **Subtitle font mismatch**: Subtitles should use the playbook's body font, not a random default.
