# Asymmetric High-Retention Reference Workflow

Version: 2.0
Status: Phase 2 — active
Last updated: 2026-05-06

---

## Purpose

This workflow defines how to analyze high-performing YouTube videos to extract pacing DNA, visual rhythm targets, and style constraints for Asymmetric productions.

The current reference analysis (stored in `reference_video_analysis_profile.md`) was sufficient to identify structural patterns but did not produce actionable shot-rhythm targets, anti-pattern inventories, or render-specific quality gates. This workflow produces all of those.

**Every Asymmetric project must complete this workflow before the script is written.**

The output of this workflow directly informs:
- Narration word-per-minute target
- Visual event frequency target
- Scene event plan structure
- Pattern break plan
- QC metrics for the retention gate

---

## Minimum Requirements Per Project

- Analyze at least 3 reference videos per project
- At least one reference must be topically adjacent (same genre of hidden-control or leverage content)
- At least one reference must be structurally aspirational (a video that performs well on retention metrics)
- At least one reference must have failed in some way that is instructive (a video the operator identifies as "close but wrong")

Analysis must be completed at the shot level for the first 30 seconds and at the section level for the remainder.

---

## Part 1: First 30 Seconds — Shot-by-Shot Extraction

For every reference, produce a shot-by-shot table for the first 30 seconds.

### Required fields per shot:

| Field | Description |
|-------|-------------|
| `shot_id` | Sequential number |
| `start_sec` | Start time in seconds |
| `end_sec` | End time in seconds |
| `duration_sec` | Duration |
| `visual_mode` | One of: source_clip, diagram, text_card, proof_document, hard_text_flash, talking_head, b_roll, title_card |
| `content_description` | One sentence. What is actually visible. Not what it "represents." |
| `narration_density` | Words spoken over this shot |
| `proof_present` | true/false — does this shot contain a primary source, institution named, or evidence moment? |
| `tension_level` | 1–5. 1=neutral, 5=peak conflict |
| `open_loop_present` | true/false — does this shot plant a question the viewer wants answered? |
| `viewer_question_created` | What question does the viewer have after this shot? |

### Shot-by-shot analysis produces:
- Average shot duration in first 30 seconds
- Visual mode sequence in first 30 seconds
- First proof moment timestamp
- First open loop timestamp
- Tension curve shape in first 30 seconds

---

## Part 2: Visual Event Frequency

For the full video, measure visual event frequency at 30-second intervals.

### Method:
- Sample frames every 2 seconds
- Count the number of frames where a meaningful visual change has occurred vs. the preceding sample
- A meaningful visual change is any of: new shot, new diagram element, new text, new animation state, new overlay

### Produce:
- Events per 30-second window (baseline, minimum, maximum)
- Sections with the lowest event frequency (where did the video slow down?)
- Sections with the highest event frequency (where did the video accelerate?)

### Target derivation:
The reference video's median event frequency per 30-second window becomes the minimum target for the Asymmetric production. The reference's peak window becomes the aspirational target for the highest-tension section.

---

## Part 3: Transition Types

For every transition in the first 90 seconds, record:

| Transition | From visual mode | To visual mode | Duration (frames) | Effect |
|------------|-----------------|---------------|-------------------|--------|
| Cut | source_clip | hard_text_flash | 0 | Immediate |
| Cut | diagram | source_clip | 0 | Immediate |
| Dissolve | b_roll | b_roll | 12 | Slow |

### Produce:
- Most common transition type used
- Whether hard cuts dominate or softer transitions dominate
- What transition types appear before the highest-tension moments
- What transition type is used into the payoff

---

## Part 4: Hook Pattern Classification

Classify the reference video's hook into one of:

| Hook type | Description | Example |
|-----------|-------------|---------|
| Contradiction | States what appears true, then flips it | "Apple is winning. Except it isn't." |
| Consequence first | Opens with the outcome before showing the cause | "This single regulation cost developers $600M." |
| Question gap | Names something the viewer doesn't know that they should | "There is a company you've never heard of that owns most of what you use." |
| Stakes announcement | Names the scale before showing the mechanism | "One decision affected 1.8 billion devices." |
| Conflict in progress | Drops into a fight already happening | Clip of testimony begins, narration arrives underneath |
| False choice reveal | Shows a choice that turns out not to be a choice | "You can pay Apple. Or you can not exist on iOS." |

For Asymmetric, **Contradiction**, **Consequence first**, and **Conflict in progress** are the preferred hook types.

**Produce:**
- Reference's hook type
- First 6 words of the hook narration or visual action
- Whether the hook would hold a scrolling viewer at t=0 (honest judgment)
- What the Asymmetric production's hook type should be given this reference

---

## Part 5: Proof Density

Record the timestamp and form of every proof moment in the reference.

A proof moment is: named institution, cited statistic, document screenshot, source clip, court filing, regulator statement.

### Produce:
- Total proof events in the full video
- Proof events per minute (reference density)
- First proof event timestamp
- Longest gap between proof events
- Whether proof was front-loaded (first 30 seconds) or back-loaded (second half)

**For Asymmetric:** If the reference front-loads proof (first proof hit before t=12), adopt that as the target. If proof is back-loaded, note this as a structural pattern to override.

---

## Part 6: Pattern Break Inventory

Identify every moment in the first 90 seconds where the visual or audio pattern broke unexpectedly.

### Record:
- Timestamp
- Type of break (hard cut to testimony, text flash, number slam, map compression, split screen)
- Prior visual mode (what was broken)
- Duration of the break

