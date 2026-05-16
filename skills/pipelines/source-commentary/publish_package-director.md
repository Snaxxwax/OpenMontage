# Stage: publish_package

## Inputs
- `source_commentary_qc_report` — must have `qc_passed: true`
- `source_commentary_render_report`
- `research_brief`
- `narration_claim_map`
- `approved_clip_manifest`

## Outputs
- `exports/publish_package/publish_package.json`
- `exports/publish_package/publish_package.md`

## Allowed Actions
- Read all five input artifacts
- Assemble `publish_package.json` against `schemas/artifacts/publish_package.schema.json`
- Write `package_status: "pending_review"` — operator sets `"approved"` manually
- Write `publish_package.md` as a single consolidated human-review file
- Validate `publish_package.json` before writing

## Forbidden Actions
- Proceeding if `source_commentary_qc_report.qc_passed` is not `true`
- Writing `package_status` as anything other than `pending_review` on first write
- Creating separate title, description, tag, or source Markdown files
- Uploading to YouTube, calling n8n, calling FastAPI, or any external service
- Auto-approving the package

## Stop Conditions
- `source_commentary_qc_report.qc_passed` is not `true`
- `publish_package.json` fails schema validation
- Any required input artifact missing

## Handoff Requirements
- `exports/publish_package/publish_package.json` exists and validates against schema
- `exports/publish_package/publish_package.md` exists
- `package_status` is `pending_review`
- Operator reviews both files and sets `package_status: "approved"` to authorize upload
