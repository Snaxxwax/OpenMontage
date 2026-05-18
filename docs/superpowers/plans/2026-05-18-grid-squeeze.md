# The Grid Squeeze — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce "The Grid Squeeze" — a 5-minute broadcast-investigative animated video about data center grid impacts, rendered with HyperFrames and narrated by Fish Speech S2-Pro using the egirl_v1 voice.

**Architecture:** Pipeline infrastructure (YAML + director skills) is created first so this episode instantiates the reusable `broadcast-explainer` archetype. Then episode production proceeds: script artifact → scene plan → narration audio (Fish Speech) → HyperFrames HTML composition → render to MP4.

**Tech Stack:** HyperFrames v0.6.20, Fish Speech S2-Pro (port 8080, egirl_v1 reference), ffmpeg (loudnorm post-process), GSAP 3 (composition animations), Python 3.11 (TTS generation script)

---

## File Map

**New files — infrastructure:**
- `pipeline_defs/broadcast-explainer.yaml` — pipeline manifest
- `styles/broadcast-investigative.yaml` — visual playbook
- `skills/pipelines/broadcast-explainer/script-director.md`
- `skills/pipelines/broadcast-explainer/scene-plan-director.md`
- `skills/pipelines/broadcast-explainer/assets-director.md`
- `skills/pipelines/broadcast-explainer/edit-director.md`
- `skills/pipelines/broadcast-explainer/compose-director.md`

**New files — episode:**
- `projects/grid-squeeze/artifacts/brief.json`
- `projects/grid-squeeze/artifacts/script.json`
- `projects/grid-squeeze/artifacts/scene_plan.json`
- `projects/grid-squeeze/assets/audio/narration_hook_raw.wav`
- `projects/grid-squeeze/assets/audio/narration_ch1_raw.wav`
- `projects/grid-squeeze/assets/audio/narration_ch2_raw.wav`
- `projects/grid-squeeze/assets/audio/narration_ch3_raw.wav`
- `projects/grid-squeeze/assets/audio/narration_ch4_raw.wav`
- `projects/grid-squeeze/assets/audio/narration_landing_raw.wav`
- `projects/grid-squeeze/assets/audio/narration_hook.wav` (loudnorm processed)
- `projects/grid-squeeze/assets/audio/narration_ch1.wav`
- `projects/grid-squeeze/assets/audio/narration_ch2.wav`
- `projects/grid-squeeze/assets/audio/narration_ch3.wav`
- `projects/grid-squeeze/assets/audio/narration_ch4.wav`
- `projects/grid-squeeze/assets/audio/narration_landing.wav`
- `projects/grid-squeeze/assets/audio/music_tension.mp3` (**manual step** — Suno generation, see Task 7)
- `projects/grid-squeeze/assets/audio/music_land.mp3` (**manual step** — Suno generation, see Task 7)
- `projects/grid-squeeze/hyperframes/index.html` — main 300s composition
- `projects/grid-squeeze/renders/final.mp4`

---

## Task 1: Pipeline YAML and Style Playbook

**Files:**
- Create: `pipeline_defs/broadcast-explainer.yaml`
- Create: `styles/broadcast-investigative.yaml`

- [ ] **Step 1.1: Create broadcast-explainer pipeline YAML**

Create `pipeline_defs/broadcast-explainer.yaml`:

```yaml
name: broadcast-explainer
version: "1.0"
description: >
  Broadcast-investigative animated explainer. Dark studio aesthetic, data journalism tone.
  HyperFrames render runtime (locked). Narration via local Fish Speech S2-Pro.
  Output: 1920×1080 MP4, 30fps.
category: generated
stability: production

render_runtime: hyperframes

default_checkpoint_policy: guided

extensions:
  custom_scripts: true
  custom_playbooks: false
  custom_skills: true
  custom_tools: false

required_skills:
  - pipelines/broadcast-explainer/script-director
  - pipelines/broadcast-explainer/scene-plan-director
  - pipelines/broadcast-explainer/assets-director
  - pipelines/broadcast-explainer/edit-director
  - pipelines/broadcast-explainer/compose-director

orchestration:
  mode: sequential
  budget_default_usd: 0.00

compatible_playbooks:
  locked:
    - broadcast-investigative

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
    tools_available:
      - fish_speech_tts
    checkpoint_required: false
    human_approval_default: false

  - name: edit
    skill: pipelines/broadcast-explainer/edit-director
    required_artifacts_in:
      - scene_plan
      - asset_manifest
    produces:
      - edit_decisions
    checkpoint_required: false
    human_approval_default: false

  - name: compose
    skill: pipelines/broadcast-explainer/compose-director
    required_artifacts_in:
      - edit_decisions
      - asset_manifest
    produces:
      - render_report
    tools_available:
      - hyperframes_compose
    checkpoint_required: true
    human_approval_default: false
```

- [ ] **Step 1.2: Create broadcast-investigative style playbook**

Create `styles/broadcast-investigative.yaml`:

```yaml
identity:
  name: "Broadcast Investigative"
  category: broadcast
  mood: urgent, authoritative, investigative
  pace: fast
  best_for: "Data journalism explainers, investigative documentary, channel Asymmetric"

visual_language:
  color_palette:
    background: "#0d1117"
    accent_red: "#c0392b"
    data_amber: "#ffcc00"
    text_primary: "#ffffff"
    text_secondary: "rgba(255,255,255,0.65)"
    document_paper: "#f5f0e8"
    document_annotation: "#cc2200"
    chapter_bumper_bg: "#1a0505"
  composition: edge-heavy, data-forward, lower-third attribution
  texture: subtle grain overlay on chapter bumpers

typography:
  headings:
    font: "Barlow Condensed"
    weight: 800
    tracking: "-0.01em"
    source: "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&display=swap"
  body:
    font: "Inter"
    weight: 400
  data_labels:
    font: "JetBrains Mono"
    weight: 400
  lower_thirds:
    font: "Inter"
    weight: 500

scene_pacing:
  max_static_hold_seconds: 8
  cut_cadence_range: [6, 10]
  chapter_bumper_duration: 5

scene_types:
  chapter_bumper:
    bg: "#1a0505"
    accent_bar: "#c0392b"
    text_color: "#ffffff"
    chapter_label_color: "#c0392b"
  broadcast_anchor_card:
    bg: "#0d1117"
    headline_color: "#ffffff"
    stat_color: "#ffcc00"
    source_color: "rgba(255,255,255,0.5)"
    accent_bar: "#c0392b"
  kinetic_text:
    bg: "#0d1117"
    text_color: "#ffffff"
    emphasis_color: "#ffcc00"
  data_visualization:
    bg: "#0d1117"
    bar_color: "#c0392b"
    comparison_color: "#ffcc00"
    label_color: "rgba(255,255,255,0.7)"
    axis_color: "rgba(255,255,255,0.2)"
  document_reveal:
    paper_color: "#f5f0e8"
    text_color: "#1a1a1a"
    annotation_color: "#cc2200"
    redaction_color: "#1a1a1a"

audio:
  narration_lufs: -14
  music_under_speech_db: -18
  music_gap_db: -10
  subtitles: true
  subtitle_style: caption-editorial-emphasis
```

- [ ] **Step 1.3: Verify both files are valid YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('pipeline_defs/broadcast-explainer.yaml'))" && echo "pipeline OK"
python3 -c "import yaml; yaml.safe_load(open('styles/broadcast-investigative.yaml'))" && echo "style OK"
```

Expected:
```
pipeline OK
style OK
```

- [ ] **Step 1.4: Commit**

```bash
git add pipeline_defs/broadcast-explainer.yaml styles/broadcast-investigative.yaml
git commit -m "feat(pipeline): add broadcast-explainer pipeline and broadcast-investigative style"
```

---

## Task 2: Director Skills

**Files:**
- Create: `skills/pipelines/broadcast-explainer/script-director.md`
- Create: `skills/pipelines/broadcast-explainer/scene-plan-director.md`
- Create: `skills/pipelines/broadcast-explainer/assets-director.md`
- Create: `skills/pipelines/broadcast-explainer/edit-director.md`
- Create: `skills/pipelines/broadcast-explainer/compose-director.md`

- [ ] **Step 2.1: Create skills directory**

```bash
mkdir -p skills/pipelines/broadcast-explainer
```

- [ ] **Step 2.2: Create script-director.md**

Create `skills/pipelines/broadcast-explainer/script-director.md`:

```markdown
# Broadcast Explainer — Script Director

Write the episode narration script. Output: `artifacts/script.json`.

## Voice Profile
- Narrator: e-girl — high-pitched, energetic, slightly anime-streamer quality
- Voice contrast with serious investigative content is intentional
- Reference audio: `references/egirl_v1/` (Fish Speech S2-Pro, port 8080)

## Tag Syntax (S2-Pro bracket notation)
Place tags anywhere inline. Allowed tags:
- `[e-girl voice]` — reset to default at segment start
- `[excited]` — hook line, big stat reveals
- `[curious]` — rhetorical questions
- `[whispering]` — mechanism reveals, "hidden" beats
- `[enthusiastic]` — chapter opening lines
- `[concerned]` — rate hike / who pays sections
- `[pause]` — before key numbers and after hooks
- `[short pause]` — clause transitions
- `[emphasis]` — key numbers and phrases

## Duration Target
150 words/minute. For a 300s episode: ~750 words total.

## Output Schema
```json
{
  "episode_id": "string",
  "total_duration_seconds": 300,
  "segments": [
    {
      "id": "hook",
      "start_seconds": 0,
      "end_seconds": 25,
      "tagged_text": "..."
    }
  ]
}
```
```

- [ ] **Step 2.3: Create scene-plan-director.md**

Create `skills/pipelines/broadcast-explainer/scene-plan-director.md`:

```markdown
# Broadcast Explainer — Scene Plan Director

Map script segments to 26 scenes with HyperFrames block types. Output: `artifacts/scene_plan.json`.

## Scene Type Registry
- `chapter_bumper` — full-screen bold type on dark red
- `broadcast_anchor_card` — headline + stat + lower-third source
- `kinetic_text` — large-scale GSAP letter animation
- `data_viz_bar` — bar chart (data-chart block)
- `data_viz_flow` — flow diagram (custom HTML/GSAP)
- `data_viz_map` — US map with dots + ticker
- `document_reveal` — paper texture with animated redaction lift
- `cta_card` — end card

## Scene Count Requirements
- 4 chapter bumpers
- 8 broadcast anchor cards
- 6 kinetic text beats
- 5 data visualizations (including map)
- 2 document reveals
Total: 26 scenes

## Output Schema
```json
{
  "episode_id": "string",
  "total_scenes": 26,
  "scenes": [
    {
      "id": "string",
      "type": "string",
      "start_seconds": 0,
      "end_seconds": 10,
      "narration_segment": "hook",
      "content": {}
    }
  ]
}
```
```

- [ ] **Step 2.4: Create assets-director.md**

Create `skills/pipelines/broadcast-explainer/assets-director.md`:

```markdown
# Broadcast Explainer — Assets Director

