# The Modern Archivist

Autonomous YouTube channel package for DOM-rendered, research-led explainer videos.

This channel is intentionally separate from the generic OpenMontage pipeline set. OpenMontage provides shared tools, rendering infrastructure, checkpoints, and provider plumbing; this directory owns the channel identity, puppet contract, episode schemas, and Remotion-first rendering rules.

## Channel premise

The Modern Archivist investigates how old web artifacts, public records, forgotten standards, and online communities still shape current technology and culture.

## Renderer contract

- Canonical renderer: Remotion / React.
- Output is DOM-based animation using CSS transforms, opacity, and state machines.
- No WebGL.
- No canvas skeletal rigging.
- No image-to-video character animation.
- Live research/data must be fetched before rendering and stored as local JSON. Remotion renders deterministic props only.

## Core visual states

- `STATE_MONOLOGUE`: Archivist centered, slate/teal palette.
- `STATE_DEEP_DIVE`: Archivist exits; MediaContainer owns the frame.
- `STATE_CRITICAL_ERROR`: pattern interrupt; crimson/red palette; Archivist as bottom-right HUD.

## Asset status

The current character asset in `channels/modern-archivist/assets/source/` is a temporary transparent portrait source. It is not yet a final layered puppet because it lacks glasses, cutout lenses, separated mouth layers, and separated arm/mug layers. The MVP renderer overlays synthetic mouth/glasses/mug layers until final assets are prepared.
