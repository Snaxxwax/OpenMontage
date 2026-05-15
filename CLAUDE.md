# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **MANDATORY — read before responding to any user message:** `AGENT_GUIDE.md` contains routing rules that determine your first action. For Asymmetric channel productions specifically, `.claude/CLAUDE.md` is the brand and editorial authority. For all pipeline behavior and artifact generation, `AGENTS.md` is the model-agnostic contract.

---

## What This Repo Is

OpenMontage is an **agent-orchestrated video production platform**. The LLM agent IS the orchestrator — it reads YAML pipeline manifests and Markdown skill files, calls Python tools, and checkpoints state. There is no runtime Python orchestrator.

```
Agent reads pipeline manifest → reads stage director skill → calls Python tools
  → self-reviews → checkpoints → human approval gate → next stage
```

**Python = tools + persistence only.** All creative decisions, orchestration logic, and quality standards live in instruction files (YAML + Markdown).

---

## Commands

```bash
# Setup (Python deps + Remotion npm install + Piper TTS + HyperFrames cache)
make setup

# Install Python deps only
make install

# GPU support (local video/image generation)
make install-gpu

# Run all tests
make test

# Contract tests only (no API keys needed — fast)
make test-contracts

# Capability preflight — shows what tools are configured
make preflight
# Or the human-readable summary:
python3 -c "from tools.tool_registry import registry; import json; registry.discover(); print(json.dumps(registry.provider_menu_summary(), indent=2))"

# Render zero-key demo videos (Remotion only, no API keys)
make demo

# Validate HyperFrames runtime
make hyperframes-doctor
```

**Asymmetric channel slash commands** (available in Claude Code):
- `/om-asymmetric-run-sequence` — 14-step production checklist
- `/om-asymmetric-format-gate <project_id>` — F1–F3 + P1–P7 status view
- `/om-asymmetric-performance-package` — concept evaluation gate
- `/om-asymmetric-clip-quality-gate` — score clips before acquisition
- `/om-asymmetric-render-readiness` — pre-render gate check
- `/om-asymmetric-postmortem` — post-render lessons capture
- `/om-asymmetric-opening-proof` — F3 opening sequence proof

**Remotion render (Asymmetric — only working invocation):**
```bash
cd remotion-composer && npx remotion render src/index.tsx Explainer <output>.mp4 \
  --props <receipts/remotion_props_final_v5.json> \
  --concurrency=1 --every-nth-frame=2 --offthreadvideo-video-threads=4 \
  --timeout=600000 --browser-executable=/usr/bin/google-chrome
```
`--concurrency > 1` hangs (OffthreadVideo deadlock). GPU rendering is 3× slower due to readback overhead. `--every-nth-frame=2` = 15fps; upsample with ffmpeg after.

---

## Architecture

### Three-Layer Knowledge System

```
Layer 1: tools/ + pipeline_defs/   "What exists" — BaseTool contracts + YAML manifests
Layer 2: skills/                   "How OpenMontage uses it" — stage director skills
Layer 3: .agents/skills/           "How the technology works" — vendor knowledge packs
```

Each tool's `agent_skills[]` field links Layer 1 → Layer 3. **Always read the Layer 3 skill before writing generation prompts** — it contains provider-specific prompt engineering that materially improves output quality.

### Key Files

| File | Purpose |
|------|---------|
| `AGENT_GUIDE.md` | Full agent contract — read first |
| `PROJECT_CONTEXT.md` | Architecture + key file reference |
| `pipeline_defs/*.yaml` | Pipeline manifests (stages, tools, approval gates) |
| `skills/pipelines/<pipeline>/<stage>-director.md` | Stage-level agent instructions |
| `skills/meta/reviewer.md` | Self-review protocol |
| `skills/meta/checkpoint-protocol.md` | When to pause for human approval |
| `tools/base_tool.py` | `BaseTool` ABC — all tools inherit from this |
| `tools/tool_registry.py` | Auto-discovery singleton (no manual registration) |
| `tools/cost_tracker.py` | Budget: estimate → reserve → reconcile |
| `lib/checkpoint.py` | Pipeline state persistence |
| `schemas/artifacts/` | JSON schemas for all 11 canonical artifacts |
| `remotion-composer/` | React/Remotion composition engine |
| `docs/asymmetric/orchestration_contract.md` | 17-phase Asymmetric sequence |
| `docs/asymmetric/subagent_orchestration.md` | Claude-specific subagent invocation |

