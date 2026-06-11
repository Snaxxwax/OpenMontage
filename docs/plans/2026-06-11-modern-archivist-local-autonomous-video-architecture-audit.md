# Modern Archivist Local Autonomous Video Architecture Audit

Date: 2026-06-11
Repo: `/home/pop/repos/openmontage-asymmetric`
Input: user-provided 2026 local autonomous video workflow report
Scope: determine what should change in the Modern Archivist / Failure Ledger channel package and what should be rejected or treated as optional infrastructure.

## Executive verdict

The local-first direction is strategically correct for Modern Archivist, but the pasted report should not be adopted as a literal architecture.

Recommended stance:

```text
Local-first, evidence-led, deterministic final assembly.
```

Meaning:
- Use local tools where they reduce cost, improve privacy, or create repeatable outputs.
- Keep Remotion as the canonical final assembler.
- Prefer real source footage, public artifacts, archived pages, product UI, filings, launch demos, and recreated evidence cards over synthetic video generation.
- Use ComfyUI / local diffusion as an optional source-asset provider, not as the backbone of the episode.
- Use local TTS only if it passes voice consistency and disclosure checks.
- Add AI disclosure and provenance review to publish prep.

Do not pivot the channel into “10–15 minutes of chained AI video clips.” That would weaken the evidence-cinema promise and increase the risk of low-trust AI-slop perception.

## Research grounding

External references checked:

- YouTube Blog, “How we’re helping creators disclose altered or synthetic content”
  - YouTube requires disclosure when realistic altered/synthetic media could be mistaken for a real person, place, scene, or event.
  - AI used for scripts, captions, minor production assistance, and clearly unrealistic content is generally not the same disclosure category.
  - YouTube is aligned with C2PA/content provenance work.
- YouTube Help, “Disclosing use of GenAI content”
  - Disclosure is required for photorealistic altered/generated people, places, events, or realistic fake scenes.
  - AI scripts, thumbnails, infographics, upscaling, sharpening, audio repair, captions, and own-voice dubbing are listed as cases that may not require disclosure by themselves.
  - Non-disclosure risk includes manual labels, removals, and YPP penalties.
- Wan2.2 official GitHub
  - Wan2.2 includes T2V-A14B, I2V-A14B, TI2V-5B, S2V-14B, and Animate-14B variants.
  - Official examples state A14B can require very high VRAM for native single-GPU runs; TI2V-5B is the consumer-GPU-oriented variant.
  - The repo emphasizes offload / dtype conversion / t5_cpu and cites under-9-minute 5-second 720P generation on a consumer GPU for the 5B path.
- ComfyUI Wan2.2 native workflow docs
  - ComfyUI supports Wan2.2 workflows and FP8 scaled model paths.
  - TI2V-5B can fit with native offloading on lower VRAM; 14B workflows use dual high/low-noise models and may need quantized/GGUF paths on constrained hardware.

## Claim reliability assessment

### Strong / useful claims

1. Local-first economics are real.
   - Local generation avoids per-call API costs and supports private iteration.
   - This matches the user’s RTX 3090 setup and OpenMontage’s free/local path.

2. VRAM is the main bottleneck for local video generation.
   - Correct. Modern video diffusion is VRAM-bound.
   - For this machine class, 24GB VRAM is useful but still forces careful model/precision choices.

3. ComfyUI as a local graph runner is a reasonable provider layer.
   - Correct, but it must remain a provider/helper, not the pipeline orchestrator.
   - OpenMontage architecture requires YAML/Markdown stage policy and registry-discoverable tools.

4. Audio must be segmented for long-form TTS quality.
   - Correct operational principle.
   - Long narration should be generated per section/paragraph, then loudness-normalized, concatenated, probed, and timed.

5. FFmpeg/pydub-style audio cleanup is valuable.
   - Correct, but aggressive silence removal can damage documentary pacing.
   - Modern Archivist should use silence shaping, not hyperactive jump-cut compression.

6. Local embeddings/deduplication can protect channel variety.
   - Useful, but a hard cosine threshold such as 0.6 should be treated as tunable and empirically calibrated.

### Overstated / risky claims

1. “Top-tier creators are shifting away from cloud” is not proven.
   - Treat as a trend hypothesis, not a fact.
   - Top channels often mix local tools, paid cloud tools, contractors, NLEs, and bespoke asset workflows.

2. “Uncensored / bypass filters” is the wrong operating frame.
   - The channel should optimize for editorial control, privacy, cost, and repeatability, not bypassing safety systems.
   - Corporate/product-failure documentaries must stay rights-aware and disclosure-aware.

3. “No watermarks, no content filters, no limits” is incomplete.
   - Open-source model licenses, platform policies, source-media rights, impersonation rules, and disclosure duties still apply.

4. Wan2.2 14B on 24GB is not a universal safe assumption.
   - Official examples show A14B can be very heavy without offload/quantization.
   - ComfyUI FP8/GGUF paths may make it practical, but the pipeline should not depend on 14B as a guaranteed local path.

