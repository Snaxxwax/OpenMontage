# Broadcast-Explainer Agent Decomposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the broadcast-explainer pipeline's broad `assets`/`compose`/`edit` stages into 6 focused sub-agent stages, each with a dedicated director skill, clear artifact contracts, and a `composition_qa` human approval gate before render.

**Architecture:** New stages run as isolated sub-agent dispatches from the coordinator conversation. `composition-author` and `narration` run in parallel after `scene_plan` approval. `composition-sync` joins both outputs. `composition-qa` is the mandatory blocking gate. Two new artifact schemas (`audio_timing`, `qa_report`) formalize the handoffs. Director skills replace the content of the retired `compose-director.md` and `edit-director.md`.

**Tech Stack:** YAML pipeline manifests, JSON Schema (draft 2020-12), HyperFrames CLI (`npx hyperframes`), Fish Speech S2-Pro (port 8080), ffmpeg/ffprobe, jsonschema (Python), pytest

---

## File Map

**New files:**
- `schemas/artifacts/audio_timing.schema.json` — timing contract between audio-post and composition-sync
- `schemas/artifacts/qa_report.schema.json` — QA gate output with blocking/warning classification
- `tests/pipelines/broadcast_explainer/__init__.py` — test package marker
- `tests/pipelines/broadcast_explainer/test_schemas.py` — validates audio_timing and qa_report schemas
- `skills/pipelines/broadcast-explainer/narration-director.md` — Fish Speech tag rules, temperature, retry policy
- `skills/pipelines/broadcast-explainer/audio-post-director.md` — loudnorm params, concat, audio_timing.json production
- `skills/pipelines/broadcast-explainer/composition-author-director.md` — HyperFrames authoring with TIMINGS placeholders
- `skills/pipelines/broadcast-explainer/composition-sync-director.md` — mechanical TIMINGS population from audio_timing.json
- `skills/pipelines/broadcast-explainer/composition-qa-director.md` — lint/validate/animation-map, blocking vs warning rules
- `skills/pipelines/broadcast-explainer/render-director.md` — render invocation, polling, distribution

**Modified files:**
- `pipeline_defs/broadcast-explainer.yaml` — replace 3 broad stages with 6 focused stages
- `skills/pipelines/broadcast-explainer/assets-director.md` — strip TTS/audio content (now in narration + audio-post directors)

**Retired (content redistributed, do not delete — archive with a deprecation header):**
- `skills/pipelines/broadcast-explainer/compose-director.md`
- `skills/pipelines/broadcast-explainer/edit-director.md`

---

## Task 1: `audio_timing` schema + tests

**Files:**
- Create: `schemas/artifacts/audio_timing.schema.json`
- Create: `tests/pipelines/broadcast_explainer/__init__.py`
- Create: `tests/pipelines/broadcast_explainer/test_schemas.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/pipelines/broadcast_explainer/__init__.py` (empty).

Create `tests/pipelines/broadcast_explainer/test_schemas.py`:

```python
"""Schema validation tests for broadcast-explainer artifact schemas."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest
import jsonschema

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas" / "artifacts"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text())


# ── audio_timing ──────────────────────────────────────────────────────────────

VALID_AUDIO_TIMING = {
    "version": "1.0",
    "total_duration_seconds": 54.94,
    "sections": [
        {"id": "s01_hook",  "start": 0.0,   "end": 3.855,  "duration": 3.855},
        {"id": "s02_scale", "start": 3.855, "end": 17.229, "duration": 13.374},
    ],
}


def test_audio_timing_valid():
    schema = load_schema("audio_timing")
    jsonschema.validate(VALID_AUDIO_TIMING, schema)


def test_audio_timing_missing_sections():
    schema = load_schema("audio_timing")
    bad = {**VALID_AUDIO_TIMING}
    del bad["sections"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_audio_timing_section_missing_id():
    schema = load_schema("audio_timing")
    bad = {
        **VALID_AUDIO_TIMING,
        "sections": [{"start": 0.0, "end": 3.855, "duration": 3.855}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_audio_timing_negative_duration():
    schema = load_schema("audio_timing")
    bad = {
        **VALID_AUDIO_TIMING,
        "sections": [{"id": "s01_hook", "start": 0.0, "end": 3.855, "duration": -1.0}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
```

- [ ] **Step 2: Run tests to confirm they fail (schema file missing)**

```bash
cd /home/pop/repos/openmontage-asymmetric
python -m pytest tests/pipelines/broadcast_explainer/test_schemas.py::test_audio_timing_valid -v
```

Expected: `FileNotFoundError` or `JSONDecodeError` — schema doesn't exist yet.

