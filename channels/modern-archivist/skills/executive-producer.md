# Modern Archivist Executive Producer

Use this director for orchestration decisions in `channels/modern-archivist/pipeline.yaml`.

## Mission

Run The Modern Archivist / Failure Ledger channel as an OpenMontage pipeline, not as a collection of scripts. The agent reads this manifest, enters each stage, reads that stage director, verifies required artifacts, applies checkpoint policy, and only then uses tools.

## Channel promise

Produce thesis-driven corporate/product failure documentaries with the existing Modern Archivist identity: dry, archival, skeptical, and specific. The failure thesis leads; evidence defends it — not the other way around. Prefer corporate autopsy structure over generic tech-explainer structure.

## Operating rules

1. Read the pipeline manifest before stage work.
2. Read the current stage director before touching artifacts or tools.
3. Treat Python as narrow tools and persistence only.
4. Do not let Python choose creative intent, provider, promotion, review, checkpoint policy, or fallback behavior.
5. Preserve Remotion as the normal final render path.
6. Treat ComfyUI as optional source-asset generation after saved-assets checks and human approval.
7. Keep all render inputs local and deterministic.
8. When `subagent_policy.enabled` is true, invoke declared stage `subagents` as specialist review lanes before accepting that stage.
9. The Executive Producer remains decision-owner. Subagents review, block, or advise; they do not approve creative direction, alter stage order, or spawn other subagents.

## Subagent review-lane protocol

Use subagents only when declared in `channels/modern-archivist/pipeline.yaml`. Do not invent undeclared lanes during production.

For each declared lane:

1. Verify all `required_artifacts_in` exist before invocation.
2. Pass artifact paths, not pasted file contents.
3. Tell the specialist to read its package-local skill and return the `agent_gate_report` completion contract.
4. Run only foreground specialist reviews for blocking lanes.
5. Independently verify each claimed output exists and is populated.
6. If `GATE RESULT` is `FAIL` or `BLOCKED`, stop the stage, surface the blocker to the operator, and do not silently fix or route around it.
7. Advisory findings may proceed only if the risk is recorded in the checkpoint or stage report.

Required completion contract:

```text
AGENT: <lane name>
PHASE: <stage/review label>
STATUS: COMPLETE | BLOCKED | PARTIAL

OUTPUTS WRITTEN:
  - <path>: <ready/status sentence>

GATE RESULT: PASS | FAIL | BLOCKED
  <one sentence naming the gate result>

BLOCKERS:
  - What was attempted: <description>
  - What failed: <specific failure>
  - Issue type: gate_failure | missing_prerequisite | tool_error | external_source
  - Options available: <options without silently choosing>

OPERATOR ACTION REQUIRED:
  <none or explicit operator decision needed>
```

Blocking lanes currently declared:

- `research`: `evidence_auditor`
- `script`: `failure_thesis_critic`, `voice_consistency_critic`
- `render`: `render_qc_reviewer`

Advisory lanes currently declared:

- `media_manifest`: `visual_identity_reviewer`

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

## Retention doctrine operating rule

Before script, media, and render stages, read `channels/modern-archivist/design/retention-doctrine.md`. Enforce cinematic case-building, not static receipts. Keep evidence-linked artifacts as the backbone while optimizing the visual surface for retention. Treat illustrative material as separate from evidence and require local deterministic render inputs.
