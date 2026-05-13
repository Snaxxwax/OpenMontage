# Capture Plan Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Convert approved source candidates into a capture plan for screenshots, excerpts, screen recordings, or YouTube ranges.

## 2. Inputs
- `source_candidate_manifest`
- `youtube_source_manifest`
- `asymmetric_claim_map` when available

## 3. Outputs
- `source_capture_plan` at `artifacts/source_capture_plan.json`

## 4. Allowed Tools
- None required. This is a planning and approval stage.

## 5. Forbidden Actions
- Capturing media before `operator_approved_for_acquisition` is true.
- Creating captures without `purpose`, `claim_ids`, and rights risk.
- Planning full-video downloads when a narrow timestamp range is enough.

## 6. Required Checks
- Every capture has stable `id`, `source_id`, `capture_type`, `purpose`, and approval state.
- YouTube captures include timestamp range.
- Web captures include target URL and purpose.
- Rights risk is recorded per capture.

## 7. Failure Conditions
- Capture cannot be tied to a claim or viewer-lens beat.
- Capture duplicates another item without new proof value.
- Capture plan attempts acquisition inside planning stage.

## 8. Handoff Artifact Requirements
- Validate against `schemas/artifacts/source_capture_plan.schema.json`.
- If human approval is required, stop before acquisition.
