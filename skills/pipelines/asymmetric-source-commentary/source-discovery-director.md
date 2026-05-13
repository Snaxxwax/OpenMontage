# Source Discovery Director - Asymmetric Source-Commentary Pipeline

## 1. Stage Purpose
Create a metadata-only source query plan and source candidate manifest for the approved viewer lens.

## 2. Inputs
- `asymmetric_greenlight`

## 3. Outputs
- `source_query_plan` at `artifacts/source_query_plan.json`
- `source_candidate_manifest` at `artifacts/source_candidate_manifest.json`

## 4. Allowed Tools
- Web search
- Documentation search
- Repository and issue search
- Metadata-only source inspection

## 5. Forbidden Actions
- Downloading or creating binary media files.
- Capturing screenshots or clips.
- Adding local media paths to source candidates.
- Using sources that cannot support a claim or viewer lens.

## 6. Required Checks
- Each query has intent, platform, and preferred source type.
- Each source has stable `id`, `url`, `kind`, `relevance`, and capture potential.
- Prefer primary sources: vendor docs, disclosures, papers, repos, issue threads, original demos.
- Label limitations when primary sources are weak or unavailable.

## 7. Failure Conditions
- Manifest is link-dump only.
- Candidate sources do not map to the greenlit viewer problem.
- Any binary media appears in the Artifact Bus before acquisition.

## 8. Handoff Artifact Requirements
- Validate against `source_query_plan.schema.json` and `source_candidate_manifest.schema.json`.
- Persist artifacts before proceeding.
