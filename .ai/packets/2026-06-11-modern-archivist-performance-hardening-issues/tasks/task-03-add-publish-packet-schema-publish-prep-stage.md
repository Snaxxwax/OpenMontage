# Modern Archivist 2026 Performance Hardening Issue Breakdown — Task 3: Add publish packet schema + publish_prep stage

Plan: .ai/issues/2026-06-11-modern-archivist-performance-hardening-issues.md
Source PRD: docs/plans/2026-06-11-modern-archivist-performance-hardening-plan.md
Validation report: reports/validation/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-3-add-publish-packet-schema-publish-prep-stage-validation-report.md
Review report: reports/reviews/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-3-add-publish-packet-schema-publish-prep-stage-review-report.md

Objective:
Treat upload packaging as a first-class artifact so title, description, chapters, pinned comment, end-screen, teaser prep, and AI/provenance disclosure review are all generated before publish.

Files:
- Create: `channels/modern-archivist/schemas/publish_packet.schema.json`
- Create: `channels/modern-archivist/skills/youtube-metadata.md`
- Modify: `channels/modern-archivist/pipeline.yaml`
- Create or modify: `tests/contracts/test_modern_archivist_publish_packet_contract.py`
- Modify: `tests/contracts/test_channel_package_boundary.py`

Execution protocol:
1. Implement with a fresh subagent or tightly scoped local session.
2. Preserve the plan's module boundaries and smallest-shippable-slice scope.
3. Run targeted tests first, then broader validation.
4. Record command output and pass/fail evidence in the validation report.
5. Review tests first, then implementation, and record the verdict in the review report.
6. Turn QA findings into follow-up issues instead of silent TODOs.

Plan steps:
- Step 1: Add a failing schema-validation test for the publish packet artifact.
- Step 2: Create `publish_packet.schema.json` with title variants, thumbnail selection, chapters, description, pinned comment, end-screen target, teaser fields, and AI/provenance disclosure review fields.
- Step 3: Add `youtube-metadata.md` to define the packaging workflow and artifact contract.
- Step 4: Patch `pipeline.yaml` to add a checkpointed `publish_prep` stage after `thumbnail`.
- Step 5: Run targeted tests and capture results.

Original task body:
Objective: Treat upload packaging as a first-class artifact so title, description, chapters, pinned comment, end-screen, and teaser prep are all generated before publish.

Files:
- Create: `channels/modern-archivist/schemas/publish_packet.schema.json`
- Create: `channels/modern-archivist/skills/youtube-metadata.md`
- Modify: `channels/modern-archivist/pipeline.yaml`
- Create or modify: `tests/contracts/test_modern_archivist_publish_packet_contract.py`
- Modify: `tests/contracts/test_channel_package_boundary.py`

Step 1: Add a failing schema-validation test for the publish packet artifact.
Step 2: Create `publish_packet.schema.json` with title variants, thumbnail selection, chapters, description, pinned comment, end-screen target, and teaser fields.
Step 3: Add `youtube-metadata.md` to define the packaging workflow and artifact contract.
Step 4: Patch `pipeline.yaml` to add a checkpointed `publish_prep` stage after `thumbnail`.
Step 5: Run targeted tests and capture results.

Acceptance criteria:
- `publish_packet` exists as a schema-backed artifact.
- `publish_prep` is required before an episode is operationally complete.
- Upload packaging includes explicit YouTube altered/synthetic disclosure review and generated/recreated asset provenance notes.
- Tests verify artifact shape and stage placement.

Blocked by: Task 2.
Type: AFK.
