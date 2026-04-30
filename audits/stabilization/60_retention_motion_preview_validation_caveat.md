# Retention-Motion Preview Validation Caveat (Asymmetric)

Date: 2026-04-30

## Summary

The earlier “preview validation” result is **not** an end-to-end proof that the updated retention-first Asymmetric pipeline regenerates correct output.

It **does** prove that the new motion QA check can distinguish between:
- clips that behave like static/deck-like spans, and
- clips that contain sustained visible motion/state change.

## What Actually Happened

### A) Clips cut directly from `final.mp4` (FAILED motion QA)

These were produced by cutting segments from the previously-rendered full episode:
- Source: `projects/chip-factory-runs-world-v2/renders/final.mp4` (780s)
- Method: `ffmpeg -ss <t> -t 25 ...` re-encode
- Outputs:
  - `projects/chip-factory-runs-world-v2/renders/previews_retention_motion_20260429/intro.mp4`
  - `projects/chip-factory-runs-world-v2/renders/previews_retention_motion_20260429/middle_diagram.mp4`
  - `projects/chip-factory-runs-world-v2/renders/previews_retention_motion_20260429/final_leverage_map.mp4`

Result:
- These clips **failed** `visual_qa` `motion_density` due to long static spans and high static ratios.

Interpretation:
- This indicates the *existing* full episode render contains long low-change spans (as measured by frame-diff heuristics).
- It does **not** validate the new retention-first script or a regenerated scene plan.

### B) Clips re-encoded from existing preview renders (PASSED motion QA)

These were produced by re-encoding already-generated preview videos:
- Sources:
  - `projects/chip-factory-runs-world-v2/renders/previews/intro_preview_with_audio.mp4`
  - `projects/chip-factory-runs-world-v2/renders/previews/middle_diagram_preview_with_audio.mp4`
  - `projects/chip-factory-runs-world-v2/renders/previews/final_map_preview_with_audio.mp4`
- Outputs:
  - `projects/chip-factory-runs-world-v2/renders/previews_retention_motion_20260429/intro_hf.mp4`
  - `projects/chip-factory-runs-world-v2/renders/previews_retention_motion_20260429/middle_diagram_hf.mp4`
  - `projects/chip-factory-runs-world-v2/renders/previews_retention_motion_20260429/final_leverage_map_hf.mp4`

Result:
- These clips **passed** `visual_qa` `motion_density`.

Interpretation:
- This confirms the QA tool’s measurement + thresholds are able to recognize the motion characteristics of the existing preview clips.
- It does **not** prove that a new retention-first `script.json` → regenerated `scene_plan.json` → regenerated preview renders will also pass.

## Conclusion

Preview validation currently proves:
- the new QA check works on existing assets.

Preview validation does *not* yet prove:
- the retention-first script generation is correct,
- the scene planner will regenerate a retention-first scene plan,
- regenerated previews will pass motion QA without relying on previously-produced preview assets.

