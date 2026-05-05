# Edit Plan Director - Source-Commentary Pipeline

## 1. Stage Purpose
Assemble the final edit decisions. Lock the timeline using only verified evidence.

## 2. Inputs
- `narration_claim_map`
- `approved_clip_manifest`

## 3. Outputs
- `edit_decisions`

## 4. Allowed Tools
- None.

## 5. Forbidden Actions
- **REJECT ANY CLIP** missing from `approved_clip_manifest`.
- Using generic b-roll fallbacks for evidence gaps.
- Overlapping narration with source audio without `ducking` rules.

## 6. Required Checks
- Every `claim_id` in the script is covered by at least one cut.
- `source_label_required` is respected in the overlay plan.
- Render runtime matches the proposal (default to `remotion`).

## 7. Failure Conditions
- Timeline contains gaps where evidence was promised.
- Use of unverified media files.

## 8. Handoff Artifact Requirements
- Must follow `edit_decisions.schema.json`.
- Must include precise `ducking` and `source-label` overlay instructions.