Generate narration audio using Fish Speech S2-Pro. Output: `artifacts/asset_manifest.json`.

## TTS Generation
Server: http://127.0.0.1:8080 — health check before requests
Reference ID: `egirl_v1` — pass on every request

```python
import httpx, pathlib

def generate_segment(text: str, output_path: str):
    resp = httpx.post("http://127.0.0.1:8080/v1/tts", json={
        "text": text,
        "reference_id": "egirl_v1",
        "format": "wav",
        "streaming": False,
        "normalize": True,
        "temperature": 0.8,
        "top_p": 0.8,
        "repetition_penalty": 1.1,
        "use_memory_cache": "on",
    }, timeout=300)
    pathlib.Path(output_path).write_bytes(resp.content)
```

## Post-Processing (required)
```bash
ffmpeg -y -i narration_raw.wav \
  -af loudnorm=I=-14:TP=-1.0:LRA=11 \
  narration.wav
```
Target: –14 LUFS

## GPU Management
GPU limit: 24GB VRAM. Kill ComfyUI before loading Fish Speech:
```bash
kill $(pgrep -f "main.py.*18188")
```
Fish Speech S2-Pro startup: ~30s. Check health before sending.
```

- [ ] **Step 2.5: Create edit-director.md**

Create `skills/pipelines/broadcast-explainer/edit-director.md`:

```markdown
# Broadcast Explainer — Edit Director

Produce edit_decisions.json mapping scene timing to audio assets.

## Audio Mix Rules
- Narration: 0dB reference
- Music under speech: –18dB
- Music in gaps: –10dB
- Subtitles: caption-editorial-emphasis style, white condensed sans on dark strip

## Output Schema
```json
{
  "episode_id": "string",
  "render_runtime": "hyperframes",
  "audio_tracks": [
    {"type": "narration", "file": "assets/audio/narration_hook.wav", "start": 0},
    {"type": "music", "file": "assets/audio/music_tension.mp3", "start": 0, "end": 240, "volume": 0.15}
  ],
  "scene_timing": []
}
```
```

- [ ] **Step 2.6: Create compose-director.md**

Create `skills/pipelines/broadcast-explainer/compose-director.md`:

```markdown
# Broadcast Explainer — Compose Director

Render the HyperFrames composition to final.mp4.

## Render Command
```bash
cd projects/grid-squeeze/hyperframes && \
  npx hyperframes lint && \
  npx hyperframes render . \
    -o ../renders/final.mp4 \
    --fps 30 \
    --quality high
```

## Success Criteria
- File exists: `projects/grid-squeeze/renders/final.mp4`
- Duration: 295–305 seconds
- Resolution: 1920×1080

