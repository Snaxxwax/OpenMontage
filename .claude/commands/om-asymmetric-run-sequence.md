# om-asymmetric-run-sequence

Main operator workflow checklist for Asymmetric productions. Enforces the complete production gate sequence. The main Claude session acts as executive producer. Do not use tmux as an orchestrator. Only one write-capable agent may run at a time.

Full invocation protocol for all agent calls: `docs/asymmetric/subagent_orchestration.md`

## How to Use

Run this command at the start of any new Asymmetric production session, or to get the current status of an in-progress project.

Provide the project ID. The command checks the status of each gate in sequence and tells you exactly where to resume.

---

## Phase 2S Format Gates (Run Before Production Sequence)

Status check: `/om-asymmetric-format-gate <project_id>`

These gates must pass before the production sequence begins. F2 and F3 require explicit operator approval. F1 is a prerequisite for F2.

### F1: Pacing DNA

**What:** Analyze 3+ reference videos to extract measurable pacing targets.

**Artifact:** `shared_studio/projects/<project_id>/artifacts/phase2r_pacing_dna.yaml`

**Orchestration:** Main session executes directly using `docs/asymmetric/high_retention_reference_workflow.md` as guide, OR invokes om-researcher with a pacing-focused prompt (see om-researcher Invocation Protocol). If delegating: launch prompt must include reference video paths/URLs and the pacing doc path. After completion: write `phase2r_pacing_dna.yaml` from completion message (if delegated).

**Pass condition:** ≥3 references analyzed; measurable targets defined for WPM, visual events per window, first proof timing, and pattern break frequency.

**Operator gate:** No — F1 is informational. Feeds F2 and the F3 invocation.

---

### F2: Packaging Test

**What:** Lock title, thumbnail, and viewer promise before research begins.

**Artifact:** `shared_studio/projects/<project_id>/artifacts/packaging_test.yaml`

**Agent:** om-performance-producer

**Orchestration:** Invoke om-performance-producer (foreground). Prompt: `project_id`, `phase="F2 Packaging Test"`, concept/working title, path to `phase2r_pacing_dna.yaml` if it exists. After completion: write `packaging_test.yaml` from completion message.

**Verify:** ≥1 title with `decision: PASS`; ≥1 thumbnail with `decision: PASS`; `viewer_promise.specific_enough: true`; `operator_approved: false` until operator confirms.

**Operator gate:** YES — operator must review, approve, and set `operator_approved: true` before F3 begins. Blocks F3 and the full production sequence.

---

### F3: Opening Sequence Proof

**What:** Generate 3–5 opening variants, score all 11 gates, get operator approval.

**Artifact:** `shared_studio/projects/<project_id>/artifacts/opening_sequence_proof.yaml`

**Agent:** om-writer (via `/om-asymmetric-opening-proof` command)

**Orchestration:** Invoke om-writer (foreground). Prompt: `project_id`, `phase="F3 Opening Sequence Proof"`, paths to approved `packaging_test.yaml` + `phase2r_pacing_dna.yaml` (if exists) + `docs/asymmetric/edit_grammar.md` + `docs/asymmetric/high_retention_format_system.md`. After completion: verify `opening_sequence_proof.yaml` was written to disk directly by the agent; verify ≥1 variant passes all 11 gates per GATE RESULT.

**Operator gate:** YES — operator must approve one variant and set `approved_variant_id` and `operator_approved: true`. Blocks all downstream work. Production sequence does not begin until this gate clears.

---

## The 14-Step Production Sequence

Every Asymmetric production must complete these steps in order. No step may be skipped. Operator approval steps are hard gates — production cannot proceed without explicit operator confirmation.

---

### STEP 1: Git Preflight

**What:** Verify the repo is in a clean state before any production work.

**Check:**
```
git status --short
```

**Pass condition:** No uncommitted changes to product code (pipeline_defs, tools, lib, remotion-composer, schemas).

**Note:** Untracked files in `shared_studio/projects/` are expected and safe — this directory is gitignored.

**Blocker:** Any uncommitted product-code changes. Resolve before proceeding.

---

### STEP 2: Performance Package

**What:** Evaluate the concept for hook strength, viewer stakes, leverage clarity, visual energy, boredom risk, Asymmetric fit, and title/thumbnail potential.

**Command:** `/om-asymmetric-performance-package`

