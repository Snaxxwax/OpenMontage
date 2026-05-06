# Asymmetric Channel Production Doctrine

Version: 1.0
Pipeline: `source-commentary`
Last updated: 2026-05-06

---

## 1. Channel Promise

Asymmetric is a systems-briefing channel for operators, founders, analysts, and high-agency professionals who want to know where power actually concentrates.

Tagline: **Where the leverage is.**

Every video must help the viewer answer at least one of:
- Who really controls this?
- Where does the system narrow?
- What is the chokepoint?
- What small input moves the whole system?
- Where does value leak?
- Who benefits from the current structure?

If leverage is not legible from the output, the output fails — regardless of technical quality.

---

## 2. Target Viewer Experience

The viewer should feel like they intercepted a private intelligence briefing that was not meant for them.

Not a lecture. Not a summary. Not a presentation.

A private briefing. Coming alive.

The first 30 seconds must create the sensation that the viewer has arrived mid-story — something already happened, something is already under pressure, and the viewer is just now being shown the mechanism.

By the end, the viewer should possess a reusable mental model — not just a collection of facts. Viewers share videos that gave them a framework.

---

## 3. What "High-Quality Output" Means

A high-quality Asymmetric output:

- Opens with a concrete, already-happened fact or visible contradiction — not a question, not setup
- Delivers a hook that would stop a scrolling viewer cold in under 5 seconds
- Creates a new open loop within the first 60 seconds that is not answered until late
- Alternates between clip pressure, diagram pressure, and narration punch — never one mode for more than 20 seconds
- Uses source clips to create conflict, constraint, and stakes — not to decorate or confirm
- Uses diagrams as trap maps, pressure maps, or route maps — not as explainer slides
- Labels every source with a safe-zone placement that never fights body text or proof visuals
- Delivers a reusable operator-level mental model as the payoff
- Passes a boredom stress test: no 5-second window where a random viewer would stop watching
- Has no silence over 1 second, no blank screens, no silent tails

---

## 4. What Counts as a Failed Output

Technical pass is not creative pass.

A render is a failed output if any of the following are true:

**Tone failures**
- Sounds like a corporate explainer or institutional overview
- Sounds like a business school case study
- Sounds like self-help or startup hype
- Sounds like an AI-generated documentary (sterile narration, no edge, no stakes)
- Has "AI-documentary smell": flat pacing, generic transitions, no point of view

**Structure failures**
- Opens with institutional context instead of tension
- Never establishes viewer stakes in the first 60 seconds
- Tells what happened without showing why it matters to the viewer
- Payoff is a summary instead of a reusable mental model
- Chapters are just time markers, not genuine narrative turning points

**Visual failures**
- More than 5 consecutive seconds of a static image or diagram
- Clips used as evidence inserts (drop clip in, pull clip out, narration continues unaffected)
- Diagrams look like PowerPoint explainer slides
- Source labels overlap body text, proof visuals, or key diagram elements
- Cards-only render submitted for a milestone that requires real source clips
- Blank screens at any point
- Silent tails at the end

**Clip failures**
- Low-energy keynote footage that shows the comfortable surface without pressure
- Generic developer tutorial or training footage
- Hearing footage where the selected range has no visible confrontation or constraint
- Clips that explain the mechanism instead of demonstrating the constraint

**Rhythm failures**
- Visual state unchanged for more than 5 seconds in diagram sections
- Visual state unchanged for more than 8 seconds in narrative sections
- Fewer than 12 meaningful visual events in any 75-second window
- Long narration passages with no visual progression underneath them

---

## 5. What the System Learned from Phase 1A and Phase 1B

### Phase 1A

Phase 1A proved the static render spine works. The OpenMontage source-commentary pipeline could produce a render with narration, source-labeled proof cards, and diagram cards without silence or blank frames.

Phase 1A failed creatively because:
- Visual change rate was too slow (cards held ~7.5 seconds instead of 3-5)
- The render used static proof cards only — no real source clips
- The output felt like a clean presentation with source citations, not a conflict-led YouTube cut
- Intellectual hook existed but viewer stakes were not established early enough

