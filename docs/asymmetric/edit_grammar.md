# Asymmetric Edit Grammar

Version: 2.0
Status: Phase 2 — active
Last updated: 2026-05-06

---

## What This Document Is

This is the editorial grammar for all Asymmetric source-commentary productions. It defines the rules for pacing, structure, clip use, diagram behavior, pattern breaks, tension escalation, and payoff construction.

Every script, beat map, scene event plan, and visual rhythm plan must be checked against this grammar before the render readiness gate.

Any output that violates this grammar is not ready to render.

---

## Core Principle

The viewer should feel like they have been pulled into a private intelligence briefing mid-operation — not invited to a lecture.

Every decision in the grammar serves that sensation: conflict already in progress, pressure already building, mechanism about to become visible.

---

## 1. The First 3 Seconds Rule

The first 3 seconds must create an irreversible sensation.

The viewer cannot have time to decide whether to keep watching. The sensation must arrive before the decision.

**Required by second 3:**
- A constraint, conflict, or consequence is visible or audible
- OR a hard, concrete fact has been stated that is unexpected
- OR a person is visibly under institutional pressure

**Rejected by second 3:**
- Topic introduction
- Channel or brand setup
- Context-building narration
- Question posed to the viewer
- Generic b-roll with ambient narration

**The test:** Would a viewer who landed on this video at t=0 stop scrolling before t=3? If no, the opening is wrong.

---

## 2. The First 10 Seconds Rule

By second 10, the viewer must have seen the conflict from the outside and understood what is at stake.

The viewer does not need to understand the full mechanism yet. They need to feel the stakes.

**Required by second 10:**
- At least one source clip, proof hit, or hard text flash has appeared
- The open loop is forming — the viewer knows something is wrong but not why
- The narration has moved past surface setup and is pointing at a mechanism

**Rejected by second 10:**
- More than one uninterrupted narration-only passage longer than 4 seconds
- A diagram that is still being introduced without clip or proof pressure first
- Generic "here is what we will show you" framing
- Rhetorical questions used as hooks

---

## 3. The First 30 Seconds Rule

By second 30, the viewer is locked in or gone.

The first 30 seconds must deliver a complete mini-argument: conflict → mechanism → open question.

**Required by second 30:**
- At least 2 distinct visual modes have appeared (clip + diagram, or clip + flash, or flash + map)
- The open loop is explicit — the viewer has been shown the surface story and told it hides something
- At least one source-backed proof hit has occurred (clip, document, rule text, or institution named)
- Stakes are personal or concrete: a developer, a company, a user, a number — not an abstraction

**Rejected by second 30:**
- Still explaining the topic setup
- Only one visual mode used so far
- No concrete proof hit
- Stakes only stated abstractly ("this matters for millions of developers")

---

## 4. Visual Change Density

**Minimum targets:**
- In clip sections: meaningful change every 4–8 seconds
- In diagram sections: meaningful change every 3–5 seconds
- In flash/text sections: change every 1.5–3 seconds
- Across the full render: minimum 12 meaningful events per 75-second window

**What counts as a meaningful change:**
- New clip or clip cut within a clip
- New diagram element appearing
- Arrow extending or route closing
- Label or text replacing prior text
- Hard text flash entering or exiting
- Proof document punching in
- Map compression, expansion, or highlight shift
- Source label burn-in
- Split screen appearing or collapsing
- Pattern interrupt of any kind

**What does not count:**
- Narration continuing over an unchanged frame
- Same diagram with one additional label added but no composition change
- Slow fade or dissolve that does not change the underlying content

**Hard ceiling:**
No visual state may remain completely unchanged for more than 5 seconds in a diagram section or 8 seconds in a narrative or clip section. If a state must hold longer, a motion element (arrow, highlight, counter, expanding text) must be active within it.

---

## 5. Clip Interruption Rules

Source clips must interrupt the narration, not confirm it.

**A clip is used correctly when:**
- It appears before the narration has finished explaining what the clip shows
- The viewer sees the conflict or constraint operating before they understand why
- The clip creates pressure the narration then uses as leverage
- The clip is cut hard — no dissolve, no fade-in from black

**A clip is used incorrectly when:**
- The narration announces the clip ("here's what happened at the Senate hearing")
- The clip plays and confirms what was already said
- The clip is a decorative beat — removable without changing the video's emotional trajectory
- The clip holds longer than 10 seconds without a cut, flash, or overlay interrupting it

