# Compose Director - Source-Commentary Pipeline

## 1. Stage Purpose
Execute the render and generate the final video file with proper attribution.

## 2. Inputs
- `edit_decisions`
- `approved_clip_manifest`

## 3. Outputs
- `render_report`

## 4. Allowed Tools
- `video_compose`
- `audio_mixer`

## 5. Forbidden Actions
- Rendering without `source_label` overlays for evidence clips.
- Muting source audio that was flagged as `quote_audio`.

## 6. Required Checks
- Source labels are visible and legible (name, channel, URL/handle).
- Audio mix levels (narration vs source) follow ducking rules.
- Resolution and FPS follow the media profile.

## 7. Failure Conditions
- Render failure or timeout.
- Missing overlays for attributed content.

## 8. Handoff Artifact Requirements
- Path to final rendered MP4.
- Verification that all clips in the render have trace receipts.
