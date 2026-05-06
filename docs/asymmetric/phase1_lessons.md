# Asymmetric Phase 1 Lessons

Version: 1.0
Project: `app-store-leverage-p001`
Last updated: 2026-05-06

---

## What Phase 1 Proved and What It Didn't

### Phase 1A: Static Render Spine

**Proved:**
- The OpenMontage source-commentary pipeline can produce a render with narration, proof cards, and diagram cards
- Audio continuity, source-label placement, and blank-screen elimination are achievable
- The pipeline's checkpoint and receipt system works correctly

**Did not prove:**
- Creative effectiveness — only tested static cards and diagram cards
- Visual rhythm at the 3-5 second target — cards held ~7.5 seconds
- Clip integration — no real source clips were used

**What failed creatively:**
- Cards-only render for a milestone that conceptually requires source clip pressure
- Visual change rate too slow relative to reference video rhythm (WSJ, Wendover, Magnates)
- Viewer stakes were not established early enough
- Output felt like a clean presentation with source citations

---

### Phase 1A.2: Improved Static Render

**Proved:**
- Opening with tension instead of institutional setup improves hook quality
- Audio loudness can be improved from -28.0 dB to -20.5 dB without pipeline changes
- Second-half silence and blank-frame issues are fixable
- Visual states can be increased from 3 to 8 while keeping source labels in safe zones

**Did not prove:**
- Creative effectiveness — still only tested static cards, no real clips
- Visual rhythm at the 3-5 second target — still at ~7.5 seconds per card
- Whether the output holds viewer attention in real watch conditions

**Key finding:**
Phase 1A.2 is technically sound but still a static proof-of-concept. Static cards are support assets, not the editorial product. The next production phase must integrate real source clips.

---

### Phase 1B: Real Clip Integration

**Proved:**
- Real source clips can enter the source-commentary pipeline
- The clip receipt, acquisition, media QC, and edit plan workflow functions
- Clips can be composed with narration and source labels without pipeline changes

**What failed editorially:**
- Clip selection was not evaluated for editorial force before acquisition
- App Store curation clip: calm keynote footage, showed the comfortable surface without pressure
- StoreKit clip: developer education/tutorial, explained purchase plumbing, did not create constraint
- Senate hearing clip: correct category, wrong timestamp range — no sharp confrontation in the selected window
- The resulting video felt like a presentation with source inserts, not a conflict-led YouTube cut

**Root cause:**
The clip quality gate did not exist before Phase 1B. Clips were evaluated for technical eligibility (duration, transcript, metadata) but not for editorial force (clip energy, cut value, visual texture under pressure).

---

### Phase 1B.2: Source Clip Quality Gate

**Proved:**
- A scored clip quality evaluation can be run before acquisition
- The five-score gate (clip energy, claim relevance, visual texture, authority, cut value) correctly identifies high-force candidates
- 6 candidates pass the gate from the App Store leverage topic
- The top 3 (Klobuchar anti-steering testimony, Klobuchar monopoly grilling, House hearing Cook defense) create the conflict and constraint that Phase 1B clips lacked

**Did not prove:**
- Whether the upgraded clips will hold attention when edited together
- Whether the visual rhythm plan will achieve the 3-5 second target with real clip cuts
- Creative effectiveness — still awaiting operator clip approval and render

**Key finding:**
Clip quality evaluation must happen BEFORE acquisition, not after. The quality gate is now a first-class production gate.

---

## Core Lessons for All Future Asymmetric Productions

### 1. Performance package before everything else

Before research, before clip hunting, before scripting: run the performance package. Evaluate hook strength, viewer stakes, visual energy, and boredom risk at the concept level. Kill boring-but-technically-correct concepts early. A concept that does not pass the performance package will not be saved by good clips or good narration.

### 2. Static cards are support assets, not the product

Source-commentary productions require real source clips to create pressure. Static cards (text, proof, diagram) support the narrative structure. They do not carry the editorial weight alone. Any milestone that requires clips must not ship as a cards-only render.

### 3. No cards-only render for clip-required milestones

If the milestone plan calls for source clips, the render must contain source clips. A technically valid cards-only render is not a substitute. It should not be submitted for operator review as if it were the target deliverable.

### 4. Real source clips must create pressure

A clip that merely confirms the narration is a waste of cut time. The clip must create pressure before the narration explains the mechanism. The viewer should feel the constraint or conflict in the clip before they fully understand it.

### 5. Clip quality gate before acquisition, not after

Score every candidate before acquisition:
- Clip energy: does this clip have force, movement, and visible tension?
- Claim relevance: does this clip directly support the specific claim it is paired with?
- Visual texture: does this clip have readable, interesting, pressure-signaling visuals?
- Authority: does this clip carry the credibility the claim requires?
- Cut value: can this clip be trimmed to 8-14 seconds of high-force material?

Minimum scores: all five dimensions must reach 4/5 for the clip to be a primary source. A 3/5 is acceptable only for texture support, never for a primary claim moment.

### 6. Visual rhythm is a production gate

The visual rhythm plan must be written before composing. If the plan cannot achieve a meaningful visual change every 3-5 seconds in diagram sections and every 5-8 seconds in narrative sections, the plan is not ready.

Targets:
- Diagram sections: 1 meaningful change every 3-5 seconds
- Narrative/clip sections: 1 meaningful change every 4-8 seconds
- No diagram state holds for more than 5 seconds
- Minimum 12 meaningful visual events per 75 seconds

### 7. Technical QC and creative review are separate

Technical QC can be automated: silencedetect, blackdetect, duration check, source label check. These catch pipeline failures.

Creative review cannot be automated. The operator must watch the full render. `creative_pass: true` is never set by an agent or tool.

### 8. Source labels in the safe zone

Source labels must be placed in the designated safe zone (bottom strip, no higher than the lower 20% of frame). Labels must never overlap body text, diagram labels, proof text, or key visual elements. This is a hard rule, not a style preference. Phase 1A.2 proved this is achievable. It must not regress.

### 9. Performance review must happen before production starts

The Phase 1 sequence discovered editorial weaknesses mid-production (after rendering). The next system must run performance evaluation — hook strength, viewer stakes, boredom stress test — before research begins and certainly before any asset is created.

### 10. The operator is the final gate — always

No agent, tool, or QC process grants creative pass. The operator watches and decides. This is not bureaucracy — it is the editorial integrity mechanism that keeps Asymmetric from shipping technically valid but editorially weak content.

---

## Status at End of Phase 1

| Gate | Status |
|------|--------|
| Static render spine | Proved (Phase 1A) |
| Audio continuity | Proved (Phase 1A.2) |
| Source label safe zone | Proved (Phase 1A.2) |
| Real clip integration | Proved (Phase 1B) |
| Clip quality gate | Defined (Phase 1B.2), not yet render-tested |
| Upgraded clip slate | Identified (6 candidates), not yet acquired |
| Visual rhythm at 3-5s target | Not yet proved with real clips |
| Creative pass for App Store video | Not yet — awaiting operator approval and clip upgrade render |

---

## What the Next Production System Must Do Differently

1. Run performance package before research begins
2. Run clip quality gate before acquisition begins
3. Write visual rhythm plan before composing
4. Require operator approval at each of the three gates above
5. Never submit a cards-only render for a clip-required milestone
6. Score clip energy, claim relevance, visual texture, authority, and cut value before approving any clip
7. Enforce source label safe zone as a hard rule, not a review suggestion
8. Run technical QC immediately after render — before operator review
9. Run postmortem on every render to capture lessons for the next episode
10. Separate technical pass from creative pass at every stage
