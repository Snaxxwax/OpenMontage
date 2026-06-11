# Modern Archivist 2026 Performance Hardening Issue Breakdown

Date: 2026-06-11
Source: docs/plans/2026-06-11-modern-archivist-performance-hardening-plan.md

Goal: Break the performance-hardening plan into independently dispatchable AFK slices that preserve the channel-package-first architecture and are ready for packet generation / Kanban export.

## Slice summary

1. AFK — Lock doctrine + playbook performance contract
2. AFK — Add thumbnail packaging stage + multi-variant brief contract
3. AFK — Add publish packet schema + publish_prep stage
4. AFK — Add retention review artifact + pipeline stage
5. AFK — Tighten script/episode retention contract
6. AFK — Run full contract validation and close documentation gaps

## Task 1: Lock doctrine + playbook performance contract

Objective: Convert the new performance doctrine into durable docs/tests/playbook keys so future work has measurable pacing, safe-area, and contrast rules.

Files:
- Modify: `channels/modern-archivist/design/retention-doctrine.md`
- Modify: `channels/modern-archivist/design/channel-source-of-truth.md`
- Modify: `styles/modern-archivist.yaml`
- Create or modify: `tests/contracts/test_modern_archivist_playbook_contract.py`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`

Step 1: Add or extend contract tests for doctrine references, playbook performance keys, and red-usage guardrails.
Step 2: Patch channel doctrine docs to make packaging and post-publish review part of the official channel contract.
Step 3: Add local-first but not synthetic-first doctrine: local tools are for cost/privacy/repeatability; real evidence, source footage, recreated UI/documents, and deterministic Remotion assembly remain the default.
Step 4: Patch the playbook with measurable motion, narration, thumbnail safe-zone, mobile safe-area, audio ducking, and critical-error limits.
Step 5: Run targeted contract tests and capture results.

Acceptance criteria:
- Doctrine docs explicitly state that render is not the finish line and packaging/review are required.
- Playbook includes measurable performance keys rather than style-only prose.
- Channel docs reject long-form chained AI-video generation as the default visual architecture.
- Tests lock the new contract so it cannot silently drift.

Blocked by: None — can start immediately.
Type: AFK.

## Task 2: Add thumbnail packaging stage + multi-variant brief contract

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

## Task 3: Add publish packet schema + publish_prep stage

Objective: Treat upload packaging as a first-class artifact so title, description, chapters, pinned comment, end-screen, and teaser prep are all generated before publish.

Files:
- Create: `channels/modern-archivist/schemas/publish_packet.schema.json`
- Create: `channels/modern-archivist/skills/youtube-metadata.md`
- Modify: `channels/modern-archivist/pipeline.yaml`
- Create or modify: `tests/contracts/test_modern_archivist_publish_packet_contract.py`
- Modify: `tests/contracts/test_channel_package_boundary.py`

Step 1: Add a failing schema-validation test for the publish packet artifact.
Step 2: Create `publish_packet.schema.json` with title variants, thumbnail selection, chapters, description, pinned comment, end-screen target, teaser fields, and AI/provenance disclosure review fields.
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

## Task 4: Add retention review artifact + pipeline stage

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

## Task 5: Tighten script/episode retention contract

Objective: Push measurable retention requirements into the script-stage skill and the episode schema without over-constraining creative judgment.

Files:
- Modify: `channels/modern-archivist/skills/script-director.md`
- Modify: `channels/modern-archivist/schemas/episode.schema.json`
- Modify: `tests/contracts/test_modern_archivist_retention_contract.py`
- Create or modify: `tests/contracts/test_modern_archivist_episode_contract.py`

Step 1: Add failing tests for WPM guidance, anchor return cadence, non-neutral section endings, and required retention-device/section fields.
Step 2: Patch `script-director.md` with measurable pacing and section-ending rules.
Step 3: Add long-form audio/TTS guidance where appropriate: section-sized generation blocks, prosody/listening QA, loudness normalization, and silence shaping that preserves documentary reveal pauses.
Step 4: Patch `episode.schema.json` minimally to require fields already treated as canonical by the skill/doctrine.
Step 5: Run targeted tests and capture results.

Acceptance criteria:
- Script director contains measurable retention rules instead of only qualitative advice.
- Script/audio guidance avoids one-pass long narration and preserves intentional documentary pacing.
- Episode schema requires the canonical per-section fields needed by downstream stages.
- Tests verify the stronger contract while avoiding subjective-storytelling assertions.

Blocked by: Task 1.
Type: AFK.

## Task 6: Run full validation and align residual docs

Objective: Prove the hardened package works as a coherent contract and capture any remaining documentation alignment needed for future execution.

Files:
- Modify: `tests/contracts/test_channel_package_boundary.py`
- Modify: any newly added/edited contract tests as needed
- Modify: channel docs only if test failures expose a real contract mismatch

Step 1: Add or update a high-level channel contract test covering playbook keys, new stages, and required new skills/schemas.
Step 2: Run targeted Modern Archivist contract suites.
Step 3: Verify the final channel contract is local-first but not synthetic-first: ComfyUI/video diffusion may be optional source-asset support, but not required final-video infrastructure or hidden orchestration.
Step 4: Run the broader contracts suite and `make validate` if feasible.
Step 5: Record any non-related or pre-existing failures explicitly instead of burying them.

Acceptance criteria:
- The package has a single coherent tested contract from playbook through retention review.
- Final docs preserve Remotion-first deterministic assembly and evidence-cinema defaults.
- Validation results are concrete and reproducible.
- Residual risks or unrelated failures are documented explicitly.

Blocked by: Tasks 2, 3, 4, and 5.
Type: AFK.