**Pass condition:** All 7 dimensions at or above minimum. Decision: PASS.

**Output:** `shared_studio/projects/<project_id>/artifacts/performance_package.md`

**Blocker:** Leverage clarity below 4. Boredom risk high. Asymmetric fit below 3.

**Orchestration:** Invoke om-performance-producer (foreground). Prompt: `project_id`, `phase="Step 2 Performance Package"`, concept/working title, path to approved `packaging_test.yaml`, path to draft `performance_package.md` if one exists. After completion: write `performance_package.md` from completion message. Verify: all 7 scorecard rows populated; DECISION is not "pending". Do not proceed to Step 3 without writing the artifact to disk.

---

### STEP 3: Operator Approval — Performance Package

**What:** Operator reviews the performance package evaluation and explicitly approves or rejects.

**Required operator action:** State approval explicitly. "Approved" or "proceed" is sufficient. Silence is not approval.

**Blocker:** No production proceeds without this approval.

---

### STEP 4: Research and Source Discovery

**What:** Find primary sources, official records, and source video candidates that prove the chokepoint.

**Agent:** om-researcher (read-only research, no media acquisition)

**Output:** `shared_studio/projects/<project_id>/artifacts/research_brief.json` and `narration_claim_map.json`

**Pass condition:** Research brief identifies the mechanism from primary sources. Narration claim map has at least one verifiable source per major claim. Source video candidates identified for clip evaluation.

**Blocker:** Mechanism cannot be proven from primary sources — surface to operator before proceeding.

**Orchestration:** Invoke om-researcher (foreground). Prompt: `project_id`, `phase="Step 4 Research"`, path to approved `performance_package.md` and approved `packaging_test.yaml` (the packaging test defines the viewer promise, which shapes what must be proven). After completion: write `research_brief.json` and `narration_claim_map.json` from completion message. Verify: both files non-empty; `mechanism_confirmed`, `control_confirmed`, and `cost_confirmed` are all true; read gaps section; surface to operator if any major claim is unverifiable.

---

### STEP 5: Clip Quality Gate Evaluation

**What:** Score all source video candidates before acquisition.

**Command:** `/om-asymmetric-clip-quality-gate`

**Pass condition:** At least 3 candidates pass all five primary thresholds (clip energy ≥4, claim relevance ≥4, visual texture ≥3, authority ≥4, cut value ≥4).

**Output:** `shared_studio/projects/<project_id>/artifacts/source_clip_quality_manifest.yaml`

**Note:** `acquisition_allowed: false` on all candidates. No acquisition yet.

**Blocker:** Fewer than 3 primary-grade candidates exist. Return to research or change clip targeting approach.

**Orchestration:** Invoke om-source-clip-curator (foreground). Prompt: `project_id`, `phase="Step 5 Clip Quality Gate"`, paths to `performance_package.md` + `research_brief.json` + `narration_claim_map.json` + approved `packaging_test.yaml`. After completion: write `source_clip_quality_manifest.yaml` from completion message. Verify: ≥3 entries in `recommended_primary_clips`; all have `acquisition_allowed: false` and `approval_status: pending`. Present to operator for Step 6 approval.

---

### STEP 6: Operator Approval — Clip Slate

**What:** Operator reviews the scored clip manifest and approves specific candidates for acquisition.

**Required operator action:**
1. Review each candidate's scores and risk notes
2. Approve specific candidates by name
3. Confirm `acquisition_allowed: true` on approved candidates
4. Confirm `approval_status: approved` on approved candidates

**Blocker:** No clip may be acquired without explicit operator approval per candidate.

---

### STEP 7: Script and Beat Map

**What:** Write narration and map every beat to approved clips, proof moments, and visual events.

**Agent:** om-writer (requires approved performance package + approved clip slate as prerequisites)

**Output:**
- `shared_studio/projects/<project_id>/artifacts/script_beat_map.yaml`

**Pass condition:**
- Hook creates tension in line 1
- Open loop planted by 60 seconds
- Clip pressure in mechanism section
- Payoff delivers a reusable mental model
- All clips in the beat map are from the approved manifest
- Read-aloud check passed

**Blocker:** Script contains a summary payoff, no clip pressure in the mechanism, or clips not in the approved manifest.

---

### STEP 8: Visual Rhythm Plan