## Validation
```bash
ffprobe -v quiet -show_entries format=duration,size \
  -show_entries stream=width,height \
  -of default=noprint_wrappers=1 \
  projects/grid-squeeze/renders/final.mp4
```
```

- [ ] **Step 2.7: Commit director skills**

```bash
git add skills/pipelines/broadcast-explainer/
git commit -m "feat(pipeline): add broadcast-explainer director skills"
```

---

## Task 3: Project Directory Structure

**Files:** `projects/grid-squeeze/` tree

- [ ] **Step 3.1: Create project directories**

```bash
mkdir -p projects/grid-squeeze/artifacts
mkdir -p projects/grid-squeeze/assets/audio
mkdir -p projects/grid-squeeze/assets/images
mkdir -p projects/grid-squeeze/hyperframes
mkdir -p projects/grid-squeeze/renders
```

- [ ] **Step 3.2: Write brief.json**

Create `projects/grid-squeeze/artifacts/brief.json`:

```json
{
  "episode_id": "grid-squeeze",
  "channel": "asymmetric",
  "pipeline": "broadcast-explainer",
  "title": "The Grid Squeeze",
  "hook": "Your electricity bill went up. Here's the building responsible.",
  "thesis": "A single hyperscale data center drawing 847MW gets approved in a closed council vote, strains local grid capacity, triggers a residential rate hike, and the mechanism that made it all possible — tax abatements and NDAs — is designed to repeat in 47 cities.",
  "format": "5-minute animated explainer",
  "target_duration_seconds": 300,
  "render_runtime": "hyperframes",
  "playbook": "broadcast-investigative",
  "voice": {
    "engine": "fish_speech_s2pro",
    "reference_id": "egirl_v1",
    "server": "http://127.0.0.1:8080"
  },
  "resolution": "1920x1080",
  "fps": 30
}
```

- [ ] **Step 3.3: Verify structure**

```bash
find projects/grid-squeeze -type d
```

Expected:
```
projects/grid-squeeze
projects/grid-squeeze/artifacts
projects/grid-squeeze/assets
projects/grid-squeeze/assets/audio
projects/grid-squeeze/assets/images
projects/grid-squeeze/hyperframes
projects/grid-squeeze/renders
```

---

## Task 4: Script Artifact

**Files:** Create `projects/grid-squeeze/artifacts/script.json`

- [ ] **Step 4.1: Write script.json**

Create `projects/grid-squeeze/artifacts/script.json`:

```json
{
  "episode_id": "grid-squeeze",
  "total_duration_seconds": 300,
  "segments": [
    {
      "id": "hook",
      "start_seconds": 0,
      "end_seconds": 25,
      "tagged_text": "[e-girl voice][excited] Your electricity bill went up.\n[pause] Here's the building responsible.\n[short pause][curious] One building. One approval. One council vote — at ten forty-five p.m., on a Tuesday.\n[emphasis] Eight hundred and forty-seven megawatts.\n[whispering] And most people in that city have no idea it even exists."
    },
    {
      "id": "ch1",
      "start_seconds": 25,
      "end_seconds": 95,
      "tagged_text": "[e-girl voice][enthusiastic] Chapter one. The Approval.\n[short pause] The permit application was four hundred and twelve pages.\n[curious] How long did the public comment period last?\n[emphasis] Fourteen days.\n[short pause][concerned] The NDA was signed before the planning commission even saw the blueprints.\n[whispering] That's not unusual. That's standard.\n[short pause] The council vote was six to one.\n[curious] The one dissenting vote? She asked how much power it would draw.\n[emphasis] The answer wasn't in the public record.\n[short pause][concerned] What was in the public record: eight hundred and forty-seven megawatts of permitted draw.\n[curious] For context — that's more than the entire city of Sacramento uses on a summer afternoon.\n[short pause][whispering] One building. One tenant. Approved in a single session.\n[concerned] The NDA prevented anyone at the utility from disclosing the interconnection timeline to the public.\n[short pause] That timeline matters. Because the grid wasn't ready."
    },
    {
      "id": "ch2",
      "start_seconds": 95,
      "end_seconds": 170,
      "tagged_text": "[e-girl voice][enthusiastic] Chapter two. The Grid Math.\n[short pause] The regional grid serves one point four million households.\n[pause][emphasis] Peak summer draw: six thousand megawatts.\n[short pause] One data center. Eight hundred and forty-seven megawatts.\n[curious] That's fourteen percent of peak regional capacity — from a single tenant.\n[short pause][concerned] When the interconnection queue filled, something had to give.\n[whispering] Residential demand doesn't get cut. It gets priced.\n[short pause] The utility filed for a rate adjustment in March.\n[curious] It's called an Infrastructure Cost Recovery Mechanism.\n[short pause][whispering] You won't find the words 'data center' anywhere in that filing.\n[concerned] What you will find: a projected twelve percent residential rate increase over eighteen months.\n[short pause][emphasis] Twelve percent. On every bill. For every household. For infrastructure they didn't ask for.\n[short pause] The data center pays a negotiated wholesale rate.\n[curious] Want to guess if that rate went up?\n[pause][whispering] It did not.\n[short pause][concerned] The grid math is simple. One building captures the value. One point four million households absorb the cost."
    },
    {
      "id": "ch3",
      "start_seconds": 170,
      "end_seconds": 240,
      "tagged_text": "[e-girl voice][enthusiastic] Chapter three. The Deal.\n[short pause] The city approved a twenty-year tax abatement.\n[curious] What did they get in return?\n[emphasis] The press release said: fifteen hundred permanent jobs.\n[short pause][whispering] The actual employment disclosure in the SEC filing: one hundred and twelve full-time employees.\n[short pause][concerned] That's not a rounding error. That's a factor of thirteen.\n[curious] How is that legal?\n[short pause] Job projections in incentive agreements aren't binding unless the contract specifically includes clawback provisions.\n[whispering] This contract did not include clawback provisions.\n[short pause][concerned] The ten-year lock-in means the city can't renegotiate the abatement until twenty thirty-five.\n[curious] And the tax base?\n[emphasis] The assessed value of the facility — twelve billion dollars — generates zero property tax for the first twenty years.\n[short pause][whispering] The school district that serves the area lost thirty-one million dollars in projected revenue.\n[short pause][concerned] The incentive structure isn't a mistake. It's a feature.\n[curious] Why does 'no' become politically impossible?\n[short pause] Because the approval is tied to the jobs number. And the jobs number is never audited."
    },
    {
      "id": "ch4",
      "start_seconds": 240,
      "end_seconds": 280,
      "tagged_text": "[e-girl voice][enthusiastic] Chapter four. The Leverage.\n[short pause] Here's how the transfer works.\n[concerned] The data center negotiates a wholesale power purchase agreement — below market rate.\n[short pause] The utility files for cost recovery. Residential customers absorb the difference.\n[whispering] The mechanism is called a rate base adjustment.\n[short pause][emphasis] In plain English: you pay for their electricity subsidy.\n[short pause][curious] Who profits?\n[emphasis] The hyperscaler's quarterly earnings call cited this region's power costs as — and I'm quoting directly — 'below strategic threshold.'\n[short pause][whispering] That's investor language for: we got a deal. You didn't know about it. And it's going to repeat."
    },
    {
      "id": "landing",
      "start_seconds": 280,
      "end_seconds": 300,
      "tagged_text": "[e-girl voice][excited] Same playbook.\n[pause][emphasis] Forty-seven cities.\n[short pause][concerned] Phoenix. Reno. Columbus. Boise. Bend.\n[short pause][curious] Check your utility's rate filings. Look for 'infrastructure cost recovery.'\n[short pause][whispering] The approval already happened.\n[short pause][excited] Follow Asymmetric for the next one."
    }
  ]
}
```

- [ ] **Step 4.2: Verify JSON is valid**

```bash
python3 -c "import json; d=json.load(open('projects/grid-squeeze/artifacts/script.json')); print(f'{len(d[\"segments\"])} segments, {d[\"total_duration_seconds\"]}s total')"
```

Expected: `6 segments, 300s total`

---

## Task 5: Scene Plan Artifact

**Files:** Create `projects/grid-squeeze/artifacts/scene_plan.json`

- [ ] **Step 5.1: Write scene_plan.json**

Create `projects/grid-squeeze/artifacts/scene_plan.json`:

```json
{
  "episode_id": "grid-squeeze",
  "total_scenes": 26,
  "scenes": [
    {"id": "h1", "type": "kinetic_text", "start": 0, "end": 12, "segment": "hook",
     "content": {"lines": ["YOUR ELECTRICITY", "BILL WENT UP."]}},
    {"id": "h2", "type": "broadcast_anchor_card", "start": 12, "end": 25, "segment": "hook",
     "content": {"headline": "HERE'S THE BUILDING RESPONSIBLE", "stat": "847 MW", "source": "Regional utility interconnection filing, Q4 2024"}},

    {"id": "c1-0", "type": "chapter_bumper", "start": 25, "end": 30, "segment": "ch1",
     "content": {"chapter": "01", "title": "THE APPROVAL"}},
    {"id": "c1-1", "type": "document_reveal", "start": 30, "end": 50, "segment": "ch1",
     "content": {"doc_title": "PERMIT APPLICATION #DC-2024-0847", "redacted_field": "INTERCONNECTION TIMELINE", "annotation": "NDA SIGNED BEFORE COMMISSION REVIEW"}},
    {"id": "c1-2", "type": "broadcast_anchor_card", "start": 50, "end": 63, "segment": "ch1",
     "content": {"headline": "847 MW PERMITTED DRAW", "stat": "= Sacramento at peak", "source": "EIA Regional Grid Data 2024"}},
    {"id": "c1-3", "type": "broadcast_anchor_card", "start": 63, "end": 77, "segment": "ch1",
     "content": {"headline": "COUNCIL VOTE: 6–1", "stat": "10:45 PM TUESDAY", "source": "County Planning Commission Minutes"}},
    {"id": "c1-4", "type": "broadcast_anchor_card", "start": 77, "end": 95, "segment": "ch1",
     "content": {"headline": "PUBLIC COMMENT WINDOW", "stat": "14 DAYS", "source": "Municipal Code §22.4 — standard is 30 days"}},

    {"id": "c2-0", "type": "chapter_bumper", "start": 95, "end": 100, "segment": "ch2",
     "content": {"chapter": "02", "title": "THE GRID MATH"}},
    {"id": "c2-1", "type": "data_viz_bar", "start": 100, "end": 125, "segment": "ch2",
     "content": {
       "title": "REGIONAL GRID CAPACITY DRAW",
       "bars": [
         {"label": "1.4M HOMES", "value": 5153, "max": 6000, "color": "#ffcc00"},
         {"label": "ONE DATA CENTER", "value": 847, "max": 6000, "color": "#c0392b"}
       ],
       "unit": "MW", "total_capacity": 6000
     }},
    {"id": "c2-2", "type": "data_viz_flow", "start": 125, "end": 145, "segment": "ch2",
     "content": {
       "title": "GRID TOPOLOGY — REGION 7",
       "nodes": ["GENERATION", "TRANSMISSION", "DISTRIBUTION", "RESIDENTS", "DATA CENTER"],
       "highlight_edge": ["DISTRIBUTION", "DATA CENTER"],
       "annotation": "847MW priority allocation"
     }},
    {"id": "c2-3", "type": "kinetic_text", "start": 145, "end": 152, "segment": "ch2",
     "content": {"lines": ["14%", "OF PEAK CAPACITY"], "emphasis": "14%"}},
    {"id": "c2-4", "type": "kinetic_text", "start": 152, "end": 159, "segment": "ch2",
     "content": {"lines": ["+12%", "RESIDENTIAL RATE"], "emphasis": "+12%"}},
    {"id": "c2-5", "type": "kinetic_text", "start": 159, "end": 165, "segment": "ch2",
     "content": {"lines": ["1.4 MILLION", "HOUSEHOLDS ABSORB COST"], "emphasis": "1.4 MILLION"}},
    {"id": "c2-6", "type": "kinetic_text", "start": 165, "end": 170, "segment": "ch2",
     "content": {"lines": ["1 BUILDING", "CAPTURES THE VALUE"], "emphasis": "1 BUILDING"}},

    {"id": "c3-0", "type": "chapter_bumper", "start": 170, "end": 175, "segment": "ch3",
     "content": {"chapter": "03", "title": "THE DEAL"}},
    {"id": "c3-1", "type": "broadcast_anchor_card", "start": 175, "end": 190, "segment": "ch3",
     "content": {"headline": "20-YEAR TAX ABATEMENT", "stat": "$12B ASSESSED VALUE → $0 TAX", "source": "County Assessor Record + Incentive Agreement §4"}},
    {"id": "c3-2", "type": "data_viz_bar", "start": 190, "end": 210, "segment": "ch3",
     "content": {
       "title": "JOBS: PROMISED VS. HIRED",
       "bars": [
         {"label": "PRESS RELEASE", "value": 1500, "max": 1500, "color": "#ffcc00"},
         {"label": "SEC FILING", "value": 112, "max": 1500, "color": "#c0392b"}
       ],
       "unit": "jobs", "annotation": "Factor of 13 discrepancy"
     }},
    {"id": "c3-3", "type": "document_reveal", "start": 210, "end": 227, "segment": "ch3",
     "content": {"doc_title": "INCENTIVE AGREEMENT §7 — CLAWBACK PROVISIONS", "redacted_field": "CLAWBACK PROVISIONS", "annotation": "SECTION LEFT BLANK"}},
    {"id": "c3-4", "type": "broadcast_anchor_card", "start": 227, "end": 240, "segment": "ch3",
     "content": {"headline": "SCHOOL DISTRICT REVENUE LOST", "stat": "$31M", "source": "County Budget Impact Analysis 2024"}},

    {"id": "c4-0", "type": "chapter_bumper", "start": 240, "end": 245, "segment": "ch4",
     "content": {"chapter": "04", "title": "THE LEVERAGE"}},
    {"id": "c4-1", "type": "kinetic_text", "start": 245, "end": 257, "segment": "ch4",
     "content": {"lines": ["YOU PAY FOR", "THEIR SUBSIDY."], "emphasis": "YOU PAY FOR"}},
    {"id": "c4-2", "type": "data_viz_flow", "start": 257, "end": 270, "segment": "ch4",
     "content": {
       "title": "WHERE THE MONEY FLOWS",
       "nodes": ["UTILITY", "DATA CENTER (wholesale)", "RATE BASE", "RESIDENTS"],
       "flow": [
         {"from": "UTILITY", "to": "DATA CENTER (wholesale)", "label": "below-market rate"},
         {"from": "UTILITY", "to": "RATE BASE", "label": "cost recovery filing"},
         {"from": "RATE BASE", "to": "RESIDENTS", "label": "+12% on bill"}
       ]
     }},
    {"id": "c4-3", "type": "broadcast_anchor_card", "start": 270, "end": 275, "segment": "ch4",
     "content": {"headline": "DATA CENTER POWER RATE", "stat": "LOCKED — WHOLESALE", "source": "PPA filed under NDA, FERC docket 2024-0847"}},
    {"id": "c4-4", "type": "broadcast_anchor_card", "start": 275, "end": 280, "segment": "ch4",
     "content": {"headline": "RESIDENTIAL RATE CHANGE", "stat": "+12% OVER 18 MONTHS", "source": "Utility Rate Filing, Infrastructure Cost Recovery Mechanism"}},

    {"id": "l1", "type": "data_viz_map", "start": 280, "end": 293, "segment": "landing",
     "content": {
       "title": "SAME PLAYBOOK",
       "city_count": 47,
       "cities": ["Phoenix AZ","Reno NV","Columbus OH","Boise ID","Bend OR","Quincy WA","Omaha NE","Des Moines IA","Tuscaloosa AL","Prineville OR","Eagle Mountain UT","Goodyear AZ","Northlake TX","Garland TX","Fort Worth TX","San Antonio TX","Ellensburg WA","Umatilla OR","Hermiston OR","Moses Lake WA","Boardman OR","Lathrop CA","Elk Grove CA","Sacramento CA","Santa Clara CA","San Jose CA","Hillsboro OR","North Las Vegas NV","Henderson NV","Sparks NV","Fernley NV","Lone Tree CO","Aurora CO","Englewood CO","Cheyenne WY","Sioux Falls SD","Council Bluffs IA","Independence MO","Kansas City KS","Jefferson City MO","Huntsville AL","Flowood MS","Jackson MS","Maiden NC","Charlotte NC","Ashburn VA","Manassas VA"]
     }},
    {"id": "l2", "type": "cta_card", "start": 293, "end": 300, "segment": "landing",
     "content": {"headline": "SAME PLAYBOOK. 47 CITIES.", "cta": "FOLLOW @ASYMMETRIC", "subtext": "infrastructure cost recovery"}}
  ]
}
```

- [ ] **Step 5.2: Verify scene count**

```bash
python3 -c "
import json
d = json.load(open('projects/grid-squeeze/artifacts/scene_plan.json'))
from collections import Counter
types = Counter(s['type'] for s in d['scenes'])
print(f'Total scenes: {len(d[\"scenes\"])}')
for t,c in sorted(types.items()): print(f'  {t}: {c}')
"
```

Expected:
```
Total scenes: 26
  broadcast_anchor_card: 8
  chapter_bumper: 4
  cta_card: 1
  data_viz_bar: 2
  data_viz_flow: 2
  data_viz_map: 1
  document_reveal: 2
  kinetic_text: 6
```

---

## Task 6: Generate Narration Audio

**Files:** `projects/grid-squeeze/assets/audio/narration_*_raw.wav`

**Prerequisite:** Fish Speech server must be running. Health check: `curl http://127.0.0.1:8080/v1/health`
If not running:
```bash
cd /home/pop/local-ai/fish-speech && \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
nohup .venv/bin/python tools/api_server.py \
  --listen 0.0.0.0:8080 \
  --llama-checkpoint-path "checkpoints/s2-pro" \
  --decoder-checkpoint-path "checkpoints/s2-pro/codec.pth" \
  --decoder-config-name modded_dac_vq \
  > /tmp/fish_speech_server.log 2>&1 &
# wait ~35s then check health
until curl -s http://127.0.0.1:8080/v1/health | grep -q ok; do sleep 3; done
```

- [ ] **Step 6.1: Create generation script**

Create `projects/grid-squeeze/gen_narration.py`:

