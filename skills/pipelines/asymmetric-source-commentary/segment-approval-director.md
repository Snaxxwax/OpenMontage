# Segment Approval Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Approve or reject visual rhythm segments before acquisition and render work proceeds.

## 2. Inputs
- `visual_rhythm_plan`
- `evidence_candidate_manifest`
- `rights_risk_manifest`

## 3. Outputs
- `source_segment_approval_manifest` at `artifacts/source_segment_approval_manifest.json`

## 4. Allowed Tools
- None required. This is a human checkpoint and logic gate.

## 5. Forbidden Actions
- Approving segments without required evidence ids.
- Approving source/proof segments without source labels.
- Treating approval as acquisition permission unless capture plan is also approved.

## 6. Required Checks
- Every approved segment id exists in `visual_rhythm_plan`.
- Required evidence ids exist in `evidence_candidate_manifest`.
- Approval reason explains proof value or context value.
- Rights risk does not exceed approved use.

## 7. Failure Conditions
- Segment references missing evidence.
- Segment approval conflicts with rights risk.
- Segment is visual filler, not source/proof/context.

## 8. Handoff Artifact Requirements
- Validate against `schemas/artifacts/source_segment_approval_manifest.schema.json`.
- Stop if human approval is required and absent.
