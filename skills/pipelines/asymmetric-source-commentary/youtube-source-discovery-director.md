# YouTube Source Discovery Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Identify YouTube videos that may contain proof, demos, quotes, or context. This stage remains metadata-only.

## 2. Inputs
- `source_query_plan`
- `source_candidate_manifest`

## 3. Outputs
- `youtube_source_manifest` at `artifacts/youtube_source_manifest.json`

## 4. Allowed Tools
- YouTube metadata lookup
- Transcript availability lookup
- Search result inspection

## 5. Forbidden Actions
- Downloading video or audio.
- Extracting frames.
- Approving clip use.
- Treating a video as usable without timestamp purpose and rights risk.

## 6. Required Checks
- Every video has `url`, `title`, `channel`, `source_role`, candidate ranges, and rights risk.
- Candidate ranges include purpose and claim ids when known.
- Prefer original researcher, vendor, conference, or firsthand demonstration sources.
- Record transcript availability.

## 7. Failure Conditions
- Candidate video lacks timestamp range for intended use.
- Source role is unclear.
- Rights risk is omitted.

## 8. Handoff Artifact Requirements
- Validate against `schemas/artifacts/youtube_source_manifest.schema.json`.
- Persist under Artifact Bus `artifacts/`.
