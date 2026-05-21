> **Scope (post-decomposition):** This director handles non-audio asset prep only —
> SVG character retrieval, background imagery, props, and font confirmation.
> TTS generation is handled by `narration-director.md`.
> Audio post-processing is handled by `audio-post-director.md`.

# Broadcast Explainer — Assets Director

Prepare non-audio assets and write `artifacts/asset_manifest.json`.

## Inputs

- `artifacts/scene_plan.json` — scene structure, character actions, required visuals
- `artifacts/script.json` — section text (for context only; do not generate audio here)

## Steps

### 1. Character SVG

Check `assets/characters/` for the character SVG used in this production. If it
exists (from a prior `character_generation` stage or the character library), record
its path. Do not regenerate it here.

If no character SVG is present, check `character_library/` for a matching character
and copy it to `assets/characters/<character-id>/`.

### 2. Background imagery

For each scene in `scene_plan.json` that requires a background:
- Check `assets/images/` for existing assets
- Generate or retrieve backgrounds using `image_selector` if not present
- Record provider, model, and prompt in the manifest

### 3. Props and overlays

For stat cards, text overlays, and graphical elements described in `scene_plan.json`:
- Note what HyperFrames will render natively (stat cards, text) vs what needs image assets
- Generate image assets for non-native visual elements only

### 4. Font confirmation

If `DESIGN.md` specifies custom fonts, confirm they are loaded via CDN or present
in `assets/fonts/`. List in the manifest.

### 5. Write `artifacts/asset_manifest.json`

```json
{
  "version": "1.0",
  "characters": [
    {
      "id": "axiom",
      "svg_path": "assets/characters/axiom/character.svg",
      "rig_manifest_path": "assets/characters/axiom/rig_manifest.json",
      "pose_library_path": "assets/characters/axiom/pose_library.json"
    }
  ],
  "backgrounds": [
    {
      "scene_id": "s01_hook",
      "path": "assets/images/s01_background.png",
      "provider": "flux",
      "prompt": "..."
    }
  ],
  "props": [],
  "fonts": [],
  "notes": ""
}
```

## Pass Condition

- `artifacts/asset_manifest.json` written
- All referenced asset paths exist on disk
- Character SVG accounted for (path recorded)

## Report Format

- pass/fail
- Files written or confirmed existing
- Any assets that could not be sourced (flag for human review)
