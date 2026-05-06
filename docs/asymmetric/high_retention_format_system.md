# Asymmetric High-Retention Format System

Version: 1.0
Status: Active — applies to all Asymmetric productions
Last updated: 2026-05-06
Derived from: phase2r_pacing_dna.yaml, phase2r_asymmetric_style_targets.yaml, edit_grammar.md, visual_style_system.md

---

## Purpose

This document defines the reusable channel-wide system that forces every Asymmetric video to behave more like high-performing YouTube before production begins.

It is not a style guide. It is not a brand guide. It is a production machine — a sequence of hard gates, templates, and feedback loops that makes retention-class output the default, not the exception.

Every project in the Asymmetric pipeline must pass through this system. No exceptions for short-form, no exceptions for "test" renders.

---

## 1. What High-Performing YouTube Channels Systematize

The gap between channels that consistently perform and channels that occasionally perform is almost never talent. It is always system.

High-retention channels have systematized four things:

**The opening sequence.** Every episode's first 30 seconds is designed as a discrete unit — tested, scored, and approved before any other production work begins. The opening sequence is not the start of the script. It is a separate artifact that must pass its own gate.

**The packaging decision.** Title and thumbnail direction are locked before research starts, not after. The packaging decision defines what kind of proof the episode needs, what kind of conflict to find, what the viewer will expect. Packaging that changes after scripting is a sign that the concept was never correctly defined.

**The pacing DNA.** Every episode is calibrated against a reference pacing profile — a set of measurable targets derived from analyzing how competing high-retention videos actually move. WPM, visual events per window, first proof timing, pattern break frequency. These are measured against references, not invented per episode.

**The feedback loop.** Every render produces a retention postmortem that feeds back into the system. Static hold failures, pattern break failures, visual-narration decoupling — these are logged, not forgotten. The system learns from every render.

Channels that do not systematize these four things rely on getting lucky with each episode. They cannot reproduce success.

---

## 2. Why Clear Explanation Is Not Enough

The clearest explanation in the world will not retain a YouTube viewer past the 30-second mark if the visual state is not moving.

This is the central lesson of Phase 1. The narration was correct. The clips were the right clips. The structural logic was sound. The render still failed the creative review because:

- Static PNGs held for 3-4 seconds are not visual events. The viewer reads the diagram in 2 seconds and waits for the next cut.
- A bold text card displayed for 1.8 seconds without a kinetic entrance is a title slide, not a flash.
- Narration delivering a data point over a static image that does not correspond to that data point is decoupled — the viewer experiences audio and video as separate tracks instead of one synchronized argument.

The mechanism the viewer is trying to understand and the visual state they are looking at must arrive together. This is not a stylistic preference — it is how the medium works.

A private intelligence briefing that is read aloud over a static slide deck is not a briefing. It is a report. YouTube audiences know the difference immediately.

---

## 3. The Asymmetric Format Machine

The Asymmetric format machine is a sequence of gates that every episode passes through in order. No gate may be skipped. No gate may be passed by an agent without the artifacts to prove it.

```
STEP 0: Pacing DNA
         ↓ reference analysis complete before scripting
STEP 1: Packaging Test
         ↓ title/thumbnail/viewer promise approved before research
         → OPERATOR APPROVAL REQUIRED
STEP 2: Opening Sequence Proof
         ↓ 3-5 opening variants generated and scored
         ↓ at least one variant passes all opening gates
         → OPERATOR APPROVAL REQUIRED
STEP 3: Performance Package
         ↓ concept scored for hook strength, stakes, leverage clarity
         → OPERATOR APPROVAL REQUIRED
STEP 4: Research and Source Discovery
         ↓ primary sources, mechanism proof, clip candidates
STEP 5: Clip Quality Gate
         ↓ all candidates scored before acquisition
         → OPERATOR APPROVAL REQUIRED
STEP 6: Script and Beat Map
         ↓ uses retention_timeline.yaml
         ↓ narration WPM verified
         ↓ visual-narration coupling confirmed
STEP 7: Scene Event Plan
         ↓ every event scored for tension, novelty, pattern break
         ↓ static hold limits enforced
STEP 8: Pattern Break Plan
         ↓ break cadence verified before render readiness gate
STEP 9: Render Readiness Gate
         → OPERATOR APPROVAL REQUIRED
STEP 10: Render
STEP 11: Technical QC
STEP 12: Postmortem (standard + retention_postmortem.yaml)
STEP 13: Manual Creative Review
         → OPERATOR ONLY — creative_pass never set by agent
```

