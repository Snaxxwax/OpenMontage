# Asymmetric Render Readiness Gate

<!-- Run this before every render. All items must be checked before proceeding. -->
<!-- Reference: channels/asymmetric/channel_profile.yaml -->
<!-- Doctrine: docs/asymmetric/production_doctrine.md section 11 -->

---

## Header

```yaml
project_id: ""
video_title: ""
date: ""
operator: ""
render_runtime: ""   # remotion | hyperframes | ffmpeg
status: pending      # pending | approved | blocked
```

---

## Gate 1: Performance Package

- [ ] Performance package exists at `shared_studio/projects/<project_id>/artifacts/performance_package.md`
- [ ] All scorecard dimensions at or above minimum (hook ≥4, stakes ≥4, leverage ≥5, visual energy ≥4, boredom risk ≤low, Asymmetric fit ≥4)
- [ ] Performance package decision: PASS
- [ ] Operator approved performance package before research began

**Blocker if not met:** Do not proceed. Return to performance package.

---

## Gate 2: Clip Quality

- [ ] Source clip quality manifest exists at `shared_studio/projects/<project_id>/artifacts/source_clip_quality_manifest.yaml`
- [ ] At least 3 primary clips have all five scores at 4 or above
- [ ] No primary clip has clip_energy_score below 4
- [ ] No primary clip has cut_value_score below 4
- [ ] All approved clips have `acquisition_allowed: false` changed to `true` by operator
- [ ] All approved clips have `approval_status: approved` set by operator
- [ ] Operator approval recorded with date and clip IDs in the manifest

**Blocker if not met:** Do not proceed. Return to clip quality gate.

---

## Gate 3: Script and Beat Map

- [ ] Script beat map exists at `shared_studio/projects/<project_id>/artifacts/script_beat_map.yaml`
- [ ] Hook appears in the first narration beat
- [ ] Open loop planted within first 60 seconds
- [ ] Viewer stakes stated within first 60 seconds
- [ ] Clip pressure present in the mechanism section
- [ ] At least one diagram present in the mechanism section
- [ ] Open loop closed before or during payoff section
- [ ] Payoff delivers a reusable mental model (not a summary)
- [ ] Every clip in the beat map is in the approved clip manifest
- [ ] Read-aloud check passed (narration sounds like a briefing, not a report)

**Blocker if not met:** Return to script. Do not render with a summary payoff or a clip that is not approved.

---

## Gate 4: Visual Rhythm Plan

- [ ] Visual rhythm plan exists at `shared_studio/projects/<project_id>/artifacts/visual_rhythm_plan.yaml`
- [ ] No gap between visual events exceeds 5 seconds in diagram sections
- [ ] No gap between visual events exceeds 8 seconds in narrative/clip sections
- [ ] Minimum 12 visual events per every 75-second window across the full runtime
- [ ] No static diagram hold over 5 seconds
- [ ] Pattern interrupts planned every 10-15 seconds in long sections
- [ ] Source label safe zone verified for all clips and proof cards
- [ ] No source label overlaps body text, diagram labels, or proof visuals in plan
- [ ] rhythm_passes_targets: true in the plan file

**Footage ratio gate (mandatory for long-form 10min+):**
- [ ] `footage_ratio_audit.footage_gap_passes: true` — no consecutive stretch >90s without a footage cut
- [ ] Stat/callout beats use text overlays ON footage, not text-card-on-black (stat_cards_on_black == 0 or each is explicitly justified)
- [ ] Narrative sections use footage as the primary medium, not diagram or card sequences
- [ ] Mechanism sections do not run longer than 90s without a narrative bridge cut to footage

**Blocker if not met:** Revise the visual rhythm plan. Do not render with a failing rhythm or footage ratio.

---

## Gate 5: Source Labels

- [ ] Every source clip has a source label in the plan
- [ ] Every proof card has a source label in the plan
- [ ] All source labels are in the bottom strip safe zone (lower 20% of frame)
- [ ] No source label is planned to overlap body text, proof text, or diagram elements
- [ ] Source label timing: label stays visible for the full duration of the clip or proof card

**Blocker if not met:** Fix the label placement in the visual plan before rendering.

---

## Gate 6: Assets

- [ ] All narration audio files present in `shared_studio/projects/<project_id>/assets/audio/`
- [ ] All approved clips extracted and present in `shared_studio/projects/<project_id>/clips/`
- [ ] All clip durations verified against approved timestamp ranges
- [ ] All diagram/card assets accounted for in the edit plan
- [ ] Music track identified (or confirmed not used for this episode)
- [ ] Git status is clean (no uncommitted product-code changes)

**Blocker if not met:** Resolve missing assets before render.

---

## Gate 7: Pipeline Preflight

- [ ] OpenMontage tool registry passes preflight for this project
- [ ] `video_compose` available for selected render runtime
- [ ] `audio_mixer` available
- [ ] Source-commentary pipeline manifest is unmodified
- [ ] No product-code changes are staged or uncommitted

**Blocker if not met:** Resolve tool availability before render.

---

## Summary

| Gate | Status |
|------|--------|
| Performance package | pending |
| Clip quality | pending |
| Script and beat map | pending |
| Visual rhythm plan | pending |
| Source labels | pending |
| Assets | pending |
| Pipeline preflight | pending |

**Overall render readiness:**
- [ ] ALL GATES PASS — render may proceed
- [ ] ONE OR MORE GATES BLOCKED — render is blocked, see notes below

**Operator approval to render:**

Name:
Date:
Notes:
