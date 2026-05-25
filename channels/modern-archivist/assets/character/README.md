# Modern Archivist Character Assets

## Shared Canvas

All layers use a **1254×1254 pixel** shared canvas. Every PNG must be exported at exactly this size — do not crop to tight layer bounds unless the coordinate system is explicitly documented. Layers are composited in z-order at pixel-perfect positions.

## Alpha Requirements

- **Mode:** RGBA only. No RGB, no paletted PNG.
- **Alpha:** Hard alpha — fully opaque or fully transparent pixels. No soft/feathered edges unless part of the character design.
- **Transparent ratio:** At least 20% of the canvas must be transparent (alpha < 10).
- No baked backgrounds. Every layer must be transparent outside its element.

## Limited Palette Target

The character uses a flat, limited-palette visual style. When producing new layers:
- Use the reference palette from the existing body/head assets.
- Maximum ~12–16 colours per layer.
- Flat fills, hard edges, no gradients or anti-aliased painterly strokes.

## Layer Naming Convention

```
modern_archivist_{layer_id}.png
```

Examples: `modern_archivist_mouth_closed.png`, `modern_archivist_glasses_frame.png`

All layer IDs are defined in `modern_archivist_puppet_manifest.json`.

## Semantic Groups

| Group | Purpose |
|-------|---------|
| `body` | Torso/body base layer |
| `head` | Head, hair front/back |
| `eyes` | Open/closed eye variants (L and R separate) |
| `brows` | Neutral and skeptical brow variants |
| `mouths` | All mouth/phoneme shapes |
| `glasses` | Glasses frame and lens highlight |
| `arms` | Arm/hand variants (idle, mug grip) |
| `props` | Mug, steam, drop shadow |

## Adding New Layers

1. Export the PNG at 1254×1254 RGBA with hard alpha.
2. Place in `channels/modern-archivist/assets/character/layers/`.
3. Also mirror to `remotion-composer/public/modern-archivist/layers/`.
4. Add or update the layer entry in `modern_archivist_puppet_manifest.json`.
5. Change `"status": "placeholder"` to `"status": "production"` when done.
6. Run `pytest tests/contracts/test_modern_archivist_puppet_assets.py -q` to verify.

## No Head-Only Replacements

Never replace the full puppet with a head-only or face-only crop. The manifest enforces `rig_contract: full_body_layered`. Partial puppet variants must be explicitly approved by the user.

## Production vs Placeholder

- `"status": "production"` — file exists, passes all alpha/canvas checks, ready for render.
- `"status": "placeholder"` — file does not exist yet, tests skip asset checks for this layer.
