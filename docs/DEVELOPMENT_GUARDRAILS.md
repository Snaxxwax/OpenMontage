# OpenMontage Development Guardrails

This document prevents future development from drifting away from the OpenMontage architecture.

## Core rule

OpenMontage is an agent-orchestrated system. The control plane is:

1. YAML pipeline manifests
2. Markdown stage director skills
3. JSON artifacts and checkpoints
4. BaseTool/provider utilities called only after the manifest + director skill authorize them

Python is allowed for tools and persistence. Python is not allowed to become the pipeline.

## Allowed Python

Python may implement:

- `BaseTool` subclasses under `tools/` with registry-discoverable contracts
- deterministic validators and preflight checks
- filesystem/artifact persistence utilities
- checkpoint read/write helpers
- schema validation
- narrow provider submission helpers whose inputs were selected by the stage director
- narrow lifecycle helpers such as `status`, `ensure`, `free`

Allowed Python must be deterministic or contract-bound. It should accept explicit inputs and return explicit JSON/tool results.

## Forbidden Python

Do not add Python that decides:

- pipeline stage order
- whether a creative stage is approved
- which asset intent should be generated
- which provider/model/workflow should be used
- when to launch or stop GPU services as pipeline flow
- which generated candidates are acceptable
- when to promote generated assets
- fallback behavior after a provider failure
- checkpoint policy or human approval policy

Those decisions belong in the pipeline manifest and director skills.

## Required shape for new pipeline work

Every new pipeline in `pipeline_defs/` must include:

- `version`
- `category`
- `stability`
- `default_checkpoint_policy`
- `orchestration`
- `required_skills`
- `extensions`
- stage `skill` references
- stage `required_artifacts_in` where applicable
- stage `produces`
- stage `tools_available` / `required_tools` / `optional_tools`
- stage `checkpoint_required`
- stage `human_approval_default`
- stage `review_focus`
- stage `success_criteria`

If a stage needs a new behavior, first update the stage director skill. Add Python only after the skill defines the contract and only for the narrow utility/tool portion.

Pipeline-specific work belongs in its manifest, skills, schemas, design docs, templates, and render contracts. Do not place pipeline-specific identity, voice, assets, or render assumptions in unrelated manifests or skills unless the behavior has been intentionally generalized for all OpenMontage users.

## Required review questions for new scripts

Before adding or keeping a Python script, answer yes to all:

1. Is this a tool, validator, persistence helper, schema check, or lifecycle utility?
2. Does it avoid creative decisions and provider/model/workflow selection?
3. Does it avoid checkpoint and human approval policy?
4. Are all inputs explicit rather than hidden in local state?
5. Does it return explicit JSON/tool output suitable for an agent to review?
6. Is the corresponding pipeline stage/director skill the authority for when to call it?

If any answer is no, move that logic into YAML/Markdown and reduce the Python to a narrow helper.


## Validation

Run the contract tests after pipeline or script changes:

```bash
pytest tests/contracts/test_pipeline_governance.py
```

These tests are not a substitute for architectural review, but they catch the highest-risk drift patterns.