**What:** Map every visual event across the full runtime. Verify rhythm targets are achievable.

**Agent:** om-writer (produces as part of the same writing session as Step 7, or separately)

**Output:** `shared_studio/projects/<project_id>/artifacts/visual_rhythm_plan.yaml`

**Pass condition:**
- No gap >5 seconds in diagram sections
- No gap >8 seconds in narrative/clip sections
- Minimum 12 visual events per 75-second window
- All source labels in safe zone (lower 20% of frame)
- No label overlapping body text or diagram elements
- `rhythm_passes_targets: true`

**Blocker:** Plan cannot achieve rhythm targets — identify the sections and revise script or structure.

**Orchestration (Steps 7 and 8 combined):** Invoke om-writer ONCE for both outputs. Do not invoke twice — a single invocation must produce both `script_beat_map.yaml` and `visual_rhythm_plan.yaml`. Two sequential invocations risk inconsistency between the script and the rhythm plan. Prompt: `project_id`, `phase="Steps 7 and 8 Script and Visual Rhythm"`, paths to `performance_package.md` + `source_clip_quality_manifest.yaml` + `research_brief.json` + `narration_claim_map.json` + approved `opening_sequence_proof.yaml` (the approved variant drives the opening structure); list of operator-approved clip candidate IDs as explicit literals. After completion: both files are written directly by the agent — verify both exist and are non-empty. Read `rhythm_passes_targets`; if false, surface the specific failing sections to the operator before Step 9.

---

### STEP 9: Render Readiness Gate

**Orchestration:** Main session executes directly — no agent invocation needed. Evaluate all 8 gates by reading existing artifacts with Read and Glob tools. For Gate 8 (Local Tool Readiness): run `bash scripts/asymmetric_gpu_tool_status.sh` and `bash scripts/asymmetric_discover_local_tools.sh` if config is missing or unverified. For a unified gate status view: run `/om-asymmetric-format-gate <project_id>`.

**What:** Verify all 8 gates pass before render. Gate 8 (Local Tool Readiness) runs automatic local tool discovery if config is missing or unverified — the operator does not need to provide commands manually.

**Command:** `/om-asymmetric-render-readiness`

**Output:** `shared_studio/projects/<project_id>/artifacts/render_readiness_gate.md`

**Gate 8 automatic behavior:**
- If required local tool config is missing or unverified, discovery runs immediately: `bash scripts/asymmetric_discover_local_tools.sh`
- Discovery writes candidates to `config/asymmetric_local_tools.local.yaml` with `operator_verified: false`
- Validation runs: `bash scripts/asymmetric_validate_local_tool.sh <tool_name>`
- Gate 8 result is REVIEW_REQUIRED (not BLOCKED) if candidates were found
- Gate 8 result is BLOCKED only if discovery found nothing and no fallback is available
- Gate 8 result is DRAFT_ONLY if only draft-quality TTS fallback is available

**Pass condition:** All 8 gates show PASS. Gate 8 REVIEW_REQUIRED requires operator to confirm discovered tool config before Step 10 approval is valid.

**Blocker:** Any gate shows BLOCKED. Gate 8 DRAFT_ONLY requires explicit operator authorization before proceeding.

**Operator note:** You do not need to remember or provide Fish Speech or ComfyUI start commands. Discovery finds them. You only need to confirm the discovered config is correct.

---

### STEP 10: Operator Approval — Render

**What:** Operator reviews the render readiness gate report and explicitly approves the render.

**Required operator action:** Confirm render approval. State the approved render runtime (remotion / hyperframes / ffmpeg).

**If Gate 8 was REVIEW_REQUIRED:** also confirm the discovered local tool config is correct (i.e., explicitly state "local tool config looks correct, proceed" or set `operator_verified: true` in the config). This confirmation is required before the render may start. Silence does not clear REVIEW_REQUIRED.

**If Gate 8 was DRAFT_ONLY:** explicitly authorize the draft pass ("proceed as draft"). The render receipt will be labeled draft — not channel-ready.

**Blocker:** Operator has not reviewed the gate report. Render does not start without this approval.

---

### STEP 11: Render

**What:** Execute the render through the OpenMontage source-commentary pipeline.

**Agent:** om-render-operator

