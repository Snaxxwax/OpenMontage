# Modern Archivist render performance

This document records the measurement protocol for optimizing the Modern Archivist Remotion route. Do not optimize CSS/DOM components from anecdote alone; run the benchmark variants and compare report JSON.

## Benchmark command

```bash
python scripts/render/bench_modern_archivist_render.py \
  --props projects/<project-id>/artifacts/render_props.modern_archivist.json \
  --asset-manifest projects/<project-id>/artifacts/asset_manifest.json \
  --audio-path projects/<project-id>/assets/audio/narration.wav \
  --output /tmp/modern-archivist-bench.mp4 \
  --concurrency 4 \
  --port 3767 \
  --mode final
```

The script calls the official `VideoCompose().execute({operation: "render"})` route. Inputs must already declare:

- `render_runtime: "remotion"`
- `renderer_family: "modern-archivist"`

The script records:

- wall-clock render duration
- approximate rendered fps at 30 fps
- `remotion-composer/public` size
- whether audio was enabled or muted
- output duration and stream details from `ffprobe`
- Remotion package versions
- git SHA

## Profiling variants

Run variants only to identify bottlenecks; they are not creative options for final publication.

```bash
python scripts/render/bench_modern_archivist_render.py --props ... --output /tmp/ma-baseline.mp4 --concurrency 4 --variant baseline
python scripts/render/bench_modern_archivist_render.py --props ... --output /tmp/ma-muted.mp4 --concurrency 4 --variant muted --mode preview
python scripts/render/bench_modern_archivist_render.py --props ... --output /tmp/ma-no-backdrop.mp4 --concurrency 4 --variant no-backdrop --mode preview
python scripts/render/bench_modern_archivist_render.py --props ... --output /tmp/ma-no-puppet.mp4 --concurrency 4 --variant no-puppet --mode preview
python scripts/render/bench_modern_archivist_render.py --props ... --output /tmp/ma-no-media.mp4 --concurrency 4 --variant no-media --mode preview
python scripts/render/bench_modern_archivist_render.py --props ... --output /tmp/ma-no-audio.mp4 --concurrency 4 --variant no-audio --mode preview
```

Interpretation:

- `muted` / `no-audio` isolates audio mux/decoding cost.
- `no-backdrop` isolates the scrolling CSS/code backdrop.
- `no-puppet` isolates puppet layer and word-timing animation cost.
- `no-media` isolates evidence/media overlay rendering cost.

Only apply production optimizations to a component after the variant data shows it is a meaningful bottleneck.

## Current baseline notes

- The stale public Modern Archivist `.wav` fixtures have been removed from `remotion-composer/public`.
- Generated narration should remain in the project workspace and be passed as `narration_audio_path`, `audio_path`, or `audio_analysis.audio_path`.
- Final renders must include audio unless the approved episode is intentionally silent. Use muted/dev variants only for iteration and profiling.

## Smoke benchmark sample, 2026-05-24

Fixture: `/tmp/ma-smoke-props.json`, 1.267 seconds rendered, preview/muted, concurrency 2, 1920x1080.

| Variant | Wall clock | Approx FPS @30fps | Notes |
| --- | ---: | ---: | --- |
| baseline | 34.084s | 1.115 | Official `video_compose` route, no audio stream |
| no-backdrop | 26.903s | 1.413 | Fastest smoke variant; backdrop is a likely bottleneck candidate |
| no-puppet | 33.599s | 1.131 | Similar to baseline on smoke fixture |
| no-media | 30.407s | 1.250 | Mild improvement on smoke fixture |
| no-audio | 34.593s | 1.099 | Similar to baseline because smoke was already muted/no-audio |

Public dir size during the sample: 2.0 MiB. The sample is intentionally short and should be treated as harness verification plus directional evidence, not a replacement for a full episode benchmark.

After the first safe backdrop optimization (`repeatedArchiveText` hoisted out of per-frame render plus `willChange: "transform"`), the same short baseline measured 35.602s / 1.068 approx FPS. That short run does not prove a speedup; it verifies the optimized component still renders and keeps the benchmark ready for a longer episode-length measurement.
