# Agent Boot Packet
**Compiled:** 2026-05-16T03:54:13.223852+00:00

## Stop Conditions
- If `contract_status.yaml` shows `stale: true` or `blocking_conflicts: true`: **halt and report to operator**.
- If `bootstrap_ok: false`: **halt and report bootstrap gap**.
- Current conflicts: 0 blocking. No action required.

## Role
Orchestrator. Not renderer. Not schema improviser.

## Operational Rules
1. Read active task packet before any action.
2. Stay inside allowed paths listed in this packet.
3. Discover tools through `tool_registry` only. Do not invent tool names.
4. Use selector tools (`tts_selector`, `image_selector`, `video_selector`) when provider is unspecified.
5. Load stage-specific skills only when the task requires them.
6. Required receipts vary by pipeline — read `skills/pipelines/<pipeline>/CONTRACT.md` on entry.
7. Checkpoint state after each stage.

## Allowed Paths
- `AGENTS.md`
- `GEMINI.md`
- `CLAUDE.md`
- `CODEX.md`
- `.agent/`
- `pipeline_defs/`
- `skills/`
- `schemas/`
- `tools/`
- `tests/`
- `docs/`
- `remotion-composer/src/`

## Forbidden Paths
- `.git/`
- `.env`
- `node_modules/`
- `__pycache__/`
- `shared_studio/`
- `remotion-composer/public/`

## Conflict Status
0 blocking conflict(s). No action required.
