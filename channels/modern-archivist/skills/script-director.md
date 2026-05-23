# Modern Archivist Script Director

Use this director for the `script` stage.

## Mission

Convert `research_packet` into `artifacts/episode.json` that follows the channel schema and is ready for narration, media planning, and Remotion rendering.

## Inputs

- `artifacts/research_packet.json`

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

## Success criteria

- `artifacts/episode.json` exists and validates against the episode schema or documents any intentional schema gap.
- Estimated narration duration fits the target.
- Every scene has a visual slot and state tag.
- Factual lines link back to research claim/source IDs.
- Human approval is obtained before audio generation.
