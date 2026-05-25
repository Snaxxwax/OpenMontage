# Quibi: The Kill Switch — Episode Design Spec

Status: approved
Date: 2026-05-25
Channel: Modern Archivist / Failure Ledger
Franchise: The Kill Switch

## Thesis

Turnstile — Quibi's proprietary DRM — made virality architecturally impossible on a platform that
needed virality to survive. This is not a story about bad timing or the pandemic. It is a story about
one architectural decision, made in 2019, that predetermined the outcome.

## Episode metadata

| Field | Value |
|---|---|
| Title | The App That Made Sharing Impossible |
| Target duration | 10–14 minutes |
| Pipeline | channels/modern-archivist/pipeline.yaml |
| Project ID | quibi-kill-switch |
| Render runtime | Remotion (final assembly) + HyperFrames (kinetic segments) |

## Act structure

| Act | Title | Start | Duration | Visual mode | Runtime |
|---|---|---|---|---|---|
| 1 | Cold open: the shutdown | 0:00 | 20s | Sourced clip — Quibi shutdown statement | FFmpeg plate |
| 2 | Promise | 0:20 | 25s | Puppet monologue — sets the thesis | Remotion STATE_MONOLOGUE |
| 3 | The machine | 0:45 | 105s | Sourced: launch keynote + Katzenberg interview + app demo | FFmpeg plates |
| 4 | The first crack: Turnstile | 2:30 | 120s | HyperFrames kinetic reveal | HyperFrames segment |
| 5 | The paper trail | 4:30 | 180s | Sourced clips as FFmpeg plates, cut-to HyperFrames evidence board segment (~45s) | Mixed: FFmpeg plates + HyperFrames insert |
| 6 | The decision that broke it | 7:30 | 180s | Sourced interviews + puppet contradiction reveal | Remotion STATE_CRITICAL_ERROR |
| 7 | The collapse | 10:30 | 120s | HyperFrames collapse timeline + sourced shutdown coverage | HyperFrames segment |
| 8 | The verdict | 12:30 | 90s | Puppet closes the ledger | Remotion STATE_MONOLOGUE |

## Source footage targets

### Act 1 — Cold open
- Katzenberg/Whitman joint shutdown statement, October 21 2020
- CNBC/Bloomberg live reaction coverage, same date

### Act 3 — The machine
- Quibi launch keynote, CES January 2020 (full keynote on YouTube)
- Katzenberg Bloomberg Businessweek interview, February 2020
- App UI hands-on demo footage from launch-day reviewers

### Act 5 — The paper trail
- The Verge video review mentioning Turnstile/no-sharing
- Creator interviews about the platform limitations
- Pull quotes from Vulture/NYT pieces on users unable to screenshot

### Act 6 — The decision
- Katzenberg "I attribute everything to COVID" interview (the contradiction)
- Whitman post-shutdown interviews where Turnstile justification surfaces

### Provenance rules
- All clips used for commentary and criticism (fair use)
- Every clip labeled in episode: source + date
- Acquisition: yt-dlp with `curl_cffi==0.14.0 --impersonate "Chrome-133"`
- Immediate transcode to H264 after download
- No stock footage, no AI-generated video

## HyperFrames segments

### Segment 1 — Act 4: Turnstile Reveal (2 min)

Three beats:

1. **Normal platform mechanics** — animated split showing how a TikTok/Instagram clip travels:
   record → share → screenshot → viral. Fast, tactile, familiar.
2. **Turnstile intercept** — same flow attempted on Quibi. Hard block at each step.
   DRM architecture visualized as a wall between content and the outside world.
3. **The irony landing** — stat cards: Quibi spent $63M on marketing Q1 2020.
   Zero organic clips spread. Not one viral moment from 175 shows.

Typography-heavy, GSAP-driven. Palette: black + white + red accent.

### Segment 2 — Act 7: Collapse Timeline (2 min)

Kinetic timeline: April 6 2020 → October 21 2020 (198 days).

- Headlines sweep in at key dates
- Running counter: $8.8M/day burn rate
- Final state: 5.6M downloads, ~500K paying subscribers, $1.75B gone

Clean, fast, documentary-style. No decoration — just the receipts moving. Same palette.

## Remotion puppet scenes

| Act | State | Narration intent |
|---|---|---|
| 2 | STATE_MONOLOGUE | Opens the case. "This isn't a story about bad timing. It's about one decision." |
| 6 | STATE_CRITICAL_ERROR | Plays Katzenberg COVID quote, then: "He blamed a pandemic for a DRM decision made in 2019." |
| 8 | STATE_MONOLOGUE | Closes the ledger. Names who decided, when, and what it cost. |

## Asset requirements

| Asset | Decision |
|---|---|
| TTS provider | Fish Speech S2-Pro (primary, local port 8080); ElevenLabs (fallback) |
| Music style | Cold, clinical, electronic — no emotional signposting |
| Music provider | Suno or ElevenLabs music |
| HyperFrames palette | Black (#000) + white (#fff) + red (#dc2626) accent |
| Evidence cards | Monochrome with red for Turnstile/kill switch callouts |

## Render pipeline sequencing

1. **Source ingest** — yt-dlp acquisition, H264 transcode, trim to required segments (FFmpeg)
2. **TTS narration** — Fish Speech S2-Pro generates per-act narration WAV files
3. **Music generation** — Suno/ElevenLabs generates 14-min cold/clinical track
4. **HyperFrames renders** — Act 4 and Act 7 segments rendered to MP4 independently
5. **Final Remotion assembly** — puppet scenes + pre-cached plates + HyperFrames segments
   + narration audio + music + captions; one render pass
6. **Audio mix** — FFmpeg post-mux if needed
7. **QC gates** — evidence labels, render integrity, visual identity checks

### Fish Speech startup (before TTS stage)
```bash
# Stop ComfyUI first (VRAM rule):
kill $(pgrep -f "main.py.*18188") 2>/dev/null

cd /home/pop/local-ai/fish-speech && \
nohup .venv/bin/python tools/api_server.py \
  --listen 0.0.0.0:8080 \
  --llama-checkpoint-path checkpoints/s2-pro \
  --decoder-checkpoint-path checkpoints/s2-pro/codec.pth \
  --decoder-config-name modded_dac_vq \
  > /tmp/fish_speech_server.log 2>&1 &
echo $! > /tmp/fish_speech.pid
# Wait ~30s then: curl http://127.0.0.1:8080/v1/health
```

## Anti-patterns (per channel source of truth)

- No static SEC filing screenshots as primary visual surface
- No generic line charts as main visual
- No AI-generated video clips
- No permanent bottom-right puppet mascot
- No unlabeled illustrative material
- No live network fetches during render
