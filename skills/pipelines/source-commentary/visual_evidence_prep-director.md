# Stage: visual_evidence_prep

## Inputs
- `approved_clip_manifest` — verified clip paths, source labels, claim_ids
- `extracted_clip_manifest` — timing per receipt: `in_seconds`, `out_seconds`, `duration_seconds`
- `clip_use_receipts` — `original_audio_use` per receipt for audio role mapping
- Screenshot list (explicit, operator-provided — no directory scanning)

## Outputs
- `artifacts/prepared_media_manifest.json` with `operator_approved_for_staging: false`

## Allowed Actions
- Read the three upstream manifests and any explicitly listed screenshot paths
- Assemble one asset entry per approved clip and per listed screenshot
- Map `original_audio_use` → `audio_role`: `muted`→`muted`, `ducked`→`ambient`, `quote_audio`→`quoted_audio`
- Set `preparation_status: "prepared"` on every asset
- Write `operator_approved_for_staging: false` — operator flips this manually before staging

## Forbidden Actions
- Scanning `assets/`, `clips/`, `narration/`, or any directory to discover assets
- Adding assets not in `approved_clip_manifest` or not explicitly listed
- Cropping, transcoding, or acquiring media
- Setting `operator_approved_for_staging: true`
- Inferring `source_label` from filenames or paths

## Stop Conditions
- Any clip with `approved_for_edit: true` is missing from `extracted_clip_manifest`
- `source_label_text` is empty for a `source_label_required: true` clip
- Narration asset present but `loudness_lufs` is unknown
- Any asset path does not exist on disk

## Handoff Requirements
- `artifacts/prepared_media_manifest.json` schema-valid against `schemas/artifacts/prepared_media_manifest.schema.json`
- `operator_approved_for_staging: false`
- Operator reviews, confirms paths and labels, then sets `operator_approved_for_staging: true` to unlock `render_asset_staging`
