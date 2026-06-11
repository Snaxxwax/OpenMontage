# Modern Archivist 2026 Performance Hardening Issue Breakdown — Task 4: Add retention review artifact + pipeline stage

Plan: .ai/issues/2026-06-11-modern-archivist-performance-hardening-issues.md
Source PRD: docs/plans/2026-06-11-modern-archivist-performance-hardening-plan.md
Validation report: reports/validation/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-4-add-retention-review-artifact-pipeline-stage-validation-report.md
Review report: reports/reviews/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-4-add-retention-review-artifact-pipeline-stage-review-report.md

Objective:
Close the performance loop by turning post-publish retention and CTR observations into a durable artifact and stage.

Files:
- Create: `channels/modern-archivist/schemas/retention_analysis.schema.json`
- Create: `channels/modern-archivist/skills/retention-analyst.md`
- Modify: `channels/modern-archivist/pipeline.yaml`
- Create or modify: `tests/contracts/test_modern_archivist_retention_review_contract.py`
- Modify: `tests/contracts/test_channel_package_boundary.py`

Execution protocol:
1. Implement with a fresh subagent or tightly scoped local session.
2. Preserve the plan's module boundaries and smallest-shippable-slice scope.
3. Run targeted tests first, then broader validation.
4. Record command output and pass/fail evidence in the validation report.
5. Review tests first, then implementation, and record the verdict in the review report.
6. Turn QA findings into follow-up issues instead of silent TODOs.

Plan steps:
- Step 1: Add failing tests for the retention-analysis artifact shape and stage existence.
- Step 2: Create the retention-analysis schema with intro notes, spikes, dips, top moments, CTR/title-fit notes, and playbook update recommendations.
- Step 3: Create the retention-analyst skill using YouTube retention-key-moment guidance as the review lens.
- Step 4: Patch `pipeline.yaml` to add the `retention_review` stage after `publish_prep`.
- Step 5: Run targeted tests and capture results.

Original task body:
Objective: Close the performance loop by turning post-publish retention and CTR observations into a durable artifact and stage.

Files:
- Create: `channels/modern-archivist/schemas/retention_analysis.schema.json`
- Create: `channels/modern-archivist/skills/retention-analyst.md`
- Modify: `channels/modern-archivist/pipeline.yaml`
- Create or modify: `tests/contracts/test_modern_archivist_retention_review_contract.py`
- Modify: `tests/contracts/test_channel_package_boundary.py`

Step 1: Add failing tests for the retention-analysis artifact shape and stage existence.
Step 2: Create the retention-analysis schema with intro notes, spikes, dips, top moments, CTR/title-fit notes, and playbook update recommendations.
Step 3: Create the retention-analyst skill using YouTube retention-key-moment guidance as the review lens.
Step 4: Patch `pipeline.yaml` to add the `retention_review` stage after `publish_prep`.
Step 5: Run targeted tests and capture results.

Acceptance criteria:
- A durable retention-analysis artifact exists.
- Pipeline architecture acknowledges post-publish learning as a real stage.
- Tests verify the stage and schema.

Blocked by: Task 3.
Type: AFK.
