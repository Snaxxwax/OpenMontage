# Acquisition Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Create local source assets only after capture and segment approval gates pass.

## 2. Inputs
- `source_capture_plan`
- `source_segment_approval_manifest`
- `evidence_candidate_manifest`
- `rights_risk_manifest`
- `youtube_source_manifest`

## 3. Outputs
- Local assets under `assets/`
- Local clips under `clips/` when clip acquisition is approved
- Capture receipts or sidecars under `receipts/` or `assets/`

## 4. Allowed Tools
- `steel_browser_capture` for approved web captures
- `video_downloader` or approved acquisition adapter for approved timestamp ranges
- `scripts/asymmetric_real_smoke_acquisition.py` for deterministic local smoke assets

## 5. Forbidden Actions
- Any acquisition before `operator_approved_for_acquisition` is true.
- Full-source downloads when only timestamp ranges are approved.
- Capturing unapproved segments or sources.
- Live YouTube download in standard test runs.

## 6. Required Checks
- Run `scripts/asymmetric_gate.py render-readiness` before render-facing acquisition.
- Every acquired asset maps to source id, evidence id, claim ids, purpose, rights risk, and capture timestamp.
- Physical files exist and are under the Artifact Bus.

## 7. Failure Conditions
- Missing approval.
- File outside Artifact Bus.
- Asset cannot be traced to evidence and source manifests.

## 8. Handoff Artifact Requirements
- Persist sidecars/receipts with enough data for render and QC.
- Never write artifacts to repository root.
