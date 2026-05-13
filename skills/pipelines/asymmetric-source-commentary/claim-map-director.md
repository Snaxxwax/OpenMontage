# Claim Map Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Turn the greenlit premise into discrete, source-checkable claims with overstatement controls.

## 2. Inputs
- `asymmetric_greenlight`
- `source_candidate_manifest`
- `youtube_source_manifest`

## 3. Outputs
- `asymmetric_claim_map` at `artifacts/asymmetric_claim_map.json`

## 4. Allowed Tools
- None required. This is logic and editorial mapping.

## 5. Forbidden Actions
- Writing claims that exceed available source support.
- Hiding uncertainty or limitations.
- Using one claim id for multiple unrelated assertions.

## 6. Required Checks
- Every claim has stable `id`, claim text, status, source ids, mechanism relevance, and overstatement risk.
- Claim wording is falsifiable and supportable by primary sources.
- Claims preserve the Asymmetric viewer lens: hidden control surface, trust boundary, extraction layer, or leverage map.

## 7. Failure Conditions
- Claims are vague, moralized, or unverifiable.
- Source ids do not exist in source manifests.
- No explicit overstatement risk.

## 8. Handoff Artifact Requirements
- Validate against `schemas/artifacts/asymmetric_claim_map.schema.json`.
- Persist before evidence triage and scripting.
