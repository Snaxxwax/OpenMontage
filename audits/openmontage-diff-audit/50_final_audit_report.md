# OpenMontage Fork Diff Audit

## Executive Summary

- original upstream repo: https://github.com/calesthio/OpenMontage.git
- upstream base used: \
- current branch: \
- origin remote: \
- current HEAD: \
- upstream HEAD: \
- merge base: \
- commits ahead of upstream: 1
- commits behind upstream: 7
- staged changes: 0 files
- unstaged changes: 8 files
- untracked files: 24 files
- total changed files vs upstream (committed): 87
- total working-tree changes (staged+unstaged+untracked): 32
- test status:
  - \Listing '.\\'...
Can't list '.\\': PASS
  - full \: HUNG / terminated (exit 143)
  - targeted contracts: PASS (see \)
  - \: **FAIL** (1 failing assertion)

### High-Risk Changes (Top)

- **HyperFramesCompose scaffold/render behavior** changed and currently breaks .
- **ComfyUI backend** adds a large new execution surface (local server dependency) and new tools.
- **Schema loosening** in  reduces validation strictness (higher chance of silent typos).

## What Actually Changed

### Pipelines
- , , : adds \ as an “also works” playbook.

### Skills
- Added/updated skills and assistant-facing guidance:
  - 
  -  (modified)
  -  (new)

### Playbooks
- Added playbooks:
  - 
  - , ,  (added in this fork diff)

### Schemas
- : adds  + .
- : makes playbooks more permissive (removes enums, allows extra fields, relaxes colors).

### Tools
- Added ComfyUI backend + provider tools:
  - , 
  -  ()
  -  ()
  -  ()
  -  ( legacy)
- Added Fish Speech provider:
  -  ()
- Significant modification:
  -  (large behavioral change; currently breaks a tool test)
- Other tool updates included in this fork diff (not exhaustive):
  - , , 
  - stock sources: , 

### Renderer / Composer
- Remotion-side files are present in the repo, but this fork diff’s primary render-runtime change is inside  and its routing via .

### Config
- , ,  changed.

### Docs
- , , , ,  changed.

### Tests
- Added/changed contracts:
  - 
  - 
  - 
- QA test changed:
  - 
- Tool test failing:
  - 

### Generated / Large Artifacts
- Added binary assets (examples): , , , .

## Legit Implemented Features

(Strict: code + wiring + verification path)

- **ComfyUI image/video providers** (, ): discoverable via , selectable via  / , contract tests pass.
- **Fish Speech TTS provider** (): discoverable via , selectable via , contract tests pass.

## Partial or Misleading Features

- **ComfyUI audio provider** (): implemented and discoverable, but there is no generic  in this repo; it requires explicit pipeline/stage usage.
- **Asymmetric channel strategy/templates** (, ): substantial documentation content but not runtime-enforced.
- **Schema loosening**: makes playbooks “work” with more shapes but increases silent-typo risk (a governance tradeoff).

## Hallucinated / Docs-Only Features

- No hard “HALLUCINATED” features were found in the committed diff for ComfyUI/Fish Speech.
- **However**, ’s docstring implies pipeline integration, but the repo has no call-sites — treat as **hallucination risk** until wired.

## Dead Code

- : no references found (manual utility only).
- , : appear to be manual utilities, not pipeline-invoked.

## Broken or Risky Changes

- : fails  (missing expected text content).
- Full ============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/pop/OpenMontage-fresh
plugins: langsmith-0.7.22, asyncio-1.3.0, cov-7.0.0, anyio-4.11.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 355 items

tests/contracts/test_comfyui_backend.py ..............                   [  3%]
tests/contracts/test_fish_speech_tts_contract.py ....                    [  5%]
tests/contracts/test_phase0_contracts.py ............................... [ 13%]
....                                                                     [ 14%]
tests/contracts/test_phase1_contracts.py ............................... [ 23%]
......................................                                   [ 34%]
tests/contracts/test_phase1_golden.py ...s                               [ 35%]
tests/contracts/test_phase2_comparison.py sssss                          [ 36%]
tests/contracts/test_phase2_contracts.py ............................... [ 45%]
..........................                                               [ 52%]
tests/contracts/test_phase3_contracts.py ............................... [ 61%]
.................................                                        [ 70%]
tests/contracts/test_runtime_presentation_contract.py .................. [ 76%]
......                                                                   [ 77%]
tests/qa/test_09_hyperframes_compose.py ss                               [ 78%]
tests/tools/test_clip_cache.py .......................                   [ 84%]
tests/tools/test_documentary_governance.py .......                       [ 86%]
tests/tools/test_hyperframes_compose.py ..............................F. [ 95%]
.........                                                                [ 98%]
tests/tools/test_stock_source_adapters.py ......                         [100%]

