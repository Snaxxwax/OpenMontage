# Visual Evidence Prep Director - Source-Commentary Pipeline

## 1. Stage Purpose
Assemble `prepared_media_manifest.json` from the upstream acquisition artifacts.
This manifest is the single source of truth for `render_asset_staging` — it
records which assets are ready, their editorial metadata, and their paths.
No binary processing. No directory scanning. Every asset must be explicitly listed.

## 2. Inputs
- `approved_clip_manifest` — verified video clip paths, source labels, claim_ids
- `extracted_clip_manifest` — timing: `in_seconds`, `out_seconds`, `duration_seconds` (match by `receipt_id`)
- `clip_use_receipts` — `original_audio_use` per receipt for audio role mapping
- Screenshot files (if any) — must be explicitly provided by operator; do not infer paths

## 3. Outputs
- `artifacts/prepared_media_manifest.json` with `operator_approved_for_staging: false`

## 4. Allowed Tools
- None. This is a manifest-authoring stage.

## 5. Asset construction rules

### Video clips (from `approved_clip_manifest`)
For each clip where `approved_for_edit: true`:
- `asset_id` — use `receipt_id`
- `media_type` — `"video"`
- `role` — map `clip_role` from receipt: `primary_evidence` or `timeline_proof` → `"proof"`; all others → `"b-roll"`
- `input_path` / `prepared_path` — `local_clip_path` from `approved_clip_manifest`
- `source_label_required` — from `approved_clip_manifest`
- `source_label` — from `source_label_text` in `approved_clip_manifest` (required when `source_label_required: true`)
- `in_seconds`, `out_seconds`, `duration_seconds` — from `extracted_clip_manifest` (matched by `receipt_id`)
- `audio_role` — map from `original_audio_use` in receipt:
  - `muted` → `"muted"`
  - `ducked` → `"ambient"`
  - `quote_audio` → `"quoted_audio"`
- `framing` — `"full_frame"` unless operator specifies otherwise (no AI cropping)
- `preparation_status` — `"prepared"`
- `qc_notes` — brief note on why the clip is ready; include any QC observations from `media_qc`

### Screenshots (operator-listed only)
Do not scan directories. For each screenshot the operator explicitly supplies:
- `asset_id` — operator-assigned identifier
- `media_type` — `"screenshot"`
- `role` — `"proof"` (screenshots are always evidence assets in this pipeline)
- `input_path` / `prepared_path` — absolute path to the captured PNG/JPEG
- `source_label_required` — `true` (screenshots in source-commentary always require attribution)
- `source_label` — operator supplies: publication name, date, URL or handle
- `legibility_ok` — operator confirms text is readable at render resolution
- `framing` — `"full_page"` for full-page scroll captures; `"cropped"` if a section was pre-cropped
- `render_treatment` — `"scale_fit"` for standard renders; operator may specify `"pan_and_scan"` if needed
- `preparation_status` — `"prepared"`
- `qc_notes` — note on capture quality, dimensions, any legibility concerns

### Narration audio (if present)
- `asset_id` — e.g. `"NAR-01"`
- `media_type` — `"audio"`
- `role` — `"narration"`
- `input_path` / `prepared_path` — absolute path to the MP3/WAV
- `source_label_required` — `false`
- `duration_seconds` — measured from file (ffprobe or known value)
- `audio_role` — `"narration"`
- `loudness_lufs` — measured value (ffmpeg loudnorm); must not be omitted
- `silence_gate_passed` — `true` only if silence gate has been run and passed
- `preparation_status` — `"prepared"`
- `qc_notes` — note on loudness, silence gate run, any fixes applied

## 6. Forbidden Actions
- Setting `operator_approved_for_staging: true` — operator must do this manually after review.
- Scanning `assets/`, `clips/`, or `narration/` directories to discover assets.
- Adding assets that are not in `approved_clip_manifest` or explicitly listed by operator.
- Inferring `source_label` from filenames or paths.
- Setting `preparation_status: "raw"` or `"failed"` — if an asset is not ready, halt and report.

## 7. Required Checks
- Every clip with `approved_for_edit: true` in `approved_clip_manifest` has an entry.
- Every asset with `source_label_required: true` has a non-empty `source_label`.
- `in_seconds < out_seconds` and `duration_seconds > 0` for all video assets.
- `preparation_status: "prepared"` on every asset.
- Manifest is schema-valid against `schemas/artifacts/prepared_media_manifest.schema.json`.
- `operator_approved_for_staging` is `false` on write.

## 8. Failure Conditions
- Any approved clip from `approved_clip_manifest` is missing from `extracted_clip_manifest` — halt.
- `source_label_text` is empty for a `source_label_required: true` clip — halt.
- Narration asset present but `loudness_lufs` is unknown — halt; operator must measure first.
- Any asset path does not exist on disk — halt; do not write a manifest with broken paths.

## 9. Handoff Artifact Requirements
- `artifacts/prepared_media_manifest.json` written with `operator_approved_for_staging: false`.
- Operator reviews the manifest, confirms all paths are valid and labels are accurate, then sets `operator_approved_for_staging: true`.
- `render_asset_staging` will refuse to run until `operator_approved_for_staging: true`.
