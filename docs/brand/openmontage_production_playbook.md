# Asymmetric OpenMontage Production Playbook

Version: 1.0
Last updated: 2026-05-17
Status: Active — recommended pipeline path for all Asymmetric productions

---

## Recommended Pipeline Architecture

Asymmetric productions use a **hybrid pipeline as the outer production shell** with **source-commentary evidence discipline** layered inside.

Do not create a new pipeline. Use OpenMontage's existing `hybrid` pipeline for production and borrow source-commentary's evidence contracts for claim integrity.

### Why Hybrid, Not Source-Commentary

The `source-commentary` pipeline is experimental and built for commentary-on-video-clips aesthetics. Asymmetric's target format — cinematic business documentary with motion graphics — requires the `hybrid` pipeline's footage-first architecture, which supports:
- Real-world graded stock footage as the primary narrative medium
- Designed support assets (motion graphics, diagrams, receipt cards) as the secondary layer
- Quality gates for source/support balance and overlay density

### Why Source-Commentary Discipline, Not Full Pipeline

Source-commentary's evidence contracts (evidence_candidate_manifest, clip_use_receipt, approved_clip_manifest) enforce claim-to-source traceability that the hybrid pipeline does not natively require. Borrowing these contracts prevents the most common Asymmetric failure mode: producing a technically correct video with claims that cannot be sourced to primary documents.

---

## Full Production Sequence

### Phase 0: Leverage Brief

Create `artifacts/leverage_brief.json` and have it approved before any research begins.

The leverage brief locks:
- The hidden mechanism (not a topic — a specific structural mechanism)
- The control surface (the specific clause, rule, rate schedule, or policy that concentrates control)
- The cost transfer chain (ordered list of who absorbs what cost)
- The beneficiaries (specific entities that capture the value)
- The accountability gap (why this mechanism has not been constrained)
- The viewer takeaway (the reusable mental model)
- The advertiser safety posture (risk_level + approved/forbidden language list)

No research begins without an approved leverage_brief. This is the intellectual contract for the episode.

### Phase 1: Reference Analysis

Run reference analysis on 1–2 target-format reference videos. See `docs/brand/reference_analysis_protocol.md`.

Produce `reference_metrics_profile.json`. Lock `visual_rhythm_plan.json` from reference metrics.

Reference analysis must complete before scripting. The writer uses the visual_rhythm_plan to annotate every beat.

### Phase 2: Research Brief

Produce `research_brief.json` using the leverage brief as the intellectual framework.

Research must:
- Confirm the mechanism with primary sources
- Find the specific receipts: filings, contracts, rate cases, regulatory orders, court records
- Identify source candidates for each episode section
- Identify footage candidates for narrative sections (archive.org, Wikimedia, NARA, NASA, other public domain)

Research must not:
- Change the core mechanism without operator approval and leverage_brief revision
- Acquire footage or pay for sources without operator approval

### Phase 3: Performance Brief

Produce `performance_brief.json`. Lock the hook, title angle, thumbnail angle, and first-15-seconds plan.

The performance brief must pass the hook strength gate: "Would a viewer who stumbled onto this at 0:00 stay for the next 60 seconds?" Required answer: yes.

The performance brief is locked before scripting. No script begins without an approved performance_brief.

### Phase 4: Evidence Planning

Produce `evidence_candidate_manifest.json` and `source_candidate_manifest.json`.

Every claim in the script must map to a candidate receipt. Claims without candidates must be cut or softened to what can be proven.

Clip use receipts (`clip_use_receipt.json`) must be created for every source clip before acquisition is approved.

### Phase 5: Script and Beat Map

Write the script following:
- `docs/brand/leverage_story_template.md` (ten-part structure)
- `docs/brand/advertiser_safety.md` (language discipline)
- `visual_rhythm_plan.json` (pacing targets)

The beat map annotates every narration line with:
- Visual state at that moment (footage / diagram / card / title)
- Source clip or asset reference
- Visual event type (cut, highlight, label, arrow, reframe)
- Running visual event count per 75-second window

No script advances to asset planning without a beat map that hits visual rhythm targets.

### Phase 6: Asset Planning and Acquisition

Plan visual assets by section:
- **Narrative sections:** Graded archive/public-domain footage
- **Mechanism sections:** Remotion animated diagrams (chokepoint map, leverage map, cost transfer diagram)
- **Evidence beats:** Remotion receipt_card scenes (document close-up with Amber overlay)
- **Stat moments:** Remotion stat_card scenes
- **Segment titles:** HyperFrames kinetic typography cards
- **Chapter cards:** HyperFrames full-screen chapter cards (long-form only)