Steps 0–2 are new to Phase 2S. They run before the existing 14-step sequence begins. They do not replace it.

---

## 4. The 30-Second Opening Sequence System

The first 30 seconds of an Asymmetric video is produced as a standalone proof unit before any other scripting begins.

**Why this order matters:** Most scripting failures originate in the opening. A weak opening is almost never fixable by rewriting the middle. When the opening is designed last (as a result of scripting forward), the writer is trying to hook a story that is already defined — they cannot change the fundamental structure to serve the hook. When the opening is designed first, the entire script is written in service of the hook the writer already knows works.

### What the 30-second opening must accomplish

By second 30, the viewer must have experienced:
- Conflict or consequence already in progress (not being set up)
- At least one source-backed proof hit (clip, document, number, institution named)
- An open loop that is not yet answered
- At least two distinct visual modes
- At least one pattern break
- Concrete stakes (a person, a number, an institution — not an abstraction)

By second 30, the viewer must not have experienced:
- Topic introduction or context-building
- Any sentence that begins with a hedge or setup phrase
- A diagram that has not been earned with prior clip or proof pressure
- A static visual state lasting more than 4 seconds

### The opening sequence proof artifact

For every episode, the writer generates 3–5 opening variants using `opening_sequence_proof.yaml`. Each variant represents a materially different way to enter the story — different first visual, different first narration line, different proof type, different hook classification.

Variants are scored against the opening gate checklist. At least one must pass. Operator selects from passing variants. No production proceeds until this approval is explicit.

### Opening gate checklist (required for PASS)

- [ ] First frame creates curiosity, pressure, consequence, conflict, or visual novelty — not a title card
- [ ] No title-card-only opening
- [ ] No context dump in the first 10 seconds
- [ ] Viewer stakes appear by second 8
- [ ] Viewer question is created by second 10
- [ ] Viewer promise is clear before second 30
- [ ] Proof, conflict, source pressure, rule text, or human tension appears in the opening sequence
- [ ] Mechanism begins before second 30
- [ ] At least one pattern break occurs in the opening
- [ ] Visual state changes with information delivery (narration data point = visual state change)
- [ ] Opening does not feel like a corporate explainer
- [ ] Opening does not feel like a school presentation

### Reject an opening if any of these are true

- Starts with a clean title card
- Opens with generic context ("The App Store has been at the center of debate for years...")
- First narration line begins with "You think..." or "You might think..."
- Explains before creating tension
- Uses a diagram as the first visual before any clip or proof pressure
- Delays proof or conflict past second 15
- Could belong to a corporate training video
- Could belong to a school presentation or lecture recording

---

## 5. Packaging-Before-Production Rules

Packaging (title + thumbnail direction + viewer promise) is locked before research begins.

**The rule:** If you don't know what you're selling the viewer before you start researching, you cannot evaluate whether the research is finding the right evidence. Packaging defines the proof standard.

A title like "Who Really Controls the App Store?" tells the researcher to find evidence of hidden control. A title like "Apple's App Store Strategy Explained" tells the researcher to find confirmation. These are different research briefs. The packaging choice determines what counts as sufficient evidence.

### Packaging gate requirements

1. At least three title candidates tested against the title engine library
2. At least three thumbnail concepts (power / mechanism / consequence variants)
3. One viewer promise statement using the channel template: "By the end of this video you will understand [mechanism] well enough to recognize it in [adjacent system] — and know what [insight] it implies."
4. One curiosity gap statement: what does the viewer not know that they will know?
5. One emotional trigger: what feeling does the viewer have at t=0 that carries them forward?
6. One proof promise: what primary source evidence does the viewer expect to see?

### Packaging gate pass conditions

- Title creates curiosity gap without giving away the mechanism
- Thumbnail can be understood in under 2 seconds on mobile
- Viewer promise is specific enough to define what "success" means for the episode
- Title, thumbnail, and opening sequence are aligned — they promise the same thing

### Packaging gate blockers

- Title is too generic (does not name a hidden mechanism or chokepoint)
- Thumbnail requires more than 2 seconds to decode on mobile
- Viewer promise is so broad it could apply to any documentary on the topic
- Title/thumbnail/opening promise three different things

---

## 6. Reference Pacing DNA Workflow

Every Asymmetric project must complete reference analysis using `high_retention_reference_workflow.md` before the script is written.

This is not optional. It is not optional for "simpler" episodes. It is not optional when the operator believes the format is already understood.

