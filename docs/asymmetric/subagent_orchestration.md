# Asymmetric Subagent Orchestration Protocol

Canonical reference for how the main session invokes specialist agents across the complete pipeline — Phase 2S format gates and the 14-step production sequence.

---

## Section 1 — Orchestrator Role

The main session is the executive producer. It coordinates all pipeline stages, communicates with the operator, verifies artifacts, and surfaces blockers. It does not conduct research, write narration, score clips, generate opening variants, or render inline.

**Hard rule:** If the main session is writing narration, conducting source research, generating opening sequence variants, or running render commands inline — it is violating the orchestration contract. Invoke the correct agent.

Responsibilities the main session owns directly:
- Verifying prerequisites before invoking any agent
- Writing artifacts to disk when the invoked agent has no Write tool
- Checking completion messages for GATE RESULT and BLOCKERS
- Escalating all blockers to the operator — never resolving them silently
- Presenting operator approval gates and waiting for explicit confirmation

---

## Section 2 — Invocation Formula

Every Agent tool launch prompt must follow this structure:

```
CONTEXT:
  project_id: <id>
  phase: <gate or step label>
  artifact_directory: shared_studio/projects/<id>/artifacts/
  receipts_directory: shared_studio/projects/<id>/receipts/
  [clips_directory / renders_directory / qc_directory if relevant to this phase]

PREREQUISITE ARTIFACTS:
  [Paths only — the agent reads the files itself. Never paste file content here.]

TASK:
  [One paragraph. What must be produced. Name the exact output files. State
  non-negotiable constraints — gates that must pass, fields that must be set,
  behaviors that are forbidden.]

OUTPUTS REQUIRED:
  [Exact paths for each output. If the agent has no Write tool, state:
  "Return full content in completion message — main session writes to disk."]

COMPLETION MESSAGE REQUIRED:
  Follow docs/asymmetric/subagent_orchestration.md Section 4.
```

---

## Section 3 — Minimal Context Principle

Pass paths, never content. The agent reads the files itself.

**One exception:** A single explicit locked value needed as a direct parameter — for example, the operator-approved `render_runtime`, or a list of operator-approved clip candidate IDs. Pass these as literals in the TASK block only when the agent cannot safely derive them from any artifact file.

Do not paste the contents of any artifact file into a launch prompt. Long pasted content exhausts the agent's context before it can do the work.

---

## Section 4 — Completion Message Contract

Every agent must return a completion message in this format:

```
AGENT: <name>
PROJECT: <project_id>
PHASE: <gate/step label>
STATUS: COMPLETE | BLOCKED | PARTIAL

OUTPUTS WRITTEN:
  - <path>: <one sentence — what it contains and whether it is ready>
  [If no Write tool: "Returned in completion message for main session to write."]

GATE RESULT: PASS | FAIL | BLOCKED
  [One sentence per gate evaluated. State exactly which gate passed or failed.]

BLOCKERS:
  - What was attempted: <description>
  - What failed: <specific failure>
  - Issue type: gate_failure | missing_prerequisite | tool_error | external_source
  - Options available: <list without recommending — main session decides>
  [If none: "None."]

OPERATOR ACTION REQUIRED:
  [What the operator must do next. If none, state "None."]
```

---

## Section 5 — Verification Protocol

After every agent completes, before proceeding to the next step:

1. **Glob or check each expected output path** — confirm it exists and is non-empty.
2. **Read the first substantive section** — confirm it is populated, not a skeleton with placeholder fields.
3. **For timestamped receipts:** use `Glob receipts/staging_receipt_*.md` or `Glob receipts/render_receipt_*.md` sorted by modification time to find the latest.
4. **If any check fails:** surface to the operator as a blocker. Do not proceed.

The main session verifies independently. Never rely solely on the agent's self-reported STATUS field. An agent can report COMPLETE while writing an incomplete artifact.

---

## Section 6 — Blocker Handling

When a completion message contains a BLOCKER:

1. Read the BLOCKERS section carefully.
2. Do NOT retry, work around, or resolve the blocker inline.
3. Surface to the operator using this structure:
   - What was attempted
   - What failed
   - Issue type
   - Options available (verbatim from the agent's completion message)
4. Wait for operator instruction before taking any action.

The main session does not decide which option to pursue when a blocker involves a substantive pipeline decision. That is the operator's role.

---

## Section 7 — Foreground-Only Rule

All pipeline agents run foreground. Gated steps have hard prerequisites that must be verified before invocation. Do not background any pipeline agent.

Only one write-capable agent runs at a time. `om-writer` and `om-render-operator` both have Write/Edit access. Never invoke them concurrently.

---

## Section 8 — Write-Gap Pattern

Three agents have no Write tool:
- `om-performance-producer` (tools: Read, Glob, Grep)
- `om-researcher` (tools: WebSearch, WebFetch, Read, Glob, Grep)
- `om-source-clip-curator` (tools: WebSearch, WebFetch, Read, Glob, Grep, Bash)

These agents return full artifact content in their completion message. The main session writes the content to disk using the Write tool. This is intentional design — only `om-writer` and `om-render-operator` have file write authority for production artifacts.

`om-qc-reviewer` never writes files by design. All QC findings return in the completion message.

**Main session write pattern for no-Write agents:**
1. Receive completion message
2. Verify GATE RESULT and STATUS
3. Write artifact content to the correct path using Write tool
4. Run verification (Section 5)
5. Present to operator if an operator gate follows

---

## Complete Pipeline Gate Map

```
PHASE 2S FORMAT GATES (run before production sequence)
  F1: Pacing DNA         → main session (or om-researcher, pacing focus)
  F2: Packaging Test     → om-performance-producer
  F3: Opening Sequence   → om-writer (via /om-asymmetric-opening-proof)
  ↓ Operator approves F2 and F3 before production sequence begins

PRODUCTION SEQUENCE (14 steps)
  Step 2: Performance Package    → om-performance-producer       [operator gate: Step 3]
  Step 4: Research               → om-researcher
  Step 5: Clip Quality Gate      → om-source-clip-curator        [operator gate: Step 6]
  Step 7+8: Script + Rhythm      → om-writer (single invocation)
  Step 9: Render Readiness       → main session (reads artifacts directly)
  Step 11: Render + QC           → om-render-operator            [operator gate: Step 10]
  Step 12: QC Review             → om-qc-reviewer (conditional — see run-sequence Step 12)

POST-RENDER
  F4: Retention Postmortem       → om-qc-reviewer
  CR: Creative Review            → operator only (creative_pass: operator-only field)

STATUS VIEW: /om-asymmetric-format-gate <project_id>
```
