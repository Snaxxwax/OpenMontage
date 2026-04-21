# Asset Director — Explainer Pipeline

## When to Use

You are the Asset Producer for a generated explainer video. You have a `scene_plan` with required assets and a `script` with narration text. Your job is to generate every asset needed: narration audio, images, diagrams, code snippets, and background music. Every file must exist on disk before you finish.

This is where plans become real files. A missing or low-quality asset will torpedo the final video.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/asset_manifest.schema.json` | Artifact validation |
| Prior artifacts | `state.artifacts["scene_plan"]["scene_plan"]`, `state.artifacts["script"]["script"]`, `state.artifacts["proposal"]["proposal_packet"]` | What to produce |
| Playbook | Active style playbook | Image prompts, diagram style, audio preferences |
| Tools | `tts_selector`, `image_selector`, `video_selector`, `diagram_gen`, `code_snippet`, `music_gen` — selectors auto-discover all available providers from the registry | Generation capabilities |
| Cost tracker | `tools/cost_tracker.py` | Budget governance |

## Process

### Step 1: Inventory Required Assets

Walk every scene in the scene plan. For each `required_assets` entry, create an asset task:

```
Asset Task:
  scene_id: scene-3
  type: diagram
  description: "Mermaid flowchart: query -> encode -> search -> rank -> return"
  source: generate
  tool: diagram_gen
  estimated_cost: $0.00