- [ ] **Step 3: Write `audio_timing.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "openmontage/artifacts/audio_timing",
  "title": "Audio Timing",
  "description": "Section-level timing data produced by audio-post, consumed by composition-sync.",
  "type": "object",
  "required": ["version", "total_duration_seconds", "sections"],
  "properties": {
    "version": { "type": "string", "const": "1.0" },
    "total_duration_seconds": { "type": "number", "exclusiveMinimum": 0 },
    "sections": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "start", "end", "duration"],
        "properties": {
          "id":       { "type": "string" },
          "start":    { "type": "number", "minimum": 0 },
          "end":      { "type": "number", "minimum": 0 },
          "duration": { "type": "number", "exclusiveMinimum": 0 }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/pipelines/broadcast_explainer/test_schemas.py -k "audio_timing" -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add schemas/artifacts/audio_timing.schema.json \
        tests/pipelines/broadcast_explainer/__init__.py \
        tests/pipelines/broadcast_explainer/test_schemas.py
git commit -m "feat(schema): add audio_timing artifact schema with tests"
```

---

## Task 2: `qa_report` schema + tests

**Files:**
- Modify: `tests/pipelines/broadcast_explainer/test_schemas.py` (add qa_report tests)
- Create: `schemas/artifacts/qa_report.schema.json`

- [ ] **Step 1: Add failing tests to `test_schemas.py`**

Append to `tests/pipelines/broadcast_explainer/test_schemas.py`:

```python
# ── qa_report ─────────────────────────────────────────────────────────────────

VALID_QA_REPORT_PASS = {
    "version": "1.0",
    "passed": True,
    "lint": {"errors": 0, "warnings": 1},
    "validate": {"contrast_failures": []},
    "animation_map": {"flags": [], "dead_zones": []},
    "issues": [],
    "warnings": ["File size 348 lines exceeds recommendation"],
}

VALID_QA_REPORT_FAIL = {
    "version": "1.0",
    "passed": False,
    "lint": {"errors": 0, "warnings": 0},
    "validate": {"contrast_failures": []},
    "animation_map": {"flags": [], "dead_zones": []},
    "issues": [
        {
            "severity": "block",
            "type": "animation_map_offscreen",
            "element": "#axiom-layer #mouth-open",
            "description": "Element offscreen during speech section s02_scale",
        }
    ],
    "warnings": [],
}


def test_qa_report_pass_valid():
    schema = load_schema("qa_report")
    jsonschema.validate(VALID_QA_REPORT_PASS, schema)


def test_qa_report_fail_valid():
    schema = load_schema("qa_report")
    jsonschema.validate(VALID_QA_REPORT_FAIL, schema)


def test_qa_report_missing_passed():
    schema = load_schema("qa_report")
    bad = {**VALID_QA_REPORT_PASS}
    del bad["passed"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_qa_report_invalid_severity():
    schema = load_schema("qa_report")
    bad = {
        **VALID_QA_REPORT_FAIL,
        "issues": [{"severity": "critical", "type": "x", "element": "y", "description": "z"}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/pipelines/broadcast_explainer/test_schemas.py -k "qa_report" -v
```

Expected: `FileNotFoundError` — schema doesn't exist yet.

- [ ] **Step 3: Write `qa_report.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "openmontage/artifacts/qa_report",
  "title": "Composition QA Report",
  "description": "Output of composition-qa stage. passed=false blocks render.",
  "type": "object",
  "required": ["version", "passed", "lint", "validate", "animation_map", "issues"],
  "properties": {
    "version": { "type": "string", "const": "1.0" },
    "passed": { "type": "boolean" },
    "lint": {
      "type": "object",
      "required": ["errors", "warnings"],
      "properties": {
        "errors":   { "type": "integer", "minimum": 0 },
        "warnings": { "type": "integer", "minimum": 0 }
      },
      "additionalProperties": false
    },
    "validate": {
      "type": "object",
      "required": ["contrast_failures"],
      "properties": {
        "contrast_failures": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["selector", "ratio", "required"],
            "properties": {
              "selector": { "type": "string" },
              "ratio":    { "type": "number" },
              "required": { "type": "number" },
              "timestamp_seconds": { "type": "number" }
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    },
    "animation_map": {
      "type": "object",
      "required": ["flags", "dead_zones"],
      "properties": {
        "flags": {
          "type": "array",
          "items": { "type": "string" }
        },
        "dead_zones": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["start", "end", "duration_seconds"],
            "properties": {
              "start":            { "type": "number" },
              "end":              { "type": "number" },
              "duration_seconds": { "type": "number" }
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["severity", "type", "element", "description"],
        "properties": {
          "severity":    { "type": "string", "enum": ["block", "warn"] },
          "type":        { "type": "string" },
          "element":     { "type": "string" },
          "description": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Run all schema tests**

```bash
python -m pytest tests/pipelines/broadcast_explainer/test_schemas.py -v
```

Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add schemas/artifacts/qa_report.schema.json \
        tests/pipelines/broadcast_explainer/test_schemas.py
git commit -m "feat(schema): add qa_report artifact schema with tests"
```

