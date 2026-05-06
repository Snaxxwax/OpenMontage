# Asymmetric Render Postmortem

<!-- Run after every render — pass or fail. Captures lessons for the next episode. -->
<!-- Doctrine: docs/asymmetric/production_doctrine.md -->

---

## Header

```yaml
project_id: ""
video_title: ""
render_version: ""      # e.g. v01, v02
render_path: ""
date: ""
technical_pass: false
creative_pass: false
operator: ""
```

---

## 1. What Was Built

**Concept:**
**Pipeline:**
**Milestones completed:**
**Clips used (count and candidate IDs):**
**Total production sessions:**

---

## 2. Technical QC Results

| Check | Result | Delta from last render |
|-------|--------|----------------------|
| Duration | | |
| Silence events | | |
| Blank screen events | | |
| Source labels present | | |
| Source label overlap | | |
| Audio loudness (LUFS) | | |

**Technical pass:** yes / no
**If fail, root cause:**

---

## 3. Creative Review Results

| Dimension | Score | Minimum | Pass? |
|-----------|-------|---------|-------|
| Hook strength | | 4 | |
| Viewer stakes | | 4 | |
| Clip energy | | 4 | |
| Visual rhythm | | 4 | |
| Diagram quality | | 4 | |
| AI-documentary smell (5=none) | | 4 | |
| Payoff quality | | 4 | |
| Asymmetric fit | | 4 | |

**Creative pass:** yes / no
**If fail, primary reason:**

---

## 4. What Worked

<!-- Be specific. Name the exact moment, clip, or structural decision that succeeded and why. -->

| What worked | Why it worked | Replicate in future? |
|-------------|---------------|---------------------|
| | | yes / no |
| | | |
| | | |

---

## 5. What Failed

<!-- Be specific. Name the exact moment, section, clip choice, or structural decision that failed and why. -->

| What failed | Root cause | Phase where it should have been caught |
|-------------|-----------|---------------------------------------|
| | | performance package / clip gate / script / rhythm plan / render |
| | | |
| | | |

---

## 6. Clip Evaluation in Practice

<!-- How did the clips actually perform versus their pre-acquisition scores? -->

| Candidate ID | Pre-acquisition clip energy score | Actual editorial force in render | Delta |
|-------------|----------------------------------|--------------------------------|-------|
| | | | |
| | | | |

**Lesson for clip scoring:**

---

## 7. Visual Rhythm in Practice

**Planned change frequency:** every X seconds
**Actual perceived change frequency:** every X seconds
**Sections that felt slow:**
**Root cause of slow sections:**
**Fix for next render:**

---

## 8. Hook Performance

**Selected hook:**
**Did it stop the operator cold?** yes / no
**First 30 seconds verdict:**
**What the hook missed or could improve:**

---

## 9. Payoff Performance

**Payoff stated:**
**Did it deliver a reusable mental model?** yes / no
**If not, what was delivered instead:**
**What the payoff should have been:**

---

## 10. Gates That Should Have Caught This Earlier

<!-- For every failure, identify which gate — if stronger — would have caught it before render. -->

| Failure | Should have been caught at | Gate change needed |
|---------|---------------------------|-------------------|
| | performance package / clip gate / script / rhythm plan / readiness gate | |
| | | |

---

## 11. System Changes Required

<!-- What must change in the production doctrine, channel profile, or templates? -->

| Change needed | File to update | Priority |
|--------------|----------------|----------|
| | docs/asymmetric/production_doctrine.md | high / medium / low |
| | channels/asymmetric/channel_profile.yaml | |
| | templates/asymmetric/ | |

---

## 12. Next Render Plan

**If revise:**
- Specific changes to make:
- Clips to replace or re-cut:
- Sections to rewrite:
- Estimated sessions required:

**If reject:**
- Concept verdict (save or kill):
- If save: minimum changes to make the concept viable:
- If kill: note the failure mode to avoid in future episode selection:

---

## 13. Lessons for Future Episodes

<!-- Extract 2-3 portable lessons from this postmortem. These belong in phase1_lessons.md if they change the standing system knowledge. -->

| Lesson | Applies to | Update standing docs? |
|--------|-----------|----------------------|
| | all episodes / this topic type | yes / no |
| | | |
| | | |

---

## Operator Sign-off

Name:
Date:
Next action approved:
