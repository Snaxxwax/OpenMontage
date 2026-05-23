# Legacy broadcast-explainer archive

This directory preserves the old `broadcast-explainer` prototype as Modern Archivist / Failure Ledger reference material.

## Status

- Archived from: `pipeline_defs/broadcast-explainer.yaml`
- Old director skills archived from: `skills/pipelines/broadcast-explainer/`
- Style snapshot archived from: `styles/broadcast-investigative.yaml`
- Canonical successor: `channels/modern-archivist/pipeline.yaml`
- Runtime assumptions: HyperFrames, GSAP timeline authoring, local Fish Speech S2-Pro narration

## Why it was moved out of core

The old pipeline was useful production DNA, but it mixed channel-specific assumptions into generic OpenMontage locations:

- investigative-broadcast / Asymmetric channel identity
- e-girl narrator voice and Fish Speech reference-audio assumptions
- AXIOM character pivot constants and animation details
- HyperFrames-specific composition and QA flow
- local distribution behavior such as copying to `~/syncthing/final.mp4`

Those details belong in a channel package, not in `pipeline_defs/` or `skills/pipelines/`.

## How to use this archive

Use this as reference only when developing Modern Archivist channel behavior. Do not load it as a first-class OpenMontage core pipeline.

Reusable ideas may be generalized back into core only after removing channel identity and preserving the YAML/Markdown orchestration model. Likely candidates:

- audio timing artifact pattern
- composition QA checklist
- render verification checklist
- generic investigative/data-journalism style guidance
- HyperFrames lint/render lessons, if HyperFrames remains a supported generic runtime
