# Evidence Triage Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Select candidate evidence for each claim and assess rights risk before any acquisition.

## 2. Inputs
- `asymmetric_claim_map`
- `source_candidate_manifest`
- `youtube_source_manifest`
- `source_capture_plan`

## 3. Outputs
- `evidence_candidate_manifest` at `artifacts/evidence_candidate_manifest.json`
- `rights_risk_manifest` at `artifacts/rights_risk_manifest.json`

## 4. Allowed Tools
- Metadata inspection
- Transcript inspection when available

## 5. Forbidden Actions
- Downloading or capturing media.
- Marking evidence as production-ready without rights risk.
- Selecting decorative b-roll as evidence.

## 6. Required Checks
- Every evidence item maps to a `claim_id`, `source_id`, asset type, and purpose.
- Evidence priority reflects proof value, not visual appeal.
- Rights risk is recorded for every evidence item.
- YouTube evidence has timestamp range when used as a clip.

## 7. Failure Conditions
- Claim has no evidence candidate and no labeled limitation.
- Evidence purpose does not explain what the viewer learns.
- Rights risk missing or unsupported.

## 8. Handoff Artifact Requirements
- Validate against `evidence_candidate_manifest.schema.json` and `rights_risk_manifest.schema.json`.
- Persist both artifacts before scripting or visual rhythm.