### Phase 1A.2

Phase 1A.2 improved the render: opened with tension, fixed audio loudness, removed second-half silence, increased visual states from 3 to 8, isolated source labels. Still only tested static cards and diagram cards. Visual change rate still slower than reference target.

### Phase 1B

Phase 1B proved real clip integration works in the pipeline. Clips could enter the source-commentary pipeline, get receipted, acquired, and composed.

Phase 1B failed because the selected clips had the wrong editorial character:
- App Store curation clip: calm, polished, no pressure — showed the comfortable surface
- StoreKit clip: developer education, explained plumbing instead of showing constraint
- Senate hearing clip: correct category, wrong timestamp range — no sharp confrontation visible

The clips made the video feel like a presentation with source inserts, not a conflict-led YouTube cut.

### Phase 1B.2

Phase 1B.2 created a source clip quality gate with scored criteria: clip energy, claim relevance, visual texture, authority, cut value. Identified 6 candidates that pass the gate. Acquisition blocked pending operator approval.

The lesson: source clips must be evaluated and approved for editorial force BEFORE acquisition — not after.

---

## 6. Technical Pass vs. Creative Pass

These are separate gates. Both must pass before a render ships.

**Technical pass** means:
- Duration within target range
- No silence over 1 second (silencedetect)
- No blank frames (blackdetect)
- Source labels present and readable on all proof moments
- Source labels in the designated safe zone, not overlapping body text
- Audio loudness within acceptable range
- All approved clips present and correctly trimmed

**Creative pass** means:
- The operator watched the full render
- The hook would stop a scrolling viewer
- The viewer stakes are established within 60 seconds
- Clip energy creates pressure, not just confirmation
- Visual rhythm is high enough to hold attention throughout
- The payoff is a reusable mental model
- No AI-documentary smell
- Asymmetric brand integrity is maintained

**Only the operator can grant creative pass.** No agent marks `creative_pass: true`. The operator watches and decides.

---

## 7. How Source Clips Must Create Story Pressure

Source clips are not footnotes. They are not evidence inserts. They are not decoration.

A source clip that merely confirms what the narration already said is a waste of cut time. It slows the video and adds no stakes.

A source clip must do at least one of these things:

**Create conflict before the narration explains it**
The viewer sees a person under pressure, an institution making a decision, a warning screen, or a confrontation — before the narration names what they're looking at.

**Show a constraint operating in real time**
The clip should make the rule visible as a constraint — not as policy text, but as something someone had to navigate, fight against, or enforce.

**Deliver authority the narration cannot**
A regulator naming a violation, a senator asking the direct question, a developer testifying under oath — these carry weight that narration cannot manufacture.

**Punch-cut value**
The clip should be cuttable to 8-14 seconds max. If the best moment requires more than 15 seconds of context to land, the clip is wrong. Find the sharper range or find a better clip.

**Anti-patterns to reject:**
- Calm keynote or training footage (shows the system as it wants to be seen, not as it operates under pressure)
- Generic B-roll of products, offices, or user interfaces (decorative, not evidential)
- Academic or tutorial explainer clips (explains instead of demonstrates)
- Long hearing ranges where no sharp question or answer appears in the selected window
- Any clip where "removing it" would not change the emotional trajectory of the video

---

## 8. Why Diagrams Must Act Like Pressure Maps

Diagrams in Asymmetric are not explainer slides. They do not walk the viewer through a system step by step. They reveal the hidden structure that the surface story conceals.

A diagram should function as one of:
- **Chokepoint map**: shows where the system narrows and who controls the narrow point
- **Trap map**: shows the path the actor is forced to take and why there is no exit
- **Route map**: shows the approved path, the blocked alternate path, and the toll at the gate
- **Pressure map**: shows where force is applied, by whom, and what it costs the other party
- **Extraction map**: shows where value is taken, who takes it, and who pays