```

Also create tasks for:
- **Narration audio** — one per script section (use `tts_selector` or a concrete TTS provider)
- **Background music** — one track for the whole video (use `music_gen` or select from library)
- **Sound effects** — per playbook's `sfx_style` (optional, use `music_gen` or stock)

### Step 2: Check Budget

Before generating anything:
1. Sum all estimated costs from the asset tasks
2. Compare against the cost tracker's remaining budget
3. If over budget:
  - Switch expensive tools to cheaper alternatives (use `tts_selector` with `preferred_provider` to route to cheaper TTS; use `image_selector` to route to cheaper image providers)
   - Reduce image count (combine similar scenes)
   - Skip optional assets (SFX, B-roll)
4. Get cost approval via cost tracker before proceeding

### Step 2b: Sample Preview (Prevents Wasted Spend)

Before batch-generating assets, produce one sample of each expensive asset type and present them to the user for approval:

1. **TTS sample**: Generate narration for the first script section only. Play it for the user. Confirm voice, pace, and tone are acceptable before generating the rest.
2. **Image sample**: Generate one image for the most representative scene. Show it to the user. Confirm the style, quality, and prompt approach before batch-generating all images.
3. **Music sample** (if using `music_gen`): Generate one short clip. Confirm mood and energy before committing.

If the user rejects a sample:
- Adjust the parameters (voice, prompt style, provider) and regenerate the sample.
- Do not batch-generate until the sample is approved.
- Max 3 sample iterations per asset type before escalating to the user for a decision.

This step typically costs $0.03–0.08 total and prevents $1–3 of wasted generation.

### Step 3: Generate Narration

Use **ElevenLabs TTS** as the default narration provider. It produces broadcast-quality results suitable for documentary and explainer content.

**Default voice selection by mood:**
| Mood / Genre | Voice | Voice ID |
|---|---|---|
| Documentary / Investigative / Noir | George — "Warm, Captivating Storyteller" | `JBFqnCBsd6RMkjVDRZzb` |
| Informational / Educational | Daniel — "Steady Broadcaster" | `onwK4e9ZLuTAKqWW03F9` |
| Corporate / Professional | Matilda — "Knowledgeable, Professional" | `XrExE9yKIg1WjnnlVkGX` |
| Social / Energetic | Liam — "Energetic, Social Media Creator" | `TX3LPaxmHKxFdv7VOQHJ` |

Use the `elevenlabs_tts` tool (or `curl` to `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`). On the free plan all premade voices are available.

For each script section:
1. Extract the narration text
2. Apply speaker directions from the script (pace, emphasis, emotion)
3. Apply `stability: 0.5, similarity_boost: 0.75, style: 0.3` for natural delivery with character
4. Generate with `model_id: "eleven_multilingual_v2"` for best quality
5. Save to `projects/<project>/assets/<chapter>/audio/s{N}.mp3`
6. Verify the file exists and duration matches expected timing (±15%)

**Pronunciation guide**: If the script contains technical terms, acronyms, or names (e.g. "Equifax", "FICO"), spell them phonetically in the text or use SSML `<phoneme>` tags.

**Free plan note**: 10,000 characters/month included. A 10-minute documentary chapter is ~800–1,200 characters of narration, well within limits.

### Step 3b: Extract Word Timestamps (mandatory post-TTS)

After generating ALL narration audio sections, run the `transcriber` tool on each narration file to extract word-level timestamps. This is required for the Edit Director to snap `visual_beats` to exact spoken words.

**Process:**

1. For each narration audio file in the asset manifest (subtype: "narration"):
   ```
   transcriber.execute({
     "input_path": "<narration_path>",
     "model_size": "base",
     "output_dir": "<project>/artifacts/"
   })
   ```

2. Convert from transcriber's native format `{ word, start (seconds), end (seconds) }` to Remotion's format `{ word, startMs (milliseconds), endMs (milliseconds) }`:
   - `startMs = round(word["start"] * 1000)` — must be integer; fractional ms causes one-frame sync errors
   - `endMs = round(word["end"] * 1000)`

3. Merge all sections' word lists in chronological order. If narration segments have `start_seconds` offsets (i.e., section 2 starts at 8s), add the section's narration `start_seconds` to each word's timestamps before merging. The result is a flat global list where `word_index=0` is the first word spoken in the video, `word_index=N` is the Nth word spoken across all sections.

4. Write merged list to `{project}/artifacts/word_timestamps.json`:
   ```json
   {
     "version": "1.0",
     "word_count": 847,
     "words": [
       { "word": "Your", "startMs": 0, "endMs": 250 },
       { "word": "database", "startMs": 260, "endMs": 580 },
       ...
     ]
   }
   ```

5. Add as supplementary artifact in the asset manifest:
   ```json
   {
     "id": "word-timestamps",
     "type": "data",
     "subtype": "word_timestamps",
     "path": "artifacts/word_timestamps.json",
     "source_tool": "transcriber",
     "cost_usd": 0.0
   }
   ```

**Validation:**
- [ ] `artifacts/word_timestamps.json` exists on disk
- [ ] `word_count` is plausible (roughly matches total narration word count ± 10%)
- [ ] `startMs` values are monotonically increasing across the merged list
- [ ] No word has `endMs - startMs > 2000` (2s/word is a transcription artifact — flag it)

**Critical gotcha — global vs. section-local indices:** The merged word list uses GLOBAL indices. `word_index=42` refers to the 42nd word across ALL sections combined, not the 42nd word in section 2. The Scene Director's `word_trigger.word_index` values reference this global list. Document this explicitly in your decision log.

### Step 4: Generate Visual Assets

Process asset tasks grouped by tool for efficiency:

**Images (`image_selector`)**:
1. Build the prompt from the scene's actual purpose:
   - scene-specific shot/lighting/texture cues from `shot_language`, `shot_intent`, and `texture_keywords`
   - an adapted visual anchor from the playbook or custom identity
   - the concrete subject/action/environment
   Use `lib/shot_prompt_builder.py` when helpful.
2. Add negative prompt from playbook
3. Include consistency anchors (same character/world/palette family), but do NOT reuse the exact same phrasing for every image
4. Generate and verify the file exists
5. If the result doesn't match expectations, refine the prompt and regenerate (max 2 retries)

**Diagrams (`diagram_gen`)**:
1. Convert the scene description into valid Mermaid syntax
2. Apply playbook's `asset_generation.diagram_style`
3. Generate SVG/PNG
4. Verify all nodes and edges are present

**Code snippets (`code_snippet`)**:
1. Extract language and code from the scene description
2. Apply syntax highlighting theme from playbook's overlay styles
3. Generate highlighted image or Remotion-compatible data

### Step 5: Generate Per-Scene Music Cues and Sound Effects

**Do NOT generate a single long background track for the whole video.** Music should be targeted and scene-specific. Generate short cues (10–45s) that match individual scene moments, and spot sound effects for punctuation.

#### 5a: Map scenes to audio needs

Walk the scene plan. For each scene, determine:
- Does it need a **music cue**? (tension swell, calm underscore, stinger, silence)
- Does it need **sound effects**? (typewriter click, paper rustle, door slam, ambient hum)
- What is the **emotional beat**? (revelation, dread, urgency, resolution)

Create an audio cue sheet:
```
sc01 (0-6s):   music_cue = "noir-intro-swell" (0-8s), sfx = "typewriter-click" at 1s, 2.3s
sc02 (6-14s):  music_cue = "tension-pulse" (6-16s), sfx = none
sc03 (14-20s): music_cue = none (silence for impact), sfx = "low-rumble" at 14s
...
```

#### 5b: Generate music cues with ACE-Step (local GPU) or ElevenLabs

**Preferred: ACE-Step** (free, local GPU, `tools/audio/acestep_music.py`)
- Generate 15–45s clips targeting specific scenes
- Set `duration` to scene length + 3s (for fade margins)
- Use focused prompts: `"5-second tense string swell, dramatic reveal, dark orchestral"` rather than generic moods

**Fallback: ElevenLabs Music API** if ACE-Step unavailable
- Use `POST https://api.elevenlabs.io/v1/sound-generation` for SFX
- Keep clips short (under 22s for music; ElevenLabs SFX is best for 0.5–10s)