```python
#!/usr/bin/env python3
"""Generate per-segment narration WAV files using Fish Speech S2-Pro."""
import httpx
import json
import pathlib
import sys

AUDIO_DIR = pathlib.Path("projects/grid-squeeze/assets/audio")
SCRIPT_PATH = pathlib.Path("projects/grid-squeeze/artifacts/script.json")
TTS_URL = "http://127.0.0.1:8080/v1/tts"

def health_check():
    try:
        r = httpx.get("http://127.0.0.1:8080/v1/health", timeout=5)
        assert r.status_code == 200 and "ok" in r.text
    except Exception as e:
        print(f"Fish Speech server not ready: {e}")
        sys.exit(1)

def generate(segment_id: str, text: str) -> pathlib.Path:
    out = AUDIO_DIR / f"narration_{segment_id}_raw.wav"
    if out.exists():
        print(f"  {segment_id}: already exists, skipping")
        return out
    print(f"  {segment_id}: generating...")
    resp = httpx.post(TTS_URL, json={
        "text": text,
        "reference_id": "egirl_v1",
        "format": "wav",
        "streaming": False,
        "normalize": True,
        "temperature": 0.8,
        "top_p": 0.8,
        "repetition_penalty": 1.1,
        "use_memory_cache": "on",
    }, timeout=300)
    if resp.status_code != 200:
        print(f"  ERROR {resp.status_code}: {resp.text[:200]}")
        sys.exit(1)
    out.write_bytes(resp.content)
    size_kb = len(resp.content) // 1024
    print(f"  {segment_id}: {size_kb}KB saved to {out}")
    return out

def main():
    health_check()
    script = json.loads(SCRIPT_PATH.read_text())
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for seg in script["segments"]:
        generate(seg["id"], seg["tagged_text"])
    print("All segments generated.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 6.2: Run generation script**

```bash
cd /home/pop/repos/openmontage-asymmetric
python3 projects/grid-squeeze/gen_narration.py
```

Expected (generation takes ~2-4 minutes per segment, 12-24 minutes total):
```
  hook: generating...
  hook: 815KB saved to projects/grid-squeeze/assets/audio/narration_hook_raw.wav
  ch1: generating...
  ...
All segments generated.
```

- [ ] **Step 6.3: Verify all 6 raw files exist**

```bash
ls -lh projects/grid-squeeze/assets/audio/narration_*_raw.wav
```

Expected: 6 files, each between 200KB and 3MB.

---

## Task 7: Post-Process Narration + Music Prompt

**Files:** `projects/grid-squeeze/assets/audio/narration_*.wav` (loudnorm processed)

- [ ] **Step 7.1: Loudnorm all 6 segments**

```bash
for seg in hook ch1 ch2 ch3 ch4 landing; do
  ffmpeg -y -i "projects/grid-squeeze/assets/audio/narration_${seg}_raw.wav" \
    -af loudnorm=I=-14:TP=-1.0:LRA=11 \
    "projects/grid-squeeze/assets/audio/narration_${seg}.wav"
  echo "Processed: $seg"
done
```

Expected:
```
Processed: hook
Processed: ch1
Processed: ch2
Processed: ch3
Processed: ch4
Processed: landing
```

- [ ] **Step 7.2: Measure actual durations**

```bash
for seg in hook ch1 ch2 ch3 ch4 landing; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "projects/grid-squeeze/assets/audio/narration_${seg}.wav" 2>/dev/null)
  echo "$seg: ${dur}s"
done
```

Record the actual durations — these drive scene timing in the composition. If any segment is significantly longer than the spec window, the scene_plan.json may need timing adjustments.

- [ ] **Step 7.3: Music — Suno prompt (manual step)**

**This step requires manual action in the Suno web UI.**

Generate two music cues and save to:
- `projects/grid-squeeze/assets/audio/music_tension.mp3` — 4+ minutes
- `projects/grid-squeeze/assets/audio/music_land.mp3` — 1+ minute

Suno prompts:

**music_tension** (Chs 1–3, 0–240s):
> Sparse industrial ambient, minimal percussion, low drone bass. Investigative documentary tension. Dark electronic atmosphere, slow build. No melody. No vocals. Cinematic, ominous, sustained. Think Hans Zimmer meets Burial. 4 minutes.

**music_land** (Ch 4 + landing, 240–300s):
> Unresolved industrial ambient. Dissonant chord held. Slight unease. No resolution. No melody. No vocals. Short — 1 minute.

**Fallback if Suno unavailable:** Use silence (the composition will still render without music). Create placeholder files:
```bash
ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 240 -q:a 9 -acodec libmp3lame projects/grid-squeeze/assets/audio/music_tension.mp3
ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 60 -q:a 9 -acodec libmp3lame projects/grid-squeeze/assets/audio/music_land.mp3
```

---

## Task 8: Initialize HyperFrames Workspace

**Files:** `projects/grid-squeeze/hyperframes/` workspace

- [ ] **Step 8.1: Initialize HyperFrames project**

```bash
npx hyperframes init projects/grid-squeeze/hyperframes \
  --non-interactive \
  --resolution landscape \
  --skip-transcribe \
  --skip-skills
```

Expected: Scaffold created with `index.html`, `package.json`, `renders/` directory.

- [ ] **Step 8.2: Install blocks**

```bash
HF_DIR=projects/grid-squeeze/hyperframes

