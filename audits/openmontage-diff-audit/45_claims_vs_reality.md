# Claims vs Reality (Changed Docs/Skills)

Scope:
- Only claims found in **changed** markdown/skill files in this fork diff (`upstream/main...HEAD`).
- Evidence is limited to: code, wiring, schemas, tests, diff outputs, and command output captured under `audits/openmontage-diff-audit/`.

Legend:
- **TRUE**: code + wiring exists; verification path exists.
- **MOSTLY_TRUE**: implemented, but conditional (env/deps), or not guaranteed in every pipeline.
- **EXAGGERATED**: directionally true, but overstated ("always", "guarantees", etc).
- **DOCS_ONLY**: described in docs/skills but no runtime path.
- **FALSE**: contradicted by code.
- **UNVERIFIABLE**: depends on external agent tooling/process, not enforceable by this repo.

## High-signal claims

### 1) “ComfyUI local backend integration for image, video, and audio generation”
- **Where:** `.agents/skills/comfyui/SKILL.md:3`
- **Classification:** TRUE
- **Evidence:**
  - Tools: `tools/graphics/comfyui_image.py`, `tools/video/comfyui_video.py`, `tools/audio/comfyui_audio.py`
  - Shared backend: `tools/_comfyui/client.py`
  - Contract tests: `tests/contracts/test_comfyui_backend.py` (PASS in `40_verification_results.md`)
- **Notes:** actual generation requires a reachable ComfyUI server; selectors will filter it out when unavailable.

### 2) “OpenMontage can upload a local/URL image via /upload/image”
- **Where:** `.agents/skills/comfyui/SKILL.md:44`
- **Classification:** TRUE
- **Evidence:** `tools/_comfyui/client.py` uses the `/upload/image` endpoint.

### 3) “Supports lightweight safety gates per call” (ComfyUI)
- **Where:** `.agents/skills/comfyui/SKILL.md:65`
- **Classification:** MOSTLY_TRUE
- **Evidence:** ComfyUI tools expose queue/resource gating fields; contract tests assert consistent override contract (`tests/contracts/test_comfyui_backend.py`).
- **Caveat:** “safety” is limited to the controls actually used by the caller + what the ComfyUI server enforces.

### 4) “Agent builds a corpus from free stock footage… retrieves motion clips… edits… renders a finished piece (not just stills)”
- **Where:** `README.md:35`
- **Classification:** MOSTLY_TRUE
- **Evidence:** stock source tooling exists under `tools/video/stock_sources/*` and compose tooling exists (`tools/video/video_compose.py`, `tools/video/video_stitch.py`, `tools/video/video_trimmer.py`).
- **Caveat:** whether a given run uses stock motion clips depends on pipeline choice and stage inputs; this is not an always-on guarantee.

### 5) “Agent researches your topic with live web search”
- **Where:** `README.md:133`
- **Classification:** UNVERIFIABLE
- **Reason:** “live web search” is not enforceable by this repository’s runtime; it depends on the external assistant environment/tooling.

### 6) “Before you see anything, the system runs a multi-point self-review (ffprobe validation, frame sampling, audio level analysis, delivery promise verification, subtitle checks)”
- **Where:** `README.md:133`
- **Classification:** EXAGGERATED / MOSTLY_TRUE
- **Evidence:**
  - `tools/video/video_compose.py` includes a final review step and references slideshow-risk scoring.
  - Review guidance exists in `skills/meta/reviewer.md` (e.g., slideshow risk + checks).
- **Caveat:** not every pipeline/stage necessarily enforces every check in every run; some checks can be skipped if required artifacts/inputs are missing.

### 7) “Every provider selection is scored across 7 dimensions… picks the best match automatically”
- **Where:** `README.md:329`
- **Classification:** TRUE (for selector-driven families)
- **Evidence:** `lib/scoring.py` computes a weighted score over 7 dimensions and is used by selectors (e.g., `tools/graphics/image_selector.py`).
- **Caveat:** provider scoring applies where selectors are used; direct provider calls bypass selector scoring.

### 8) “Delivery promise enforcement blocks slideshow-looking renders”
- **Where:** `README.md:330`
- **Classification:** MOSTLY_TRUE
- **Evidence:** `tools/video/video_compose.py` calls `lib.slideshow_risk.score_slideshow_risk` and can fail early with “revise scene plan before rendering.”
- **Caveat:** enforcement depends on having the expected scene plan / edit decisions available.

### 9) “Slideshow risk scoring — 6-dimension analysis … prevents ‘animated PowerPoint’ outputs”
- **Where:** `README.md:573`
- **Classification:** MOSTLY_TRUE
- **Evidence:** slideshow risk scoring is implemented and referenced by `video_compose` and `skills/meta/reviewer.md`.
- **Caveat:** “prevents” is too strong; the system can still render low-quality outputs if checks are skipped/overridden.

### 10) “video_compose render auto-detects when Remotion is needed”
- **Where:** `docs/PROVIDERS.md:495`
- **Classification:** MOSTLY_TRUE
- **Evidence:** `tools/video/video_compose.py` has runtime routing, plus guardrails around `render_runtime` being locked at proposal stage.
- **Caveat:** governance rules explicitly disallow silent runtime swaps; “auto-detect” is constrained by the locked `edit_decisions.render_runtime` contract.

### 11) “Supports voice_id/reference_id plus reference-audio prompting through tts_selector path”
- **Where:** `docs/PROVIDERS.md:550`
- **Classification:** TRUE
- **Evidence:** `tools/audio/tts_selector.py` passes through provider-specific keys; `tools/audio/fish_speech_tts.py` explicitly supports reference prompting fields; contract tests pass (`tests/contracts/test_fish_speech_tts_contract.py`).

### 12) “Missing a provider? system falls through to the next one automatically”
- **Where:** `docs/PROVIDERS.md:735`
- **Classification:** MOSTLY_TRUE
- **Evidence:** selector tools implement fallback ranking across available providers.
- **Caveat:** fallback exists within a capability family; if *no* providers are available, selectors fail.

## Notes
- Keyword hit list (raw): `audits/openmontage-diff-audit/45b_claim_keyword_hits.txt`.
- Contract test results: `audits/openmontage-diff-audit/40_verification_results.md`.