---

## Task 3: Update `broadcast-explainer.yaml` pipeline manifest

**Files:**
- Modify: `pipeline_defs/broadcast-explainer.yaml`

- [ ] **Step 1: Replace the stages block**

Open `pipeline_defs/broadcast-explainer.yaml`. Replace the `required_skills` list and `stages` block with:

```yaml
required_skills:
  - pipelines/broadcast-explainer/script-director
  - pipelines/broadcast-explainer/scene-plan-director
  - pipelines/broadcast-explainer/assets-director
  - pipelines/broadcast-explainer/narration-director
  - pipelines/broadcast-explainer/audio-post-director
  - pipelines/broadcast-explainer/composition-author-director
  - pipelines/broadcast-explainer/composition-sync-director
  - pipelines/broadcast-explainer/composition-qa-director
  - pipelines/broadcast-explainer/render-director

stages:
  - name: script
    skill: pipelines/broadcast-explainer/script-director
    produces:
      - script
    checkpoint_required: true
    human_approval_default: true

  - name: scene_plan
    skill: pipelines/broadcast-explainer/scene-plan-director
    required_artifacts_in:
      - script
    produces:
      - scene_plan
    checkpoint_required: true
    human_approval_default: true

  - name: assets
    skill: pipelines/broadcast-explainer/assets-director
    required_artifacts_in:
      - scene_plan
      - script
    produces:
      - asset_manifest
    checkpoint_required: false
    human_approval_default: false

  - name: narration
    skill: pipelines/broadcast-explainer/narration-director
    required_artifacts_in:
      - script
    produces: []
    notes: "Writes assets/audio/{section_id}_raw.wav per section"
    checkpoint_required: false
    human_approval_default: false

  - name: audio_post
    skill: pipelines/broadcast-explainer/audio-post-director
    required_artifacts_in:
      - script
    produces: []
    notes: "Writes normalized WAVs, narration_full.wav, artifacts/audio_timing.json"
    checkpoint_required: false
    human_approval_default: false

  - name: composition_author
    skill: pipelines/broadcast-explainer/composition-author-director
    required_artifacts_in:
      - scene_plan
      - script
    produces: []
    notes: "Writes index.draft.html with TIMINGS placeholders"
    tools_available:
      - hyperframes_compose
    checkpoint_required: false
    human_approval_default: false

  - name: composition_sync
    skill: pipelines/broadcast-explainer/composition-sync-director
    required_artifacts_in:
      - scene_plan
    produces: []
    notes: "Reads index.draft.html + audio_timing.json, writes index.synced.html"
    checkpoint_required: false
    human_approval_default: false

  - name: composition_qa
    skill: pipelines/broadcast-explainer/composition-qa-director
    required_artifacts_in:
      - scene_plan
    produces: []
    notes: "Runs lint/validate/animation-map on index.synced.html, writes qa_report.json"
    checkpoint_required: true
    human_approval_default: true

  - name: render
    skill: pipelines/broadcast-explainer/render-director
    required_artifacts_in:
      - scene_plan
    produces:
      - render_report
    tools_available:
      - hyperframes_compose
    checkpoint_required: true
    human_approval_default: false
```

- [ ] **Step 2: Validate YAML parses**

```bash
python3 -c "import yaml; d=yaml.safe_load(open('pipeline_defs/broadcast-explainer.yaml')); print(f'{len(d[\"stages\"])} stages, ok')"
```

Expected: `10 stages, ok`

- [ ] **Step 3: Commit**

```bash
git add pipeline_defs/broadcast-explainer.yaml
git commit -m "feat(pipeline): decompose broadcast-explainer into 6 focused stages"
```

---

## Task 4: `narration-director.md`

**Files:**
- Create: `skills/pipelines/broadcast-explainer/narration-director.md`

- [ ] **Step 1: Write the skill**

```markdown
# Narration Director — broadcast-explainer

You are the narration agent. Your job is to generate Fish Speech TTS for each
section in `artifacts/script.json` and write raw WAV files to `assets/audio/`.

## Setup

Fish Speech S2-Pro runs locally at `http://127.0.0.1:8080`. If it does not
respond, check memory/fish_speech.md for start instructions.

Required Python packages (available in Fish Speech venv):
- `ormsgpack`, `requests`
- `fish_speech.utils.schema.ServeTTSRequest` (from `/home/pop/local-ai/fish-speech/`)

## Script

