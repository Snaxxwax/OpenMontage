# om-asymmetric-render-readiness

Check whether the current Asymmetric project is ready to render. This command runs after the script, beat map, and visual rhythm plan are complete — before any render is initiated.

## How to Use

Run this command when:
- The script, beat map, and visual rhythm plan are complete
- You want to verify all gates pass before requesting operator render approval
- Diagnosing why a render cannot proceed

Provide the project ID. The command reads all required artifacts and verifies each gate.

## What This Command Does

Checks all 7 render readiness gates against the `channels/asymmetric/channel_profile.yaml` thresholds:

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

## Notes

This command reads artifacts only — it does not write to any production file except the render_readiness_gate.md report. If assets are missing, it identifies which are missing and where they should be. It does not acquire, download, or generate assets.
