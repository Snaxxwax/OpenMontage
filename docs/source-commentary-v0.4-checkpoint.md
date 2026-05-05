# Source-Commentary Checkpoint v0.4: Rendered Local Pipeline with Real QC Gate

## 1. Current Status
The pipeline has achieved a functional end-to-end local vertical slice. We have successfully bridged high-level "Evidence Lock" logic with physical rendering and technical quality control.

- **Milestone:** v0.4
- **State:** Functional Prototype
- **Core Achievement:** Generated physical MP4 deliverables with verified source labels from high-level edit plans.

## 2. Verified Command
```bash
pytest tests/tools/test_media_qc_adapter.py \
       tests/pipelines/test_source_commentary_local_media_slice.py \
       tests/pipelines/test_source_commentary_render_poc.py \
       tests/pipelines/test_source_commentary_vertical_slice.py \
       tests/tools/test_source_commentary_render_adapter.py \
       tests/tools/test_clip_acquisition_adapter.py \
       tests/tools/test_clip_use_receipt_builder.py \
       tests/tools/test_evidence_candidate_matcher.py \
       tests/tools/test_transcript_index_builder.py \
       tests/tools/test_youtube_metadata_adapter.py \
       tests/contracts/test_source_commentary_contracts.py \
       -q -m "not manual"
```

## 3. Verified Result
- **Passed:** 60
- **Deselected:** 1
- **Warnings:** 34 (Expected jsonschema/Deprecation warnings)
- **Execution Time:** ~50s (includes physical FFmpeg/Remotion rendering)

## 4. Artifact Flow
1. **Source Discovery** (`source_candidate_manifest`)
2. **Evidence Search** (`evidence_candidate_manifest`)
3. **Evidence Gate** (`clip_use_receipts`)
4. **Acquisition** (`extracted_clip_manifest`) -> **Physical Extraction**
5. **Real QC Gate** (`approved_clip_manifest`) -> **Integrity Check**
6. **Edit Planning** (`source_commentary_edit_plan`)
7. **Render Adapter** (`edit_decisions` + `asset_manifest`) -> **Rendering Contract**
8. **Composition** (`renders/final.mp4`) -> **Physical Video**

## 5. Tools Implemented
- `SourceCommentaryEditPlanBuilder`: Aligns narration and evidence into a timeline.
- `MediaQCAdapter` (Hardened): Performs `ffprobe` duration/integrity checks.
- `SourceCommentaryRenderAdapter`: Lowers pipeline artifacts to the `video_compose` contract.

## 6. Real QC Behavior
Clips are now technically verified before reaching the edit stage:
- **Integrity:** Rejects zero-byte or missing files.
- **Provenance:** Rejects clips without a corresponding `clip_use_receipt`.
- **Duration:** Verifies `actual_duration` matches `expected_duration` (within 2s tolerance).
- **Labeling:** Dynamically generates "Source: [Channel]" text from receipt metadata.

## 7. Render POC Behavior
- **Path:** Routes via `video_compose` operation: `render` with `render_runtime: "remotion"`.
- **Labels:** Uses the `SectionTitle` overlay in the Remotion `Explainer` composition.
- **Deterministic:** Uses local FFmpeg-generated fixtures for zero-network testing.

## 8. Known Limitations
- **Transitions/Music:** Audio mixing and visual transitions (crossfades) are not yet wired.
- **Label Positioning:** Limited to `top-left` / `bottom-left` in the current Remotion component.
- **Narration:** Narration clips are planned in the timeline but not yet rendered/muxed.
- **YouTube Enforcement:** acquisition-gate currently trusts the requested range; tool-level buffer enforcement is pending.

## 9. Next Milestone: Agent Operating Contract
- **Goal:** Formalize the `agent-skills` and "Stage Director" markdown files so a LLM agent can drive the pipeline autonomously.
- **Demo:** A full agent-run demo from a `research_brief` to a `final.mp4`.

## 10. Do-Not-Touch Boundaries
- **No changes** to core `video_compose` or `remotion-composer` internals.
- **No changes** to the `ClipUseReceipt` schema (Evidence Lock is frozen).
- **No network calls** in standard test suite.
