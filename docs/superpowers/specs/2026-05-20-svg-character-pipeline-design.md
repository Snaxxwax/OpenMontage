# SVG Character Pipeline Design

**Date:** 2026-05-20
**Status:** Approved — pending implementation plan

## Problem

The `character-animation` pipeline exists but `CharacterRigRenderer` generates placeholder blob
characters (basic ellipses/circles with hardcoded geometry). There is no mechanism for producing
real styled SVG characters, no character persistence across videos, and no preview step.

SVGMontage (VectorForge) was delivered as a ZIP — a Gemini-powered web app that generates rigged
SVG characters. Rather than wrapping it as an API call, the OpenMontage agent generates SVG
characters directly using its own intelligence guided by the existing `svg-character-animation`
and `character-rigging` Layer 3 skills. This guarantees that `<g>` IDs in the SVG match rig
manifest part names by construction, with no schema translation layer.

## Goals

- Phase 1: Agent-driven SVG character generation integrated into the existing character-animation
  pipeline infrastructure, with character preview and a persistent character library.
- Phase 2: A new `svg-character` pipeline purpose-built for this workflow, collapsing the two
  placeholder stages (`character_design` + `rig_plan`) into a single coherent `character_generation`
  stage.
- Success criterion: Generate one styled SVG character, animate it to a TTS narration line
  (talk pose timed to audio), render a short MP4 clip end-to-end.

## Architecture

### New tools

**`SvgCharacterWriter`** (`tools/character/svg_character_writer.py`)

Validation and persistence. No generation logic.

- Inputs: `svg_content`, `rig_manifest`, `pose_library`, `asset_spec`, `output_dir`
- Validates that every `part.id` in `rig_manifest.parts` exists as a `<g id="...">` element in
  the SVG. Fails fast with a clear error listing missing IDs if not.
- Writes to `output_dir/`:
  - `character.svg`
  - `rig_manifest.json`
  - `pose_library.json`
  - `asset_spec.json`
  - `preview.html` — self-contained GSAP preview with pose buttons (GSAP from CDN, no other deps)
- Returns paths to all written files

**`CharacterLibrary`** (`tools/character/character_library.py`)

Save, load, and list reusable characters. Backed by `character_library/` at the repo root
(gitignored, like `music_library/`).

Operations:
- `list` — returns all saved characters: `[{id, name, style, description, preview_path}]`
- `load(character_id)` — returns full bundle: `{asset_spec, svg_content, rig_manifest, pose_library, preview_path}`
- `save(asset_spec, svg_content, rig_manifest, pose_library)` — writes to
  `character_library/<slug>/` where slug is derived from `asset_spec.id`

Library structure:
```
character_library/
└── <character-slug>/
    ├── asset_spec.json
    ├── character.svg
    ├── rig_manifest.json
    ├── pose_library.json
    └── preview.html
```

### Upgraded tools

**`CharacterRigRenderer`** — gains an `svg_path` / `svg_content` input. When provided, uses the
real SVG instead of generating placeholder blobs. Existing callers that provide neither still get
placeholder output (no breaking change).

**`CharacterSpecGenerator`** — gains a `library_check` action that calls `CharacterLibrary.list()`
and returns matches. Used by the director skill at proposal time.

### New pipeline: `svg-character`

File: `pipeline_defs/svg-character.yaml`

Shares most stages with `character-animation`. Key difference: `character_design` and `rig_plan`
are replaced by a single `character_generation` stage.

| Stage | Produces | Human approval |
|-------|----------|----------------|
| `research` | `research_brief` | No |
| `proposal` | `proposal_packet`, `decision_log` | Yes |
| `script` | `script` | Yes |
| `character_generation` | `character_design`, `rig_plan`, `pose_library` | Yes |
| `scene_plan` | `scene_plan` | Yes |
| `assets` | `asset_manifest` | No |
| `edit` | `edit_decisions`, `action_timeline` | No |
| `compose` | `render_report` | No |
| `publish` | `publish_log` | Yes |

`proposal` stage checks `CharacterLibrary.list()` and surfaces matches before any generation.
`assets` stage handles backgrounds and props only; character assets come from `character_generation`.

### New director skill: `character-generation-director`

File: `skills/pipelines/svg-character/character-generation-director.md`

Teaches the agent to:

1. Read `svg-character-animation` and `character-rigging` Layer 3 skills before generating anything.
2. Check the character library for existing matches and present the user with reuse/modify/new options.
3. Generate the SVG with semantic `<g>` IDs that exactly match the rig manifest part names.
   Required IDs: `body`, `head`, `eyes-open`, `eyes-closed`, `mouth-neutral`, `mouth-open`, plus
   limb/appendage groups appropriate to the character type.
