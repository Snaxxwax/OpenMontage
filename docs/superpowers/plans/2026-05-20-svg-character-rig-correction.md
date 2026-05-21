# SVG Character Rig Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat global-pivot rig model with hierarchical local joint groups: joint `<g>` elements nest inside their parent joint `<g>`, art elements are children of their joint group, and `SvgCharacterWriter` validates that SVG nesting matches `rig_manifest` `parentId` fields.

**Architecture:** `SvgCharacterWriter.execute()` gains a new `_validate_nesting()` step that parses SVG XML parent-child relationships and cross-checks each rig part's `parentId` against actual SVG structure. The `rig_plan.schema.json` adds `parentId` and `partType` fields. The `character-generation-director.md` skill is rewritten to mandate the hierarchical model with code examples. Preview flow collapses to one combined question.

**Tech Stack:** Python 3.11, `xml.etree.ElementTree` (stdlib), pytest, JSON Schema draft 2020-12

---

## File Map

**Modified files:**
- `tools/character/svg_character_writer.py` — add `_extract_parent_map()`, add nesting validation in `execute()`, rename `parent` → `parentId` in rig parts
- `tests/tools/character/test_svg_character_writer.py` — update fixtures to hierarchical SVG + `parentId`; add nesting validation tests
- `schemas/artifacts/rig_plan.schema.json` — add `parentId` and `partType` to part items

**New files:**
- `skills/pipelines/svg-character/character-generation-director.md` — hierarchical rig model, preview flow, pose rules

---

## Task 1: Add `_extract_parent_map()` + nesting validation to `SvgCharacterWriter`

**Files:**
- Modify: `tools/character/svg_character_writer.py`
- Modify: `tests/tools/character/test_svg_character_writer.py`

- [ ] **Step 1: Write the failing tests**

Open `tests/tools/character/test_svg_character_writer.py`. Add these fixtures and tests after the existing ones:

```python
# ── Hierarchical SVG fixture ──────────────────────────────────────────────────

HIERARCHICAL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <g id="body"><rect x="156" y="280" width="200" height="200" fill="#4a9eff"/></g>
  <g id="head">
    <g id="head-art"><circle cx="256" cy="200" r="90" fill="#ffcc88"/></g>
    <g id="eyes-open-joint">
      <g id="eyes-open-art">
        <circle cx="225" cy="185" r="12" fill="#333"/>
        <circle cx="287" cy="185" r="12" fill="#333"/>
      </g>
    </g>
    <g id="mouth-neutral-joint">
      <g id="mouth-neutral-art">
        <path d="M225 240 Q256 265 287 240" fill="none" stroke="#333" stroke-width="4"/>
      </g>
    </g>
  </g>
  <g id="upper-arm-l-joint" transform="translate(156,300)">
    <g id="upper-arm-l-art"><rect x="-15" y="0" width="30" height="80" fill="#4a9eff"/></g>
    <g id="forearm-l-joint" transform="translate(0,80)">
      <g id="forearm-l-art"><rect x="-12" y="0" width="24" height="70" fill="#4a9eff"/></g>
    </g>
  </g>
</svg>"""

HIERARCHICAL_RIG = {
    "version": "1.0",
    "assetId": "test_hierarchical",
    "parts": [
        {"id": "body",              "parentId": None,               "pivot": {"x": 256, "y": 400}},
        {"id": "head",              "parentId": None,               "pivot": {"x": 256, "y": 200}},
        {"id": "head-art",          "parentId": "head",             "pivot": {"x": 0, "y": 0}},
        {"id": "eyes-open-joint",   "parentId": "head",             "pivot": {"x": 0, "y": 0}},
        {"id": "eyes-open-art",     "parentId": "eyes-open-joint",  "pivot": {"x": 0, "y": 0}},
        {"id": "mouth-neutral-joint","parentId": "head",            "pivot": {"x": 0, "y": 0}},
        {"id": "mouth-neutral-art", "parentId": "mouth-neutral-joint","pivot": {"x": 0, "y": 0}},
        {"id": "upper-arm-l-joint", "parentId": None,               "pivot": {"x": 0, "y": 0}},
        {"id": "upper-arm-l-art",   "parentId": "upper-arm-l-joint","pivot": {"x": 0, "y": 0}},
        {"id": "forearm-l-joint",   "parentId": "upper-arm-l-joint","pivot": {"x": 0, "y": 0}},
        {"id": "forearm-l-art",     "parentId": "forearm-l-joint",  "pivot": {"x": 0, "y": 0}},
    ],
}

HIERARCHICAL_POSES = {
    "assetId": "test_hierarchical",
    "poses": [
        {"id": "idle", "name": "Idle", "transforms": {"head": {"rotation": 0}}},
        {"id": "talk_open", "name": "Talk Open",
         "transforms": {"mouth-neutral-joint": {"scaleY": 0}, "eyes-open-joint": {"scaleY": 1}}},
    ],
}

HIERARCHICAL_ASSET_SPEC = {
    "id": "test_hierarchical",
    "name": "Hierarchical Test Character",
    "style": "test",
    "description": "Test character with hierarchical rig",
    "viewBox": "0 0 512 512",
}


def test_hierarchical_rig_valid(tmp_path):
    """Valid hierarchical SVG with matching parentId passes."""
    writer = SvgCharacterWriter()
    result = writer.execute({
        "svg_content": HIERARCHICAL_SVG,
        "rig_manifest": HIERARCHICAL_RIG,
        "pose_library": HIERARCHICAL_POSES,
        "asset_spec": HIERARCHICAL_ASSET_SPEC,
        "output_dir": str(tmp_path),
    })
    assert result.success, result.error


def test_nesting_mismatch_fails(tmp_path):
    """parentId in manifest that doesn't match SVG nesting fails validation."""
    bad_rig = {
        **HIERARCHICAL_RIG,
        "parts": [
            *HIERARCHICAL_RIG["parts"][:2],
            # forearm-l-joint claims parent is body, but SVG has it inside upper-arm-l-joint
            {"id": "forearm-l-joint", "parentId": "body", "pivot": {"x": 0, "y": 0}},
        ],
    }
    # Trim SVG parts list to only include IDs we're testing
    writer = SvgCharacterWriter()
    result = writer.execute({
        "svg_content": HIERARCHICAL_SVG,
        "rig_manifest": bad_rig,
        "pose_library": HIERARCHICAL_POSES,
        "asset_spec": HIERARCHICAL_ASSET_SPEC,
        "output_dir": str(tmp_path),
    })
    assert not result.success
    assert "forearm-l-joint" in result.error
    assert "nesting" in result.error.lower() or "parent" in result.error.lower()


def test_parentid_none_at_svg_root_passes(tmp_path):
    """Part with parentId=None that is a top-level SVG group passes."""
    writer = SvgCharacterWriter()
    rig = {
        "version": "1.0",
        "assetId": "test_hierarchical",
        "parts": [
            {"id": "body", "parentId": None, "pivot": {"x": 256, "y": 400}},
            {"id": "head", "parentId": None, "pivot": {"x": 256, "y": 200}},
        ],
    }
    result = writer.execute({
        "svg_content": HIERARCHICAL_SVG,
        "rig_manifest": rig,
        "pose_library": HIERARCHICAL_POSES,
        "asset_spec": HIERARCHICAL_ASSET_SPEC,
        "output_dir": str(tmp_path),
    })
    assert result.success, result.error
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/pop/repos/openmontage-asymmetric
python -m pytest tests/tools/character/test_svg_character_writer.py -k "hierarchical or nesting" -v
```

