# Modern Archivist 2026 Performance Hardening Issue Breakdown — Task 5: Tighten script/episode retention contract

Plan: .ai/issues/2026-06-11-modern-archivist-performance-hardening-issues.md
Source PRD: docs/plans/2026-06-11-modern-archivist-performance-hardening-plan.md
Validation report: reports/validation/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-5-tighten-script-episode-retention-contract-validation-report.md
Review report: reports/reviews/2026-06-11-modern-archivist-2026-performance-hardening-issue-breakdown-task-5-tighten-script-episode-retention-contract-review-report.md

Objective:
Push measurable retention requirements into the script-stage skill and the episode schema without over-constraining creative judgment, while adding long-form narration/TTS quality guardrails.

Files:
- Modify: `channels/modern-archivist/skills/script-director.md`
- Modify: `channels/modern-archivist/schemas/episode.schema.json`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`
- Create or modify: `tests/contracts/test_modern_archivist_episode_contract.py`

Execution protocol:
1. Implement with a fresh subagent or tightly scoped local session.
2. Preserve the plan's module boundaries and smallest-shippable-slice scope.
3. Run targeted tests first, then broader validation.
4. Record command output and pass/fail evidence in the validation report.
5. Review tests first, then implementation, and record the verdict in the review report.
6. Turn QA findings into follow-up issues instead of silent TODOs.

Plan steps:
- Step 1: Add failing tests for WPM guidance, anchor return cadence, non-neutral section endings, and required retention-device/section fields.
- Step 2: Patch `script-director.md` with measurable pacing and section-ending rules.
- Step 3: Add long-form audio/TTS guidance where appropriate: section-sized generation blocks, prosody/listening QA, loudness normalization, and silence shaping that preserves documentary reveal pauses.
- Step 4: Patch `episode.schema.json` minimally to require fields already treated as canonical by the skill/doctrine.
- Step 5: Run targeted tests and capture results.

Original task body:
Objective: Push measurable retention requirements into the script-stage skill and the episode schema without over-constraining creative judgment.

Files:
- Modify: `channels/modern-archivist/skills/script-director.md`
- Modify: `channels/modern-archivist/schemas/episode.schema.json`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`
- Create or modify: `tests/contracts/test_modern_archivist_episode_contract.py`

Step 1: Add failing tests for WPM guidance, anchor return cadence, non-neutral section endings, and required retention-device/section fields.
Step 2: Patch `script-director.md` with measurable pacing and section-ending rules.
Step 3: Patch `episode.schema.json` minimally to require fields already treated as canonical by the skill/doctrine.
Step 4: Run targeted tests and capture results.

Acceptance criteria:
- Script director contains measurable retention rules instead of only qualitative advice.
- Script/audio guidance avoids one-pass long narration and preserves intentional documentary pacing.
- Episode schema requires the canonical per-section fields needed by downstream stages.
- Tests verify the stronger contract while avoiding subjective-storytelling assertions.

Blocked by: Task 1.
Type: AFK.
