# Audio Post Director — broadcast-explainer

You are the audio-post agent. Your job is to normalize all raw WAV sections,
concatenate them, and produce `artifacts/audio_timing.json`.

## Steps

### 1. Normalize each section to -14 LUFS

```bash
for f in s01_hook s02_scale s03_secrecy s04_community s05_political s06_punchline; do
  ffmpeg -y -i assets/audio/${f}_raw.wav \
    -af loudnorm=I=-14:TP=-1.0:LRA=11 \
    assets/audio/${f}.wav \
    -loglevel error
done
```

If loudnorm clips (`TP` exceeded), retry with `-14` → `-16` LUFS and document the
deviation in `audio_timing.json` under a `notes` field.

### 2. Measure section durations

```bash
for f in s01_hook s02_scale s03_secrecy s04_community s05_political s06_punchline; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/audio/${f}.wav)
  echo "$f $dur"
done
```

### 3. Build concat list and concatenate

Use absolute paths to avoid ffmpeg treating paths as relative to the list file:

```bash
PROJ=$(pwd)
cat > /tmp/concat_audio.txt << EOF
file '${PROJ}/assets/audio/s01_hook.wav'
file '${PROJ}/assets/audio/s02_scale.wav'
file '${PROJ}/assets/audio/s03_secrecy.wav'
file '${PROJ}/assets/audio/s04_community.wav'
file '${PROJ}/assets/audio/s05_political.wav'
file '${PROJ}/assets/audio/s06_punchline.wav'
EOF
ffmpeg -y -f concat -safe 0 -i /tmp/concat_audio.txt assets/audio/narration_full.wav -loglevel error
```

### 4. Write `artifacts/audio_timing.json`

Compute cumulative start times from section durations. Validate that
`total_duration_seconds` is within 0.1s of the actual `narration_full.wav` duration
(check with ffprobe).

Section IDs must match `script.json` `sections[].id` exactly.

```json
{
  "version": "1.0",
  "total_duration_seconds": 54.94,
  "sections": [
    { "id": "s01_hook",      "start": 0.0,    "end": 3.855,  "duration": 3.855  },
    { "id": "s02_scale",     "start": 3.855,  "end": 17.229, "duration": 13.374 },
    { "id": "s03_secrecy",   "start": 17.229, "end": 32.322, "duration": 15.093 },
    { "id": "s04_community", "start": 32.322, "end": 39.938, "duration": 7.616  },
    { "id": "s05_political", "start": 39.938, "end": 48.576, "duration": 8.638  },
    { "id": "s06_punchline", "start": 48.576, "end": 54.938, "duration": 6.362  }
  ]
}
```

## Pass Condition

- All `assets/audio/{section_id}.wav` exist
- `assets/audio/narration_full.wav` exists
- `artifacts/audio_timing.json` exists and validates against `schemas/artifacts/audio_timing.schema.json`
- `narration_full.wav` duration within 0.1s of `audio_timing.json` `total_duration_seconds`
- For each section: `end >= start` and `abs(duration - (end - start)) < 0.01`

Verify section consistency before writing:
```python
for s in sections:
    assert s["end"] >= s["start"], f"{s['id']}: end ({s['end']}) < start ({s['start']})"
    assert abs(s["duration"] - (s["end"] - s["start"])) < 0.01, \
        f"{s['id']}: duration {s['duration']} != end-start {s['end']-s['start']:.3f}"
```

## Report Format

When complete, report:
- pass/fail
- Files written
- Total duration
- Any loudnorm deviation (if target was lowered from -14 to -16 LUFS)