### Produce:
- Breaks per 30-second window
- Most common break type
- Whether breaks correlated with narration emphasis or ran independently
- The longest unbroken visual mode sequence before a break

**For Asymmetric:** The reference's break frequency per 30-second window becomes the minimum target. If the reference achieves retention with fewer breaks than the Asymmetric minimum, note why (e.g., physical presence of a host anchors the viewer differently than faceless narration).

---

## Part 7: Narration Density and Style

For the first 90 seconds:
- Total words spoken
- Words per minute
- Average sentence length (words)
- Percentage of sentences that are 8 words or fewer
- Tone classification: journalistic, analytical, dramatic, explanatory, documentary

### Produce:
- WPM target for Asymmetric production
- Target short-sentence ratio (ideally ≥40% of sentences ≤8 words)
- Whether narration punches in under clips or breathes over neutral b-roll

---

## Part 8: Diagram Appearance — When and How

Record the timestamp of every diagram or graphic element in the reference.

For each:
- What preceded the diagram (clip, narration-only, text card)
- What was the diagram's first state vs. its evolved state
- Did the diagram animate, or was it static?
- How long did each diagram state hold?
- What ended the diagram section (clip cut, text flash, new diagram)?

### Produce:
- First diagram timestamp
- Whether diagrams were earned by prior clip/proof moments or appeared cold
- Whether diagrams animated internally or were static
- Average diagram section duration
- Whether diagrams improved retention (followed by continued engagement) or dropped it (followed by flat or exiting behavior)

---

## Part 9: Stakes Emergence Timeline

Record the first moment the reference made the viewer care.

Identify:
- First moment a concrete person, institution, or number was named (not described)
- First moment the viewer could feel the cost of the mechanism to someone
- Whether stakes were stated explicitly or implied by the footage

### Produce:
- Stakes emergence timestamp
- Form of stakes (person named, dollar figure, institutional consequence)
- Whether stakes preceded or followed the hook

**For Asymmetric:** Stakes must emerge before t=15. If the reference achieved it earlier, adopt that as the target.

---

## Part 10: Payoff Structure

Analyze the final 60 seconds of the reference.

Classify the payoff:
- Summary payoff: "So as we've seen, this is how the system works."
- Mental model payoff: "The key insight is X — wherever you see Y, expect Z."
- Operator payoff: "This means if you're doing A, you should change B."
- Revelation payoff: "The company you thought controlled this does not. This other entity does."

**For Asymmetric:** Mental model payoff is the target. Revelation payoff is acceptable. Summary payoff is a failure.

Record:
- Payoff timestamp
- Payoff type
- Whether the final frame was a diagram, clip, or text card
- Whether the viewer was left with a reusable structural insight

---

## Part 11: Synthesized Outputs

After completing Parts 1–10 for all reference videos, produce the following outputs. These become inputs to the project's scene event plan and pattern break plan.

### 11A: Pacing DNA Table

| Reference | Avg shot duration (first 30s) | Events/30s | First proof hit | First stakes | Hook type | Payoff type |
|-----------|-------------------------------|------------|-----------------|--------------|-----------|-------------|
| [Ref 1]   |                               |            |                 |              |           |             |
| [Ref 2]   |                               |            |                 |              |           |             |
| [Ref 3]   |                               |            |                 |              |           |             |
| **Asymmetric target** |                   |            |                 |              |           |             |

### 11B: Shot Rhythm Targets

Based on the pacing DNA table:
- Target average shot duration (first 30 seconds): `X seconds`
- Target events per 30-second window (minimum): `N`
- Target events per 30-second window (peak): `N`
- Maximum allowed unbroken visual mode: `X seconds`

### 11C: Style Constraints

Derived from reference analysis:
- Required: [list of structural elements that all successful references used]
- Preferred: [list of patterns that appeared in 2 of 3 references]
- Prohibited: [list of patterns that appeared in failed or lower-retention references]

### 11D: Anti-Pattern List

Every pattern that appeared in a reference and damaged retention:
- [Pattern] — appeared in [Ref] at [timestamp] — dropped engagement because [reason]
- [Pattern] — ...

### 11E: Render-Specific Quality Gates

Based on reference analysis, these thresholds become project-specific QC gates:

| Gate | Threshold | Source |
|------|-----------|--------|
| First proof hit | By second [N] | [Ref 1/2/3 average] |
| First stakes moment | By second [N] | |
| Events per 30-second window | Minimum [N] | |
| Maximum unbroken visual mode | [N] seconds | |
| Payoff type | mental_model / revelation | |
| WPM target | [N] | |

These gates are added to the render readiness checklist for this project. They are in addition to the standard Asymmetric grammar gates.

---

## Where Reference Analysis Outputs Go

| Output | Stored in |
|--------|-----------|
| Full analysis per reference | `shared_studio/projects/<id>/artifacts/reference_video_analysis_profile.md` |
| Pacing DNA table | Same file, appended as Phase 2 synthesis section |
| Shot rhythm targets | `templates/asymmetric/retention_timeline.yaml` (project instance) |
| Render-specific QC gates | `shared_studio/projects/<id>/artifacts/render_readiness_gate.md` (Phase 2 section) |

---

## Notes on Tool Limitations

When full video download is blocked by duration guards:
- Use the first 90 seconds only for hook, shot rhythm, and visual event analysis
- Use the transcript for narration density, proof density, and payoff structure
- Note the limitation in the analysis file
- Do not estimate data that was not observed — mark fields as `[blocked — transcript only]`

Frame-difference analysis from uniform samples is an estimate, not a precise measurement. Mark it as an estimate in the output. Err on the side of reporting a wider range rather than false precision.