5. “YouTube parser deboosts blur/synthetic distortion” is plausible but not sourced enough.
   - Treat this as a quality-risk hypothesis.
   - What we can enforce: visual QA rejects obvious synthetic shimmer, blur, face/hand warping, text glitches, and continuity errors because they hurt viewer trust.

6. Mocha AE / Premiere / Resolve plugins should not become canonical.
   - They are useful manual/pro tools, but they break the current free/local Remotion-first operating model unless explicitly added as optional post paths.

## Fit with current Modern Archivist architecture

Current architecture already points in the right direction:

- `channels/modern-archivist/pipeline.yaml` owns channel stage order.
- `styles/modern-archivist.yaml` owns identity and prompt contract.
- ComfyUI is referenced as saved-asset generation support, not final assembly.
- Remotion is the canonical deterministic renderer.
- Source footage / public artifacts are preferred over generic generated visuals.

The local-autonomy report reinforces the need for stronger contracts in five places:

1. Publish packet must include AI/provenance disclosure review.
2. TTS/audio stage must enforce sectioned generation, loudness, silence, and prosody QA.
3. Asset generation stage must explicitly classify local video diffusion as optional support visuals only.
4. Media/visual QA must reject synthetic artifacts that break trust.
5. Content collection should include local concept-repetition checks once enough episodes exist.

## Recommended architecture additions

### 1. Add `ai_disclosure_review` to the publish packet

Add fields such as:

```json
{
  "ai_disclosure_review": {
    "realistic_synthetic_media_present": false,
    "simulated_real_person_voice_or_likeness": false,
    "altered_real_event_or_place": false,
    "realistic_fake_scene": false,
    "youtube_disclosure_required": false,
    "rationale": "AI used for script assistance, evidence cards, and non-photorealistic UI recreations only.",
    "provenance_notes": [
      "List generated/recreated assets and source-footage rights notes."
    ]
  }
}
```

This belongs in Task 3 (`publish_packet.schema.json` + `youtube-metadata.md`).

### 2. Add local-autonomy policy to the channel source of truth

Rule wording:

```text
Modern Archivist is local-first but not synthetic-first. Local generation is used to reduce cost and improve repeatability. The editorial default is evidence cinema: real artifacts, public records, direct source footage when usable, recreated UI/documents when needed, and deterministic Remotion assembly. AI video diffusion is optional support B-roll only and must never replace the evidence chain.
```

This belongs in Task 1.

### 3. Strengthen audio/TTS contract

Add to audio/script director rules:

- Narration is generated in section-sized blocks, not one long pass.
- Each block must pass prosody/listening QA before concatenation.
- Long silences are shaped intentionally; silence removal must preserve documentary pauses before reveals.
- Final narration should be loudness-normalized and probed.
- Any cloned/non-original voice path must carry consent/provenance and disclosure review notes.

This belongs in Task 5 or the audio stage if a separate packet is later created.

### 4. Add synthetic-media artifact rejection rules

For generated support visuals:

Reject when any of these appear:
- warped hands/faces/logos
- unreadable or hallucinated in-frame text presented as evidence
- shimmer or geometry crawl during camera motion
- fake documentary artifacts that could be mistaken for real records without labeling/recreation treatment
- mismatched company/product era details

Use generated visuals as:
- abstract atmosphere
- recreated UI clearly treated as reconstruction
- non-evidence transitions
- stylized case-board backgrounds
- support B-roll when source material cannot carry the beat

This belongs in Task 1 and Task 6 validation docs, and later in asset-generation skill work.

### 5. Add concept/visual repetition check as a future scale gate

Do not block Phase 1 on this. After 5–10 episodes, add a local episode-memory artifact that records:

- topic
- thesis
- villain/incentive pattern
- visual motif
- thumbnail formula
- title pattern
- opening contradiction

Then compare new episodes against recent history using deterministic text similarity or local embeddings. Treat scores as advisory until calibrated.

## What not to implement now

Do not add these to the current hardening task set:

- A Python LLM orchestrator that writes scripts end-to-end outside the pipeline.
- A ComfyUI autonomous generation loop that promotes assets automatically.
- A video-diffusion long-form assembly chain using final-frame continuation as the main visual engine.
- Resolve/Premiere/Mocha as required canonical steps.
- A hard, unsupported claim that YouTube deboosts AI blur via parser detection.
- A universal “local only” mandate that prevents using source footage or approved cloud tools when they are the best editorial path.

## Packet impact

Update existing packets rather than creating a new task:

- Task 1: add local-first / not synthetic-first source-of-truth language and generated-asset trust rules.
- Task 3: add AI disclosure/provenance review to `publish_packet` schema and `youtube-metadata.md`.
- Task 5: add sectioned TTS/prosody/silence shaping contract if audio/script docs are touched.
- Task 6: validate that the final channel contract does not treat ComfyUI/video diffusion as mandatory final-video infrastructure.

## Bottom line

The pasted report is valuable as a pressure test: it confirms the economic and operational value of local tools. But for Modern Archivist, the winning 2026 architecture is not “fully autonomous synthetic video.” It is a local-first evidence-cinema factory with deterministic final assembly, source-footage discipline, strong packaging, post-publish learning, and explicit provenance/disclosure review.
