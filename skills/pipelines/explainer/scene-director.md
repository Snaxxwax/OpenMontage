# Scene Director — Explainer Pipeline

## When to Use

You are the Scene Planner for a generated explainer video. You have a `script` artifact with timestamped sections and enhancement cues. Your job is to transform the script into a visual plan: what the viewer sees at every moment, what assets need to be created, and how scenes transition.

This is where words become visuals. A great script with a bad scene plan produces a confusing video.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/scene_plan.schema.json` | Artifact validation |
| Prior artifacts | `state.artifacts["script"]["script"]`, `state.artifacts["proposal"]["proposal_packet"]` | Script sections and proposal packet |
| Playbook | Active style playbook | Visual language, transitions, motion rules |
| Layer 3 | `.agents/skills/flux-best-practices/`, `.agents/skills/beautiful-mermaid/`, `.agents/skills/manim-composer/` | Image gen, diagram, animation knowledge |

## Asymmetric Mode (Style Playbook = `asymmetric`)

When `style_playbook == "asymmetric"`, scene plans must be **device-driven**, **kinetic (state beats)**, and **source-aware**.

### Retention-Motion Layer (Required)

Plan scenes around **retention beats**, not calm information delivery.

Every scene MUST include the following fields (see `schemas/artifacts/scene_plan.schema.json`):
- `viewer_hook`: What the viewer is *currently* trying to resolve (their active question / suspicion).
- `tension_type`: Why it feels unresolved (mystery / contradiction / escalation / bottleneck / consequence / etc.).
- `visual_event_cadence_seconds`: Target cadence for meaningful visual events (default **5–8s**).
- `retention_function`: The emotional/narrative job the scene does (opens a loop, proves a claim, reveals mechanism, hits consequence, sets payoff, etc.).
- `payoff_moment`: The specific moment/beat that “pays” the loop inside the scene.
- `next_open_loop`: The next unresolved question you intentionally hand off to the following scene.

Mini-arc rule (per section): **question → mechanism → consequence → payoff**. If a script section needs multiple scenes, they should collectively form this arc and explicitly carry the open loop forward.

**Device-driven planning (major scenes):**
- Add `devices: [...]` referencing device IDs from `channel_assets/asymmetric/diagrams/devices/manifest.json`.
- Recognized device IDs:
  - `amber-pivot-marker`, `chokepoint-ring`, `route-trace`, `collapse-to-one-node`
  - `surface-vs-structure-split`, `xray-layer-reveal`, `blueprint-reveal`, `under-the-hood-mechanism`
  - `red-consequence-layer`, `source-card-reveal`, `final-leverage-map`, `dependency-tree-stop-point`

**State-change requirements:**
- Include `state_changes` beats (seconds from scene start) so later validation can enforce motion cadence.
- Hard rule: no unchanged visual state longer than **4 seconds**; preferred meaningful change every **2–4 seconds**.
- Every major visual must create **motion, tension, reveal, or consequence** — avoid “static chart/deck energy”.
- Diagrams must change **visible state** at least every 4 seconds (not just swapping text).
- A “visual event” means: reveal, collapse, route trace, node highlight, contradiction, source proof, map zoom, consequence hit, comparison slam, or final synthesis.
- Text-card sequences must include motion/state changes or be split.
- Stat cards must animate as evidence (not bullet slides).
- Every major claim must have a visual mechanism, not just text.

**Required episode coverage (minimum):**
- System map (`route-trace` or `dependency-tree-stop-point`)
- Chokepoint reveal (`amber-pivot-marker` or `chokepoint-ring`)
- Surface-vs-structure reveal (`surface-vs-structure-split` or `xray-layer-reveal`)
- Source/evidence moment (`source-card-reveal`)
- Final leverage map (`final-leverage-map`)

**SVG/CSS fallback planning (generated imagery must not block production):**
- Any `required_assets[]` entry with `source: "generate"` should include fallback planning:
  - `fallback_type` (`svg_css` | `hyperframes_native` | `generated_image` | `stock` | `none`)
  - set `fallback_required: true` and `fallback_path` when the visual is mission-critical
- Prefer `svg_css` / `hyperframes_native` when brand-compatible; stock-photo documentary is not the default.

**Evidence/stat-card planning:**
- Hard stat cards must include `source_claim_ids` (claim IDs from `source_map`).
- Every stat card must be introduced as **proof of a claim or contradiction** (never “here are some numbers”).
- Analyst/media estimates must set `qualifier_required: true` and include on-screen qualifiers.
- Low-confidence claims cannot be planned as hard stat cards.
- For major non-obvious claims, plan a `source-card-reveal` (set `evidence_device_id: "source-card-reveal"`).

**Color semantics (non-negotiable):**
- Amber = leverage/chokepoint/control point only (not decorative).
- Cyan = structure/flow/system map only.
- Red = consequence/failure/exposure only (not decorative).

**Human-host and tone defaults:**
- Default to no recurring human host; interface-driven visuals; abstract silhouettes only if needed.
- Avoid cyberpunk / spy / control-room fantasy; avoid life-hack/gamer-meta public language.

## Process

### Step 1: Analyze the Script

Read every section. For each, note:
- What concept is being explained?
- What enhancement cues did the script writer embed?
- What's the emotional beat? (curiosity, revelation, emphasis, humor, conclusion)
- How much time is available? (end_seconds - start_seconds)

### Step 2: Research Visual Approaches

**Use web search** to find visual techniques for this topic:

1. **How do top creators visualize this?** Search YouTube thumbnails, blog diagrams, conference slides for the topic.
2. **What visual metaphors work?** Some concepts have well-known visual representations (e.g., neural networks as node graphs, encryption as locks/keys). Use these — viewers recognize them instantly.
3. **What's novel?** Is there a visual approach nobody has tried? A fresh visualization can make an explainer memorable.
4. **What's feasible?** Match your ambitions to available tools: `image_selector` (static images), `diagram_gen` (Mermaid flowcharts/sequences), `code_snippet` (syntax-highlighted code), Remotion (motion graphics, text animations), Manim (mathematical animations).

If you encounter a visualization need that no existing skill covers, use the **Skill Creator** (`skills/meta/skill-creator.md`) to create a new skill.

### Step 3: Decompose into Scenes

Transform each script section into 1-3 visual scenes. Each scene is a distinct visual moment.

```json
{
  "id": "scene-3",
  "type": "diagram",
  "description": "Mermaid flowchart showing query → encode → vector search → rank → return results. Nodes appear one by one as narrator describes each step.",
  "start_seconds": 15,
  "end_seconds": 22,
  "script_section_id": "s3",
  "framing": "full-screen diagram, centered",
  "movement": "progressive reveal left-to-right",
  "transition_in": "fade",
  "transition_out": "dissolve",
  "overlay_notes": "Label each node as it appears",
  "required_assets": [
    {
      "type": "diagram",
      "description": "Mermaid flowchart: query → encode embedding → vector search (ANN) → rank by cosine similarity → return top-k results",
      "source": "generate"
    }
  ]
}
```

#### Scene Types and When to Use Them

| Type | Best For | Available Tools | Duration Guidance |
|------|----------|-----------------|-------------------|
| `hero_title` | Opening titles, dramatic reveals | Remotion HeroTitle (theme-driven title treatment) | 3-5s |
| `stat_card` | Big dramatic numbers, impactful metrics | Remotion StatCard (large stat + subtitle) | 4-6s |
| `bar_chart` | Category comparisons, rankings | Remotion BarChart (animated grow-up/slide-in/pop) | 5-7s |
| `line_chart` | Trends, time series, growth curves | Remotion LineChart (draw/fade animation, multi-series) | 5-7s |
| `pie_chart` | Proportions, breakdowns, distributions | Remotion PieChart (donut mode, center label, spin/expand) | 5-7s |
| `kpi_grid` | Dashboards, traction metrics, at-a-glance data | Remotion KPIGrid (2-4 columns, count-up/pop/cascade) | 5-7s |
| `comparison` | Before/after, A/B, versus comparisons | Remotion ComparisonCard (dual-value with divider) | 4-6s |
| `callout` | Expert quotes, tips, warnings, important notes | Remotion CalloutBox (info/warning/tip/quote types) | 4-6s |
| `progress_bar` | Journey visualization, completion, stacked metrics | Remotion ProgressBar (fill/pulse/step animations) | 4-6s |
| `text_card` | Statements, closing messages, key terms | Remotion TextCard (centered, spring animation) | 3-5s |
| `animation` | Concepts needing motion (data flow, math) | Remotion, Manim | 4-10s |
| `diagram` | Processes, architecture, relationships | `diagram_gen` (Mermaid), `image_selector` | 4-8s |
| `generated` | Illustrations, metaphors, real-world imagery | `image_selector` (FLUX/DALL-E) | 3-6s |
| `talking_head` | AI avatar speaking (if HeyGen available) | HeyGen tools | 5-15s |
| `broll` | Context, real-world examples | Stock or generated footage | 3-6s |
| `screen_recording` | Code demos, UI walkthroughs | Recorded or simulated | 5-15s |

**Zero-key scene selection:** When no image/video generation is available, prefer `hero_title`, `stat_card`, `bar_chart`, `line_chart`, `pie_chart`, `kpi_grid`, `comparison`, `callout`, `progress_bar`, and `text_card`. These render entirely from Remotion components with zero external dependencies and can still feel distinct if you derive color, typography, and pacing from the subject instead of defaulting to a generic dashboard aesthetic.

### Step 4: Apply the Visual Technique Library

These are proven patterns for explainer visuals. Reference them by name in scene descriptions:

**Diagram Reveal**
Build a diagram progressively — start empty, add components with labels as the narrator describes each part. Perfect for architecture, processes, and systems.
- Tools: Mermaid + Remotion animation or FLUX-generated diagram
- Example: "Show the vector database architecture. Add the encoder node when narrator says 'embeddings'. Add the index when narrator says 'search'."

**Analogy Visualization**
Show the abstract concept alongside its real-world analogy. Split screen or side-by-side.
- Tools: `image_selector` for both sides
- Example: "Left: actual vector space with dots. Right: a library with books sorted by topic."

**Stat Card Punch**
Full-screen number with impact animation (scale up, slight bounce). Use `stat_card` type with a background and accent treatment chosen for the video's identity. Hold for 4-5 seconds.
- Tools: Remotion StatCard component
- Example: stat="1ms", subtitle="vs 500ms with traditional search", accentColor="<theme_accent>"

**Data Dashboard Sequence**
A series of data visualization scenes that tell a story through numbers. Start with a KPI overview, then drill into specific charts. Use section_title overlays to group related data. This pattern works with zero external tools.
- Tools: Remotion chart components (bar_chart, line_chart, pie_chart, kpi_grid)
- Example: kpi_grid (4 key stats) → bar_chart (breakdown) → line_chart (trend) → pie_chart (distribution)
- Choose the background treatment from the visual identity: dark for dramatic/technical subjects, light for approachable/educational, textured or warm when the topic calls for it.

**Before/After Split**
Show the problem, then the solution using `comparison` type. The comparison card shows dual values side-by-side with animated entrance.
- Tools: Remotion ComparisonCard component
- Example: leftLabel="Before", leftValue="500ms", rightLabel="After", rightValue="1ms"

**Timeline Progression**
Left-to-right or top-to-bottom sequence showing evolution or process steps. Each step appears as narrator describes it.
- Tools: Remotion with animated elements or Mermaid timeline
- Example: "1990: keyword search → 2010: semantic search → 2020: vector databases → 2024: multimodal search"

**Zoom and Focus**
Start with a wide view of a system, then zoom into a specific component to explain it in detail. Creates spatial context.
- Tools: Remotion with scale animation on a generated image
- Example: "Show full system architecture. Zoom into the 'embedding model' component."

**Code Walkthrough**
Show code with syntax highlighting. Highlight specific lines as the narrator explains them. Can animate typing or progressive reveal.
- Tools: `code_snippet` tool + Remotion
- Example: "Python code: `results = collection.query(embedding, n_results=5)`. Highlight `embedding` parameter when narrator says 'vector'."

### Step 4b: Write Narration with Duration Budget

If the video includes narration, the script **must** be written to fit the video duration.

**Duration budgeting formula:**
1. Calculate total video duration from scene timings (last cut's `out_seconds`).
2. Target narration at **85-90%** of video duration to leave breathing room at intro/outro.
3. Budget words: **2.0-2.5 words/second** for documentary style with natural pauses; **2.5-3.0 words/second** for energetic/fast-paced delivery.
4. Example: 53s video → target 45-48s of narration → 90-120 words max (documentary) or 112-144 words (energetic).

**Per-scene word budgets:**
- Allocate words proportionally to each scene's duration.
- A 5s scene gets ~10-12 words. A 6s scene gets ~12-15 words.
- Leave 0.5-1s of silence between scene transitions for visual breathing room.

**Validation (mandatory before TTS generation):**
- [ ] Total word count is within budget for the target duration
- [ ] No single scene's narration exceeds its time slot
- [ ] Opening and closing scenes have brief narration (let visuals breathe)

**After TTS generation:**
- The TTS tool returns `audio_duration_seconds` — compare it against video duration.
- If narration exceeds video by >1s, either trim the script and regenerate, or extend the video's closing scene.
- Always run `composition_validator` before rendering to catch mismatches automatically.

### Step 5: Validate Against Playbook

The style playbook constrains your visual choices:

| Playbook Field | Scene Impact |
|----------------|-------------|
| `visual_language.color_palette` | All generated images and diagrams must use these colors |
| `visual_language.composition` | Framing rules (rule-of-thirds, centered, etc.) |
| `motion.transitions` | Allowed transition types (e.g., `gentle-fade`, `soft-dissolve`) |
| `motion.animation_style` | Animation feel (e.g., `ease-in-out, organic curves`) |
| `motion.pacing_rules` | Minimum hold times (e.g., "hold establishing shots for 2s minimum") |
| `asset_generation.image_prompt_prefix` | Distill into a short visual anchor; do not paste verbatim into all prompts |
| `asset_generation.consistency_anchors` | What must stay consistent across all images (color palette, lighting, style) |

**Checklist before submitting:**
- [ ] Every scene uses playbook-compatible transitions
- [ ] All required_asset descriptions include style cues from the playbook
- [ ] No scene violates pacing rules (min/max duration)
- [ ] Image descriptions reference the video's actual visual identity, not just a preset name

### Step 6: Verify Coverage and Variety

**Coverage check:**
- [ ] Scenes span the full script duration (first scene starts at 0s, last scene ends at total_duration)
- [ ] Every script section has at least one corresponding scene
- [ ] No gaps > 1s between scenes (unless intentional beat)
- [ ] All enhancement cues from the script are addressed by a scene or required_asset

**Variety check:**
- [ ] No more than 3 consecutive scenes of the same type
- [ ] At least 3 different scene types used in the video
- [ ] Visual pacing alternates between high-information scenes (diagrams, animations) and breathing room (text cards, generated images)

**Feasibility check:**
- [ ] Every `required_asset` with `source: "generate"` is achievable with available tools
- [ ] Diagram descriptions are specific enough for Mermaid syntax generation
- [ ] Image descriptions are specific enough for FLUX/DALL-E prompt engineering
- [ ] No scene requires tools that aren't in the tool registry

### Step 7: Self-Evaluate

Score (1-5):

| Criterion | Question |
|-----------|----------|
| **Visual storytelling** | Does each scene advance understanding, not just decorate? |
| **Script alignment** | Does every scene match what the narrator is saying at that moment? |
| **Technique variety** | Did you use multiple visual techniques, not just one? |
| **Playbook fidelity** | Would every scene look like it belongs to the same video? |
| **Asset feasibility** | Can every required_asset actually be generated with available tools? |
| **Pacing** | Does the visual rhythm feel natural? High-info scenes balanced with breathing room? |

If any dimension scores below 3, revise.

### Step 8: Submit

Call `handle_explainer_scene_plan(state, {"scene_plan": scene_plan_json})` to validate and persist.

## Common Pitfalls

- **One scene per section**: Script sections often cover multiple concepts. A 10-second section might need 2-3 visual scenes to avoid boring stasis.
- **Ignoring enhancement cues**: The script writer embedded visual hints in `enhancement_cues`. Don't ignore them — they represent the writer's visual intent.
- **Overly ambitious animations**: "Photorealistic 3D fly-through of a data center" can't be generated with current tools. Keep it achievable.
- **No transition strategy**: Random transitions feel chaotic. Use the playbook's transition rules consistently. Reserve special transitions for topic shifts.
- **Vague required_assets**: "An image about databases" is useless for prompt engineering. "Isometric illustration of a vector database with embedding vectors floating in 3D space, using the playbook's blue-green palette" is actionable.
- **Preset thinking**: A scene plan that says "make it flat-motion-graphics" is not enough. The planner must specify what makes THIS video's motion graphics feel distinct.
- **Static scenes for dynamic concepts**: If the narrator describes a process or transformation, the visual should move. Use animation or progressive reveal, not a static image.
- **Using `generated` type for CTA/closing screens with exact text**: AI image models hallucinate text — wrong business names, misspelled words, wrong phone numbers. Any scene with verbatim text (CTA, business info, contact details, legal) MUST be `type: "text_card"` so Remotion renders the text exactly. Never plan a `generated` image for a scene where text accuracy matters.
