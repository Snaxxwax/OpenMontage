# Modern Archivist Character Assets

This directory is the production gate for the Modern Archivist full-body layered puppet. Source/trial assets may live under `channels/modern-archivist/assets/source/` or `channels/modern-archivist/assets/svg_layers/`, but they are not production until they pass this rubric and are declared in `modern_archivist_puppet_manifest.json`.

## Production source of truth

- Production v2 manifest: `modern_archivist_puppet_manifest.json`
- Legacy manifest: `puppet_manifest.json` is v1 compatibility only, not the current production rig contract.
- Asset ledger: `asset-inventory.md`
- Render-facing mirror: `remotion-composer/public/modern-archivist/`

## Shared canvas

The canonical puppet canvas is **1254×1254 pixels**. The v2 manifest declares `rig_contract: full_body_layered` and preserves the full-body Modern Archivist identity.

## Coordinate modes

The manifest supports explicit mixed coordinate modes:

- `canvas_registered`: full-canvas 1254×1254 RGBA layers aligned by shared canvas coordinates. Most body/head/glasses/arm/prop layers should use this mode.
- `anchored_overlay`: cropped overlays positioned by manifest `anchor` and `pivot`. Current mouth PNGs use this mode for near-term compatibility.

Do not pretend cropped assets are shared-canvas layers. Do not tightly crop a layer unless its `coordinate_mode`, `anchor`, and `pivot` are correct in the manifest.

## Alpha requirements

- **Mode:** RGBA only for production PNGs.
- **Hard alpha:** Prefer fully opaque or fully transparent pixels. Avoid soft/feathered transparent edges unless the layer is explicitly exempted, such as a controlled lens highlight.
- **Transparency:** Production layers must have a non-empty alpha bbox and must not fill the full canvas with opaque pixels.
- **No baked backgrounds:** Transparent outside the semantic element.

## Flat palette target

The character uses a flat, limited-palette visual style.

- Target a small visible color set, roughly black plus a few character/accent colors.
- Prefer flat fills, hard edges, and simple vector-like shapes.
- Avoid gradients, painterly texture, fuzzy extraction, and over-traced noise.

## Promotion process

A trial asset becomes production only after all steps below are complete:

1. Record the candidate in `asset-inventory.md` with dimensions, alpha/bbox stats, visible color count, semantic group, coordinate mode, issue, and next action.
2. Verify the coordinate mode:
   - `canvas_registered`: exactly 1254×1254 RGBA.
   - `anchored_overlay`: cropped/small PNG is allowed only with explicit `anchor` and `pivot` in the manifest.
3. Verify hard alpha, visible bbox, transparent background, and flat palette target.
4. Check the semantic role: layer must be an animation part, not a baked preview/composite unless the manifest intentionally treats it as such.
5. Copy the production asset to the appropriate channel asset path and mirror render-facing files under `remotion-composer/public/modern-archivist/`.
6. Update `modern_archivist_puppet_manifest.json` with `status: production`, `coordinate_mode`, `anchor`, `pivot`, and `bounds_required`.
7. Run:

```bash
pytest tests/contracts/test_modern_archivist_puppet_assets.py -q
cd remotion-composer && npx tsc --noEmit --pretty false
```

## Preview-only rule

Preview-only assets, composites, HTML demos, or manually stacked SVG experiments under `assets/svg_layers/` must not be promoted directly. Use them as visual references only. Production preview and Remotion should converge on the same manifest asset list.

## No head-only replacements

No head-only, bust-only, or cropped-face puppet may replace the full-body rig unless the user explicitly approves it. The body/base layer must preserve full-body bounds and the channel's recognizable full-body puppet identity.

## Semantic groups

| Group | Purpose |
|---|---|
| `body` | Torso/body base layer |
| `head` | Head and hair layers |
| `eyes` | Open/closed eye variants, ideally separated L/R |
| `brows` | Neutral/skeptical/deadpan brow variants |
| `mouths` | Anchored mouth/phoneme overlays |
| `glasses` | Glasses frame, masks, and highlights |
| `arms` | Arm/hand variants for idle and action poses |
| `props` | Mug, steam, character shadow, and related props |

## Production vs placeholder

- `status: production`: asset exists, is referenced by the v2 manifest, and passes contract tests.
- `status: placeholder`: semantic slot exists but must not be treated as production. `asset-inventory.md` must state why it is a placeholder and what should happen next.
