# Modern Archivist Audio Director

Use this director for the `audio` stage.

## Mission

Generate `assets/audio/narration.wav` from the approved episode script using the configured local narration path, normally Fish Speech S2 Pro.

## Inputs

- `artifacts/episode.json`

## Tool contract

Use the OpenMontage tool/provider contract when available. Do not hide GPU lifecycle decisions inside orchestration scripts. If a local TTS service must be started, announce the tool/provider, check current status, and keep the action scoped to TTS.

## Output contract

- `assets/audio/narration.wav`
- Optional segment files under `assets/audio/<episode-id>/`
- Notes sufficient for `audio_analysis` to identify the canonical narration file.

## Quality bar

- Calm documentary delivery.
- No unexplained voice/model switch.
- No clipping, truncation, doubled lines, or wrong order.
- Duration matches script estimate closely enough for scene timing.

## Verification

Run ffprobe or equivalent validation. Record duration, sample rate, channels, and any warnings in stage notes or the downstream artifact.