The pacing DNA workflow produces project-specific QC targets that go into the render readiness gate. Without them, the render readiness gate is checking against generic channel targets that may not match the specific structural demands of the current episode's topic, format, or target runtime.

### What reference analysis produces

- **Pacing DNA table** — average shot duration, events per window, first proof timing, hook type, payoff type — for each reference, with an Asymmetric target row
- **Shot rhythm targets** — specific numeric targets for this project's scene event plan
- **Anti-pattern list** — visual modes or structural choices that appeared in references and dropped engagement
- **Render-specific QC gates** — added to this project's render readiness gate

### Minimum reference requirements

- At least 3 reference videos per project
- At least 1 topically adjacent (same genre of hidden-control or leverage content)
- At least 1 structurally aspirational (high retention, well-performing)
- At least 1 instructive failure or near-miss

Reference analysis outputs are stored in `shared_studio/projects/<id>/artifacts/` and linked in the render readiness gate.

---

## 7. Visual State / Narration Coupling Rule

**The rule:** Every time the narration delivers a data point — a number, a named entity, a rule claim, a percentage — a corresponding visual state change must occur within ±1 second of narration delivery.

This is the universal mechanic found in every high-retention reference analyzed in Phase 2R. WSJ, Wendover, MagnatesMedia — all three achieve it through different means, but all three achieve it.

The failure mode is: narration runs over pre-set static visuals on a fixed schedule regardless of what is being said. This produces audio and video as independent tracks. The viewer experiences them separately. The briefing feeling collapses into a presentation feeling.

### How to implement this in the scene event plan

When writing `scene_event_plan.yaml`, every event's `narration_under` field must be read alongside the event's `timestamp_seconds`. For every data-bearing statement in `narration_under`, a visual state change must appear in the event list within ±1 second of the timestamp where that statement is spoken.

If narration says "30%" at t=22 and the next visual event is at t=25, the coupling is broken. Move the event to t=22, or move the narration to t=25.

Coupling is mandatory for:
- Specific numbers (commission rates, percentages, dollar amounts, counts)
- Named institutions or actors first appearance
- Rule claims and policy assertions
- Chokepoint naming moments
- Payoff line delivery

Coupling is not required for:
- Connecting tissue narration
- Transition sentences
- Context-building phrases

### What this requires from the current pipeline

The coupling rule can be enforced in artifact planning (scene event plan) before any render. It does not require new Remotion components. It requires discipline in the beat map and scene event plan.

However: if the visual element that must appear at t=22 is a diagram node snapping in, and the current Remotion component only supports static PNG display, the coupling requirement cannot be fully met at the visual layer. The narration can be timed correctly, but the visual element will appear as a static image, not as an animated snap. This is a Phase 2B limitation acknowledged clearly: coupling in timing is achievable now; coupling in motion requires `PressureMapScene` and related animated components.

---

## 8. Proof Timing Rule

Proof is not ornament. It is the reason the argument is credible.

**The rule:** Every Asymmetric episode must land its first proof hit by second 10. Minimum 3 proof hits in a 60–90 second render. The final proof hit sets up the payoff.

### Proof hit ranking (strongest to weakest)

1. Institutional conflict clip — senator, regulator, judge naming the violation under oath
2. Rule text zoom — policy document with the key phrase visible and scaled
3. Number flash — commission rate, market share, fee — IBM Plex Mono, amber, full frame
4. Document punch-in — official document screenshot, amber border, source label
5. Named entity proof — case number, filing date, company name — specific, not generic

Narration alone is never a proof hit. A diagram that illustrates a claim is not a proof hit. B-roll labeled with a source name is not a proof hit.

### Proof timing in the scene event plan

The `scene_event_plan.yaml` sequence analysis section must show:
- `first_proof_hit_timestamp` ≤ 10 seconds
- At least 3 events with `retention_purpose: proof_hit`
- Final proof hit event is followed by the payoff section

### What happens without timely proof

Without a proof hit by second 10, the opening is narration-only. The viewer has been told something by a voice. They have no reason to trust the voice. They have no reason to stay.

With a proof hit by second 5–8 (as achieved by WSJ and Wendover), the viewer has evidence before they consciously decide to trust the narrator. The trust is established by the institution or document, not by the voice.

---

## 9. Pattern Break Cadence

**The rule:** Minimum one pattern break every 12 seconds. No visual mode repeats three times in a row. Every diagram section longer than 6 seconds is interrupted.

Pattern breaks prevent the viewer from habituating. The viewer who has habituated to the rhythm can predict what is coming next. A viewer who can predict what is coming next has no reason to stay. The surprise is the retention mechanism.

