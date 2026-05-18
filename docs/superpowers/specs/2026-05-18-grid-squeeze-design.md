# Design Spec: "The Grid Squeeze"

**Date:** 2026-05-18  
**Channel:** Asymmetric  
**Episode ID:** grid-squeeze  
**Format:** 5-minute animated explainer  
**Render runtime:** HyperFrames  
**Visual style:** Broadcast-investigative (cinematic documentary)  

---

## 1. Story

**Angle:** The Grid Squeeze — one data center approval, thousands of residents paying the bill.

**Hook:** "Your electricity bill went up. Here's the building responsible."

**Thesis:** A single hyperscale data center drawing 847MW gets approved in a closed council vote, strains local grid capacity, triggers a residential rate hike, and the mechanism that made it all possible — tax abatements and non-disclosure agreements — is designed to repeat in 47 cities.

**Hidden leverage:** The approval process is structured so "no" is politically impossible, and the cost transfer to residents is buried in utility rate filings no one reads.

---

## 2. Episode Structure

| Segment | Time | Title | Story beat |
|---------|------|-------|-----------|
| Hook | 0–25s | — | "Your electricity bill went up. Here's the building responsible." Kinetic text + stat reveal. |
| Ch. 1 | 25–95s | THE APPROVAL | How 847MW gets greenlit overnight — permit process, NDA, council vote. |
| Ch. 2 | 95–170s | THE GRID MATH | What 847MW displaces. Grid capacity, homes vs. servers, peak demand conflicts. |
| Ch. 3 | 170–240s | THE DEAL | Why the city said yes. Tax abatements, job promises vs. actual headcounts, 10-year lock-in. |
| Ch. 4 | 240–280s | THE LEVERAGE | Who profits, who pays. Rate hike mechanism — how grid demand becomes a residential bill line item. |
| Landing | 280–300s | — | "Same playbook. 47 cities." US map, rolling ticker, CTA. |

Total runtime: ~300 seconds (5 minutes)

---

## 3. Visual Style

**Aesthetic:** Broadcast-investigative. Cinematic documentary tone — Al Jazeera meets MKBHD. Not TV news camp.

**Palette:**
- Background: `#0d1117` (near-black charcoal)
- Accent: `#c0392b` (deep red — chapter bumpers, alert states)
- Data: `#ffcc00` (amber — charts, stats, data reveals)
- Text: `#ffffff` primary, `rgba(255,255,255,0.65)` secondary
- Document reveals: `#f5f0e8` (aged paper) with `#cc2200` red annotations

**Typography:**
- Headlines: Barlow Condensed Bold (Google Font, free — distinctive, high contrast)
- Body/lower-thirds: Inter Regular
- Kinetic text: large-scale, letter-by-letter GSAP assembly
- Data labels: monospace (JetBrains Mono or system monospace)

**Scene cadence:** Cut every 6–10 seconds. No static holds beyond 8 seconds.

---

## 4. Scene Inventory (26 total)

| Type | Count | Description |
|------|-------|-------------|
| Chapter bumper | 4 | Full-screen bold white type on dark red — chapter number + title |
| Broadcast anchor card | 8 | Headline + supporting stat + lower-third source attribution |
| Kinetic text beat | 6 | Large-scale GSAP letter animation — emphasis moments |
| Data visualization | 5 | Bar chart (grid math), flow diagram (money), map (47 cities), before/after (jobs) |
| Document reveal | 2 | Permit filing + rate hike document with animated redaction lift |
| Map + ticker | 1 | US map with 47 dots + rolling city name ticker |

---

## 5. Pipeline

**New pipeline:** `pipeline_defs/broadcast-explainer.yaml`

This is the reusable archetype for Asymmetric broadcast-style episodes. Differences from `animated-explainer`:
- `render_runtime: hyperframes` (locked — not user-selectable at proposal for this pipeline)
- `playbook: broadcast-investigative` — **must be created** as `styles/broadcast-investigative.yaml` (new file, not an existing playbook)
- Scene plan artifact includes `hyperframes_blocks[]` field listing registry blocks per scene
- Compose stage runs `hyperframes_compose` directly, not `video_compose` generic

**Note on HyperFrames block names:** Block names in Section 8 are based on the installed skill docs. Verify against the actual registry at workspace init with `npx hyperframes add --list` and adjust names if they differ.

**Stage flow:**
```
idea → script → scene_plan → assets → edit → compose
```

Each stage reads its director skill from `skills/pipelines/broadcast-explainer/<stage>-director.md`.

---

## 6. Project Directory

