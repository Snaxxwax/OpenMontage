# Transcript Index Director - Source-Commentary Pipeline

## 1. Stage Purpose
Create a searchable, local index of all text-based content found in the `source_candidate_manifest`.

## 2. Inputs
- `source_candidate_manifest`

## 3. Outputs
- `transcript_index` (canonical artifact)

## 4. Allowed Tools
- None (Internal processing of discovery artifacts).

## 5. Forbidden Actions
- Downloading media files.
- Indexing content not present in the manifest.

## 6. Required Checks
- Timestamps are preserved and normalized to seconds.
- Speaker labels are included if available in the source transcript.
- Semantic grouping of transcript segments.

## 7. Failure Conditions
- Transcript text is missing timestamps.
- Index refers to source IDs that do not exist in the manifest.

## 8. Handoff Artifact Requirements
- Must provide a searchable map of `source_id` -> `timestamped_segments`.