**GPU discipline**: If ACE-Step is used, stop it after each clip. Run `nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader` to confirm VRAM freed before next GPU step.

Save each cue to `projects/<project>/assets/<chapter>/audio/music_<label>.mp3`

#### 5c: Generate sound effects with ElevenLabs

Use ElevenLabs SFX API for spot effects:
```
POST https://api.elevenlabs.io/v1/sound-generation
{
  "text": "single typewriter key click, mechanical, sharp",
  "duration_seconds": 0.5,
  "prompt_influence": 0.3
}
```

Save to `projects/<project>/assets/<chapter>/audio/sfx_<label>.mp3`

Common SFX for documentary/investigative:
- `"typewriter key click, crisp, single stroke"` — 0.3–0.5s
- `"paper rustling, document folder opening"` — 1–2s
- `"low ominous drone, building tension"` — 3–5s
- `"sharp news stinger, dramatic reveal"` — 1–2s
- `"ambient hum, server room, electronic"` — 5–10s (loop)

**Critical:** If music/SFX generation fails, log it in the asset manifest as `"music_status": "unavailable"` with the reason. Do NOT silently produce a video without audio — report it.

### Step 6: Build Asset Manifest

Assemble all generated assets into the manifest:

```json
{
  "version": "1.0",
  "assets": [
    {
      "id": "narration-s1",
      "type": "audio",
      "subtype": "narration",
      "path": "assets/narration/s1.mp3",
      "source_tool": "tts_selector",
      "scene_id": "scene-1",
      "duration_seconds": 8.2,
      "cost_usd": 0.003
    },
    {
      "id": "img-scene-3",
      "type": "image",
      "path": "assets/images/scene-3-diagram.png",
      "source_tool": "diagram_gen",
      "scene_id": "scene-3",
      "cost_usd": 0.00
    },
    {
      "id": "music-cue-intro",
      "type": "audio",
      "subtype": "music_cue",
      "path": "assets/audio/music_intro-swell.mp3",
      "source_tool": "acestep_music",
      "label": "intro-swell",
      "scene_id": "scene-1",
      "duration_seconds": 9.0,
      "cost_usd": 0.0
    },
    {
      "id": "sfx-typewriter",
      "type": "audio",
      "subtype": "sfx",
      "path": "assets/audio/sfx_typewriter-click.mp3",
      "source_tool": "elevenlabs_sfx",
      "label": "typewriter-click",
      "duration_seconds": 0.4,
      "cost_usd": 0.001
    }
  ],
  "total_cost_usd": 0.053,
  "generation_summary": {
    "narration_sections": 5,
    "images_generated": 8,
    "diagrams_generated": 2,
    "music_cues": 4,
    "sfx_clips": 6
  }
}
```

