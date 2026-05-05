# Clip Use Gate Director - Source-Commentary Pipeline

## 1. Stage Purpose
Act as the semantic gatekeeper. Issue "Evidence Lock" receipts for specific clips, binding them to claims.

## 2. Inputs
- `evidence_candidate_manifest`

## 3. Outputs
- `clip_use_receipts` (collection of artifacts)

## 4. Allowed Tools
- None (Logic and human-review stage).

## 5. Forbidden Actions
- Approving b-roll. `decorative_broll` MUST be `false`.
- Approving clips without commentary. `commentary_attached` MUST be `true`.
- Approving clips without source labels. `source_label_required` MUST be `true`.

## 6. Required Checks
- `rationale` field must explain *how* the clip proves the claim.
- `original_audio_use` is explicitly chosen (`muted`, `ducked`, `quote_audio`).
- `status` is only set to `approved` if all evidence criteria are met.

## 7. Failure Conditions
- Receipts that lack `claim_id` traceability.
- `approved_for_edit` is set to `true` while `status` is `pending`.

## 8. Handoff Artifact Requirements
- Must follow `clip_use_receipt.schema.json`.
- Approved receipts are mandatory for the next stage (Acquisition).
