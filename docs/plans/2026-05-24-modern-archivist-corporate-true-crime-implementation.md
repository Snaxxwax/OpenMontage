# Modern Archivist Corporate True Crime End-to-End Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
**Goal:** Convert Modern Archivist / Failure Ledger into a source-footage/artifact-first Corporate True Crime pipeline, with content collection before scriptwriting, cinematic case-building visual contracts, Remotion-final assembly, optional HyperFrames segment generation, and objective render QC.
**Architecture:** Preserve OpenMontage's instruction-driven architecture. YAML manifests and Markdown director skills own stage order, runtime policy, visual policy, approval gates, review criteria, and fallback behavior. Python/TypeScript changes are limited to deterministic schemas, validators, renderer components, prop normalization, local asset materialization, and tests.
**Tech Stack:** Channel package under `channels/modern-archivist/`, YAML pipeline manifest, Markdown director skills, JSON schemas, pytest/jsonschema contract tests, TypeScript/React/Remotion renderer, optional HyperFrames via `hyperframes_compose`, FFmpeg/ffprobe for verification.

---

## ⚠️ Note: Character Rig Removed (2026-06-14)

The Modern Archivist character rig and puppet assets have been removed from the repository. The channel now operates as **evidence-cinema without a permanent puppet character** — using source footage, archived web, recreated UI, case-board sequences, kinetic typography, and evidence cards as the primary visual language. The Archivist identity persists through the channel frame (teal/crimson palette, typography, branding) but not as a full-body puppet layer.

Tasks 7.1 and 7.2 (puppet alpha fixes, full-body puppet contract) in Phase 7 are **obsolete** and should be skipped. The `visual-identity-reviewer.md` skill has been updated to reflect evidence-first visual checks without puppet-specific validations.

---

## Source of truth

Canonical channel brief:

- `channels/modern-archivist/design/channel-source-of-truth.md`

Supporting doctrine:

- `channels/modern-archivist/design/retention-doctrine.md`
- `channels/modern-archivist/CHANNEL.md`
- `channels/modern-archivist/pipeline.yaml`
- `docs/DEVELOPMENT_GUARDRAILS.md`

## Non-goals

- Do not create a generic SEC/court-document explainer channel.
- Do not move channel-specific logic into `pipeline_defs/` or generic `skills/pipelines/`.
- Do not add Python orchestration that decides topic, creative approach, runtime, provider, approval, or fallback behavior.
- Do not replace the full-body Modern Archivist puppet with portrait/head-only variants.
- Do not normalize multi-hour renders as acceptable. Performance problems are bugs.

## End-state pipeline

Target stage order:

```text
research -> content_collection -> script -> audio -> audio_analysis -> media_manifest -> asset_generation -> render
```

`content_collection` is the major new stage. It turns research into a visual feasibility packet before scriptwriting so episodes are written around what can be shown.

## Phase 0: Record doctrine and wire docs

### Task 0.1: Link source of truth from channel docs

**Objective:** Make the new channel source of truth discoverable from the channel package.

**Files:**
- Modify: `channels/modern-archivist/CHANNEL.md`
- Test: `tests/contracts/test_modern_archivist_retention_contract.py`

**Step 1: Add contract expectation**

Extend `test_channel_docs_and_directors_reference_retention_contract` to assert:

```python
assert "design/channel-source-of-truth.md" in channel
assert "Corporate True Crime" in channel
```

Run:

```bash
pytest tests/contracts/test_modern_archivist_retention_contract.py::test_channel_docs_and_directors_reference_retention_contract -q
```

Expected: FAIL until `CHANNEL.md` is patched.

**Step 2: Patch `CHANNEL.md`**

Add a short section after the channel premise:

```markdown
## Canonical development brief

The continuing source of truth for channel strategy and development is `design/channel-source-of-truth.md`. It defines the Corporate True Crime positioning, source-footage/artifact-first visual policy, topic selection rules, runtime split, and anti-patterns. If older exploratory notes conflict with that document, `design/channel-source-of-truth.md` wins unless the user explicitly supersedes it.
```

