# Modern Archivist Playbook + Pipeline Audit

Date: 2026-06-11
Repo: `/home/pop/repos/openmontage-asymmetric`
Scope: `styles/modern-archivist.yaml`, `channels/modern-archivist/pipeline.yaml`, `channels/modern-archivist/skills/script-director.md`, `channels/modern-archivist/skills/thumbnail-director.md`, channel doctrine docs

## Executive summary

Verdict: the new Modern Archivist package is directionally strong and much closer to a high-performing 2026 documentary channel than the earlier generic explainer shape.

What is already good:
- strong niche fit: “corporate true crime” with clear evidence-first positioning
- distinct visual identity: near-black + slate + signal teal + scarce red
- retention-aware scripting rules: 20s cold open, 60–90s tension beats, evidence-first scenes
- channel/package separation is correct: playbook + pipeline + director skills + schemas
- thumbnail system now exists and is much better than leaving thumbnail logic implicit

What is still missing if the goal is top-tier 2026 performance:
- no explicit publish system in the pipeline: title/description/chapters/end screen/Shorts teaser/test-and-compare loop
- no post-publish retention feedback loop back into the playbook
- script/playbook contracts are still a little too qualitative where top performance needs measurable constraints
- some visual accessibility/mobile-shelf rules are underspecified
- pipeline stops at render even though 2026 YouTube performance depends heavily on packaging + feedback iteration

Bottom line:
The creative doctrine is now strong enough to make a compelling pilot. The growth system is not yet strong enough to reliably compound learnings across episodes.

## Grounding: what I inspected

Local files:
- `styles/modern-archivist.yaml`
- `channels/modern-archivist/pipeline.yaml`
- `channels/modern-archivist/skills/script-director.md`
- `channels/modern-archivist/skills/thumbnail-director.md`
- `channels/modern-archivist/design/retention-doctrine.md`
- `channels/modern-archivist/design/channel-source-of-truth.md`
- `channels/modern-archivist/schemas/episode.schema.json`

External references used for 2025–2026 YouTube behavior:
- YouTube Help: `Measure key moments for audience retention`
- YouTube Help: `Thumbnail & title tips`
- YouTube CEO 2025 letter: TV is primary device in US by watch time; 1B+ hours/day on TVs
- YouTube CEO 2026 letter: multi-format platform, anti-AI-slop posture, AI disclosures, continued creator-as-studio shift
- Retention Rabbit 2025 benchmark report: useful third-party directional benchmark, but not an official YouTube source

## 2026 audience and platform implications

Facts from sources:
- YouTube explicitly advises creators to inspect the first 30 seconds and change intros, title, or thumbnail when retention underperforms.
- YouTube says titles and thumbnails are the primary discovery/decision surface and notes that 90% of best-performing videos have custom thumbnails.
- YouTube says TV is now the primary device for viewing in the US by watch time. This matters for long-form documentary pacing, typography size, and composition.
- YouTube’s 2026 posture explicitly distinguishes high-effort creator work from low-quality repetitive AI slop.

Directional but non-official benchmark signals:
- third-party retention data suggests very sharp early dropoff and strong correlation between hook clarity and first-minute retention
- third-party reports also indicate viewers are increasingly sensitive to low-effort AI-feeling narration/visuals

Implication for Modern Archivist:
- this channel should optimize for “premium long-form on TV/mobile” rather than “fast social explainer”
- packaging and payoff must feel authored, specific, and human
- every system should be designed to avoid the “AI summary over slides” failure mode

## Audit by layer

### 1) Playbook (`styles/modern-archivist.yaml`)

Assessment: strong identity foundation, but incomplete as a high-performance execution contract.

What is strong:
- `identity.best_for` correctly frames the format as thesis-driven long-form documentary
- palette is distinctive and coherent: `#0F1117`, `#1E2330`, `#00CEC9`, `#E53935`
- typography choices are good for big-screen documentary packaging; Barlow Condensed is especially strong for title cards and thumbnails
- asset prompt prefix is specific enough to reduce generic corporate-explainer drift
- quality rules correctly ban dead static narration and force early tension

