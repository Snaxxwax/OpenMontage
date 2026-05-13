# QC Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Perform final creative, technical, and source-integrity review of the rendered deliverable.

## 2. Inputs
- Rendered MP4
- `asymmetric_claim_map`
- `visual_rhythm_plan`
- `source_segment_approval_manifest`
- QC logs and reports

## 3. Outputs
- `qc_report` or canonical review artifact under `artifacts/`
- Gate payloads/logs under `qc/`

## 4. Allowed Tools
- `ffprobe`
- `ffmpeg` silencedetect through approved script
- Visual/audio QC adapters when available
- `scripts/asymmetric_gate.py qc`

## 5. Forbidden Actions
- Approving render with missing source labels.
- Approving unsupported or overstated claims.
- Ignoring silence, broken audio, black frames, or missing render file.

## 6. Required Checks
- Render file exists and is playable.
- Audio has no silence over 1 second unless intentionally justified.
- `creative_pass` and `operator_approved_for_creative_pass` are true before final pass.
- Source/proof events still map to approved segments and claims.

## 7. Failure Conditions
- QC gate fails.
- Claim support cannot be traced.
- Technical defect blocks publication.

## 8. Handoff Artifact Requirements
- Persist QC payloads under Artifact Bus `qc/`.
- Final handoff requires render report or QC report pointing to physical MP4.
