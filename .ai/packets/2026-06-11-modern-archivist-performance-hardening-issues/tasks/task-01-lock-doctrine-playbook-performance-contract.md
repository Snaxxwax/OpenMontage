# Modern Archivist 2026 Performance Hardening Issue Breakdown — Task 1: Lock doctrine + playbook performance contract

Plan: .ai/issues/2026-06-11-modern-archivist-performance-hardening-issues.md
Source PRD: docs/plans/2026-06-11-modern-archivist-performance-hardening-plan.md
Validation report: reports/validation/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-1-lock-doctrine-playbook-performance-contract-validation-report.md
Review report: reports/reviews/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-1-lock-doctrine-playbook-performance-contract-review-report.md

Objective:
Convert the new performance doctrine into durable docs/tests/playbook keys so future work has measurable pacing, safe-area, contrast rules, and a local-first but not synthetic-first channel stance.

Files:
- Modify: `channels/modern-archivist/design/retention-doctrine.md`
- Modify: `channels/modern-archivist/design/channel-source-of-truth.md`
- Modify: `styles/modern-archivist.yaml`
- Create or modify: `tests/contracts/test_modern_archivist_playbook_contract.py`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`

Execution protocol:
1. Implement with a fresh subagent or tightly scoped local session.
2. Preserve the plan's module boundaries and smallest-shippable-slice scope.
3. Run targeted tests first, then broader validation.
4. Record command output and pass/fail evidence in the validation report.
5. Review tests first, then implementation, and record the verdict in the review report.
6. Turn QA findings into follow-up issues instead of silent TODOs.

Plan steps:
- Step 1: Add or extend contract tests for doctrine references, playbook performance keys, and red-usage guardrails.
- Step 2: Patch channel doctrine docs to make packaging and post-publish review part of the official channel contract.
- Step 3: Add local-first but not synthetic-first doctrine: local tools are for cost/privacy/repeatability; real evidence, source footage, recreated UI/documents, and deterministic Remotion assembly remain the default.
- Step 4: Patch the playbook with measurable motion, narration, thumbnail safe-zone, mobile safe-area, audio ducking, and critical-error limits.
- Step 5: Run targeted contract tests and capture results.

Original task body:
Objective: Convert the new performance doctrine into durable docs/tests/playbook keys so future work has measurable pacing, safe-area, and contrast rules.

Files:
- Modify: `channels/modern-archivist/design/retention-doctrine.md`
- Modify: `channels/modern-archivist/design/channel-source-of-truth.md`
- Modify: `styles/modern-archivist.yaml`
- Create or modify: `tests/contracts/test_modern_archivist_playbook_contract.py`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`

Step 1: Add or extend contract tests for doctrine references, playbook performance keys, and red-usage guardrails.
Step 2: Patch channel doctrine docs to make packaging and post-publish review part of the official channel contract.
Step 3: Patch the playbook with measurable motion, narration, thumbnail safe-zone, mobile safe-area, audio ducking, and critical-error limits.
Step 4: Run targeted contract tests and capture results.

Acceptance criteria:
- Doctrine docs explicitly state that render is not the finish line and packaging/review are required.
- Playbook includes measurable performance keys rather than style-only prose.
- Channel docs reject long-form chained AI-video generation as the default visual architecture.
- Tests lock the new contract so it cannot silently drift.

Blocked by: None — can start immediately.
Type: AFK.
