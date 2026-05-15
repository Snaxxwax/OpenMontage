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

Fish S2 accepts bracketed tags placed immediately before the text they affect. Tags apply from that point until the next tag or end of sentence. They can appear anywhere mid-sentence to shift delivery from that word forward.

### Complete S2 Tag Reference

**Breathing and reactions**

| Tag | Effect |
|-----|--------|
| `[sigh]` | Expressive exhale — use after a stark fact or a bleak reveal |
| `[inhale]` | Audible breath in — use before a major reveal or a pivot sentence |
| `[exhale]` | Audible breath out |
| `[gasp]` | Sharp intake — use at genuine surprise moments |
| `[panting]` | Heavy rapid breathing — rarely needed in documentary |
| `[clears throat]` | Throat-clear before speaking — use to reset after a dense passage |

**Pacing**

| Tag | Effect |
|-----|--------|
| `[short pause]` | Clause boundary beat — most common pacing tool |
| `[pause]` | Full beat pause — reserve for genuine load-bearing moments |
| `[long pause]` | Extended silence — use only at absolute maximum-weight moments |

**Voice register**

| Tag | Effect |
|-----|--------|
| `[whispering]` | Hushed, breathy — for private-briefing moments |
| `[soft voice]` | Quiet, gentle — for consequence/aftermath lines |
| `[low voice]` | Deeper register, restrained — for weight and gravity |
| `[loud voice]` | Raised volume — use to create energy contrast |
| `[shouting]` | Full volume — almost never appropriate for documentary |

**Emotion**

| Tag | Effect |
|-----|--------|
| `[excited]` | High energy — use sparingly to spike urgency at leverage reveals |
| `[angry]` | Harsh, forceful — for lines naming extraction or structural harm |
| `[sad]` | Heavy, downcast — for consequence lines about structural loss |

**Vocal sounds (use sparingly)**

| Tag | Effect |
|-----|--------|
| `[laughing]` | Full laughter |
| `[chuckling]` | Quiet, contained laugh — can work for bitter irony |
| `[groan]` | Discomfort or exasperation |

**Open-domain descriptions**

S2 is trained on open-ended descriptions, not a fixed keyword list. Any natural language description that reads like a stage direction to an actor generalizes — including novel combinations not in any example list.

```text
[professional broadcast tone]
[speaking slowly, almost hesitant]
[dead tired, end of a very long shift]
[voice rough from crying, trying to sound normal]
[speaking with quiet urgency]
[pitch up]
[declarative, no hesitation]
[slightly ironic, controlled]
[clipped, no emotion, reading from a document]
[reading a verdict]
[the way someone talks when they already know the answer]
[like explaining something obvious to someone who should know better]
[flat affect, post-shock]
[building to something, not quite there yet]
[pressing a point without raising the voice]
```

Use open-domain when the preset tags don't capture the specific shade of delivery needed. Describe what an actor would feel or what the character knows — not what the voice should sound like technically.

### Combination Patterns

**Chaining tags** — place multiple tags in sequence to layer effects. Each tag adds to or overrides the previous.

```text
[soft voice] I wasn't sure what to say. [long pause] [loud voice] But then it hit me.
[low voice] The system is not broken. [short pause] [emphasis] It is working exactly as designed.
```

**Physical + emotion pairing** — combining a body state with an emotional state produces stronger results than either alone:

```text
[panting] [angry] I've been running for twenty minutes and nothing changed.
[whispering] [sad] Don't move. I just need a second.
[shouting] [angry] I told you this would happen!
[clears throat] [professional broadcast tone] Let's go back to the beginning.
```

**Mid-sentence shift** — tags can appear anywhere inside a sentence to shift delivery from that word forward, not just at sentence boundaries:

```text
The route looks simple. [pause] The leverage [emphasis] is hidden inside it.
One company makes that decision. [short pause] [low voice] No appeal. No review. No election.
```

**Register ramp** — use a sequence of register tags across a passage to build or release tension:

```text
[professional broadcast tone] The system has three layers.
[short pause] DNS. TLS. DDoS filtering.
[short pause] [low voice] All three pass through one company.
[pause] [emphasis] One company.
```

### Constraints and Rules

1. **A tag requires text to follow it.** Do not place a tag on its own line with no following content. `[sigh]` on a blank line generates nothing.

2. **Voice selection matters more than tag wording** in some cases. Different reference voices respond with different intensity to identical tags. If a tag is not working, try a simpler tag or adjust the reference audio before stacking more tags.