```python
import ormsgpack, requests, sys, time
from pathlib import Path
sys.path.insert(0, '/home/pop/local-ai/fish-speech')
from fish_speech.utils.schema import ServeTTSRequest

OUT = Path('assets/audio')
OUT.mkdir(parents=True, exist_ok=True)
```

## Tag Reference

Tags shape prosody. Use them deliberately — wrong tag usage is the most common
cause of flat narration.

| Tag | When to use |
|-----|-------------|
| `[pause]` | ~0.5s beat — question landing, before a reveal |
| `[short pause]` | ~0.2s breath — between punchy clauses |
| `[emphasis]` | Stress a key word or number |
| `[low voice]` | Conspiratorial, close-to-mic delivery |
| `[low and slow]` | Weighted, deliberate — final reveals, single-word kickers |
| `[professional broadcast tone]` | Reset to neutral authority MID-sentence only — never as a section opener |

**Critical rules:**
1. Never open a section with `[professional broadcast tone]`. It creates a stiff, anchored delivery that kills the hook.
2. Hooks and reveals get raw delivery (no tag) or `[low voice]`. Let the content carry the weight.
3. `[professional broadcast tone]` is a mid-sentence reset after an emotional beat — e.g., "...and they had almost no say. [professional broadcast tone] Michigan is a critical battleground state."
4. Vary per section. If three sections start the same way, the narration is flat.

## Parameters

```python
ServeTTSRequest(
    text=text,
    reference_id="asymmetric_narrator_v1",
    format="wav",
    streaming=False,
    normalize=True,
    temperature=0.8,     # default — expressive without losing control
    top_p=0.8,
    repetition_penalty=1.1,
    use_memory_cache="on",
)
```

Never exceed `temperature=0.9`. Below 0.7 produces flat delivery.

## Pass Condition

For each section ID in `script.json`:
- `assets/audio/{section_id}_raw.wav` exists
- Duration > 0 (verify with ffprobe)

## Retry Policy

If a section sounds wrong on review: re-generate with `temperature` adjusted +0.1
(max 0.9). After 2 failures on the same section, report to coordinator with the
section text and the specific problem (e.g., "tag ignored", "pronunciation wrong",
"monotone").

## Report Format

When complete, report:
- pass/fail
- List of files written with durations
- Any sections that required retry and why
```

- [ ] **Step 2: Verify file exists**

```bash
wc -l skills/pipelines/broadcast-explainer/narration-director.md
```

Expected: ~80 lines.

- [ ] **Step 3: Commit**

```bash
git add skills/pipelines/broadcast-explainer/narration-director.md
git commit -m "feat(skill): add narration-director for broadcast-explainer"
```

---

## Task 5: `audio-post-director.md`

**Files:**
- Create: `skills/pipelines/broadcast-explainer/audio-post-director.md`

- [ ] **Step 1: Write the skill**

```markdown
# Audio Post Director — broadcast-explainer

You are the audio-post agent. Your job is to normalize all raw WAV sections,
concatenate them, and produce `artifacts/audio_timing.json`.

## Steps

### 1. Normalize each section to -14 LUFS

```bash
for f in s01_hook s02_scale s03_secrecy s04_community s05_political s06_punchline; do
  ffmpeg -y -i assets/audio/${f}_raw.wav \
    -af loudnorm=I=-14:TP=-1.0:LRA=11 \
    assets/audio/${f}.wav \
    -loglevel error
done
```

If loudnorm clips (`TP` exceeded), retry with `-14` → `-16` LUFS and document the
deviation in `audio_timing.json` under a `notes` field.

### 2. Measure section durations

```bash
for f in s01_hook s02_scale s03_secrecy s04_community s05_political s06_punchline; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/audio/${f}.wav)
  echo "$f $dur"
done
```

### 3. Build concat list and concatenate

Use absolute paths to avoid ffmpeg treating paths as relative to the list file:

```bash
PROJ=$(pwd)
cat > /tmp/concat_audio.txt << EOF
file '${PROJ}/assets/audio/s01_hook.wav'
file '${PROJ}/assets/audio/s02_scale.wav'
file '${PROJ}/assets/audio/s03_secrecy.wav'
file '${PROJ}/assets/audio/s04_community.wav'
file '${PROJ}/assets/audio/s05_political.wav'
file '${PROJ}/assets/audio/s06_punchline.wav'
EOF
ffmpeg -y -f concat -safe 0 -i /tmp/concat_audio.txt assets/audio/narration_full.wav -loglevel error
```

### 4. Write `artifacts/audio_timing.json`

Compute cumulative start times from section durations. Validate that
`total_duration_seconds` is within 0.1s of the actual `narration_full.wav` duration
(check with ffprobe).

Section IDs must match `script.json` `sections[].id` exactly.

