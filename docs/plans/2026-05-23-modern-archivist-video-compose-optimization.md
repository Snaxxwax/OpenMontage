# Modern Archivist video_compose Optimization Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make the official `video_compose` route render Modern Archivist episodes without registry bypasses, while fixing stale audio prop paths and reducing Remotion iteration time.

**Architecture:** Keep orchestration in `channels/modern-archivist/pipeline.yaml` and director skills. Python changes stay limited to `VideoCompose` routing/props materialization and deterministic validation. Remotion changes stay inside the existing channel package adapter and composer project; no ad hoc render scripts become the canonical path.

**Tech Stack:** Python `BaseTool` (`tools/video/video_compose.py`), pytest, Remotion 4 / React 18, channel package files under `channels/modern-archivist/`, and `ffprobe`/Remotion CLI verification.

---

## Current findings

1. `remotion-composer/src/Root.tsx` already registers `id="ModernArchivist"` at lines 304-312.
2. `tools/video/video_compose.py` has a registry map at lines 643-652, but it does not include `"modern-archivist": "ModernArchivist"`.
3. The official Remotion path calls `_get_composition_id(renderer_family)` at `tools/video/video_compose.py:1347-1348`, so `renderer_family="modern-archivist"` currently fails before reaching the valid Remotion composition.
4. Modern Archivist audio is split between canonical project audio (`projects/<id>/assets/audio/narration.wav` / `channels/modern-archivist/pipeline.yaml:22`) and stale public audio props (`modern-archivist/narration.wav`, `modern-archivist/audio/stadia-autopsy-narration.wav`).
5. `channels/modern-archivist/remotion/src/ModernArchivistComposition.tsx:24` can already load absolute audio via `resolveAsset()` when `audio_src` starts with `/`, and relative public audio via `staticFile()` otherwise.
6. Remotion’s public dir currently contains Modern Archivist audio and puppet assets under `remotion-composer/public/modern-archivist/`; copying this public tree adds avoidable iteration overhead and keeps stale audio easy to reference.

## Non-goals

- Do not replace Remotion with HyperFrames for Modern Archivist.
- Do not add a Python pipeline orchestrator or make Python choose creative/render policy.
- Do not remove the runtime governance rule that `render_runtime` must be explicit.
- Do not optimize by degrading visual identity, removing the puppet, or disabling audio in final renders.

---

### Task 1: Add a failing renderer-family routing test

**Objective:** Prove that `video_compose` recognizes `renderer_family="modern-archivist"` and maps it to the existing Remotion composition.

**Files:**
- Modify: `tests/tools/test_documentary_governance.py`
- Test: `tests/tools/test_documentary_governance.py`

**Step 1: Write failing test**

Add near `test_documentary_renderer_family_maps_to_remotion()`:

```python
def test_modern_archivist_renderer_family_maps_to_remotion_composition():
    assert VideoCompose._get_composition_id("modern-archivist") == "ModernArchivist"
```

**Step 2: Run test to verify failure**

Run:

```bash
pytest tests/tools/test_documentary_governance.py::test_modern_archivist_renderer_family_maps_to_remotion_composition -q
```

Expected: FAIL with `ValueError: Unknown renderer_family 'modern-archivist'`.

**Step 3: Commit only after Task 2 passes**

Do not commit this failing test alone unless using strict TDD checkpoints.

---

### Task 2: Register Modern Archivist in video_compose renderer map

**Objective:** Route official `video_compose` Remotion renders to the `ModernArchivist` composition.

**Files:**
- Modify: `tools/video/video_compose.py:643-652`
- Test: `tests/tools/test_documentary_governance.py`

**Step 1: Implement the minimal map change**

Update `RENDERER_FAMILY_MAP`:

```python
RENDERER_FAMILY_MAP = {
    "explainer-data": "Explainer",
    "explainer-teacher": "Explainer",
    "cinematic-trailer": "CinematicRenderer",
    "documentary-montage": "CinematicRenderer",
    "product-reveal": "Explainer",
    "screen-demo": "Explainer",
    "presenter": "TalkingHead",
    "animation-first": "Explainer",
    "modern-archivist": "ModernArchivist",
}
```

