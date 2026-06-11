# Modern Archivist 2026 Performance Hardening Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Turn the new Modern Archivist playbook and pipeline from a strong creative package into a measurable 2026 YouTube performance system by hardening retention contracts, packaging stages, and post-publish learning loops.

**Architecture:** Preserve OpenMontage’s instruction-first boundary. Put channel behavior, packaging workflow, and review policy in `channels/modern-archivist/pipeline.yaml`, channel skills, design docs, and schemas. Limit code changes to deterministic schema/contract validation and any narrow helpers required to validate new artifacts.

**Tech Stack:** Channel package files under `channels/modern-archivist/`, style playbook under `styles/`, JSON schemas, Markdown director skills, YAML pipeline manifests, pytest/jsonschema contract tests, optional YouTube metadata/analytics artifact generation, existing render/report artifacts.

---

## Source material to keep open while implementing

- `docs/plans/2026-06-11-modern-archivist-playbook-pipeline-audit.md`
- `docs/plans/2026-06-11-modern-archivist-local-autonomous-video-architecture-audit.md`
- `styles/modern-archivist.yaml`
- `channels/modern-archivist/pipeline.yaml`
- `channels/modern-archivist/design/retention-doctrine.md`
- `channels/modern-archivist/design/channel-source-of-truth.md`
- `channels/modern-archivist/skills/script-director.md`
- `channels/modern-archivist/skills/thumbnail-director.md`
- `channels/modern-archivist/schemas/episode.schema.json`
- `docs/DEVELOPMENT_GUARDRAILS.md`

## Non-goals

- Do not broaden Modern Archivist into a generic business-explainer package.
- Do not move channel-specific packaging policy into generic OpenMontage pipeline definitions.
- Do not add Python orchestration that decides titles, thumbnails, or retention strategy.
- Do not treat Shorts as a separate channel identity; they are support assets for long-form.
- Do not invent numeric KPI guarantees as if they were official YouTube thresholds.
- Do not reinterpret local-first production as synthetic-first production. Modern Archivist remains evidence-cinema: real source material, public artifacts, recreated evidence cards, and deterministic Remotion assembly are preferred over long-form chained AI-video generation.
- Do not add autonomous Python/ComfyUI loops that choose prompts, providers, candidates, promotion, or review outcomes outside the manifest/director-skill contract.

## Desired end state

```text
research
-> content_collection
-> script
-> audio
-> audio_analysis
-> media_manifest
-> asset_generation
-> render
-> thumbnail
-> publish_prep
-> retention_review
```

Where:
- `content_collection` performs real source discovery across the web and YouTube, not just abstract planning
- `thumbnail` creates structured, multi-variant packaging concepts before upload
- `publish_prep` creates a complete upload packet
- `retention_review` converts actual performance data into channel learning artifacts

## Rights-aware footage policy

Modern Archivist should aggressively prefer real, already-existing visual material over rendering from scratch when that material is legally usable and editorially strong.

Priority order:
1. directly usable public-domain, licensed, own-created, or otherwise approved source footage/public video
2. usable archived web, product UI, hearings, demos, interviews, and public statements
3. recreated digital artifacts when direct use is not allowed or not visually workable
4. bespoke rendered support visuals only when sourced footage/artifacts cannot carry the beat alone

Important distinction:
- YouTube is a discovery surface, not an automatic rights grant.
- A clip being on YouTube does not make it automatically reusable.
- But if a YouTube-hosted clip is public-domain, licensed, owned, or otherwise approved for use, the pipeline should prefer using it directly because it reduces unnecessary rendering and better matches documentary norms.

Operational implication for `content_collection`:
- find candidate clips on the web and YouTube
- record exact relevant timestamps
- classify rights conservatively
- decide whether each clip is `usable`, `needs_review`, `recreate_only`, `unusable`, or `unknown`
- prefer direct use when `rights_status=usable`

---

## Phase 0: Lock the doctrine in tests and docs

### Task 0.1: Add a performance-hardening design note

**Objective:** Record the new operational rules in channel docs before changing the pipeline.