```json
{
  "version": "1.0",
  "total_duration_seconds": 54.94,
  "sections": [
    { "id": "s01_hook",      "start": 0.0,    "end": 3.855,  "duration": 3.855  },
    { "id": "s02_scale",     "start": 3.855,  "end": 17.229, "duration": 13.374 },
    { "id": "s03_secrecy",   "start": 17.229, "end": 32.322, "duration": 15.093 },
    { "id": "s04_community", "start": 32.322, "end": 39.938, "duration": 7.616  },
    { "id": "s05_political", "start": 39.938, "end": 48.576, "duration": 8.638  },
    { "id": "s06_punchline", "start": 48.576, "end": 54.938, "duration": 6.362  }
  ]
}
```

## Pass Condition

- All `assets/audio/{section_id}.wav` exist
- `assets/audio/narration_full.wav` exists
- `artifacts/audio_timing.json` exists and validates against `schemas/artifacts/audio_timing.schema.json`
- `narration_full.wav` duration within 0.1s of `audio_timing.json` `total_duration_seconds`

## Report Format

When complete, report:
- pass/fail
- Files written
- Total duration
- Any loudnorm deviation (if target was lowered from -14 to -16 LUFS)
```

- [ ] **Step 2: Commit**

```bash
git add skills/pipelines/broadcast-explainer/audio-post-director.md
git commit -m "feat(skill): add audio-post-director for broadcast-explainer"
```

---

## Task 6: `composition-author-director.md`

**Files:**
- Create: `skills/pipelines/broadcast-explainer/composition-author-director.md`

- [ ] **Step 1: Write the skill**

```markdown
# Composition Author Director — broadcast-explainer

You are the composition-author agent. Your job is to write `index.draft.html` —
a complete HyperFrames composition for the project, with timing placeholders
instead of hardcoded section boundary times.

## Before writing anything

1. Read `DESIGN.md` in the project root. Use its exact colors, fonts, and
   motion rules. Do not reach for generic colors (`#3b82f6`, `#333`) or fonts
   (`Roboto`, `Inter` without a DESIGN.md mandate).
2. Read `artifacts/scene_plan.json` to understand scene structure, character
   actions, and AXIOM poses per section.
3. Read `assets/` to find character SVGs.

## TIMINGS placeholder pattern

At the top of your `<script>` block, declare a `TIMINGS` object with `null`
values. `composition-sync` will populate these from `audio_timing.json`.
Use section IDs that exactly match `script.json`.

```js
// Populated by composition-sync — do NOT hardcode these values
const TIMINGS = {
  s01_hook:      { start: null, end: null, duration: null },
  s02_scale:     { start: null, end: null, duration: null },
  s03_secrecy:   { start: null, end: null, duration: null },
  s04_community: { start: null, end: null, duration: null },
  s05_political: { start: null, end: null, duration: null },
  s06_punchline: { start: null, end: null, duration: null },
  total: null
};
```

Use these throughout the timeline:

```js
// Scene transition — 0.5s before section end
tl.to("#scene1", { filter:"blur(10px)", opacity:0, duration:0.5 },
  TIMINGS.s01_hook.end - 0.5);

// Mouth flap — from 0.3s after section start to 0.5s before end
mouthFlap(TIMINGS.s02_scale.start + 0.3, TIMINGS.s02_scale.end - 0.5);

// data-duration on the composition div
// Write: data-duration="TOTAL_DURATION_PLACEHOLDER"
// composition-sync replaces this token too
```

For `data-duration`, write the literal string `TOTAL_DURATION_PLACEHOLDER` as
the attribute value. Composition-sync replaces it with `TIMINGS.total`.

## AXIOM SVG pivot constants

When animating AXIOM, declare these at the top of the script block:

```js
const MO   = "256 219"; // mouth-open center in SVG viewbox space
const MN   = "256 218"; // mouth-neutral center
const HEAD = "256 267"; // head pivot
const BODY = "256 460"; // body pivot
const ARM_L = "164 328"; // left arm shoulder
const ARM_R = "348 328"; // right arm shoulder
```

Always pass `svgOrigin: MO` (or the relevant constant) in every GSAP tween that
targets an AXIOM element. Without this, GSAP uses SVG (0,0) as the transform
origin and elements jump to wrong positions.

## mouthFlap helper