Gaps:
1. Motion is defined stylistically, not operationally enough.
   - Current file has transition list + hold ranges, but no hard visual-beat maximum despite `retention-doctrine.md` requiring a visual change every 3–6 seconds.
   - Recommendation: add `visual_beat_max_gap_seconds: 5` as a hard cap and separate hold rules by mode (`monologue`, `case_file`, `critical_error`, `data_sequence`).

2. Audio contract is under-specified.
   - Current playbook only gives voice style, music mood, volume, and `ducking_threshold_db`.
   - For repeatable quality, it should specify ducking attack/release, narration loudness target, music ceiling, and silence-before-reveal rule.

3. Accessibility and TV/mobile legibility are underspecified.
   - Because TV is now a primary viewing surface, large typography and clean composition matter more.
   - Because mobile browse still drives discovery, thumbnails and evidence cards need safe-zone rules.
   - Recommendation: add thumbnail safe zones, minimum text sizes, edge-avoidance rules, and evidence-card text limits.

4. Contrast needs tightening.
   - Measured contrast ratios:
     - `#E53935` on `#1E2330` = 3.71:1
     - `#E53935` on `#0F1117` = 4.46:1
     - `#00CEC9` on `#0F1117` = 9.59:1
     - `#F0F2F5` on `#0F1117` = 16.83:1
   - Implication: current red is fine for large accents but not robust for normal text on slate and narrowly misses 4.5:1 on the darkest background.
   - Recommendation: either lighten the red or explicitly reserve red for large labels/icons/pattern interrupts, not paragraph/small-card text.

5. Thumbnail contract lives outside the playbook.
   - The new thumbnail director is good, but the playbook itself should carry canonical thumbnail-safe rules so generator/pipeline stages can share one source of truth.

Suggested additions to the playbook schema:
- `thumbnail.safe_zone`
- `thumbnail.variants_per_brief`
- `mobile.safe_area`
- `motion.visual_beat_max_gap_seconds`
- `audio.ducking.attack_ms/release_ms/ratio`
- `narration.words_per_minute_range`
- `character.return_interval_seconds`
- `critical_error.max_duration_seconds`

### 2) Pipeline (`channels/modern-archivist/pipeline.yaml`)

Assessment: excellent pre-render quality gating, incomplete post-render growth loop.

What is strong:
- evidence audit before the script hardens is the right move
- content collection before script is exactly right for this format
- blocking script critics are valuable and aligned with the brand
- deterministic local render constraints are strong and protect reproducibility
- saved-assets-first policy is cost-disciplined and avoids silent AI generation sprawl

Main gap: the pipeline ends at render.

That is the biggest strategic weakness in the current design. For a 2026 YouTube system, render is not the finish line. The channel’s actual performance loop is:
research -> script -> media -> render -> package -> publish -> measure -> adapt

Missing stages and why they matter:
1. Thumbnail stage
   - `thumbnail-director.md` exists, but the pipeline does not invoke it as a first-class stage.
   - This creates drift risk and makes CTR optimization optional when it should be mandatory.

2. Publish-prep stage
   Missing outputs:
   - shelf title
   - description
   - chapters
   - pinned comment / CTA strategy
   - end-screen target
   - cards placement notes
   - Shorts teaser / promo cut
   - upload checklist

3. Test-and-compare loop
   - YouTube has expanded title/thumbnail test-and-compare capabilities; your system should assume packaging iteration is part of the production pipeline.
   - Recommendation: require three thumbnail variants and at least two title variants in a `publish_packet`.

4. Retention review stage
   - YouTube explicitly tells creators to inspect intro performance and retention key moments.
   - Current pipeline has no stage that converts actual retention graphs into updated rules.
   - This means the channel can ship strong episodes without building a learning flywheel.