Acquire footage only after operator approves each clip via clip_use_receipt.

### Phase 7: Composition

#### Remotion — Use for
- Data-driven cinematic scenes: receipt cards, leverage maps, cost-transfer flow diagrams, stat cards
- Timeline sequences, ownership web diagrams
- Caption overlay (word-level, narration-synced)
- Audio embedding (narration + music with volume control)

**Scene types for Asymmetric:**
- `text_card` — cost transfer callouts, claims
- `stat_card` — large figure reveals in IBM Plex Mono + Amber highlight
- `receipt_card` — document close-up with Amber overlay strip, slow push-in
- `leverage_map` — control surface diagram, Amber chokepoint markers, animated dependency arrows
- `cost_transfer` — value flow diagram with Acid Lime extraction arrows
- `chapter_card` — full-screen near-black, Amber accent line, chapter name

#### HyperFrames — Use for
- Kinetic segment title cards ("THE LEVERAGE MAP", "WHO PAYS", etc.) with GSAP animation
- Chapter opening cards with GSAP letter-reveal or line-wipe in Amber
- High-end typography inserts that require CSS/GSAP-native animation

#### FFmpeg — Use for
- Final assembly and concat unless a stronger Remotion path is proven
- Color grade on stock footage (shadows to near-black, desaturate highlights)
- Loudness normalization to -14 LUFS integrated
- QC: silence detection, black frame detection, audio level check
- Subtitle burn-in on already-rendered video (post-hoc only)

Do not use FFmpeg for composition when Remotion provides the scene type. Remotion is the default composition engine.

### Phase 8: Quality Control

Run the QC sequence:
1. **Prepared media QC:** Check acquired footage and assets for technical issues
2. **Staging gate:** Validate all staged assets are present and correctly formatted
3. **Render QC:** `ffprobe` + `silencedetect` + `blackdetect` + frame extraction checks
4. **Visual rhythm QC:** Verify beat map targets are met in the final render
5. **Source label QC:** Confirm all clips have visible source labels in the bottom 20% strip
6. **Advertiser safety QC:** Review script and title against `docs/brand/advertiser_safety.md`

### Phase 9: Operator Review

The operator watches the full render before any creative_pass is declared.

`creative_pass` is operator-only. No agent or tool may set it.

The operator may declare: pass, conditional pass (with documented revision notes), or fail (triggers postmortem before next episode).

### Phase 10: Publish Package

Produce `publish_package.json` with:
- Final video path
- Title (approved)
- Description with affiliate stack (if applicable)
- Chapter timestamps
- Thumbnail variants (minimum 3: power, mechanism, consequence)
- Pinned comment draft

---

## Tool Availability Reference

Tools confirmed available in this repo:

| Category | Tool | Status |
|---|---|---|
| Analysis | `video_analyzer`, `scene_detect`, `frame_sampler`, `transcript_fetcher`, `transcriber`, `audio_energy` | Available |
| Footage | `archive_org`, `wikimedia`, `nasa`, `nara`, `coverr` | Available |
| Footage | `pexels_video`, `pixabay_video` | Unavailable (Cloudflare) |
| Composition | Remotion (via `remotion-composer/`) | Available |
| Composition | HyperFrames (via `hyperframes_compose`) | Available |
| Composition | FFmpeg | Available |
| TTS | Fish Speech S2 Pro (port 8080) | Local service — requires manual start |
| QC | `composition_validator`, `visual_qa`, `audio_probe` | Available |

---

## What Not to Do

- Do not start scripting before the leverage_brief and performance_brief are approved
- Do not start scripting before visual_rhythm_plan.json is populated from reference analysis
- Do not acquire footage without operator-approved clip_use_receipts
- Do not use source cards as the final visual aesthetic — they are evidence beats inside a cinematic structure
- Do not use static diagram holds longer than 5 seconds without a visual state change
- Do not use stock footage without the Asymmetric color grade
- Do not create a new pipeline until one manual pilot proves the hybrid+evidence template
- Do not set creative_pass — that is the operator's role only

---

## Pipeline vs. Playbook

This playbook does not require a new pipeline. The `hybrid` pipeline handles the outer production structure. The evidence discipline comes from borrowing source-commentary artifacts.

When the hybrid+evidence template has proven itself across two or more episodes, create a `playbooks/asymmetric-leverage.yaml` to codify it as a named extension of the hybrid pipeline. Do not do this before the template is proven.
