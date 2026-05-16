# Stage: qc

## Inputs
- `source_commentary_render_report`
- `source_commentary_qc_report`
- `staging/<render_id>/staged_asset_manifest.json`
- `approved_clip_manifest`
- `research_brief`

## Outputs
- `qc/final_qc.md`

## Allowed Actions
- Read the five input artifacts listed above
- Run:
  ```
  python3 scripts/asymmetric_write_final_qc.py \
    --render-report <project>/artifacts/source_commentary_render_report.json \
    --qc-report <project>/artifacts/source_commentary_qc_report.json \
    --staged-manifest <project>/staging/<render_id>/staged_asset_manifest.json \
    --approved-clips <project>/artifacts/approved_clip_manifest.json \
    --output <project>/qc/final_qc.md
  ```
- Write only to `qc/`

## Forbidden Actions
- Modifying source clips, narration, or staged files
- Overriding `qc_passed` or `gate_passed` values
- Proceeding to publish_package if the script exits nonzero

## Stop Conditions
- Script exits nonzero — read `qc/final_qc.md` for failures
- Any required input file missing

## Handoff Requirements
- `qc/final_qc.md` exists with `verdict: PASS`
- Script exit code is 0
