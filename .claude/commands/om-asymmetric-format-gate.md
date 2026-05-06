# om-asymmetric-format-gate

Check whether an Asymmetric project has passed all format system gates. Returns a unified status report covering the full Phase 2S format machine plus the existing production sequence gates.

## How to Use

Run this command:
- At the start of any production session to get current status
- Before any gate that requires prior gates to pass
- When diagnosing why a project cannot proceed
- After completing a new artifact to confirm gate advancement

Provide the project ID. The command reads all artifacts across the project and reports pass/blocked status for each gate.

## What This Command Checks

### FORMAT SYSTEM GATES (Phase 2S — new upstream gates)

**Gate F1: Pacing DNA**
- `phase2r_pacing_dna.yaml` exists for this project (or channel-wide pacing DNA confirmed available)
- Pacing DNA targets have been reviewed before scripting
- Status: PASS | BLOCKED

**Gate F2: Packaging Test**
- `packaging_test.yaml` exists in project artifacts
- At least one title candidate shows `decision: PASS`
- At least one thumbnail concept shows `decision: PASS`
- Viewer promise is complete and `specific_enough: true`
- Proof promise is identified
- Alignment check confirms title/thumbnail/opening are aligned
- `operator_approved: true` and `approved_title_id` is set
- Status: PASS | BLOCKED

**Gate F3: Opening Sequence Proof**
- `opening_sequence_proof.yaml` exists in project artifacts
- At least one variant shows `decision: PASS`
- `operator_approved: true` and `approved_variant_id` is set
- Approved variant has `first_proof_or_conflict: true`
- Approved variant has `story_locked_by_second_30: true`
- Status: PASS | BLOCKED

### PRODUCTION SEQUENCE GATES (existing — verified here for unified status)

**Gate P1: Performance Package**
- `performance_package.md` exists in project artifacts
- All 7 dimensions at or above channel profile minimums
- Decision is PASS
- Operator approval recorded
- Status: PASS | BLOCKED

**Gate P2: Clip Quality**
- `source_clip_quality_manifest.yaml` exists
- At least 3 primary candidates pass all five quality dimensions (energy ≥4, relevance ≥4, texture ≥3, authority ≥4, cut_value ≥4)
- Operator approval of clip slate recorded
- Status: PASS | BLOCKED

**Gate P3: Scene Event Plan**
- `scene_event_plan.yaml` exists in project artifacts (project instance, not template)
- `sequence_analysis.plan_approved: true`
- `first_proof_hit_timestamp` ≤ 10 seconds
- `longest_unbroken_visual_mode_seconds` ≤ 5 for diagram sections
- `grammar_violations` is empty
- At least one `rule_zoom` or `document_punch_in` event present
- All clip events have `viewer_question_answered` populated
- Status: PASS | BLOCKED

**Gate P4: Pattern Break Plan**
- `pattern_break_plan.yaml` exists in project artifacts (project instance, not template)
- `compliance.plan_approved: true`
- `compliance.longest_gap_between_breaks_seconds` ≤ 12
- `compliance.at_least_one_rule_text_event: true`
- `compliance.every_diagram_section_interrupted: true`
- Status: PASS | BLOCKED

**Gate P5: Script and Beat Map**
- `script_beat_map.yaml` exists in project artifacts
- Hook in first narration beat
- Open loop planted within first 60 seconds
- Clip pressure present in mechanism section
- Payoff delivers a reusable mental model
- All clips in beat map are from approved manifest
- Narration WPM verified ≥130 for first 30 seconds
- Status: PASS | BLOCKED

**Gate P6: Render Readiness**
- `render_readiness_gate.md` exists with all gates PASS
- Operator approval of render recorded
- Status: PASS | BLOCKED

**Gate P7: Technical QC**
- Technical QC report exists for this render version
- No silence events >1 second
- No blank screen events
- Audio loudness within -23 to -14 LUFS
- Source labels present, in safe zone, no body text overlap
- Status: PASS | BLOCKED

### FORMAT SYSTEM REVIEW GATE

**Gate F4: Retention Postmortem**
- `retention_postmortem.yaml` exists for this render version
- `overall_result.overall_retention_grade` is not empty
- `system_changes` documented if any section failed
- Status: PASS | BLOCKED (BLOCKED only if render exists but retention postmortem has not been run)

### CREATIVE REVIEW GATE

**Gate CR: Manual Creative Review**
- Operator has watched the full render
- `creative_pass` status has been explicitly declared by the operator
- Status: PENDING (operator has not yet watched) | PASS | REVISE | REJECT
- Note: This gate is ALWAYS operator-only. The format gate command reads and reports the status; it never sets it.

## Output Format

A status report written to the console (not to an artifact file) with:

```
ASYMMETRIC FORMAT GATE — <project_id>
Report date: <date>

FORMAT SYSTEM GATES
  F1: Pacing DNA         [PASS | BLOCKED]
  F2: Packaging Test     [PASS | BLOCKED]
  F3: Opening Sequence   [PASS | BLOCKED]

PRODUCTION SEQUENCE GATES
  P1: Performance Package [PASS | BLOCKED]
  P2: Clip Quality        [PASS | BLOCKED]
  P3: Scene Event Plan    [PASS | BLOCKED]
  P4: Pattern Break Plan  [PASS | BLOCKED]
  P5: Script & Beat Map   [PASS | BLOCKED]
  P6: Render Readiness    [PASS | BLOCKED]
  P7: Technical QC        [PASS | BLOCKED]

REVIEW GATES
  F4: Retention Postmortem [PASS | BLOCKED]
  CR: Creative Review      [PENDING | PASS | REVISE | REJECT]

CURRENT STEP: <next action required>
BLOCKER: <specific artifact or approval missing>
```

## Blocker Resolution

For each BLOCKED gate, the command produces one specific resolution instruction:
- What artifact is missing
- What field in that artifact must be set
- Whether operator approval is required to advance

The command does not suggest workarounds or partial progress. A gate is PASS or BLOCKED. If BLOCKED, the specific blocker is named.

## Hard Rules This Command Enforces

- **Gate F3 (opening sequence proof) must pass before any research, scripting, or clip acquisition.** If F3 is BLOCKED, the command will block P1 evaluation — there is no point checking the performance package if the opening concept is not approved.
- **Gate CR status is read-only.** The command never writes `creative_pass`. It reads whatever status the operator has last set and reports it.
- **No gate may be bypassed by agent decision.** If the operator has not approved a required gate, it is BLOCKED regardless of whether an agent believes the underlying work is good.

## What This Command Does Not Do

- It does not write any artifacts
- It does not acquire media or generate assets
- It does not set `creative_pass`
- It does not approve any gate — it reads and reports what is already there
- It does not recommend skipping a BLOCKED gate

## Anti-Patterns This Command Prevents

- Starting research before the opening sequence proof is approved
- Starting scripting before clip quality gate is complete
- Initiating a render before the operator has explicitly approved render readiness
- Proceeding to a new episode without completing the retention postmortem on the current render
- Believing a project is production-ready without checking all format system gates in addition to the production sequence gates

## Notes

This command does not replace `/om-asymmetric-render-readiness`. The render readiness command checks detailed artifact content (asset files, audio paths, pipeline preflight). This command checks gate-level status across the full format system. Run `/om-asymmetric-render-readiness` before render; run `/om-asymmetric-format-gate` to understand the project's position in the full sequence.
