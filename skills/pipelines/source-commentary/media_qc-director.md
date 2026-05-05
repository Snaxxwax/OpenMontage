# Media QC Director - Source-Commentary Pipeline

## 1. Stage Purpose
Technically and visually verify that the extracted clips are suitable for production.

## 2. Inputs
- `extracted_clip_manifest`

## 3. Outputs
- `approved_clip_manifest` (canonical artifact)

## 4. Allowed Tools
- `video_analyzer`
- `frame_sampler`
- `visual_qa`

## 5. Forbidden Actions
- Proceeding with corrupted, low-resolution, or black-frame clips.
- Editing the content of the clips (analysis only).

## 6. Required Checks
- Resolution matches project requirements.
- Audio levels are audible for `quote_audio` clips.
- Visual content matches the `rationale` from the receipt.

## 7. Failure Conditions
- Black frames or freeze frames detected.
- Mismatch between transcript-based rationale and actual visual content.

## 8. Handoff Artifact Requirements
- Canonical `approved_clip_manifest` mapping `receipt_id` to a verified `local_path`.
