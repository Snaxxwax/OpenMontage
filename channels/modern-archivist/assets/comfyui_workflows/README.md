# Pipeline-managed ComfyUI for Modern Archivist assets

This directory holds workflow templates, prompts, and generated output for the ComfyUI-assisted asset stage.

ComfyUI's role in this channel is constrained:

- generate props, backgrounds, and thumbnail base art
- inpaint or upscale source assets before cleanup
- never generate image-to-video character shots
- never fetch/generate during the final Remotion render

Final video remains deterministic:

```text
research/evidence JSON -> script -> Fish Speech -> media manifest -> optional ComfyUI source assets -> cleanup -> Remotion render
```

## Runtime contract

The pipeline must be saved-assets-first. It should not load or launch ComfyUI unless the requested asset profile/intent is missing from saved assets.

Decision order:

1. Run `scripts/comfyui/asset_generation_needed.py` for the requested profile or intent.
2. If `needs_generation=false`, skip ComfyUI entirely and continue with saved manifests/public assets.
3. Only if `needs_generation=true`, enter Docker lifecycle management.
4. Check whether ComfyUI is already running in Docker.
5. Verify `http://127.0.0.1:8188/system_stats` and `/queue`.
6. If healthy, reuse the existing container.
7. If not running, inspect RTX 3090 GPU state with `nvidia-smi`.
8. Stop/unload only configured, allowlisted, non-essential workloads.
9. Refuse to kill unknown GPU processes.
10. Launch `docker-compose.comfyui.yml`.
11. Wait for `/system_stats` before submitting workflows.
12. After batches, call `/free` with `unload_models=true` and `free_memory=true`.

Lifecycle files:

- `channels/modern-archivist/assets/comfyui_workflows/asset_requirements.yaml`
- `scripts/comfyui/asset_generation_needed.py`
- `scripts/comfyui/ensure_comfyui_docker.py`
- `pipeline_defs/support/comfyui-gpu-lifecycle.yaml`
- `docker-compose.comfyui.yml`
- `channels/modern-archivist/skills/asset-generation-director.md`

## Saved asset check

Props/backgrounds check:

```bash
python3 scripts/comfyui/asset_generation_needed.py --profile props_backgrounds --pretty
```

Thumbnail check:

```bash
python3 scripts/comfyui/asset_generation_needed.py --profile thumbnails --pretty
```

MVP check (minimal):

```bash
python3 scripts/comfyui/asset_generation_needed.py --profile mvp --pretty
```

Intent-based check for a new requested asset batch:

```bash
python3 scripts/comfyui/asset_generation_needed.py --intent props --pretty
```

Only run the ComfyUI lifecycle commands below when the check reports `needs_generation=true`.

## Commands

Read-only status:

```bash
python3 scripts/comfyui/ensure_comfyui_docker.py status
```

Dry-run readiness/launch plan:

```bash
python3 scripts/comfyui/ensure_comfyui_docker.py ensure --dry-run
```

Ensure ComfyUI is running:

```bash
python3 scripts/comfyui/ensure_comfyui_docker.py ensure
```

Free VRAM after an asset batch:

```bash
python3 scripts/comfyui/ensure_comfyui_docker.py free
```

Stop the managed container if another stage needs the GPU:

```bash
python3 scripts/comfyui/ensure_comfyui_docker.py stop
```

## Output layout

```text
channels/modern-archivist/assets/source/comfyui_generated/
  raw/
    props/
    backgrounds/
    thumbnails/
  selected/
  final_png/
  manifests/
```

## Workflow priorities

First workflows to build:

1. Failure Ledger prop sheet
2. archive-room background
3. thumbnail base art

## Safety notes

- Unknown GPU process: abort.
- Display/compositor process: never stop.
- Fish Speech: report by default; do not stop unless the lifecycle policy is explicitly changed.
- Generic Python GPU job: report by default; do not stop automatically.