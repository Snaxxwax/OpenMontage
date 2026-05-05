# Source Discovery Director - Source-Commentary Pipeline

## 1. Stage Purpose
Identify external media sources that potentially contain evidence for the claims in the `narration_claim_map`.

## 2. Inputs
- `narration_claim_map`

## 3. Outputs
- `source_candidate_manifest` (canonical artifact)

## 4. Allowed Tools
- `transcript_fetcher`
- `youtube_metadata_adapter` (metadata-only)

## 5. Forbidden Actions
- **BINARY DOWNLOADS ARE BANNED.** No MP4, MKV, or media files may be created.
- Accessing content without extracting/verifying metadata/transcripts.

## 6. Required Checks
- Verify `transcript_availability` for every source.
- Confirm metadata includes `uploader`, `duration`, and `title`.
- No media file exists in the project workspace after this stage.

## 7. Failure Conditions
- Manifest contains sources without verifiable transcripts or descriptions.
- Any tool call results in a local `.mp4` or `.wav` file.

## 8. Handoff Artifact Requirements
- `source_candidate_manifest` must map `source_id` to `source_url` and `metadata`.
- Explicit `review_focus` check: "No media file may be created in this stage."
