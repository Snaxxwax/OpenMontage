# Modern Archivist Audio Director

Use this director for the `audio` stage.

## Mission

Generate high-quality narration audio from the approved episode script with strict quality and generation guidelines. Prioritize deterministic, section-based audio generation that preserves documentary pacing and narrative intent.

## Inputs

- `artifacts/episode.json`

## Audio Generation Principles

1. Section-Based Generation
   - Narration MUST be generated in section-sized blocks, NOT one continuous pass.
   - Each section (paragraph, scene transition, evidence reveal) gets individual generation.
   - Preserve documentary pauses and reveal timing intentionally.

2. Prosody and Listening Quality
   - Each audio block must pass subjective listening quality check.
   - Validate speakability, natural flow, and Modern Archivist voice consistency.
   - Reject sections with unnatural prosody, robotic artifacts, or incorrect emphasis.
   - Long silences are intentional documentary techniques, NOT generation errors.

## Tool Contract

Use `tts_selector` as the required manifest-level tool name. Prefer the Modern Archivist narrator voice via local providers when approved reference material is available:

1. `fish_speech_tts` with `reference_id: asymmetric_narrator_v1` when the Fish Speech service is running.
2. `f5_tts` with explicit `reference_audio_path` and `reference_text` when operating local-first without the Fish Speech service.
3. API/Piper fallbacks only after documenting the provider switch and voice-quality risk.

Additional requirements:
- Do not hide GPU lifecycle/model switches or human approval.
- Keep generation decisions explicit in notes/reviews.
- If a local TTS service must be started, announce the tool/provider, check current status.

## Audio Processing Rules

1. Generation Strategy
   - Use deterministic section start/end timestamps from script.
   - Generate each section separately.
   - Concatenate generated sections preserving original script timing.

2. Audio Normalization
   - Loudness-normalize to target LUFS (-16 LUFS default).
   - Match target narrative duration within ±5 seconds.
   - Ensure no clipping or distortion.

3. Segment Management
   - Main narration audio: `assets/audio/narration.wav`
   - Optional per-section segments: `assets/audio/<episode-id>/section_001.wav`
   - Annotate generated segments with reference script positioning

## Non-Negotiable Rules
- No voiceovers or simulations without consent documentation.
- Voice must match Modern Archivist persona consistently.
- Avoid generic business language or hype.

## Voice Provision/Requirements
- Record explicit consent/provenance for any cloned/synthetic voice.
- Explicitly note voice generation method in AI disclosure review.
- Require human approval of voice for simulation.

## Output Contract

- `assets/audio/narration.wav`
- Optional segment files under `assets/audio/<episode-id>/`
- Provide audio analysis file tracking canonical details

## Quality Bar

- Calm, authoritative documentary delivery.
- No unexplained voice/model switches.
- No clipping, truncation, repeated lines, or incorrect order.
- Duration matches script intent and timing targets.

## Verification

1. Run `audio_probe` or equivalent validation.
2. Record:
   - Duration
   - Sample rate
   - Number of channels
   - Prosody quality metrics
   - Silence/pause intentions
3. Document any manual edits or corrections

## Provenance Tracking

For every generated narration, capture:
- TTS tool used
- Voice model/reference
- Generation parameters
- Segment-level quality metadata

## Guideline Support

- Treat voice generation as documentary support, not the editorial first priority.
- Approve as documentary tool for evidence-first content.

## Retention

- Remove per-section files after episode preparation is complete.
- Keep main narration audio in project archives.