```js
function mouthFlap(startT, endT) {
  const half = 0.11;
  const cycles = Math.ceil((endT - startT) / (half * 2)) - 1;
  const sub = gsap.timeline({ repeat: cycles });
  sub.to("#axiom-layer #mouth-open",    { scaleY: 1,    svgOrigin: MO, duration: half, ease: "power1.inOut" }, 0)
     .to("#axiom-layer #mouth-neutral", { scaleY: 0,    svgOrigin: MN, duration: half, ease: "power1.inOut" }, 0)
     .to("#axiom-layer #mouth-open",    { scaleY: 0.05, svgOrigin: MO, duration: half, ease: "power1.inOut" }, half)
     .to("#axiom-layer #mouth-neutral", { scaleY: 0.18, svgOrigin: MN, duration: half, ease: "power1.inOut" }, half);
  tl.add(sub, startT);
}
```

Call mouthFlap for every section where AXIOM is speaking. Never use `repeat: -1`.

## Layout before animation

Write CSS for every element's fully-visible hero state first. Only then add
GSAP tweens. Use `gsap.from()` for entrances (FROM offscreen TO CSS position).
Use `gsap.to()` for exits only on the final scene.

## Scene transitions

Every multi-scene composition must:
1. Use blur crossfade between every scene pair (no jump cuts)
2. Animate every element IN with `gsap.from()` — no element appears fully-formed
3. NOT add exit animations except on the final scene — the transition IS the exit
4. The outgoing scene must be fully visible at the moment the transition starts

## HyperFrames rules (mandatory)

- All timelines: `{ paused: true }` — framework controls playback
- Register: `window.__timelines["<composition-id>"] = tl`
- No `Math.random()`, `Date.now()`, or async timeline construction
- Audio always as separate `<audio>` element; video always `muted playsinline`
- `data-track-index` does not affect z-index — use CSS `z-index`

## Pass condition

Run `npx hyperframes lint` from the project directory. Zero errors required.
Warnings are acceptable. Confirm `window.__timelines` is registered. Confirm all
`TIMINGS.*` references exist (grep for any hardcoded section boundary numbers).

## Output

Write to: `index.draft.html`
Do NOT write to `index.html` or `index.synced.html`.

## Report format

- pass/fail
- File written: `index.draft.html`
- Lint result summary
- List of TIMINGS references used (to help composition-sync verify coverage)
```

- [ ] **Step 2: Commit**

```bash
git add skills/pipelines/broadcast-explainer/composition-author-director.md
git commit -m "feat(skill): add composition-author-director for broadcast-explainer"
```

---

## Task 7: `composition-sync-director.md`

**Files:**
- Create: `skills/pipelines/broadcast-explainer/composition-sync-director.md`

- [ ] **Step 1: Write the skill**

```markdown
# Composition Sync Director — broadcast-explainer

You are the composition-sync agent. Your job is purely mechanical: read
`index.draft.html` and `artifacts/audio_timing.json`, populate all TIMINGS
values, and write `index.synced.html`. No creative decisions.

## Steps

### 1. Read audio_timing.json

Parse `artifacts/audio_timing.json`. Build a lookup by section ID:

```python
import json
timing = json.loads(open('artifacts/audio_timing.json').read())
by_id = {s['id']: s for s in timing['sections']}
total = timing['total_duration_seconds']
```

### 2. Read index.draft.html

Read the full file as text.

### 3. Replace the TIMINGS object

Find the `const TIMINGS = {` block. Replace every `null` value with the
corresponding number from `audio_timing.json`:

```python
import re

def replace_timings(html, by_id, total):
    for section_id, t in by_id.items():
        html = html.replace(
            f'  {section_id}:      {{ start: null, end: null, duration: null }}',
            f'  {section_id}: {{ start: {t["start"]}, end: {t["end"]}, duration: {t["duration"]} }}'
        )
    html = html.replace('  total: null', f'  total: {total}')
    return html
```

Note: match the exact whitespace from `index.draft.html`. If the whitespace
differs, use a regex: `r'\b(s\d+_\w+):\s*\{[^}]+\}'`.

### 4. Replace data-duration placeholder

```python
html = html.replace('data-duration="TOTAL_DURATION_PLACEHOLDER"',
                    f'data-duration="{total}"')
```

### 5. Validate — no nulls remain

```python
assert 'start: null' not in html, "TIMINGS not fully populated"
assert 'end: null'   not in html, "TIMINGS not fully populated"
assert 'TOTAL_DURATION_PLACEHOLDER' not in html, "data-duration not replaced"
```

### 6. Write output

Write to `index.synced.html`. Do NOT modify `index.draft.html`.

### 7. Lint check

```bash
npx hyperframes lint
```

The linter reads `index.html` by default. Temporarily symlink or pass the path:

```bash
npx hyperframes lint --composition index.synced.html
```

If the linter does not support `--composition`, copy `index.synced.html` to
`index.html` for linting only, then remove it: 
`cp index.synced.html index.html && npx hyperframes lint && rm index.html`

Zero errors required.

## Pass condition