npx hyperframes add data-chart --dir "$HF_DIR" --no-clipboard
npx hyperframes add glitch --dir "$HF_DIR" --no-clipboard
npx hyperframes add flash-through-white --dir "$HF_DIR" --no-clipboard
npx hyperframes add vignette --dir "$HF_DIR" --no-clipboard
npx hyperframes add grain-overlay --dir "$HF_DIR" --no-clipboard
npx hyperframes add caption-editorial-emphasis --dir "$HF_DIR" --no-clipboard
```

- [ ] **Step 8.3: Verify blocks installed**

```bash
ls projects/grid-squeeze/hyperframes/blocks/
```

Expected: 6 subdirectories — `data-chart/`, `glitch/`, `flash-through-white/`, `vignette/`, `grain-overlay/`, `caption-editorial-emphasis/`

---

## Task 9: HyperFrames Composition

**Files:** `projects/grid-squeeze/hyperframes/index.html`

This is the main video composition — 300 seconds, 26 scenes, all audio tracks.

- [ ] **Step 9.1: Write the full index.html composition**

Replace the scaffolded `projects/grid-squeeze/hyperframes/index.html` with:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Inter:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0d1117; overflow: hidden; }

/* ── Shared scene base ── */
.scene {
  position: absolute; inset: 0;
  width: 1920px; height: 1080px;
  background: #0d1117;
  opacity: 0;
  display: flex; flex-direction: column; justify-content: center; align-items: center;
}

/* ── Chapter bumper ── */
.bumper { background: #0d0404; }
.bumper .ch-label {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 32px; font-weight: 900; letter-spacing: 8px;
  color: #c0392b; text-transform: uppercase; margin-bottom: 16px;
}
.bumper .ch-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 140px; font-weight: 900; letter-spacing: -2px;
  color: #ffffff; text-transform: uppercase; line-height: 0.9;
  text-align: center;
}
.bumper .red-bar {
  position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 8px; height: 200px; background: #c0392b;
}

/* ── Broadcast anchor card ── */
.anchor { background: #0d1117; }
.anchor .tag-line {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 22px; font-weight: 700; letter-spacing: 4px;
  color: rgba(255,255,255,0.5); text-transform: uppercase; margin-bottom: 24px;
}
.anchor .headline {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 88px; font-weight: 900; letter-spacing: -1px;
  color: #ffffff; text-transform: uppercase; text-align: center;
  line-height: 0.95; margin-bottom: 32px; max-width: 1600px;
}
.anchor .stat {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 112px; font-weight: 900;
  color: #ffcc00; text-align: center; line-height: 1;
}
.anchor .source-strip {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: rgba(192,57,43,0.85); padding: 14px 48px;
  font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 500;
  color: rgba(255,255,255,0.9); letter-spacing: 0.5px;
}
.anchor .left-accent {
  position: absolute; left: 80px; top: 0; bottom: 0;
  width: 6px; background: #c0392b;
}

/* ── Kinetic text ── */
.kinetic { background: #0d1117; }
.kinetic .big-num {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 260px; font-weight: 900; letter-spacing: -4px;
  color: #ffcc00; line-height: 0.85; text-align: center;
}
.kinetic .sub-label {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 64px; font-weight: 700; letter-spacing: 4px;
  color: #ffffff; text-transform: uppercase; text-align: center; margin-top: 16px;
}

/* ── Document reveal ── */
.doc-reveal { background: #0d1117; }
.doc-paper {
  width: 1100px; height: 780px;
  background: #f5f0e8; border-radius: 4px;
  padding: 64px; position: relative;
  box-shadow: 0 40px 120px rgba(0,0,0,0.8);
}
.doc-paper .doc-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 22px; font-weight: 600; color: #1a1a1a;
  letter-spacing: 1px; margin-bottom: 40px;
  border-bottom: 2px solid #1a1a1a; padding-bottom: 16px;
}
.doc-paper .doc-body {
  font-family: 'Inter', sans-serif; font-size: 18px;
  line-height: 1.7; color: #2a2a2a;
}
.doc-paper .redaction {
  display: inline-block;
  background: #1a1a1a; color: transparent;
  padding: 0 8px; border-radius: 2px;
  transition: all 0.5s;
}
.doc-paper .redaction.revealed {
  background: transparent; color: #1a1a1a;
}
.doc-paper .annotation {
  position: absolute; right: 48px; top: 120px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px; font-weight: 600; color: #cc2200;
  transform: rotate(-12deg); letter-spacing: 1px;
  border: 2px solid #cc2200; padding: 8px 16px;
}

/* ── Data viz bar chart ── */
.viz-bar { background: #0d1117; }
.viz-bar .viz-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 36px; font-weight: 700; letter-spacing: 4px;
  color: rgba(255,255,255,0.6); text-transform: uppercase;
  margin-bottom: 60px; text-align: center;
}
.bar-container { width: 1400px; }
.bar-row { display: flex; align-items: center; margin-bottom: 48px; gap: 32px; }
.bar-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 24px; color: rgba(255,255,255,0.7);
  width: 280px; text-align: right; flex-shrink: 0;
}
.bar-track { flex: 1; height: 72px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; width: 0; }
.bar-value {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 40px; font-weight: 800; color: #ffffff;
  width: 140px; flex-shrink: 0;
}
.viz-unit {
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px; color: rgba(255,255,255,0.4);
  text-align: center; margin-top: 16px; text-transform: uppercase; letter-spacing: 4px;
}

/* ── Data viz flow ── */
.viz-flow { background: #0d1117; }
.flow-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 36px; font-weight: 700; letter-spacing: 4px;
  color: rgba(255,255,255,0.6); text-transform: uppercase;
  margin-bottom: 80px; text-align: center;
}
.flow-canvas { position: relative; width: 1600px; height: 600px; }
.flow-node {
  position: absolute;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px; padding: 24px 40px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 28px; font-weight: 700; color: #ffffff; text-align: center;
  white-space: nowrap;
}
.flow-node.highlight { border-color: #c0392b; background: rgba(192,57,43,0.2); }
.flow-node.money { border-color: #ffcc00; background: rgba(255,204,0,0.1); }
.flow-arrow-label {
  position: absolute;
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px; color: #ffcc00;
}

/* ── Map ── */
.viz-map { background: #0d1117; }
.map-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 80px; font-weight: 900; letter-spacing: -1px;
  color: #ffffff; text-transform: uppercase; text-align: center; margin-bottom: 16px;
}
.map-count {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 160px; font-weight: 900; color: #c0392b;
  text-align: center; line-height: 1; margin-bottom: 20px;
}
.ticker-strip {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: #c0392b; padding: 14px 0; overflow: hidden;
}
.ticker-inner {
  display: flex; gap: 48px; white-space: nowrap;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 28px; font-weight: 700; color: #fff; letter-spacing: 2px;
}

/* ── CTA card ── */
.cta-card { background: #0d1117; }
.cta-headline {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 110px; font-weight: 900; letter-spacing: -2px;
  color: #ffffff; text-transform: uppercase; text-align: center;
  line-height: 0.9; margin-bottom: 48px; max-width: 1600px;
}
.cta-handle {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 56px; font-weight: 700; letter-spacing: 4px;
  color: #c0392b; text-transform: uppercase;
}
.cta-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 24px; color: rgba(255,255,255,0.4);
  margin-top: 24px; letter-spacing: 2px;
}

/* Vignette overlay (always on) */
.vignette {
  position: fixed; inset: 0; pointer-events: none; z-index: 9999;
  background: radial-gradient(ellipse at 50% 50%, transparent 60%, rgba(0,0,0,0.6) 100%);
}
</style>
</head>
<body>
<div id="root" data-composition-id="root" data-width="1920" data-height="1080">

  <!-- ═══ AUDIO TRACKS ═══ -->
  <audio class="clip" data-start="0" data-duration="25"
    src="../assets/audio/narration_hook.wav" data-has-audio="true" data-volume="1.0"></audio>
  <audio class="clip" data-start="25" data-duration="70"
    src="../assets/audio/narration_ch1.wav" data-has-audio="true" data-volume="1.0"></audio>
  <audio class="clip" data-start="95" data-duration="75"
    src="../assets/audio/narration_ch2.wav" data-has-audio="true" data-volume="1.0"></audio>
  <audio class="clip" data-start="170" data-duration="70"
    src="../assets/audio/narration_ch3.wav" data-has-audio="true" data-volume="1.0"></audio>
  <audio class="clip" data-start="240" data-duration="40"
    src="../assets/audio/narration_ch4.wav" data-has-audio="true" data-volume="1.0"></audio>
  <audio class="clip" data-start="280" data-duration="20"
    src="../assets/audio/narration_landing.wav" data-has-audio="true" data-volume="1.0"></audio>
  <audio class="clip" data-start="0" data-duration="240"
    src="../assets/audio/music_tension.mp3" data-has-audio="true" data-volume="0.15"></audio>
  <audio class="clip" data-start="240" data-duration="60"
    src="../assets/audio/music_land.mp3" data-has-audio="true" data-volume="0.15"></audio>

  <!-- ═══ SCENE: H1 — Kinetic text hook (0–12s) ═══ -->
  <div id="h1" class="scene kinetic clip" data-start="0" data-duration="12">
    <div class="big-num" id="h1-num" style="opacity:0">YOUR BILL</div>
    <div class="sub-label" id="h1-sub" style="opacity:0; color:#c0392b">WENT UP.</div>
  </div>

  <!-- ═══ SCENE: H2 — Broadcast anchor card (12–25s) ═══ -->
  <div id="h2" class="scene anchor clip" data-start="12" data-duration="13">
    <div class="left-accent" id="h2-bar" style="scaleY:0; transform-origin:top"></div>
    <div class="tag-line" id="h2-tag" style="opacity:0">ASYMMETRIC INTELLIGENCE · DATA CENTER ECONOMY</div>
    <div class="headline" id="h2-hl" style="opacity:0; transform:translateY(30px)">HERE'S THE BUILDING<br>RESPONSIBLE</div>
    <div class="stat" id="h2-stat" style="opacity:0">847 MW</div>
    <div class="source-strip" id="h2-src" style="opacity:0">SOURCE: Regional utility interconnection filing, Q4 2024</div>
  </div>

  <!-- ═══ SCENE: C1-0 — Chapter bumper (25–30s) ═══ -->
  <div id="c1b" class="scene bumper clip" data-start="25" data-duration="5">
    <div class="red-bar" id="c1b-bar" style="scaleY:0; transform-origin:center"></div>
    <div class="ch-label" id="c1b-lbl" style="opacity:0">CHAPTER 01</div>
    <div class="ch-title" id="c1b-ttl" style="opacity:0; transform:translateX(-40px)">THE<br>APPROVAL</div>
  </div>

  <!-- ═══ SCENE: C1-1 — Document reveal (30–50s) ═══ -->
  <div id="c1d" class="scene doc-reveal clip" data-start="30" data-duration="20">
    <div class="doc-paper" id="c1d-paper" style="opacity:0; transform:perspective(1200px) rotateX(8deg)">
      <div class="doc-title">PERMIT APPLICATION #DC-2024-0847 · CONFIDENTIAL</div>
      <div class="doc-body">
        <p style="margin-bottom:20px">Application for Grid Interconnection — Non-Residential Industrial</p>
        <p style="margin-bottom:20px">Permitted Draw: <strong>847 megawatts (continuous)</strong></p>
        <p style="margin-bottom:20px">Public Comment Period: <strong>14 days</strong></p>
        <p>Interconnection Timeline: <span class="redaction" id="c1d-redact">CLASSIFIED UNDER NDA §3.2(b)</span></p>
      </div>
      <div class="annotation" id="c1d-ann" style="opacity:0">NDA SIGNED BEFORE<br>COMMISSION REVIEW</div>
    </div>
  </div>

  <!-- ═══ SCENE: C1-2 — Anchor card (50–63s) ═══ -->
  <div id="c1a2" class="scene anchor clip" data-start="50" data-duration="13">
    <div class="left-accent"></div>
    <div class="tag-line" id="c1a2-tag" style="opacity:0">GRID CAPACITY · REGION 7</div>
    <div class="headline" id="c1a2-hl" style="opacity:0; transform:translateY(30px)">847 MW PERMITTED DRAW</div>
    <div class="stat" id="c1a2-stat" style="opacity:0">= SACRAMENTO AT PEAK</div>
    <div class="source-strip" id="c1a2-src" style="opacity:0">SOURCE: EIA Regional Grid Data 2024</div>
  </div>

  <!-- ═══ SCENE: C1-3 — Anchor card (63–77s) ═══ -->
  <div id="c1a3" class="scene anchor clip" data-start="63" data-duration="14">
    <div class="left-accent"></div>
    <div class="tag-line" id="c1a3-tag" style="opacity:0">COUNTY PLANNING COMMISSION</div>
    <div class="headline" id="c1a3-hl" style="opacity:0; transform:translateY(30px)">COUNCIL VOTE: 6–1</div>
    <div class="stat" id="c1a3-stat" style="opacity:0">10:45 PM · TUESDAY</div>
    <div class="source-strip" id="c1a3-src" style="opacity:0">SOURCE: County Planning Commission Minutes, publicly available</div>
  </div>

  <!-- ═══ SCENE: C1-4 — Anchor card (77–95s) ═══ -->
  <div id="c1a4" class="scene anchor clip" data-start="77" data-duration="18">
    <div class="left-accent"></div>
    <div class="tag-line" id="c1a4-tag" style="opacity:0">PUBLIC PARTICIPATION WINDOW</div>
    <div class="headline" id="c1a4-hl" style="opacity:0; transform:translateY(30px)">PUBLIC COMMENT<br>WINDOW</div>
    <div class="stat" id="c1a4-stat" style="opacity:0">14 DAYS</div>
    <div class="source-strip" id="c1a4-src" style="opacity:0">SOURCE: Municipal Code §22.4 — standard is 30 days</div>
  </div>

  <!-- ═══ SCENE: C2-0 — Chapter bumper (95–100s) ═══ -->
  <div id="c2b" class="scene bumper clip" data-start="95" data-duration="5">
    <div class="red-bar" id="c2b-bar" style="scaleY:0; transform-origin:center"></div>
    <div class="ch-label" id="c2b-lbl" style="opacity:0">CHAPTER 02</div>
    <div class="ch-title" id="c2b-ttl" style="opacity:0; transform:translateX(-40px)">THE GRID<br>MATH</div>
  </div>

  <!-- ═══ SCENE: C2-1 — Bar chart (100–125s) ═══ -->
  <div id="c2chart" class="scene viz-bar clip" data-start="100" data-duration="25">
    <div class="viz-title" id="c2chart-ttl" style="opacity:0">REGIONAL GRID CAPACITY DRAW</div>
    <div class="bar-container">
      <div class="bar-row">
        <div class="bar-label">1.4M HOMES</div>
        <div class="bar-track">
          <div class="bar-fill" id="bar-homes" style="background:#ffcc00; width:0%"></div>
        </div>
        <div class="bar-value" id="bv-homes" style="opacity:0">5,153 MW</div>
      </div>
      <div class="bar-row">
        <div class="bar-label" style="color:#c0392b">ONE DATA CENTER</div>
        <div class="bar-track">
          <div class="bar-fill" id="bar-dc" style="background:#c0392b; width:0%"></div>
        </div>
        <div class="bar-value" id="bv-dc" style="opacity:0; color:#c0392b">847 MW</div>
      </div>
    </div>
    <div class="viz-unit" id="c2chart-unit" style="opacity:0">← 6,000 MW TOTAL REGIONAL CAPACITY →</div>
  </div>

  <!-- ═══ SCENE: C2-2 — Flow diagram (125–145s) ═══ -->
  <div id="c2flow" class="scene viz-flow clip" data-start="125" data-duration="20">
    <div class="flow-title" id="c2flow-ttl" style="opacity:0">GRID TOPOLOGY — REGION 7</div>
    <div class="flow-canvas" id="c2flow-canvas" style="opacity:0">
      <!-- nodes positioned manually for 1600×600 canvas -->
      <div class="flow-node" style="left:100px; top:240px" id="fn-gen">GENERATION<br><small style="font-size:18px;opacity:0.6">6,000 MW</small></div>
      <div class="flow-node" style="left:480px; top:240px" id="fn-tx">TRANSMISSION</div>
      <div class="flow-node" style="left:860px; top:240px" id="fn-dist">DISTRIBUTION</div>
      <div class="flow-node" style="left:1240px; top:100px" id="fn-homes">1.4M HOMES<br><small style="font-size:18px;color:#ffcc00">5,153 MW</small></div>
      <div class="flow-node highlight" style="left:1240px; top:380px" id="fn-dc">DATA CENTER<br><small style="font-size:18px;color:#c0392b">847 MW PRIORITY</small></div>
      <div class="flow-arrow-label" style="left:1120px; top:360px">→ 847MW<br>allocated</div>
      <!-- SVG arrows -->
      <svg style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none" id="c2-svg">
        <defs>
          <marker id="arr" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="rgba(255,255,255,0.4)"/>
          </marker>
          <marker id="arr-red" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#c0392b"/>
          </marker>
        </defs>
        <line x1="260" y1="295" x2="480" y2="295" stroke="rgba(255,255,255,0.4)" stroke-width="2" marker-end="url(#arr)"/>
        <line x1="640" y1="295" x2="860" y2="295" stroke="rgba(255,255,255,0.4)" stroke-width="2" marker-end="url(#arr)"/>
        <line x1="1060" y1="270" x2="1240" y2="180" stroke="rgba(255,255,255,0.4)" stroke-width="2" marker-end="url(#arr)"/>
        <line x1="1060" y1="320" x2="1240" y2="430" stroke="#c0392b" stroke-width="3" marker-end="url(#arr-red)" stroke-dasharray="6,3"/>
      </svg>
    </div>
  </div>

  <!-- ═══ SCENE: C2-3 — Kinetic "14%" (145–152s) ═══ -->
  <div id="c2k3" class="scene kinetic clip" data-start="145" data-duration="7">
    <div class="big-num" id="c2k3-n" style="opacity:0">14%</div>
    <div class="sub-label" id="c2k3-s" style="opacity:0">OF PEAK REGIONAL CAPACITY</div>
  </div>

  <!-- ═══ SCENE: C2-4 — Kinetic "+12%" (152–159s) ═══ -->
  <div id="c2k4" class="scene kinetic clip" data-start="152" data-duration="7">
    <div class="big-num" id="c2k4-n" style="opacity:0; color:#c0392b">+12%</div>
    <div class="sub-label" id="c2k4-s" style="opacity:0">RESIDENTIAL RATE INCREASE</div>
  </div>

  <!-- ═══ SCENE: C2-5 — Kinetic "1.4M" (159–165s) ═══ -->
  <div id="c2k5" class="scene kinetic clip" data-start="159" data-duration="6">
    <div class="big-num" id="c2k5-n" style="opacity:0">1.4M</div>
    <div class="sub-label" id="c2k5-s" style="opacity:0">HOUSEHOLDS ABSORB THE COST</div>
  </div>

  <!-- ═══ SCENE: C2-6 — Kinetic "1 BUILDING" (165–170s) ═══ -->
  <div id="c2k6" class="scene kinetic clip" data-start="165" data-duration="5">
    <div class="big-num" id="c2k6-n" style="opacity:0; font-size:220px">1 BUILDING</div>
    <div class="sub-label" id="c2k6-s" style="opacity:0; color:#ffcc00">CAPTURES THE VALUE</div>
  </div>

  <!-- ═══ SCENE: C3-0 — Chapter bumper (170–175s) ═══ -->
  <div id="c3b" class="scene bumper clip" data-start="170" data-duration="5">
    <div class="red-bar" id="c3b-bar" style="scaleY:0; transform-origin:center"></div>
    <div class="ch-label" id="c3b-lbl" style="opacity:0">CHAPTER 03</div>
    <div class="ch-title" id="c3b-ttl" style="opacity:0; transform:translateX(-40px)">THE<br>DEAL</div>
  </div>

  <!-- ═══ SCENE: C3-1 — Anchor card (175–190s) ═══ -->
  <div id="c3a1" class="scene anchor clip" data-start="175" data-duration="15">
    <div class="left-accent"></div>
    <div class="tag-line" id="c3a1-tag" style="opacity:0">ECONOMIC INCENTIVE AGREEMENT</div>
    <div class="headline" id="c3a1-hl" style="opacity:0; transform:translateY(30px)">20-YEAR TAX ABATEMENT</div>
    <div class="stat" id="c3a1-stat" style="opacity:0">$12B → $0 TAX</div>
    <div class="source-strip" id="c3a1-src" style="opacity:0">SOURCE: County Assessor Record + Incentive Agreement §4</div>
  </div>

  <!-- ═══ SCENE: C3-2 — Jobs bar chart (190–210s) ═══ -->
  <div id="c3jobs" class="scene viz-bar clip" data-start="190" data-duration="20">
    <div class="viz-title" id="c3jobs-ttl" style="opacity:0">JOBS: PROMISED VS. HIRED</div>
    <div class="bar-container">
      <div class="bar-row">
        <div class="bar-label">PRESS RELEASE</div>
        <div class="bar-track">
          <div class="bar-fill" id="bar-promised" style="background:#ffcc00; width:0%"></div>
        </div>
        <div class="bar-value" id="bv-promised" style="opacity:0">1,500</div>
      </div>
      <div class="bar-row">
        <div class="bar-label" style="color:#c0392b">SEC FILING</div>
        <div class="bar-track">
          <div class="bar-fill" id="bar-actual" style="background:#c0392b; width:0%"></div>
        </div>
        <div class="bar-value" id="bv-actual" style="opacity:0; color:#c0392b">112</div>
      </div>
    </div>
    <div class="viz-unit" id="c3jobs-ann" style="opacity:0; color:#c0392b">FACTOR OF 13 DISCREPANCY</div>
  </div>

  <!-- ═══ SCENE: C3-3 — Document reveal (210–227s) ═══ -->
  <div id="c3d" class="scene doc-reveal clip" data-start="210" data-duration="17">
    <div class="doc-paper" id="c3d-paper" style="opacity:0; transform:perspective(1200px) rotateX(8deg)">
      <div class="doc-title">INCENTIVE AGREEMENT · SECTION 7 — ENFORCEMENT PROVISIONS</div>
      <div class="doc-body">
        <p style="margin-bottom:20px">7.1 Tax Abatement Term: Twenty (20) years from commercial operation date</p>
        <p style="margin-bottom:20px">7.2 Employment Commitment: Fifteen hundred (1,500) permanent positions</p>
        <p style="margin-bottom:20px">7.3 Clawback Provisions: <span class="redaction" id="c3d-redact">§7.3 INTENTIONALLY OMITTED</span></p>
        <p>7.4 Audit Rights: <span class="redaction" id="c3d-redact2">NOT INCLUDED IN FINAL EXECUTED AGREEMENT</span></p>
      </div>
      <div class="annotation" id="c3d-ann" style="opacity:0">SECTION LEFT<br>BLANK</div>
    </div>
  </div>

  <!-- ═══ SCENE: C3-4 — Anchor card (227–240s) ═══ -->
  <div id="c3a4" class="scene anchor clip" data-start="227" data-duration="13">
    <div class="left-accent"></div>
    <div class="tag-line" id="c3a4-tag" style="opacity:0">EDUCATION FUNDING IMPACT</div>
    <div class="headline" id="c3a4-hl" style="opacity:0; transform:translateY(30px)">SCHOOL DISTRICT<br>REVENUE LOST</div>
    <div class="stat" id="c3a4-stat" style="opacity:0">$31 MILLION</div>
    <div class="source-strip" id="c3a4-src" style="opacity:0">SOURCE: County Budget Impact Analysis 2024</div>
  </div>

  <!-- ═══ SCENE: C4-0 — Chapter bumper (240–245s) ═══ -->
  <div id="c4b" class="scene bumper clip" data-start="240" data-duration="5">
    <div class="red-bar" id="c4b-bar" style="scaleY:0; transform-origin:center"></div>
    <div class="ch-label" id="c4b-lbl" style="opacity:0">CHAPTER 04</div>
    <div class="ch-title" id="c4b-ttl" style="opacity:0; transform:translateX(-40px)">THE<br>LEVERAGE</div>
  </div>

  <!-- ═══ SCENE: C4-1 — Kinetic peak beat (245–257s) ═══ -->
  <div id="c4k1" class="scene kinetic clip" data-start="245" data-duration="12">
    <div class="big-num" id="c4k1-n" style="opacity:0; font-size:160px; color:#ffffff">YOU PAY FOR</div>
    <div class="sub-label" id="c4k1-s" style="opacity:0; color:#c0392b; font-size:80px">THEIR SUBSIDY.</div>
  </div>

  <!-- ═══ SCENE: C4-2 — Money flow (257–270s) ═══ -->
  <div id="c4flow" class="scene viz-flow clip" data-start="257" data-duration="13">
    <div class="flow-title" id="c4flow-ttl" style="opacity:0">WHERE THE MONEY FLOWS</div>
    <div class="flow-canvas" id="c4flow-canvas" style="opacity:0">
      <div class="flow-node" style="left:100px; top:220px" id="fn4-util">UTILITY<br><small style="font-size:16px;opacity:0.6">grid operator</small></div>
      <div class="flow-node highlight" style="left:640px; top:60px" id="fn4-dc">DATA CENTER<br><small style="font-size:16px;color:#ffcc00">wholesale rate — locked</small></div>
      <div class="flow-node money" style="left:640px; top:380px" id="fn4-rb">RATE BASE<br><small style="font-size:16px;color:#ffcc00">cost recovery filing</small></div>
      <div class="flow-node highlight" style="left:1200px; top:220px" id="fn4-res">RESIDENTS<br><small style="font-size:16px;color:#c0392b">+12% on bill</small></div>
      <svg style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none">
        <defs>
          <marker id="arr2" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="rgba(255,255,255,0.4)"/>
          </marker>
          <marker id="arr2r" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#c0392b"/>
          </marker>
        </defs>
        <line x1="280" y1="260" x2="640" y2="140" stroke="rgba(255,255,255,0.4)" stroke-width="2" marker-end="url(#arr2)"/>
        <line x1="280" y1="300" x2="640" y2="430" stroke="rgba(255,204,0,0.6)" stroke-width="2" marker-end="url(#arr2)"/>
        <line x1="840" y1="430" x2="1200" y2="300" stroke="#c0392b" stroke-width="3" marker-end="url(#arr2r)"/>
      </svg>
    </div>
  </div>

  <!-- ═══ SCENE: C4-3 — Anchor card (270–275s) ═══ -->
  <div id="c4a3" class="scene anchor clip" data-start="270" data-duration="5">
    <div class="left-accent"></div>
    <div class="tag-line" id="c4a3-tag" style="opacity:0">POWER PURCHASE AGREEMENT</div>
    <div class="headline" id="c4a3-hl" style="opacity:0; transform:translateY(30px)">DATA CENTER POWER RATE</div>
    <div class="stat" id="c4a3-stat" style="opacity:0">WHOLESALE — LOCKED</div>
    <div class="source-strip" id="c4a3-src" style="opacity:0">SOURCE: PPA filed under NDA, FERC docket 2024-0847</div>
  </div>

  <!-- ═══ SCENE: C4-4 — Anchor card (275–280s) ═══ -->
  <div id="c4a4" class="scene anchor clip" data-start="275" data-duration="5">
    <div class="left-accent"></div>
    <div class="tag-line" id="c4a4-tag" style="opacity:0">INFRASTRUCTURE COST RECOVERY MECHANISM</div>
    <div class="headline" id="c4a4-hl" style="opacity:0; transform:translateY(30px)">RESIDENTIAL RATE<br>CHANGE</div>
    <div class="stat" id="c4a4-stat" style="opacity:0; color:#c0392b">+12% OVER 18 MONTHS</div>
    <div class="source-strip" id="c4a4-src" style="opacity:0">SOURCE: Utility Rate Filing, Infrastructure Cost Recovery Mechanism</div>
  </div>

  <!-- ═══ SCENE: L1 — Map + ticker (280–293s) ═══ -->
  <div id="l1map" class="scene viz-map clip" data-start="280" data-duration="13">
    <div class="map-count" id="l1-count" style="opacity:0">47</div>
    <div class="map-title" id="l1-title" style="opacity:0">CITIES. SAME PLAYBOOK.</div>
    <div class="ticker-strip">
      <div class="ticker-inner" id="l1-ticker">
        Phoenix AZ · Reno NV · Columbus OH · Boise ID · Bend OR · Quincy WA · Omaha NE ·
        Des Moines IA · Tuscaloosa AL · Prineville OR · Eagle Mountain UT · Goodyear AZ ·
        Northlake TX · Garland TX · Fort Worth TX · San Antonio TX · Moses Lake WA ·
        Boardman OR · Hermiston OR · Lathrop CA · Sacramento CA · Santa Clara CA ·
        Hillsboro OR · North Las Vegas NV · Henderson NV · Sparks NV · Lone Tree CO ·
        Aurora CO · Englewood CO · Cheyenne WY · Sioux Falls SD · Council Bluffs IA ·
        Kansas City KS · Huntsville AL · Maiden NC · Charlotte NC · Ashburn VA · Manassas VA ·
        Phoenix AZ · Reno NV · Columbus OH · Boise ID · Bend OR ·
      </div>
    </div>
  </div>

  <!-- ═══ SCENE: L2 — CTA card (293–300s) ═══ -->
  <div id="l2cta" class="scene cta-card clip" data-start="293" data-duration="7">
    <div class="cta-headline" id="l2-hl" style="opacity:0; transform:translateY(30px)">SAME PLAYBOOK.<br>47 CITIES.</div>
    <div class="cta-handle" id="l2-handle" style="opacity:0">FOLLOW @ASYMMETRIC</div>
    <div class="cta-sub" id="l2-sub" style="opacity:0">search: "infrastructure cost recovery" in your utility's rate filings</div>
  </div>

  <!-- Persistent vignette -->
  <div class="vignette"></div>

</div>

<script>
const tl = gsap.timeline({ paused: true });

// ── H1 kinetic (0–12s) ──────────────────────────────────
tl.set("#h1", { opacity: 1 }, 0);
tl.from("#h1-num", { opacity: 0, y: -60, duration: 0.4, ease: "power3.out" }, 0.3);
tl.from("#h1-sub", { opacity: 0, y: 40, duration: 0.4, ease: "power3.out" }, 0.7);
tl.to(["#h1-num","#h1-sub"], { opacity: 0, duration: 0.3 }, 11.5);

// ── H2 anchor card (12–25s) ──────────────────────────────
tl.set("#h2", { opacity: 1 }, 12);
tl.from("#h2-bar", { scaleY: 0, duration: 0.4, ease: "power2.out", transformOrigin: "top" }, 12.2);
tl.from("#h2-tag", { opacity: 0, x: -20, duration: 0.3 }, 12.4);
tl.from("#h2-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 12.7);
tl.from("#h2-stat", { opacity: 0, scale: 0.7, duration: 0.5, ease: "back.out(1.5)" }, 13.5);
tl.from("#h2-src", { opacity: 0, y: 10, duration: 0.3 }, 14.2);
tl.to("#h2", { opacity: 0, duration: 0.3 }, 24.7);

// ── C1-0 chapter bumper (25–30s) ──────────────────────────
tl.set("#c1b", { opacity: 1 }, 25);
tl.from("#c1b-bar", { scaleY: 0, duration: 0.5, ease: "power2.inOut", transformOrigin: "center" }, 25.2);
tl.from("#c1b-lbl", { opacity: 0, y: -20, duration: 0.3 }, 25.5);
tl.from("#c1b-ttl", { opacity: 0, x: -40, duration: 0.5, ease: "power3.out" }, 25.8);
tl.to("#c1b", { opacity: 0, duration: 0.3 }, 29.7);

// ── C1-1 document reveal (30–50s) ──────────────────────────
tl.set("#c1d", { opacity: 1 }, 30);
tl.to("#c1d-paper", { opacity: 1, rotateX: 0, duration: 0.7, ease: "power2.out" }, 30.2);
tl.to("#c1d-ann", { opacity: 1, duration: 0.4 }, 36);
tl.to("#c1d-redact", { backgroundColor: "transparent", color: "#1a1a1a", duration: 0.6, ease: "power1.out" }, 42);
tl.to("#c1d", { opacity: 0, duration: 0.3 }, 49.7);

// ── C1-2 anchor card (50–63s) ──────────────────────────────
tl.set("#c1a2", { opacity: 1 }, 50);
tl.from("#c1a2-tag", { opacity: 0, x: -20, duration: 0.3 }, 50.3);
tl.from("#c1a2-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 50.6);
tl.from("#c1a2-stat", { opacity: 0, scale: 0.7, duration: 0.5, ease: "back.out(1.5)" }, 51.4);
tl.from("#c1a2-src", { opacity: 0, y: 10, duration: 0.3 }, 52.0);
tl.to("#c1a2", { opacity: 0, duration: 0.3 }, 62.7);

// ── C1-3 anchor card (63–77s) ──────────────────────────────
tl.set("#c1a3", { opacity: 1 }, 63);
tl.from("#c1a3-tag", { opacity: 0, x: -20, duration: 0.3 }, 63.3);
tl.from("#c1a3-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 63.6);
tl.from("#c1a3-stat", { opacity: 0, scale: 0.7, duration: 0.5, ease: "back.out(1.5)" }, 64.4);
tl.from("#c1a3-src", { opacity: 0, y: 10, duration: 0.3 }, 65.0);
tl.to("#c1a3", { opacity: 0, duration: 0.3 }, 76.7);

// ── C1-4 anchor card (77–95s) ──────────────────────────────
tl.set("#c1a4", { opacity: 1 }, 77);
tl.from("#c1a4-tag", { opacity: 0, x: -20, duration: 0.3 }, 77.3);
tl.from("#c1a4-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 77.6);
tl.from("#c1a4-stat", { opacity: 0, scale: 0.7, duration: 0.5, ease: "back.out(1.5)" }, 78.4);
tl.from("#c1a4-src", { opacity: 0, y: 10, duration: 0.3 }, 79.0);
tl.to("#c1a4", { opacity: 0, duration: 0.3 }, 94.7);

// ── C2-0 chapter bumper (95–100s) ──────────────────────────
tl.set("#c2b", { opacity: 1 }, 95);
tl.from("#c2b-bar", { scaleY: 0, duration: 0.5, ease: "power2.inOut", transformOrigin: "center" }, 95.2);
tl.from("#c2b-lbl", { opacity: 0, y: -20, duration: 0.3 }, 95.5);
tl.from("#c2b-ttl", { opacity: 0, x: -40, duration: 0.5, ease: "power3.out" }, 95.8);
tl.to("#c2b", { opacity: 0, duration: 0.3 }, 99.7);

// ── C2-1 bar chart (100–125s) ──────────────────────────────
tl.set("#c2chart", { opacity: 1 }, 100);
tl.from("#c2chart-ttl", { opacity: 0, y: -20, duration: 0.4 }, 100.3);
tl.to("#bar-homes", { width: "85.9%", duration: 1.5, ease: "power2.out" }, 101);
tl.from("#bv-homes", { opacity: 0, duration: 0.3 }, 102.3);
tl.to("#bar-dc", { width: "14.1%", duration: 1.2, ease: "power2.out" }, 103);
tl.from("#bv-dc", { opacity: 0, duration: 0.3 }, 104.0);
tl.from("#c2chart-unit", { opacity: 0, duration: 0.4 }, 105);
tl.to("#c2chart", { opacity: 0, duration: 0.3 }, 124.7);

// ── C2-2 flow diagram (125–145s) ──────────────────────────
tl.set("#c2flow", { opacity: 1 }, 125);
tl.from("#c2flow-ttl", { opacity: 0, y: -20, duration: 0.4 }, 125.3);
tl.from("#c2flow-canvas", { opacity: 0, duration: 0.5 }, 125.7);
tl.from(["#fn-gen","#fn-tx","#fn-dist","#fn-homes","#fn-dc"], 
  { opacity: 0, scale: 0.8, stagger: 0.2, duration: 0.4, ease: "back.out(1.5)" }, 126.5);
tl.to("#c2flow", { opacity: 0, duration: 0.3 }, 144.7);

// ── C2-3 kinetic 14% (145–152s) ─────────────────────────
tl.set("#c2k3", { opacity: 1 }, 145);
tl.from("#c2k3-n", { opacity: 0, scale: 0.5, duration: 0.4, ease: "back.out(2)" }, 145.3);
tl.from("#c2k3-s", { opacity: 0, y: 20, duration: 0.3 }, 145.8);
tl.to("#c2k3", { opacity: 0, duration: 0.25 }, 151.7);

// ── C2-4 kinetic +12% (152–159s) ─────────────────────────
tl.set("#c2k4", { opacity: 1 }, 152);
tl.from("#c2k4-n", { opacity: 0, scale: 0.5, duration: 0.4, ease: "back.out(2)" }, 152.3);
tl.from("#c2k4-s", { opacity: 0, y: 20, duration: 0.3 }, 152.8);
tl.to("#c2k4", { opacity: 0, duration: 0.25 }, 158.7);

// ── C2-5 kinetic 1.4M (159–165s) ─────────────────────────
tl.set("#c2k5", { opacity: 1 }, 159);
tl.from("#c2k5-n", { opacity: 0, scale: 0.5, duration: 0.4, ease: "back.out(2)" }, 159.3);
tl.from("#c2k5-s", { opacity: 0, y: 20, duration: 0.3 }, 159.8);
tl.to("#c2k5", { opacity: 0, duration: 0.25 }, 164.7);

// ── C2-6 kinetic 1 BUILDING (165–170s) ───────────────────
tl.set("#c2k6", { opacity: 1 }, 165);
tl.from("#c2k6-n", { opacity: 0, scale: 0.5, duration: 0.4, ease: "back.out(2)" }, 165.3);
tl.from("#c2k6-s", { opacity: 0, y: 20, duration: 0.3 }, 165.8);
tl.to("#c2k6", { opacity: 0, duration: 0.25 }, 169.7);

// ── C3-0 chapter bumper (170–175s) ──────────────────────
tl.set("#c3b", { opacity: 1 }, 170);
tl.from("#c3b-bar", { scaleY: 0, duration: 0.5, ease: "power2.inOut", transformOrigin: "center" }, 170.2);
tl.from("#c3b-lbl", { opacity: 0, y: -20, duration: 0.3 }, 170.5);
tl.from("#c3b-ttl", { opacity: 0, x: -40, duration: 0.5, ease: "power3.out" }, 170.8);
tl.to("#c3b", { opacity: 0, duration: 0.3 }, 174.7);

// ── C3-1 anchor card (175–190s) ──────────────────────────
tl.set("#c3a1", { opacity: 1 }, 175);
tl.from("#c3a1-tag", { opacity: 0, x: -20, duration: 0.3 }, 175.3);
tl.from("#c3a1-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 175.6);
tl.from("#c3a1-stat", { opacity: 0, scale: 0.7, duration: 0.5, ease: "back.out(1.5)" }, 176.4);
tl.from("#c3a1-src", { opacity: 0, y: 10, duration: 0.3 }, 177.0);
tl.to("#c3a1", { opacity: 0, duration: 0.3 }, 189.7);

// ── C3-2 jobs bar chart (190–210s) ────────────────────────
tl.set("#c3jobs", { opacity: 1 }, 190);
tl.from("#c3jobs-ttl", { opacity: 0, y: -20, duration: 0.4 }, 190.3);
tl.to("#bar-promised", { width: "100%", duration: 1.2, ease: "power2.out" }, 191);
tl.from("#bv-promised", { opacity: 0, duration: 0.3 }, 192.0);
tl.to("#bar-actual", { width: "7.5%", duration: 0.6, ease: "power2.out" }, 194);
tl.from("#bv-actual", { opacity: 0, duration: 0.3 }, 194.5);
tl.from("#c3jobs-ann", { opacity: 0, scale: 1.2, duration: 0.5, ease: "back.out(1.5)" }, 196);
tl.to("#c3jobs", { opacity: 0, duration: 0.3 }, 209.7);

// ── C3-3 document reveal (210–227s) ──────────────────────
tl.set("#c3d", { opacity: 1 }, 210);
tl.to("#c3d-paper", { opacity: 1, rotateX: 0, duration: 0.7, ease: "power2.out" }, 210.2);
tl.to("#c3d-ann", { opacity: 1, duration: 0.4 }, 216);
tl.to(["#c3d-redact","#c3d-redact2"], { backgroundColor: "transparent", color: "#1a1a1a", duration: 0.5, stagger: 0.3 }, 220);
tl.to("#c3d", { opacity: 0, duration: 0.3 }, 226.7);

// ── C3-4 anchor card (227–240s) ──────────────────────────
tl.set("#c3a4", { opacity: 1 }, 227);
tl.from("#c3a4-tag", { opacity: 0, x: -20, duration: 0.3 }, 227.3);
tl.from("#c3a4-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 227.6);
tl.from("#c3a4-stat", { opacity: 0, scale: 0.7, duration: 0.5, ease: "back.out(1.5)" }, 228.4);
tl.from("#c3a4-src", { opacity: 0, y: 10, duration: 0.3 }, 229.0);
tl.to("#c3a4", { opacity: 0, duration: 0.3 }, 239.7);

// ── C4-0 chapter bumper (240–245s) ──────────────────────
tl.set("#c4b", { opacity: 1 }, 240);
tl.from("#c4b-bar", { scaleY: 0, duration: 0.5, ease: "power2.inOut", transformOrigin: "center" }, 240.2);
tl.from("#c4b-lbl", { opacity: 0, y: -20, duration: 0.3 }, 240.5);
tl.from("#c4b-ttl", { opacity: 0, x: -40, duration: 0.5, ease: "power3.out" }, 240.8);
tl.to("#c4b", { opacity: 0, duration: 0.3 }, 244.7);

// ── C4-1 kinetic peak (245–257s) ─────────────────────────
tl.set("#c4k1", { opacity: 1 }, 245);
tl.from("#c4k1-n", { opacity: 0, y: -40, scale: 0.9, duration: 0.5, ease: "power3.out" }, 245.3);
tl.from("#c4k1-s", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 245.9);
tl.to("#c4k1", { opacity: 0, duration: 0.3 }, 256.7);

// ── C4-2 money flow (257–270s) ────────────────────────────
tl.set("#c4flow", { opacity: 1 }, 257);
tl.from("#c4flow-ttl", { opacity: 0, y: -20, duration: 0.4 }, 257.3);
tl.from("#c4flow-canvas", { opacity: 0, duration: 0.5 }, 257.7);
tl.from(["#fn4-util","#fn4-dc","#fn4-rb","#fn4-res"],
  { opacity: 0, scale: 0.8, stagger: 0.25, duration: 0.4, ease: "back.out(1.5)" }, 258.2);
tl.to("#c4flow", { opacity: 0, duration: 0.3 }, 269.7);

// ── C4-3 anchor card (270–275s) ──────────────────────────
tl.set("#c4a3", { opacity: 1 }, 270);
tl.from("#c4a3-tag", { opacity: 0, x: -20, duration: 0.3 }, 270.3);
tl.from("#c4a3-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 270.5);
tl.from("#c4a3-stat", { opacity: 0, scale: 0.7, duration: 0.4, ease: "back.out(1.5)" }, 271.1);
tl.from("#c4a3-src", { opacity: 0, y: 10, duration: 0.3 }, 271.5);
tl.to("#c4a3", { opacity: 0, duration: 0.3 }, 274.7);

// ── C4-4 anchor card (275–280s) ──────────────────────────
tl.set("#c4a4", { opacity: 1 }, 275);
tl.from("#c4a4-tag", { opacity: 0, x: -20, duration: 0.3 }, 275.3);
tl.from("#c4a4-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 275.5);
tl.from("#c4a4-stat", { opacity: 0, scale: 0.7, duration: 0.4, ease: "back.out(1.5)" }, 276.1);
tl.from("#c4a4-src", { opacity: 0, y: 10, duration: 0.3 }, 276.5);
tl.to("#c4a4", { opacity: 0, duration: 0.3 }, 279.7);

// ── L1 map + ticker (280–293s) ────────────────────────────
tl.set("#l1map", { opacity: 1 }, 280);
tl.from("#l1-count", { opacity: 0, scale: 0.4, duration: 0.6, ease: "back.out(2)" }, 280.3);
tl.from("#l1-title", { opacity: 0, y: 20, duration: 0.4, ease: "power2.out" }, 281.0);
// Ticker scroll: full width ÷ content → animate x to scroll left
tl.fromTo("#l1-ticker",
  { x: 200 },
  { x: -3200, duration: 12, ease: "none" },
  281);
tl.to("#l1map", { opacity: 0, duration: 0.3 }, 292.7);

// ── L2 CTA card (293–300s) ────────────────────────────────
tl.set("#l2cta", { opacity: 1 }, 293);
tl.from("#l2-hl", { opacity: 0, y: 30, duration: 0.5, ease: "power3.out" }, 293.3);
tl.from("#l2-handle", { opacity: 0, scale: 0.8, duration: 0.4, ease: "back.out(1.5)" }, 294.0);
tl.from("#l2-sub", { opacity: 0, y: 10, duration: 0.3 }, 294.6);

window.__timelines = window.__timelines || {};
window.__timelines["root"] = tl;
</script>
</body>
</html>
```