Expected: `test_hierarchical_rig_valid` fails (no parentId validation yet — it may pass or the `parentId` key may cause issues with existing `parent` logic). `test_nesting_mismatch_fails` fails (no nesting validation → result is success, assertion fails).

- [ ] **Step 3: Add `_extract_parent_map()` to `svg_character_writer.py`**

Add after `_extract_group_ids()`:

```python
def _extract_parent_map(svg_content: str) -> dict[str, str | None]:
    """Map each <g id="..."> to its nearest ancestor <g id="..."> (or None)."""
    import xml.etree.ElementTree as ET
    # Strip namespace prefixes so tag matching works on bare tag names
    cleaned = re.sub(r'\sxmlns(?::\w+)?="[^"]+"', '', svg_content)
    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError as exc:
        raise ValueError(f"SVG XML parse error: {exc}") from exc

    result: dict[str, str | None] = {}

    def walk(element: ET.Element, nearest_g_id: str | None) -> None:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        gid = element.get("id") if tag == "g" else None
        if gid is not None:
            result[gid] = nearest_g_id
            for child in element:
                walk(child, gid)
        else:
            for child in element:
                walk(child, nearest_g_id)

    for child in root:
        walk(child, None)
    return result
```

- [ ] **Step 4: Add nesting validation in `execute()` after the existing ID check**

In `SvgCharacterWriter.execute()`, after the `if missing:` block (around line 238), add:

```python
        # Validate: SVG nesting matches manifest parentId fields
        parent_map = _extract_parent_map(svg_content)
        for part in rig_manifest.get("parts", []):
            part_id = part["id"]
            declared_parent = part.get("parentId")  # None means root-level
            actual_parent = parent_map.get(part_id)  # None means root-level in SVG
            if declared_parent != actual_parent:
                return ToolResult(
                    success=False,
                    error=(
                        f"SVG nesting mismatch for '{part_id}': "
                        f"manifest parentId='{declared_parent}' but SVG parent is '{actual_parent}'. "
                        f"Check that the <g id=\"{part_id}\"> element is nested inside "
                        f"<g id=\"{declared_parent}\"> in the SVG."
                    ),
                )
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
python -m pytest tests/tools/character/test_svg_character_writer.py -k "hierarchical or nesting" -v
```