5. Shorts / cross-format bridge
   - YouTube’s 2026 platform direction is explicitly multi-format.
   - For a long-form documentary channel, Shorts should act as trailer/curiosity engine, not replacement content.
   - Recommendation: a post-render teaser stage that cuts a 15–45 second unresolved contradiction clip.

Operational gap:
- `orchestration.max_wall_time_minutes: 60` may be tight for a full 10–20 minute polished render pipeline with QC on some hardware.
- Recommendation: split orchestration timeout from render timeout, or raise the ceiling.

### 3) Script director (`channels/modern-archivist/skills/script-director.md`)

Assessment: much improved and mostly aligned with high-retention documentary writing.

What is strong:
- cold-open doctrine is good and specific
- narrative structure is useful without becoming formula sludge
- retention loop rules are actually performance-oriented rather than generic storytelling advice
- source-footage/artifact-first rule is critical and correctly enforced at the script layer
- strong anti-pattern protection against lecture-mode openings

Where it still needs tightening:
1. Duration/pacing is not quantified enough.
   - The file says narration must fit the target, but it does not specify a preferred WPM band or expected density by section.
   - Recommendation: add a calibrated narration band, likely around 125–145 WPM depending on delivery mode.

2. Section-level retention contract is not fully enforced in the prose rules.
   - The schema has `retention_device`, but the script director should explicitly require every section to carry a non-neutral retention device.
   - Recommendation: no section may end on summary; each section must end on contradiction, escalation, reveal, or unresolved question.

3. Character return cadence should be explicit in the skill, not just doctrine.
   - `retention-doctrine.md` says return to the anchor every 45–60 seconds during evidence-heavy sections.
   - Recommendation: require that as a script-review checklist item.

4. Visual beat density should be explicit.
   - The skill requires mapping every beat to a render mode, which is good, but top performance will need a more measurable beat cadence.
   - Recommendation: require planned motion/visual reset every 3–6 seconds and a sequence-type change every 20–35 seconds in dense sections.

### 4) Thumbnail director (`channels/modern-archivist/skills/thumbnail-director.md`)

Assessment: strong start; now it needs to become a testable packaging system.

What is strong:
- correctly frames the thumbnail as provocation, not summary
- formulas are usable and tuned to documentary tension
- headline rules are short, aggressive, and shelf-aware
- title/headline split is correct and modern
- visual contract matches the playbook well

Gaps:
1. No mandatory multi-variant output.
   - The file currently produces one brief. That leaves learning on the table.
   - Recommendation: output 3 ranked variants by default.

2. No safe-zone contract.
   - Needed for mobile browse, suggested, search, and possible future shelf crops.

3. No explicit “TV + mobile readability” check.
   - Headline length is short, which helps, but the system should still enforce preview readability at small sizes.

4. No measurement loop.
   - Recommendation: include predicted reason-to-click, primary curiosity axis, and post-publish result logging fields.

5. Character/face policy is unclear.
   - Since Modern Archivist is not a standard talking-head channel, the thumbnail system should define when the puppet is used versus when a company/product artifact dominates.

### 5) Overall 2026 audience fit

Assessment: good audience fit, with one major caveat.

Why it fits:
- “corporate true crime” is a high-curiosity framing with broad stakes
- evidence-first positioning helps differentiate from shallow AI recap channels
- the channel doctrine correctly prioritizes contradiction, receipts, and machine-failure explanations
- the visual world is specific enough to feel like a real show rather than a generic automation stack

Main caveat:
- if the finished videos feel even slightly like narration over stylized slides, the format will underperform relative to the ambition of the package
- your own doctrine already recognizes this; the next step is converting that doctrine into harder measurable constraints and QA checks

## Priority findings

### P0: fix before relying on this as the canonical “high performance” pipeline
1. Add a mandatory `thumbnail` stage to `pipeline.yaml`.
2. Add a mandatory `publish_prep` stage with title, description, chapters, end-screen target, pinned comment, and Shorts teaser outputs.
3. Add a `retention_review` stage or companion operating workflow after publish.
4. Tighten the playbook with measurable motion, narration, and thumbnail safe-zone constraints.
5. Clarify red usage in the playbook due to contrast limitations.

