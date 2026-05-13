# Visual Rhythm Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Plan the source/proof rhythm of the edit so the viewer sees evidence early and repeatedly.

## 2. Inputs
- `script`
- `asymmetric_claim_map`
- `evidence_candidate_manifest`
- `source_capture_plan`

## 3. Outputs
- `visual_rhythm_plan` at `artifacts/visual_rhythm_plan.json`

## 4. Allowed Tools
- None required. This is timeline planning.

## 5. Forbidden Actions
- Approving render before human approval.
- Planning source clips without burned-in labels.
- Using visual filler where proof is needed.

## 6. Required Checks
- At least one approved proof event starts by 10 seconds before render.
- At least two source/proof events exist before render.
- Every source/proof segment has `source_label_present` and `source_label`.
- Segment ids are stable and later used by segment approval and render.

## 7. Failure Conditions
- Visual rhythm is narration-only.
- Source/proof events do not map to evidence ids.
- Source labels missing or vague.

## 8. Handoff Artifact Requirements
- Validate against `schemas/artifacts/visual_rhythm_plan.schema.json`.
- Render readiness later checked by `scripts/asymmetric_gate.py render-readiness`.