If video assets are present, add a `quality_gate` section that records fallback counts, fallback runtime ratio, consecutive fallback runs, thresholds used, and whether the manifest passes.

### Step 7: Verify All Assets

**Existence check:**
- [ ] Every asset `path` exists on disk
- [ ] Every narration section has a corresponding audio file
- [ ] Every scene with `required_assets` has all assets generated
- [ ] Background music file exists

**Quality check:**
- [ ] Narration durations within ±15% of expected timing
- [ ] Images match the playbook's style (review consistency anchors)
- [ ] Diagrams are legible and complete
- [ ] Total cost within budget
- [ ] Fallback runtime ratio stays within threshold
- [ ] No fallback run exceeds the consecutive-scene threshold

### Step 8: Self-Evaluate

Score (1-5):

| Criterion | Question |
|-----------|----------|
| **Completeness** | Does every scene have all required assets? |
| **Audio quality** | Does narration sound natural with correct pacing? |
| **Visual consistency** | Do all images look like they belong to the same video? |
| **Budget adherence** | Is total cost within the approved budget? |
| **Playbook fidelity** | Do assets match the playbook's style guide? |

If any dimension scores below 3, fix before proceeding.

### Step 9: Submit

Validate the asset_manifest against the schema and persist via checkpoint.
If the manifest includes video assets, it must also include a passing `quality_gate` block documenting fallback ratios and consecutive fallback runs.

### Mid-Production Fact Verification

If you encounter uncertainty during asset generation:
- Use `web_search` to verify visual accuracy of subjects (e.g. what does this building actually look like?)
- Use `web_search` to find reference images before generating illustrations
- Log verification in the decision log: `category="visual_accuracy_check"`

Visual accuracy matters. If the script mentions a specific place, person, or object,
verify what it actually looks like before generating images. Don't rely on
the AI model's training data — it may be wrong or outdated.

## Common Pitfalls

- **Generating before checking budget**: Always estimate total cost first. A 60-second video with 15 images can burn $3+ quickly.
- **Inconsistent image style**: Each image_selector call is independent. Use consistent anchors, but adapt them per scene. If you paste the same style prefix into every prompt, the video will feel machine-made and repetitive.
- **Ignoring narration timing**: If TTS produces 12s of audio for a 10s section, the edit phase will struggle. Check durations.
- **Missing pronunciation guide**: "PostgreSQL" or "Kubernetes" will be mispronounced without explicit guidance.
- **One retry then give up**: If an image doesn't match, refine the prompt specifically — don't just retry the same prompt.
- **AI-generating images with exact text (CTA, business names, contact info)**: AI image models frequently hallucinate wrong text — wrong business name, wrong phone number, misspelled words. **Never use AI image generation for scenes where text must be verbatim.** Use Remotion `text_card` type instead. This applies to: CTA screens, title cards with business names, contact info overlays, legal disclaimers. If a scene's `type` is `text_card` in the scene plan, do NOT generate an image for it — skip it and let the compose stage render it natively in Remotion.


## When You Do Not Know How

If you encounter a generation technique, provider behavior, or prompting pattern you are unsure about:

1. **Search the web** for current best practices — models and APIs change frequently, and the agent's training data may be stale
2. **Check `.agents/skills/`** for existing Layer 3 knowledge (provider-specific prompting guides, API patterns)
3. **If neither helps**, write a project-scoped skill at `projects/<project-name>/skills/<name>.md` documenting what you learned
4. **Reference source URLs** in the skill so the knowledge is traceable
5. **Log it** in the decision log: `category: "capability_extension"`, `subject: "learned technique: <name>"`

This is especially important for:
- **Video generation prompting** — models respond to specific vocabularies that change with each version
- **Image model parameters** — optimal settings for FLUX, DALL-E, Imagen differ and evolve
- **Audio provider quirks** — voice cloning, music generation, and TTS each have model-specific best practices
- **Remotion component patterns** — new composition techniques emerge as the framework evolves

Do not rely on stale knowledge. When in doubt, search first.
