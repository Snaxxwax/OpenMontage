# Asymmetric Reference Analysis Protocol

Version: 1.0
Last updated: 2026-05-17
Status: Active — required before scripting any serious Asymmetric episode

---

## Purpose

Asymmetric does not invent pacing targets per episode. It measures them from reference videos and calibrates each production to match or exceed the retention performance of comparable cinematic documentary content.

This protocol defines the exact repo-native path for running that analysis and feeding the results into the production system.

---

## When to Run Reference Analysis

Run reference analysis before scripting any episode that:
- Is longer than 5 minutes
- Involves complex multi-section structure
- Introduces a new visual grammar or format
- Is the first episode after a brand or format change

Short-form episodes (under 3 minutes) may use cached reference metrics from a prior analysis of the same format family, if approved.

---

## Repo-Native Tools

All reference analysis runs inside OpenMontage using these tools:

| Tool | Purpose |
|---|---|
| `video_downloader` | Download reference video for local analysis |
| `transcript_fetcher` | Fetch transcript for WPM and pacing analysis without download |
| `video_analyzer` | Extract VideoAnalysisBrief: shot duration, visual events, scene count, pacing profile |
| `scene_detect` | Scene boundary detection and cut frequency measurement |
| `frame_sampler` | Keyframe extraction at configurable intervals |
| `video_understand` | Semantic content analysis of frames and sequences |
| `audio_energy` | Music offset detection and energy profiling |

The coordinating skill is `skills/meta/video-reference-analyst.md`. Read it before running analysis.

---

## Step-by-Step Protocol

### Step 1: Select References

Choose 1–2 reference videos from channels with documented retention performance in the target format:
- MagnatesMedia (cinematic business documentary)
- Company Man (business history with strong retention)
- Wendover Productions (systems documentary)
- Kurzgesagt (mechanism-first explainer with high visual rhythm)

The reference must be in the same format family as the episode being planned: long-form documentary, short-form mechanism reveal, etc.

### Step 2: Fetch Transcript (Fast Path)

For WPM and structural analysis without downloading video:

```python
transcript_fetcher.execute({
    "source": "<youtube_url>",
    "output_format": "timestamped"
})
```

This returns timestamped text. Use it to measure:
- Words per minute (WPM) at different sections
- Time to first proof or evidence
- Time to first mode shift
- Total narration density

### Step 3: Run VideoAnalyzer (Full Analysis)

```python
video_analyzer.execute({
    "source": "<youtube_url_or_local_path>",
    "analysis_depth": "standard",
    "max_keyframes": 20
})
```

This returns a `VideoAnalysisBrief`. The critical fields:

| Field | What It Measures |
|---|---|
| `avg_shot_duration_seconds` | Average time between cuts |
| `scene_count` | Total number of distinct scenes |
| `visual_events_per_minute` | Meaningful visual state changes per minute |
| `motion_clip_ratio` | Fraction of scenes that are motion video (not stills) |
| `narration_wpm` | Words per minute of narration |
| `flow_variance` | Variance in shot duration — higher = more dynamic pacing |

### Step 4: Run Scene Detection

For cut-level granularity:

```python
scene_detect.execute({
    "input_path": "<local_video_path>",
    "threshold": 0.4
})
```

This returns scene boundaries. Calculate:
- Median shot duration
- Distribution of shot durations (short vs. long)
- Frequency of cuts in high-tension sections vs. low-tension sections

### Step 5: Extract Keyframes (Optional)

For visual style analysis:

```python
frame_sampler.execute({
    "input_path": "<local_video_path>",
    "mode": "scene_first",
    "max_frames": 20
})
```

Use extracted frames to characterize:
- Color grade (dark vs. bright, saturated vs. desaturated)
- Text density per frame
- Diagram vs. footage ratio
- Composition patterns (wide shot, close-up, document, talking head)

### Step 6: Interpret via video-reference-analyst.md

Read `skills/meta/video-reference-analyst.md` before presenting results.

Present analysis in the canonical 5-aspect form:
- Subject
- Subject Motion
- Scene
- Spatial Framing
- Camera

**Do not collapse to prose.** The 5-aspect form is what downstream stage directors read. Keep the labels.

---

## Translating Reference Metrics to Production Targets

After analysis, derive Asymmetric-specific targets using this mapping:

| Reference Metric | Asymmetric Target Derivation |
|---|---|
| `avg_shot_duration_seconds` | `max_static_hold_seconds` = reference × 0.8 (tighter than reference) |
| `visual_events_per_minute` | `target_visual_events_per_minute` = reference value (match, do not exceed without reason) |
| Pattern break frequency | `pattern_break_interval_max_seconds` = reference value, hard cap at 15s |
| `motion_clip_ratio` | `footage_ratio_target` = reference value (minimum for narrative sections) |
| `narration_wpm` | `narration_wpm_target` = reference value ± 10 WPM |
| Time to first proof | `first_receipt_timing_max_seconds` = reference time to first evidence moment |

---

## Outputs: What Gets Populated

Reference analysis produces or informs these artifacts:

### `visual_rhythm_plan.json`

Populate these fields from reference metrics before scripting:

```json
{
  "max_static_hold_seconds": "<derived from reference>",
  "target_visual_events_per_minute": "<from reference>",
  "pattern_break_interval_max_seconds": "<from reference, max 15>",
  "footage_ratio_target": "<motion_clip_ratio from reference>",
  "narration_wpm_target": "<from reference>",
  "first_receipt_timing_max_seconds": "<from reference>",
  "source_card_hold_duration_seconds": "<from reference avg_shot_duration>",
  "cut_density_target_cuts_per_minute": "<60 / avg_shot_duration>"
}
```

The visual_rhythm_plan is locked before the writer begins. The writer annotates every beat against these targets.

### `performance_brief.json`

Reference analysis informs:
- `visual_pacing_notes`: Cite the reference and its measured targets
- `retention_risks`: Flag sections where the episode structure may miss reference targets
- `first_15_seconds_plan`: Model the hook structure on the reference opening if strong

### Script Pacing

The writer uses reference WPM to calibrate narration density. Dense mechanism sections should match or slightly exceed reference WPM. Narrative sections should breathe at or below reference WPM.

---

## What Not to Do

- Do not invent pacing targets per episode without reference data
- Do not use reference analysis to copy content — measure mechanics, not topics
- Do not skip the 5-aspect output form — it is required for downstream director skills
- Do not run analysis and discard the output — it must populate `visual_rhythm_plan.json`
- Do not reuse cached reference metrics across format families without review

---

## Caching Reference Metrics

Once a `reference_metrics_profile.json` is produced and approved for a format family, it may be reused for subsequent episodes in the same format family without re-running analysis, provided:

1. No more than 90 days have passed
2. The format family has not changed
3. The brand has not undergone a visual system update

When in doubt, re-run analysis. Reference metrics are cheap to produce.
