# Modern Archivist 2026 Performance Hardening Issue Breakdown — Task 2: Add thumbnail packaging stage + multi-variant brief contract

Plan: .ai/issues/2026-06-11-modern-archivist-performance-hardening-issues.md
Source PRD: docs/plans/2026-06-11-modern-archivist-performance-hardening-plan.md
Validation report: reports/validation/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-2-add-thumbnail-packaging-stage-multi-variant-brief-contract-validation-report.md
Review report: reports/reviews/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-2-add-thumbnail-packaging-stage-multi-variant-brief-contract-review-report.md

Objective:
Make thumbnail packaging a required pipeline stage with a structured three-variant output and explicit shelf-readability rules.

Files:
- Modify: `channels/modern-archivist/pipeline.yaml`
- Modify: `channels/modern-archivist/skills/thumbnail-director.md`
- Modify: `tests/contracts/test_channel_package_boundary.py`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`

Execution protocol:
1. Implement with a fresh subagent or tightly scoped local session.
2. Preserve the plan's module boundaries and smallest-shippable-slice scope.
3. Run targeted tests first, then broader validation.
4. Record command output and pass/fail evidence in the validation report.
5. Review tests first, then implementation, and record the verdict in the review report.
6. Turn QA findings into follow-up issues instead of silent TODOs.

Plan steps:
- Step 1: Add/extend contract tests asserting a `thumbnail` stage exists after `render` and produces structured thumbnail artifacts.
- Step 2: Patch `thumbnail-director.md` to require three ranked variants, safe-zone checks, and a recommended upload winner.
- Step 3: Patch `pipeline.yaml` to make thumbnail packaging checkpointed and human-reviewed.
- Step 4: Run targeted contract tests and capture results.

Original task body:
Objective: Make thumbnail packaging a required pipeline stage with a structured three-variant output and explicit shelf-readability rules.

Files:
- Modify: `channels/modern-archivist/pipeline.yaml`
- Modify: `channels/modern-archivist/skills/thumbnail-director.md`
- Modify: `tests/contracts/test_channel_package_boundary.py`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`

Step 1: Add/extend contract tests asserting a `thumbnail` stage exists after `render` and produces structured thumbnail artifacts.
Step 2: Patch `thumbnail-director.md` to require three ranked variants, safe-zone checks, and a recommended upload winner.
Step 3: Patch `pipeline.yaml` to make thumbnail packaging checkpointed and human-reviewed.
Step 4: Run targeted contract tests and capture results.

Acceptance criteria:
- `thumbnail` is a first-class pipeline stage.
- Thumbnail output contract requires 3 variants, clear rationale, and safe-zone awareness.
- Pipeline tests verify ordering, artifact names, and approval behavior.

Blocked by: Task 1.
Type: AFK.