- `index.synced.html` written
- No `null` values in TIMINGS object
- `data-duration` is a number, not `TOTAL_DURATION_PLACEHOLDER`
- `npx hyperframes lint` passes (zero errors)

## Failure: section ID not found

If a section ID in the draft's TIMINGS object has no match in
`audio_timing.json`, stop and report:
- Which section IDs are in the draft but missing from audio_timing.json
- Which section IDs are in audio_timing.json but not in the draft

The coordinator reconciles the ID mismatch and re-dispatches.

## Report format

- pass/fail
- File written: `index.synced.html`
- `data-duration` value used
- Any section IDs that required special handling
```

- [ ] **Step 2: Commit**

```bash
git add skills/pipelines/broadcast-explainer/composition-sync-director.md
git commit -m "feat(skill): add composition-sync-director for broadcast-explainer"
```

---

## Task 8: `composition-qa-director.md`

**Files:**
- Create: `skills/pipelines/broadcast-explainer/composition-qa-director.md`

- [ ] **Step 1: Write the skill**

```markdown
# Composition QA Director — broadcast-explainer

You are the composition-qa agent. Your job is to run three checks on
`index.synced.html` and write `artifacts/qa_report.json`. A `passed: false`
report blocks render — the coordinator routes the issue to the right fix agent.

## Check 1: Lint

```bash
# Run from project root; linter finds index.html by default
# If using index.synced.html, symlink temporarily:
cp index.synced.html index.html
npx hyperframes lint
rm index.html
```

**Blocks:** any `error` in output.
**Warns (does not block):** `composition_file_too_large` warning.

## Check 2: Validate (WCAG contrast)

```bash
npx hyperframes validate --composition index.synced.html
# or: cp index.synced.html index.html && npx hyperframes validate && rm index.html
```

**Blocks:** text contrast < 3:1 on primary content text.
**Warns (does not block):**
- Contrast 3:1–4.5:1 on large display text (≥24px or ≥19px bold)
- Contrast failure on decorative/background elements
- Failure on elements that are opacity:0 at the checked timestamp (false positive)

To distinguish false positives: check whether the failing element is in a scene
that is invisible at the checked timestamp. If the scene is faded out, it's a
false positive → treat as warning.

## Check 3: Animation map

```bash
node skills/hyperframes/scripts/animation-map.mjs . --out .hyperframes/anim-map
```

Read `.hyperframes/anim-map/animation-map.json`.

**Blocks:**
- Any `offscreen` or `invisible` flag on an element that is active during a
  speech section (cross-reference section times with `artifacts/audio_timing.json`)
- Any dead zone > 2s that overlaps with active narration (not a pause/beat)

**Warns (does not block):**
- Dead zones during intentional dramatic pauses or holds (check scene_plan notes)
- Dead zones in non-speech sections

## Blocking vs warning classification

| Issue | Classification |
|-------|---------------|
| `window.__timelines` not registered | Block |
| `data-duration` mismatch | Block |
| Speech-active element `invisible`/`offscreen` | Block |
| Dead zone > 2s during active narration | Block |
| Text contrast < 3:1 on primary content | Block |
| Decorative element contrast failure | Warn |
| Large display text contrast 3:1–4.5:1 | Warn |
| Dead zone during intentional pause/hold | Warn |
| File-size lint warning | Warn |
| False-positive contrast (invisible scene) | Warn |

## Writing qa_report.json

Write to `artifacts/qa_report.json`. Schema: `schemas/artifacts/qa_report.schema.json`.

```json
{
  "version": "1.0",
  "passed": true,
  "lint": { "errors": 0, "warnings": 1 },
  "validate": { "contrast_failures": [] },
  "animation_map": { "flags": [], "dead_zones": [] },
  "issues": [],
  "warnings": ["File size 348 lines exceeds recommendation"]
}
```

On failure, `passed: false` and populate `issues[]`:

```json
{
  "severity": "block",
  "type": "animation_map_offscreen",
  "element": "#axiom-layer #mouth-open",
  "description": "Element offscreen during speech section s02_scale (3.855–17.229s)"
}
```

## QA failure routing (for coordinator reference)

| `issues[].type` | Fix agent |
|-----------------|-----------|
| `wcag_contrast` | composition-author (color fix only) |
| `lint_error` | composition-author (structural fix) |
| `animation_map_invisible` | composition-author (add entrance tween) |
| `animation_map_offscreen` | composition-author (fix svgOrigin) |
| `animation_map_dead_zone` | composition-author (add animation in gap) |
| `sync_token_remaining` | composition-sync |

## Report format

