> **DEPRECATED** — Content split into `composition-author-director.md`,
> `composition-sync-director.md`, and `composition-qa-director.md`.
> This file is kept for reference only. Do not use for new productions.

---

# Broadcast Explainer — Compose Director

Render the HyperFrames composition to final.mp4.

## Runtime Constraint

This pipeline is locked to `render_runtime: hyperframes`. The `edit_decisions`
artifact must carry `render_runtime: "hyperframes"`. Do not route to Remotion or
FFmpeg — if HyperFrames is unavailable, escalate the blocker to the user before
proceeding.

## Render Command
```bash
cd projects/grid-squeeze/hyperframes && \
  npx hyperframes lint && \
  npx hyperframes render . \
    -o ../renders/final.mp4 \
    --fps 30 \
    --quality high
```

## Success Criteria
- File exists: `projects/grid-squeeze/renders/final.mp4`
- Duration: 295–305 seconds
- Resolution: 1920×1080

## Validation
```bash
ffprobe -v quiet -show_entries format=duration,size \
  -show_entries stream=width,height \
  -of default=noprint_wrappers=1 \
  projects/grid-squeeze/renders/final.mp4
```
