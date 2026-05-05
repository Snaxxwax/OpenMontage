# QC Director - Source-Commentary Pipeline

## 1. Stage Purpose
Final audit of narrative integrity and evidence traceability.

## 2. Inputs
- `render_report`
- `research_brief`
- `clip_use_receipts`

## 3. Outputs
- `final_review`

## 4. Allowed Tools
- None.

## 5. Forbidden Actions
- Approving a video that deviates from the `research_brief` truth.
- Overlooking missing source attributions.

## 6. Required Checks
- **Traceability**: "Does Clip X in the final render prove Claim Y from the map?"
- **Labeling**: Are all source clips attributed on-screen?
- **Accuracy**: Does the narration align with the research facts?

## 7. Failure Conditions
- "Hallucinated" claims not supported by the evidence clips.
- Technical glitches (audio pops, visual jitter).

## 8. Handoff Artifact Requirements
- Structured `final_review` with pass/fail verdict.
