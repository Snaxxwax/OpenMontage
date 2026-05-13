# Greenlight Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Decide whether the topic deserves an Asymmetric episode before research spend. The topic must serve an AI security or trust-failure viewer lens, not general tech news.

## 2. Inputs
- User topic or episode premise
- Channel profile and Asymmetric style playbook when available

## 3. Outputs
- `asymmetric_greenlight` at `artifacts/asymmetric_greenlight.json`

## 4. Allowed Tools
- None required. This is an editorial gate.

## 5. Forbidden Actions
- Starting source discovery or scripting before greenlight is true.
- Greenlighting broad topics without a concrete viewer problem and viewer outcome.
- Treating novelty as enough without channel fit.

## 6. Required Checks
- `primary_function` is education, investigation, or source-led explanation.
- `viewer_problem` names what the viewer misunderstands or misses.
- `viewer_outcome` names the reusable lens the viewer gains.
- `audience_equity_score`, `sauce_integrity_score`, and `consistency_score` meet the schema range.
- Topic centers AI security, trust failure, platform control, or adjacent systems leverage.

## 7. Failure Conditions
- No concrete viewer lens.
- No source-led path to proof.
- Topic cannot be explained without speculation or hype.

## 8. Handoff Artifact Requirements
- Validate against `schemas/artifacts/asymmetric_greenlight.schema.json`.
- Persist only in the Artifact Bus: `shared_studio/projects/<project_slug>/artifacts/`.