**Files:**
- Modify: `channels/modern-archivist/design/retention-doctrine.md`
- Modify: `channels/modern-archivist/design/channel-source-of-truth.md`
- Test: `tests/contracts/test_modern_archivist_retention_contract.py`

**Step 1: Write failing test**

Add/extend a contract test to assert that the doctrine references:
- visual change every 3–6 seconds
- anchor return every 45–60 seconds
- thumbnail/title packaging as part of channel success
- post-publish review as required learning behavior

Run:

```bash
pytest tests/contracts/test_modern_archivist_retention_contract.py -q
```

Expected: FAIL until docs are updated.

**Step 2: Patch doctrine docs**

Add a short section to `retention-doctrine.md` covering:
- packaging is part of the show, not an afterthought
- shelf promise must match cold open promise
- post-publish retention review updates future episodes

Add a short section to `channel-source-of-truth.md` covering:
- upload packaging packet required for every episode
- no episode is “done” at render
- local-first but not synthetic-first doctrine: local tools are used for cost/privacy/repeatability, while real evidence, source footage, recreated UI/documents, and deterministic Remotion assembly remain the channel default

**Step 3: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_retention_contract.py -q
```

Expected: PASS.

### Task 0.2: Make `content_collection` explicitly discovery-driven

**Objective:** Record in the implementation plan that `content_collection` is not just a thought exercise; it must actively find candidate source material on the web and YouTube and prefer direct use of legally usable clips over unnecessary rendering.

**Files:**
- Modify: `channels/modern-archivist/skills/content-collection-director.md`
- Modify: `channels/modern-archivist/schemas/content_collection.schema.json`
- Modify: `channels/modern-archivist/pipeline.yaml`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Write failing contract test**

Extend the content-collection contract test to assert:
- the director explicitly mentions web/YouTube discovery
- `public_video` opportunities can carry exact candidate timestamps
- the pipeline stage advertises actual discovery tooling instead of `tools_available: []`
- the schema supports fields such as `candidate_timestamps`, `clip_summary`, and `on_screen_use_strategy`

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py tests/contracts/test_channel_package_boundary.py -q
```

Expected: FAIL.

**Step 2: Patch the director skill**

Add rules to `content-collection-director.md` stating that the stage must:
- search the web and YouTube for demos, interviews, hearings, ads, launch footage, public statements, archived captures, and other showable artifacts
- record exact timestamps for relevant moments in public videos
- prefer directly usable public-domain/licensed/approved clips when available
- downgrade clips to `needs_review`, `recreate_only`, `unusable`, or `unknown` when rights are unclear
- avoid spending render effort on scenes that can be carried by strong, usable sourced footage

**Step 3: Patch the schema**

For `public_video` and other clip-like opportunities, add optional structured fields such as:

```json
"candidate_timestamps": [
  {
    "start_seconds": 12,
    "end_seconds": 24,
    "why_it_matters": "Launch demo contradiction visible in-frame"
  }
],
"clip_summary": "CEO demo segment showing the claim before the reversal.",
"on_screen_use_strategy": "direct_clip" 
```

with an enum for `on_screen_use_strategy` such as:
- `direct_clip`
- `recreated_excerpt`
- `still_frame_with_annotation`
- `quote_card_only`
- `research_only`

**Step 4: Patch the pipeline stage**

Update `channels/modern-archivist/pipeline.yaml` so `content_collection` exposes real discovery tools rather than an empty list. Exact tools depend on repo capabilities, but the contract should reflect web/video discovery as a real stage capability.

**Step 5: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py tests/contracts/test_channel_package_boundary.py -q
```

Expected: PASS.

---

## Phase 1: Harden the playbook into an execution contract

### Task 1.1: Add measurable motion, narration, and safe-area keys to the playbook

**Objective:** Convert the playbook from a mostly stylistic brief into a repeatable operational contract.

**Files:**
- Modify: `styles/modern-archivist.yaml`
- Test: `tests/contracts/test_modern_archivist_playbook_contract.py`

**Step 1: Write failing test**

Create/extend a playbook contract test that asserts the presence of keys like:

```python
required_paths = [
    ("motion", "pacing_rules", "visual_beat_max_gap_seconds"),
    ("motion", "pacing_rules", "sequence_change_target_seconds"),
    ("narration", "words_per_minute_range"),
    ("thumbnail", "variants_per_brief"),
    ("thumbnail", "safe_zone"),
    ("mobile", "safe_area"),
]
```

Run:

```bash
pytest tests/contracts/test_modern_archivist_playbook_contract.py -q
```

Expected: FAIL.

**Step 2: Patch the playbook**

Add exact keys under `styles/modern-archivist.yaml`:

```yaml
motion:
  pacing_rules:
    visual_beat_max_gap_seconds: 5
    sequence_change_target_seconds: [20, 35]
    anchor_return_target_seconds: [45, 60]

