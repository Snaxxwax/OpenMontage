# Asymmetric — Shared Channel Assets

This directory holds **reusable, channel-level** assets for the Asymmetric framework: brand tokens, SVG primitives, HyperFrames templates, diagram devices, and reusable audio/caption presets.

## What belongs here (shared)
- Brand system: `brand/tokens.json`, typography notes, logos, safe color usage rules.
- Reusable visual building blocks:
  - Diagram primitives (nodes, edges, grid, labels) in `diagrams/primitives/`
  - Visual devices (chokepoint ring, pivot markers, x-ray reveals, etc.) in `diagrams/devices/`
  - SVG objects/icons in `objects/svg/`
  - Non-human silhouettes/roles in `roles/silhouettes/`
- Reusable templates:
  - HyperFrames partials and card templates in `templates/hyperframes/`
  - Thumbnail layout templates in `templates/thumbnails/`
- Reusable presets:
  - Audio mix presets (ducking, loudness targets) in `audio/presets/`
  - Caption styling presets in `captions/presets/`
- Provider receipts/log schemas and logs in `provider_logs/`

## What does **not** belong here (episode-local)
- Episode-specific research, scripts, story beats, scene plans.
- Episode-specific data pulls, charts, or one-off diagrams.
- One-off images or clips that won't be reused.
- Provider outputs tied to a single episode run.

Rule of thumb: if it will likely be reused in **3+ videos**, it belongs here.

## Naming conventions
- Prefer kebab-case for folders and filenames: `chokepoint-ring.svg`, `narration-ducking.json`.
- Prefer semantic names over scene numbers: `source-card-reveal.html` not `s07_card.html`.
- For templates, use suffixes that clarify the format:
  - `.svg` for vector objects
  - `.json` for presets/manifests
  - `.html` / `.css` / `.js` for HyperFrames templates/partials

## Accepted formats
- SVG: `.svg` (preferred for diagram-native visuals)
- JSON: `.json` (tokens, manifests, presets)
- HyperFrames templates: `.html`, `.css`, `.js` (+ optional `.md` docs)
- Typography: `.md`, `.txt`, and font files as needed (`.woff2` preferred)
- Logos: `.svg` preferred, then `.png` for raster fallback

## Reuse + versioning rules
- `manifest.json` is the source of truth for the package version and major contents.
- Backward-compatible changes: bump `manifest.json` `version` patch/minor.
- Breaking changes (renames/removals/meaning changes): bump major.
- Avoid moving/renaming assets once used; add new versions instead.

## Referencing shared assets from projects
Episode/project assets should reference shared assets by **repo-relative path**, e.g.:
- `channel_assets/asymmetric/brand/tokens.json`
- `channel_assets/asymmetric/objects/svg/...`

Do not copy shared assets into `projects/**` unless they are being modified for that episode only.