4. Generate a rig manifest referencing the same IDs with pivot points in SVG viewbox coordinates.
5. Generate a pose library with at minimum: `idle`, `blink`, `talk_open`, `talk_closed`,
   `point_left`, `point_right`, `walk_contact`, `walk_passing`, `surprised`.
6. Call `SvgCharacterWriter` to validate consistency and write files.
7. Run the preview + save flow (see below).

## Character Preview Flow

After `SvgCharacterWriter` succeeds, the agent always asks:

> *"Character generated. Want to preview it before continuing?"*

**If yes:**
1. Try Playwright or Chrome DevTools MCP first — open `preview.html`, wait for GSAP init,
   take screenshot to confirm character rendered. If successful, agent describes what it sees.
2. Fallback if no MCP browser available — agent outputs:
   `Open in your browser: file:///path/to/preview.html`

After viewing (either path), the agent asks:
> *"Does this character look right? Approve, regenerate, or adjust the description."*

- **Approve** → continue to save prompt
- **Regenerate** → re-run generation with same or updated prompt (counts against `max_revisions_per_stage: 3`)
- **Adjust** → user updates description, re-run generation

**If no:** pipeline continues immediately to save prompt.

**Save prompt:**
> *"Save this character to your library for reuse in future videos? (yes/no)"*

Yes → `CharacterLibrary.save()`. No → continue without saving.

## Data Flow

```
brief
  → character-generation-director
      → reads svg-character-animation + character-rigging skills
      → checks character library (offer reuse/modify/new)
      → agent generates SVG + rig_manifest + pose_library inline
      → SvgCharacterWriter (validate IDs, write files)
      → preview prompt (Playwright MCP → fallback HTML path)
      → approve / regenerate loop
      → save to library? prompt
  → ActionTimelineCompiler (uses real pose library)
  → CharacterRigRenderer (uses real SVG via svg_path input)
  → video_compose (HyperFrames or Remotion — presented at proposal)
  → MP4
```

## What Does Not Change

- `character-animation` pipeline is unchanged. Existing projects continue to work.
- `SvgRigBuilder` and `PoseLibraryBuilder` remain as placeholder-generation tools for the old pipeline.
- The `VectorForge` Node.js web app (SVGMontage ZIP) is kept as a reference and future human-facing
  tool but is not integrated into the agent workflow in Phase 1.

## Phase 2 (future)

Once `svg-character` is proven:
- `character-animation`'s `character_design` + `rig_plan` stages are upgraded to point at the
  `character-generation-director` skill.
- VectorForge web UI is integrated into the repo under `tools/character/vectorforge/` for
  human-driven character generation with export to the character library.

## File Checklist

**New files:**
- `tools/character/svg_character_writer.py`
- `tools/character/character_library.py`
- `pipeline_defs/svg-character.yaml`
- `skills/pipelines/svg-character/character-generation-director.md`
- `skills/pipelines/svg-character/research-director.md` — reads `skills/pipelines/character-animation/research-director.md` and follows it verbatim
- `skills/pipelines/svg-character/proposal-director.md` — reads `skills/pipelines/character-animation/proposal-director.md`, adds: check `CharacterLibrary.list()` and present matches before presenting concepts
- `skills/pipelines/svg-character/script-director.md` — reads `skills/pipelines/character-animation/script-director.md` and follows it verbatim
- `skills/pipelines/svg-character/scene-director.md` — reads `skills/pipelines/character-animation/scene-director.md` and follows it verbatim
- `skills/pipelines/svg-character/asset-director.md` — reads `skills/pipelines/character-animation/asset-director.md`; character assets (`svg_path`, `rig_manifest`, `pose_library`) are already written — do not regenerate them; handle backgrounds, props, TTS, and music only
- `skills/pipelines/svg-character/edit-director.md` — reads `skills/pipelines/character-animation/edit-director.md` and follows it verbatim
- `skills/pipelines/svg-character/compose-director.md` — reads `skills/pipelines/character-animation/compose-director.md` and follows it verbatim
- `skills/pipelines/svg-character/publish-director.md` — reads `skills/pipelines/character-animation/publish-director.md` and follows it verbatim
- `character_library/.gitkeep`

**Modified files:**
- `tools/character/character_animation.py` — upgrade `CharacterRigRenderer` + `CharacterSpecGenerator`
- `.gitignore` — add `character_library/` (keep `.gitkeep`)

## Open Questions (resolved)

- **Generation model:** agent generates SVG directly (not Gemini API), guaranteeing part ID consistency.
- **Preview runtime:** Playwright/Chrome DevTools MCP first, HTML file path fallback.
- **Render runtime:** presented at proposal per governance contract (HyperFrames and Remotion both surfaced).
- **Library location:** `character_library/` at repo root, gitignored.