**Step 2: Run targeted test**

Run:

```bash
pytest tests/tools/test_documentary_governance.py::test_modern_archivist_renderer_family_maps_to_remotion_composition -q
```

Expected: PASS.

**Step 3: Run adjacent governance tests**

Run:

```bash
pytest tests/tools/test_documentary_governance.py tests/tools/test_hyperframes_compose.py::test_video_compose_rejects_missing_render_runtime -q
```

Expected: PASS; missing/unknown runtime behavior remains blocked.

**Step 4: Commit**

```bash
git add tools/video/video_compose.py tests/tools/test_documentary_governance.py
git commit -m "fix: route modern archivist through video compose"
```

---

### Task 3: Add a channel render-contract test for official inputs

**Objective:** Lock the Modern Archivist compose contract: `render_runtime="remotion"`, `renderer_family="modern-archivist"`, and `ModernArchivist` Remotion ID.

**Files:**
- Modify: `tests/contracts/test_channel_package_boundary.py`
- Test: `tests/contracts/test_channel_package_boundary.py`

**Step 1: Write contract test**

Add a test that loads `channels/modern-archivist/package.yaml` and verifies:

```python
def test_modern_archivist_official_video_compose_contract():
    from tools.video.video_compose import VideoCompose

    assert VideoCompose._get_composition_id("modern-archivist") == "ModernArchivist"
```

If the file already imports YAML/package helpers, reuse them and also assert:

```python
assert package["entrypoints"]["remotion_composition"] == "ModernArchivist"
assert package["canonical_renderer"] == "remotion"
```

**Step 2: Run contract test**

Run:

```bash
pytest tests/contracts/test_channel_package_boundary.py::test_modern_archivist_official_video_compose_contract -q
```

Expected: PASS.

**Step 3: Commit**

```bash
git add tests/contracts/test_channel_package_boundary.py
git commit -m "test: lock modern archivist compose contract"
```

---

### Task 4: Normalize Modern Archivist render props before invoking Remotion

**Objective:** Ensure official `video_compose` can consume an episode-shaped Modern Archivist artifact and provide Remotion props with current audio paths, not stale public paths.

**Files:**
- Modify: `tools/video/video_compose.py`
- Test: `tests/tools/test_documentary_governance.py` or new `tests/tools/test_modern_archivist_video_compose.py`

**Step 1: Write failing unit test for audio normalization**

Create a test with a temp project audio file:

```python
def test_modern_archivist_props_use_project_audio_absolute_path(tmp_path):
    audio = tmp_path / "assets" / "audio" / "narration.wav"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"RIFF....WAVEfmt ")

    edit_decisions = {
        "renderer_family": "modern-archivist",
        "render_runtime": "remotion",
        "episode_id": "demo",
        "title": "Demo",
        "duration_seconds": 3,
        "audio_src": "modern-archivist/narration.wav",
        "sections": [],
    }

    props = VideoCompose._prepare_remotion_props(
        edit_decisions,
        {"narration_audio_path": str(audio)},
    )

    assert props["audio_src"] == str(audio.resolve())
```

**Step 2: Expected initial failure**

Run:

```bash
pytest tests/tools/test_documentary_governance.py::test_modern_archivist_props_use_project_audio_absolute_path -q
```

Expected: FAIL because `_prepare_remotion_props` does not exist or does not rewrite stale audio.

**Step 3: Add narrow helper**

In `VideoCompose`, add a deterministic helper used by `_remotion_render` before writing `.remotion_props.json`:

```python
@staticmethod
def _prepare_remotion_props(composition_data: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    props = json.loads(json.dumps(composition_data))
    if props.get("renderer_family") == "modern-archivist":
        narration = (
            inputs.get("narration_audio_path")
            or inputs.get("audio_path")
            or ((inputs.get("audio_analysis") or {}).get("audio_path"))
        )
        if narration and Path(narration).exists():
            props["audio_src"] = str(Path(narration).resolve())
    return props
```

