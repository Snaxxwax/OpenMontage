# Source-Commentary Pipeline v0.1 Checkpoint

**Date:** May 4, 2026  
**Status:** Vertical Slice Verified (Local Real Media)

## 1. Goal
Implement a deterministic, policy-enforced artifact chain for the `source-commentary` pipeline, ensuring that evidence clips are matched, approved, acquired, and planned for edit without modifying OpenMontage internals.

## 2. Artifact Flow
`narration_claim_map` + `transcript_index`  
→ `evidence_candidate_manifest` (via `evidence_candidate_matcher`)  
→ `clip_use_receipts` (via `clip_use_receipt_builder`)  
→ `extracted_clip_manifest` (via `clip_acquisition_adapter`)  
→ `approved_clip_manifest` (via `media_qc_adapter`)  
→ `source_commentary_edit_plan` (via `source_commentary_edit_plan_builder`)

## 3. Tools Implemented
- `clip_use_receipt_builder.py`: Maps candidates to deterministic receipts with approval logic.
- `clip_acquisition_adapter.py`: Hardened media acquisition tool that performs physical `ffmpeg` trimming of source files.
- `media_qc_adapter.py`: Validates extracted clips and generates attribution labels.
- `source_commentary_edit_plan_builder.py`: Aligns narration claims with approved source evidence into a structural timeline.

## 4. Tests Added
- `tests/tools/test_clip_use_receipt_builder.py`: Schema validation, deterministic IDs, duration flagging.
- `tests/tools/test_clip_acquisition_adapter.py`: Policy enforcement, path safety, dry-run compliance, mocked extraction.
- `tests/pipelines/test_source_commentary_vertical_slice.py`: End-to-end artifact chain verification with mocked media.
- `tests/pipelines/test_source_commentary_local_media_slice.py`: Physical media extraction test using a local `ffmpeg`-generated MP4 fixture.

## 5. Verification
**Command:**
```bash
pytest tests/pipelines/test_source_commentary_local_media_slice.py \
       tests/pipelines/test_source_commentary_vertical_slice.py \
       tests/tools/test_clip_acquisition_adapter.py \
       tests/tools/test_clip_use_receipt_builder.py \
       tests/tools/test_evidence_candidate_matcher.py \
       tests/tools/test_transcript_index_builder.py \
       tests/tools/test_youtube_metadata_adapter.py \
       tests/contracts/test_source_commentary_contracts.py \
       -q -m "not manual"
```
**Result:** `50 passed, 1 deselected, 34 warnings`

## 6. Known Limitations
- Media acquisition is verified via mocks for `VideoDownloader`; real YouTube downloads are bypassed for safety.
- `media_qc_adapter` is a minimal pass-through (logical approval only).
- `source_commentary_edit_plan` handles primary evidence but lacks transition logic or title cards.

## 7. Next Milestone
**Rendering Proof-of-Concept**
- Use `source_commentary_edit_plan` to drive a real render.
- Integrate with `tools/video/remotion_caption_burn.py` or a custom `ffmpeg` concatenator.
- Produce a final video file where narration is synced to source clips.

## 8. Do-Not-Touch Boundaries
- **No changes to `VideoDownloader` or `VideoTrimmer` internals.** Use them only via their `execute()` interface.
- **No changes to `schemas/artifacts/`** unless a test demonstrates a critical missing field.
- **No live network calls** in standard test runs.
- **No weakening of `clip_use_receipt` approval enforcement.**