=================================== FAILURES ===================================
______________ test_scaffold_workspace_generates_html_and_assets _______________

tmp_path = PosixPath('/tmp/pytest-of-pop/pytest-4/test_scaffold_workspace_genera0')

    def test_scaffold_workspace_generates_html_and_assets(tmp_path: Path):
        # Build a minimal asset manifest + edit decisions referencing a real
        # file so the staging copy has something to move.
        asset = tmp_path / "hero.png"
        asset.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 1024)
    
        workspace = tmp_path / "hyperframes"
        edit_decisions: dict[str, Any] = {
            "version": "1.0",
            "renderer_family": "animation-first",
            "render_runtime": "hyperframes",
            "cuts": [
                {
                    "id": "c1",
                    "source": "asset_hero",
                    "in_seconds": 0,
                    "out_seconds": 3,
                    "type": "image",
                },
                {
                    "id": "c2",
                    "source": "",
                    "in_seconds": 3,
                    "out_seconds": 6,
                    "type": "text_card",
                    "text": "Hello HyperFrames",
                },
            ],
        }
        asset_manifest = {
            "assets": [{"id": "asset_hero", "path": str(asset)}],
        }
    
        result = HyperFramesCompose().execute(
            {
                "operation": "scaffold_workspace",
                "workspace_path": str(workspace),
                "edit_decisions": edit_decisions,
                "asset_manifest": asset_manifest,
                "playbook": {
                    "name": "test-playbook",
                    "visual_language": {
                        "color_palette": {
                            "background": "#0B0F1A",
                            "text": "#F5F5F5",
                            "accent": "#F59E0B",
                        }
                    },
                    "typography": {
                        "heading": {"font": "Inter"},
                        "body": {"font": "Inter"},
                    },
                },
            }
        )
    
        assert result.success, result.error
        index = workspace / "index.html"
        assert index.is_file()
        html = index.read_text(encoding="utf-8")
    
        # HyperFrames authoring contract requirements we MUST emit:
        assert 'data-composition-id="root"' in html
        assert 'window.__timelines["root"]' in html
        assert 'paused: true' in html
        assert 'class="clip' in html
        assert "gsap" in html.lower()
    
        # Text card for c2 must carry data-start and data-duration.
        assert 'data-start="3"' in html
>       assert 'Hello HyperFrames' in html
E       assert 'Hello HyperFrames' in '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n  <title>OpenMontage animation-first</title>\n  ...n: 0.5, ease: "power2.out" }, 0);\n      window.__timelines["root"] = tl;\n    </script>\n  </div>\n</body>\n</html>\n'

