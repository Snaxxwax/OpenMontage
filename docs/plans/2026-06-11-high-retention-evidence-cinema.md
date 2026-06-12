# Implementation plan: High-Retention Evidence Cinema Pilot

Date: 2026-06-11
Brief: `.ai/feature-briefs/2026-06-11-high-retention-evidence-cinema.md`
Issues: `.ai/issues/2026-06-11-high-retention-evidence-cinema.md`
Target repo: `/home/pop/repos/openmontage-asymmetric`

## Decision

The current Remotion card video is rejected as a target format. It is useful only as a technical proof that props/audio/rendering work.

The next real test must be a source-footage-first evidence-cinema pilot. The format should resemble a 2026 YouTube documentary cold open / first act, not a narrated presentation.

## Constraints

- Final assembly remains Remotion.
- No WAN 2.2 or image-to-video hero footage.
- Use real/source-derived assets: public clips, screenshots, screen recordings, product pages, review moments, articles, support notices, filings, UI recreations.
- Log provenance and fair-use rationale for all source media.
- Remotion render receives only local deterministic assets/JSON.
- Use explicit Remotion ports due local port-probe failures.

## Phase 0 — Stop treating card render as success

1. Keep `humane_ai_pin_evidence_test_v2.mp4` as a failed format reference.
2. Do not promote it to channel template.
3. Use it only to confirm that audio, props, and composition routing work.

Acceptance:
- QC language explicitly marks v2 as rejected for audience appeal.

## Phase 1 — Source collection

Commands/tools:
- `yt-dlp` for public source clips where fair use is defensible.
- Browser/screenshot tooling or Playwright for webpage artifacts.
- `ffmpeg` for trims and contact sheets.

Output paths:
- `projects/humane-ai-pin-evidence-test/assets/source/video/`
- `projects/humane-ai-pin-evidence-test/assets/source/screenshots/`
- `projects/humane-ai-pin-evidence-test/artifacts/asset_log.tsv`

Minimum asset targets:
- AI Pin launch/product demo material
- MKBHD or major review moment as fair-use commentary clip or screenshot
- Verge/TechCrunch article screenshot/recreation
- official/help/shutdown notice if available
- product/device imagery
- HP acquisition article/source

Asset log columns:
- `asset_id`
- `source_url`
- `source_owner`
- `local_path`
- `asset_type`
- `duration_sec`
- `rights_status`
- `fair_use_justification`
- `evidence_role`
- `used_in_beats`

Acceptance:
- At least 12 assets.
- At least 4 motion-capable assets.
- No AI-generated footage.

## Phase 2 — Retention edit map

Create:
- `projects/humane-ai-pin-evidence-test/artifacts/visual_cues.json`
- `projects/humane-ai-pin-evidence-test/artifacts/retention_timeline.json`

Cue schema draft:

```json
{
  "at": 0.0,
  "end": 2.4,
  "asset_id": "shutdown_notice_01",
  "visual_treatment": "hard_cut_zoom_stamp",
  "overlay_text": "SERVICE ENDS IN 10 DAYS",
  "sfx": "stamp_hit",
  "evidence_refs": ["techcrunch-shutdown"],
  "retention_role": "cold_open_shock"
}
```

Acceptance:
- First 5 seconds have source-derived visuals.
- Visual change cadence <= 5 seconds average.
- Every open loop has a payoff beat.

## Phase 3 — Components

Implement only after assets/cues exist.

Likely components:

1. `SourceClipSequence.tsx`
   - local video/image playback
   - crop/zoom/pan presets
   - on-screen attribution
   - caption/annotation overlays

2. `ArtifactZoom.tsx`
   - article/webpage screenshot push-ins
   - line highlights
   - redaction/marker effects

3. `DependencyCollapse.tsx`
   - animated product dependency chain
   - server cutoff collapse
   - red critical-error rupture

4. `ReceiptHighlight.tsx`
   - number extraction from article/source
   - synced emphasis to narration

Files:
- `channels/modern-archivist/remotion/src/components/media/*.tsx`
- `channels/modern-archivist/remotion/src/types.ts`
- `channels/modern-archivist/remotion/src/components/MediaContainer.tsx`

Acceptance:
- `npx tsc --noEmit --pretty false` passes.
- Smoke render covers all new components.

## Phase 4 — Audio and sound design

Preferred:
- Restore/use Fish Speech for final-quality narration.

Fallback:
- Piper is acceptable only for scratch renders.

Add sound cues:
- low riser under cold open
- stamp hits for dates/prices
- glitch hit for critical error
- subtle whooshes for artifact zooms

Acceptance:
- Audio has narration plus basic SFX/music bed.
- No dead air.
- ffprobe confirms audio stream.

## Phase 5 — Render v3

Render command pattern:

```bash
cd /home/pop/repos/openmontage-asymmetric/remotion-composer
npx remotion render src/index.tsx ModernArchivist \
  /home/pop/repos/openmontage-asymmetric/projects/humane-ai-pin-evidence-test/renders/humane_ai_pin_high_retention_v3.mp4 \
  --props=/home/pop/repos/openmontage-asymmetric/channels/modern-archivist/episodes/humane-ai-pin-high-retention-v3.episode.json \
  --port=3987 \
  --scale=0.5
```

Validation:

```bash
npx tsc --noEmit --pretty false
python3 -m pytest tests/contracts/ -q
ffprobe -v error -show_entries format=duration,size -show_streams -of json <render.mp4>
ffmpeg -y -i <render.mp4> -vf "fps=1/10,scale=480:-1,tile=3x4" -frames:v 1 review/frames/contact_sheet_v3.jpg
```

## Phase 6 — QC gate

Create:
- `projects/humane-ai-pin-evidence-test/review/render_qc_v3.md`

QC checklist:
- Does the first frame create a question?
- Does the first 5 seconds show source-derived visuals?
- Is any text card onscreen for >4 seconds?
- Is the visual change cadence <=5 seconds?
- Does the segment use source footage/artifacts for >=70% of runtime?
- Are all clips attributed/logged?
- Does it feel like a YouTube documentary, not a presentation?

## Rollback

If the v3 render still feels like cards:
- keep the source asset collection and cue map
- reject the components
- redesign around more real footage/screen recordings before adding new visual primitives

## Next command after approval

Run packet preparation:

```bash
cd /home/pop/repos/openmontage-asymmetric
scripts/prepare-packets docs/plans/2026-06-11-high-retention-evidence-cinema.md
```

Then export to Kanban:

```bash
scripts/export-to-kanban .ai/packets/2026-06-11-high-retention-evidence-cinema/index.json --assignee default --workspace dir:/home/pop/dev
```
