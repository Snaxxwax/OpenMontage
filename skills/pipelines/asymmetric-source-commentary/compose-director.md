# Compose Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Render the approved Asymmetric source/proof timeline into a physical MP4.

## 2. Inputs
- `visual_rhythm_plan`
- `source_segment_approval_manifest`
- Acquired source assets
- Edit instructions

## 3. Outputs
- Rendered MP4 under `renders/`
- Render report when canonical render schema is used

## 4. Allowed Tools
- `video_compose`
- `scripts/asymmetric_ffmpeg_renderer.py` for deterministic source/proof smoke renders
- FFmpeg only through approved scripts/adapters

## 5. Forbidden Actions
- Rendering without source labels.
- Rendering before render-readiness gate passes.
- Substituting runtime/provider without approval.
- Writing renders outside Artifact Bus.

## 6. Required Checks
- `scripts/asymmetric_gate.py render-readiness` passes.
- Render path exists and is an MP4.
- Source/proof labels are burned in or otherwise visible.
- Render uses only approved source/proof assets.

## 7. Failure Conditions
- Missing physical MP4.
- Missing label overlays.
- Render uses unapproved asset or segment.

## 8. Handoff Artifact Requirements
- Persist render output under `shared_studio/projects/<project_slug>/renders/`.
- Persist logs/QC materials under `qc/`.