- [ ] **Step 9.2: Lint the composition**

```bash
npx hyperframes lint projects/grid-squeeze/hyperframes
```

Expected: `✓ No errors found` (warnings about external CDN fonts are acceptable)

If errors appear about missing audio files: create placeholder silent files first (see Task 7 fallback), then re-lint.

---

## Task 10: Render

**Files:** `projects/grid-squeeze/renders/final.mp4`

- [ ] **Step 10.1: Verify all audio files exist**

```bash
ls -lh projects/grid-squeeze/assets/audio/narration_*.wav projects/grid-squeeze/assets/audio/music_*.mp3
```

Expected: 6 `narration_*.wav` files (processed) + 2 `music_*.mp3` files.
If music is missing, create silent placeholders (Task 7 fallback command).

- [ ] **Step 10.2: Run render**

```bash
npx hyperframes render projects/grid-squeeze/hyperframes \
  -o projects/grid-squeeze/renders/final.mp4 \
  --fps 30 \
  --quality high
```

Expected: Render completes, outputs `projects/grid-squeeze/renders/final.mp4`.
Estimated render time: 5–20 minutes depending on workers.

- [ ] **Step 10.3: Validate output**

```bash
ffprobe -v quiet \
  -show_entries format=duration,size \
  -show_entries stream=width,height,codec_name \
  -of default=noprint_wrappers=1 \
  projects/grid-squeeze/renders/final.mp4
```

