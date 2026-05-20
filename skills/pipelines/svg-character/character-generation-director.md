# Character Generation Director

You are running the `character_generation` stage of the `svg-character` pipeline.
This stage replaces the two-stage `character_design → rig_plan` sequence with a
single coherent pass: you generate the SVG, rig manifest, and pose library yourself,
then validate and persist them with `SvgCharacterWriter`.

## Step 0 — Read Layer 3 skills first

Before generating anything, read these two skills:

1. `.agents/skills/hyperframes/SKILL.md` — for HyperFrames SVG animation conventions
2. The `svg-character-animation` and `character-rigging` skills referenced in
   `SvgCharacterWriter.agent_skills`

These contain the SVG structure requirements, part naming conventions, and pivot
point guidance you need. Do not skip this step.

## Step 1 — Check the character library

Call `CharacterLibrary` with `action=list`.

If any character matches the brief (similar style, role, or description), present
the user with three options:

> "I found a saved character — **[Name]** — that matches this brief.
> A) Reuse it as-is  B) Load it as a starting reference  C) Generate a new character"

- **A (reuse):** load the saved character bundle, skip to Step 5.
- **B (reference):** load the SVG and note the style, then proceed with generation
  using the existing character as a visual reference.
- **C (new):** proceed directly.

## Step 2 — Generate the SVG character

Using the approved concept from `proposal_packet` and the character role from
`script`, generate a complete SVG character inline.

### Required SVG structure

The SVG **must** use `viewBox="0 0 512 512"` and include a `<style>` block with
idle CSS animations. Every anatomical group **must** have an `id` attribute that
exactly matches a part in the rig manifest you will generate in Step 3.

**Mandatory `<g>` IDs (always present):**
- `body` — torso, shoulders, background attire. `transform-origin: bottom center`
- `head` — skull, hair, face shape. `transform-origin: bottom center`
- `eyes-open` — primary visible eyes
- `eyes-closed` — hidden by default (`style="display:none"`)
- `mouth-neutral` — resting mouth
- `mouth-open` — talking mouth, hidden by default (`style="display:none"`)

**Additional IDs as needed by the character type** (include in rig manifest):
- `arm-left`, `arm-right` — for humanoid characters
- `leg-left`, `leg-right` — if legs are visible and animated
- `tail`, `ears`, `hat`, `prop` — for non-humanoid features

**CSS animations to include:**
- Idle sway on `#body` and `#head`: subtle rotation ±2–4°, 3–5s `ease-in-out infinite`
- Blink on `#eyes-open`/`#eyes-closed`: `@keyframes blink` that toggles visibility
  every 3–5s for ~0.15s
- All animations use `transform-origin: bottom center` on body/head groups

**Style guidance** (from the approved concept):
- Flat Vector: bold solid fills, geometric shapes, clean paths
- Hand-Drawn: organic paths, irregular strokes, slightly imperfect geometry
- Cyberpunk: neon fills, glow effects via `<filter>`, high-contrast outlines

**Do not use:**
- `Math.random()` or dynamic JS in the SVG
- External image references
- Fonts that require loading

## Step 3 — Generate the rig manifest

Generate a VectorForge-style rig manifest. Every `id` in `parts` **must** exactly
match a `<g id="...">` in the SVG you generated in Step 2.

```json
{
  "version": "1.0",
  "assetId": "<character_id>",
  "parts": [
    { "id": "body",        "parent": null,   "pivot": {"x": 256, "y": 420}, "depth": 0 },
    { "id": "head",        "parent": "body", "pivot": {"x": 256, "y": 200}, "depth": 1 },
    { "id": "eyes-open",   "parent": "head", "pivot": {"x": 256, "y": 185}, "depth": 2 },
    { "id": "eyes-closed", "parent": "head", "pivot": {"x": 256, "y": 185}, "depth": 2 },
    { "id": "mouth-neutral","parent":"head", "pivot": {"x": 256, "y": 240}, "depth": 2 },
    { "id": "mouth-open",  "parent": "head", "pivot": {"x": 256, "y": 248}, "depth": 2 }
  ]
}
```

**Pivot point rules:**
- Pivot is the center of rotation in SVG viewbox coordinates (0–512 range)
- Body pivot: center-bottom of the torso (where it meets the ground)
- Head pivot: chin/neck junction
- Eyes/mouth: their own center
- Arms: shoulder joint
- Legs: hip joint

## Step 4 — Generate the pose library

Generate a VectorForge-style pose library. Required poses:

