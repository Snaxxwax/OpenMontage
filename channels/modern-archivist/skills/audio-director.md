# Modern Archivist Audio Director

Use this director for the `audio` stage.

## Mission

Generate `assets/audio/narration.wav` from the approved episode script using the registry-discoverable `tts_selector` path and the approved Modern Archivist voice profile.

## Inputs

- `artifacts/episode.json`

## Tool contract

Use `tts_selector` as the required manifest-level tool name. When the local Modern Archivist voice is available, route through the registry-discoverable `fish_speech_tts` provider with `reference_id: asymmetric_narrator_v1`; otherwise announce the provider switch for approval before generation. Do not hide GPU lifecycle decisions inside orchestration scripts. If a local TTS service must be started, announce the tool/provider, check current status, and keep the action scoped to TTS.

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

Run `audio_probe` or equivalent validation. Record duration, sample rate, channels, and any warnings in stage notes or the downstream artifact.