### P1: strong next improvements
6. Add WPM and duration tolerance targets to the script/playbook contract.
7. Make character-return cadence an explicit script-review rule.
8. Add mobile/TV evidence-card typography rules.
9. Require three thumbnail variants and two title variants in packaging.
10. Capture actual CTR/retention outcomes back into a durable episode log.

### P2: scale optimizations
11. Add franchise metadata so recurring formats can be measured separately.
12. Add a pre-publish “shelf audit” that checks title/thumbnail coherence.
13. Add a “Shorts trailer” pattern library derived from top-performing cold opens.
14. Build a lightweight retention rubric from your first 5–10 uploads and patch the playbook accordingly.

## Recommended contract additions

Suggested new playbook keys:

```yaml
motion:
  visual_beat_max_gap_seconds: 5
  sequence_change_target_seconds: [20, 35]
  anchor_return_target_seconds: [45, 60]

audio:
  ducking:
    attack_ms: 10
    release_ms: 150
    ratio: "4:1"
  narration_lufs_target: -16
  music_ceiling_db: -20

narration:
  words_per_minute_range: [125, 145]
  target_duration_tolerance_seconds: 5

thumbnail:
  variants_per_brief: 3
  safe_zone:
    center_width_pct: 0.72
    center_height_pct: 0.72
    avoid_top_pct: 0.10
    avoid_bottom_pct: 0.10

mobile:
  min_text_px: 16
  avoid_edges_pct: 0.08

critical_error:
  max_duration_seconds: 12
```

Suggested new pipeline stages:

```yaml
- name: thumbnail
  skill: channels/modern-archivist/skills/thumbnail-director.md
  required_artifacts_in:
    - episode
    - render_report
  produces:
    - thumbnail_brief
    - thumbnail_variants
  checkpoint_required: true
  human_approval_default: true

- name: publish_prep
  skill: channels/modern-archivist/skills/youtube-metadata.md
  required_artifacts_in:
    - episode
    - render_report
    - thumbnail_brief
  produces:
    - publish_packet
  checkpoint_required: true
  human_approval_default: true

- name: retention_review
  skill: channels/modern-archivist/skills/retention-analyst.md
  required_artifacts_in:
    - publish_packet
    - publish_log
  produces:
    - retention_analysis
  checkpoint_required: false
  human_approval_default: false
```

## Final verdict

The new package is a real upgrade.

It is no longer a vague “documentary style” idea. It now has:
- a coherent show identity
- a clearer visual language
- better retention-aware script doctrine
- an explicit thumbnail philosophy
- a stronger evidence-first boundary

That said, if the goal is “videos that will perform very highly” with a 2026 audience, the missing leverage is not more aesthetic theory. It is packaging operations and post-publish learning.

Right now the system is good at making a stronger episode.
It is not yet equally good at making the next episode smarter than the previous one.

## Confidence notes

High confidence:
- identity, narrative, and evidence-first improvements are directionally correct
- missing publish/feedback stages are real strategic gaps
- contrast issue on red is real and measured

Medium confidence:
- exact numeric retention thresholds should ultimately be tuned from your own uploads, not adopted blindly from third-party benchmarks
- optimal WPM and sequence density may vary by narrator voice and topic density

Lower confidence / watch item:
- whether the current visual system is sufficiently source-footage-rich to avoid “stylized slides” on visually weak topics should be tested with a hard pilot, not assumed from doctrine alone

## Sources

Official / primary platform references:
- YouTube Help: `Measure key moments for audience retention`
- YouTube Help: `Thumbnail & title tips`
- YouTube Blog: `From the YouTube CEO: Our big bets for 2025`
- YouTube Blog: `YouTube CEO Neal Mohan’s 2026 Letter: The Future of YouTube`

Directional third-party benchmark reference:
- Retention Rabbit: `Beyond Views: The 2025 State of YouTube Audience Retention`
