# Source-Commentary Technical Contract

This document defines the technical boundaries and state management rules for the `source-commentary` pipeline.

## 1. Artifact Bus Layout
Every `source-commentary` project MUST follow this structure under `shared_studio/projects/<project_slug>/`:

- `artifacts/`: Canonical JSON artifacts (e.g., `research_brief.json`, `narration_claim_map.json`).
- `receipts/`: Collection of `clip_use_receipt` JSONs (the Evidence Lock).
- `clips/`: Physical MP4 extractions and local media assets.
- `assets/audio/`: Generated narration audio files (Fish Speech S2 Pro only).
- `renders/`: Final rendered video and `render_report.json`.
- `qc/`: Technical analysis results and logs from `MediaQCAdapter`.

## 2. Hard Receipt Gates (The Evidence Lock)
To ensure narrative integrity, you must enforce these gates:
- **No Acquisition:** The `clip_acquisition` stage is blocked if any approved clip lacks a schema-valid `clip_use_receipt`.
- **No Edit Planning:** The `edit_plan` stage is blocked if the `approved_clip_manifest` (produced by Media QC) is missing.
- **No Composition:** The `compose` stage is blocked if the `source_commentary_edit_plan` is missing.
- **Final Handoff:** You may only consider a project "finished" once a `render_report` exists and points to a physical MP4 file.

## 3. Tool & Phase Boundaries
- **Discovery Phase:** `source_discovery` and `transcript_index` are **metadata-only**. You are forbidden from creating or downloading binary media files in these stages.
- **Acquisition Phase:** `clip_acquisition` is the **first media-touching stage**. It must be strictly restricted to the time ranges defined in the receipts.
- **QC Phase:** Every clip MUST be passed through the `MediaQCAdapter` for technical verification (existence, size, duration) before being approved for the edit.
- **No Internals Rewrite:** You use existing tools and adapters. Do not rewrite `VideoCompose` or `VideoDownloader` logic.
- **Narration:** Piper is NOT approved for this pipeline. Fish Speech S2 Pro is the required high-fidelity narration engine.

## 4. Testing & Verification
- **Local First:** Standard tests and POCs must use local media fixtures (deterministic MP4s).
- **No Live Network:** Never trigger a live YouTube download during a standard test run.
- **Current Verified Status (v0.4):**
  - Baseline: 60 passed, 1 deselected, 34 warnings.
  - Features: Extraction, Hardened QC, Rendering POC (Remotion).

## 5. Human Checkpoints
The agent MUST pause and request approval at these specific stages:
1. **`clip_use_gate`**: Before starting any physical acquisition.
2. **`edit_plan`**: Before committing to a physical render.
3. **`qc`**: Final review of the rendered deliverable.
