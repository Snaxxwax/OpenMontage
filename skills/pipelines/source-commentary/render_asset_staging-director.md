# Stage: render_asset_staging

## Inputs
- `artifacts/prepared_media_manifest.json` with `operator_approved_for_staging: true`

## Outputs
- `staging/<render_id>/staged_asset_manifest.json` with `gate_passed: true`
- `staging/<render_id>/staged_asset_qc.md`

## Allowed Actions
- Run staging script:
  ```
  python3 scripts/asymmetric_stage_assets.py \
    --manifest <project>/artifacts/prepared_media_manifest.json \
    --staging-dir <project>/staging \
    --render-id <render_id> \
    --overwrite
  ```
- Run asset gate:
  ```
  python3 scripts/asymmetric_gate.py render-asset-staging \
    --staging-manifest <project>/staging/<render_id>/staged_asset_manifest.json
  ```
- Write only under `staging/<render_id>/`

## Forbidden Actions
- Running the renderer before the gate exits 0
- Using `--legacy-no-staging` on the renderer
- Modifying staged files after staging (sha256 will fail)
- Setting `operator_approved_for_staging: true` — operator must do this

## Stop Conditions
- `operator_approved_for_staging` is not `true` in `prepared_media_manifest.json`
- Gate exits nonzero — read `staged_asset_qc.md` for failure reasons
- Any staged file missing, zero-byte, or sha256 mismatch

## Handoff Requirements
- `staged_asset_manifest.json` exists with `gate_passed: true`
- `staged_asset_qc.md` exists alongside the manifest
- Pass the full path to `staged_asset_manifest.json` to the compose stage via `--staging-manifest`