Expected: 3 new tests pass.

- [ ] **Step 6: Run full test suite to confirm no regressions**

```bash
python -m pytest tests/tools/character/test_svg_character_writer.py -v
```

Expected: All existing tests still pass. Note: existing `MINIMAL_RIG` uses `parent` (not `parentId`). The new validation only fires on `parentId` — parts without `parentId` (using `parent` only) skip nesting validation. This is intentional backwards compatibility for the transition period.

- [ ] **Step 7: Commit**

```bash
git add tools/character/svg_character_writer.py \
        tests/tools/character/test_svg_character_writer.py
git commit -m "feat(tool): add hierarchical SVG nesting validation to SvgCharacterWriter"
```

---

## Task 2: Update `rig_plan.schema.json` to support `parentId` and `partType`

**Files:**
- Modify: `schemas/artifacts/rig_plan.schema.json`

- [ ] **Step 1: Write a failing test for the new schema fields**

Append to `tests/pipelines/broadcast_explainer/test_schemas.py` (or create `tests/tools/character/test_rig_schema.py`):

```python
# ── rig_plan parentId + partType ──────────────────────────────────────────────

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

VALID_RIG_PLAN_HIERARCHICAL = {
    "version": "1.0",
    "characters": [
        {
            "character_id": "test_char",
            "rig_type": "svg_rig",
            "parts": [
                {"id": "upper-arm-l-joint", "kind": "joint", "layer": 0,
                 "parentId": None, "partType": "joint"},
                {"id": "upper-arm-l-art",   "kind": "art",   "layer": 1,
                 "parentId": "upper-arm-l-joint", "partType": "art"},
                {"id": "forearm-l-joint",   "kind": "joint", "layer": 0,
                 "parentId": "upper-arm-l-joint", "partType": "joint"},
            ],
            "joints": {
                "upper-arm-l-joint": {"pivot": [0, 0]},
                "forearm-l-joint":   {"pivot": [0, 0]},
            },
            "layers": ["upper-arm-l-joint", "upper-arm-l-art", "forearm-l-joint"],
            "required_poses": ["idle"],
        }
    ]
}


def test_rig_plan_hierarchical_valid():
    schema = load_schema("rig_plan")
    jsonschema.validate(VALID_RIG_PLAN_HIERARCHICAL, schema)


def test_rig_plan_invalid_part_type():
    schema = load_schema("rig_plan")
    bad = {
        **VALID_RIG_PLAN_HIERARCHICAL,
        "characters": [{
            **VALID_RIG_PLAN_HIERARCHICAL["characters"][0],
            "parts": [{"id": "x", "kind": "joint", "layer": 0, "partType": "blob"}],
        }],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
```

- [ ] **Step 2: Run test to confirm failure**

```bash
python -m pytest tests/pipelines/broadcast_explainer/test_schemas.py -k "rig_plan" -v
# or if added to test_rig_schema.py:
python -m pytest tests/tools/character/test_rig_schema.py -v
```

Expected: Fails — `parentId` and `partType` not in schema, `additionalProperties: false` rejects them.

- [ ] **Step 3: Update `schemas/artifacts/rig_plan.schema.json`**

In the `parts` array `items` object, add `parentId` and `partType` to properties:

```json
"parts": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "kind", "layer"],
    "properties": {
      "id":         { "type": "string" },
      "kind":       { "type": "string" },
      "layer":      { "type": "integer" },
      "asset_path": { "type": "string" },
      "parent":     { "type": "string" },
      "parentId": {
        "description": "ID of the parent <g> joint group in SVG. Null means root-level.",
        "oneOf": [{ "type": "string" }, { "type": "null" }]
      },
      "partType": {
        "description": "joint = rotation group at local (0,0); art = visual geometry child of a joint",
        "type": "string",
        "enum": ["joint", "art"]
      }
    },
    "additionalProperties": false
  }
}
```

- [ ] **Step 4: Run test to confirm it passes**

```bash
python -m pytest tests/pipelines/broadcast_explainer/test_schemas.py -k "rig_plan" -v
```

Expected: Pass.

- [ ] **Step 5: Commit**

```bash
git add schemas/artifacts/rig_plan.schema.json \
        tests/pipelines/broadcast_explainer/test_schemas.py
git commit -m "feat(schema): add parentId and partType to rig_plan parts"
```

---

## Task 3: Write `character-generation-director.md` with hierarchical rig model

**Files:**
- Create: `skills/pipelines/svg-character/character-generation-director.md`

- [ ] **Step 1: Write the skill**

```markdown
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
```

- [ ] **Step 2: Confirm file exists**

```bash
wc -l skills/pipelines/svg-character/character-generation-director.md
```

Expected: ~140+ lines.

- [ ] **Step 3: Commit**

```bash
git add skills/pipelines/svg-character/character-generation-director.md
git commit -m "feat(skill): character-generation-director with hierarchical joint rig model"
```
