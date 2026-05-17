# Stage: performance_brief

## Inputs
- `research_brief`

## Outputs
- `artifacts/performance_brief.json`

## Allowed Actions
- Read `research_brief`
- Select one viewer promise from the strongest angle discovered
- Select one opening claim — a concrete already-happened fact, not a question
- Select one title angle (title, pillar, engine)
- Select one thumbnail angle using schema fields (family, variant, headline_text)
- Write at least 3 `first_15_seconds_plan` beats with explicit seconds ranges
- Write at least 1 `retention_risk`
- Write `boring_parts_to_cut` (may be empty array if research is tight)
- Write `visual_pacing_notes` addressing movement cadence and static-slide risk
- Validate artifact against `schemas/artifacts/performance_brief.schema.json` before writing

## Forbidden Actions
- Reading CLAUDE.md or any model-specific doc
- Writing narration or script copy
- Assigning claim_ids
- Selecting clips or b-roll
- Creating Markdown review docs
- Selecting multiple title angles — commit to one

## Stop Conditions
- `research_brief` is missing or schema-invalid
- Any required performance field is missing
- `first_15_seconds_plan` has fewer than 3 beats
- Schema validation fails

## Handoff Requirements
- `artifacts/performance_brief.json` validates against `schemas/artifacts/performance_brief.schema.json`
- Operator approves before `claim_map` proceeds
