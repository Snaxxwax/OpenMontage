# om-asymmetric-run-sequence

Main operator workflow checklist for Asymmetric productions. Enforces the complete production gate sequence. The main Claude session acts as executive producer. Do not use tmux as an orchestrator. Only one write-capable agent may run at a time.

## How to Use

Run this command at the start of any new Asymmetric production session, or to get the current status of an in-progress project.

Provide the project ID. The command checks the status of each gate in sequence and tells you exactly where to resume.

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

---

### STEP 5: Clip Quality Gate Evaluation

**What:** Score all source video candidates before acquisition.

**Command:** `/om-asymmetric-clip-quality-gate`

**Pass condition:** At least 3 candidates pass all five primary thresholds (clip energy ≥4, claim relevance ≥4, visual texture ≥3, authority ≥4, cut value ≥4).

**Output:** `shared_studio/projects/<project_id>/artifacts/source_clip_quality_manifest.yaml`

**Note:** `acquisition_allowed: false` on all candidates. No acquisition yet.

**Blocker:** Fewer than 3 primary-grade candidates exist. Return to research or change clip targeting approach.

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

---

### STEP 9: Render Readiness Gate

**What:** Verify all gates pass before render.

**Command:** `/om-asymmetric-render-readiness`

**Output:** `shared_studio/projects/<project_id>/artifacts/render_readiness_gate.md`

**Pass condition:** All 7 gates show PASS.

**Blocker:** Any gate shows BLOCKED — resolve before proceeding.

---

### STEP 10: Operator Approval — Render

**What:** Operator reviews the render readiness gate report and explicitly approves the render.

**Required operator action:** Confirm render approval. State the approved render runtime (remotion / hyperframes / ffmpeg).

**Blocker:** Operator has not reviewed the gate report. Render does not start without this approval.

---

### STEP 11: Render

**What:** Execute the render through the OpenMontage source-commentary pipeline.

**Agent:** om-render-operator

**Steps:**
1. Git preflight (clean tree confirmed)
2. Asset staging and staging receipt
3. Pipeline execution through source-commentary stages
4. Render receipt written

**Pass condition:** Render completes without pipeline errors. Render file exists at expected path.

**Blocker:** Pipeline error, missing asset, or tool unavailability — surface to operator with structured blocker report (what failed, why, options available).

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
