# Modern Archivist Corporate True Crime Reuse Audit

Date: 2026-05-24
Scope: cleanup plus git-history/code audit before implementing `docs/plans/2026-05-24-modern-archivist-corporate-true-crime-implementation.md`.

## Cleanup performed

Removed ignored/generated or superseded files:

- Deleted superseded untracked plan:
  - `docs/plans/2026-05-24-modern-archivist-content-collection-puppet-first-pipeline.md`
- Deleted Remotion generated audio/static cache:
  - `remotion-composer/public/.openmontage/`
- Deleted Python bytecode cache:
  - `channels/modern-archivist/assets/source/__pycache__/`
- Deleted Modern Archivist puppet-trial intermediates:
  - `channels/modern-archivist/assets/source/production_trace_trial/_work/`
  - `channels/modern-archivist/assets/source/production_trace_trial/outline_enforced/_work/`
  - `channels/modern-archivist/assets/source/production_trace_trial/svg_render_check*/`
  - `channels/modern-archivist/assets/source/production_trace_trial/outline_enforced/svg_render_check/`
  - `channels/modern-archivist/assets/source/production_trace_trial/**/contact_sheet*.png`

Post-cleanup retained:

- `channels/modern-archivist/assets/source/production_trace_trial/` retained at about 2.78 MiB because its final PNG/SVG outputs are still referenced by current asset policy.
- `projects/svb-duration-bet/` retained at about 88.16 MiB because it remains useful diagnostic input for media-contract/render-performance work.
- Tracked `channels/modern-archivist/assets/source/comfyui_generated/*` retained because current asset requirements reference them.

## Git-history sources inspected

Relevant branches/refs:

- `main` current Modern Archivist base.
- `origin/asymmetric-staged-render-mvp` old Asymmetric/source-commentary production branch.
- `checkpoint/source-commentary-stabilized` older source-commentary vertical-slice branch.
- `feature/asymmetric-v2-contract-system` contract compiler branch.
- `origin/channel-brand` older channel branding branch.

Relevant commits identified:

- `5309d18` — source-commentary evidence-locked pipeline infrastructure.
- `4d7a921` — source-commentary rendering and asset staging fixes.
- `b802cbd` — render asset staging stage.
- `e3828c1` — visual evidence prep stage.
- `57fe506` — prepared media quality check.
- `0f4c17b` — source proof card composer.
- `796cf5d` — performance brief gate.
- `447b38d` — final QC and publish package stage.
- `45e3264` — silent motion card audio role documentation.
- `95da370` — Modern Archivist subagent quality gates, already adapted into current channel package.
- `b5571c3` — Modern Archivist retention pipeline, already adapted into current channel package.
- `15085fb` — word timestamps + HyperFrames to character pipeline.
- `8de5c9b` — Modern Archivist render optimization.

## Reuse candidates ranked by value

### 1. Reuse: `performance_brief` gate concept

Source:

- `796cf5d:schemas/artifacts/performance_brief.schema.json`
- `796cf5d:skills/pipelines/source-commentary/performance_brief-director.md`
- `docs/asymmetric/high_retention_format_system.md`
- `docs/asymmetric/phase1_lessons.md`

Why it matters:

The new Corporate True Crime plan needs a front-loaded packaging/hook/stakes gate before research and content collection. The old `performance_brief` schema already forced:

- viewer promise
- opening claim
- stakes
- title angle
- thumbnail angle
- first 15 seconds plan
- retention risks
- boring parts to cut
- visual pacing notes

Recommended adaptation:

Do not resurrect it as-is under generic `pipeline_defs/source-commentary`. Add a channel-local Modern Archivist artifact, likely `opening_package` or `performance_package`, with Corporate True Crime fields:

- `title_hypotheses[]`
- `thumbnail_hypotheses[]`
- `viewer_question`
- `collapse_or_contradiction`
- `stakes`
- `first_30_seconds_plan[]`
- `proof_promise`
- `visual_artifact_requirements[]`
- `boredom_risk`
- `reject_if_only_documents`

### 2. Reuse: visual evidence prep / prepared media manifest pattern

Source:

- `e3828c1:skills/pipelines/source-commentary/visual_evidence_prep-director.md`
- `57fe506:scripts/asymmetric_check_prepared_media.py`
- `b802cbd:skills/pipelines/source-commentary/render_asset_staging-director.md`

Why it matters:

The new `content_collection` stage should not hand raw research directly to script/render. It needs an explicit manifest of assets that are showable and rights/quality checked.

Recommended adaptation:

Create a channel-local `content_collection` schema that borrows the prepared-media discipline but expands beyond clips:

- source footage candidates
- public video/hearing/interview clips
- archived web captures
- screenshots / filings / dockets
- recreated UI scenes
- product/demo artifacts
- social posts
- stock/B-roll needs
- rights status
- source label
- local path or capture plan
- runtime affinity: `remotion`, `hyperframes`, `either`
- editorial force score
- visual texture score
- boring/static risk

Keep Python limited to deterministic validators/probes. Creative scoring and selection belongs in Markdown director skills and YAML manifests.

### 3. Reuse: source clip quality gate rubric

Source:

- `docs/asymmetric/phase1_lessons.md`
- `docs/asymmetric/production_doctrine.md`
- `channels/asymmetric/channel_profile.yaml`

Useful old rubric:

- clip energy
- claim relevance
- visual texture
- authority
- cut value

Why it matters:

This maps directly to Corporate True Crime. It prevents the pipeline from collecting low-energy source footage that technically supports the story but kills retention.

Recommended adaptation:

Use the same five dimensions in `content-collection-director.md`, but generalize from video clips to `visual_artifacts`:

- evidence force
- narrative relevance
- visual texture
- source authority
- cut/scene value

Hard rule: a primary evidence asset must pass source authority + scene value. A static document can pass only if it becomes a scene: highlight, zoom, contradiction reveal, recreated UI, case-board motion, or quote punch.

### 4. Reuse with caution: source proof card composer

Source:

- `0f4c17b:schemas/artifacts/source_card_manifest.schema.json`
- `0f4c17b:scripts/asymmetric_compose_source_cards.py`
- `tests/contracts/test_compose_source_cards.py`

Why it matters:

The new channel still needs quick proof moments: cropped article headers, court excerpts, filing quotes, deleted website claims.

Why caution:

The user explicitly rejected tons of documents/charts/graphs. Proof cards should be short receipt beats, not the main visual surface.

Recommended adaptation:

Do not make this a primary renderer. Convert the useful constraints into a `receipt_card` / `proof_beat` utility or Remotion component:

- safe crop bounds
- bottom-safe margin
- source label required
- output path safety
- QC report

Then feed those proof beats into SourceMontage/case-board scenes instead of full-screen static cards.

### 5. Reuse: source-commentary asset staging and render adapter patterns

Source:

- `checkpoint/source-commentary-stabilized:tools/video/source_commentary_asset_stager.py`
- `checkpoint/source-commentary-stabilized:tools/video/source_commentary_render_adapter.py`
- `checkpoint/source-commentary-stabilized:tools/source/source_commentary_edit_plan_builder.py`

Why it matters:

They solved practical problems that still exist:

- copy assets into Remotion public space
- generate deterministic staging receipts
- protect against path traversal
- map source assets into render-friendly edit decisions

Why caution:

The old implementation is source-commentary specific and predates the current Remotion audio cache and channel-package conventions. Do not directly import its pipeline names or generic core assumptions.

Recommended adaptation:

Borrow implementation ideas for a channel-local or generic deterministic `asset_staging` utility:

- strict relative staged paths
- sha256 receipt
- zero-byte/missing-file checks
- no directory scanning
- explicit manifest-only staging

This can support both Remotion and HyperFrames asset workspaces.

### 6. Reuse: final QC / publish package shape

Source:

- `447b38d:schemas/artifacts/publish_package.schema.json`
- `447b38d:scripts/asymmetric_write_final_qc.py`
- current `channels/modern-archivist/skills/review/render-qc-reviewer.md`

Why it matters:

Corporate True Crime needs packaging continuity: title, thumbnail, source credits, chapters, render path, QC status.

Recommended adaptation:

Later phase. Do not block content-collection implementation on it. Bring it in after proof-of-format render works.

### 7. Already reused in current code: Modern Archivist retention/render stack

Current files already contain reusable infrastructure:

- `channels/modern-archivist/design/retention-doctrine.md`
- `tests/contracts/test_modern_archivist_retention_contract.py`
- `channels/modern-archivist/remotion/src/components/media/SourceMontage.tsx`
- `channels/modern-archivist/remotion/src/components/media/CaseFileSequence.tsx`
- `channels/modern-archivist/remotion/src/components/media/KineticTypography.tsx`
- `channels/modern-archivist/remotion/src/components/media/FailureGraph.tsx`
- `channels/modern-archivist/remotion/src/state.ts`
- `channels/modern-archivist/remotion/src/types.ts`

Important caveat:

The renderer already has a `source_montage` media type, but the current artifact contract mismatch (`media_overlay.type` vs `media.kind`) can cause these components to be skipped. Fix normalization before building many new visuals.

## Recommended implementation shortcuts

1. Do not design `content_collection` from scratch. Base it on old `prepared_media_manifest` + source clip quality gate + current Modern Archivist `media.schema.json`.
2. Do not write a new renderer first. Fix media normalization and expand existing `SourceMontage`, `CaseFileSequence`, and `KineticTypography` paths.
3. Do not build source-card tooling as a central feature. Reuse only its crop/safe-label/QC constraints for proof beats.
4. Do not revive old `source-commentary` as a pipeline. Treat it as reference material only; the active home is `channels/modern-archivist/pipeline.yaml`.
5. Prefer a thin deterministic validator over new orchestration scripts. The old scripts are useful examples but must be adapted to current guardrails.

## Suggested order for the new plan after this audit

1. Add channel source-of-truth contract tests.
2. Add `performance_package` / opening gate using old `performance_brief` fields as the starting template.
3. Add `content_collection` schema + director skill using old visual evidence prep and clip quality scoring.
4. Fix `media_overlay.type` to `media.kind` normalization so existing media components render.
5. Add `recreated_ui` and richer `source_montage` fields only after step 4 proves media materializes.
6. Add deterministic asset staging/cache for collected local media, borrowing old path-safety and sha256 receipt patterns.
7. Add QC gates: static-hold, visual-event cadence, source-label, audio duration/loudness.

## Current git state after cleanup

Expected working tree changes:

- Modified: `channels/modern-archivist/CHANNEL.md`
- Untracked: `channels/modern-archivist/design/channel-source-of-truth.md`
- Untracked: `docs/plans/2026-05-24-modern-archivist-corporate-true-crime-implementation.md`
- Untracked: this reuse audit doc

No tracked source files were deleted during cleanup.