### Pipeline State Machine

```
research → proposal → script → scene_plan → assets → edit → compose → publish
```

Each stage produces a **canonical artifact** validated against `schemas/artifacts/`. Checkpoints persist to `shared_studio/projects/<project-id>/`. All generated assets go there — never to the repo root.

### Tool System

- All tools inherit `BaseTool`, implement `execute(inputs) -> ToolResult`
- Class names are **PascalCase without "Tool" suffix** (e.g., `ElevenLabsTTS`, not `ElevenLabsTTSTool`)
- Call via `.execute(params_dict)` — not `.run()`
- Registry auto-discovers via `pkgutil.walk_packages()` — adding a tool file is enough
- Three selector tools abstract multi-provider routing: `tts_selector`, `image_selector`, `video_selector`

### Composition Runtimes

`render_runtime` is locked at proposal and carried through `edit_decisions`. Silent swaps between runtimes are a governance violation.

| Runtime | Best For | Requires |
|---------|----------|---------|
| **Remotion** | React scenes, stat cards, captions, spring animations | Node.js + `remotion-composer/` |
| **HyperFrames** | Kinetic typography, GSAP, SVG character rigs, HTML-native motion | Node.js ≥ 22 + FFmpeg |
| **FFmpeg** | Simple concat/trim, subtitle burn | `ffmpeg` binary |

When both Remotion and HyperFrames are available, **always present both options** to the user before locking `render_runtime`. See `skills/core/hyperframes.md` for the decision matrix.

---

## Asymmetric Channel Production

This repo is primarily used to produce content for the **ASYMMETRIC** YouTube channel. The `.claude/CLAUDE.md` file contains the full brand and editorial authority.

### Subagents

Six specialist subagents handle specific pipeline gates. The main session acts as executive producer — it coordinates and verifies artifacts but does **not** do the work belonging to a specialist:

| Agent | Role |
|---|---|
| `om-performance-producer` | F2 Packaging Test + Step 2 |
| `om-researcher` | F1 Pacing DNA + Step 4 Research |
| `om-source-clip-curator` | Step 5 Clip Quality Gate |
| `om-writer` | F3 Opening Sequence Proof + Steps 7+8 (single invocation only) |
| `om-render-operator` | Step 11 Render |
| `om-qc-reviewer` | Step 12 QC + F4 Postmortem |

`creative_pass` is **operator-only** — no agent or tool may set it. `acquisition_allowed` stays false until the operator explicitly approves per-clip.

### Source-Commentary Pipeline

The `source-commentary` pipeline enforces an **Evidence Lock**:
- Discovery stages are metadata-only — no binary media downloads
- Acquisition is blocked unless every approved clip has a schema-valid `clip_use_receipt`
- Edit planning is blocked without the `approved_clip_manifest` from Media QC
- Composition is blocked without the `source_commentary_edit_plan`
- Narration: Fish Speech S2 Pro only (Piper is not approved for this pipeline)

### Local Services

**Fish Speech S2 Pro (TTS):** port 8080, ~30s startup. Requires stopping ComfyUI first (VRAM constraint). Full start/stop commands in `memory/fish_speech.md`.

**ComfyUI:** `python main.py --disable-auto-launch --listen 0.0.0.0 --port 18188`. Stop with `kill $(pgrep -f "main.py.*18188")`.

---

## Adding New Tools

1. Inherit from `tools/base_tool.py` `BaseTool`
2. Place in the correct package (`tools/audio/`, `tools/video/`, `tools/graphics/`, etc.)
3. Implement `execute()` returning `ToolResult`
4. Declare all contract fields: `capability`, `provider`, `runtime`, `dependencies`, `agent_skills`, `fallback_tools`
5. Registry auto-discovers — no manual registration needed

## Adding New Pipelines

1. Create YAML manifest in `pipeline_defs/` (validated against `schemas/pipelines/pipeline_manifest.schema.json`)
2. Create stage director skills in `skills/pipelines/<pipeline-name>/`
3. Add contract tests in `tests/contracts/`