Then replace the current `_remotion_render` deep copy:

```python
props = self._prepare_remotion_props(composition_data, inputs)
```

Keep existing `cuts` absolute path conversion and `themeConfig` logic after this helper.

**Step 4: Run test**

Run:

```bash
pytest tests/tools/test_documentary_governance.py::test_modern_archivist_props_use_project_audio_absolute_path -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/video/video_compose.py tests/tools/test_documentary_governance.py
git commit -m "fix: normalize modern archivist remotion props"
```

---

### Task 5: Make stale public audio references fail pre-render for Modern Archivist

**Objective:** Prevent future renders from silently using `remotion-composer/public/modern-archivist/narration.wav` or old episode-specific public audio.

**Files:**
- Modify: `tools/video/video_compose.py`
- Modify: `channels/modern-archivist/skills/render-director.md`
- Test: `tests/tools/test_documentary_governance.py`

**Step 1: Write failing validation test**

```python
def test_modern_archivist_rejects_stale_public_audio_without_current_audio(tmp_path):
    result = VideoCompose().execute({
        "operation": "render",
        "edit_decisions": {
            "version": "1.0",
            "renderer_family": "modern-archivist",
            "render_runtime": "remotion",
            "episode_id": "demo",
            "title": "Demo",
            "duration_seconds": 3,
            "audio_src": "modern-archivist/narration.wav",
            "sections": [],
        },
        "asset_manifest": {"assets": []},
        "output_path": str(tmp_path / "out.mp4"),
    })
    assert not result.success
    assert "stale public audio" in (result.error or "").lower()
```

**Step 2: Implement narrow guard**

Add a validation branch before `_remotion_render` runs:

```python
if renderer_family == "modern-archivist":
    audio_src = edit_decisions.get("audio_src")
    has_current_audio = any(
        inputs.get(key)
        for key in ("narration_audio_path", "audio_path")
    ) or bool((inputs.get("audio_analysis") or {}).get("audio_path"))
    if audio_src in {
        "modern-archivist/narration.wav",
        "modern-archivist/audio/stadia-autopsy-narration.wav",
    } and not has_current_audio:
        return ToolResult(
            success=False,
            error=(
                "Modern Archivist render blocked: stale public audio path detected. "
                "Pass narration_audio_path or audio_analysis.audio_path from the project workspace."
            ),
        )
```

Place it where `edit_decisions` and `renderer_family` are already available, before render dispatch.

**Step 3: Update render director**

In `channels/modern-archivist/skills/render-director.md`, add to Pre-render checks:

