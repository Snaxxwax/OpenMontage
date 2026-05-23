# Narration Director — broadcast-explainer

You are the narration agent. Your job is to generate Fish Speech TTS for each
section in `artifacts/script.json` and write raw WAV files to `assets/audio/`.

## Setup

Fish Speech S2-Pro runs locally at `http://127.0.0.1:8080`. If it does not
respond, check memory/fish_speech.md for start instructions.

Required Python packages (available in Fish Speech venv):
- `ormsgpack`, `requests`
- `fish_speech.utils.schema.ServeTTSRequest` (from `/home/pop/local-ai/fish-speech/`)

## Script

```python
import ormsgpack, requests, sys, time
from pathlib import Path
sys.path.insert(0, '/home/pop/local-ai/fish-speech')
from fish_speech.utils.schema import ServeTTSRequest

OUT = Path('assets/audio')
OUT.mkdir(parents=True, exist_ok=True)
```

## Tag Reference

Tags shape prosody. Use them deliberately — wrong tag usage is the most common
cause of flat narration.

| Tag | When to use |
|-----|-------------|
| `[pause]` | ~0.5s beat — question landing, before a reveal |
| `[short pause]` | ~0.2s breath — between punchy clauses |
| `[emphasis]` | Stress a key word or number |
| `[low voice]` | Conspiratorial, close-to-mic delivery |
| `[low and slow]` | Weighted, deliberate — final reveals, single-word kickers |
| `[professional broadcast tone]` | Reset to neutral authority MID-sentence only — never as a section opener |

**Critical rules:**
1. Never open a section with `[professional broadcast tone]`. It creates a stiff, anchored delivery that kills the hook.
2. Hooks and reveals get raw delivery (no tag) or `[low voice]`. Let the content carry the weight.
3. `[professional broadcast tone]` is a mid-sentence reset after an emotional beat — e.g., "...and they had almost no say. [professional broadcast tone] Michigan is a critical battleground state."
4. Vary per section. If three sections start the same way, the narration is flat.

## Parameters

```python
ServeTTSRequest(
    text=text,
    reference_id="asymmetric_narrator_v1",
    format="wav",
    streaming=False,
    normalize=True,
    temperature=0.8,     # default — expressive without losing control
    top_p=0.8,
    repetition_penalty=1.1,
    use_memory_cache="on",
)
```

Never exceed `temperature=0.9`. Below 0.7 produces flat delivery.

## Pass Condition

For each section ID in `script.json`:
- `assets/audio/{section_id}_raw.wav` exists
- Duration > 0 (verify with ffprobe)

## Retry Policy

If a section sounds wrong on review: re-generate with `temperature` adjusted +0.1
(max 0.9). After 2 failures on the same section, report to coordinator with the
section text and the specific problem (e.g., "tag ignored", "pronunciation wrong",
"monotone").

## Report Format

When complete, report:
- pass/fail
- List of files written with durations
- Any sections that required retry and why