**Step 3: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_retention_contract.py::test_channel_docs_and_directors_reference_retention_contract -q
```

Expected: PASS.

### Task 0.2: Add source-of-truth contract test

**Objective:** Ensure future edits preserve the key doctrine.

**Files:**
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`

**Step 1: Add test**

```python
def test_channel_source_of_truth_names_corporate_true_crime_visual_policy() -> None:
    text = (CHANNEL_DIR / "design" / "channel-source-of-truth.md").read_text(encoding="utf-8")
    for term in [
        "Corporate True Crime",
        "Documents, charts, filings, and graphs are evidence. They are not the show.",
        "source footage",
        "Recreated digital artifacts",
        "content_collection",
        "runtime affinity",
        "Remotion remains the canonical final renderer",
        "HyperFrames is a first-class optional runtime",
    ]:
        assert term in text
```

**Step 2: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_retention_contract.py::test_channel_source_of_truth_names_corporate_true_crime_visual_policy -q
```

Expected: PASS.

## Phase 1: Add `content_collection` artifact contract

### Task 1.1: Create content collection schema

**Objective:** Define the canonical artifact produced between research and script.

**Files:**
- Create: `channels/modern-archivist/schemas/content_collection.schema.json`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Write failing schema test**

Create `tests/contracts/test_modern_archivist_content_collection_contract.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = ROOT / "channels" / "modern-archivist"


def test_content_collection_schema_accepts_source_footage_artifact_packet() -> None:
    schema = json.loads((CHANNEL_DIR / "schemas" / "content_collection.schema.json").read_text(encoding="utf-8"))
    packet = {
        "episode_id": "nikola-fake-truck",
        "visual_thesis": "The company sold motion before it sold a working truck.",
        "topic_gate": {
            "stakes": True,
            "failure_mechanism": True,
            "visual_artifacts": True,
            "public_evidence": True,
            "human_consequence": False,
            "decision": "greenlight",
            "notes": "Strong source footage and SEC/legal trail.",
        },
        "opportunities": [
            {
                "id": "opp_001",
                "kind": "source_footage",
                "title": "Truck demo sequence",
                "source_url": "https://example.com/demo",
                "evidence_refs": ["source_001"],
                "rights_status": "needs_review",
                "evidence_role": "primary_evidence",
                "runtime_affinity": "remotion",
                "visual_mode": "source_montage",
                "motion_plan": [
                    {"at_seconds": 0, "action": "show_source_frame"},
                    {"at_seconds": 3, "action": "reveal_contradiction_label"},
                ],
                "script_use": "cold_open",
            }
        ],
        "coverage_report": {
            "source_footage_count": 1,
            "recreated_artifact_count": 0,
            "document_only_count": 0,
            "chart_only_count": 0,
            "visual_feasibility": "strong",
            "boring_visual_risk": "low",
        },
    }
    Draft202012Validator(schema).validate(packet)
```

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py -q
```

Expected: FAIL because schema does not exist.

**Step 2: Create schema**

Create `channels/modern-archivist/schemas/content_collection.schema.json` with:

- required top-level fields: `episode_id`, `visual_thesis`, `topic_gate`, `opportunities`, `coverage_report`
- `topic_gate` booleans for the five greenlight criteria and `decision` enum: `greenlight`, `revise`, `park`, `reject`
- `opportunities[].kind` enum:
  - `source_footage`
  - `public_video`
  - `archived_web`
  - `recreated_ui`
  - `social_post`
  - `legal_evidence`
  - `sec_evidence`
  - `github_artifact`
  - `status_page`
  - `cinematic_metaphor`
  - `puppet_interaction`