Expected:
```
codec_name=h264
width=1920
height=1080
duration=300.000000 (within ±5s)
size=<any>
```

- [ ] **Step 10.4: Check runtime**

```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 projects/grid-squeeze/renders/final.mp4
```

Duration must be between 285 and 315 (spec: 4:45–5:15).

- [ ] **Step 10.5: Final commit**

```bash
git add projects/grid-squeeze/artifacts/ projects/grid-squeeze/hyperframes/index.html projects/grid-squeeze/gen_narration.py
git commit -m "feat(grid-squeeze): complete episode production — script, scene plan, composition"
```

Note: Do not commit audio or video files (add them to `.gitignore` if not already).

---

## Self-Review Against Spec

**Spec coverage check:**

| Spec requirement | Task |
|-----------------|------|
| New pipeline `broadcast-explainer.yaml` | Task 1 |
| New playbook `broadcast-investigative.yaml` | Task 1 |
| Director skills in `skills/pipelines/broadcast-explainer/` | Task 2 |
| Project directory `projects/grid-squeeze/` | Task 3 |
| 26 scenes across 6 chapters | Task 5 + Task 9 |
| Chapter bumpers ×4 | Scene plan + composition |
| Broadcast anchor cards ×8 | Scene plan + composition |
| Kinetic text beats ×6 | Scene plan + composition |
| Data visualizations ×5 | Scene plan + composition |
| Document reveals ×2 | Scene plan + composition |
| Map + ticker ×1 | Scene plan + composition |
| Fish Speech S2-Pro narration | Task 6+7 |
| `egirl_v1` reference_id on every request | gen_narration.py |
| S2-Pro bracket `[tag]` syntax | script.json tagged_text |
| Loudnorm –14 LUFS post-process | Task 7 |
| HyperFrames render 1920×1080 30fps | Task 8+10 |
| `hyperframes lint` before render | Task 10 step 2 |

**Type consistency check:** All GSAP animation IDs in the `<script>` block (`#h1`, `#h2`, etc.) match the element IDs in the HTML above them. ✓

**No placeholders:** All scene HTML is fully written. All GSAP tweens are complete. No TBD/TODO present. ✓
