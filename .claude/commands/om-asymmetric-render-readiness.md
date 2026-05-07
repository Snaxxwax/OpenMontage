# om-asymmetric-render-readiness

Check whether the current Asymmetric project is ready to render. This command runs after the script, beat map, and visual rhythm plan are complete — before any render is initiated.

## How to Use

Run this command when:
- The script, beat map, and visual rhythm plan are complete
- You want to verify all gates pass before requesting operator render approval
- Diagnosing why a render cannot proceed

Provide the project ID. The command reads all required artifacts and verifies each gate.

## What This Command Does

Checks all 8 render readiness gates against the `channels/asymmetric/channel_profile.yaml` thresholds:

### Gate 1: Performance Package
- Performance package exists in artifacts
- All 7 scorecard dimensions at or above minimum
- Decision is PASS
- Operator approval was recorded

### Gate 2: Clip Quality
- Source clip quality manifest exists
- At least 3 primary clips pass all five quality dimensions
- No primary clip has clip_energy_score below 4
- All approved clips have `acquisition_allowed: false` changed to `true` by operator
- All approved clips have `approval_status: approved`
- Operator approval is recorded with date and clip IDs

### Gate 3: Script and Beat Map
- Script beat map exists in artifacts
- Hook appears in the first narration beat
- Open loop planted within first 60 seconds
- Viewer stakes stated within first 60 seconds
- Clip pressure is present in the mechanism section
- Open loop is closed before or during the payoff section
- Payoff delivers a reusable mental model (not a summary)
- All clips in the beat map are in the approved clip manifest

### Gate 4: Visual Rhythm Plan
- Visual rhythm plan exists in artifacts
- No gap between visual events exceeds 5 seconds in diagram sections
- No gap exceeds 8 seconds in narrative/clip sections
- Minimum 12 visual events per 75-second window
- Pattern interrupts planned every 10-15 seconds in long sections
- rhythm_passes_targets: true

### Gate 5: Source Labels
- Every clip has a source label in the plan
- Every proof card has a source label in the plan
- All labels are in the bottom strip safe zone (lower 20% of frame)
- No label overlaps body text, proof text, or diagram elements

### Gate 6: Assets
- All narration audio files present
- All approved clips present in clips directory
- All clips verified against approved timestamp ranges
- Music decision documented
- Git status clean (no uncommitted product-code changes)

### Gate 7: Pipeline Preflight
- video_compose available for selected render runtime
- audio_mixer available
- source-commentary pipeline manifest unmodified

### Gate 8: Local Tool Readiness
Policy: `docs/asymmetric/local_gpu_tool_orchestration.md`
Discovery: `scripts/asymmetric_discover_local_tools.sh` — runs automatically if config is missing or unverified
Validation: `scripts/asymmetric_validate_local_tool.sh <tool_name>`

**Evaluation procedure:**

1. Identify which local GPU tools are required for this render phase (narration, image, video).
2. Check `config/asymmetric_local_tools.local.yaml`, then `config/asymmetric_local_tools.yaml`.
3. **If any required tool has no config entry, or has `operator_verified: false`, or has null commands:** run `bash scripts/asymmetric_discover_local_tools.sh` immediately. Do not mark BLOCKED until after discovery has run. Discovery is automatic — it does not require an operator instruction.
4. After discovery, run `bash scripts/asymmetric_validate_local_tool.sh <tool_name>` for each found candidate.
5. Assign gate state based on discovery result (see below).

**Gate 8 has four possible states:**

#### PASS
All of the following are true:
- Required local GPU tools identified
- Each required tool has a config entry with `operator_verified: true` and `safe_to_autostart: true`
- GPU conflict check run (`asymmetric_gpu_tool_status.sh`) — no unknown processes blocking required tools
- TTS provider is channel-quality (Fish Speech confirmed, or cloud API with valid key and quota)
- Local tool receipt written or confirmed not needed

#### REVIEW_REQUIRED
Discovery ran and found candidates, but operator has not yet verified them. Specifically:
- Discovery found a running process, a listening port, or an install path for the required tool
- Config was written with `discovery_status: likely` or `candidate`, `operator_verified: false`
- Operator must review the discovered command, confirm it is correct, and set `operator_verified: true`

**Action:** Present discovered candidates with confidence level. Gate clears when operator approves. Production may not proceed to render until operator responds. Do not interpret silence as approval.

#### DRAFT_ONLY
All channel-quality TTS paths are unavailable:
- Fish Speech: not found by discovery or cannot be started
- ElevenLabs: API key missing or quota exhausted
- OpenAI TTS: API key missing or quota exhausted
- Operator has explicitly authorized a draft pass
- `draft_quality_audio: true` will be set in all receipts for this render
- Output will be labeled draft in the render receipt — not channel-ready

This state allows draft validation passes only. Operator authorization is required to enter this state.

#### BLOCKED
Any of the following — after discovery has already run:
- Discovery found nothing (discovery_status: unknown) for a required tool, and operator has not provided a command manually
- An unknown GPU process is consuming VRAM and cannot be identified — operator must resolve before render proceeds
- Config entry has `safe_to_autostart: true` but `operator_verified: false` — unsafe state requiring operator correction
- All TTS paths unavailable and operator has not authorized a draft pass

Note: "config file missing" alone is NOT a BLOCKED condition. Run discovery first. Only mark BLOCKED if discovery also fails.

## Output

A completed render readiness gate report, written to:
`shared_studio/projects/<project_id>/artifacts/render_readiness_gate.md`

With a summary table showing PASS or BLOCKED for each gate and specific blockers with remediation steps.

## Operator Action Required

After this command completes:
- **All gates PASS:** Operator reviews the gate report and explicitly approves the render
- **Any gate BLOCKED:** Operator is informed of the specific blocker; production does not proceed to render until the blocker is resolved

The operator's render approval must be explicit. It is not implied by the gate report showing all-pass.

## Anti-Patterns This Command Prevents

- Rendering with an unreviewed performance package
- Rendering with clips that have not been operator-approved for acquisition
- Rendering with a visual rhythm plan that cannot achieve target change frequency
- Rendering with a payoff section that delivers a summary instead of a reusable model
- Rendering with source labels planned to overlap body text
- Rendering with uncommitted product-code changes in the working tree
- Rendering narration with edge-tts or Piper without marking the output as draft-quality
- Starting a GPU-heavy tool without checking for conflicts first
- Killing an unknown GPU process without operator confirmation
- Silently falling back to a low-quality TTS tool without recording the failure reason

## Notes

This command reads artifacts only — it does not write to any production file except the render_readiness_gate.md report. If assets are missing, it identifies which are missing and where they should be. It does not acquire, download, or generate assets.
