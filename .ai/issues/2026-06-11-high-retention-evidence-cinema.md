# Issue breakdown: High-Retention Evidence Cinema Pivot

Date: 2026-06-11
Source brief: `.ai/feature-briefs/2026-06-11-high-retention-evidence-cinema.md`

## Issue 1 — Build source asset collector for Humane pilot

Goal: Replace card-only visuals with real/source-derived material.

Files/outputs:
- `projects/humane-ai-pin-evidence-test/assets/source/`
- `projects/humane-ai-pin-evidence-test/artifacts/asset_log.tsv`
- `projects/humane-ai-pin-evidence-test/artifacts/content_collection.json`

Tasks:
- Collect candidate public videos/articles/screenshots for AI Pin launch, reviews, return coverage, and shutdown.
- Use `yt-dlp` directly if registry wrappers are unavailable.
- Capture webpages/screenshots with provenance.
- Log fair-use rationale for every clip/screenshot.

Acceptance:
- At least 12 visual assets, including at least 4 motion clips or screen recordings.
- `asset_log.tsv` includes source_url, source_owner, local_path, duration_sec, rights_status, fair_use_justification.
- No generated WAN/AI footage.

## Issue 2 — Create visual_cues.json and retention_timeline.json

Goal: Make pacing explicit before render.

Files/outputs:
- `projects/humane-ai-pin-evidence-test/artifacts/visual_cues.json`
- `projects/humane-ai-pin-evidence-test/artifacts/retention_timeline.json`

Tasks:
- Convert the 90-120s beat sheet into timed visual cues.
- Every cue declares source asset, motion treatment, overlay text, SFX cue, and evidence ref.
- Track visual change cadence and open loops.

Acceptance:
- Average visual change cadence <= 5 seconds.
- First 5 seconds include source-derived visuals.
- Every factual visual maps to an asset_log row and source/evidence ID.

## Issue 3 — Add cinematic artifact components

Goal: Replace static text-card primitives with motion-heavy evidence scenes.

Likely files:
- `channels/modern-archivist/remotion/src/components/media/SourceClipSequence.tsx`
- `channels/modern-archivist/remotion/src/components/media/ArtifactZoom.tsx`
- `channels/modern-archivist/remotion/src/components/media/DependencyCollapse.tsx`
- `channels/modern-archivist/remotion/src/components/media/ReceiptHighlight.tsx`
- `channels/modern-archivist/remotion/src/types.ts`
- `channels/modern-archivist/remotion/src/components/MediaContainer.tsx`

Tasks:
- Add source clip / screenshot sequence component with masks, zooms, crop windows, attribution tags.
- Add artifact zoom/highlight component for article/webpage screenshots.
- Add dependency-collapse component for cloud/server/product failure mechanisms.
- Add receipt highlight component for source text and numbers.

Acceptance:
- Components consume deterministic local assets under Remotion public.
- No live fetches during render.
- TypeScript passes.
- Smoke render covers each component.

## Issue 4 — Compose Humane high-retention pilot v3

Goal: Produce a YouTube-style 90-120s pilot segment.

Files/outputs:
- `channels/modern-archivist/episodes/humane-ai-pin-high-retention-v3.episode.json`
- `projects/humane-ai-pin-evidence-test/renders/humane_ai_pin_high_retention_v3.mp4`
- `projects/humane-ai-pin-evidence-test/review/render_qc_v3.md`

Tasks:
- Build an episode JSON from asset_log + visual_cues + retention_timeline.
- Generate or reuse narration, ideally Fish Speech if available; Piper only for scratch.
- Render with explicit Remotion port.
- Generate contact sheet and frame samples.

Acceptance:
- 90-120s runtime.
- Valid video+audio streams by ffprobe.
- >= 70% source-derived/artifact motion runtime.
- No static text card > 4s.
- Manual QC: feels like documentary cold open/first act, not a deck.

## Issue 5 — Add boring-card regression gate

Goal: Prevent future regressions into card-only videos.

Likely files:
- `tests/contracts/test_modern_archivist_retention_contract.py`
- `channels/modern-archivist/schemas/episode.schema.json`

Tasks:
- Add fields or validation for visual_cues, source_asset_ratio, static_card_seconds, visual_change_cadence.
- Add a contract test for high-retention pilot fixtures.

Acceptance:
- Contract fails if an episode has too many card-only beats.
- Contract fails if the first 5 seconds are text-only.
- Existing contract suite still passes.
