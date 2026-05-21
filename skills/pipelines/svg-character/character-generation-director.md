# Character Generation Director — svg-character

You are the character-generation agent. Your job is to generate a complete SVG
character with hierarchical joint rig, validate it, write it to disk, preview it,
and ask the user what to do next.

## Step 0: Read the Layer 3 skills

Before generating anything, read:
- `.agents/skills/svg-character-animation/` — animation patterns, GSAP integration
- `.agents/skills/character-rigging/` — rig conventions, pivot rules

## Step 1: Check the character library

```python
# Via CharacterSpecGenerator with action="library_check"
# or directly via CharacterLibrary
from tools.character.character_library import CharacterLibrary
lib = CharacterLibrary()
matches = lib.list()
# Present to user: {id, name, style, description, preview_path}
```

If matches exist, ask the user: "Reuse an existing character, modify one, or generate new?"

## Step 2: Generate the SVG

Use the **hierarchical local joint group model**. This is the only permitted rig model.
Flat global-pivot rigs are not acceptable.

### Hierarchical model rules

- Joint groups (`<g id="...-joint">`) rotate around their local `(0,0)`.
  The joint's `transform="translate(x,y)"` positions it relative to its parent.
- Art groups (`<g id="...-art">`) are direct children of their joint group.
  They contain the visual geometry (shapes, paths). No geometry goes directly inside a joint group.
- Each limb segment is a separate joint group nested inside its parent's joint group.

### Required nesting hierarchy

```
<g id="body">                          ← root-level, no rotation
  <g id="body-art">...</g>

<g id="head">                          ← root-level
  <g id="head-art">...</g>
  <g id="eyes-open-joint">
    <g id="eyes-open-art">...</g>
  </g>
  <g id="eyes-closed-joint" style="display:none">
    <g id="eyes-closed-art">...</g>
  </g>
  <g id="mouth-neutral-joint">
    <g id="mouth-neutral-art">...</g>
  </g>
  <g id="mouth-open-joint" style="display:none">
    <g id="mouth-open-art">...</g>
  </g>

<g id="upper-arm-l-joint" transform="translate(SHOULDER_X, SHOULDER_Y)">
  <g id="upper-arm-l-art">...</g>
  <g id="forearm-l-joint" transform="translate(0, UPPER_ARM_LENGTH)">
    <g id="forearm-l-art">...</g>
    <g id="hand-l-joint" transform="translate(0, FOREARM_LENGTH)">
      <g id="hand-l-art">...</g>
    </g>
  </g>
</g>

<g id="upper-arm-r-joint" transform="translate(SHOULDER_X, SHOULDER_Y)">
  ... (mirror of left arm)
</g>

<g id="upper-leg-l-joint" transform="translate(HIP_X, HIP_Y)">
  <g id="upper-leg-l-art">...</g>
  <g id="lower-leg-l-joint" transform="translate(0, UPPER_LEG_LENGTH)">
    <g id="lower-leg-l-art">...</g>
    <g id="foot-l-joint" transform="translate(0, LOWER_LEG_LENGTH)">
      <g id="foot-l-art">...</g>
    </g>
  </g>
</g>

<g id="upper-leg-r-joint" ...>...</g>
```

### Why local joints

When you animate `upper-arm-l-joint` with `rotation: 30`, the forearm and hand
rotate with it automatically because they're children. The forearm can then be
independently rotated on top. This is how real skeletal animation works. Without
nesting, every limb segment needs a manually-computed global rotation.

## Step 3: Generate the rig manifest

Every part gets:
- `id` — matches the `<g id>` in SVG exactly
- `parentId` — the `id` of the parent `<g>` in SVG (null for root-level)
- `partType` — `"joint"` or `"art"`
- `pivot` — `{x: 0, y: 0}` for all joint groups (they rotate at their own origin)

```json
{
  "version": "1.0",
  "assetId": "my-character",
  "parts": [
    {"id": "upper-arm-l-joint", "parentId": null,                "partType": "joint", "pivot": {"x": 0, "y": 0}},
    {"id": "upper-arm-l-art",   "parentId": "upper-arm-l-joint", "partType": "art",   "pivot": {"x": 0, "y": 0}},
    {"id": "forearm-l-joint",   "parentId": "upper-arm-l-joint", "partType": "joint", "pivot": {"x": 0, "y": 0}},
    {"id": "forearm-l-art",     "parentId": "forearm-l-joint",   "partType": "art",   "pivot": {"x": 0, "y": 0}},
    {"id": "hand-l-joint",      "parentId": "forearm-l-joint",   "partType": "joint", "pivot": {"x": 0, "y": 0}}
  ]
}
```

## Step 4: Generate the pose library

Poses target **joint IDs** (not art IDs) with rotation values:

```json
{
  "assetId": "my-character",
  "poses": [
    {
      "id": "idle",
      "name": "Idle",
      "transforms": {
        "head": {"rotation": 0},
        "upper-arm-l-joint": {"rotation": -10},
        "upper-arm-r-joint": {"rotation": 10}
      }
    },
    {
      "id": "point_right",
      "name": "Point Right",
      "transforms": {
        "upper-arm-r-joint": {"rotation": -60},
        "forearm-r-joint":   {"rotation": -20}
      }
    }
  ]
}
```

Required poses: `idle`, `blink`, `talk_open`, `talk_closed`, `point_left`,
`point_right`, `walk_contact`, `walk_passing`, `surprised`.

## Step 5: Call SvgCharacterWriter

```python
from tools.character.svg_character_writer import SvgCharacterWriter

result = SvgCharacterWriter().execute({
    "svg_content": svg_string,
    "rig_manifest": rig_manifest,
    "pose_library": pose_library,
    "asset_spec": asset_spec,
    "output_dir": "projects/<project>/assets/characters/<character-id>/",
})
```

If validation fails, fix the specific error reported. The most common errors:
- `SVG is missing <g> elements` → add missing `<g id>` to SVG
- `SVG nesting mismatch` → nest the SVG `<g>` inside its parent joint group
- `missing a valid pivot` → add `"pivot": {"x": 0, "y": 0}` to the part

## Step 6: Preview + single combined question

After SvgCharacterWriter succeeds:

1. Open `preview.html` with Playwright or Chrome DevTools MCP. Take a screenshot.
   Describe: poses visible, proportions, any rendering artifacts.
   Fallback if no browser MCP: output `Preview: file:///path/to/preview.html`

2. Ask **one combined question**:

   > "Approve, adjust, regenerate, or save to library?"

   - **Approve** → continue to next stage (character not saved to library)
   - **Adjust** → user provides updated description; re-run generation (counts against `max_revisions_per_stage: 3`)
   - **Regenerate** → re-run with same prompt (counts against limit)
   - **Save to library** → `CharacterLibrary.save()`, then continue

   Never ask "do you want to preview?" first — preview is automatic.
   Never split this into two separate questions.
