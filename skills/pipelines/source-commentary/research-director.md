# Research Director - Source-Commentary Pipeline

## 1. Stage Purpose
Ground the video production in verified facts, data, and diverse perspectives. Provide the evidentiary foundation for all future claims.

## 2. Inputs
- User prompt / Topic description
- (Optional) Preliminary research links

## 3. Outputs
- `research_brief` (canonical artifact)

## 4. Allowed Tools
- Web search / Research agents (external to project tools)

## 5. Forbidden Actions
- Generating narration or scripts (deferred to `claim_map`).
- Assuming facts without citation.
- Proposing visual treatments (focus only on content truth).

## 6. Required Checks
- At least 5 unique sources cited.
- Specific data points identified (usable for `stat_card` or evidence).
- Contradictory perspectives included if the topic is debated.

## 7. Failure Conditions
- Vague findings without source URLs.
- Failure to identify underserved gaps in the current content landscape.

## 8. Handoff Artifact Requirements
- Must follow `research_brief.schema.json`.
- Must contain an `angles_discovered` section grounded in the research.
