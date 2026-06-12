# High-Retention Evidence Cinema Pivot

Date: 2026-06-11
Channel: Modern Archivist / Failure Ledger
Status: Draft for implementation

## Problem

The latest Humane AI Pin render proved the deterministic Remotion path works, but it failed the audience test. It is a narrated sequence of text/data cards. That is not competitive with 2026 YouTube documentary channels. It reads like a research deck, not a high-retention documentary.

The previous WAN 2.2 trailer failed in the opposite direction: it looked like generic AI footage and damaged trust. The target is neither AI-cinematic slop nor static text cards.

## Target outcome

Build a repeatable 90-120 second pilot segment that feels like a top YouTube documentary cold open / first act:

- real source footage or screen-recorded artifacts in the first 3 seconds
- fast visual changes every 2-5 seconds
- tension loop: claim -> contradiction -> receipt -> escalation -> payoff
- cinematic motion built from real artifacts, not generated hero video
- source clips, product footage, review clips, webpages, screenshots, UI captures, documents, and diagrams
- deterministic Remotion final assembly
- every clip logged with provenance and fair-use rationale

## Non-goals

- No WAN / image-to-video hero footage.
- No static deck-style sequence as final surface.
- No generic explainer cards as the main video.
- No paid stock/API dependency for the pilot.
- No live network fetches during Remotion render.

## Audience standard

The target viewer in 2026 expects documentary pacing closer to Coffeezilla / MagnatesMedia / Johnny Harris / James Jani-style YouTube editing:

- a strong curiosity gap immediately
- visual novelty before attention decays
- receipts shown as drama, not as slides
- motion, zooms, masks, overlays, sound design, and rhythmic cuts
- chapter-like act turns and pattern interrupts
- source material that proves the story is real

## Creative principle

Evidence is the hero, but it must move like cinema.

A good frame should be one of these:

1. Real artifact: source clip, product footage, launch demo, review moment, webpage, screenshot, filing, tweet/post, support notice.
2. Cinematic reconstruction: camera flying through a timeline, money/returns graph, dependency map, cloud-server shutdown map, UI recreation.
3. Kinetic emphasis: one sentence or number timed to narration and sound design.
4. Pattern interrupt: brief red/critical visual rupture at the moment the story breaks.

A bad frame is:

- a centered paragraph
- a generic text card
- a chart with no emotional or narrative reason
- any synthetic shot pretending to be real footage

## Humane AI Pin pilot visual spine

Working title: `Humane AI Pin: The $699 Paperweight`

Runtime: 90-120 seconds.

Beat structure:

1. 0:00-0:03 — Cold open
   - Visual: hard cut between AI Pin product/demo clip, shutdown notice text, device silhouette, and a red countdown stamp.
   - Narration: “This was sold as the end of the smartphone. Ten days later, owners were told it would become a paperweight.”

2. 0:03-0:08 — Thumbnail promise fulfilled
   - Visual: product price, $24/month subscription, “service ends” countdown stacked in frame.
   - Purpose: viewer instantly understands the contradiction.

3. 0:08-0:18 — Launch myth
   - Visual: launch/demo clips or screen captures; animated labels call out “screenless”, “AI OS”, “Laser Ink Display”, “cloud-dependent”.
   - Motion: push-ins, parallax, masked zooms, freeze-frame annotation.

4. 0:18-0:32 — Review collision
   - Visual: short fair-use review clips or screenshots from major reviews; waveform/quote slams; fast cuts every 2-3 seconds.
   - Purpose: social proof and credibility.

5. 0:32-0:47 — Returns signal
   - Visual: The Verge article screenshot/recreation; numbers animate as receipts, not a static bar chart.
   - Motion: article scroll, highlight, number extraction, red return arrow.

6. 0:47-1:08 — Failure mechanism
   - Visual: phone already in pocket vs AI Pin dependency stack: hardware -> T-Mobile -> cloud -> AI query -> server cutoff.
   - Motion: dependency graph builds and then collapses.

7. 1:08-1:30 — Shutdown receipt
   - Visual: TechCrunch/official shutdown notice recreation, HP acquisition amount, Feb. 28 cutoff countdown.
   - Motion: hard red critical-error pattern interrupt.

8. 1:30-2:00 — Thesis payoff
   - Visual: three lessons as kinetic receipts: trust, utility, dependency.
   - Narration: “Credibility is a product feature. If your demo looks like magic, your receipt better look like infrastructure.”

## Required new artifacts

- `asset_log.tsv`: every clip/screenshot/source with URL, timestamp, source owner, duration, rights status, and fair-use justification.
- `visual_cues.json`: timed edit plan with clip IDs, motion type, overlay text, SFX cue, and evidence ref.
- `retention_timeline.json`: beat-level retention promises, open loops, pattern interrupts, and visual novelty score.
- `thumbnail_manifest.json`: 3-5 thumbnail/title packages before final render.
- `render_qc.md`: manual review of pacing, boring-card ratio, AI-slop risk, and proof density.

## Acceptance criteria

A test render is acceptable only if:

- First 5 seconds contain real/source-derived visuals, not just text.
- At least 70% of runtime uses source footage, screenshots, screen recordings, or artifact-derived motion.
- No static text card remains onscreen longer than 4 seconds unless combined with motion, source footage, or active annotation.
- Visual change cadence averages <= 5 seconds.
- Every factual visual has provenance.
- ffprobe confirms valid video+audio streams.
- Manual QC says it feels like a YouTube documentary segment, not a deck.

## Open implementation questions

- Whether to use short YouTube fair-use clips from public reviews for the pilot, or only screenshots/screen recordings to reduce rights risk.
- Whether Fish Speech can be restored for a final-quality voice pass before the next render.
- Whether HyperFrames should generate some source-rich motion sequences, with Remotion remaining final assembly.