- pass/fail
- `artifacts/qa_report.json` written
- One-line summary per issue (type + element + severity)
```

- [ ] **Step 2: Commit**

```bash
git add skills/pipelines/broadcast-explainer/composition-qa-director.md
git commit -m "feat(skill): add composition-qa-director for broadcast-explainer"
```

---

## Task 9: `render-director.md`

**Files:**
- Create: `skills/pipelines/broadcast-explainer/render-director.md`

- [ ] **Step 1: Write the skill**

```markdown
# Render Director — broadcast-explainer

You are the render agent. Your job is to render `index.synced.html` to MP4,
verify the output, and copy it to the distribution target.

## Pre-render check

Confirm `artifacts/qa_report.json` exists and `passed: true`. If not, stop and
report — do not render a composition that failed QA.

Confirm `assets/audio/narration_full.wav` exists and has duration > 0:
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 assets/audio/narration_full.wav
```

## Render

HyperFrames render reads `index.html` by default. Copy the synced file first:
```bash
cp index.synced.html index.html
npx hyperframes render .
```

The render writes to `renders/<project-name>_<timestamp>.mp4`. Note the output path.

## Poll for completion

If the render is dispatched as a background command, poll the task output file:
```bash
until grep -q "completed\|ERROR\|failed" <task_output_file>; do sleep 20; done
tail -5 <task_output_file>
```

## Post-render verification

```bash
RENDER_PATH="renders/<output>.mp4"
EXPECTED_DUR=$(python3 -c "import json; print(json.load(open('artifacts/audio_timing.json'))['total_duration_seconds'])")
ACTUAL_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RENDER_PATH")
python3 -c "e=$EXPECTED_DUR; a=$ACTUAL_DUR; assert abs(e-a) < 0.5, f'Duration mismatch: expected {e}s got {a}s'"
```

Also verify file size > 1MB:
```bash
python3 -c "import os; s=os.path.getsize('$RENDER_PATH'); assert s > 1_000_000, f'File too small: {s} bytes'"
```

## Distribution

Copy to syncthing:
```bash
cp "$RENDER_PATH" ~/syncthing/final.mp4
```

## Write render_report.json

```json
{
  "version": "1.0",
  "outputs": [
    {
      "path": "renders/<output>.mp4",
      "format": "mp4",
      "codec": "h264",
      "audio_codec": "aac",
      "resolution": "1080x1920",
      "fps": 30,
      "duration_seconds": 54.94,
      "file_size_bytes": 5373346,
      "platform_target": "youtube_shorts"
    }
  ],
  "render_time_seconds": 3254
}
```

## Failure recovery

| Error | Action |
|-------|--------|
| Chrome crash in render log | Retry with `npx hyperframes render . --workers 1` |
| Duration mismatch > 0.5s | Compare `narration_full.wav` duration vs `data-duration` in `index.synced.html` — report which is wrong |
| File < 1MB | Check render log for early exit; report last 20 lines |

## Report format

- pass/fail
- Output path and duration
- File size
- Distribution target confirmed
```

- [ ] **Step 2: Commit**

```bash
git add skills/pipelines/broadcast-explainer/render-director.md
git commit -m "feat(skill): add render-director for broadcast-explainer"
```

---

## Task 10: Archive retired director skills + trim assets-director

**Files:**
- Modify: `skills/pipelines/broadcast-explainer/compose-director.md`
- Modify: `skills/pipelines/broadcast-explainer/edit-director.md`
- Modify: `skills/pipelines/broadcast-explainer/assets-director.md`

- [ ] **Step 1: Add deprecation header to compose-director.md**

Prepend to `skills/pipelines/broadcast-explainer/compose-director.md`:

```markdown
> **DEPRECATED** — Content split into `composition-author-director.md`,
> `composition-sync-director.md`, and `composition-qa-director.md`.
> This file is kept for reference only. Do not use for new productions.

---

```

- [ ] **Step 2: Add deprecation header to edit-director.md**

Prepend to `skills/pipelines/broadcast-explainer/edit-director.md`:

```markdown
> **DEPRECATED** — Content moved to `render-director.md`.
> This file is kept for reference only. Do not use for new productions.

---

```

- [ ] **Step 3: Strip TTS/audio content from assets-director.md**

Open `skills/pipelines/broadcast-explainer/assets-director.md`. Add to the top:

```markdown
> **Scope (post-decomposition):** This director handles non-audio asset prep only —
> SVG character retrieval, background imagery, props, and font confirmation.
> TTS generation is handled by `narration-director.md`.
> Audio post-processing is handled by `audio-post-director.md`.

```

- [ ] **Step 4: Commit**

```bash
git add skills/pipelines/broadcast-explainer/compose-director.md \
        skills/pipelines/broadcast-explainer/edit-director.md \
        skills/pipelines/broadcast-explainer/assets-director.md
git commit -m "docs(skill): archive compose/edit directors, scope assets-director to non-audio"
```