tests/tools/test_hyperframes_compose.py:948: AssertionError
=============================== warnings summary ===============================
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/matplotlib/_fontconfig_pattern.py:64: DeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/matplotlib/_fontconfig_pattern.py:85: DeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/matplotlib/_fontconfig_pattern.py:89: DeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/matplotlib/_mathtext.py:45: DeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/numba/np/ufunc/parallel.py:373: NumbaWarning: [1mThe TBB threading layer requires TBB version 2021 update 6 or later i.e., TBB_INTERFACE_VERSION >= 12060. Found TBB_INTERFACE_VERSION = 12050. The TBB threading layer is disabled.[0m
    warnings.warn(problem)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/tools/test_hyperframes_compose.py::test_scaffold_workspace_generates_html_and_assets
====== 1 failed, 346 passed, 8 skipped, 15 warnings in 266.00s (0:04:25) ======= run hung; targeted suites pass. This suggests at least one non-contract test (likely QA/E2E/eval) is slow or blocking in this environment.
- Working tree contains **uncommitted changes** in core tools (, ffmpeg-dependent tools, , etc.) which may create local-only behavior and “it works on my machine” drift.

## Top 10 Files to Manually Review First

1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 

## Recommended Next Actions

(Do not implement; investigation only.)

1. Identify which test(s) cause ........................................................................ [ 20%]
.....................................................ssssss............. [ 40%]
........................................................................ [ 60%]
............................................................ss.......... [ 81%]
..................................................F................      [100%]
=================================== FAILURES ===================================
______________ test_scaffold_workspace_generates_html_and_assets _______________

tmp_path = PosixPath('/tmp/pytest-of-pop/pytest-5/test_scaffold_workspace_genera0')

    def test_scaffold_workspace_generates_html_and_assets(tmp_path: Path):
        # Build a minimal asset manifest + edit decisions referencing a real
        # file so the staging copy has something to move.
        asset = tmp_path / "hero.png"
        asset.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 1024)
    
        workspace = tmp_path / "hyperframes"
        edit_decisions: dict[str, Any] = {
            "version": "1.0",
            "renderer_family": "animation-first",
            "render_runtime": "hyperframes",
            "cuts": [
                {
                    "id": "c1",
                    "source": "asset_hero",
                    "in_seconds": 0,
                    "out_seconds": 3,
                    "type": "image",
                },
                {
                    "id": "c2",
                    "source": "",
                    "in_seconds": 3,
                    "out_seconds": 6,
                    "type": "text_card",
                    "text": "Hello HyperFrames",
                },
            ],
        }
        asset_manifest = {
            "assets": [{"id": "asset_hero", "path": str(asset)}],
        }
    
        result = HyperFramesCompose().execute(
            {
                "operation": "scaffold_workspace",
                "workspace_path": str(workspace),
                "edit_decisions": edit_decisions,
                "asset_manifest": asset_manifest,
                "playbook": {
                    "name": "test-playbook",
                    "visual_language": {
                        "color_palette": {
                            "background": "#0B0F1A",
                            "text": "#F5F5F5",
                            "accent": "#F59E0B",
                        }
                    },
                    "typography": {
                        "heading": {"font": "Inter"},
                        "body": {"font": "Inter"},
                    },
                },
            }
        )
    
        assert result.success, result.error
        index = workspace / "index.html"
        assert index.is_file()
        html = index.read_text(encoding="utf-8")
    
        # HyperFrames authoring contract requirements we MUST emit:
        assert 'data-composition-id="root"' in html
        assert 'window.__timelines["root"]' in html
        assert 'paused: true' in html
        assert 'class="clip' in html
        assert "gsap" in html.lower()
    
        # Text card for c2 must carry data-start and data-duration.
        assert 'data-start="3"' in html
>       assert 'Hello HyperFrames' in html
E       assert 'Hello HyperFrames' in '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n  <title>OpenMontage animation-first</title>\n  ...n: 0.5, ease: "power2.out" }, 0);\n      window.__timelines["root"] = tl;\n    </script>\n  </div>\n</body>\n</html>\n'

tests/tools/test_hyperframes_compose.py:948: AssertionError
=============================== warnings summary ===============================
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/matplotlib/_fontconfig_pattern.py:64: DeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/matplotlib/_fontconfig_pattern.py:85: DeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/matplotlib/_fontconfig_pattern.py:89: DeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/matplotlib/_mathtext.py:45: DeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

tests/contracts/test_phase0_contracts.py::TestToolRegistry::test_support_envelope
  /home/pop/.local/lib/python3.10/site-packages/numba/np/ufunc/parallel.py:373: NumbaWarning: [1mThe TBB threading layer requires TBB version 2021 update 6 or later i.e., TBB_INTERFACE_VERSION >= 12060. Found TBB_INTERFACE_VERSION = 12050. The TBB threading layer is disabled.[0m
    warnings.warn(problem)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/tools/test_hyperframes_compose.py::test_scaffold_workspace_generates_html_and_assets
1 failed, 346 passed, 8 skipped, 15 warnings in 214.68s (0:03:34) to hang (start with  and ), and decide whether to gate them behind env vars/timeouts.
2. Fix or update  scaffold logic or the failing expectation in  (decide which behavior is intended).
3. Decide whether  should have a selector (or explicit pipeline integration) to avoid docs claiming it’s “supported” but never used.
4. Decide whether  should be wired into pipelines or explicitly documented as manual-only.
5. Reduce risk from uncommitted local changes by either committing them intentionally (with tests) or discarding them.

---

Supporting artifacts:
- Repo state: 
- Raw diff: 
- Inventory: 
- Feature audit: 
- Wiring audit: 
- Verification results: 
- Claims vs reality: 
