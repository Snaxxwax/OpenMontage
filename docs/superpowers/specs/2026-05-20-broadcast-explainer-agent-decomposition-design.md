# Broadcast-Explainer Agent Decomposition

**Date:** 2026-05-20
**Pipeline:** `broadcast-explainer`
**Status:** Approved, pending implementation

## Problem

The `broadcast-explainer` pipeline's `assets` and `compose` stages are too broad. In practice, one conversation accumulates TTS generation, audio post-processing, HyperFrames composition authoring, timing sync, QA, and rendering — with no isolation between them. When something breaks (floating mouth, flat narration, timing drift), there is no targeted retry path. Everything lands in one bloated context that degrades reasoning quality and masks bugs until render time.

## Solution

Split into 6 focused stages, each dispatched as an isolated Claude Code sub-agent. Each agent reads from disk, writes to disk, and reports a structured pass/fail summary. The coordinator conversation stays thin — it sequences stages, passes artifact paths, and makes human approval decisions.

## Architecture

```
                          scene_plan approved
                                  │
              ┌───────────────────┴────────────────────┐
              │ (parallel)                              │ (parallel)
  dispatch → [narration-agent]           dispatch → [composition-author-agent]
              writes *_raw.wav                          reads scene_plan.json + DESIGN.md
              │                                         writes index.html (placeholders)
              ▼                                         │
  dispatch → [audio-post-agent]                         │
              writes narration_full.wav                 │
              writes audio_timing.json                  │
              │                                         │
              └──────────────────┬──────────────────────┘
                                 │ (join — both must complete)
                                 ▼
              dispatch → [composition-sync-agent]
                          reads index.html + audio_timing.json
                          writes index.html (real timings)
                                 │
                                 ▼
              dispatch → [composition-qa-agent]   ← human approval gate
                          runs lint + validate + animation map
                          writes qa_report.json
                          BLOCKS render on failure
                                 │
                                 ▼
              dispatch → [render-agent]
                          polls render, verifies output
                          writes render_report.json
```

**Key constraint:** sub-agents are stateless. They read artifact paths, never receive large file content inline. The coordinator passes paths only.

**Key parallel opportunity:** `narration` and `composition-author` both start immediately after `scene_plan` is approved. The composer works from `scene_plan.json` without needing exact audio durations — timing placeholders are filled later by `composition-sync`. This is the pipeline's largest time saving: the two longest creative steps run simultaneously.

## Stages

### Stage 1 — `narration`

| | |
|---|---|
| **Director skill** | `skills/pipelines/broadcast-explainer/narration-director.md` |
| **Input** | `artifacts/script.json` |
| **Output** | `assets/audio/{section_id}_raw.wav` per section |
| **Tools** | Bash, Read |
| **Pass condition** | All section WAVs exist, duration > 0 |
| **Failure recovery** | Re-dispatch with failed section IDs only; adjust temperature +0.1; surface to human after 2 failures on same section |

The director skill covers: Fish Speech tag reference and when-to-use rules (no `[professional broadcast tone]` as section opener; raw delivery for hooks and reveals), temperature guidance (0.8 default, max 0.9), reference ID (`asymmetric_narrator_v1`).

### Stage 2 — `audio-post`

| | |
|---|---|
| **Director skill** | `skills/pipelines/broadcast-explainer/audio-post-director.md` |
| **Input** | `assets/audio/*_raw.wav` |
| **Output** | `assets/audio/{section_id}.wav`, `assets/audio/narration_full.wav`, `artifacts/audio_timing.json` |
| **Tools** | Bash (ffmpeg, ffprobe), Read, Write |
| **Pass condition** | All normalized WAVs exist; `narration_full.wav` duration within 0.1s of sum of section durations; `audio_timing.json` validates against schema |
| **Failure recovery** | Re-dispatch (stateless, safe to re-run); if loudnorm clips, lower target to -16 LUFS and document deviation |

`audio_timing.json` schema:
```json
{
  "total_duration_seconds": 54.94,
  "sections": [
    { "id": "s01_hook", "start": 0.0, "end": 3.855, "duration": 3.855 },
    { "id": "s02_scale", "start": 3.855, "end": 17.229, "duration": 13.374 }
  ]
}
```

