# Scene Director - Animation Pipeline

## When To Use

You are converting the script into a feasible animation plan. This is the stage that decides whether the project feels designed or chaotic.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/scene_plan.schema.json` | Artifact validation |
| Prior artifacts | `state.artifacts["script"]["script"]`, `state.artifacts["proposal"]["proposal_packet"]` | Beat map and tool path |
| Playbook | Active style playbook | Palette, typography, motion consistency |

## Process

### 1. Make An Animatic-Minded Plan

For each scene, define:

- what appears first,
- what changes,
- what is held,
- how the scene exits.

**Duration gate (required):**
- If `proposal_packet.selected_concept.target_duration_seconds` is set (longform default), the **scene_plan total duration** must match within **±10–15%**.
- The scene plan must not silently compress a 13-minute (780s) project into a 5-minute (300s) plan.
- If a shorter pilot is intended, the proposal/project_config must explicitly set a shorter `target_duration_seconds` (e.g. ~300s).

### 1b. Asymmetric Mode (Device-Driven, Kinetic, Source-Aware)

When `style_playbook == "asymmetric"`, plan scenes as **devices + state changes**, not slides.

**Retention-motion layer (required fields on every scene):**
- `viewer_hook`: the active viewer question driving the scene.
- `tension_type`: why it feels unresolved (mystery/contradiction/escalation/bottleneck/consequence/etc.).
- `visual_event_cadence_seconds`: target cadence for meaningful visual events (default **5–8s**).
- `retention_function`: why the viewer keeps watching (open loop / proof / mechanism / consequence / payoff / synthesis).
- `payoff_moment`: the in-scene beat that resolves or flips the tension.
- `next_open_loop`: the unresolved next question you hand off to the next scene.

Mini-arc rule (per section): **question → mechanism → consequence → payoff**. If a section spans multiple scenes, the arc must be visible across them and the open loop must be explicit.

**Device references (required for major scenes):**
- Each major scene should include `devices: [...]` referencing one or more device IDs from `channel_assets/asymmetric/diagrams/devices/manifest.json`.
- Recognized device IDs:
  - `amber-pivot-marker`, `chokepoint-ring`, `route-trace`, `collapse-to-one-node`
  - `surface-vs-structure-split`, `xray-layer-reveal`, `blueprint-reveal`, `under-the-hood-mechanism`
  - `red-consequence-layer`, `source-card-reveal`, `final-leverage-map`, `dependency-tree-stop-point`

**State-change enforcement:**
- Add `state_changes` with timeline beats (seconds from scene start).
- Hard rule: **no unchanged visual state longer than 4 seconds**.
- Preferred: meaningful state change every **2–4 seconds**.
- Every 5–8 seconds requires a meaningful visual event (reveal/collapse/route trace/node highlight/contradiction/source proof/map zoom/consequence hit/comparison slam/final synthesis).
- Each diagram must change **visible state** at least every 4 seconds (not just swapping text/cards).
- Text-card sequences must include state changes or be split.
- Stat cards must animate as **evidence**, not slide bullets.
- Every major claim needs a **visual mechanism**, not just text.

**Asymmetric episode coverage (minimum):**
- One system map (`route-trace` or `dependency-tree-stop-point`)
- One chokepoint reveal (`amber-pivot-marker` or `chokepoint-ring`)
- One surface-vs-structure reveal (`surface-vs-structure-split` or `xray-layer-reveal`)
- One source/evidence moment (`source-card-reveal`)
- One final leverage map (`final-leverage-map`)

**SVG/CSS fallback planning (required):**
- Any generated-image dependency in `required_assets` must include a fallback plan:
  - `fallback_type` (`svg_css` | `hyperframes_native` | `generated_image` | `stock` | `none`)
  - `fallback_path` when `fallback_required: true`
- Prefer `svg_css` / `hyperframes_native` when brand-compatible; do not block on ComfyUI.

**Evidence/stat-card requirements:**
- Hard stat cards must carry `source_claim_ids` referencing `source_map` claim IDs.
- Every stat card must be framed as proof of a claim or contradiction (never decorative).
- Analyst/media estimates must set `qualifier_required: true` and include on-screen qualifiers.
- Low-confidence claims should not be planned as hard stat cards (use qualifiers or convert to mechanism/explanation).
- Use `evidence_device_id: "source-card-reveal"` for major non-obvious claims.

**Color semantics (non-negotiable):**
- Amber = leverage/chokepoint/control point only (not decorative).
- Cyan = structure/flow/system map only.
- Red = consequence/failure/exposure only (not decorative).

**Human-host and tone defaults:**
- Default to **no recurring human host**.
- Interface-driven, diagram-native visuals.
- Use abstract silhouettes only when necessary.
- Avoid cyberpunk / spy / control-room fantasy; avoid life-hack/gamer-meta framing.

### 2. Limit Transition Families

Choose a small set of transition meanings:

- cut,
- fade,
- slide,
- transform.

### 3. Match Scene Type To Tool Path

Use:

- `diagram` scenes for structured explanation,
- `animation` scenes for motion-first sequences,
- `text_card` for clean high-impact copy moments,
- `generated` only where needed.

**For `image_animation` approach (anime/illustration style):**

Use `anime_scene` type for each scene. Plan:

- **Images per scene**: 2-3 images built from the same visual system and nearby seeds for crossfade effect
- **Camera motion**: choose from `zoom-in`, `zoom-out`, `pan-left`, `pan-right`, `ken-burns`, `drift-up`, `drift-down`, `parallax`, `static` — vary per scene to prevent monotony
- **Particle type**: choose from `fireflies`, `petals`, `sparkles`, `mist`, `light-rays` — match to scene mood
- **Lighting**: optional `lightingFrom`/`lightingTo` gradient for atmospheric shifts within the scene
- **Vignette**: `true` for cinematic framing (default), `false` for bright/open scenes
- **Scene duration**: 4-7 seconds per scene. Longer scenes need more images for crossfade variety.

**Scene variety rules for image_animation:**
- Don't use the same camera motion for consecutive scenes
- Alternate between warm and cool particle types
- Mix close-up and wide establishing shots
- Use overlays (`hero_title`, `section_title`) to add narrative structure

**JSON prop name mapping** (use these exact field names in the composition JSON):

| Concept | JSON Field | Example Values |
|---------|-----------|----------------|
| Camera motion | `animation` | `"zoom-in"`, `"pan-right"`, `"ken-burns"` |
| Particle effect | `particles` | `"fireflies"`, `"sparkles"`, `"mist"` |
| Particle color | `particleColor` | `"#FFE082"` |
| Particle density | `particleCount` | `20` (range: 1-50) |
| Particle brightness | `particleIntensity` | `0.5` (range: 0-1) |
| Lighting start | `lightingFrom` | `"rgba(255,200,100,0.15)"` or `"transparent"` |
| Lighting end | `lightingTo` | `"rgba(255,107,157,0.08)"` or `"transparent"` |
| Cinematic edge darken | `vignette` | `true` / `false` |
| Scene background | `backgroundColor` | theme-derived value such as `"#0A0A1A"` or `"#F6F1E8"` |

Reference: `remotion-composer/public/demo-props/mori-no-seishin.json` — 6 scenes using this pattern.
Reference: `remotion-composer/public/demo-props/deep-ocean.json` — 6 underwater scenes with different palette.

### 4. Use Metadata For Timing Rules

Recommended metadata keys:

- `animatic_rules`
- `transition_rules`
- `hold_rules`
- `tool_path_map`
- `reusable_motifs`

### 5. Quality Gate

- every scene has a clear timing intent,
- the transition system is limited and meaningful,
- the tool path is explicit,
- the sequence feels like one designed system.

## Common Pitfalls

- Adding a new transition idea in every scene.
- Planning scenes that have no realistic production path.
- Overanimating text-heavy scenes.
