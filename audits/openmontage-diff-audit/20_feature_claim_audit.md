# Feature Claim Audit (Diff vs upstream)

Context:
- Comparison base: `upstream/main`
- This audit evaluates **(a)** committed changes in `upstream/main...HEAD` and **(b)** local uncommitted working-tree diffs.
- A feature is **REAL** only if it has (1) code, (2) wiring/discovery, and (3) a verification path.

## Features Introduced / Changed (Committed)

### 1) ComfyUI backend integration (image/video/audio)
- **Classification:** REAL (code + wiring via registry/selector + contract tests)
- **Evidence files:**
  - `tools/_comfyui/client.py` (shared REST client + workflow patching)
  - `tools/graphics/comfyui_image.py` (`ComfyUIImage` tool, `name="comfyui_image"`)
  - `tools/video/comfyui_video.py` (`ComfyUIVideo` tool, `name="comfyui_video"`)
  - `tools/audio/comfyui_audio.py` (`ComfyUIAudio` tool, `name="comfyui_audio"`)
  - `tools/video/comfyui_wan_video.py` (`ComfyUIWanVideo` legacy provider, `name="comfyui_wan_video"`)
  - Workflow templates: `tools/_comfyui/workflows/*.json`
  - Contract tests: `tests/contracts/test_comfyui_backend.py`
- **Key classes/functions:**
  - `tools._comfyui.client.ComfyUIClient` (`patch_workflow`, `workflow_hash`, server availability checks)
  - `tools.graphics.comfyui_image.ComfyUIImage.execute()`
  - `tools.video.comfyui_video.ComfyUIVideo.execute()`
  - `tools.audio.comfyui_audio.ComfyUIAudio.execute()`
- **How invoked:**
  - Directly by tool name via `ToolRegistry` discovery (any `BaseTool` subclass under `tools/**` is auto-registered).
  - Indirectly via selectors:
    - `tools/graphics/image_selector.py` auto-discovers providers with `capability="image_generation"`.
    - `tools/video/video_selector.py` auto-discovers providers with `capability="video_generation"`.
    - Selector contract tests assert ComfyUI providers are excluded when ComfyUI server is not reachable.
- **Registry / discoverability:** YES (subclass of `BaseTool` + registry auto-walk)
- **Pipeline presence:** INDIRECT (pipelines call `image_selector` / `video_selector`; selectors may pick ComfyUI if available)
- **Schema updates:** NO dedicated artifact schema changes in this commit; tool-level `input_schema` is present.
- **Skills / docs mention:** YES (`.agents/skills/comfyui/SKILL.md`, `docs/PROVIDERS.md`, `docs/ARCHITECTURE.md`, `README.md`, `.env.example`)
- **Compose/render usage:** NOT DIRECT (generation providers; compose is handled by `video_compose`/render runtimes)
- **Verification commands:**
  - Offline contract checks: `python3 -m pytest tests/contracts/test_comfyui_backend.py -q`
  - Registry discovery: `python3 -c "from tools.tool_registry import registry; registry.ensure_discovered(); print('comfyui_image' in registry.list_all())"`
  - Live (requires running ComfyUI): invoke `comfyui_image`/`comfyui_video` with `COMFYUI_SERVER_URL` configured.
- **Risk level:** MEDIUM (large surface area + external runtime dependency; tests are contract-only)
- **What would be required to make it MORE real:** add an optional integration test that runs only when `COMFYUI_SERVER_URL` is set and reachable.

### 2) Fish Speech local TTS provider
- **Classification:** REAL (provider tool + wiring via `tts_selector` + contract tests)
- **Evidence files:**
  - `tools/audio/fish_speech_tts.py` (`FishSpeechTTS`, `capability="tts"`, `name="fish_speech_tts"`)
  - Contract tests: `tests/contracts/test_fish_speech_tts_contract.py`
  - Selector wiring: `tools/audio/tts_selector.py` (auto-discovers capability `tts`)
- **Key classes/functions:**
  - `tools.audio.fish_speech_tts.FishSpeechTTS.execute()`
  - `tools.audio.tts_selector.TTSSelector._providers()`
- **How invoked:**
  - Direct tool call: `fish_speech_tts`
  - Indirect via `tts_selector` (if server is configured and passes dependency checks)
- **Registry / discoverability:** YES
- **Pipeline presence:** INDIRECT (pipelines use `tts_selector`)
- **Schema updates:** tool-level `input_schema` only
- **Skills / docs mention:** limited/implicit (no dedicated repo skill update beyond generic TTS skills)
- **Compose/render usage:** N/A (TTS asset generation)
- **Verification commands:**
  - `python3 -m pytest tests/contracts/test_fish_speech_tts_contract.py -q`
  - With a running Fish Speech server: call `fish_speech_tts` with `server_url`/`api_key`.
- **Risk level:** MEDIUM (external server dependency + new optional deps `requests`, `ormsgpack`)
- **What would be required to make it MORE real:** add a guarded live test when `FISH_SPEECH_BASE_URL` is set.

### 3) ComfyUI workflow override contract (workflow_json/path/patches)
- **Classification:** REAL (implemented + tested)
- **Evidence files:**
  - `tools/_comfyui/client.py` (patching + artifact discovery)
  - `tests/contracts/test_comfyui_backend.py` asserts override fields exist on all ComfyUI tools
