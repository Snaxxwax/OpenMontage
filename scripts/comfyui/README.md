# ComfyUI helper scripts

These scripts are tools, not the Modern Archivist pipeline.

Pipeline orchestration lives in:

- `channels/modern-archivist/pipeline.yaml`
- `channels/modern-archivist/skills/asset-generation-director.md`

## Script classification

### `asset_generation_needed.py`

Status: supported preflight validator.

Contract:

- Input: asset requirements policy plus filesystem state.
- Output: JSON with `needs_generation`, selected profiles, missing requirement IDs, and checked paths.
- Allowed behavior: read local files and inspect whether required saved assets exist.
- Forbidden behavior: provider choice, creative decisions, GPU mutation, asset promotion, checkpoint policy.

### `ensure_comfyui_docker.py`

Status: supported lifecycle utility.

Contract:

- Commands: `status`, `ensure`, `free`.
- Allowed behavior: report ComfyUI/GPU state, safely ensure the configured Dockerized ComfyUI service, free ComfyUI memory.
- Forbidden behavior: deciding whether a pipeline stage should run, choosing asset intent/workflow/model, promoting assets, killing unknown GPU processes.

## Correct Modern Archivist flow

1. Read `channels/modern-archivist/pipeline.yaml`.
2. Enter `asset_generation` stage.
3. Read `channels/modern-archivist/skills/asset-generation-director.md`.
4. Run `asset_generation_needed.py` for the director-selected profile/intent.
5. If saved assets satisfy the request, write/reuse `artifacts/asset_manifest.json` and skip ComfyUI.
6. If assets are missing, present a generation plan and wait for human approval.
7. Only after approval, use `ensure_comfyui_docker.py status|ensure` and a narrow provider submission helper.
8. Review candidates; promote only selected assets.
9. Run `ensure_comfyui_docker.py free` and verify success criteria.