### Break types (strongest to weakest)

1. Hard conflict clip cut — from diagram to testimony, hard cut, no warning
2. Hard text flash — amber signal, 2–5 words, 1.5–2.5 seconds, kinetic entrance
3. Rule text zoom — crop-and-scale into primary source document
4. Split screen — simultaneous contrast (before/after, surface/mechanism)
5. Number slam — large IBM Plex Mono number, amber, short hold
6. Map compression — diagram elements compressing toward chokepoint
7. Source label burn-in — label appearing on first frame of clip

### Pattern break planning

The `pattern_break_plan.yaml` must be complete and approved before the render readiness gate. It is a planning artifact, not a QC artifact. The break cadence is designed before production, not audited after render.

The compliance section of `pattern_break_plan.yaml` must show `plan_approved: true` with `longest_gap_between_breaks_seconds ≤ 12` before the format gate passes.

---

## 10. Scene-Event Density Requirements

**Minimum targets (all Asymmetric episodes):**
- 17 meaningful visual events per 75 seconds (up from the Phase 1 minimum of 12)
- 7 events in the first 30 seconds
- Maximum 4 seconds between events in diagram sections
- Maximum 8 seconds between events in clip sections
- Maximum 3 seconds for any text card hold

**How to achieve this without animated diagram components:**

The Phase 2B Remotion components (`PressureMapScene`, `HardTextFlashScene`, etc.) are not yet built. Without them, every diagram section is a static PNG. Static PNGs cannot generate multiple visual events — one PNG = one event regardless of how long it holds.

Until Phase 2B components are available, the only way to achieve the event density target is:
- Use more clips (each clip cut = one event)
- Use more hard text flashes between clips (each flash = one event)
- Use document punch-ins between diagram sections (each punch-in = one event)
- Shorten diagram PNG holds to ≤4 seconds and cut to clip or flash
- Accept that diagram sections will be shorter than target until animated components are ready

**The honest constraint:** A 75-second video with 3 clips (3 events), 3 hard text flashes (3 events), 3 diagram PNGs held 4 seconds each (3 events), 1 document punch-in (1 event), and 1 payoff frame (1 event) produces 12 events. To reach 17, either more mode-switching is needed or animated diagram components are needed.

Do not design a scene event plan that requires 17 events and only builds it by holding static PNGs for extended periods. The event density target must be met with real mode changes.

---

## 11. Clip Pressure Requirements

Source clips in Asymmetric are not evidence inserts. They are not footnotes. They are pressure events that interrupt the diagram narrative.

**The clip pressure rule:** Every clip must interrupt a diagram section that has made a mechanism claim the clip then makes undeniable. The clip does not arrive at its scheduled position. It cuts in when the diagram has raised the right question.

### Clip pressure checklist

For every source clip in the scene event plan:

- [ ] The clip cuts in to a diagram section mid-build (not after it completes)
- [ ] The viewer_question_answered field names a specific question the prior diagram event planted
- [ ] The clip has cut_value ≥ 4 (passes source clip quality gate)
- [ ] The clip is from an official source (government hearing, regulator, court record)
- [ ] The clip duration in the edit is 6–10 seconds (not longer)
- [ ] The clip exits hard to either a text flash or an updated diagram state
- [ ] The clip cannot be removed without changing the emotional trajectory of the render

### Minimum clip requirement

A 60–90 second Asymmetric episode must contain at least 2 primary source clips (institutional testimony, regulatory enforcement, or equivalent authority). A single clip with narration and diagrams is not a source-commentary production — it is a narration-with-illustration production.

---

## 12. Component Library Requirements

**This section is honest about what the current pipeline cannot do.**

The Asymmetric visual style system requires the following visual behaviors:
- Diagram nodes appearing one by one (map reveal sequence)
- Arrows extending from source to destination (route snap)
- Gates compressing toward chokepoint (gate compression)
- Hard text entering with kinetic translational motion (slide-lock entrance)
- Rule text zooming into a specific phrase in a document (crop-and-scale)
- Clips playing with Asymmetric color grade applied in composition (not FFmpeg post-patch)

**Current Remotion components available:** TextCard, StatCard, SectionTitle, HeroTitle, ComparisonCard, CinematicRenderer, TitledVideo.

**None of the above behavioral requirements are met by current components.**

Without the Phase 2B components, every diagram section in the render is a static PNG. Every hard text flash is a static PNG. Every clip is ungraded or requires a post-render FFmpeg patch. The visual-narration coupling rule can be honored in timing but not in the animated behavior that makes simultaneous delivery feel different from scheduled delivery.

