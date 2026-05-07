# Repo Cleanup Audit — OpenMontage Asymmetric
**Date:** 2026-05-06
**Auditor:** Claude Sonnet 4.6 (automated)
**Scope:** Full repository
**Working tree at audit time:** CLEAN

---

## 1. Executive Summary

The repository is in generally good shape. No tracked secrets were found. The `.gitignore` correctly excludes the `.env` file, `node_modules`, project runtime artifacts, and generated media. The primary structural issues are:

1. **Diverged dual skills registry** — `.agents/skills/` (502 tracked files) and `.claude/skills/` (432 tracked files) overlap significantly but have diverged, creating maintenance confusion and ~8.4MB of duplicated source.
2. **Machine-specific paths in four tracked files** — hardcoded `/home/pop/` and `C:/Users/ishan/` paths exist in tracked source files.
3. **`channel.yaml`** at root hardcodes a local filesystem path for the logo asset.
4. **Checkpoint/archive docs at root of `docs/`** — two source-commentary checkpoint files could move to `docs/archive/`.
5. **Runtime receipts directory** (`remotion-composer/public/`) contains debug/final media (properly ignored but large on-disk).
6. **`projects/` at root** is a separate working directory (ignored by git) that contains stale project artifacts unrelated to the current `shared_studio/` workflow.
7. **Empty `.codex/` directory** has no .gitignore rule (harmless since git doesn't track empty dirs, but a stray artifact).

No action required before next production run. All blockers are low-risk.

---

## 2. Current Git Status

```
Branch: main
Working tree: CLEAN (no staged, unstaged, or untracked changes)
Total tracked files: 1,519
```

Recent commits:
```
42f21f6 Add Asymmetric render theme and hard cut support
628edd2 Add Asymmetric subagent orchestration protocol
88a11c0 Require automatic local GPU tool discovery during render
ecf5ff7 Add Asymmetric high-retention format system
8736837 Add Asymmetric OpenMontage production operating system
```

---

## 3. Top-Level Structure Map

| Path | Type | Classification |
|------|------|----------------|
| `AGENT_GUIDE.md` | agent control / docs | KEEP |
| `AGENTS.md` | agent control | KEEP |
| `CLAUDE.md` | agent control | KEEP |
| `CODEX.md` | agent control (thin redirect) | KEEP |
| `COPILOT.md` | agent control (thin redirect) | KEEP |
| `CURSOR.md` | agent control (thin redirect) | KEEP |
| `GEMINI.md` | agent control (thin redirect) | KEEP |
| `DESIGN.md` | docs (visual identity) | KEEP |
| `LICENSE` | legal | KEEP |
| `Makefile` | build / ops | KEEP |
| `PROJECT_CONTEXT.md` | docs / architecture | KEEP |
| `PROMPT_GALLERY.md` | docs (examples) | KEEP_BUT_REVIEW |
| `README.md` | docs | KEEP |
| `channel.yaml` | config (machine path inside) | KEEP_BUT_REVIEW |
| `config.yaml` | config | KEEP |
| `diagram.png` | asset / docs | KEEP_BUT_REVIEW |
| `pytest.ini` | test config | KEEP |
| `render_demo.py` | demo script | KEEP_BUT_REVIEW |
| `render-demo.sh` | demo script | KEEP_BUT_REVIEW |
| `requirements.txt` | dependency | KEEP |
| `requirements-dev.txt` | dependency | KEEP |
| `requirements-gpu.txt` | dependency | KEEP |
| `setup.py` | package config | KEEP |
| `.env` | credentials (IGNORED — not tracked) | IGNORE_CANDIDATE (already ignored) |
| `.env.example` | credentials template | KEEP |
| `.gitignore` | git config | KEEP |
| `.windsurfrules` | agent control (thin redirect) | KEEP |
| `.agent/` | agent runtime config | KEEP_BUT_REVIEW |
| `.agents/` | agent skills registry | KEEP_BUT_REVIEW (see §5) |
| `.claude/` | Claude control plane | KEEP |
| `.codex/` | empty dir (no .gitignore rule) | IGNORE_CANDIDATE |
| `.cursor/` | Cursor control plane | KEEP |
| `.gemini/` | runtime artifact (IGNORED) | IGNORE_CANDIDATE (already ignored) |
| `.github/` | CI config | KEEP |
| `.playwright-mcp/` | runtime artifact (IGNORED) | IGNORE_CANDIDATE (already ignored) |
| `.pytest_cache/` | test cache (IGNORED) | IGNORE_CANDIDATE (already ignored) |
| `assets/` | source assets | KEEP |
| `channels/` | channel config | KEEP |
| `config/` | local tool config | KEEP |
| `docs/` | documentation | KEEP (with items inside for review) |
| `lib/` | Python library | KEEP |
| `n8n_workflows/` | workflow definitions | KEEP |
| `pipeline_defs/` | pipeline definitions | KEEP |
| `projects/` | runtime workspaces (IGNORED) | KEEP as local artifact |
| `remotion-composer/` | React/video renderer | KEEP |
| `schemas/` | JSON schemas | KEEP |
| `scripts/` | operational shell scripts | KEEP |
| `shared_studio/` | project runtime (IGNORED) | KEEP as local artifact |
| `skills/` | OpenMontage skills library | KEEP |
| `styles/` | visual style configs | KEEP |
| `templates/` | production templates | KEEP |
| `tests/` | test suite | KEEP |
| `tools/` | Python tools | KEEP |

---

## 4. Canonical Directories

These directories are confirmed canonical and should not be touched:

| Directory | Role |
|-----------|------|
| `.claude/agents/` | 6 Asymmetric subagent definitions |
| `.claude/commands/` | 7 Asymmetric slash commands |
| `.claude/CLAUDE.md` | Brand operating system |
| `skills/pipelines/source-commentary/` | Source-commentary pipeline directives |
| `skills/core/`, `skills/creative/`, `skills/meta/` | OpenMontage skill library |
| `pipeline_defs/` | 14 pipeline YAML definitions |
| `schemas/` | JSON schema library |
| `tools/` | Python tool implementations |
| `lib/` | Shared Python library |
| `docs/asymmetric/` | Asymmetric production docs |
| `templates/asymmetric/` | Asymmetric production templates |
| `channels/asymmetric/` | Channel profile and config |
| `styles/` | Visual style configs including `asymmetric.yaml` |
| `config/asymmetric_local_tools.example.yaml` | Safe-to-track local config example |

---

## 5. Suspected Duplicate / Obsolete Directories

### 5A. `.agents/skills/` vs `.claude/skills/` — DIVERGED REGISTRIES

Both directories are tracked and both serve as skill registries, but they have diverged significantly:

| | `.agents/skills/` | `.claude/skills/` |
|---|---|---|
| Tracked files | 502 | 432 |
| Disk size | 4.5MB | 3.9MB |
| Skills only in this dir | `canvas-procedural-animation`, `character-animation-qa`, `character-rigging`, `comfyui`, `grok-media`, entire GSAP suite (8 dirs), entire `hyperframes` suite (12+ entries) | `affiliate-description`, `asymmetric-episode`, `asymmetric-script`, `asymmetric-thumbnail-packaging`, `asymmetric-video-qa` |
| Shared skills | ~71 overlap | ~71 overlap |

**Observation:** `.agents/skills/` is the original OpenMontage generic registry. `.claude/skills/` is a fork that added Asymmetric-specific skills but dropped ~20 generic ones (GSAP, hyperframes, comfyui, etc.). This fork was likely created when Claude Code's skill system was introduced. The two registries are now permanently out of sync.

**Risk:** If an agent depends on a GSAP or hyperframes skill, it will find it in `.agents/skills/` but not in `.claude/skills/`. Conversely, Asymmetric skills exist only in `.claude/skills/`.

**Recommendation (Phase D):** Determine canonical home. Either merge into `.claude/skills/` (add missing skills back) and remove `.agents/skills/`, or accept dual registries with clear ownership docs. Do NOT delete either until the merge is complete.

### 5B. `.codex/` — Empty directory

Created May 5, empty. No tracked files. No .gitignore rule. Stale artifact from Codex initialization.

### 5C. `docs/stage-gates/` — Empty placeholder

Contains only `.gitkeep`. No content. This was a placeholder that was never populated.

### 5D. `projects/` at repo root vs `shared_studio/projects/`

`projects/` (at repo root, ignored by git) contains three project workspaces:
- `_analysis/` — 5 analysis subdirs from ~May 1
- `app-stores-choke-points/` — early production workspace (Apr 30)
- `fico-monopoly/` — early production workspace (May 4)

These appear to be pre-`shared_studio/` era workspaces. Current production uses `shared_studio/projects/`. The root `projects/` directory is the old convention. Both are properly ignored by git.

---

## 6. Generated / Runtime Artifact Findings

### 6A. Properly ignored (no action needed)

| Path | Type | Size |
|------|------|------|
| `remotion-composer/node_modules/` | npm dependencies | 663MB |
| `remotion-composer/public/debug_clip.mp4` | debug render | ~498KB |
| `remotion-composer/public/debug_narration.wav` | debug audio | ~696KB |
| `remotion-composer/public/final_clip.mp4` | final render | ~498KB |
| `remotion-composer/public/final_narration.wav` | final audio | ~696KB |
| `remotion-composer/public/projects` | symlink to shared_studio | — |
| `remotion-composer/public/shared_studio` | symlink to shared_studio | — |
| `.gemini/settings.json` | Gemini runtime config | tiny |
| `.playwright-mcp/*.log`, `*.yml` | Playwright session logs | ~2.8MB |
| `.agent/receipts/conflict-resolution-execution.md` | execution receipt | tiny |
| `projects/` | old-convention project workspaces | varies |
| `shared_studio/projects/` | current project workspaces | varies |
| `lib/__pycache__/` | compiled Python | ~80KB |
| `styles/__pycache__/` | compiled Python | tiny |

### 6B. Runtime artifacts in `remotion-composer/public/`

The debug and final MP4/WAV files in `remotion-composer/public/` are properly ignored but represent stale Phase 1A/1B debug renders. They take up ~1.9MB of disk space. Safe to delete locally after Phase 1B.3 render completes.

### 6C. `remotion-composer/public/source-commentary/` and `app-stores-choke-points/`

These subdirectories under `remotion-composer/public/` (covered by the `remotion-composer/public/*` ignore rule) appear to be copied project assets from render-time staging. They are properly ignored.

---

## 7. Local Config / Secrets Safety Findings

### 7A. `.env` — NOT TRACKED (properly ignored)

The `.env` file exists on disk with **real API keys** (RECRAFT, GOOGLE, ELEVENLABS, OPENROUTER). It is correctly excluded by `.gitignore` rule `*.env`. No action needed, but operator should ensure `.env` is not accidentally committed if `.gitignore` is modified.

Keys present in `.env`:
- `RECRAFT_API_TOKEN` — real key
- `GOOGLE_API_KEY` — real key
- `ELEVENLABS_API_KEY` — real key
- `OPENROUTER_API_KEY` — real key

### 7B. Machine-specific paths in TRACKED files (LOW severity)

These are not secrets, but they contain hardcoded filesystem paths that won't work on other machines:

| File | Path Found | Severity |
|------|-----------|----------|
| `channel.yaml` | `logo: /home/pop/Downloads/Asymmetriclogo.svg` | Medium — logo path won't resolve on CI or other machines |
| `channels/asymmetric/Strategy/Channel Strategy.md` | `/home/pop/OpenMontage-fresh` | Low — docs only, stale path |
| `tests/qa/QA_PLAN.md` | `cd C:/Users/ishan/Documents/OpenMontage` | Low — another dev's Windows path |
| `tests/eval/golden_scenarios/talking_head_basic.json` | `C:/Users/ishan/Documents/SocialMedia/...` | Medium — test fixture with Windows path, will break cross-platform test runs |

**`channel.yaml`** is loaded by agents at runtime. The hardcoded logo path should be made relative or moved to `config/asymmetric_local_tools.local.yaml` (already in .gitignore).

### 7C. `config/asymmetric_local_tools.example.yaml` — SAFE

The example config file contains no real credentials. The actual local file (`config/asymmetric_local_tools.local.yaml`) is properly ignored by .gitignore.

---

## 8. Large File Findings

| File | Size | Tracked? | Notes |
|------|------|----------|-------|
| `remotion-composer/node_modules/` | 663MB | No (ignored) | Normal npm install |
| `assets/showcase.jpg` | 272KB | Yes | Marketing asset, intentional |
| `assets/asymmetric-logo.png` | 224KB | Yes | Brand asset, intentional |
| `.claude/skills/vercel-react-best-practices/AGENTS.md` | 96KB | Yes | Duplicated in `.agents/skills/` |
| `.agents/skills/vercel-react-best-practices/AGENTS.md` | 96KB | Yes | Same file as above |
| `tools/video/video_compose.py` | 100KB | Yes | Large but legitimate |
| `remotion-composer/package-lock.json` | 108KB | Yes | Expected |
| `.claude/skills/flux-best-practices/AGENTS.md` | 56KB | Yes | Duplicated in `.agents/skills/` |
| `.agents/skills/flux-best-practices/AGENTS.md` | 56KB | Yes | Same file as above |
| `tests/tools/test_hyperframes_compose.py` | 48KB | Yes | Large test file |
| `tools/character/character_animation.py` | 40KB | Yes | Legitimate |
| `AGENT_GUIDE.md` | 40KB | Yes | Operational, intentional |

No tracked file exceeds the 50MB GitHub warning threshold. The binary assets (PNG, JPG) in `assets/` are intentional brand assets.

---

## 9. `.gitignore` Recommendations

### Currently missing rules

| Pattern | Reason | Priority |
|---------|---------|----------|
| `.codex/` | Empty Codex initialization dir, not needed in repo | Low |
| `remotion-composer/public/source-commentary/` | Render-time staged assets appear here | Medium |

### Current rules that look correct

All major artifact categories are correctly ignored:
- `__pycache__/`, `*.pyc` — Python bytecode
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` — test/lint caches
- `node_modules/` — npm deps
- `remotion-composer/out/`, `remotion-composer/public/*` — render output
- `shared_studio/projects/` — project workspaces
- `projects/` — old-convention workspaces
- `.env`, `*.env` — credentials
- `.gemini/`, `.playwright-mcp/` — runtime control-plane state
- `receipts/`, `runs/`, `tmp/` — runtime artifacts
- `.agent/receipts/`, `.agent/runs/`, etc. — agent runtime
- `config/asymmetric_local_tools.local.yaml` — machine-specific config

### Proposed additions to `.gitignore`

```gitignore
# Codex initialization directory (empty artifact)
.codex/

# Remotion staged source-commentary assets (copied at render time)
remotion-composer/public/source-commentary/
remotion-composer/public/app-stores-choke-points/
```

---

## 10. Cleanup Candidates Table

| # | Path | Label | Why | Confidence | Deletion Risk | Tracked? | Recovery |
|---|------|-------|-----|-----------|---------------|----------|---------|
| C1 | `.codex/` (empty dir) | DELETE_CANDIDATE | Empty Codex init artifact, never populated | High | None | No (empty dirs not tracked) | `mkdir .codex` |
| C2 | `docs/source-commentary-v0.1-checkpoint.md` | ARCHIVE_CANDIDATE | Superseded by v0.4 checkpoint; historical record only | High | Low | Yes | `git log` |
| C3 | `docs/source-commentary-v0.4-checkpoint.md` | ARCHIVE_CANDIDATE | Superseded by `docs/asymmetric/phase1_lessons.md` | High | Low | Yes | `git log` |
| C4 | `docs/stage-gates/.gitkeep` | DELETE_CANDIDATE | Empty placeholder dir, never populated; not referenced by any pipeline | Medium | None | Yes (`.gitkeep` only) | `mkdir -p docs/stage-gates && touch docs/stage-gates/.gitkeep` |
| C5 | `tests/qa/QA_PLAN.md` (Windows path) | KEEP_BUT_REVIEW | Contains `C:/Users/ishan/` path — not a delete, needs path fix | N/A | N/A | Yes | N/A |
| C6 | `tests/eval/golden_scenarios/talking_head_basic.json` (Windows path) | KEEP_BUT_REVIEW | Contains `C:/Users/ishan/` fixture path — needs path fix | N/A | N/A | Yes | N/A |
| C7 | `channel.yaml:logo` field | KEEP_BUT_REVIEW | Machine path `/home/pop/Downloads/...` — needs fix, not delete | N/A | N/A | Yes | N/A |
| C8 | `diagram.png` (root) | KEEP_BUT_REVIEW | Tracked binary at repo root; purpose unclear; may be architecture diagram for README | Low | Low | Yes | `git show HEAD:diagram.png` |
| C9 | `render_demo.py`, `render-demo.sh` | KEEP_BUT_REVIEW | Demo scripts at root; could move to `scripts/` for tidiness | Low | Low | Yes | `git log` |
| C10 | `PROMPT_GALLERY.md` | KEEP_BUT_REVIEW | Large doc (72KB); may be outdated relative to current skills/pipeline system | Low | Low | Yes | `git log` |

---

## 11. Archive Candidates Table

| Path | Why Archive | Last Meaningful Commit | Risk if Deleted |
|------|-------------|----------------------|-----------------|
| `docs/source-commentary-v0.1-checkpoint.md` | Phase 1A vertical slice record; superseded by phase1_lessons.md | May 4 | Lose Phase 1A checkpoint history (recoverable from git) |
| `docs/source-commentary-v0.4-checkpoint.md` | Phase 1B render checkpoint; superseded by phase1_lessons.md | May 4 | Lose Phase 1B checkpoint history (recoverable from git) |
| `docs/archive/DESIGN.cyber-noir.md` | Already in archive dir; visual identity concept that was not adopted | Initial release | None (already archived) |
| `channels/asymmetric/Topics/chip-factory-runs-world/` | Topic idea dir with only a README; may be superseded by production pipeline | May 1 | Lose one early topic note |
| `projects/app-stores-choke-points/` (untracked) | Pre-`shared_studio/` era workspace from Apr 30; early render artifacts | N/A (ignored) | Lose Phase 1A project artifacts (video renders, checkpoints) — NOT in git |
| `projects/fico-monopoly/` (untracked) | Early topic exploration workspace | N/A (ignored) | Lose early fico episode artifacts — NOT in git |
| `projects/_analysis/` (untracked) | 5 stale analysis subdirs from May 1 | N/A (ignored) | Lose analysis outputs — NOT in git |

**Note:** The `projects/` artifacts are not tracked by git. If deleted, they cannot be recovered from git. Operator must explicitly approve deletion of `projects/` contents.

---

## 12. Keep-But-Review Table

| Path | Issue | Recommended Action |
|------|-------|-------------------|
| `.agents/skills/` | Diverged from `.claude/skills/`; 502 files, 4.5MB; contains GSAP/hyperframes/comfyui skills not in `.claude/skills/` | Phase D: audit divergence, decide canonical registry, merge or document split ownership |
| `.claude/skills/` | Diverged from `.agents/skills/`; 432 files, 3.9MB; has Asymmetric skills not in `.agents/skills/` | Phase D: same as above |
| `channel.yaml` | `logo:` field contains `/home/pop/Downloads/Asymmetriclogo.svg` | Move logo path to `config/asymmetric_local_tools.local.yaml` or use relative path |
| `channels/asymmetric/Strategy/Channel Strategy.md` | Contains stale `/home/pop/OpenMontage-fresh` path | Update to current repo path or remove the path reference |
| `tests/qa/QA_PLAN.md` | Contains `C:/Users/ishan/` Windows path | Replace with placeholder or relative path |
| `tests/eval/golden_scenarios/talking_head_basic.json` | Contains `C:/Users/ishan/` Windows fixture path | Replace with relative path or environment variable |
| `diagram.png` | Root-level PNG binary; unclear if referenced in README or any doc | Check if still referenced; if not, move to `assets/` or remove |
| `render_demo.py`, `render-demo.sh` | Demo scripts at repo root | Consider moving to `scripts/` for structural consistency |
| `PROMPT_GALLERY.md` | 72KB doc; unclear if current relative to Phase 2S pipeline | Review for currency; archive or update |
| `.agent/allowed_paths.yaml`, `.agent/repo_policy.yaml` | Tracked runtime config for local agent; machine paths may be inside | Review for machine-specific content before sharing |
| `docs/stage-gates/.gitkeep` | Empty placeholder directory | Populate with content or remove with `.gitkeep` |
| `channels/asymmetric/Topics/chip-factory-runs-world/` | Single README, appears to be an early topic stub | Archive or remove if superseded by production pipeline |
| `channels/asymmetric/Templates/` | Channel-level templates; verify not duplicated by `templates/asymmetric/` | Cross-check with `templates/asymmetric/`; consolidate if overlapping |

---

## 13. Do Not Delete List

**These must not be deleted, moved, or modified without explicit operator approval:**

| Path | Reason |
|------|--------|
| `shared_studio/projects/app-store-leverage-p001/` | Active Phase 1B project workspace — current episode in production |
| `templates/asymmetric/` | All 15 production template files — actively used by subagents |
| `.claude/agents/` | All 6 subagent definitions — core production system |
| `.claude/commands/` | All 7 slash commands — core production workflow |
| `docs/asymmetric/` | All 8 docs — production doctrine, phase lessons, orchestration protocol |
| `channels/asymmetric/channel_profile.yaml` | Quality gates and pass/fail thresholds |
| `styles/asymmetric.yaml` | Visual playbook |
| `skills/pipelines/source-commentary/CONTRACT.md` | Evidence Lock contract — enforced by all agents |
| `pipeline_defs/source-commentary.yaml` | Active pipeline definition |
| `schemas/` | All schema files — artifact validation |
| `.env` | Real API keys on disk — do not commit, do not delete (needed for renders) |
| `projects/` contents | Untracked project artifacts — NOT in git; if deleted, gone forever |
| `remotion-composer/public/debug_clip.mp4` etc. | Phase 1B debug renders — needed for QC comparison until Phase 1B.3 completes |

---

## 14. Recommended Cleanup Plan

### Phase A — Safe ignore updates (no file deletion)

Add to `.gitignore`:
```gitignore
# Codex initialization directory (empty artifact)
.codex/

# Remotion staged project assets (copied at render time)
remotion-composer/public/source-commentary/
remotion-composer/public/app-stores-choke-points/
```

Risk: Zero. No tracked files affected.

### Phase B — Archive stale docs (after operator review)

1. Move `docs/source-commentary-v0.1-checkpoint.md` → `docs/archive/`
2. Move `docs/source-commentary-v0.4-checkpoint.md` → `docs/archive/`
3. Optionally: remove `docs/stage-gates/.gitkeep` if this dir will never be populated

Risk: Low. Files remain in git history.

### Phase C — Delete high-confidence junk (after operator approval)

1. Remove empty `.codex/` directory: `rmdir .codex`
2. Fix machine-specific paths in:
   - `channel.yaml:logo` field
   - `channels/asymmetric/Strategy/Channel Strategy.md`
   - `tests/qa/QA_PLAN.md`
   - `tests/eval/golden_scenarios/talking_head_basic.json`
3. After Phase 1B.3 render completes, operator may optionally clean `remotion-composer/public/debug_clip.mp4`, `debug_narration.wav`, `final_clip.mp4`, `final_narration.wav` (untracked, 1.9MB)
4. Operator decision: delete stale `projects/_analysis/`, `projects/app-stores-choke-points/`, `projects/fico-monopoly/` (untracked, irreversible)

Risk: Low for items 1-2. Medium for items 3-4 (unrecoverable from git).

### Phase D — Normalize duplicate control-plane paths

**Requires operator architectural decision:**

Option 1 — Claude Code as canonical:
- Merge GSAP suite, hyperframes, comfyui, grok-media skills from `.agents/skills/` into `.claude/skills/`
- Remove `.agents/skills/` from tracked files
- Add `.agents/skills/` to `.gitignore` if the external Claude Code CLI maintains it

Option 2 — Maintain split ownership with explicit documentation:
- Document that `.agents/skills/` is the generic OpenMontage registry (all agents)
- Document that `.claude/skills/` is the Claude Code fork (Claude-only + Asymmetric brand skills)
- Accept the ~71-skill overlap as intentional redundancy

Option 3 — `.agents/skills/` becomes the superset:
- Merge Asymmetric skills from `.claude/skills/` into `.agents/skills/`
- `.claude/skills/` becomes a symlink or is removed

**Do not execute Phase D without explicit operator decision.** This affects all production agents.

---

## 15. Operator Approvals Required Before Any Cleanup

| Action | Approval Required | Risk |
|--------|------------------|------|
| Add `.codex/` to `.gitignore` | Yes | None |
| Archive v0.1/v0.4 checkpoint docs | Yes | Low |
| Fix machine-specific paths in tracked files | Yes | Low |
| Remove `docs/stage-gates/.gitkeep` | Yes | None |
| Delete stale `projects/` workspaces (untracked) | **Explicit approval required** | Irreversible |
| Delete Phase 1B debug renders in `remotion-composer/public/` | Yes (after Phase 1B.3) | Low |
| Resolve `.agents/skills/` vs `.claude/skills/` divergence | **Explicit architectural decision required** | High if done wrong |
| Move `render_demo.py` and `render-demo.sh` to `scripts/` | Yes | Low |
| Commit any cleanup changes | Yes | Low |

---

*Audit complete. No files were modified, moved, deleted, or committed during this audit.*
