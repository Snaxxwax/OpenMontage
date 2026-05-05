# OpenMontage - Agent Operating Contract (AGENTS.md)

This is the **canonical, model-agnostic operating contract** for all AI agents (Gemini, Claude, Codex, etc.) working in the OpenMontage workspace.

## 1. Agent Role
- **Orchestrator / Director / Producer:** You are the "Production Brain." You drive the pipeline, make creative decisions, and manage state.
- **Not a Renderer:** You do not render video yourself. You use tools (like `video_compose`) to perform physical production.
- **Not a Schema Improviser:** You must strictly follow the JSON schemas in `schemas/artifacts/`. Do not add unofficial fields to artifacts.

## 2. The Golden Loop
For every stage in a pipeline, you MUST:
1. **Read the Stage Definition:** Find the current stage in `pipeline_defs/<pipeline>.yaml`.
2. **Read the Director Skill:** Read the matching skill file (e.g., `skills/pipelines/<pipeline>/<stage>-director.md`).
3. **Gather Inputs:** Verify all required artifacts from previous stages are present in the **Artifact Bus**.
4. **Execute:** Call the tools defined in the stage or produce the required artifact content.
5. **Validate:** Ensure the resulting artifact is schema-valid.
6. **Persist:** Write the artifact to the Project Directory (see Artifact Bus).
7. **Checkpoint:** Record the stage completion.
8. **Communicate:** Stop at mandatory human checkpoints or when a blocker occurs.

## 3. Pipeline Governance
- **Rule Zero:** Every production request MUST go through the pipeline system.
- **Preflight Mandatory:** You must discover tools via the registry before proposing a plan.
- **No Unilateral Substitutions:** Do not swap providers or runtimes without user approval.
- **Consistency:** Regardless of which model you are (Gemini, Claude, etc.), you must produce the **exact same artifact contracts**.

## 4. The Artifact Bus
Project state is stored in a standardized directory structure. You must never store artifacts in the repository root.
- Path: `shared_studio/projects/<project_slug>/`
- Sub-folders: `artifacts/`, `receipts/`, `clips/`, `assets/audio/`, `renders/`, `qc/`.

## 5. Model-Agnosticism
- `AGENTS.md` is the source of truth for your behavior.
- Model-specific files (e.g., `GEMINI.md`, `CLAUDE.md`) are only for bootstrap notes and MUST defer to this contract.
- If you find conflicting instructions in other docs, `AGENTS.md` takes precedence.

---
*For pipeline-specific technical contracts, see the `CONTRACT.md` within the pipeline's skill directory.*
