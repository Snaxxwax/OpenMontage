# Fish Speech in OpenMontage

Fish Speech is the local high-control TTS path in OpenMontage.

Use it when we want:

- expressive narration driven by inline performance tags
- local generation on an NVIDIA GPU instead of a paid API
- fine-grained control over pauses, emphasis, volume, emotion, and delivery inside the line itself

The active OpenMontage tool is [fish_speech_tts.py](/home/pop/OpenMontage/tools/audio/fish_speech_tts.py), usually selected through [tts_selector.py](/home/pop/OpenMontage/tools/audio/tts_selector.py).

## Why Fish is Different

Most TTS systems treat narration as plain text plus a small set of global controls.
Fish S2 is different: it is meant to read **formatted inline performance instructions**.

That means the quality bar is different too:

- weak Fish prompt: plain script with no embedded guidance
- strong Fish prompt: script rewritten with localized `[tag]` cues that shape delivery phrase by phrase

For OpenMontage narration, this is the main rule:

**Do not pass script prose through Fish unchanged when the scene depends on tone. Convert speaker directions into inline tags first.**

## Tagging Model

Fish accepts bracketed natural-language tags directly inside the text.

Examples from the upstream Fish docs include:

- `[whisper]`
- `[pause]`
- `[short pause]`
- `[emphasis]`
- `[excited]`
- `[angry]`
- `[sigh]`
- `[laughing]`
- `[low voice]`
- `[volume up]`
- `[volume down]`
- `[professional broadcast tone]`
- `[whisper in small voice]`
- `[pitch up]`

The model also supports many free-form descriptions, not just a fixed shortlist.

## OpenMontage Writing Rules

When preparing Fish narration for OpenMontage:

1. Start from the approved script section text.
2. Read the section's `speaker_directions`.
3. Rewrite the spoken text with sparse inline tags.
4. Keep the words natural enough that the subtitle transcript still matches the script closely.

Good defaults:

- Put tags **before the phrase** they should affect.
- Use pauses at clause boundaries, not every sentence.
- Prefer one clear instruction over stacked micro-directions.
- Tag only the moments that matter to the beat.
- Keep the semantic wording of the script intact unless a rewrite is necessary for speakability.

## Recommended Patterns

### 1. Local emphasis

Use tags to sharpen one phrase rather than changing the whole paragraph.

```text
The most valuable software gate is not code. [emphasis] It is permission.
```

### 2. Clause timing

Use pauses to create documentary pacing.

```text
Before an app can reach your pocket, [short pause] someone has to approve the route.
```

### 3. Tone shifts

Use tone changes where the argument turns.

```text
The strange part is that most of this power does not feel like power. [low voice] It feels like convenience.
```

### 4. Global framing through repeated light tags

If a section should feel ominous or restrained, repeat a small number of compatible tags instead of one giant opening instruction.

```text
[low voice] The route looks simple. [short pause] [emphasis] The leverage is hidden inside it.
```

## Patterns to Avoid

Avoid these failure modes:

- tagging every sentence
- stacking many tags on the same phrase
- using tags as metadata instead of performance instructions
- rewriting the narration so heavily that subtitles and source script diverge
- relying only on a single opening tag for a long paragraph

Bad:

```text
[serious][ominous][cinematic][deep][slow][emotional] The app store controls the route.
```

Better:

```text
[low voice] The app store controls the route. [short pause] [emphasis] That is the lever.
```

## Converting Speaker Directions

OpenMontage scripts often carry directions like:

```text
Low, precise, and slightly ominous. Pause after "permission" and again before the final sentence.
```

That should become something like:

```text
[low voice] The most valuable software gate is not code. [emphasis] It is permission. [short pause]
Before an app can reach your pocket, someone has to approve the route, the payment, the update, the warning label, and sometimes even the sentence that tells you there is a cheaper way to pay.
[short pause] [low voice] The strange part is that most of this power does not feel like power. It feels like convenience. [emphasis] That is where the leverage is.
```

The goal is not maximal tagging. The goal is to preserve the approved script while making the intended performance legible to Fish.

## Operational Notes

- Fish S2-Pro is GPU-hungry. On a 24 GB card, leave headroom for inference, not just model load.
- The OpenMontage Fish tool refuses unsafe long single-shot requests by default.
- Long narration should go through `tts_selector`, which chunks long Fish generations and concatenates them.
- The current local server path is usually `http://127.0.0.1:8080`.
- Health check endpoint: `GET /v1/health` (returns `{"status":"ok"}`). Not `/health` or `/api/health`.

## Required tts_selector Parameters for Fish Speech

Always pass these when calling via `tts_selector`. Missing either will cause silent truncation or chunk failures.

```python
selector.execute({
    "text": tagged_text,
    "provider": "fish_speech",
    "output_path": "shared_studio/projects/<name>/assets/audio/<section>.mp3",
    "format": "mp3",
    "max_new_tokens": 4096,   # MUST be top-level. Default=1024 caps audio at ~47.5s.
    "chunking": {
        "enabled": True,          # MUST be True for any section > ~30s
        "threshold_seconds": 30,
        "target_chunk_seconds_min": 20,
        "target_chunk_seconds_max": 35,
    },
})
```

**Common mistakes:**
- Passing `max_new_tokens` nested inside a `"fish_speech": {}` dict — that key is not read by the tool
- Calling the Fish Speech server directly with `curl` — bypasses chunking and token limit, always truncates
- Not verifying output duration after generation — all sections at 47.5s means chunking or `max_new_tokens` failed
- Prepending raw `speaker_directions` as `f"[{directions}] {text}"` — directions are multi-sentence prose; `split_sentences` splits them mid-tag creating unclosed `[` fragments; Fish Speech generates near-zero audio and the truncation guard fires. Convert directions to 1-3 short inline Fish tags instead, or pass plain text with no prefix.

**After batch generation, always verify:**
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 section.mp3
# Rule of thumb: ~2.5 words/sec. 200 words → ~80s expected. 47.5s = truncation.
```

## Suggested Workflow

For narrated videos:

1. Generate one Fish sample for the first script section.
2. Listen for tone, pacing, and whether tag placement is doing real work.
3. Adjust the inline tags, not just the raw text.
4. Only then batch the rest of the narration.

## Where This Lives in the Pipeline

- Asset stage guidance: [asset-director.md](/home/pop/OpenMontage/skills/pipelines/explainer/asset-director.md)
- Provider setup and tradeoffs: [PROVIDERS.md](/home/pop/OpenMontage/docs/PROVIDERS.md)
- Tool implementation: [fish_speech_tts.py](/home/pop/OpenMontage/tools/audio/fish_speech_tts.py)
- Selector chunking path: [tts_selector.py](/home/pop/OpenMontage/tools/audio/tts_selector.py)