| id | name | What it expresses |
|----|------|-------------------|
| `idle` | Idle | Neutral standing, slight weight |
| `blink` | Blink | Eyes closed (handled by CSS, transforms empty) |
| `talk_open` | Talk (Open) | Mouth open, slight head tilt |
| `talk_closed` | Talk (Closed) | Mouth neutral, slight head forward |
| `surprised` | Surprised | Head back, eyes wide (scaleY > 1 on eyes-open) |
| `point_left` | Point Left | Arm extended left (if arm parts exist) |
| `point_right` | Point Right | Arm extended right (if arm parts exist) |

Each pose's `transforms` maps `part_id → {rotation?, x?, y?, scaleX?, scaleY?}`.
Only include parts that actually change. Idle transforms should all be 0/1 (rest pose).

## Step 5 — Construct the asset_spec

```json
{
  "id": "<slug derived from character name>",
  "name": "<character display name>",
  "description": "<one sentence describing the character>",
  "style": "<visual style from proposal>",
  "colors": {
    "body": "#hex",
    "skin": "#hex",
    "<other key colors>": "#hex"
  }
}
```

## Step 6 — Call SvgCharacterWriter

```python
result = svg_character_writer.execute({
    "svg_content":  "<the SVG you generated>",
    "rig_manifest": { ... },
    "pose_library": { ... },
    "asset_spec":   { ... },
    "output_dir": "projects/<project_name>/assets/characters/<character_id>/",
})
```

If `result.success` is False, read `result.error`. It will list specific `<g>` IDs
that are missing from the SVG. Fix the SVG (add the missing groups) and retry.
Maximum 3 attempts before escalating to the user.

If `result.success` is True:
- `result.data["rig_plan"]` is the schema-valid OpenMontage `rig_plan` artifact
- `result.data["pose_library"]` is the schema-valid OpenMontage `pose_library` artifact
- `result.data["svg_path"]` is the path to `character.svg`
- `result.data["preview_path"]` is the path to `preview.html`

## Step 7 — Preview prompt

Ask the user:

> "Character generated. Want to preview it before continuing? (yes / no)"

**If yes:**
1. Try to open `result.data["preview_path"]` using Playwright or Chrome DevTools MCP.
   Navigate to the file URL, wait 2s for GSAP to initialize, take a screenshot.
   Describe what you see: character name, colors, visible pose buttons.
2. If no MCP browser is available, output:
   `Open in your browser: file://<preview_path>`
3. Ask: "Does this character look right? (approve / regenerate / adjust description)"
   - **approve** → proceed to Step 8
   - **regenerate** → repeat from Step 2 with the same prompt (counts as one revision)
   - **adjust** → user provides updated description, repeat from Step 2

**If no:** proceed directly to Step 8.

## Step 8 — Save to library prompt

Ask the user:

> "Save this character to your library for reuse in future videos? (yes / no)"

**If yes:**
```python
character_library.execute({
    "action": "save",
    "asset_spec":   asset_spec,
    "svg_content":  svg_content,
    "rig_manifest": rig_manifest,
    "pose_library": pose_library,
    "source_dir":   result.data["output_dir"],
})
```

**If no:** continue.

## Step 9 — Write stage artifacts

Write three JSON artifacts to `projects/<project_name>/artifacts/`:

**`character_design.json`** — construct from asset_spec + script/proposal context:
```json
{
  "version": "1.0",
  "style": {
    "visual_style": "<from proposal>",
    "palette": ["<hex colors from asset_spec.colors>"],
    "line_style": "outline"
  },
  "characters": [{
    "id": "<asset_spec.id>",
    "display_name": "<asset_spec.name>",
    "role": "main",
    "body_type": "<humanoid / animal / robot / abstract>",
    "style": "<asset_spec.style>",
    "required_emotions": ["neutral", "happy", "surprised", "focused"],
    "required_actions": ["idle", "talk", "point", "react"]
  }]
}
```

**`rig_plan.json`** — write `result.data["rig_plan"]` directly.

**`pose_library.json`** — write `result.data["pose_library"]` directly.

Validate each against its schema before checkpointing:
```python
validate_artifact(character_design, "character_design")
validate_artifact(rig_plan, "rig_plan")
validate_artifact(pose_library, "pose_library")
```

## Step 10 — Checkpoint

Stage complete. Present to user:
- Character name, style, and saved path
- Pose library summary (list of pose IDs)
- Whether character was saved to library
- Preview path (if generated)

Wait for human approval before advancing to `scene_plan`.
