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

Use `video_compose` as the manifest-level render tool. Canonical runtime is Remotion / React, but `hyperframes_compose` must be considered and presented when HyperFrames is available. Do not switch between Remotion, HyperFrames, FFmpeg-only, image-to-video, WebGL, or canvas skeletal rigging unless the user explicitly approves a material runtime change.

## Pre-render checks

1. Verify all required artifacts exist.
2. Verify referenced local assets exist.
3. Verify narration audio exists and matches `audio_analysis` duration.
4. Verify no render prop requires network fetches.
5. Verify Modern Archivist constraints from `DESIGN.md` and `CHANNEL.md` are preserved.

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
