---
name: text-to-speech
description: |
  Generate speech audio across OpenMontage TTS providers. Use when: (1) Creating narration, voiceovers, or spoken samples, (2) Choosing between Fish Speech, Piper, HeyGen, ElevenLabs, Google, or OpenAI TTS, (3) Converting speaker directions into delivery controls, (4) Working with inline performance tags for Fish Speech, (5) Generating local or API-backed speech assets.
metadata:
  openclaw:
    requires:
      env: []
---

# Text-to-Speech

This skill explains how to choose and drive TTS inside OpenMontage.

## Provider Defaults

Use these defaults unless the user has already approved a specific provider:

- `fish_speech_tts`: best local expressive narration, strongest when the script uses inline formatting and tags
- `piper_tts`: local CPU fallback for drafts and zero-cost offline work
- `google_tts`: strongest localization coverage
- `elevenlabs_tts`: premium cloud narration
- `openai_tts`: lightweight cloud fallback
- `mcp__heygen__*`: standalone HeyGen Starfish audio flow when those MCP tools are available

## Fish Speech First

Fish is not plain TTS. It is designed to respond to **inline bracketed performance instructions** embedded directly in the text.

Examples:

```text
[low voice] The route looks simple. [short pause] [emphasis] That is the trap.
[whisper] It feels like convenience.
[professional broadcast tone] The platform owns the route to users.
```

Fish supports both short tags and free-form natural-language tags. Complete reference in `docs/FISH_SPEECH.md`.

Key tags by category:

- **Pacing:** `[short pause]`, `[pause]`, `[long pause]`
- **Register:** `[low voice]`, `[soft voice]`, `[loud voice]`, `[whispering]`
- **Breath/reaction:** `[sigh]`, `[inhale]`, `[clears throat]`, `[gasp]`
- **Emotion:** `[excited]`, `[angry]`, `[sad]`
- **Emphasis:** `[emphasis]`
- **Open-domain:** `[professional broadcast tone]`, `[speaking with quiet urgency]`, `[declarative, no hesitation]`, `[slightly ironic, controlled]`

For Asymmetric channel narration, read `docs/FISH_SPEECH.md#asymmetric-narrator-mode-delivery-profiles` before tagging. Each narrator mode (Subject, Cartographer, Operator, Skeptic, Realist) has a defined delivery profile. Using only weight tags (`[low voice]`, `[pause]`) throughout a full video produces monotonous output — vary delivery by section.

The core rule:

**When using Fish, convert `speaker_directions` into sparse inline tags before synthesis.**

## CRITICAL: Never Prepend Raw speaker_directions as a Tag

Do NOT do this:

```python
# WRONG — causes malformed chunks and truncation detection failure
tagged = f"[{speaker_directions}] {narration_text}"
```

`speaker_directions` are multi-sentence prose (50+ words). When passed as a bracket prefix, `split_sentences` splits them mid-tag, creating unclosed `[` fragments. Fish Speech receives e.g. `[Subject mode — warm but restrained.` as its entire chunk and generates near-zero audio. The truncation guard then fires on every chunk.

Do this instead — convert directions to 1-3 short Fish tags inline:

```python
# CORRECT — translate directions to sparse Fish tags embedded in the narration
text = "In 1956, an engineer named Bill Fair... [pause] Their system worked. [low voice] The problem is what it became."
result = selector.execute({"text": text, "provider": "fish_speech", ...})
```

If no Fish tags have been embedded in the narration yet, pass the raw narration text with no prefix — plain prose generates better audio than a malformed tag block:

```python
# ACCEPTABLE for baseline audio — no tags is better than a broken tag
result = selector.execute({"text": narration_text, "provider": "fish_speech", ...})
```

## Fish Best Practices

1. Put the tag immediately before the phrase it should affect.
2. Use pauses at clause boundaries, not every sentence.
3. Prefer a few sharp tags over a dense wall of markup.
4. Keep the script semantically close to the approved subtitle text.
5. Tune the tags first if the read sounds flat.