**Steps:**
1. Git preflight (clean tree confirmed)
2. **Local Tool Resolution** — mandatory before any narration or asset generation (see om-render-operator.md LTR steps):
   - Run `bash scripts/asymmetric_gpu_tool_status.sh`
   - If required tool has `operator_verified: true` and `safe_to_autostart: true`: start it
   - If a conflicting GPU tool is running and `safe_to_autostop: true`: stop it first, verify port clears
   - If an unknown GPU process is found: stop and surface to operator — do not kill
   - Write local tool receipt
3. Asset staging and staging receipt
4. Pipeline execution through source-commentary stages
5. Render receipt written

**Pass condition:** Render completes without pipeline errors. Render file exists at expected path.

**Blocker:** Pipeline error, missing asset, or tool unavailability — surface to operator with structured blocker report. Do not silently fall back to draft-quality tools.

**Orchestration:** Invoke om-render-operator (foreground). Prompt: `project_id`, `phase="Step 11 Render"`, all 5 directory paths (artifact, receipts, clips, renders, qc), operator-approved `render_runtime` as a literal value (this is the one explicit value exception to the minimal context principle), path to `render_readiness_gate.md`, and whether `draft_quality_audio: true` applies (state this explicitly if audio is from edge-tts fallback, so the render receipt is labeled correctly). After completion: use `Glob receipts/staging_receipt_*.md` and `Glob receipts/render_receipt_*.md` (sorted by mtime, not hardcoded) to find the latest receipts. Verify render file exists at the path stated in the render receipt. Read the technical QC report — all dimensions must PASS before the operator sees the render. If STATUS is BLOCKED: surface the structured blocker to the operator — do not retry silently.

---

### STEP 12: Technical QC

**What:** Run the full technical QC suite on the render.

**Agent:** om-render-operator (runs QC immediately after render) or om-qc-reviewer

**Checks:**
- Duration within target range
- No silence event >1.0 second
- No blank screen events
- Audio loudness within -23 to -14 LUFS
- Source labels present and readable in frame samples
- Source labels in safe zone (lower 20% of frame)
- No label overlapping body text

**Output:** `shared_studio/projects/<project_id>/qc/technical_qc_<timestamp>.md`

**Pass condition:** All technical checks pass.

**Blocker:** Any technical check fails — do not present render to operator. Fix root cause, re-render, re-QC.

**Orchestration:** Check whether om-render-operator wrote a `technical_qc_*.md` file in the qc directory. If yes and all checks passed: main session reads the file directly — no new agent invocation needed. If the QC file is missing or contains failures: invoke om-qc-reviewer (foreground) with the render file path + all prerequisite artifact paths. After completion: write `operator_review_packet.md` from the completion message. Only present the render to the operator after TECHNICAL QC STATUS is confirmed as PASS.

---

### STEP 13: Postmortem

**What:** Run the structured postmortem on the completed render.

**Command:** `/om-asymmetric-postmortem`

**Output:** `shared_studio/projects/<project_id>/artifacts/postmortem_<version>.md`

Mandatory after every render — pass or fail.

---

### STEP 14: Manual Creative Review

**What:** Operator watches the full render and declares creative pass, revise, or reject.

**Required operator action:**
- Watch the full render (not a summary)
- Fill out the operator review packet
- Declare the decision: creative_pass | revise | reject
- If revise: document specific changes required
- If reject: trigger next postmortem cycle before planning next render

**Hard rule:** Only the operator may set `creative_pass: true`. No agent, tool, or command does this.

---

## Status Check Mode

If you run this command mid-production, it checks which steps are complete and which are next:

1. Reads `shared_studio/projects/<project_id>/artifacts/` for existing artifacts
2. Reads `shared_studio/projects/<project_id>/qc/` for QC results
3. Reads `shared_studio/projects/<project_id>/receipts/` for render receipts
4. Reports current step and what is required to advance

Output: A numbered list of completed steps, current step, and next required action.

## Orchestration Rules

- The main Claude session is the executive producer — it coordinates steps and communicates with the operator
- Subagents (om-performance-producer, om-researcher, om-source-clip-curator, om-writer, om-render-operator, om-qc-reviewer) are used for specific task execution
- Only one write-capable agent runs at a time
- Do not use tmux as an orchestrator
- Do not assume subagents can safely spawn further subagents — route all inter-agent coordination through the main session
- Every operator approval must be explicit before proceeding to the next step
