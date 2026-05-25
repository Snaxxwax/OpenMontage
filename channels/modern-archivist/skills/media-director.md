# Modern Archivist Media Director

Use this director for the `media_manifest` stage.

## Mission

Create `artifacts/media_manifest.json`: a local, provenance-rich plan for all visual inputs used by the episode.

## Inputs

- `artifacts/episode.json`
- `artifacts/research_packet.json`
- `artifacts/content_collection.json`

Before finalizing `media_manifest`, run the deterministic content asset staging utility for any approved opportunities with `local_path`, and run content opportunity reference validation against the episode + media manifest draft. The utility may copy/hash declared local files and report unresolved refs; it must not choose opportunities, download sources, or decide runtime/provider fallback.

## Output contract

Produce a media manifest compatible with `channels/modern-archivist/schemas/media.schema.json` when possible. Include every required visual slot, local path or planned creation source, provenance, license/usage notes, and render-time props.

## Rules

1. No network fetches during Remotion render.
2. Every visual asset has provenance.
3. Use saved channel assets before generating new assets.
4. Differentiate factual media from illustrative graphics.
5. Do not choose ComfyUI generation here; only identify missing assets and creation requirements for the asset_generation stage.

## Visual language

Favor source_montage, recreated_ui, case-file/editorial sequences, public video, archived pages, product screenshots, source receipts, quote cards, and failure-ledger UI elements. Preserve Modern Archivist palette and deterministic React components. Documents and charts can appear as receipt beats, but they should not become the main visual surface.

## content_collection mapping workflow

1. Read `episode`, `research_packet`, and `content_collection` before authoring `media_manifest`.
2. For each scene, map the visual slot to one or more content_collection opportunity IDs.
3. Convert each approved visual opportunity into local render inputs: local files, inline deterministic JSON, or explicit creation/acquisition requirements. No render-time network fetches.
4. Carry through `rights_status`, `runtime_affinity`, evidence role, source label, and provenance notes.
5. Prefer `source_montage`, `recreated_ui`, `case_file_sequence`, and `failure_graph` over `data_sequence` when both can explain the beat.
6. Preserve HyperFrames-affinity opportunities as planned local segment assets; do not choose or swap runtime here.
7. Mark blocked or missing assets explicitly instead of silently replacing them with generic stock.

The manifest must make opportunity IDs traceable from script beat to local render inputs.

## Success criteria

- `artifacts/media_manifest.json` exists.
- Every scene visual slot has local media, inline deterministic data, or an explicit missing-asset requirement.
- All source media includes URL/publisher/license/retrieved-at when applicable.
- The asset_generation director can decide whether saved assets satisfy the missing requirements.

## Cinematic case-building media contract

Use `case_file_sequence` as the default for proof-heavy beats. Use `cinematic_metaphor` only when `evidence_role = illustrative_only`, and label it as illustrative in the manifest/render props. Source materials must be localized before render; Remotion must not fetch live network material. Motion plan is required for any source receipt longer than 6 seconds. Separate factual media from illustrative and brand-world media. The media manifest should satisfy `channels/modern-archivist/schemas/media.schema.json` and include provenance, license, retrieved-at, and evidence refs where applicable.
