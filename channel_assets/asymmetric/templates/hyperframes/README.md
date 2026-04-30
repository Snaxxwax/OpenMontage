# HyperFrames Templates (Asymmetric)

This folder is the shared library of **HyperFrames-native** SVG/CSS/HTML templates and partials used across Asymmetric episodes.

## Structure
- `_shared/`: reusable partials (tokens import, grid, transitions, common card shells)
- `title-cards/`: opening titles / cold opens
- `chapter-cards/`: chapter/act transitions
- `lower-thirds/`: captions, labels, speakerless callouts
- `stat-cards/`: quantitative claims with confidence qualifiers
- `source-cards/`: evidence moments (what/where/when/source_map ref)
- `cta-cards/`: end cards and calls to action

## Rules
- Prefer SVG/CSS-first implementations; avoid generated imagery unless necessary.
- Keep templates parameterized; do not bake in episode-specific copy.
- If a template variant is reused 3+ times, promote it into `_shared/` or a dedicated folder with a stable name.

