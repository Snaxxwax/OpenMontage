# OpenMontage - Gemini Agent Instructions

> **MANDATORY:** Read and follow the model-agnostic contract in [`AGENTS.md`](AGENTS.md) first.

This file contains Gemini-specific bootstrap notes. For all pipeline behavior, creative decisions, and artifact generation, `AGENTS.md` is the canonical source of truth.

### Model-Specific Reminders
- **Artifact Contract:** Regardless of being Gemini, you must produce the same schema-valid artifact JSONs as any other model.
- **Source-Commentary:** For this pipeline, strictly enforce the "Evidence Lock" described in `skills/pipelines/source-commentary/CONTRACT.md`.
- **Tool Use:** Always use `.execute(params)` for tool calls.
