# The Modern Archivist / Failure Ledger

Autonomous YouTube channel package for DOM-rendered, thesis-driven corporate and product failure autopsies.

This channel is intentionally separate from the generic OpenMontage pipeline set. OpenMontage provides shared tools, rendering infrastructure, checkpoints, and provider plumbing; this directory owns the channel identity, episode schemas, retention doctrine, and Remotion-first rendering rules.

## Channel premise

The Modern Archivist investigates corporate promises, product failures, abandoned systems, public records, source code, and online artifacts to show how a failure actually happened. The format is a Failure Ledger: a premium, evidence-linked autopsy that names the claim, follows the receipts, exposes the mechanism, and lands the lesson without turning into generic outrage.

## Canonical development brief

The continuing source of truth for channel strategy and development is `design/channel-source-of-truth.md`. It defines the Corporate True Crime positioning, source-footage/artifact-first visual policy, topic selection rules, runtime split, and anti-patterns. If older exploratory notes conflict with that document, `design/channel-source-of-truth.md` wins unless the user explicitly supersedes it.

## Retention format

The channel follows `design/retention-doctrine.md`: Coffeezilla credibility, MagnatesMedia pacing, and Modern Archivist identity. Receipts remain the backbone, but the visual surface should be cinematic case-building: case-file boards, contradiction reveals, failure graphs, kinetic text, code walkthroughs, source montages, and scarce critical-error interrupts. The channel frame and evidence treatment carry the identity; there is no permanent mascot layer.

## Renderer contract

- Canonical renderer: Remotion / React.
- Output is DOM-based animation using CSS transforms, opacity, SVG, and state machines.
- No WebGL.
- No canvas skeletal rigging.
- No image-to-video character animation.
- Live research/data must be fetched before rendering and stored as local JSON. Remotion renders deterministic props only.
- Illustrative cinematic material must be labeled internally and must not impersonate evidence.

## Core visual states

- `STATE_CASE_OPEN`: case-file premise, slate/teal palette, and the first verifiable receipt.
- `STATE_DEEP_DIVE`: source montage, recreated UI, documents, or diagrams own the frame.
- `STATE_CRITICAL_ERROR`: pattern interrupt; crimson/red palette reserved for a material contradiction or failure point.

## Asset status

The legacy character rig, puppet assets, and puppet-specific ComfyUI workflow were removed. Episode visuals use source footage, archived web, recreated UI, evidence cards, diagrams, and approved props/backgrounds/thumbnails. Generated assets must remain review-gated and must not impersonate sourced evidence.
