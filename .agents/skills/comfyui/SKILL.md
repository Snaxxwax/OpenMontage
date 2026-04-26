---
name: comfyui
description: ComfyUI local backend integration for OpenMontage image, video, and audio generation workflows, including custom workflow overrides, provenance, and runtime troubleshooting.
---

# ComfyUI (Local Backend) — OpenMontage Skill

Use this when you are routing image/video/audio generation through **ComfyUI** instead of direct diffusers/PyTorch or paid APIs.

## What ComfyUI is (in OpenMontage terms)

ComfyUI is treated as a **local execution layer**: OpenMontage tools submit a workflow graph to a running ComfyUI server, poll for completion, then download the resulting artifacts.

OpenMontage provides:

- `comfyui_image` — image generation (bundled FLUX2 txt2img + custom workflow override)
- `comfyui_video` — video generation (bundled WAN 2.2 t2v/i2v + custom workflow override)
- `comfyui_audio` — audio/music generation (custom workflow override-first)
- `comfyui_wan_video` — legacy WAN TI2V-focused workflow (separate provider `comfyui_wan`)

Default recommendation: use `comfyui_video` for ComfyUI-based video generation. Treat `comfyui_wan_video` as an explicit legacy path.

## Configuration

Required: a running ComfyUI server with API enabled (default port is `8188`).

Environment variables (recommended in `.env`):

- `COMFYUI_SERVER_URL` — base URL, e.g. `http://127.0.0.1:8188`
- Optional per-capability overrides:
  - `COMFYUI_IMAGE_SERVER_URL`
  - `COMFYUI_VIDEO_SERVER_URL`
  - `COMFYUI_AUDIO_SERVER_URL`
- Legacy alias (supported for older setups): `COMFYUI_BASE_URL`

## Custom workflow contract (governance-critical)

When using `workflow_json` / `workflow_path` overrides:

- Provide an explicit `output_node` whenever possible.
  - If omitted, OpenMontage will *auto-detect* artifacts across all output nodes, which can be ambiguous for complex workflows.
- For **image_to_video** custom workflows:
  - ComfyUI requires the reference image to exist on the server (input directory).
  - OpenMontage can upload a local/URL image via `/upload/image`, but it must know **where** to patch the uploaded filename in your workflow.
  - Use either:
    - `reference_image_patch={ "node_id": "...", "input_key": "image" }`, or
    - `workflow_patches` with the correct node id + input name.

## Provenance fields (auditability)

If the workflow is user-supplied, avoid claiming a fixed model name downstream.

Use `provenance` to record:

- `declared_model` (freeform)
- `workflow_name`
- `notes` (e.g. which ComfyUI workflow export, which node pack, which checkpoint)

OpenMontage will also compute `workflow_hash` to uniquely identify the graph.

## VRAM/RAM management

Most memory strategy is controlled by the **ComfyUI server** (offload/lowvram flags, model caching, etc).

OpenMontage supports lightweight safety gates per call:

- `wait_for_queue=true` (+ `queue_timeout_seconds`) to avoid piling jobs into a busy server
- `require_free_vram_mb` / `require_free_ram_mb` (+ `resource_timeout_seconds`) to wait for minimum free memory (best-effort via `/system_stats`)

## Troubleshooting checklist

1. Verify server: `curl $COMFYUI_SERVER_URL/system_stats`
2. Verify queue is empty: `curl $COMFYUI_SERVER_URL/queue`
3. If bundled workflows fail, ensure the referenced model filenames exist in ComfyUI’s model directories.
4. If custom workflow fails with “No output artifacts found”, check `output_node` and confirm the Save node writes to ComfyUI outputs.
