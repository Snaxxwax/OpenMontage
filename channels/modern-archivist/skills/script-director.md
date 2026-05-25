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

## Structure

1. Cold open: the promise or contradiction.
2. Context: why people believed it could work.
3. Evidence: the decisions, incentives, and missing assumptions.
4. Failure mode: the point where the story becomes inevitable.
5. Autopsy: what the case reveals about markets, platforms, or institutions.

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
