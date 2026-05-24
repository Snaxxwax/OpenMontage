# The Modern Archivist / Failure Ledger

Autonomous YouTube channel package for DOM-rendered, thesis-driven corporate and product failure autopsies.

This channel is intentionally separate from the generic OpenMontage pipeline set. OpenMontage provides shared tools, rendering infrastructure, checkpoints, and provider plumbing; this directory owns the channel identity, puppet contract, episode schemas, retention doctrine, and Remotion-first rendering rules.

## Channel premise

The Modern Archivist investigates corporate promises, product failures, abandoned systems, public records, source code, and online artifacts to show how a failure actually happened. The format is a Failure Ledger: a premium, evidence-linked autopsy that names the claim, follows the receipts, exposes the mechanism, and lands the lesson without turning into generic outrage.

## Retention format

The channel follows `design/retention-doctrine.md`: Coffeezilla credibility, MagnatesMedia pacing, and Modern Archivist identity. Receipts remain the backbone, but the visual surface should be cinematic case-building: case-file boards, contradiction reveals, failure graphs, kinetic text, code walkthroughs, source montages, and scarce critical-error interrupts. The Archivist is an anchor and punctuation device, not a permanent mascot.

## Renderer contract

- Canonical renderer: Remotion / React.
- Output is DOM-based animation using CSS transforms, opacity, SVG, and state machines.
- No WebGL.
- No canvas skeletal rigging.
- No image-to-video character animation.
- Live research/data must be fetched before rendering and stored as local JSON. Remotion renders deterministic props only.
- Illustrative cinematic material must be labeled internally and must not impersonate evidence.

## Core visual states

- `STATE_MONOLOGUE`: Archivist centered, slate/teal palette.
- `STATE_DEEP_DIVE`: Archivist exits; MediaContainer owns the frame.
- `STATE_CRITICAL_ERROR`: pattern interrupt; crimson/red palette; Archivist as purposeful interruption.

## Asset status

The current character asset in `channels/modern-archivist/assets/source/` is a temporary transparent portrait source. It is not yet a final layered puppet because it lacks glasses, cutout lenses, separated mouth layers, and separated arm/mug layers. The MVP renderer overlays synthetic mouth/glasses/mug layers until final assets are prepared.