```
projects/grid-squeeze/
├── artifacts/
│   ├── brief.json
│   ├── script.json
│   ├── scene_plan.json
│   └── edit_decisions.json
├── assets/
│   ├── audio/
│   │   ├── narration_*.mp3      (per-segment ElevenLabs TTS)
│   │   ├── music_tension.mp3    (Suno — Chs 1–3)
│   │   └── music_land.mp3       (Suno — Ch 4 + landing)
│   └── images/                  (any supporting assets)
├── hyperframes/
│   ├── index.html               (HyperFrames workspace root)
│   └── blocks/                  (installed registry blocks)
└── renders/
    └── final.mp4
```

---

## 7. Audio Plan

### TTS — Fish Speech S2-Pro (local, port 8080)

- **Voice character:** e-girl — high-pitched, energetic, slightly anime-streamer quality. Contrast with the serious investigative content is intentional (makes the data land harder).
- **Reference audio:** `references/egirl_v1/` — **must be created before generation.** Record or source ~15–30s of clean e-girl voice speech, place as `sample.wav` + `sample.lab` (transcript). Without this, S2-Pro uses its default voice timbre.
- **reference_id:** `egirl_v1` — pass on every request or voice drifts between segments.
- **Tag syntax:** S2-Pro uses `[natural language description]` brackets, NOT S1 parenthesis tags. Tags may appear anywhere in the text.

**API parameters:**
```python
ServeTTSRequest(
    text="...",           # with inline [tags]
    reference_id="egirl_v1",
    format="wav",
    streaming=False,
    normalize=True,
    temperature=0.8,
    top_p=0.8,
    repetition_penalty=1.1,
    use_memory_cache="on",
)
```

**GPU management:** Kill ComfyUI (`kill $(pgrep -f "main.py.*18188")`) before generating. Fish Speech S2-Pro requires ~30s startup; health-check at `http://127.0.0.1:8080/v1/health` before sending requests.

**Tag vocabulary for this episode:**

| Tag | Use case |
|-----|----------|
| `[e-girl voice]` | Default reset — apply at segment start |
| `[excited]` | Hook line, big stat reveals |
| `[curious]` | Rhetorical questions ("But why?") |
| `[whispering]` | Mechanism reveals, the "hidden" beats |
| `[enthusiastic]` | Chapter opening lines |
| `[concerned]` | Rate hike / who pays sections |
| `[pause]` | Before key numbers and after hooks |
| `[short pause]` | Clause transitions |
| `[emphasis]` | Key numbers: "847 megawatts", "47 cities" |

**Sample tagged script (hook):**
```
[e-girl voice][excited] Your electricity bill went up.
[pause] Here's the building responsible.
[short pause][curious] One building.
[emphasis] Eight hundred and forty-seven megawatts.
[whispering] And most people in that city have no idea it exists.
```

**Post-processing (required):**
```bash
ffmpeg -y -i narration_raw.wav \
  -af loudnorm=I=-14:TP=-1.0:LRA=11 \
  narration.wav
```
Target: –14 LUFS (YouTube/Instagram standard). Fish Speech outputs –15 to –24 LUFS raw.

### Music — Suno

Two cues:
- `music_tension`: sparse industrial ambient, builds through Chs 1–3
- `music_land`: unresolved/uneasy, Ch 4 through landing

### Mix

- Narration: 0dB reference
- Music: ducked to –18dB under speech, –10dB in music-only gaps
- Subtitles: HyperFrames caption block, white condensed sans on dark strip, burned into render

---

## 8. HyperFrames Block Registry

Blocks installed at workspace init via `hyperframes add <name>`:

| Block | Purpose |
|-------|---------|
| `title-card` | Chapter bumpers |
| `lower-third` | Source attribution strips |
| `data-overlay` | Broadcast anchor cards |
| `kinetic-typography` | Hook + emphasis beats |
| `data-chart` | Bar charts, before/after |
| `data-flow` | Money flow, grid topology diagram |
| `data-map` | 47-city US map |
| `ticker` | Rolling city name list |
| `image-reveal` | Document/permit reveals |
| `cta` | End card |

---

## 9. Out of Scope

- No AI-generated video clips (no Runway, no LTX-2) — pure HyperFrames animation
- No character illustrations — broadcast style is typography and data-led
- No live footage — this is a fully synthetic render
- No HeyGen avatar

---

## 10. Success Criteria

- Renders to `projects/grid-squeeze/renders/final.mp4` at 1920×1080, 30fps
- Runtime between 4:45 and 5:15
- All 26 scenes present and timed to narration
- Subtitles legible at mobile size
- Music mixed correctly (narration intelligible throughout)
