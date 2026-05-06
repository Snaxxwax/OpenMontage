# Asymmetric Operator Review Packet

<!-- Prepare after technical QC passes. Present to operator for manual creative review. -->
<!-- Doctrine: docs/asymmetric/production_doctrine.md sections 3, 4, 6, 11 -->

---

## Header

```yaml
project_id: ""
video_title: ""
render_path: ""        # e.g. shared_studio/projects/p001/renders/render_v01.mp4
render_date: ""
qc_status: ""          # technical_pass | technical_fail
operator: ""
review_status: pending # pending | creative_pass | revise | reject
```

---

## What to Watch For

This is a creative review, not a technical review. Technical QC has already run.

You are evaluating:
1. **Hook** — does it stop you cold in the first 5 seconds?
2. **Viewer stakes** — do you understand why this matters within 60 seconds?
3. **Clip pressure** — do the source clips create conflict and constraint, or do they just confirm narration?
4. **Visual rhythm** — does the pace hold your attention throughout, or do you feel the urge to skip?
5. **Diagram quality** — do the diagrams reveal the hidden structure, or do they explain the visible surface?
6. **AI-documentary smell** — does any section feel sterile, flat, or AI-generated?
7. **Payoff** — do you leave with a reusable mental model or just a summary of facts?
8. **Asymmetric brand fit** — does this feel like a private intelligence briefing or a corporate explainer?

---

## Technical QC Summary

| Check | Result | Notes |
|-------|--------|-------|
| Duration | | |
| No silence > 1s | | |
| No blank screens | | |
| Source labels present | | |
| Source label safe zone | | |
| No label overlap | | |
| Audio loudness (LUFS) | | |
| All clips present and trimmed | | |

---

## Creative Scorecard

<!-- Operator fills after watching full render. Rate 1-5. -->

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| Hook strength (1 = flat, 5 = stops cold) | | |
| Viewer stakes clarity by 60s | | |
| Clip energy and pressure | | |
| Visual rhythm — diagram sections | | |
| Visual rhythm — narrative sections | | |
| Diagram quality (pressure map, not explainer) | | |
| AI-documentary smell (5 = none detected, 1 = obvious) | | |
| Payoff quality (5 = reusable model, 1 = summary) | | |
| Asymmetric brand fit (5 = private briefing, 1 = corporate) | | |

**Average creative score:** /5

---

## Clip-by-Clip Pressure Evaluation

<!-- Operator fills for each source clip used in the render. -->

| Clip | Candidate ID | What it created (pressure / conflict / authority) | Pass or revise? |
|------|-------------|--------------------------------------------------|----------------|
| | | | |
| | | | |
| | | | |

---

## Boredom Audit

<!-- Mark any 10-second window where you felt the urge to stop watching. -->

| Timecode | Issue | Severity (low / medium / high) |
|----------|-------|-------------------------------|
| | | |
| | | |

---

## Source Label Audit

<!-- Note any source label that was hard to read, overlapped other text, or was missing. -->

| Timecode | Clip or card | Issue |
|----------|-------------|-------|
| | | |

---

## Specific Revision Notes

<!-- If creative_pass is not declared, document exactly what must change. -->

| Issue | Severity | Fix required before |
|-------|----------|-------------------|
| | | next render attempt |
| | | |

---

## Decision

Only the operator may mark creative pass.

- [ ] **CREATIVE PASS** — The render meets the Asymmetric standard. Ready to ship.
- [ ] **REVISE** — Specific sections must be corrected. See revision notes above. Do not ship.
- [ ] **REJECT** — The render fails the Asymmetric standard at a fundamental level. Trigger postmortem before planning next render.

**Operator name:**
**Date:**
**creative_pass declared:** yes / no
**Next step:**