### Stage 3 — `composition-author`

| | |
|---|---|
| **Director skill** | `skills/pipelines/broadcast-explainer/composition-author-director.md` |
| **Input** | `artifacts/scene_plan.json`, `DESIGN.md`, `assets/` (SVG characters) |
| **Output** | `index.draft.html` with timing placeholders |
| **Tools** | Read, Write, Edit, Bash (hyperframes lint) |
| **Pass condition** | `hyperframes lint` exits 0 (warnings ok); all `TIMINGS.*` placeholders present; `window.__timelines` registered |
| **Failure recovery** | Re-dispatch with lint errors appended to prompt; patch only flagged issues |

**Timing placeholder pattern.** The composer writes a `TIMINGS` object at the top of the script block, using per-section objects with `start`, `end`, and `duration` fields. Composition-sync populates these from `audio_timing.json`:

```js
// Populated by composition-sync from audio_timing.json
const TIMINGS = {
  s01_hook:      { start: null, end: null, duration: null },
  s02_scale:     { start: null, end: null, duration: null },
  s03_secrecy:   { start: null, end: null, duration: null },
  s04_community: { start: null, end: null, duration: null },
  s05_political: { start: null, end: null, duration: null },
  s06_punchline: { start: null, end: null, duration: null },
  total: null
};

// Usage throughout timeline:
tl.to("#scene1", { opacity: 0, duration: 0.5 }, TIMINGS.s01_hook.end - 0.5);
mouthFlap(TIMINGS.s02_scale.start + 0.3, TIMINGS.s02_scale.end - 0.5);
```

Section IDs in `TIMINGS` match `script.json` section IDs exactly.

Director skill covers: AXIOM SVG pivot constants, `mouthFlap()` sub-timeline pattern with finite repeat calculation, DESIGN.md gate, layout-before-animation rule, scene transition rules (entrance-only, no exits except final scene).

### Stage 4 — `composition-sync`

| | |
|---|---|
| **Director skill** | `skills/pipelines/broadcast-explainer/composition-sync-director.md` |
| **Input** | `index.draft.html` (placeholder timings), `artifacts/audio_timing.json` |
| **Output** | `index.synced.html` (real timings), updated `data-duration` |
| **Tools** | Read, Write, Bash (hyperframes lint) |
| **Pass condition** | All `TIMINGS.*` fields populated; `data-duration` matches `audio_timing.json` total; no `null` values remain in TIMINGS object |
| **Failure recovery** | If a section ID in `TIMINGS` has no match in `audio_timing.json`: coordinator reconciles section ID drift between `script.json` and `audio_timing.json`, re-dispatches with corrected mapping |

This stage is purely mechanical — no creative decisions. The agent reads `index.draft.html`, populates all `TIMINGS.*` fields from `audio_timing.json`, updates `data-duration`, and writes to `index.synced.html`. The draft file is never modified in place.

### Stage 5 — `composition-qa`

| | |
|---|---|
| **Director skill** | `skills/pipelines/broadcast-explainer/composition-qa-director.md` |
| **Input** | `index.synced.html` |
| **Output** | `artifacts/qa_report.json` |
| **Tools** | Bash (hyperframes lint/validate, animation map), Read, Write |
| **Pass condition** | No render-breaking or viewer-facing defects (see blocking vs warning below) |
| **Human approval** | Required after pass — coordinator presents QA summary before render |
| **Failure recovery** | Failure type determines target agent (see QA failure routing below) |

QA runs in sequence:
1. `npx hyperframes lint` — structural errors block; file-size warning is informational only
2. `npx hyperframes validate` — WCAG contrast check; **only blocks if text is illegible at normal viewing size**; decorative elements and intentional low-contrast treatments are warnings
3. Animation map — `invisible` or `offscreen` on speech-active elements blocks; dead zones >2s on speech sections block; **intentional holds (pauses, dramatic beats) are warnings, not errors**

**Blocking vs warning classification:**

| Issue | Classification |
|---|---|
| `window.__timelines` not registered | Block |
| `data-duration` mismatch | Block |
| Speech-active element `invisible` or `offscreen` | Block |
| Dead zone >2s during active narration | Block |
| Text contrast < 3:1 on primary content | Block |
| Decorative element contrast failure | Warning |
| Text contrast 3:1–4.5:1 on large display text | Warning |
| Dead zone during intentional pause/hold | Warning |
| File-size lint warning | Warning |

`qa_report.json` schema:
```json
{
  "passed": true,
  "lint": { "errors": 0, "warnings": 1 },
  "validate": { "contrast_failures": [] },
  "animation_map": { "flags": [], "dead_zones": [] },
  "issues": []
}
```

**QA failure routing:**

| Failure type | Dispatched to |
|---|---|
| WCAG contrast failure | composition-author-agent (color fix only) |
| lint error | composition-author-agent (structural fix) |
| animation map: `invisible` | composition-author-agent (entrance tween missing) |
| animation map: `offscreen` | composition-author-agent (`svgOrigin` fix) |
| animation map: dead zone | composition-author-agent (timing gap) |
| sync token remaining | composition-sync-agent |

The QA agent writes the exact issue type and affected element into `qa_report.json`. The author agent reads the report — it receives a precise target, not a vague "fix it."

### Stage 6 — `render`

| | |
|---|---|
| **Director skill** | `skills/pipelines/broadcast-explainer/render-director.md` |
| **Input** | `index.synced.html` (QA-passed), `assets/audio/narration_full.wav` |
| **Output** | `renders/final.mp4`, `artifacts/render_report.json` |
| **Tools** | Bash (hyperframes render, ffprobe, cp), Read |
| **Pass condition** | MP4 exists; duration within 0.5s of `audio_timing.json` total; file size > 1MB |
| **Failure recovery** | Re-dispatch with last 20 lines of render log; if Chrome crash, retry with `--workers=1`; if duration mismatch, compare `narration_full.wav` duration vs `data-duration` and flag which is wrong |

## Pipeline Manifest Changes

`pipeline_defs/broadcast-explainer.yaml` updated stages:

```yaml
stages:
  - name: script           # unchanged
  - name: scene_plan       # unchanged
  - name: assets           # trimmed: non-audio asset prep only (SVG, imagery)
  - name: narration        # new
  - name: audio_post       # new
  - name: composition_author   # new — replaces compose
  - name: composition_sync     # new
  - name: composition_qa       # new; checkpoint_required: true; human_approval_default: true
  - name: render           # new — replaces edit
```

`compose-director.md` and `edit-director.md` are retired. Their content is redistributed across the new director skills.

## Sub-Agent Prompt Contract

Every coordinator dispatch follows this shape:

```
You are the [stage] agent for the broadcast-explainer pipeline.

Read the director skill at:
  skills/pipelines/broadcast-explainer/[stage]-director.md

Project root: /home/pop/repos/openmontage-asymmetric
Working directory: projects/[project-name]/

Inputs available:
  [list of artifact paths with types]

Your job:
  [one-sentence task description]

When done, report:
  - pass/fail
  - files written (paths)
  - warnings (if any)
  - if failed: exact error, which QA gate failed, affected element or section
```

## Files to Create

```
skills/pipelines/broadcast-explainer/
  narration-director.md
  audio-post-director.md
  composition-author-director.md
  composition-sync-director.md
  composition-qa-director.md
  render-director.md

schemas/artifacts/
  audio_timing.schema.json
  qa_report.schema.json
  render_report.schema.json
```

`pipeline_defs/broadcast-explainer.yaml` — updated (existing file)

## Files to Retire

```
skills/pipelines/broadcast-explainer/compose-director.md   → content split into composition-author + composition-sync + composition-qa directors
skills/pipelines/broadcast-explainer/edit-director.md      → content moved to render-director
```

## What This Fixes

| Problem from this session | Fixed by |
|---|---|
| Floating mouth not caught before render | `composition-qa` animation map flags `offscreen` |
| Flat narration (wrong tag usage) | `narration-director.md` codifies tag rules explicitly |
| Timing drift after audio regen | `composition-sync` stage is a dedicated mechanical step with validation |
| Single conversation grows unmanageable | Each stage runs in isolated sub-agent context |
| No targeted retry path | QA failure routing dispatches the right agent for each failure type |
