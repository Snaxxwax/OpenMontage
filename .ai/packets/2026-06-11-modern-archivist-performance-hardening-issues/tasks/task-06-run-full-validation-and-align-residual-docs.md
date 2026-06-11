# Modern Archivist 2026 Performance Hardening Issue Breakdown — Task 6: Run full validation and align residual docs

Plan: .ai/issues/2026-06-11-modern-archivist-performance-hardening-issues.md
Source PRD: docs/plans/2026-06-11-modern-archivist-performance-hardening-plan.md
Validation report: reports/validation/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-6-run-full-validation-and-align-residual-docs-validation-report.md
Review report: reports/reviews/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-6-run-full-validation-and-align-residual-docs-review-report.md

Objective:
Prove the hardened package works as a coherent contract and capture any remaining documentation alignment needed for future execution.

Files:
- Modify: `tests/contracts/test_channel_package_boundary.py`
- Modify: any newly added/edited contract tests as needed
- Modify: channel docs only if test failures expose a real contract mismatch

Execution protocol:
1. Implement with a fresh subagent or tightly scoped local session.
2. Preserve the plan's module boundaries and smallest-shippable-slice scope.
3. Run targeted tests first, then broader validation.
4. Record command output and pass/fail evidence in the validation report.
5. Review tests first, then implementation, and record the verdict in the review report.
6. Turn QA findings into follow-up issues instead of silent TODOs.

Plan steps:
- Step 1: Add or update a high-level channel contract test covering playbook keys, new stages, and required new skills/schemas.
- Step 2: Run targeted Modern Archivist contract suites.
- Step 3: Verify the final channel contract is local-first but not synthetic-first: ComfyUI/video diffusion may be optional source-asset support, but not required final-video infrastructure or hidden orchestration.
- Step 4: Run the broader contracts suite and `make validate` if feasible.
- Step 5: Record any non-related or pre-existing failures explicitly instead of burying them.

Original task body:
Objective: Prove the hardened package works as a coherent contract and capture any remaining documentation alignment needed for future execution.

Files:
- Modify: `tests/contracts/test_channel_package_boundary.py`
- Modify: any newly added/edited contract tests as needed
- Modify: channel docs only if test failures expose a real contract mismatch

Step 1: Add or update a high-level channel contract test covering playbook keys, new stages, and required new skills/schemas.
Step 2: Run targeted Modern Archivist contract suites.
Step 3: Run the broader contracts suite and `make validate` if feasible.
Step 4: Record any non-related or pre-existing failures explicitly instead of burying them.

Acceptance criteria:
- The package has a single coherent tested contract from playbook through retention review.
- Final docs preserve Remotion-first deterministic assembly and evidence-cinema defaults.
- Validation results are concrete and reproducible.
- Residual risks or unrelated failures are documented explicitly.

Blocked by: Tasks 2, 3, 4, and 5.
Type: AFK.
