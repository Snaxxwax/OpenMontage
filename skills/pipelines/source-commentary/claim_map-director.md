# Claim Map Director - Source-Commentary Pipeline

## 1. Stage Purpose
Decompose the narrative into discrete, falsifiable "Claims" that require evidence. This stage builds the "Production Brain" for the commentary.

## 2. Inputs
- `research_brief`
- `performance_brief`

## 3. Outputs
- `narration_claim_map` (canonical artifact)
- `script` (supporting artifact)

## 4. Allowed Tools
- None. This is a logic and scripting stage.

## 5. Forbidden Actions
- Creating generic narration without specific claim anchors.
- Planning visual b-roll (all clips must be "Evidence").
- Using internal IDs that do not persist across stages.

## 6. Required Checks
- Every major narrative beat has a unique `claim_id`.
- Claims are specific enough to be "proven" by a video clip.
- Narration includes explicit cues for source-commentary.

## 7. Failure Conditions
- Script sections that cannot be mapped to evidence.
- Claims that are too broad for visual verification (e.g., "The world is changing").

## 8. Handoff Artifact Requirements
- `narration_claim_map` must associate each narration segment with one or more `claim_id`s.