Good:

```text
The most valuable software gate is not code. [emphasis] It is permission. [short pause]
[low voice] The strange part is that most of this power does not feel like power.
```

Bad:

```text
[serious][ominous][deep][slow][cinematic] The app store controls the route.
```

Detailed Fish guidance lives in [FISH_SPEECH.md](/home/pop/OpenMontage/docs/FISH_SPEECH.md).

## CRITICAL: Fish Speech Truncation Trap

**Every section longer than ~30 seconds MUST use chunking. Skipping this causes silent truncation at 47.5s regardless of text length.**

Fish Speech's default `max_new_tokens=1024` caps output at ~47.5 seconds. A 286-word section will be silently cut at 47.5s with no error. The tool even flags this as a `duration_cluster_48s` warning — if you see all sections coming out exactly 47.5s, chunking is off.

### Always call via `tts_selector`, never raw curl or direct API

Raw curl calls against the Fish Speech server will always truncate because they bypass the tool's chunking logic. Use `tts_selector` with chunking explicitly enabled:

```python
from tools.audio.tts_selector import TTSSelector
selector = TTSSelector()
result = selector.execute({
    "text": tagged_text,
    "provider": "fish_speech",
    "output_path": "path/to/section.mp3",
    "format": "mp3",
    "max_new_tokens": 4096,             # TOP LEVEL — NOT nested. Default 1024 truncates.
    "chunking": {
        "enabled": True,
        "threshold_seconds": 30,        # chunk anything estimated > 30s
        "target_chunk_seconds_min": 20,
        "target_chunk_seconds_max": 35,
    },
})
```

### Duration sanity check after batch generation

After generating a batch, always verify durations are proportional to word count:

```python
import subprocess
dur = float(subprocess.run(
    ['ffprobe','-v','error','-show_entries','format=duration',
     '-of','default=noprint_wrappers=1:nokey=1', path],
    capture_output=True, text=True).stdout.strip())
# Rule of thumb: ~2.5 words/sec narration pace
# 200 words → expect ~80s. If you see 47.5s, chunking failed.
```

If every section is exactly 47.5s — stop. Fix chunking before continuing.

### GPU memory discipline

Fish Speech S2-Pro occupies ~22 GB VRAM. Always unload it before starting ACE-Step, ComfyUI, or any other GPU tool. Failure causes OOM on the next tool with no warning:

```bash
# Kill Fish Speech server before starting next GPU tool
pkill -f "python.*main.py.*18188" || true
# Verify GPU is clear before proceeding
nvidia-smi --query-compute-apps=pid,used_memory,name --format=csv,noheader
```

## OpenMontage Workflow

For narration work:

1. Use `tts_selector` unless the user explicitly wants a specific provider.
2. Generate one section sample first — verify duration is proportional to word count.
3. Approve voice, pacing, and tag behavior.
4. Then batch the remaining sections with chunking enabled.
5. After batch: verify all durations, update `narration_manifest.json`.

If selecting Fish:

- prefer `preferred_provider="fish_speech"`
- always use `tts_selector` with `chunking.enabled=True` for sections > 30s
- always set `fish_speech.max_new_tokens=4096` (never rely on the default)
- ensure the Fish local server is already running and healthy at `/v1/health`
- expect S2-Pro to use ~22 GB VRAM — unload before starting any other GPU tool

## HeyGen Starfish

If HeyGen MCP tools are available, they are still valid for standalone TTS tasks:

- `mcp__heygen__list_audio_voices`
- `mcp__heygen__text_to_speech`

HeyGen auth:

```bash
export HEYGEN_API_KEY=...
```

## Quick Heuristics

- expressive local narration with delivery markup: Fish Speech
- fully offline draft narration with no GPU: Piper
- multilingual production narration: Google TTS
- premium cloud narration: ElevenLabs
- lightweight cloud fallback: OpenAI TTS

When using Fish, the formatting is part of the performance.