**Clip entrance rule:**
Clips cut in hard. No dissolve. No title card before a clip. The clip is the interruption.

**Clip exit rule:**
Clips cut out hard to either a hard text flash or a diagram element that converts the clip's content into a structural insight.

**Clip length rule:**
Primary source clips: 6–10 seconds in the edit, regardless of source duration.
Support clips: 3–6 seconds.
No clip runs longer than 12 seconds without a cut or overlay interrupting it.

---

## 6. Diagram Interruption Rules

Diagrams must be interrupted. They must not breathe.

A diagram that holds unchanged for more than 4 seconds is failing the viewer. The viewer has already read it.

**Required diagram behavior:**
- Every diagram section must have at least one of: motion element, text addition, arrow extension, node highlight, or clip cut out of and back to it
- No diagram state holds more than 4 seconds without a visual change inside it
- Diagrams enter on a cut or a hard snap — never a slow fade
- Diagrams exit into either a clip cut or a hard text flash — never a silent dissolve to black

**Diagram role enforcement:**
Every diagram in the render must be classified as one of:
- Pressure map (shows where force is applied)
- Route map (shows the approved path and the blocked alternate)
- Trap map (shows the options closing)
- Chokepoint map (shows where the system narrows)
- Extraction map (shows where value is taken)

A diagram that does not fit any of these roles is a lesson slide and must be cut.

**Diagram position rule:**
Diagrams must be earned with a setup. A source clip or a hard text flash that creates the question must appear before the diagram appears that answers it. A diagram that opens cold — with no prior clip or proof hit to motivate it — is a presentation, not a reveal.

---

## 7. Proof-Hit Timing

A proof hit is a moment where the argument becomes undeniable because a primary source makes the claim for you.

**Required proof hits:**
- Minimum 3 proof hits in a 60–90 second render
- First proof hit must occur by second 12
- Second proof hit must occur between seconds 20–40
- Final proof hit must be the setup for the payoff

**Proof hit forms (in order of force):**
1. Institutional conflict clip (senator, regulator, judge naming the violation)
2. Rule text zoom (policy document with the key phrase highlighted or zoomed)
3. Number flash (commission rate, market share, fee — precise, large, amber)
4. Document punch-in (screenshot of official document with rule visible)
5. Named entity proof (company name, case number, filing date — specific, not generic)

**What is not a proof hit:**
- Narration alone, even citing a source
- Generic b-roll labeled with a source name
- A diagram that illustrates the claim without showing primary source evidence
- A card with a quote that does not name an institutional or legal source

---

## 8. Pattern Break Cadence

Pattern breaks prevent the viewer from habituating to the rhythm.

**Required cadence:**
- Minimum one pattern break every 12 seconds
- No visual mode repeats more than twice in a row before a break
- Every diagram section of more than 6 seconds must include a motion interrupt or clip cut

**Pattern break types (in order of strength):**
1. Hard conflict clip cut (strongest — from diagram to testimony, hard cut)
2. Hard text flash (amber signal color, 2–5 words, 1.5–2.5 second hold)
3. Rule text zoom (cut into a document or policy text, zooming into the key phrase)
4. Split screen (simultaneous contrast — before/after, surface/mechanism, user view/developer view)
5. Number slam (number appears large, centered, with a short hold before narration continues)
6. Source label burn-in (label appears on clip, marking authority)
7. Map compression or expansion (diagram element that suddenly closes or expands)

**Pattern break anti-patterns:**
- Soft dissolve between two similar visual states
- Slow text card replacement
- Fade to black and fade back in
- Long cross-fades between clips

---

## 9. Tension Escalation Rules

The render must escalate. It cannot plateau.

**Tension arc required:**
- t=0–15s: tension introduced (conflict visible, open loop forming)
- t=15–35s: tension built (mechanism becomes visible, more proof hits, map tightening)
- t=35–50s: tension peak (the trap closes — the viewer sees the full chokepoint)
- t=50–65s: payoff (the mechanism is stated, the mental model delivered)

**No section may reduce tension once escalation has begun.** A neutral or explanatory section after a high-tension moment loses the viewer.

**Tension in narration:**
- Short sentences under the high-tension section (8 words or fewer)
- Longer sentences permitted only in the payoff
- Every sentence in the escalation section must either increase the stakes or advance the mechanism
- No sentence in the escalation section may begin with a hedge, qualification, or context-building phrase