audio:
  ducking:
    attack_ms: 10
    release_ms: 150
    ratio: "4:1"
  narration_lufs_target: -16
  music_ceiling_db: -20

narration:
  words_per_minute_range: [125, 145]
  target_duration_tolerance_seconds: 5

thumbnail:
  variants_per_brief: 3
  safe_zone:
    center_width_pct: 0.72
    center_height_pct: 0.72
    avoid_top_pct: 0.10
    avoid_bottom_pct: 0.10

mobile:
  safe_area:
    min_text_px: 16
    avoid_edges_pct: 0.08

critical_error:
  max_duration_seconds: 12
```

Also clarify red usage in prose or comments: red is accent/pattern-interrupt color, not default small-text color.

**Step 3: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_playbook_contract.py -q
```

Expected: PASS.

### Task 1.2: Add a small contrast-safety rule to the playbook contract

**Objective:** Prevent inaccessible small red text from creeping into templates.

**Files:**
- Modify: `styles/modern-archivist.yaml`
- Modify: `tests/contracts/test_modern_archivist_playbook_contract.py`

**Step 1: Add a failing assertion**

Assert the playbook contains one of:
- a lighter red token for text, or
- an explicit rule that red is restricted to large labels/icons/pattern interrupts

**Step 2: Implement minimal contract text**

Add a quality rule such as:

```yaml
quality_rules:
  - "Red accents are for large labels, warnings, and pattern interrupts; do not use red for small body text on slate panels"
```

**Step 3: Verify**

Run the targeted test again.

---

## Phase 2: Make thumbnail packaging a first-class stage

### Task 2.1: Add `thumbnail` stage to the channel pipeline

**Objective:** Ensure every episode has structured thumbnail packaging before publish.

**Files:**
- Modify: `channels/modern-archivist/pipeline.yaml`
- Test: `tests/contracts/test_channel_package_boundary.py`

**Step 1: Write failing contract test**

Add a test that loads `channels/modern-archivist/pipeline.yaml` and asserts:
- a `thumbnail` stage exists after `render`
- it requires `episode` and `render_report`
- it produces `thumbnail_brief` and `thumbnail_variants`
- it is checkpointed and human-reviewed by default

Run:

```bash
pytest tests/contracts/test_channel_package_boundary.py::test_modern_archivist_pipeline_has_thumbnail_stage -q
```

Expected: FAIL.

**Step 2: Patch the pipeline**

Add a stage similar to:

```yaml
- name: thumbnail
  skill: channels/modern-archivist/skills/thumbnail-director.md
  required_artifacts_in:
    - episode
    - render_report
  produces:
    - thumbnail_brief
    - thumbnail_variants
  tools_available: []
  checkpoint_required: true
  human_approval_default: true
```

**Step 3: Verify**

Run the targeted test; expected PASS.

### Task 2.2: Upgrade the thumbnail director to multi-variant output

**Objective:** Change the thumbnail skill from single-concept advice into a structured packaging system.

**Files:**
- Modify: `channels/modern-archivist/skills/thumbnail-director.md`
- Test: `tests/contracts/test_modern_archivist_retention_contract.py`

**Step 1: Write failing test**

Assert the skill references:
- 3 variants by default
- safe-zone check
- title/headline distinction
- rationale for why each variant should win clicks

**Step 2: Patch the skill**

Change the output contract from one brief to:
- 3 ranked variants
- formula per variant
- headline per variant
- curiosity axis / click impulse
- safe-zone compliance check
- recommendation for initial upload winner

Add guidance on when the puppet is dominant versus when artifact/logo dominates.

