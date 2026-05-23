# Modern Archivist Executive Producer

Use this director for orchestration decisions in `channels/modern-archivist/pipeline.yaml`.

## Mission

Run The Modern Archivist / Failure Ledger channel as an OpenMontage pipeline, not as a collection of scripts. The agent reads this manifest, enters each stage, reads that stage director, verifies required artifacts, applies checkpoint policy, and only then uses tools.

## Channel promise

Produce evidence-led corporate/product failure documentaries with the existing Modern Archivist identity: dry, archival, skeptical, and specific. Prefer corporate autopsy structure over generic tech-explainer structure.

## Operating rules

1. Read the pipeline manifest before stage work.
2. Read the current stage director before touching artifacts or tools.
3. Treat Python as narrow tools and persistence only.
4. Do not let Python choose creative intent, provider, promotion, review, checkpoint policy, or fallback behavior.
5. Preserve Remotion as the normal final render path.
6. Treat ComfyUI as optional source-asset generation after saved-assets checks and human approval.
7. Keep all render inputs local and deterministic.

## Stage order

research -> script -> audio -> audio_analysis -> media_manifest -> asset_generation -> render

Do not skip a stage unless its director and manifest success criteria explicitly allow reusing a valid artifact.

## Artifact contract

- `artifacts/research_packet.json`
- `artifacts/episode.json`
- `assets/audio/narration.wav`
- `artifacts/audio_analysis.json`
- `artifacts/media_manifest.json`
- `artifacts/asset_manifest.json`
- `artifacts/render_report.json`

## Review posture

Require stronger evidence for stronger claims. Prefer "what the records show" over speculation. If a point cannot be sourced, label it as interpretation or cut it.
