# Script Director — Animation Pipeline

## When to Use

This stage turns the approved proposal into animation-ready beats. The script must leave room for motion, staging, and hold time — and must integrate the research findings and respect the selected animation mode.

For **Asymmetric** pipelines, this director enforces a **retention-first systems documentary** style: fast editorial drama, hidden mechanisms, and real-world stakes.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/script.schema.json` | Artifact validation (Strict Retention Fields for Asymmetric) |
| Prior artifact | `proposal_packet` from Proposal Director | Selected concept, animation mode, target duration, reuse strategy |
| Optional artifact | `research_brief` from Research Director | Data points, proof, audience insights, accuracy constraints |
| Tools | `transcriber` | Optional source transcript support |

## Process

### 1. Absorb the Proposal

Read the `proposal_packet.selected_concept` thoroughly. Extract:

- **Title and hook** — the opening must deliver on this promise. (See Asymmetric Hook rules below).
- **Animation mode** — `manim`, `remotion`, `ai_video`, `diagram_stills`, or `mixed`. This constrains how you write.
- **Narrative structure** — `progressive_build`, `myth_busting`, `journey`, etc. Follow it.
- **Target duration** — Derive a word budget from target_seconds using documentary pacing:
  - Default narration pacing: **140–150 words/min**
  - Word budget = `target_duration_seconds / 60 * 140–150`
  - A 780s (13:00) target implies roughly **1,800–2,000 words**
  - **Hard gate**: If the script is outside **±10–15%**, it fails validation.
- **Key points** — from `selected_concept.key_points`
- **Reuse strategy** — recurring motifs mean recurring script structures

If `research_brief` is available, also extract:
- **Data points** — weave specific, sourced facts into the narration (not vague claims)
- **Audience misconceptions** — address them directly in the script
- **Mathematical accuracy notes** — constraints on what can and cannot be simplified

---

### [ASYMMETRIC ONLY] Retention Rules

If `style_playbook` is **Asymmetric**, the following rules are MANDATORY:

#### A. The Asymmetric Hook (First 20 Seconds)
The hook must deliver a concrete anomaly and a power system.
- **NO** "In this video...", "welcome back", "let's dive", "to understand this", "today we're going to", "this video is about".
- **NO** Throat-clearing.
- **GOOD:** "NVIDIA is worth trillions. Apple sells the phone. OpenAI sells the future. But none of them control the factory that makes the chips."

#### B. Retention Section Structure
Every section must follow this mini-arc:
**Question → Contradiction/Pressure → Mechanism → Proof → Consequence → Handoff**

Required Section Fields:
- `viewer_question`: What specific curiosity are we satisfying?
- `tension_type`: mystery / contradiction / escalation / constraint / bottleneck / etc.
- `open_loop`: The loop opened at the start.
- `proof_moment`: The specific fact/stat (must be framed as proof).
- `consequence`: The stakes.
- `payoff`: The resolution of the question.
- `next_open_loop`: The handoff line (empty for final section only).
- `visual_event_plan`: Timestamped visual beats every 5-8 seconds.

#### C. Language and Stat Framing
- **Short sentences** and concrete actors (The Buyer, The Factory).
- **Stats as Proof**: Stats are not exposition; they prove a claim or contradiction.
  - *Better:* "If this were a normal market, the top layer would split. It does not. Analysts estimate TSMC controls over ninety percent of the leading edge."

---

### 2. Write in Animation Beats

Each section should express ONE clear visual idea:

- **Statement** — introduce a concept (entrance animation)
- **Demonstration** — show it working (the main animation)
- **Transformation** — morph from one state to another (transition)
- **Comparison** — show two things side by side (split screen or sequential)
- **Conclusion** — land the insight (hold + emphasis)

**Animation mode affects writing style:**

| Mode | Writing Style |
|------|---------------|
| Manim | Precise, mathematical. Each beat maps to a specific geometric transformation. |
| Remotion | Data-driven, punchy. Each beat maps to a chart/component animation. |
| AI Video | Descriptive, evocative. Each beat describes a scene the AI should generate. |
| Diagram Stills | Explanatory, progressive. Each beat adds a layer to a building diagram. |

### 3. Keep On-Screen Text Tight

- **Max 8 words** for on-screen titles
- **Max 15 words** for on-screen descriptions
- Prefer phrases over sentences
- Mathematical notation is fine — it IS the content in math-animation mode

### 4. Leave Room for Visual Holds

Do NOT fill every second with new information. The scene plan will need time for:
- **Entrances** (0.5-1s): objects appearing on screen
- **Reveals** (1-2s): progressive disclosure of complexity
- **Holds** (1-3s): letting the viewer absorb what they see
- **Exits** (0.5s): clearing the stage for the next beat

**Rule of thumb:** Budget 3-4 seconds of visual breathing room for every 10 seconds of narration.

### 5. Use Metadata for Motion Intent

Recommended metadata keys per section:
- `beat_type`: statement / demonstration / transformation / comparison / conclusion
- `animation_mode`: which mode this section uses
- `text_constraints`: max words for on-screen text in this section
- `narration_plan`: how narration relates to visual (describes / complements / silent)
- `visual_priority`: what the viewer should focus on
- `hold_time_seconds`: minimum visual hold time after this section
- `data_source`: reference research data point

### 6. Research Integration

- Use at least 2 data points from the research in the narration.
- Ground the hook in the research's most surprising finding.
- Cite sources naturally ("According to [source]...").
- Do NOT invent statistics.

### 7. Quality Gate

Before submitting the script, verify:
- [ ] Every section supports ONE strong visual idea.
- [ ] **Word count accuracy**: Within ±10–15% of target for the duration.
- [ ] **[Asymmetric]** Hook lacks forbidden phrases.
- [ ] **[Asymmetric]** Every section has retention metadata and `visual_event_plan`.
- [ ] **[Asymmetric]** Visual events occur every 5-8 seconds.
- [ ] Animation mode is respected.
- [ ] Research data points are integrated.

## Common Pitfalls

- **Writing too many ideas into one section.** One beat = one visual idea.
- **Forgetting visual holds.** Motion needs pause and emphasis.
- **Ignoring the animation mode.**
- **Silent compression**: Cutting words to fit a shorter-than-requested duration.