**Step 3: Verify**

Run the targeted test; expected PASS.

---

## Phase 3: Add publish packaging as a required artifact

### Task 3.1: Create a publish packet schema

**Objective:** Define the canonical upload-package artifact.

**Files:**
- Create: `channels/modern-archivist/schemas/publish_packet.schema.json`
- Test: `tests/contracts/test_modern_archivist_publish_packet_contract.py`

**Step 1: Write failing schema test**

Create a schema-validation test for a packet containing:
- `episode_title_variants`
- `selected_title`
- `description`
- `chapters`
- `thumbnail_variants`
- `selected_thumbnail`
- `pinned_comment`
- `end_screen_target`
- `shorts_teaser`
- `packaging_notes`
- `ai_disclosure_review` with flags for realistic synthetic media, simulated real person voice/likeness, altered real event/place, realistic fake scene, YouTube disclosure required, rationale, and generated/recreated asset provenance notes

Run:

```bash
pytest tests/contracts/test_modern_archivist_publish_packet_contract.py -q
```

Expected: FAIL.

**Step 2: Create the schema**

Keep it narrow and deterministic. Do not bake creative logic into code. Include the AI/provenance disclosure review as an upload-safety artifact, not as an automated legal determination.

**Step 3: Verify**

Run the schema test; expected PASS.

### Task 3.2: Add `publish_prep` stage to the pipeline

**Objective:** Make upload packaging required before an episode is considered complete.

**Files:**
- Modify: `channels/modern-archivist/pipeline.yaml`
- Create: `channels/modern-archivist/skills/youtube-metadata.md`
- Test: `tests/contracts/test_channel_package_boundary.py`

**Step 1: Write failing contract test**

Assert:
- `publish_prep` exists after `thumbnail`
- it consumes `episode`, `render_report`, `thumbnail_brief`
- it produces `publish_packet`

**Step 2: Create skill**

The new skill should define outputs for:
- 2–3 title variants
- final recommended title
- description with source notes structure
- chapter list mapped to narrative phases
- pinned comment
- end-screen target recommendation
- teaser cut brief for Shorts

**Step 3: Patch pipeline**

Add the stage with checkpoint + human approval.

**Step 4: Verify**

Run targeted tests.

---

## Phase 4: Close the learning loop with retention review

### Task 4.1: Add retention review artifact contract

**Objective:** Make post-publish learning explicit and durable.

**Files:**
- Create: `channels/modern-archivist/schemas/retention_analysis.schema.json`
- Create: `channels/modern-archivist/skills/retention-analyst.md`
- Test: `tests/contracts/test_modern_archivist_retention_review_contract.py`

**Step 1: Write failing schema test**

Require fields like:
- `video_id`
- `observed_intro_retention_notes`
- `top_moments`
- `dips`
- `spikes`
- `thumbnail_ctr_notes`
- `title_fit_notes`
- `recommended_playbook_updates`

Run:

```bash
pytest tests/contracts/test_modern_archivist_retention_review_contract.py -q
```

Expected: FAIL.

**Step 2: Create schema + skill**

The skill should explicitly reference YouTube retention key moments:
- intro performance
- spikes
- dips
- moving successful moments earlier when appropriate

Do not hardcode platform scraping logic here; define the artifact and review lens first.

**Step 3: Verify**

Run the schema test; expected PASS.

### Task 4.2: Add `retention_review` stage to the pipeline

**Objective:** Ensure the pipeline architecture acknowledges post-publish iteration.

**Files:**
- Modify: `channels/modern-archivist/pipeline.yaml`
- Test: `tests/contracts/test_channel_package_boundary.py`

**Step 1: Write failing test**

Assert the stage exists and produces `retention_analysis`.

**Step 2: Patch pipeline**

Add:

```yaml
- name: retention_review
  skill: channels/modern-archivist/skills/retention-analyst.md
  required_artifacts_in:
    - publish_packet
  produces:
    - retention_analysis
  checkpoint_required: false
  human_approval_default: false
```

If actual analytics ingestion is not yet implemented, document this stage as a post-publish operational stage with manual artifact entry allowed.

**Step 3: Verify**