```markdown
6. Verify `audio_src` resolves to the current project narration file (`assets/audio/narration.wav` or `audio_analysis.audio_path`), not a stale `remotion-composer/public/modern-archivist/*.wav` fixture.
```

**Step 4: Run tests**

Run:

```bash
pytest tests/tools/test_documentary_governance.py::test_modern_archivist_rejects_stale_public_audio_without_current_audio -q
pytest tests/contracts/test_pipeline_governance.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/video/video_compose.py channels/modern-archivist/skills/render-director.md tests/tools/test_documentary_governance.py
git commit -m "fix: block stale modern archivist audio props"
```

---

### Task 6: Remove public audio from the hot Remotion public path

**Objective:** Shrink Remotion public-copy overhead by keeping generated narration in project workspaces instead of `remotion-composer/public`.

**Files:**
- Modify/delete generated fixture files only after confirming they are not required by tests:
  - `remotion-composer/public/modern-archivist/narration.wav`
  - `remotion-composer/public/modern-archivist/audio/stadia-autopsy-narration.wav`
- Modify: `.gitignore` if needed
- Test: `tests/contracts/test_channel_package_boundary.py`, Remotion smoke render

**Step 1: Check whether files are tracked**

Run:

```bash
git ls-files remotion-composer/public/modern-archivist/narration.wav remotion-composer/public/modern-archivist/audio/stadia-autopsy-narration.wav
```

Expected: Ideally no output. If tracked, remove with `git rm`; if untracked, delete locally.

**Step 2: Add ignore rule for generated Modern Archivist audio**

If no existing rule covers it, add:

```gitignore
remotion-composer/public/modern-archivist/*.wav
remotion-composer/public/modern-archivist/audio/*.wav
```

Do not ignore puppet PNGs unless a separate asset packaging decision is made.

**Step 3: Remove stale generated audio**

Run:

```bash
rm -f remotion-composer/public/modern-archivist/narration.wav
rm -f remotion-composer/public/modern-archivist/audio/stadia-autopsy-narration.wav
```

**Step 4: Verify public dir size**

Run:

```bash
du -sh remotion-composer/public
```

Expected: Size drops materially from the current ~43 MB public tree if the audio was the bulk.

**Step 5: Run tests**

Run:

```bash
pytest tests/contracts/test_channel_package_boundary.py tests/tools/test_documentary_governance.py -q
```

Expected: PASS.

**Step 6: Commit**

```bash
git add .gitignore remotion-composer/public/modern-archivist || true
git commit -m "chore: remove stale modern archivist public audio"
```

---

### Task 7: Add a fast Modern Archivist Remotion smoke render path

**Objective:** Verify official routing without paying the full CSS-heavy/audio render cost on every iteration.

**Files:**
- Modify: `tests/tools/test_documentary_governance.py` or create `tests/render/test_modern_archivist_smoke.py`
- Optional modify: `tools/video/video_compose.py` to support `options.remotion_extra_args`

**Step 1: Write a short smoke fixture**

Use a minimal 1-2 second episode with no audio, `renderer_family="modern-archivist"`, `render_runtime="remotion"`, and one simple section. The smoke test should call the official `VideoCompose().execute()` path, not a direct `npx remotion render` bypass.

**Step 2: Keep it opt-in if it invokes Remotion CLI**

Mark the test so normal unit runs do not spend time rendering:

```python
import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("OPENMONTAGE_RENDER_SMOKE") != "1",
    reason="Set OPENMONTAGE_RENDER_SMOKE=1 to run Remotion smoke renders",
)
```

**Step 3: Smoke command**

Run manually:

```bash
OPENMONTAGE_RENDER_SMOKE=1 pytest tests/render/test_modern_archivist_smoke.py -q
```

Expected: PASS, output MP4 exists, `VideoCompose` data reports `operation="remotion_render"`.

**Step 4: Commit**

```bash
git add tests/render/test_modern_archivist_smoke.py
git commit -m "test: add modern archivist compose smoke render"
```

---

### Task 8: Add Remotion iteration flags for development renders

**Objective:** Speed development iteration while preserving final-render quality defaults.

**Files:**
- Modify: `tools/video/video_compose.py`
- Test: `tests/tools/test_documentary_governance.py` or `tests/tools/test_hyperframes_compose.py`

**Step 1: Write command-construction test**

Refactor command building into a helper if needed:

```python
def test_remotion_dev_options_append_render_flags():
    cmd = VideoCompose._build_remotion_command(
        composer_dir=Path("/repo/remotion-composer"),
        composition_id="ModernArchivist",
        output_path=Path("/tmp/out.mp4"),
        props_path=Path("/tmp/props.json"),
        inputs={"options": {"remotion_dev_fast": True, "concurrency": 4}},
    )
    assert "--concurrency" in cmd
    assert "4" in cmd
```

**Step 2: Implement safe options**

Support only explicit, bounded flags:

```python
options = inputs.get("options", {})
concurrency = int(options.get("concurrency", 0) or 0)
if concurrency > 0:
    cmd.extend(["--concurrency", str(min(concurrency, 8))])

if options.get("muted") is True:
    cmd.append("--muted")
```

Do not default final renders to muted. Use muted only for explicit preview/smoke iteration.

**Step 3: Update render director**

Add a note:

```markdown
Development previews may pass explicit render options such as `concurrency` or `muted`; final deliverables must render with audio unless the approved episode is silent.
```

**Step 4: Run tests**

Run:

```bash
pytest tests/tools/test_documentary_governance.py tests/tools/test_hyperframes_compose.py::test_video_compose_rejects_unknown_render_runtime -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/video/video_compose.py channels/modern-archivist/skills/render-director.md tests/tools/test_documentary_governance.py
git commit -m "feat: expose safe remotion iteration options"
```

---

### Task 9: Profile render bottlenecks with a repeatable benchmark artifact

**Objective:** Replace anecdotal “0.8 fps” observations with a before/after benchmark that separates public-copy, audio, and CSS scene cost.

**Files:**
- Create: `tests/render/bench_modern_archivist_render.py` or `scripts/render/bench_modern_archivist_render.py`
- Create/modify: `docs/rendering/modern-archivist-performance.md`

**Step 1: Write benchmark utility with explicit inputs**

The utility should accept:

```bash
python scripts/render/bench_modern_archivist_render.py \
  --props projects/<id>/artifacts/render_props.modern_archivist.json \
  --output /tmp/modern-archivist-bench.mp4 \
  --concurrency 4 \
  --mode final
```

It must record:
- public dir size (`du -sh remotion-composer/public`)
- render duration wall-clock
- Remotion-reported fps if available
- output duration and streams via `ffprobe`
- whether audio was enabled/muted
- git SHA and Remotion package version

**Step 2: Keep utility deterministic**

The script must not choose renderer/runtime or mutate project artifacts. It only runs an already selected explicit Remotion command or official `video_compose` call with explicit inputs.

**Step 3: Run before/after benchmark**

Run after Tasks 1-8:

```bash
python scripts/render/bench_modern_archivist_render.py \
  --props projects/humane-ai-pin-autopsy/artifacts/render_props.modern_archivist.json \
  --output /tmp/modern-archivist-bench.mp4 \
  --concurrency 4
```

Expected: Generates a JSON/markdown benchmark entry and a valid MP4.

**Step 4: Commit**

```bash
git add scripts/render/bench_modern_archivist_render.py docs/rendering/modern-archivist-performance.md
git commit -m "chore: add modern archivist render benchmark"
```

---

### Task 10: Optimize CSS-heavy scene rendering only after benchmark evidence

**Objective:** Improve frame render speed without changing the channel’s visual language.

**Files:**
- Inspect/possibly modify:
  - `channels/modern-archivist/remotion/src/ModernArchivistComposition.tsx`
  - `channels/modern-archivist/remotion/src/components/ScrollingCodeBackdrop.tsx`
  - `channels/modern-archivist/remotion/src/components/ArchivistPuppet.tsx`
  - `channels/modern-archivist/remotion/src/components/MediaContainer.tsx`
- Test: Remotion smoke benchmark and visual QC frames

**Step 1: Profile component suspects**

Create benchmark variants that disable one feature at a time through explicit props:
- `debug_disable_backdrop`
- `debug_disable_puppet`
- `debug_disable_media`
- `debug_disable_audio`

Do not ship these as creative options; use them only for profiling.

**Step 2: Add guarded debug props**

In `ModernArchivistComposition`, gate expensive layers only if debug props are true:

```tsx
{!episode.debug_disable_backdrop ? <ScrollingCodeBackdrop layout={layout} /> : null}
{!episode.debug_disable_media ? <MediaContainer layout={layout} media={media} visualMode={visualMode} /> : null}
{!episode.debug_disable_puppet ? (
  <ArchivistPuppet ... />
) : null}
```

Add optional fields to `channels/modern-archivist/remotion/src/types.ts` if TypeScript requires it.

**Step 3: Benchmark each variant**

Run:

```bash
python scripts/render/bench_modern_archivist_render.py --props ... --variant no-backdrop
python scripts/render/bench_modern_archivist_render.py --props ... --variant no-puppet
python scripts/render/bench_modern_archivist_render.py --props ... --variant no-media
python scripts/render/bench_modern_archivist_render.py --props ... --variant muted
```

Expected: One or two dominant bottlenecks identified.

**Step 4: Apply only evidence-backed optimizations**

Likely safe optimizations:
- Memoize deterministic section/tag flattening if it is recomputed per frame expensively.
- Reduce number of DOM nodes in `ScrollingCodeBackdrop`.
- Prefer transform/opacity changes over layout-affecting CSS.
- Replace per-frame array scans with pre-indexed timeline segments only if benchmark shows state lookup cost matters.

Forbidden optimizations:
- Removing the puppet or channel frame from final output.
- Rasterizing the whole scene into static screenshots as the normal path.
- Changing renderer runtime without user approval.

**Step 5: Verify visual output**

Run:

```bash
OPENMONTAGE_RENDER_SMOKE=1 pytest tests/render/test_modern_archivist_smoke.py -q
python scripts/render/bench_modern_archivist_render.py --props projects/humane-ai-pin-autopsy/artifacts/render_props.modern_archivist.json --output /tmp/modern-archivist-final-bench.mp4 --concurrency 4
ffprobe -v error -show_streams -show_format /tmp/modern-archivist-final-bench.mp4
```

Expected: MP4 exists, has video and audio streams for final mode, no visual identity regression in sampled frames.

**Step 6: Commit**

```bash
git add channels/modern-archivist/remotion/src tests/render scripts/render docs/rendering
git commit -m "perf: optimize modern archivist remotion render path"
```

---

## Acceptance criteria

1. Official `VideoCompose().execute()` accepts `render_runtime="remotion"` and `renderer_family="modern-archivist"` and routes to Remotion composition `ModernArchivist`.
2. Missing or unknown `render_runtime` still fails; no silent runtime swaps are introduced.
3. Modern Archivist render props use the current project narration audio path, preferably absolute file path resolved by `resolveAsset()`, not stale public audio fixtures.
4. Stale `remotion-composer/public/modern-archivist/*.wav` paths are blocked unless a current project audio path is supplied and normalized.
5. Generated narration audio is not stored in `remotion-composer/public` as the canonical path.
6. A short opt-in smoke render verifies the official registry route.
7. A benchmark records render speed, public dir size, audio mode, output streams, and Remotion version before/after optimization.
8. Any CSS/DOM optimization is benchmark-backed and preserves Modern Archivist visual identity.

## Validation commands

Run before merge:

```bash
pytest tests/tools/test_documentary_governance.py -q
pytest tests/contracts/test_channel_package_boundary.py -q
pytest tests/contracts/test_pipeline_governance.py -q
OPENMONTAGE_RENDER_SMOKE=1 pytest tests/render/test_modern_archivist_smoke.py -q
python scripts/render/bench_modern_archivist_render.py --props projects/humane-ai-pin-autopsy/artifacts/render_props.modern_archivist.json --output /tmp/modern-archivist-bench.mp4 --concurrency 4
ffprobe -v error -show_streams -show_format /tmp/modern-archivist-bench.mp4
```

## Rollout risks

- If old project artifacts still contain `audio_src="modern-archivist/narration.wav"`, they will now block unless the render call supplies `narration_audio_path` or `audio_analysis.audio_path`. This is intentional; update artifacts or pass the canonical project audio path.
- Removing public audio may break one-off manual Remotion commands that relied on stale fixtures. Keep a small no-audio fixture for Studio if needed, but do not use it for pipeline renders.
- Remotion CLI flags vary by version. Confirm `--concurrency` and `--muted` against installed Remotion 4 before finalizing helper tests.
- Performance work can accidentally alter visual timing. Always compare frame samples from before/after renders.

## Recommended implementation order

1. Tasks 1-3: restore official routing and lock the contract.
2. Tasks 4-6: fix props/audio path and remove stale public audio from the hot path.
3. Tasks 7-9: add smoke and benchmark tools so iteration is measurable.
4. Task 10: optimize CSS-heavy components only after benchmark evidence identifies the bottleneck.
