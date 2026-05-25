# Modern Archivist Render Director

Use this director for the `render` stage.

## Mission

Render the approved Modern Archivist episode through registry-discoverable composition tools and create `artifacts/render_report.json`.

## Inputs

- `artifacts/episode.json`
- `artifacts/media_manifest.json`
- `artifacts/asset_manifest.json`
- `artifacts/audio_analysis.json`

## Runtime contract

Use `video_compose` as the manifest-level render tool. Remotion / React is the canonical final assembler for Modern Archivist, not a rule that every pixel must originate in Remotion. Declared mixed-runtime production is allowed and encouraged when it improves quality: HyperFrames may render approved segment assets, FFmpeg may provide probe/transcode/mux utility work, and Remotion assembles the final episode. Do not switch the approved final assembler, add a new visual paradigm (image-to-video, WebGL, canvas skeletal rigging), or downgrade to FFmpeg-only unless the user explicitly approves a material runtime change.

Remotion remains the canonical final renderer. Read `runtime_affinity` from `content_collection` and `media_manifest` as planning input and segment-routing guidance: Remotion handles final assembly, puppet timing, case-file scenes, receipts, source montage integration, and deterministic React/SVG/CSS scenes; HyperFrames may produce approved local segment assets for source-rich motion, website-to-video, recreated UI, or kinetic HTML/CSS sequences. Do not silently swap runtimes. Record a `render_runtime_selection` decision with options considered, rejected options, whether mixed-runtime segment rendering is part of the approved plan, and whether any HyperFrames segment was rendered as a local asset.

Development previews may pass explicit `video_compose` render options such as bounded `concurrency` or `muted=true` for faster iteration. Final deliverables must render with audio unless the approved episode is intentionally silent; never make muted output the default.

## Pre-render checks

1. Verify all required artifacts exist.
2. Verify referenced local assets exist, including staged `content_collection` assets and HyperFrames segment outputs.
3. Verify every `content_opportunity_ref` used by `episode` and `media_manifest` resolves to `artifacts/content_collection.json`.
4. Verify narration audio exists and matches `audio_analysis` duration.
5. Verify no render prop requires network fetches.
6. Verify Modern Archivist constraints from `DESIGN.md` and `CHANNEL.md` are preserved.
7. Verify `audio_src` resolves to the current project narration file (`assets/audio/narration.wav` or `audio_analysis.audio_path`), not a stale `remotion-composer/public/modern-archivist/*.wav` fixture.

## Output contract

`render_report` should include:

- input artifact paths and hashes or modification times
- runtime and composition name
- output video path
- duration, resolution, codec, and audio stream details
- `audio_probe` / media-probe result
- keyframe/self-review notes
- warnings or approved deviations

## Success criteria

- Final video file exists.
- `audio_probe` or an equivalent media probe validates video and audio streams.
- Duration matches the script/audio plan.
- Report records inputs and verification notes.
- No hidden network, provider, or runtime substitution occurred.

## Puppet Rendering Policy

### Sequencing

1. **Plan puppet visibility early.** Decide at scene-plan time whether each section uses `MONOLOGUE` layout (puppet visible) or `SOURCE_MONTAGE`/`FULLSCREEN` (puppet hidden). This drives the `characterCue.visible` flag.
2. **Render source-heavy plates first.** If the episode uses pre-rendered source clips, render/cache those before the final Remotion assembly pass.
3. **Puppet and captions in the final overlay pass.** Run the full puppet + captions + word-timing pass after narration and timing are locked. Do not render puppet before audio timing is final.

### Benchmark requirement

4. **Run benchmarks before changing timeouts or disabling the puppet.** If render time is the concern, run `bench_modern_archivist_render.py` with `--variant source-plate-only`, `--variant puppet-static`, and `--variant puppet-no-filters` to isolate which sub-path is the bottleneck before making a decision.
5. **No head-only puppet variants unless the user explicitly approves.** Replacing the full-body puppet with a head-only or face-only crop breaks the `rig_contract: full_body_layered` policy. Raise a critical review finding if this occurs.

### Debug flags (explicit use only)

These flags are available for benchmarking and debugging — not for production workarounds:

| flag | effect |
|------|--------|
| `debug_disable_puppet` | hide puppet entirely |
| `debug_puppet_static` | show puppet, no mouth/gesture animation |
| `debug_disable_puppet_mouth` | show puppet, freeze mouth |
| `debug_disable_puppet_filters` | disable drop-shadow/glow filters |
| `debug_disable_audio` | mute audio track |

Never set these flags in a production episode props without user approval.