3. **Start simple, layer only when needed.** A single well-placed `[sigh]` or `[long pause]` can transform a line. Add more only when the simpler version is genuinely insufficient — not as insurance.

4. **Tags apply forward, not backward.** A tag shifts delivery from its position to the next tag or end of sentence. Place it where the delivery change should begin.

5. **Language match.** Tags can be written in any of ~80 supported languages to match the script's language. English tags work for English narration.

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

## Asymmetric Narrator Mode Delivery Profiles

The Asymmetric narrator uses five modes. Each requires a different delivery profile. Using the same tag set throughout a 13-minute video produces monotonous output — the cloudflare-chokepoint-test render is the documented failure case.

**Subject mode** — events, character moments, timeline, named actors making decisions

Tone: controlled, precise, measured. The gravity of named decisions.
Primary tags: `[low voice]`, `[pause]`, `[emphasis]`
Avoid: energy tags, `[excited]`, `[loud voice]`
```text
[low voice] On August 5th, 2019, a website disappeared. [pause]
Not taken down by a court. [short pause] Not removed by a government. [short pause] Gone in minutes.
```

**Cartographer mode** — mapping the system, showing structure, node-by-node

Tone: clear, authoritative, slightly faster. Explains structure without threat framing.
Primary tags: `[professional broadcast tone]` (open-domain), `[short pause]` at nodes, `[emphasis]` on chokepoint names
Avoid: `[low voice]` — this mode explains, it doesn't threaten. Save weight for later.
```text
[professional broadcast tone] Every HTTPS request passes through three layers. [short pause]
TLS encryption. [short pause] DNS resolution. [short pause] DDoS filtering. [short pause]
[emphasis] Cloudflare sits at all three.
```

**Operator mode** — naming the leverage point, "here's where the asymmetry is"

Tone: direct, sharp, briefly elevated energy. This is the payoff of the mechanism section — the moment the viewer gets the answer. It should feel different from what preceded it.
Primary tags: `[inhale]` before the reveal sentence, `[emphasis]` on the mechanism word, then `[short pause]` to let it land
Open-domain option: `[speaking with quiet urgency]`
```text
[inhale] The chokepoint is not the hosting. [short pause] [emphasis] It is the DDoS shield.
Every site that cannot absorb a volumetric attack has no alternative. [short pause]
[low voice] That is the gate.
```

**Skeptic mode** — comparing stated incentives to actual incentives

Tone: slight ironic distance, controlled edge. The contrast between "what they said" and "what they did" IS the tag.
Primary tags: `[soft voice]` on the stated/official position, plain voice on the contradiction, `[sigh]` at an obvious gap
Open-domain option: `[slightly ironic, controlled]`
```text
[soft voice] Cloudflare says it only acts when content is clearly illegal. [pause]
The Daily Stormer was not illegal. [short pause] 8chan was not illegal. [short pause]
[sigh] Neither were the sites deplatformed in 2022.
```

**Realist mode** — consequence, who wins, who pays, what changes

Tone: direct, unsentimental, declarative. Not `[low voice]` — this mode is about clarity, not weight. The weight comes from the facts, not the delivery.
Primary tags: `[emphasis]` on the number or fact proving the consequence, `[short pause]` to separate the win from the loss
Open-domain option: `[declarative, no hesitation]`
```text
[declarative, no hesitation] One private company now makes content moderation decisions
that affect 20% of the internet. [short pause] It has no appeals process. [short pause]
[emphasis] No regulatory oversight. [short pause] No election.
```

---

### The Monotone Trap

**This is the documented failure mode for Asymmetric narration.**

Using only weight tags (`[low voice]`, `[pause]`, `[short pause]`, `[emphasis]`) throughout a full video produces a flat, undifferentiated result. Every line sounds equally ominous. The viewer cannot tell when something is more important than something else.

Weight tags create valleys. Valleys only work if there are peaks.

The fix: vary delivery intentionally across sections. The presence of a lighter, more direct register in Cartographer and Realist sections makes the `[low voice]` sections in Subject and Operator modes land harder by contrast.

**Delivery variation check before batch generation:**
1. Is each section tagged for its correct narrator mode profile?
2. Is the leverage reveal section (Operator mode) distinctly different from the mechanism section (Cartographer mode)?
3. Is the payoff section (Realist mode) declarative and clear, not uniformly ominous?
4. Are `[pause]` tags used only at genuine load-bearing moments — no more than 3-4 per section?
5. Is there at least one tag variation in each section that differs from the preceding section?

If the answer to any of these is no, adjust the tags before generating audio.

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
