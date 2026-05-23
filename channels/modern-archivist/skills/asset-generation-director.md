# Modern Archivist Asset Generation Director

Use this director only for the `asset_generation` stage in `channels/modern-archivist/pipeline.yaml`.

## Mission

Create `artifacts/asset_manifest.json` by reusing saved channel assets first and generating source assets only when the manifest and human approval require it.

ComfyUI is optional. The normal path is saved vector/PNG assets plus Remotion.

## Hard rules

1. Do not load, launch, or health-check ComfyUI until the saved-assets check says generation is needed.
2. If saved assets satisfy the requested profile/intent, write/reuse `asset_manifest` and stop the stage.
3. ComfyUI outputs are source/reference assets only. They are not final image-to-video shots.
4. Final video render remains Remotion-driven and deterministic.
5. Never kill unknown GPU processes.
6. Never kill desktop/display/compositor processes.
7. Use Dockerized ComfyUI lifecycle only through `scripts/comfyui/ensure_comfyui_docker.py` and only after approval.
8. Generated assets are not auto-promoted. Human review selects candidates before promotion.
9. Do not use `scripts/comfyui/run_asset_generation.py` as pipeline orchestration. It is a deprecated legacy shim, not the stage director.

## Stage workflow

### 1. Read inputs

Read:

- `artifacts/episode.json`
- `artifacts/media_manifest.json`
- `channels/modern-archivist/assets/comfyui_workflows/asset_requirements.yaml`

Determine the required asset profile or intent from those artifacts. The stage director decides this; Python does not.

### 2. Run saved-assets preflight

Use the deterministic checker only:

```bash
python3 scripts/comfyui/asset_generation_needed.py --profile mvp --pretty
python3 scripts/comfyui/asset_generation_needed.py --profile production_puppet --pretty
python3 scripts/comfyui/asset_generation_needed.py --intent expression_sheet --pretty
```

Pick the profile/intent based on the media manifest and approved production need.

### 3. Skip provider if not needed

If the checker returns `needs_generation: false`:

- do not call `ensure_comfyui_docker.py`
- do not start Docker
- do not touch GPU state
- write `artifacts/asset_manifest.json` recording saved asset reuse
- continue to render

### 4. Ask before generation

If generation is needed, present a generation plan before any lifecycle command:

- missing requirement IDs
- requested intent/profile
- provider: ComfyUI Docker, optional local source-asset generator
- workflow/model path if known
- count, expected output location, and review plan
- explicit note that assets will not be auto-promoted

Wait for human approval.

### 5. Lifecycle and provider call

After approval only:

```bash
python3 scripts/comfyui/ensure_comfyui_docker.py status
python3 scripts/comfyui/ensure_comfyui_docker.py ensure
```

Then submit the approved workflow through a narrow provider/tool call. The provider call may use a helper that only submits an already-approved workflow and records outputs; it must not choose intent, workflow, provider, promotion, checkpoint policy, or fallback behavior.

After the batch:

```bash
python3 scripts/comfyui/ensure_comfyui_docker.py free
```

### 6. Review and promotion

Review generated candidates against the quality bar. Present candidates for selection. Promote only selected assets and record source path, selected path, workflow, seed, prompt template, model, review notes, and approval status.

## Output contract

`artifacts/asset_manifest.json` should include:

- `saved_assets_check` payload
- `assets[]` with IDs, paths, type, provenance, and use in scenes
- `generated_candidates[]` if any
- `selected_assets[]` if any were approved
- `provider_plan` and human approval record when ComfyUI was used
- `skipped_provider: true` when saved assets were sufficient

## Quality criteria

Generated candidates must preserve:

- current Archivist silhouette and face
- wavy medium-brown hair
- round black glasses
- tired/deadpan expression language
- dark hoodie identity
- flat 2.5D vector/anime-hybrid style
- hard alpha-friendly edges
- minimal color palette

Reject candidates with:

- changed character identity
- missing/duplicated glasses
- photorealism
- soft painterly shading
- text/watermarks/logos
- noisy backgrounds
- uncuttable merged elements

## Success criteria

- `artifacts/asset_manifest.json` exists.
- Saved-assets check ran before generation.
- ComfyUI was skipped when not needed.
- Any generated asset has provenance and review status.
- No generated asset was promoted without approval.
