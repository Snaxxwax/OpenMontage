# Render Asset Staging Director - Source-Commentary Pipeline

## 1. Stage Purpose
Stage all prepared media into a clean, integrity-verified directory and run the
asset gate before any render command is issued. The renderer reads only from
`staged_asset_manifest.json` — never from raw asset paths.

## 2. Inputs
- `prepared_media_manifest.json` (required) — operator-authored; lists every
  asset to stage with `operator_approved_for_staging: true`
- `source_commentary_edit_plan` (optional context) — use to verify that all
  assets referenced in the edit plan are present in the prepared manifest

## 3. Outputs
- `staged_asset_manifest.json` with `gate_passed: true`
- `staged_asset_qc.md` — gate QC report written alongside the manifest

## 4. Allowed Tools
- None. Run the two CLI commands below directly.

## 5. Commands

**Step 1 — Stage assets:**
```bash
python3 scripts/asymmetric_stage_assets.py \
  --manifest shared_studio/projects/<episode_id>/artifacts/prepared_media_manifest.json \
  --staging-dir shared_studio/projects/<episode_id>/staging \
  --render-id <render_id> \
  --overwrite
```
`render_id` must match `^[a-z0-9][a-z0-9_-]*$` (lowercase, digits, hyphens, underscores).

**Step 2 — Run asset gate:**
```bash
python3 scripts/asymmetric_gate.py render-asset-staging \
  --staging-manifest shared_studio/projects/<episode_id>/staging/<render_id>/staged_asset_manifest.json
```

## 6. Forbidden Actions
- Running the renderer before the gate exits 0.
- Modifying staged files after staging (sha256 will fail).
- Using `--legacy-no-staging` on the renderer for this pipeline.
- Setting `operator_approved_for_staging: true` without operator confirmation.

## 7. Required Checks
- `operator_approved_for_staging` is `true` in `prepared_media_manifest.json`.
- Gate exits 0 and `gate_passed` is `true` in the written manifest.
- `staged_asset_qc.md` exists in the staging root.
- Every asset with `source_label_required: true` has a non-empty `source_label`.

## 8. Failure Conditions
- Gate exits nonzero — read `staged_asset_qc.md` for reasons; halt and report.
- Any staged file missing, zero-byte, or sha256 mismatch — halt.
- Orphan files in `media/` or `audio/` not listed in the manifest — halt.
- `operator_approved_for_staging: false` — halt before running staging script.

## 9. Handoff Artifact Requirements
- `staging/<render_id>/staged_asset_manifest.json` with `gate_passed: true`.
- Pass the full path to `staged_asset_manifest.json` to the compose stage via
  `--staging-manifest` flag on `scripts/asymmetric_ffmpeg_renderer.py`.
