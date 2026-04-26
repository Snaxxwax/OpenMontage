# Working Tree Cleanup Plan

## Modified files (staged in git index from prior commit, now dirty)

These are the 8 files showing `M` in `git status`. Each needs an explicit commit decision.

### Commit as-is (substantive changes, tests pass)

| File | Change summary | Status |
|------|---------------|--------|
| `tools/video/hyperframes_compose.py` | Fix `_cut_to_html` scene-comp guard to not swallow text_card/hero_title/callout | **COMMITTED** in this stabilization pass |
| `tools/video/video_stitch.py` | Modified in prior session (e2df3ef) | Review diff before committing |
| `tools/video/video_trimmer.py` | Modified in prior session | Review diff before committing |
| `tools/base_tool.py` | Modified in prior session | Review diff before committing |
| `tools/audio/acestep_music.py` | Modified in prior session | Review diff before committing |
| `tools/analysis/audio_energy.py` | Modified in prior session | Review diff before committing |
| `tools/analysis/audio_probe.py` | Modified in prior session | Review diff before committing |
| `tools/analysis/composition_validator.py` | Modified in prior session | Review diff before committing |

**Recommended action**: Run `git diff tools/` to inspect all changes, then commit as a single "chore: stabilization fixes" commit or group by tool category.

### Fix before committing

| File | Issue |
|------|-------|
| `projects/chip-factory-runs-world/assets/sample/compose_sample.sh` | Still uses broken YUV-space blend — missing `format=gbrp`. Fix before committing or mark as deprecated. |
| `projects/chip-factory-runs-world/assets/sample/render_overlay.js` | `spawnSync` for ffmpeg can fail silently in background; switch to `execSync`. Low priority since encoding is done. |

## Untracked directories

### `audits/` — KEEP, commit

All `.md` files in `audits/stabilization/` are stabilization documentation. Commit them with:
```
git add audits/
git commit -m "docs: add stabilization audit trail"
```

### `pipelines/` — REVIEW first

```
ls -la pipelines/
```
If it contains only generated/transient files, add to `.gitignore`. If it contains configuration or pipeline definitions, commit.

### `server.pid` — DO NOT COMMIT

This is a runtime PID file. Add to `.gitignore`:
```
echo "server.pid" >> .gitignore
```

## Binary artifacts (not in git, but on disk)

These mp4 files exist on disk and are the product of this session's work. They are not tracked by git (presumably covered by `.gitignore`).

| File | Keep? |
|------|-------|
| `sample_final.mp4` | **KEEP** — the working composite proof |
| `sc09_overlay_rendered_v2.mp4` | **KEEP** — the rendered overlay used in final composite |
| `footage_processed.mp4` | **KEEP** — re-encoded clean source |
| `sc09_overlay_fixed.mp4` | Can delete — intermediate step |
| `sc09_overlay_rendered.mp4` | Can delete — broken (wrong pix_fmt) |
| `sample_v1.mp4` through `sample_v4.mp4` | Can delete — failed compositing attempts |

To remove intermediates:
```bash
cd projects/chip-factory-runs-world/assets/sample
rm sc09_overlay_rendered.mp4 sc09_overlay_fixed.mp4 sample_v1.mp4 sample_v2.mp4 sample_v3.mp4 sample_v4.mp4
```

## QA test slow test gate (recommended follow-up)

Add to top of `tests/qa/test_05_video_compose.py` and `tests/qa/test_06_video_stitch.py`:
```python
import os, pytest
if not os.getenv("SLOW_TESTS"):
    pytest.skip("set SLOW_TESTS=1 to run ffmpeg integration tests", allow_module_level=True)
```
This prevents pytest CI hangs without removing the tests.
