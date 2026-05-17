# Stage: visual_evidence_prep

## Inputs
- `approved_clip_manifest` — verified clip paths, source labels, claim_ids
- `extracted_clip_manifest` — timing per receipt: `in_seconds`, `out_seconds`, `duration_seconds`
- `clip_use_receipts` — `original_audio_use` per receipt for audio role mapping
- Screenshot list (explicit, operator-provided — no directory scanning)
- Optional: `artifacts/source_card_manifest.json` — operator-authored source card composition manifest

## Outputs
- `artifacts/prepared_media_manifest.json` with `operator_approved_for_staging: false`
- `qc/prepared_media_qc.md` (written by check script)
- Optional: composed source cards under `assets/composed/` (present if `source_card_manifest.json` was used)

## Allowed Actions
- Read the three upstream manifests and any explicitly listed screenshot paths
- Assemble one asset entry per approved clip and per listed screenshot
- Map `original_audio_use` → `audio_role`: `muted`→`muted`, `ducked`→`ambient`, `quote_audio`→`quoted_audio`; silent motion-card video assets (no audio track) use `audio_role: "none"`
- Set `preparation_status: "prepared"` on every asset
- Write `operator_approved_for_staging: false` — operator flips this manually before staging
- Set screenshot `prepared_path` to a cropped/framed file (square or landscape aspect, ideally 16:9); `input_path` stays pointing to the original
- If `artifacts/source_card_manifest.json` exists, run composition before prepared media QC:
  ```
  python3 scripts/asymmetric_compose_source_cards.py \
    --manifest <project>/artifacts/source_card_manifest.json \
    --output <project>/qc/source_card_composition_qc.md
  ```
- Use composed card outputs as `prepared_path` values for screenshot assets
- Run check script after authoring manifest:
  ```
  python3 scripts/asymmetric_check_prepared_media.py \
    --manifest <project>/artifacts/prepared_media_manifest.json \
    --output <project>/qc/prepared_media_qc.md
  ```

## Forbidden Actions
- Scanning `assets/`, `clips/`, `narration/`, or any directory to discover assets
- Adding assets not in `approved_clip_manifest` or not explicitly listed
- Auto-cropping, transcoding, or acquiring media (operator crops manually before this stage)
- Setting `operator_approved_for_staging: true`
- Inferring `source_label` from filenames or paths
- Setting screenshot `prepared_path` equal to `input_path`
- Running Remotion or HyperFrames, or burning source labels into composed cards

## Stop Conditions
- Any clip with `approved_for_edit: true` is missing from `extracted_clip_manifest`
- `source_label_text` is empty for a `source_label_required: true` clip
- Narration asset present but `loudness_lufs` is unknown
- Any asset path does not exist on disk
- Screenshot `prepared_path` equals `input_path`
- Check script exits nonzero — read `qc/prepared_media_qc.md` for failures
- Composition script exits nonzero or a composed card output is missing before prepared media QC

## Handoff Requirements
- `artifacts/prepared_media_manifest.json` schema-valid against `schemas/artifacts/prepared_media_manifest.schema.json`
- `qc/prepared_media_qc.md` exists with `verdict: PASS`
- `operator_approved_for_staging: false`
- Operator reviews manifest and QC report, then sets `operator_approved_for_staging: true` to unlock `render_asset_staging`
- If `source_card_manifest.json` was used, `qc/source_card_composition_qc.md` exists with `verdict: PASS`