A diagram that merely illustrates what the narration already said is a weak diagram. A strong diagram reveals something the narration has set up but not yet shown — it should make the viewer say "oh" when it appears.

Diagram rules:
- Every diagram should be earned with a verbal setup before it appears
- The diagram must be readable in under 3 seconds for a viewer who has not seen it before
- No diagram state should hold for more than 5 seconds without a meaningful change
- Every element of the diagram that is not directly supporting the argument should be removed

---

## 9. Why "Clean Explainer" Is Not Enough

A clean explainer tells you what a system is. It does not show you where the leverage is.

Clean explainers:
- Present the subject neutrally
- Walk through how something works
- Conclude with a summary
- Leave the viewer informed but not mobilized

Asymmetric videos:
- Open with a contradiction or constraint already in motion
- Reveal the mechanism that the surface story hides
- Show who benefits and who pays
- Deliver a reusable mental model the viewer can apply elsewhere
- Leave the viewer feeling like they now see something others miss

The editorial standard is not "did we explain it correctly?" It is "did we show where it narrows, who controls it, and why it matters?"

---

## 10. Anti-Patterns

### Corporate Explainer
Neutral tone. Institutional framing. Walks through the system without taking a position on where the leverage sits. Payoff is "here's how it works." Wrong.

### School-like Diagram
Step-by-step labeled flow chart. Walks the viewer through a process from left to right. Adds narration under each step. Looks like a slide deck. Wrong.

### Evidence Insert Montage
Series of clips dropped in to confirm narration claims. Each clip plays, narration acknowledges it, clip exits. No pressure, no conflict, no stakes. The clips could be removed and the video would be structurally identical. Wrong.

### Cards-Only Render
Static text cards and diagram cards submitted as the deliverable for a milestone that requires real source clips. Technically renders. Editorially incomplete. Wrong for any milestone with `clip_required: true`.

### Sterile AI-Documentary Feel
Smooth narration, clean transitions, generic stock-footage texture. Sounds like it was written by an AI and read by another AI. No edge. No stakes. No point of view. The viewer knows they are watching something generated, not discovered. Wrong.

### Intellectual Hook With No Stakes
Opens with a clever observation about a hidden mechanism but never establishes why the viewer should care. The system is interesting, but the viewer's connection to it is never activated. Wrong.

### Low-Energy Keynote/Training Footage
Clips sourced from product keynotes, developer tutorials, or corporate training materials. Shows the system as the platform wants it to be seen. Polished, calm, and designed to reassure. The opposite of pressure. Wrong.

---

## 11. Manual Operator Creative Approval Policy

The operator is the final gate. No production system, reviewer agent, or QC tool can substitute for manual operator review.

**When operator approval is required:**
1. After the performance package is complete — before research begins
2. After the clip quality gate evaluation — before acquisition begins
3. After the render readiness gate — before render begins
4. After technical QC — before creative pass is declared

**What the operator reviews at creative approval:**
- Watches the full render, not a summary
- Evaluates hook strength and viewer stakes in real time
- Evaluates clip energy and pressure as experienced, not as scored
- Evaluates visual rhythm by feel, not just by metric
- Evaluates Asymmetric brand fit
- Declares pass, revision required, or reject

**What the operator does not delegate:**
- `creative_pass: true` — operator only
- Final clip approval — operator only
- Performance package approval — operator only

If the operator is unavailable or has not watched the render, the project status is `awaiting_operator_review`. Production does not proceed.

---

## 12. Quick Reference: Gate Sequence

```
1. Performance package                → operator approval required
2. Research and source discovery      → auto-proceed
3. Clip quality gate evaluation       → operator approval required
4. Script and beat map                → auto-proceed after operator-approved clip slate
5. Visual rhythm plan                 → auto-proceed
6. Render readiness gate              → operator approval required
7. Render                             → auto-proceed
8. Technical QC                       → auto-proceed
9. Postmortem                         → auto-proceed
10. Creative review                   → operator watches, declares creative_pass
```
