# Evidence Candidates Director - Source-Commentary Pipeline

## 1. Stage Purpose
Perform semantic matching between the `narration_claim_map` and the `transcript_index` to find candidate clips.

## 2. Inputs
- `narration_claim_map`
- `transcript_index`

## 3. Outputs
- `evidence_candidate_manifest` (canonical artifact)

## 4. Allowed Tools
- `clip_search` (Text-to-clip ranking based on transcripts)

## 5. Forbidden Actions
- Proposing clips that do not directly address a `claim_id`.
- Hand-writing timestamps without transcript verification.

## 6. Required Checks
- Each claim has at least 1 candidate segment.
- Semantic relevance scores are recorded.
- Candidate ranges (in/out) are sufficient for editorial context.

## 7. Failure Conditions
- Claims with zero candidates.
- Candidate ranges that overlap incorrectly or lack duration metadata.

## 8. Handoff Artifact Requirements
- Map of `claim_id` -> `[source_id, in_seconds, out_seconds, score]`.
