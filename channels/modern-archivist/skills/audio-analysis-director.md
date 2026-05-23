# Modern Archivist Audio Analysis Director

Use this director for the `audio_analysis` stage.

## Mission

Create `artifacts/audio_analysis.json` so Remotion receives normalized, deterministic timing and amplitude props. Remotion must not perform live audio analysis during render.

## Inputs

- `assets/audio/narration.wav`

## Output contract

`audio_analysis` should include:

- `audio_path`
- `duration_seconds`
- `word_timings[]` when available, normalized to seconds
- `amplitude_samples[]` at a declared sample rate/window
- `silence_ranges[]` if detected
- `method`, tool versions, and verification notes

## Rules

1. Use deterministic local analysis.
2. Do not mutate narration audio here.
3. Do not fetch network resources.
4. Keep values compact enough for Remotion props.

## Success criteria

- `artifacts/audio_analysis.json` exists.
- Duration matches `audio_probe` or equivalent media-probe output.
- Amplitude samples and word timing formats are stable.
- The render stage can consume the artifact without analyzing audio again.
