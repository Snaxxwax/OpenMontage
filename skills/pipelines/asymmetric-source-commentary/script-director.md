# Script Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Write source-led commentary that teaches the viewer lens while staying tied to claim and evidence artifacts.

## 2. Inputs
- `asymmetric_greenlight`
- `asymmetric_claim_map`
- `evidence_candidate_manifest`
- `rights_risk_manifest`

## 3. Outputs
- `script` at `artifacts/script.json` when using canonical script artifact

## 4. Allowed Tools
- None required. This is writing and structure.

## 5. Forbidden Actions
- Adding claims not present in `asymmetric_claim_map`.
- Describing exploitation steps beyond educational context.
- Using hype, gossip, or unsupported causal certainty.
- Using Piper narration for this pipeline.

## 6. Required Checks
- Hook states consequence or control surface quickly.
- Claims appear with source-backed language and labeled limitations.
- Narration points to source/proof moments early.
- Voice is forensic, controlled, direct, and unsentimental.

## 7. Failure Conditions
- Script cannot be traced back to claim ids.
- Viewer outcome from greenlight is lost.
- Evidence gaps are hidden.

## 8. Handoff Artifact Requirements
- If `script.json` is produced, validate against `schemas/artifacts/script.schema.json`.
- Persist under Artifact Bus `artifacts/`.
