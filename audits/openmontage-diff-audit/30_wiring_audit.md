# Architecture Wiring Audit (Diff vs upstream)

This audit answers, for each changed feature:
1) Discoverable? (`tools/tool_registry.py`)
2) Invoked by any pipeline? (`pipeline_defs/*.yaml` + director skills)
3) Artifact schema updated? (`schemas/artifacts/*.schema.json` etc)
4) Reviewer knows how to check it? (`skills/meta/reviewer.md` and pipeline directors)
5) Compose/render uses it? (`video_compose`, Remotion/HyperFrames)
6) Test coverage exists?
7) Could an agent believe it exists while runtime ignores it? (hallucination risk)

## ComfyUI backend (comfyui_image / comfyui_video / comfyui_audio / comfyui_wan_video)
1. **Discoverable?** YES
   - `ToolRegistry.discover()` walks the `tools` package and registers concrete `BaseTool` subclasses.
   - Tools are implemented as `BaseTool` subclasses: `tools/graphics/comfyui_image.py`, `tools/video/comfyui_video.py`, `tools/audio/comfyui_audio.py`, `tools/video/comfyui_wan_video.py`.
2. **Invoked by any pipeline?** INDIRECT
   - Pipelines use `image_selector` / `video_selector` (see multiple `pipeline_defs/*.yaml`).
   - Selectors auto-discover providers by capability; ComfyUI providers declare `capability="image_generation"` / `"video_generation"`.
   - `comfyui_audio` is `capability="music_generation"` but there is **no** generic music selector; it must be called explicitly by stage logic.
3. **Artifact schema updated?** NO dedicated global schema changes in this commit.
4. **Reviewer knows how to check it?** PARTIAL
   - Contract tests exist.
   - No explicit reviewer skill change in this fork diff; verification relies on tool-level `user_visible_verification` fields + pipeline director guidance.
5. **Compose/render uses it?** NO (generation tools, not render runtimes).
6. **Test coverage exists?** YES
   - `tests/contracts/test_comfyui_backend.py`.
7. **Hallucination risk?** MEDIUM
   - Risk mode: docs/skills may imply “ComfyUI works” but runtime silently routes away when the server isn’t reachable (selectors filter candidates).
   - `comfyui_audio` is especially at risk of being “claimed” but unused unless a pipeline explicitly calls it.

## Fish Speech TTS provider (fish_speech_tts)
1. **Discoverable?** YES (`tools/audio/fish_speech_tts.py` is a `BaseTool`)
2. **Invoked by any pipeline?** INDIRECT
   - Pipelines call `tts_selector`.
   - `TTSSelector` auto-discovers `capability="tts"` providers; Fish Speech declares that capability.
3. **Artifact schema updated?** NO
4. **Reviewer knows how to check it?** PARTIAL
   - Contract tests exist.
5. **Compose/render uses it?** N/A
6. **Test coverage exists?** YES (`tests/contracts/test_fish_speech_tts_contract.py`)
7. **Hallucination risk?** MEDIUM
   - Risk mode: tool is discoverable, but will be unavailable if Fish server/deps are missing; selectors will fall back.

## HyperFramesCompose changes (render runtime)
1. **Discoverable?** YES (`tools/video/hyperframes_compose.py` tool)
2. **Invoked by any pipeline?** YES
   - Via `video_compose` when `edit_decisions.render_runtime == "hyperframes"`.
3. **Artifact schema updated?** NO (behavioral change inside tool)
4. **Reviewer knows how to check it?** YES-ish
   - `video_compose` has explicit governance checks around `render_runtime` stability and logs.
5. **Compose/render uses it?** YES (it *is* the HyperFrames render path)
6. **Test coverage exists?** UNKNOWN / PARTIAL
   - No dedicated unit tests in this fork diff; end-to-end QA tests may cover it (`tests/qa/test_08_end_to_end.py` changed).
7. **Hallucination risk?** LOW/MEDIUM
   - The tool is definitely invoked when runtime is set, but machines without HyperFrames installed will fail/route away.

## “Asymmetric” playbook
1. **Discoverable?** YES
   - Playbooks are loaded by `styles/playbook_loader.py` from `styles/*.yaml`.
2. **Invoked by any pipeline?** YES (optional)
   - Pipelines list it under `compatible_playbooks.also_works`.
3. **Artifact schema updated?** YES
   - `schemas/styles/playbook.schema.json` is loosened, which affects validation of `styles/asymmetric.yaml`.
4. **Reviewer knows how to check it?** PARTIAL
   - No reviewer update specific to asymmetric; relies on playbook-defined quality rules + manual review.
5. **Compose/render uses it?** YES INDIRECT
   - Used by render tools that bridge playbook → CSS vars (e.g., HyperFramesCompose style bridge).
6. **Test coverage exists?** NO explicit tests for the new playbook.
7. **Hallucination risk?** MEDIUM
   - Risk mode: playbook exists but renderer may not honor every field; schema looseness increases silent acceptance.

## Pipeline manifest schema expansion
1. **Discoverable?** YES (schema file)
2. **Invoked by any pipeline?** YES if validators reference it
3. **Artifact schema updated?** YES (this is a schema)
4. **Reviewer knows how to check it?** PARTIAL
5. **Compose/render uses it?** INDIRECT (governance/validation)
6. **Test coverage exists?** LIKELY (contract tests exist in `tests/contracts/test_phase3_contracts.py`, changed in this commit)
7. **Hallucination risk?** LOW
   - It’s either used by validation or it isn’t; not a “claimed-but-ignored” feature so much as a governance surface.

## lib/verify_asset.py
1. **Discoverable?** NO (not a tool, not imported)
2. **Invoked by any pipeline?** NO evidence
3. **Artifact schema updated?** NO
4. **Reviewer knows how to check it?** NO evidence
5. **Compose/render uses it?** NO
6. **Test coverage exists?** NO
7. **Hallucination risk?** HIGH (utility docstring implies pipeline usage, but runtime does not call it)

## Local uncommitted diffs (dependency/status + VideoStitch/Trimmer)
- These changes are **not** wired through any pipeline definitions directly; they affect behavior only because the working tree differs from `HEAD`.
- Hallucination risk is HIGH in conversations (“it supports X”) because the committed code does not include these changes and they may be absent for other users/clones.