- `runtime_affinity` enum: `remotion`, `hyperframes`, `either`
- `visual_mode` enum aligned to renderer/media modes, including `source_montage`, `case_file`, `case_file_sequence`, `data_sequence`, `failure_graph`, `code_walkthrough`, `cinematic_metaphor`, `critical_error`, `monologue`
- `evidence_role` enum: `primary_evidence`, `secondary_reporting`, `inference`, `allegation`, `admission`, `finding`, `settlement`, `conviction`, `dismissal`, `illustrative_only`
- `rights_status` enum: `usable`, `needs_review`, `recreate_only`, `unusable`, `unknown`

**Step 3: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py -q
```

Expected: PASS.

### Task 1.2: Add content collection template

**Objective:** Give agents and subagents a concrete artifact example.

**Files:**
- Create: `channels/modern-archivist/templates/content_collection.example.json`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Add failing template validation test**

Append:

```python
def test_content_collection_template_validates() -> None:
    schema = json.loads((CHANNEL_DIR / "schemas" / "content_collection.schema.json").read_text(encoding="utf-8"))
    template = json.loads((CHANNEL_DIR / "templates" / "content_collection.example.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(template)
```

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py::test_content_collection_template_validates -q
```

Expected: FAIL until template exists.

**Step 2: Create template**

Create a Nikola-oriented example with at least:

- one `source_footage` opportunity
- one `archived_web` opportunity
- one `legal_evidence` or `sec_evidence` opportunity
- one `puppet_interaction` opportunity
- one `cinematic_metaphor` opportunity labeled `illustrative_only`

**Step 3: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py -q
```

Expected: PASS.

## Phase 2: Insert `content_collection` into the channel pipeline

### Task 2.1: Add director skill for content collection

**Objective:** Make the stage instruction-driven rather than Python-orchestrated.

**Files:**
- Create: `channels/modern-archivist/skills/content-collection-director.md`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Add failing test**

Add:

```python
def test_content_collection_director_encodes_source_footage_first_policy() -> None:
    text = (CHANNEL_DIR / "skills" / "content-collection-director.md").read_text(encoding="utf-8")
    for term in [
        "What can we actually show?",
        "source footage",
        "recreated digital artifacts",
        "Documents, charts, filings, and graphs are evidence. They are not the show.",
        "runtime_affinity",
        "rights_status",
        "greenlight",
        "Reject or park a topic if it only has filings and charts",
    ]:
        assert term in text
```

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py::test_content_collection_director_encodes_source_footage_first_policy -q
```

Expected: FAIL until director skill exists.

**Step 2: Create director skill**

The skill must define:

- inputs: `research_packet`
- output: `content_collection`
- core question: “What can we actually show?”
- topic gate using the five greenlight criteria from the source of truth
- opportunity taxonomy and required fields
- rights/provenance classification
- runtime affinity guidance: Remotion vs HyperFrames vs either
- anti-patterns: document-only, chart-only, generic stock, unlabelled illustrative visuals
- review checklist

**Step 3: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py -q
```

Expected: PASS.

### Task 2.2: Modify pipeline manifest stage order

**Objective:** Insert `content_collection` between `research` and `script`.

**Files:**
- Modify: `channels/modern-archivist/pipeline.yaml`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Add failing pipeline test**

Add:

```python
import yaml


def test_channel_pipeline_inserts_content_collection_before_script() -> None:
    manifest = yaml.safe_load((CHANNEL_DIR / "pipeline.yaml").read_text(encoding="utf-8"))
    stage_names = [stage["name"] for stage in manifest["stages"]]
    assert stage_names.index("research") < stage_names.index("content_collection") < stage_names.index("script")
    stages = {stage["name"]: stage for stage in manifest["stages"]}
    content = stages["content_collection"]
    assert content["skill"] == "channels/modern-archivist/skills/content-collection-director.md"
    assert content["required_artifacts_in"] == ["research_packet"]
    assert content["produces"] == ["content_collection"]
    assert content["checkpoint_required"] is True
    assert "source footage" in "\n".join(content["review_focus"]).lower()
    assert "filings and charts" in "\n".join(content["review_focus"] + content["success_criteria"]).lower()


def test_script_stage_requires_content_collection() -> None:
    manifest = yaml.safe_load((CHANNEL_DIR / "pipeline.yaml").read_text(encoding="utf-8"))
    stages = {stage["name"]: stage for stage in manifest["stages"]}
    assert "content_collection" in stages["script"]["required_artifacts_in"]
```

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py::test_channel_pipeline_inserts_content_collection_before_script -q
```

Expected: FAIL until manifest is changed.

**Step 2: Patch manifest metadata**

Add to `metadata.artifact_paths`:

```yaml
content_collection: artifacts/content_collection.json
```

Add to `metadata.schemas`:

```yaml
content_collection: channels/modern-archivist/schemas/content_collection.schema.json
```

Add required skill:

```yaml
- channels/modern-archivist/skills/content-collection-director.md
```

**Step 3: Insert stage after research**

Add stage:

```yaml
- name: content_collection
  skill: channels/modern-archivist/skills/content-collection-director.md
  required_artifacts_in:
  - research_packet
  produces:
  - content_collection
  tools_available: []
  checkpoint_required: true
  human_approval_default: false
  review_focus:
  - Source footage, public video, archived web, product UI, or recreated artifact opportunities are identified before scriptwriting
  - Documents, filings and charts are treated as evidence moments, not the main visual surface
  - Topic passes at least three of five greenlight criteria or is explicitly parked/rejected
  - Every visual opportunity records provenance, rights_status, evidence_role, runtime_affinity, and intended script use
  - HyperFrames candidates are flagged for source-rich motion sequences without replacing Remotion final assembly
  success_criteria:
  - Schema-valid content_collection artifact exists at artifacts/content_collection.json
  - Coverage report classifies visual feasibility and boring_visual_risk
  - Reject or park a topic if it only has filings and charts
```

**Step 4: Patch script stage**

Change script `required_artifacts_in` from only `research_packet` to:

```yaml
required_artifacts_in:
- research_packet
- content_collection
```

Patch script review/success criteria to require script beats to map to content collection opportunity IDs.

**Step 5: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_content_collection_contract.py -q
pytest tests/contracts/test_pipeline_governance.py tests/contracts/test_channel_package_boundary.py -q
```

Expected: PASS or only unrelated pre-existing failures, which must be reported explicitly.

## Phase 3: Update director skills for visual-first scripting and media planning

### Task 3.1: Update script director

**Objective:** Make `content_collection` authoritative for script visual planning.

**Files:**
- Modify: `channels/modern-archivist/skills/script-director.md`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Add failing test**

```python
def test_script_director_requires_content_collection_visual_opportunities() -> None:
    text = (CHANNEL_DIR / "skills" / "script-director.md").read_text(encoding="utf-8")
    for term in [
        "content_collection",
        "visual opportunity",
        "opportunity IDs",
        "Do not write scenes around abstract ideas when the content_collection packet lacks visual material",
        "source-footage/artifact-first",
    ]:
        assert term in text
```

**Step 2: Patch director**

Add rules:

- script scenes must reference content_collection opportunity IDs where visual-dependent
- cold open must use the strongest source/artifact contradiction
- document-only beats must be rewritten into artifact scenes or compressed into receipt moments
- if content_collection marks `boring_visual_risk: high`, script must either narrow/reframe the topic or stop for operator review

**Step 3: Verify**

Run targeted test and then full content-collection contract test.

### Task 3.2: Update media director

**Objective:** Ensure media_manifest turns opportunities into local render inputs and motion plans.

**Files:**
- Modify: `channels/modern-archivist/skills/media-director.md`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Add failing test**

```python
def test_media_director_maps_content_collection_to_local_render_inputs() -> None:
    text = (CHANNEL_DIR / "skills" / "media-director.md").read_text(encoding="utf-8")
    for term in [
        "content_collection",
        "opportunity IDs",
        "local render inputs",
        "rights_status",
        "runtime_affinity",
        "source_montage",
        "recreated_ui",
    ]:
        assert term in text
```

**Step 2: Patch director**

Add a workflow:

1. Read `episode` and `content_collection`.
2. For each scene, map visual slot to one or more opportunity IDs.
3. Resolve source files or mark acquisition/recreation plan.
4. Convert raw evidence into local deterministic render inputs.
5. Prefer source_montage/recreated_ui/case_file/failure_graph over data_sequence when both work.
6. Preserve `runtime_affinity` for render-stage runtime selection.

**Step 3: Verify**

Run targeted tests.

### Task 3.3: Update review skills

**Objective:** Add explicit quality gates against boring visual output.

**Files:**
- Modify: `channels/modern-archivist/skills/review/evidence-auditor.md`
- Modify: `channels/modern-archivist/skills/review/visual-identity-reviewer.md`
- Modify: `channels/modern-archivist/skills/review/render-qc-reviewer.md`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Add failing test**

```python
def test_reviewers_guard_against_document_chart_channel_drift() -> None:
    files = [
        CHANNEL_DIR / "skills" / "review" / "evidence-auditor.md",
        CHANNEL_DIR / "skills" / "review" / "visual-identity-reviewer.md",
        CHANNEL_DIR / "skills" / "review" / "render-qc-reviewer.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for term in [
        "document-only",
        "chart-only",
        "source-footage/artifact-first",
        "boring visual risk",
        "content_collection",
    ]:
        assert term in combined
```

**Step 2: Patch review skills**

Add gate criteria:

- Evidence auditor: claims are safe and opportunity evidence roles are accurate.
- Visual identity reviewer: blocks drift into research deck/static receipt style.
- Render QC reviewer: frame samples must show source/artifact motion variety, not just charts/documents/puppet-over-text.

**Step 3: Verify**

Run targeted tests.

## Phase 4: Normalize artifact schemas for source-rich media

### Task 4.1: Extend episode schema for opportunity linkage

**Objective:** Let each scene section link to content_collection opportunities.

**Files:**
- Modify: `channels/modern-archivist/schemas/episode.schema.json`
- Modify: `channels/modern-archivist/templates/episode.example.json`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`

**Step 1: Add failing test**

Add a section field in the existing schema test:

```python
"content_opportunity_refs": ["opp_001"],
```

Assert schema accepts it.

**Step 2: Patch schema**

Add optional `content_opportunity_refs` as an array of strings on each section.

**Step 3: Patch template**

Add example refs to visual-dependent scenes.

**Step 4: Verify**

Run:

```bash
pytest tests/contracts/test_modern_archivist_retention_contract.py -q
```

### Task 4.2: Extend media schema with runtime affinity and local source fields

**Objective:** Preserve source provenance and runtime routing through media_manifest.

**Files:**
- Modify: `channels/modern-archivist/schemas/media.schema.json`
- Test: `tests/contracts/test_modern_archivist_retention_contract.py`

**Step 1: Add failing validation fixture**

Extend `test_modern_archivist_media_schema_accepts_retention_media_items` with a source montage item:

```python
validator.validate({
    "id": "source-001",
    "kind": "source_montage",
    "title": "Demo footage contradiction",
    "evidence_role": "primary_evidence",
    "evidence_refs": ["source_001"],
    "content_opportunity_refs": ["opp_001"],
    "runtime_affinity": "hyperframes",
    "rights_status": "needs_review",
    "local_assets": [{"path": "assets/source/demo-frame-001.png", "type": "image"}],
    "motion_plan": [{"at_seconds": 0, "action": "push_into_frame"}],
})
```

**Step 2: Patch schema**

Add optional fields:

- `content_opportunity_refs: string[]`
- `runtime_affinity: remotion | hyperframes | either`
- `rights_status: usable | needs_review | recreate_only | unusable | unknown`
- `local_assets[]` with `path`, `type`, optional `source_url`, `license_note`, `retrieval_date`

Add `source_montage` and `recreated_ui` to `kind` enum if missing.

**Step 3: Verify**

Run retention contract tests.

## Phase 5: Renderer support for source montage and recreated artifacts

### Task 5.1: Fix media overlay contract normalization

**Objective:** Prevent the known `media_overlay.type` vs renderer `media.kind` mismatch from dropping media.

**Files:**
- Modify: `channels/modern-archivist/remotion/src/state.ts` or current media normalization file
- Test: nearest TypeScript/unit test if present; otherwise add a lightweight test or fixture validation under `tests/render/`

**Step 1: Locate normalization**

Inspect:

```bash
rg "getActiveMediaSequence|media_overlay|kind|type" channels/modern-archivist/remotion/src remotion-composer/src
```

**Step 2: Add failing test or fixture**

Create a minimal fixture where a section has:

```json
"media_overlay": {"type": "source_montage", "beats": []}
```

Expected normalized media has `kind: "source_montage"`.

**Step 3: Implement normalization**

Normalize all incoming media overlays:

```ts
const kind = media.kind ?? media.type;
```

Ensure downstream components use normalized `kind`.

**Step 4: Verify**

Run:

```bash
npm --prefix channels/modern-archivist/remotion run typecheck
pytest tests/render/test_modern_archivist_smoke.py -q
```

If package scripts differ, inspect `channels/modern-archivist/remotion/package.json` and use the real script.

### Task 5.2: Ensure SourceMontage and RecreatedUI visual paths exist

**Objective:** Render source footage/artifact-first scenes instead of falling back to static cards.

**Files:**
- Modify: `channels/modern-archivist/remotion/src/components/MediaContainer.tsx`
- Modify/Create: `channels/modern-archivist/remotion/src/components/media/SourceMontage.tsx`
- Create if absent: `channels/modern-archivist/remotion/src/components/media/RecreatedUI.tsx`
- Modify: `channels/modern-archivist/remotion/src/fixtures.ts`

**Step 1: Add fixture scene**

Add a short fixture section with `visual_mode: "source_montage"` and local placeholder assets.

**Step 2: Route media kind**

Ensure `MediaContainer` routes:

- `source_montage` -> `SourceMontage`
- `recreated_ui` -> `RecreatedUI`
- existing modes still work

**Step 3: Implement minimal visual components**

`SourceMontage` should support:

- local image/video frames
- source label
- date label
- push/slide/reveal motion
- contradiction stamp overlay

`RecreatedUI` should support:

- URL/title bar
- page/app frame
- claim highlight
- before/after variant
- source/provenance label

**Step 4: Verify**

Run typecheck and smoke render. Build a contact sheet from smoke frames if the smoke render produces MP4.

## Phase 6: Runtime selection and HyperFrames segment path

### Task 6.1: Add runtime-affinity policy to render director

**Objective:** Make Remotion-vs-HyperFrames decision explicit and artifact-driven.

**Files:**
- Modify: `channels/modern-archivist/skills/render-director.md`
- Test: `tests/contracts/test_modern_archivist_content_collection_contract.py`

**Step 1: Add failing test**

```python
def test_render_director_uses_runtime_affinity_without_silent_swaps() -> None:
    text = (CHANNEL_DIR / "skills" / "render-director.md").read_text(encoding="utf-8")
    for term in [
        "runtime_affinity",
        "Remotion remains the canonical final renderer",
        "HyperFrames",
        "local segment assets",
        "Do not silently swap runtimes",
        "render_runtime_selection",
    ]:
        assert term in text
```

**Step 2: Patch render director**

Add policy:

- Check available runtimes via registry/provider menu.
- Present Remotion and HyperFrames if both are available.
- Recommend Remotion final assembly by default.
- Use HyperFrames only for approved segment assets or explicitly approved full-runtime experiments.
- Record options considered in render report/decision log.

**Step 3: Verify**

Run contract tests.

### Task 6.2: Define HyperFrames segment artifact convention

**Objective:** Allow HyperFrames to contribute local segment assets without replacing final Remotion assembly.

**Files:**
- Modify: `channels/modern-archivist/schemas/media.schema.json`
- Modify: `channels/modern-archivist/skills/media-director.md`
- Modify: `channels/modern-archivist/skills/render-director.md`

**Step 1: Extend media schema**

Add optional `segment_render` object:

```json
{
  "runtime": "hyperframes",
  "workspace_path": "assets/hyperframes/opp_001",
  "output_path": "assets/video/segments/opp_001.mp4",
  "status": "planned"
}
```

`status` enum: `planned`, `rendered`, `skipped`, `blocked`.

**Step 2: Update directors**

Media director may plan segment renders; render director executes or verifies them only after runtime approval.

**Step 3: Verify**

Run schema tests.

## Phase 7: Asset and puppet corrections

### Task 7.1: Fix puppet alpha assets

**Objective:** Eliminate white boxes caused by RGB/non-alpha puppet PNGs.

**Files:**
- Inspect/modify assets under `channels/modern-archivist/remotion/public/`
- Inspect/modify `channels/modern-archivist/assets/character/puppet_manifest.json`
- Test: add or extend asset validation test

**Step 1: Add alpha validation test**

Create a test that opens required puppet PNGs with Pillow and asserts mode is `RGBA` or has alpha.

Candidate test path:

```text
tests/contracts/test_modern_archivist_puppet_assets.py
```

**Step 2: Fix assets**

Use the existing clean semantic/outline-enforced source assets where possible. Do not regenerate via ComfyUI unless the saved assets cannot satisfy the contract.

**Step 3: Verify**

Run the asset test and a render smoke. Inspect frame samples for no white boxes.

### Task 7.2: Enforce full-body puppet contract

**Objective:** Prevent future partial/head-only puppet drift.

**Files:**
- Modify: `channels/modern-archivist/assets/character/puppet_manifest.json`
- Modify: `channels/modern-archivist/schemas/puppet_manifest.schema.json`
- Modify: `channels/modern-archivist/skills/review/visual-identity-reviewer.md`
- Test: `tests/contracts/test_modern_archivist_puppet_assets.py`

**Step 1: Add schema/test assertion**

Required manifest should declare full-body visible layers:

- body/torso
- head
- glasses
- mouth variants
- arm(s)
- mug/prop if used

**Step 2: Patch manifest/schema**

Add `rig_contract: "full_body"` and required layer groups.

**Step 3: Verify**

Run puppet contract tests.

## Phase 8: Evidence/source acquisition utilities as narrow tools or manual artifact protocol

### Task 8.1: Decide whether acquisition is docs-only or BaseTool-backed

**Objective:** Avoid ad hoc Python orchestration while enabling repeatable source collection.

**Files:**
- Modify: `channels/modern-archivist/skills/research-director.md`
- Modify: `channels/modern-archivist/skills/content-collection-director.md`
- Optional Create: `tools/research/source_artifact_collector.py` only if needed as a BaseTool

**Step 1: Start with director-skill protocol**

Define source collection requirements in Markdown first:

- source URL
- retrieval timestamp
- rights/provenance notes
- local cache path if downloaded
- claim/evidence mapping
- no render-time network fetches

**Step 2: Only add Python if needed**

If repeated manual steps become error-prone, add a narrow BaseTool that accepts explicit URLs and outputs JSON/local files. It must not decide what to collect.

Allowed tool behavior:

- fetch/capture a provided URL
- snapshot metadata
- write local file
- return JSON result

Forbidden tool behavior:

- choose the story
- decide source relevance
- approve rights
- pick runtime
- alter stage flow

**Step 3: Add tests if a tool is created**

Test contract fields, explicit inputs, deterministic output shape, and no hidden provider decisions.

## Phase 9: Render performance and QC

### Task 9.1: Add benchmark expectations to render QC

**Objective:** Treat excessive render times as a bug, not a timeout issue.

**Files:**
- Modify: `channels/modern-archivist/skills/render-director.md`
- Modify: `channels/modern-archivist/skills/review/render-qc-reviewer.md`
- Optional: add benchmark helper/test if existing harness supports it

**Step 1: Patch render QC criteria**

Add:

- report wall-clock render time
- report output duration
- compute render_speed_factor = wall_clock_seconds / output_seconds
- flag performance warning above target
- flag blocker above hard ceiling

Initial targets:

- short smoke render: under 4x real time
- 10-14 minute production target: operational goal under 2x real time after optimization
- any estimate over 30 minutes for a 10-14 minute episode requires performance diagnosis before publication-scale rendering

**Step 2: Verify with benchmark variant**

Use existing render smoke/benchmark harness. Do not simply raise timeouts.

## Phase 10: Pilot production validation

### Task 10.1: Produce a 60-90 second Nikola proof-of-format fixture

**Objective:** Validate the new source-footage/artifact-first pipeline before full episode production.

**Files:**
- Project workspace: `projects/nikola-proof-of-format/`
- Artifacts:
  - `artifacts/research_packet.json`
  - `artifacts/content_collection.json`
  - `artifacts/episode.json`
  - `artifacts/media_manifest.json`
  - `artifacts/render_report.json`

**Step 1: Create research packet**

Use a small, safe source set: official/public sources, archived page placeholders if necessary, and clearly labeled recreated visuals.

**Step 2: Create content_collection packet**

Must include at least:

- one source/demo visual opportunity
- one archived/recreated web opportunity
- one SEC/legal receipt moment
- one puppet interaction
- one cinematic metaphor labeled illustrative_only

**Step 3: Generate script and media manifest**

The script must reference content opportunity IDs.

**Step 4: Render short proof**

Use approved runtime split. Remotion final assembly is default; HyperFrames only for local segment asset if explicitly approved.

**Step 5: QC**

Verify:

- no white puppet boxes
- source/artifact visuals are visible
- visual change every 3-6 seconds
- no long document/chart holds
- audio sync and duration valid
- render speed reported

## Full validation command set

Run after implementation phases touching contracts/manifests:

```bash
pytest tests/contracts/test_modern_archivist_retention_contract.py -q
pytest tests/contracts/test_modern_archivist_content_collection_contract.py -q
pytest tests/contracts/test_pipeline_governance.py tests/contracts/test_channel_package_boundary.py -q
```

Run after renderer changes:

```bash
npm --prefix channels/modern-archivist/remotion run typecheck
pytest tests/render/test_modern_archivist_smoke.py -q
```

If scripts differ, inspect `channels/modern-archivist/remotion/package.json` and use the actual typecheck/build command.

## Acceptance criteria

The implementation is complete when:

1. `channels/modern-archivist/design/channel-source-of-truth.md` is linked from channel docs and guarded by tests.
2. `content_collection` exists as a schema-valid canonical artifact between research and script.
3. The pipeline manifest includes `content_collection` before script and script requires it.
4. Script/media directors require source-footage/artifact-first planning.
5. Media schema can carry opportunity refs, runtime affinity, rights status, local assets, and HyperFrames segment plans.
6. Renderer no longer drops media because of `media_overlay.type` vs `media.kind` mismatch.
7. Source montage/recreated UI scenes render as visible, moving scenes.
8. Puppet assets have alpha and preserve full-body rig identity.
9. Runtime policy presents Remotion and HyperFrames when both are available and records selection.
10. Render QC reports objective media visibility, audio validity, frame samples, and render speed.
11. A short proof-of-format render demonstrates the new cinematic Corporate True Crime direction without devolving into charts/documents.

## Recommended execution approach

Use `subagent-driven-development` for implementation:

- one fresh implementation subagent per phase or small task cluster
- main session verifies changed files and tests after each subagent
- run spec-compliance review first
- run code-quality review after spec passes
- commit after each passing phase if the repo workflow allows commits

