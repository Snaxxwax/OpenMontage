# Modern Archivist Script Director

Use this director for the `script` stage.

## Mission

Convert `research_packet` into `artifacts/episode.json` that follows the channel schema and is ready for narration, media planning, and Remotion rendering.

## Inputs

- `artifacts/research_packet.json`
- `artifacts/content_collection.json`

## Output contract

Produce `artifacts/episode.json` conforming to `channels/modern-archivist/schemas/episode.schema.json` when possible. It must contain narration, scene beats, timing estimates, visual state tags, and references back to research evidence.

## Voice

Dry, forensic, and precise. The Archivist should sound like a skeptical narrator opening a case file, not a hype channel. Use phrases that imply evidence handling: "the record says", "the promise was", "the failure mode was", "the receipt is".

Sound like you're following a trail, not teaching a class. Let the evidence feel dangerous. Use silence and short lines before major reveals.

## Long-form narration and local TTS guardrails

Modern Archivist is local-first, but long narration must not be generated as one uninterrupted TTS pass.

- Plan narration in section-sized blocks that can be generated, reviewed, and replaced independently.
- Preserve short intentional silences before major reveals; do not let silence removal flatten documentary tension into jump-cut pacing.
- Each narration block must be listenable for prosody, emphasis, pacing, and voice consistency before concatenation.
- Final narration must be loudness-normalized and probed by the audio/audio-analysis stages before render.
- Any cloned, synthetic, or non-original voice path must carry consent/provenance notes so publish_prep can complete `ai_disclosure_review` accurately.

**Good style examples:**
- "The demo looked harmless. That was the problem."
- "For a few weeks, everyone wanted to believe it."
- "Then the receipts started appearing."
- "The company did not fail because nobody understood the future. It failed because too many people did."
- "This was not a bug. It was the business model showing through."

**Bad style — never write this:**
- "In today's video we are going to talk about..."
- "First, let's define..."
- "This is an important topic because..."
- "To understand this, we need to go back to..."
- "There are many factors..."
- "Overall, it is clear that..."

## Cold Open Rules

The cold open is the only line of defense against the back button.

- Open with stakes, not context. The first 20 seconds must create an unanswered question.
- Acceptable cold open hooks: a bizarre failure nobody can explain yet; a company promise that aged terribly; a quote that sounds fake but is real; a product demo that reveals the whole lie; a strange artifact from an old forum, lawsuit, repo, ad, keynote, or leaked document; a contradiction between what the public was told and what actually happened.
- Do not start with definitions.
- Do not begin with "To understand this, we need to go back." Earn the flashback first.
- The cold open ends on a question or contradiction — not an answer.

## Narrative Structure

1. Cold open: the strange artifact or failure
2. Title sting: bold thesis line
3. Setup: what people thought this was
4. First crack: the first sign something was wrong
5. Incentives: who benefited from the illusion
6. Escalation: how the system got bigger than the truth
7. Evidence sequence: documents, demos, posts, timelines, contradictions
8. Reversal: the thing everyone missed
9. Collapse or consequence: what broke, who paid, what changed
10. Final thesis: what this reveals about the internet, tech, AI, or culture

## Retention Loop Rules

These are hard constraints, not suggestions:

### Quantitative Retention Guidelines

- **Words Per Minute (WPM)**:
  - Target: 130-150 WPM average
  - Peaks/valleys allowed: 90-180 WPM for specific dramatic moments
  - No more than 3 consecutive sentences above 180 WPM

- **Tension Introduction Cadence**:
  - Mandatory: Introduce a new tension element every 60-90 seconds
  - Tension types (must rotate):
    1. Money dynamics
    2. Power structures
    3. Ego/reputation
    4. Technological failure
    5. Systemic deception
    6. Unintended consequences

- **Section Ending Contract**:
  - Prohibited: Neutral summary endings
  - Required: Each section must end with one of:
    1. A revealing contradiction (mandatory escalation)
    2. An unexpected pivot
    3. A stakes-raising question
    4. A dramatic reversal

- **Visual State Transition**:
  - Mandatory visual mode change every 3-6 sections
  - No more than 2 consecutive sections in the same visual mode
  - Enforce visual rhythm: `case_file` → `source_montage` → `recreated_ui` → repeat

### Qualitative Retention Principles

- Plant unanswered questions before giving background.
- Delay the full explanation until the viewer understands why it matters.
- Avoid long neutral chronology unless each beat changes the viewer's understanding.
- Use evidence cards as payoff moments, not as visual filler.

### Retention Tracking

Each section MUST include:
- `narrative_phase`
- `retention_device`
- Explicit `estimated_duration_seconds`
- At least one `evidence_ref`

Violation of these rules requires human review and explicit override.

## Visual mapping

Every beat must map to one of the channel render modes:

- `STATE_MONOLOGUE`: Archivist on camera; framing, thesis, transitions.
- `STATE_DEEP_DIVE`: MediaContainer owns the frame; charts, documents, source receipts.
- `STATE_CRITICAL_ERROR`: pattern interrupt; failure, contradiction, shutdown, or decisive quote.

## Source-footage/artifact-first scripting

The `content_collection` packet is authoritative for visual feasibility. Script visual-dependent scenes around concrete visual opportunity entries and cite their opportunity IDs in scene metadata, media overlays, or notes. The cold open should use the strongest source footage, archived artifact, public video, or recreated digital artifact contradiction available in `content_collection`.

Do not write scenes around abstract ideas when the content_collection packet lacks visual material. If the packet marks `boring_visual_risk: high`, stop for operator review or narrow the angle before scripting. Document-only beats must be compressed into receipt moments or transformed into artifact scenes with crop, reveal, contradiction stamp, recreated UI, case-board motion, or quote punch. The script must remain source-footage/artifact-first rather than research-deck-first.

Each visual opportunity referenced in the script should preserve:

- opportunity IDs from `content_collection`;
- evidence refs from the research packet;
- intended visual mode and motion plan;
- whether the moment is evidence, allegation, finding, inference, or illustrative only.

## Success criteria

- `artifacts/episode.json` exists and validates against the episode schema or documents any intentional schema gap.
- Estimated narration duration fits the target.
- Every scene has a visual slot and state tag.
- Factual lines link back to research claim/source IDs.
- Human approval is obtained before audio generation.

## Retention-first episode contract

The canonical `episode.json` artifact is structured timeline/sections only; do not treat generic screenplay prose as the canonical render contract. Every new-format block should include `narrative_phase`, `retention_device`, `visual_mode`, `layout`, `color_state`, `character`, `narration`/`text`, `evidence_refs`, `media_overlay`, and `estimated_duration_seconds`. Default evidence-heavy body sections to full-screen editorial visuals, not a persistent host HUD. Red state is scarce: 3-12 seconds for critical-error interruptions unless a human explicitly approves a longer treatment. Every factual line must link to research claim/source IDs. Static source views must be transformed with motion plans: crop, reveal, highlight, quote extraction, graph link, or compression montage.
