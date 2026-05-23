# Modern Archivist Media Director

Use this director for the `media_manifest` stage.

## Mission

Create `artifacts/media_manifest.json`: a local, provenance-rich plan for all visual inputs used by the episode.

## Inputs

- `artifacts/episode.json`
- `artifacts/research_packet.json`

## Output contract

Produce a media manifest compatible with `channels/modern-archivist/schemas/media.schema.json` when possible. Include every required visual slot, local path or planned creation source, provenance, license/usage notes, and render-time props.

## Rules

1. No network fetches during Remotion render.
2. Every visual asset has provenance.
3. Use saved channel assets before generating new assets.
4. Differentiate factual media from illustrative graphics.
5. Do not choose ComfyUI generation here; only identify missing assets and creation requirements for the asset_generation stage.

## Visual language

Favor receipts: documents, timelines, charts, product screenshots, archived pages, quote cards, and failure-ledger UI elements. Preserve Modern Archivist palette and deterministic React components.

## Success criteria

- `artifacts/media_manifest.json` exists.
- Every scene visual slot has local media, inline deterministic data, or an explicit missing-asset requirement.
- All source media includes URL/publisher/license/retrieved-at when applicable.
- The asset_generation director can decide whether saved assets satisfy the missing requirements.

## Cinematic case-building media contract

Use `case_file_sequence` as the default for proof-heavy beats. Use `cinematic_metaphor` only when `evidence_role = illustrative_only`, and label it as illustrative in the manifest/render props. Source materials must be localized before render; Remotion must not fetch live network material. Motion plan is required for any source receipt longer than 6 seconds. Separate factual media from illustrative and brand-world media. The media manifest should satisfy `channels/modern-archivist/schemas/media.schema.json` and include provenance, license, retrieved-at, and evidence refs where applicable.