Run the targeted pipeline contract test; expected PASS.

---

## Phase 5: Tighten script-stage retention enforcement

### Task 5.1: Strengthen the script director contract

**Objective:** Push measurable retention language into the stage that most strongly determines watch time.

**Files:**
- Modify: `channels/modern-archivist/skills/script-director.md`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`

**Step 1: Write failing test**

Assert the script director references:
- WPM band or narration pacing target
- anchor return cadence
- no neutral section endings
- every section uses a named retention device
- sequence-type change cadence in dense sections

**Step 2: Patch the skill**

Add concise operational rules such as:
- narration target: 125–145 WPM
- every evidence-heavy stretch returns to anchor within 45–60 seconds
- every section ends on contradiction, escalation, reveal, payoff, or unresolved question
- every section must declare `retention_device`
- every 20–35 seconds introduce a new sequence type during dense body sections

**Step 3: Verify**

Run targeted test; expected PASS.

### Task 5.2: Tighten `episode.schema.json` where safe

**Objective:** Align the schema with the stronger script contract without over-constraining creative work.

**Files:**
- Modify: `channels/modern-archivist/schemas/episode.schema.json`
- Test: `tests/contracts/test_modern_archivist_episode_contract.py`

**Step 1: Add failing tests**

Focus on required presence, not artistic correctness:
- `retention_device` required on all sections
- `estimated_duration_seconds` required on all sections
- `visual_mode` and `color_state` required on all sections

**Step 2: Patch schema minimally**

Only require fields already treated as canonical by the skill/doctrine. Avoid schema rules that pretend to validate actual storytelling quality.

**Step 3: Verify**

Run targeted tests.

---

## Phase 6: Validate the end-state contract

### Task 6.1: Add a full-channel contract test

**Objective:** Prove the package now includes playbook metrics, packaging stages, and learning stages.

**Files:**
- Modify: `tests/contracts/test_channel_package_boundary.py`

**Step 1: Add a single contract test**

The test should assert all of the following:
- `styles/modern-archivist.yaml` includes performance-hardening keys
- `pipeline.yaml` includes `thumbnail`, `publish_prep`, and `retention_review`
- required skills/files exist
- publish and retention schemas exist

**Step 2: Run targeted suite**

```bash
pytest tests/contracts/test_channel_package_boundary.py tests/contracts/test_modern_archivist_* -q
```

Expected: PASS.

### Task 6.2: Run broader validation

**Objective:** Ensure the package changes did not break nearby channel contracts.

**Files:**
- No file changes

**Step 1: Run broader tests**

```bash
pytest tests/contracts -q
```

**Step 2: Run repo validation if appropriate**

```bash
make validate
```

Expected: PASS, or explicit non-related pre-existing failures documented.

---

## Acceptance criteria

The work is done when all of the following are true:
- Modern Archivist playbook includes measurable pacing/safe-area/narration constraints
- Thumbnail packaging is a required pipeline stage
- Upload packaging is represented as a first-class artifact and stage
- Retention review exists as a first-class post-publish artifact/stage
- Script-stage retention rules are more measurable than before
- Contract tests cover the new architecture
- No new orchestration drift was introduced into Python

## Risks and rollback notes

- Risk: over-constraining the schema can make creative iteration brittle.
  - Mitigation: require artifact fields, not subjective quality outcomes.
- Risk: adding too many stages could slow early pilot execution.
  - Mitigation: keep stages artifact-light and advisory where possible.
- Risk: post-publish analytics integration may not yet exist as a tool.
  - Mitigation: allow manual artifact creation first; automate later.
- Risk: title/thumbnail optimization can drift into generic clickbait.
  - Mitigation: keep shelf promise aligned with evidence-backed cold open.

## Recommended implementation order

1. Phase 1 playbook hardening
2. Phase 2 thumbnail stage
3. Phase 3 publish packet + publish_prep
4. Phase 5 script contract tightening
5. Phase 4 retention_review artifact/stage
6. Phase 6 validation sweep

## Handoff note

This plan is intentionally channel-package-first. A good implementation should mostly edit YAML, Markdown, JSON schema, and contract tests. Any Python changes should be minimal and justified by deterministic validation needs only.