**Phase 2B components required before full episode renders:**
- `HardTextFlashScene` — kinetic text entrance, amber highlight, 1.5–2.5s hold
- `PressureMapScene` — node/arrow/gate build sequence, element-by-element reveal
- `TrapClosureScene` — gate compression toward chokepoint
- `RuleZoomScene` — document crop-and-scale zoom to key phrase
- `PayoffLockScene` — final diagram at most compressed state, payoff line overlay
- `AsymmetricClipScene` — clip with grade applied and source label burn-in
- `RouteMapScene` — route path drawing itself from source to destination

**The test for Phase 2B readiness:** A 20-second test render showing `PressureMapScene` building a 3-node map element by element, interrupted by `HardTextFlashScene`, with a clip entering and exiting hard. When this test render looks like the reference pacing DNA targets, Phase 2B is ready.

**Do not attempt a full episode render before Phase 2B components pass this test.** The gap between what static PNGs produce and what the reference DNA requires is too large to be compensated by better scripting alone.

---

## 13. Analytics and Postmortem Feedback Loop

Every render produces two postmortems:
1. The standard postmortem (`postmortem.md` template) — technical QC, clip performance, system changes
2. The retention postmortem (`retention_postmortem.yaml`) — frame-level retention analysis against the targets in this document

The retention postmortem is the feedback loop that updates the pacing DNA and style targets for the next project.

### What the retention postmortem captures

- First frame result — did it create the required sensation?
- Opening sequence result — did the first 30 seconds achieve all opening gates?
- Visual event cadence — actual events vs. target per window
- Static hold failures — any visual state held longer than the target for its mode
- Pattern break failures — any gap between breaks exceeding 12 seconds
- Visual-narration coupling failures — any data-bearing narration statement without a simultaneous visual event
- Proof timing — when was the first proof hit vs. the 10-second target?
- What to change in the system — specific recommendations for the next project's scene event plan, pattern break plan, and opening sequence

### How postmortem findings update the system

If the retention postmortem identifies a systematic failure (e.g., all diagram sections exceed the static hold limit), the root cause must be identified before the next project begins:
- Is it a planning failure (scene event plan did not enforce the limit)?
- Is it a component failure (no animated component available)?
- Is it a structural failure (diagram sections are too long for the current component set)?

The answer determines whether the fix is an artifact change, a Remotion component build, or a structural constraint on how diagrams are used until components are available.

---

## 14. How This System Connects to the Existing OpenMontage Source-Commentary Pipeline

This format system runs before the existing 14-step source-commentary production sequence. It does not replace any existing gate. It adds three upstream gates:

| New gate | Position in sequence | Artifact produced |
|----------|---------------------|-------------------|
| Pacing DNA | Before Step 1 (git preflight) | `phase2r_pacing_dna.yaml` (per project) |
| Packaging test | Before Step 2 (performance package) | `packaging_test.yaml` (project instance) |
| Opening sequence proof | Before Step 3 (operator approval) | `opening_sequence_proof.yaml` (project instance) |

The format gate command (`/om-asymmetric-format-gate`) checks all three new gates plus the existing gates 2–9 in a single status report.

The retention postmortem connects to the existing postmortem step (Step 13) as an additional artifact. The standard postmortem captures system lessons; the retention postmortem captures frame-level performance data.

The format system does not change the evidence lock in `skills/pipelines/source-commentary/CONTRACT.md`. It does not add new pipeline stages to `pipeline_defs/source-commentary.yaml`. It adds pre-production gates and post-production feedback. The pipeline itself is unchanged.

---

## Global Gates Summary

These gates are hard. None may be waived by an agent. None may be waived by time pressure.

| Gate | Block condition |
|------|----------------|
| No full video production until opening sequence proof passes | Operator has not approved at least one passing opening variant |
| No script until viewer promise and title/thumbnail direction are approved | Packaging test has not been operator-approved |
| No render until scene event plan proves visual-narration coupling | Coupling field in scene event plan not confirmed |
| No diagram section may appear complete at first frame | Any diagram event has no build sequence or is a full-state static PNG in a Phase 2B render |
| No proof sequence may delay first proof hit past second 10 | `first_proof_hit_timestamp > 10` in scene event plan |
| No full episode until a 60–90 second proof render passes manual creative review | No approved proof render exists in the project artifacts |
| No `creative_pass` may be set by an agent | Only the operator sets `creative_pass: true` after watching the full render |