**Tension in visuals:**
- More cuts = more tension
- Tighter diagram elements = more tension (nodes closer together, arrows shorter, gate narrower)
- Amber signal color increases = more pressure visible
- Red signal color appears only at peak tension (extraction, failure, consequence)

---

## 10. Payoff Rules

The payoff is the reason the video exists.

**Required payoff structure:**
- One sentence that is the reusable mental model — specific, structural, Asymmetric-brand
- The sentence must be statable without the video's context — it stands alone
- The sentence must apply beyond the specific example (Apple → any platform, App Store → any controlled infrastructure)
- The final visual must lock the mechanism in place — the last frame should be the diagram at its most compressed (trap fully closed, route fully blocked, extraction fully visible)

**The payoff test:**
Read the payoff sentence aloud. If it sounds like a summary of what was covered, it failed. If it sounds like a new tool the viewer now possesses, it passed.

**Example of a failed payoff:**
"So as you can see, Apple's App Store model gives them significant leverage over developers and users."
(This is a summary. It describes what was shown. It gives the viewer nothing they can use elsewhere.)

**Example of a passing payoff:**
"Apple does not need to own every app. It just needs to own the road money has to travel."
(This is a structural insight. The viewer now has a model: control the infrastructure, not the product.)

**Payoff visual requirement:**
The payoff narration must play over the final compressed map — the diagram in its most revealed state. No static text card. No blank screen. The mechanism should be visible while the mental model is delivered.

---

## 11. Retention Risk Rules

These are the failure modes that cause viewers to leave.

**Any of these constitutes a retention risk and must be removed before render:**

| Risk | Threshold | Fix |
|------|-----------|-----|
| Static diagram hold | >4 seconds | Add motion element or cut out to clip/flash |
| Back-to-back diagrams with no interruption | >8 seconds total | Insert hard text flash or clip cut between them |
| Narration-only passage with no visual change | >6 seconds | Add overlay, flash, or cut |
| Corporate-sounding sentence in narration | Any | Rewrite: shorter, more direct, no passive voice |
| Clip that could be removed without affecting tension | Any | Cut the clip or replace with a higher-energy clip |
| Payoff that is a summary | Any | Rewrite as a structural mental model |
| First 3 seconds without conflict | Any | Restructure the opening |
| Diagram that has not been earned with a prior clip or flash | Any | Insert earning moment before diagram |
| Source label overlapping body text or diagram elements | Any | Move label to safe zone or reduce text length |
| Silent tail | Any | Trim render or extend narration |

---

## What This Grammar Rejects

**Rejected patterns — hard rejections that require rework:**

- Clip → diagram → clip structure that repeats without interruption
- Diagrams that sit unchanged for the narration's full explanation
- Classroom flowcharts (left-to-right steps, boxes with labels, arrows connecting each step)
- Corporate explainer pacing (each section gets its own setup, explanation, and summary)
- Static text cards as the primary visual mode
- Neutral narration bridges between sections ("Now let us look at what happens when...")
- Evidence insert montage (clip plays, narration acknowledges it, clip exits, no change to tension)

**Preferred patterns:**

- Conflict clip opens with no context, narration arrives underneath
- Hard text flash converts a clip's testimony into a structural label
- Diagram enters mid-sentence, revealing the mechanism the clip was showing
- Map closes as the narration names the chokepoint
- Second clip cuts in to deepen the proof before the viewer has processed the first
- Payoff delivered over the final compressed diagram, not a text card

---

## Grammar Compliance Check

Before the render readiness gate, the scene event plan must be checked against:

- [ ] First 3 seconds: conflict or consequence visible
- [ ] First 10 seconds: at least one proof hit or hard text flash
- [ ] First 30 seconds: 2+ visual modes, open loop explicit, stakes concrete
- [ ] No static hold >5 seconds (diagrams), >8 seconds (narrative/clip)
- [ ] Minimum 12 visual events per 75-second window
- [ ] All clips: 6–10 seconds, enter hard, exit hard
- [ ] All diagrams: classified by role, earned by prior moment, interrupted by motion or cut
- [ ] Minimum 3 proof hits, first by second 12
- [ ] Minimum 1 pattern break every 12 seconds
- [ ] Tension arc: rising through t=50, payoff at t=50+
- [ ] Payoff: structural mental model, not summary
- [ ] Final frame: diagram at most compressed state
- [ ] No retention risk events listed in Section 11