- **Invocation:** via `comfyui_image` / `comfyui_video` / `comfyui_audio` inputs
- **Verification:** `python3 -m pytest tests/contracts/test_comfyui_backend.py -q`
- **Risk level:** MEDIUM (correctness depends on ComfyUI workflow JSON shapes)

### 4) HyperFramesCompose robustness + GPU encode option + auto composition scaffolding
- **Classification:** REAL (code changes inside an invoked tool)
- **Evidence files:**
  - `tools/video/hyperframes_compose.py`
  - Invocation path: `tools/video/video_compose.py` routes `render_runtime == "hyperframes"` to `HyperFramesCompose().execute()`
- **Key behavior changes (examples):**
  - Adds `gpu` option and NVENC detection
  - Normalizes relative `output_path` to absolute (avoid cwd mismatch)
  - Computes duration-based render timeout
  - Best-effort loads `projects/<id>/artifacts/scene_plan.json` to scaffold richer compositions
- **How invoked:** `video_compose` -> `_compose_hyperframes(...)` -> `HyperFramesCompose.execute(...)`
- **Verification command:** `python3 -m pytest tests/qa/test_08_end_to_end.py -q` (if it covers compose), otherwise run targeted unit tests if present
- **Risk level:** HIGH (large diff in a central compose tool; behavior depends on local Node/npm/hyperframes)
- **Notes:** Contract-level verification exists; full correctness requires an actual render on a machine with HyperFrames installed.

### 5) “Asymmetric” playbook + pipeline compatibility
- **Classification:** PARTIAL (style playbook is real; channel strategy docs are docs-only)
- **Evidence files:**
  - Style playbook: `styles/asymmetric.yaml`
  - Pipeline wiring: `pipeline_defs/animated-explainer.yaml`, `pipeline_defs/animation.yaml`, `pipeline_defs/cinematic.yaml` add `asymmetric` under `compatible_playbooks.also_works`
  - Channel materials: `channels/asymmetric/**` (strategy/templates)
- **How invoked:**
  - Runtime style: by selecting playbook `asymmetric` (loaded via `styles/playbook_loader.py`)
  - Channel strategy/templates: manual human/agent reference only
- **Verification command:** `python3 -c "from styles.playbook_loader import load_playbook; print(load_playbook('asymmetric')['meta']['name'])"`
- **Risk level:**
  - Style playbook: MEDIUM (depends on schema looseness and renderer support)
  - Channel docs: LOW

### 6) Pipeline manifest schema expansion (category + production_modes)
- **Classification:** REAL (schema changes are present) but RISKY (looser contracts can mask errors)
- **Evidence files:** `schemas/pipelines/pipeline_manifest.schema.json`
- **What changed:** adds `documentary` category and optional `production_modes[]` objects
- **How invoked:** schema validation paths that use this file
- **Verification command:** run schema validation if the repo has a validator; otherwise: `python3 -m pytest tests/contracts/test_phase3_contracts.py -q`
- **Risk level:** MEDIUM

### 7) Playbook schema loosened (more permissive)
- **Classification:** REAL (schema changes are present)
- **Evidence files:** `schemas/styles/playbook.schema.json`
- **What changed:** removes enums / allows additionalProperties / allows string-or-array for `colors.primary` and `colors.accent`
- **Risk level:** MEDIUM (less strict validation increases silent acceptance of typos)

### 8) Additional helper scripts / utilities
- `lib/archive_project.sh`
  - **Classification:** REAL utility, but not wired (manual script)
  - **Invocation:** manual CLI
  - **Risk:** LOW
- `lib/verify_asset.py`
  - **Classification:** DEAD_CODE (not referenced by any pipeline/tool in this fork diff)
  - **Evidence:** no repo references besides itself
  - **Risk:** LOW (until wired; then becomes MEDIUM/HIGH depending usage)
- `run_analysis.py`
  - **Classification:** REAL utility, but not wired
  - **Risk:** LOW

## Local Uncommitted Changes (Working Tree)

These diffs are **not** part of the committed fork-vs-upstream delta, but they affect what actually runs locally right now.

### A) Dependency naming + status overrides removed (ffmpeg/ffprobe tools)
- **Observed files (unstaged):**
  - `tools/analysis/audio_energy.py`
  - `tools/analysis/audio_probe.py`
  - `tools/analysis/composition_validator.py`
  - `tools/capture/screen_recorder.py`
  - `tools/audio/acestep_music.py`
  - `tools/base_tool.py`
- **Classification:** PARTIAL / UNVERIFIED (uncommitted)
- **Why risky:** changes tool availability reporting and dependency contracts; could change selector routing.
- **Suggested verification:** include these changes in `python3 -m pytest tests -q` results (see `40_verification_results.md`).

### B) VideoStitch / VideoTrimmer behavior tweaks
- **Observed files (unstaged):**
  - `tools/video/video_stitch.py` (adds new encode params like preset/target_fps/target_resolution)
  - `tools/video/video_trimmer.py` (capabilities list change)
- **Classification:** PARTIAL / UNVERIFIED (uncommitted)
- **Why risky:** input schema and docs may not match behavior; could be silently ignored by callers.

