"""HyperFrames composition tool — HTML/CSS/GSAP render path.

Sibling to `video_compose` (FFmpeg + Remotion). This tool owns the HyperFrames
runtime end-to-end: workspace materialization, `hyperframes lint`,
`hyperframes validate`, and `hyperframes render`. It is invoked by
`video_compose` when `edit_decisions.render_runtime == "hyperframes"`, and
can also be called directly by pipelines that want HyperFrames-specific
operations (lint-only, validate-only, scaffold-only).

This tool deliberately does NOT attempt parity with every Remotion scene
component. See `skills/core/hyperframes.md` for what is in scope in Phase 1
and what remains Remotion-only.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ResumeSupport,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


log = logging.getLogger("hyperframes_compose")


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".gif"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}


class HyperFramesCompose(BaseTool):
    name = "hyperframes_compose"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "hyperframes"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:npx", "cmd:ffmpeg"]
    install_instructions = (
        "Requires Node.js >= 22 (https://nodejs.org/) and FFmpeg "
        "(https://ffmpeg.org/download.html). The HyperFrames CLI is fetched "
        "on first use via `npx hyperframes` (npm package: `hyperframes`). "
        "Note: the upstream monorepo develops the package as `@hyperframes/cli`, "
        "but it publishes to npm as `hyperframes`. `npx @hyperframes/cli` "
        "returns 404 -- do NOT use that form. Verify setup with "
        "`npx hyperframes doctor` or run the `doctor` operation on this tool."
    )
    agent_skills = [
        "hyperframes",
        "hyperframes-cli",
        "hyperframes-registry",
        "website-to-hyperframes",
        "gsap-core",
        "gsap-timeline",
    ]

    capabilities = [
        "hyperframes_render",
        "hyperframes_lint",
        "hyperframes_validate",
        "hyperframes_doctor",
        "scaffold_workspace",
        "add_block",
    ]

    best_for = [
        "HTML/CSS/GSAP composition: kinetic typography, product promos, launch reels",
        "Motion-graphics-heavy briefs where the scene library in remotion-composer/ doesn't fit",
        "Website-to-video / UI-driven compositions",
        "Registry-block-driven scenes (hyperframes add data-chart, grain-overlay, etc.)",
    ]
    not_good_for = [
        "Word-level caption burn (stays on Remotion in Phase 1)",
        "Avatar / lip-sync presenter (stays on Remotion in Phase 1)",
        "Existing React scene stack (text_card, stat_card, chart, comparison): reuse Remotion",
    ]
    fallback_tools = ["video_compose"]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "render",
                    "lint",
                    "validate",
                    "doctor",
                    "scaffold_workspace",
                    "add_block",
                ],
                "description": (
                    "render: materialize workspace + lint + validate + render to MP4. "
                    "lint: run `hyperframes lint` on an existing workspace. "
                    "validate: run `hyperframes validate` (browser-based). "
                    "doctor: run `hyperframes doctor` to check environment. "
                    "scaffold_workspace: materialize HTML/CSS/assets but do not render. "
                    "add_block: run `hyperframes add <name>` to install a registry "
                    "block or component into an existing workspace."
                ),
            },
            "block_name": {
                "type": "string",
                "description": (
                    "Registry block or component name for operation='add_block' "
                    "(e.g. 'data-chart', 'grain-overlay', 'shimmer-sweep'). "
                    "See https://hyperframes.heygen.com/catalog for the list."
                ),
            },
            "workspace_path": {
                "type": "string",
                "description": (
                    "Target HyperFrames workspace directory. Typically "
                    "`projects/<name>/hyperframes/`. Required for every op "
                    "except doctor."
                ),
            },
            "output_path": {
                "type": "string",
                "description": "Output MP4 path. Used by operation='render'.",
            },
            "edit_decisions": {
                "type": "object",
                "description": (
                    "Full edit_decisions artifact — required for render and "
                    "scaffold_workspace. Used to generate index.html + CSS."
                ),
            },
            "asset_manifest": {
                "type": "object",
                "description": (
                    "Full asset_manifest artifact — required for render and "
                    "scaffold_workspace. Used to resolve asset IDs to file paths."
                ),
            },
            "playbook": {
                "type": "object",
                "description": (
                    "Loaded playbook dict. Used to drive the style bridge "
                    "(CSS custom properties, typography, motion defaults)."
                ),
            },
            "profile": {
                "type": "string",
                "description": "Media profile name (youtube_landscape, tiktok_vertical, etc.).",
            },
            "quality": {
                "type": "string",
                "enum": ["draft", "standard", "high"],
                "default": "standard",
                "description": "Render quality. `draft` for iterating, `high` for delivery.",
            },
            "fps": {
                "type": "integer",
                "enum": [24, 30, 60],
                "default": 30,
            },
            "gpu": {
                "type": "string",
                "enum": ["auto", "on", "off"],
                "default": "auto",
                "description": (
                    "GPU-accelerated encoding during render. "
                    "`auto` enables it when NVENC is available."
                ),
            },
            "strict": {
                "type": "boolean",
                "default": False,
                "description": (
                    "If true, fail the render on any lint error. Matches "
                    "`hyperframes render --strict`."
                ),
            },
            "skip_contrast": {
                "type": "boolean",
                "default": False,
                "description": (
                    "Skip the WCAG contrast audit during validate. Acceptable "
                    "while iterating; forbidden for final delivery."
                ),
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=4, ram_mb=3072, vram_mb=0, disk_mb=2000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=0)
    resume_support = ResumeSupport.FROM_START
    idempotency_key_fields = ["operation", "workspace_path", "edit_decisions"]
    side_effects = [
        "writes HTML/CSS/JS files into workspace_path",
        "copies asset files into workspace_path/assets/",
        "writes MP4 to output_path",
    ]
    user_visible_verification = [
        "Play the rendered MP4 and verify scene pacing, typography, and audio",
        "Inspect workspace_path/index.html in a browser via `npx hyperframes preview`",
    ]

    # ------------------------------------------------------------------
    # Status / availability
    # ------------------------------------------------------------------

    _NODE_FLOOR_MAJOR = 22
    _NPM_PACKAGE = "hyperframes"  # published npm name (NOT @hyperframes/cli — that's 404)
    # Pin a known-good CLI version for deterministic, offline-friendly runs.
    # New npm releases occasionally appear briefly as metadata but fail to
    # resolve via npx in some environments; this fallback keeps renders stable.
    _NPM_FALLBACK_VERSION = "0.4.33"
    _nvenc_available_cache: Optional[bool] = None
    # Process-level cache for the npm resolve check. Shape:
    #   {"version": "0.4.5"}   → package resolves
    #   {"error": "<short>"}   → resolution failed (offline, unpublished, etc.)
    # We cache per-process so the first call pays ~2-5s and subsequent calls
    # (get_info spam from the registry) are free.
    _npm_resolve_cache: Optional[dict[str, str]] = None

    @classmethod
    def _node_major_version(cls) -> Optional[int]:
        """Return Node.js major version, or None if node isn't installed."""
        node = shutil.which("node")
        if not node:
            return None
        try:
            out = subprocess.run(
                [node, "--version"], capture_output=True, text=True, timeout=5
            )
            if out.returncode != 0:
                return None
            match = re.match(r"v?(\d+)\.", out.stdout.strip())
            if not match:
                return None
            return int(match.group(1))
        except (OSError, subprocess.SubprocessError):
            return None

    @classmethod
    def _nvenc_available(cls) -> bool:
        """Return True iff ffmpeg exposes NVENC encoders (h264_nvenc/hevc_nvenc)."""
        if cls._nvenc_available_cache is not None:
            return cls._nvenc_available_cache
        try:
            proc = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            hay = (proc.stdout or "") + "\n" + (proc.stderr or "")
            has_encoder = "h264_nvenc" in hay or "hevc_nvenc" in hay
            has_device = Path("/dev/nvidia0").exists() or Path("/dev/nvidiactl").exists()
            has_smi = False
            try:
                smi = subprocess.run(
                    ["nvidia-smi", "-L"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    check=False,
                )
                has_smi = smi.returncode == 0 and "GPU" in (smi.stdout or "")
            except FileNotFoundError:
                has_smi = False
            cls._nvenc_available_cache = bool(has_encoder and (has_device or has_smi))
        except Exception:
            cls._nvenc_available_cache = False
        return cls._nvenc_available_cache

    @classmethod
    def _should_use_gpu_encode(cls, gpu_setting: str | None) -> bool:
        setting = (gpu_setting or "auto").lower().strip()
        if setting == "off":
            return False
        if setting == "on":
            return True
        return cls._nvenc_available()

    @classmethod
    def _resolve_npm_package(cls) -> dict[str, str]:
        """Verify the `hyperframes` npm package actually resolves.

        Runtime availability must not depend on the public npm registry being
        reachable. If `npx hyperframes --version` works, we can render even
        when the machine is offline (npx cache already populated).

        We therefore try, in order:
        1) `npx --yes hyperframes --version` (local/cache check, 20s timeout)
        2) `npm view hyperframes version` (registry check, 5s timeout)

        Returns {"version": "X.Y.Z"} on success, {"error": "<short>"} on any
        failure (404, timeout, network error, npm missing). Never raises.
        """
        if cls._npm_resolve_cache is not None:
            return cls._npm_resolve_cache

        npx = shutil.which("npx")
        if npx:
            try:
                proc = subprocess.run(
                    [npx, "--yes", cls._NPM_PACKAGE, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if proc.returncode == 0:
                    version = ((proc.stdout or "") or (proc.stderr or "")).strip()
                    if version:
                        cls._npm_resolve_cache = {"version": version}
                        return cls._npm_resolve_cache
            except subprocess.TimeoutExpired:
                # Fall through to npm view.
                pass
            except (OSError, subprocess.SubprocessError):
                # Fall through to npm view.
                pass

        npm = shutil.which("npm")
        if not npm:
            cls._npm_resolve_cache = {"error": "npm not on PATH"}
            return cls._npm_resolve_cache

        try:
            proc = subprocess.run(
                [npm, "view", cls._NPM_PACKAGE, "version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            cls._npm_resolve_cache = {"error": "timeout (5s) — offline or slow registry"}
            return cls._npm_resolve_cache
        except (OSError, subprocess.SubprocessError) as e:
            cls._npm_resolve_cache = {"error": f"npm view failed: {type(e).__name__}"}
            return cls._npm_resolve_cache

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            # Most common failure is 404 (package unpublished or name wrong).
            if "404" in stderr or "E404" in stderr:
                cls._npm_resolve_cache = {
                    "error": f"npm package `{cls._NPM_PACKAGE}` not found (404)"
                }
            else:
                tail = stderr.splitlines()[-1][:200] if stderr else f"exit {proc.returncode}"
                cls._npm_resolve_cache = {"error": f"npm view failed: {tail}"}
            return cls._npm_resolve_cache

        version = (proc.stdout or "").strip()
        if not version:
            cls._npm_resolve_cache = {"error": "npm view returned empty version"}
        else:
            cls._npm_resolve_cache = {"version": version}
        return cls._npm_resolve_cache

    def _runtime_check(self) -> dict[str, Any]:
        """Return availability state for the HyperFrames runtime.

        Checks BOTH local binaries (node >= 22, ffmpeg, npx) AND that the
        `hyperframes` npm package actually resolves. A missing/404 package
        counts as unavailable — `runtime_available: True` means the runtime
        can genuinely run end-to-end, not just that the local tooling exists.
        """
        node_major = self._node_major_version()
        ffmpeg_ok = shutil.which("ffmpeg") is not None
        npx_ok = shutil.which("npx") is not None

        reasons: list[str] = []
        if node_major is None:
            reasons.append("node not found on PATH")
        elif node_major < self._NODE_FLOOR_MAJOR:
            reasons.append(
                f"node major version {node_major} < required {self._NODE_FLOOR_MAJOR}"
            )
        if not npx_ok:
            reasons.append("npx not found on PATH")
        if not ffmpeg_ok:
            reasons.append("ffmpeg not found on PATH")

        # Only probe npm if the local tooling is actually usable — otherwise
        # a missing-node run would also show a confusing npm error.
        npm_resolve: dict[str, str] = {}
        if not reasons:
            npm_resolve = self._resolve_npm_package()
            if "error" in npm_resolve:
                # Registry reachability should not be a hard blocker: machines can
                # be offline while still having a warm npx cache (or otherwise
                # be able to render). Only treat a hard 404 as unavailable.
                err = (npm_resolve.get("error") or "").lower()
                if "404" in err or "not found" in err or "e404" in err:
                    reasons.append(
                        f"npm package `{self._NPM_PACKAGE}` not resolvable: "
                        f"{npm_resolve['error']}"
                    )

        return {
            "runtime_available": not reasons,
            "node_major": node_major,
            "ffmpeg_available": ffmpeg_ok,
            "npx_available": npx_ok,
            "npm_package": self._NPM_PACKAGE,
            "npm_package_version": npm_resolve.get("version"),
            "npm_resolve_error": npm_resolve.get("error"),
            "reasons": reasons,
        }

    def get_status(self) -> ToolStatus:
        check = self._runtime_check()
        return ToolStatus.AVAILABLE if check["runtime_available"] else ToolStatus.UNAVAILABLE

    def get_info(self) -> dict[str, Any]:
        info = super().get_info()
        check = self._runtime_check()
        info["hyperframes_runtime"] = check
        if not check["runtime_available"]:
            info["setup_offer"] = {
                "effort": (
                    "1-minute fix"
                    if check["npx_available"] and check["ffmpeg_available"]
                    else "5-minute fix (install Node 22+ and/or FFmpeg)"
                ),
                "install_instructions": self.install_instructions,
                "unlocks": (
                    "HTML/CSS/GSAP composition runtime — kinetic typography, "
                    "product promos, registry blocks, website-to-video."
                ),
            }
        return info

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        ed = inputs.get("edit_decisions") or {}
        cuts = ed.get("cuts", [])
        total = 0.0
        for c in cuts:
            out_s = float(c.get("out_seconds", 0) or 0)
            in_s = float(c.get("in_seconds", 0) or 0)
            total += max(0.0, out_s - in_s)
        return 30.0 + total * 0.5

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs["operation"]
        start = time.time()
        try:
            if operation == "doctor":
                result = self._doctor(inputs)
            elif operation == "scaffold_workspace":
                result = self._scaffold(inputs)
            elif operation == "lint":
                result = self._lint(inputs)
            elif operation == "validate":
                result = self._validate(inputs)
            elif operation == "render":
                result = self._render(inputs)
            elif operation == "add_block":
                result = self._add_block(inputs)
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
        except Exception as e:
            log.exception("hyperframes_compose failed")
            return ToolResult(success=False, error=f"{type(e).__name__}: {e}")

        result.duration_seconds = round(time.time() - start, 2)
        return result

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def _doctor(self, inputs: dict[str, Any]) -> ToolResult:
        """Probe the environment. Reports node/ffmpeg/npx plus CLI doctor output."""
        check = self._runtime_check()
        out: dict[str, Any] = {"runtime_check": check}

        if not check["runtime_available"]:
            return ToolResult(
                success=False,
                error=(
                    "HyperFrames runtime floor not met: "
                    + "; ".join(check["reasons"])
                ),
                data=out,
            )

        # Ask the CLI itself for a deeper check. This also warms the npm
        # cache so the first real render doesn't pay the download cost.
        try:
            proc = self._run_hf(["doctor"], cwd=None, timeout=180, check=False)
            out["cli_doctor"] = {
                "exit_code": proc.returncode,
                "stdout_tail": (proc.stdout or "")[-4000:],
                "stderr_tail": (proc.stderr or "")[-4000:],
            }
            ok = proc.returncode == 0
            return ToolResult(
                success=ok,
                data=out,
                error=None if ok else f"hyperframes doctor exit {proc.returncode}",
            )
        except Exception as e:
            out["cli_doctor_error"] = str(e)
            return ToolResult(
                success=False,
                error=f"hyperframes doctor failed: {e}",
                data=out,
            )

    def _scaffold(self, inputs: dict[str, Any]) -> ToolResult:
        """Materialize the HyperFrames workspace from OpenMontage artifacts.

        This does NOT call `hyperframes init` — we want full control over the
        generated files so they map cleanly to edit_decisions. `init` is
        meant for humans bootstrapping a project by hand.
        """
        workspace = self._require_workspace(inputs)
        edit_decisions = inputs.get("edit_decisions") or {}
        asset_manifest = inputs.get("asset_manifest") or {}
        playbook = inputs.get("playbook") or {}
        profile_name = inputs.get("profile")

        if not edit_decisions.get("cuts"):
            return ToolResult(
                success=False,
                error="edit_decisions with non-empty cuts[] is required for scaffold_workspace",
            )

        width, height, fps = self._resolve_dimensions(profile_name, inputs.get("fps", 30))

        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "compositions").mkdir(exist_ok=True)
        assets_dir = workspace / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Resolve asset IDs → file paths + copy into workspace.
        resolved_cuts, asset_copies = self._resolve_and_stage_assets(
            edit_decisions.get("cuts", []),
            asset_manifest.get("assets", []),
            workspace,
        )

        audio_refs = self._resolve_audio_refs(
            edit_decisions.get("audio", {}),
            asset_manifest.get("assets", []),
            workspace,
        )

        # Style bridge: playbook → CSS custom properties + DESIGN.md.
        css_vars, design_md = self._style_bridge(playbook, edit_decisions)

        # Optional: enrich with the project's scene_plan (for better-than-text-card
        # defaults). This keeps the render usable even when edit_decisions.cuts
        # are minimal placeholders.
        scene_plan_scenes = self._load_project_scene_plan(edit_decisions)
        compositions_written = self._write_auto_compositions(
            workspace=workspace,
            cuts=resolved_cuts,
            scene_plan_scenes=scene_plan_scenes,
            css_vars=css_vars,
        )

        # Write hyperframes.json (registry config).
        (workspace / "hyperframes.json").write_text(
            json.dumps(
                {
                    "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
                    "paths": {
                        "blocks": "compositions",
                        "components": "compositions/components",
                        "assets": "assets",
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # Write DESIGN.md (convenience file for human review + workspace context).
        if design_md:
            (workspace / "DESIGN.md").write_text(design_md, encoding="utf-8")

        # Write index.html — the main composition.
        total_duration = self._compute_total_duration(resolved_cuts)
        html = self._generate_index_html(
            cuts=resolved_cuts,
            audio_refs=audio_refs,
            width=width,
            height=height,
            total_duration=total_duration,
            css_vars=css_vars,
            title=edit_decisions.get("metadata", {}).get("title")
            or f"OpenMontage {edit_decisions.get('renderer_family', 'composition')}",
        )
        (workspace / "index.html").write_text(html, encoding="utf-8")

        return ToolResult(
            success=True,
            data={
                "operation": "scaffold_workspace",
                "workspace": str(workspace),
                "width": width,
                "height": height,
                "fps": fps,
                "total_duration_seconds": total_duration,
                "cut_count": len(resolved_cuts),
                "asset_copies": asset_copies,
                "compositions_written": compositions_written,
            },
            artifacts=[str(workspace / "index.html")],
        )

    def _lint(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._require_workspace(inputs)
        if not (workspace / "index.html").exists():
            return ToolResult(
                success=False,
                error=f"No index.html in {workspace}. Run scaffold_workspace first.",
            )
        proc = self._run_hf(["lint", "--json"], cwd=workspace, timeout=120, check=False)
        data: dict[str, Any] = {"exit_code": proc.returncode}
        payload = self._parse_json_output(proc.stdout)
        if payload is not None:
            data["report"] = payload
        else:
            data["stdout_tail"] = (proc.stdout or "")[-4000:]
        data["stderr_tail"] = (proc.stderr or "")[-2000:]
        ok = proc.returncode == 0
        return ToolResult(
            success=ok,
            data=data,
            error=None if ok else f"hyperframes lint exit {proc.returncode}",
        )

    def _validate(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._require_workspace(inputs)
        if not (workspace / "index.html").exists():
            return ToolResult(
                success=False,
                error=f"No index.html in {workspace}. Run scaffold_workspace first.",
            )
        args = ["validate", "--json"]
        if inputs.get("skip_contrast"):
            args.append("--no-contrast")
        proc = self._run_hf(args, cwd=workspace, timeout=300, check=False)
        data: dict[str, Any] = {"exit_code": proc.returncode}
        payload = self._parse_json_output(proc.stdout)
        if payload is not None:
            data["report"] = payload
        else:
            data["stdout_tail"] = (proc.stdout or "")[-4000:]
        data["stderr_tail"] = (proc.stderr or "")[-2000:]
        ok = proc.returncode == 0
        return ToolResult(
            success=ok,
            data=data,
            error=None if ok else f"hyperframes validate exit {proc.returncode}",
        )

    def _add_block(self, inputs: dict[str, Any]) -> ToolResult:
        """Install a registry block or component via `hyperframes add`.

        Blocks are standalone sub-compositions (own dimensions, duration, timeline)
        that land at `compositions/<name>.html`. Components are effect snippets
        that land at `compositions/components/<name>.html`. After install, the
        caller is responsible for wiring the block into `index.html` via
        `data-composition-src` or pasting the component's snippet — see
        `.agents/skills/hyperframes-registry/SKILL.md`.
        """
        workspace = self._require_workspace(inputs)
        block = (inputs.get("block_name") or "").strip()
        if not block:
            return ToolResult(
                success=False,
                error="block_name is required for operation='add_block'",
            )
        if not workspace.exists():
            return ToolResult(
                success=False,
                error=(
                    f"Workspace {workspace} does not exist. Run "
                    "operation='scaffold_workspace' first."
                ),
            )
        args = ["add", block, "--json", "--no-clipboard"]
        proc = self._run_hf(args, cwd=workspace, timeout=300, check=False)
        data: dict[str, Any] = {
            "operation": "add_block",
            "block_name": block,
            "workspace": str(workspace),
            "exit_code": proc.returncode,
        }
        payload = self._parse_json_output(proc.stdout)
        if payload is not None:
            data["report"] = payload
        else:
            data["stdout_tail"] = (proc.stdout or "")[-4000:]
        data["stderr_tail"] = (proc.stderr or "")[-2000:]
        ok = proc.returncode == 0
        return ToolResult(
            success=ok,
            data=data,
            error=None if ok else f"hyperframes add {block} exit {proc.returncode}",
        )

    def _render(self, inputs: dict[str, Any]) -> ToolResult:
        """Full pipeline: scaffold → lint → validate → render."""
        runtime_ok = self._runtime_check()
        if not runtime_ok["runtime_available"]:
            return ToolResult(
                success=False,
                error=(
                    "HyperFrames runtime not available: "
                    + "; ".join(runtime_ok["reasons"])
                    + ". Per governance, this is a blocker — do NOT silently "
                    "fall back to another runtime without user approval."
                ),
                data={"runtime_check": runtime_ok},
            )

        workspace = self._require_workspace(inputs)
        # HyperFrames is invoked with cwd=workspace. If we pass a relative
        # output path, HyperFrames will write it relative to the workspace,
        # while our post-checks (and callers like video_compose) expect the
        # path relative to the repo cwd. Normalize to an absolute path.
        raw_output = inputs.get("output_path") or (workspace / "renders" / "final.mp4")
        output_path = Path(raw_output).expanduser()
        if not output_path.is_absolute():
            output_path = (Path.cwd() / output_path).resolve()
        else:
            output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        steps: dict[str, Any] = {}

        # 1. Scaffold — generate HTML/CSS/assets.
        scaffold = self._scaffold(inputs)
        steps["scaffold"] = scaffold.data
        if not scaffold.success:
            return ToolResult(
                success=False,
                error=f"Scaffold failed: {scaffold.error}",
                data={"steps": steps},
            )

        # 2. Lint — static contract checks.
        lint = self._lint({"workspace_path": str(workspace)})
        steps["lint"] = lint.data
        if not lint.success:
            if inputs.get("strict", False):
                return ToolResult(
                    success=False,
                    error=f"Lint failed (strict mode): {lint.error}",
                    data={"steps": steps},
                )
            log.warning("hyperframes lint reported issues (non-strict mode, continuing)")

        # 3. Validate — browser-based contract + contrast.
        validate = self._validate(
            {
                "workspace_path": str(workspace),
                "skip_contrast": inputs.get("skip_contrast", False),
            }
        )
        steps["validate"] = validate.data
        if not validate.success:
            return ToolResult(
                success=False,
                error=(
                    f"Validate failed: {validate.error}. HyperFrames render "
                    f"is blocked — fix the composition and re-run."
                ),
                data={"steps": steps},
            )

        # 4. Render.
        width, height, fps = self._resolve_dimensions(
            inputs.get("profile"), inputs.get("fps", 30)
        )
        quality = inputs.get("quality", "standard")
        args = [
            "render",
            "--output", str(output_path),
            "--fps", str(fps),
            "--quality", quality,
        ]
        use_gpu_encode = self._should_use_gpu_encode(inputs.get("gpu"))
        if use_gpu_encode:
            args.append("--gpu")
        # Rendering time scales with duration. The previous fixed 30 minute
        # timeout is too short for full-length episodes and causes false
        # failures. Allow an explicit override, otherwise compute a
        # duration-based ceiling with a conservative multiplier.
        render_timeout = (
            inputs.get("render_timeout_seconds")
            or inputs.get("timeout_seconds")
        )
        if not render_timeout:
            total_seconds = 0.0
            try:
                cuts = (inputs.get("edit_decisions") or {}).get("cuts") or []
                if cuts:
                    total_seconds = max(float(c.get("out_seconds", 0.0) or 0.0) for c in cuts)
            except Exception:
                total_seconds = 0.0
            # Default: 6x realtime + 10 min overhead, min 30 min, max 4 hours.
            render_timeout = int(max(1800, (total_seconds * 6.0) + 600.0))
            render_timeout = min(int(render_timeout), 4 * 60 * 60)

        proc = self._run_hf(args, cwd=workspace, timeout=int(render_timeout), check=False)
        steps["render"] = {
            "exit_code": proc.returncode,
            "gpu_encode": use_gpu_encode,
            "timeout_seconds": int(render_timeout),
            "stdout_tail": (proc.stdout or "")[-4000:],
            "stderr_tail": (proc.stderr or "")[-4000:],
        }
        if proc.returncode != 0:
            return ToolResult(
                success=False,
                error=f"hyperframes render exit {proc.returncode}",
                data={"steps": steps},
            )

        if not output_path.exists():
            return ToolResult(
                success=False,
                error=(
                    f"hyperframes render exited 0 but output file missing: "
                    f"{output_path}. Check stdout_tail for the real path."
                ),
                data={"steps": steps},
            )

        return ToolResult(
            success=True,
            data={
                "operation": "render",
                "output": str(output_path),
                "workspace": str(workspace),
                "width": width,
                "height": height,
                "fps": fps,
                "quality": quality,
                "steps": steps,
            },
            artifacts=[str(output_path)],
        )

    # ------------------------------------------------------------------
    # Workspace generation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_workspace(inputs: dict[str, Any]) -> Path:
        raw = inputs.get("workspace_path")
        if not raw:
            raise ValueError("workspace_path is required for this operation")
        return Path(raw).resolve()

    @staticmethod
    def _resolve_dimensions(
        profile_name: Optional[str], fps_in: int
    ) -> tuple[int, int, int]:
        """Resolve output dimensions from the media profile, with a safe default."""
        if profile_name:
            try:
                from lib.media_profiles import get_profile  # type: ignore
                p = get_profile(profile_name)
                return int(p.width), int(p.height), int(p.fps)
            except Exception:
                pass
        return 1920, 1080, int(fps_in)

    @staticmethod
    def _compute_total_duration(cuts: list[dict]) -> float:
        if not cuts:
            return 0.0
        return max(float(c.get("out_seconds", 0) or 0) for c in cuts)

    def _resolve_and_stage_assets(
        self,
        cuts: list[dict],
        assets: list[dict],
        workspace: Path,
    ) -> tuple[list[dict], list[dict[str, str]]]:
        """Resolve asset IDs in cuts[].source, copy files into workspace/assets/.

        HyperFrames resolves `src=` relative to the composition HTML file, so
        every asset must live inside the workspace tree. Copying is simpler
        (and portable) than symlinking, at the cost of disk space — these
        are regenerable under `projects/`.
        """
        asset_lookup = {a["id"]: a for a in assets if "id" in a}
        assets_dir = workspace / "assets"
        copies: list[dict[str, str]] = []
        resolved: list[dict] = []
        for cut in cuts:
            source = cut.get("source", "")
            resolved_cut = dict(cut)
            if source in asset_lookup:
                resolved_cut["source"] = asset_lookup[source].get("path", source)
            src_path = Path(resolved_cut["source"]) if resolved_cut.get("source") else None
            if src_path and src_path.exists() and not self._is_inside(src_path, workspace):
                dest = assets_dir / src_path.name
                if not dest.exists() or dest.stat().st_size != src_path.stat().st_size:
                    shutil.copy2(src_path, dest)
                resolved_cut["source"] = str(dest)
                copies.append({"from": str(src_path), "to": str(dest)})
            resolved.append(resolved_cut)
        return resolved, copies

    def _resolve_audio_refs(
        self,
        audio: dict[str, Any],
        assets: list[dict],
        workspace: Path,
    ) -> dict[str, Any]:
        """Resolve narration / music asset IDs and stage them."""
        asset_lookup = {a["id"]: a for a in assets if "id" in a}
        assets_dir = workspace / "assets"
        out: dict[str, Any] = {"narration": [], "music": None}

        for seg in audio.get("narration", {}).get("segments", []) or []:
            aid = seg.get("asset_id")
            if not aid or aid not in asset_lookup:
                continue
            src = Path(asset_lookup[aid].get("path", ""))
            if not src.exists():
                continue
            if not self._is_inside(src, workspace):
                dest = assets_dir / src.name
                if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                    shutil.copy2(src, dest)
            else:
                dest = src
            out["narration"].append(
                {
                    "src": str(dest),
                    "start_seconds": float(seg.get("start_seconds", 0) or 0),
                    "end_seconds": float(seg.get("end_seconds", 0) or 0) or None,
                }
            )

        music = audio.get("music", {})
        m_id = music.get("asset_id")
        if m_id and m_id in asset_lookup:
            src = Path(asset_lookup[m_id].get("path", ""))
            if src.exists():
                if not self._is_inside(src, workspace):
                    dest = assets_dir / src.name
                    if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                        shutil.copy2(src, dest)
                else:
                    dest = src
                out["music"] = {
                    "src": str(dest),
                    "volume": float(music.get("volume", 0.15) or 0.15),
                    "fade_in_seconds": float(music.get("fade_in_seconds", 0) or 0),
                    "fade_out_seconds": float(music.get("fade_out_seconds", 0) or 0),
                }

        return out

    @staticmethod
    def _is_inside(path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except ValueError:
            return False

    def _style_bridge(
        self,
        playbook: dict[str, Any],
        edit_decisions: dict[str, Any],
    ) -> tuple[dict[str, str], str]:
        """Bridge OpenMontage playbook → HyperFrames CSS vars + DESIGN.md.

        Delegates to `lib/hyperframes_style_bridge.py` so the logic is
        shareable and testable. Falls back to a safe built-in default when
        the bridge module isn't available.
        """
        try:
            from lib.hyperframes_style_bridge import style_bridge  # type: ignore
            return style_bridge(playbook, edit_decisions)
        except Exception as e:
            log.debug("style_bridge fallback: %s", e)

        vl = (playbook or {}).get("visual_language", {})
        palette = vl.get("color_palette", {})
        typo = (playbook or {}).get("typography", {})

        def _first(raw: Any, default: str) -> str:
            if isinstance(raw, list) and raw:
                return str(raw[0])
            if isinstance(raw, str) and raw:
                return raw
            return default

        bg = _first(palette.get("background"), "#0B0F1A")
        fg = _first(palette.get("text"), "#F5F5F5")
        accent = _first(palette.get("accent"), "#F59E0B")
        primary = _first(palette.get("primary"), "#2563EB")
        heading = typo.get("heading", {}).get("font") or typo.get("heading", {}).get("family") or "Inter"
        body = typo.get("body", {}).get("font") or typo.get("body", {}).get("family") or "Inter"

        css_vars = {
            "--color-bg": bg,
            "--color-fg": fg,
            "--color-accent": accent,
            "--color-primary": primary,
            "--font-heading": heading,
            "--font-body": body,
            "--ease-primary": "cubic-bezier(0.65, 0, 0.35, 1)",
            "--duration-entrance": "0.6s",
        }
        design_md = (
            "# DESIGN\n\n"
            "Generated by OpenMontage HyperFrames style bridge (fallback).\n\n"
            f"- Background: `{bg}`\n"
            f"- Foreground: `{fg}`\n"
            f"- Accent: `{accent}`\n"
            f"- Primary: `{primary}`\n"
            f"- Heading font: `{heading}`\n"
            f"- Body font: `{body}`\n"
        )
        return css_vars, design_md

    def _load_project_scene_plan(self, edit_decisions: dict[str, Any]) -> list[dict[str, Any]]:
        """Best-effort load of the project's scene_plan for richer scaffolding.

        This tool is used in compose-time generation; keep it best-effort and
        never block rendering if the file isn't present.
        """
        project_id = (edit_decisions.get("metadata") or {}).get("project_id") or edit_decisions.get("project_id")
        if not project_id or not isinstance(project_id, str):
            return []
        path = Path("projects") / project_id / "artifacts" / "scene_plan.json"
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            scenes = data.get("scenes")
            if isinstance(scenes, list):
                return [s for s in scenes if isinstance(s, dict)]
        except Exception:
            return []
        return []

    def _write_auto_compositions(
        self,
        *,
        workspace: Path,
        cuts: list[dict],
        scene_plan_scenes: list[dict[str, Any]],
        css_vars: dict[str, str],
    ) -> list[str]:
        """Generate per-scene sub-compositions under workspace/compositions/.

        The goal is to avoid rendering an entire episode as centered text cards.
        Compositions are generated from scene_plan where possible, otherwise
        they fall back to a consistent kinetic-typography default.
        """
        comp_dir = workspace / "compositions"
        comp_dir.mkdir(exist_ok=True)
        by_id = {s.get("id"): s for s in (scene_plan_scenes or []) if isinstance(s, dict) and s.get("id")}

        written: list[str] = []
        for cut in cuts:
            scene_id = (cut.get("id") or "").strip()
            if not scene_id:
                continue
            scene = by_id.get(scene_id) or {}
            html = self._generate_scene_composition(scene_id=scene_id, cut=cut, scene=scene, css_vars=css_vars)
            (comp_dir / f"{scene_id}.html").write_text(html, encoding="utf-8")
            written.append(scene_id)
        return written

    def _generate_scene_composition(
        self,
        *,
        scene_id: str,
        cut: dict[str, Any],
        scene: dict[str, Any],
        css_vars: dict[str, str],
    ) -> str:
        """Generate a HyperFrames sub-composition (template-wrapped)."""
        bg = css_vars.get("--color-bg", "#050608")
        fg = css_vars.get("--color-fg", "#F3F5F7")
        accent = css_vars.get("--color-accent", "#F5A400")  # amber
        primary = css_vars.get("--color-primary", "#3F8FA3")  # cyan

        # House palette used throughout this episode.
        slate = "#11151C"
        steel = "#8A95A6"
        graphite = "#2A3142"
        red = "#F04A3A"

        stype = (scene.get("type") or "").strip().lower()
        desc = (scene.get("description") or "").strip()
        text = (cut.get("reason") or "").strip()

        def _wrap(inner: str, css: str, js: str) -> str:
            dur_s = max(
                0.1,
                float(cut.get("out_seconds", 0) or 0) - float(cut.get("in_seconds", 0) or 0),
            )
            return f"""<template id="{scene_id}-template">
  <div data-composition-id="{self._escape_attr(scene_id)}" data-start="0" data-duration="{self._f(dur_s)}" data-width="1920" data-height="1080">
    {inner}
    <style>
      [data-composition-id="{self._escape_attr(scene_id)}"] {{
        position: relative;
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        background: {bg};
        color: {fg};
        font-family: Inter, Arial, sans-serif;
      }}
      {css}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {js}
      window.__timelines[{json.dumps(scene_id)}] = tl;
    </script>
  </div>
</template>
"""

        # ------------------------------------------------------------------
        # Per-scene templates (episode-specific)
        # ------------------------------------------------------------------
        if scene_id in {"sc03", "sc07", "sc10", "sc15", "sc19", "sc24"}:
            title = desc.split("—", 1)[0].strip() if desc else scene_id.upper()
            # Prefer quoted title for chapter cards.
            if ":" in desc:
                # e.g. Chapter card: 'THE SURFACE STORY'
                import re
                m = re.search(r"'([^']+)'", desc)
                if m:
                    title = m.group(1)
            inner = f'<div class="chapter"><div class="label">{self._escape_text(title)}</div></div>'
            css = f"""
      .chapter {{
        position: absolute; inset: 0;
        background: {slate};
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      .label {{
        color: {accent};
        font-family: \"Space Grotesk\", Inter, Arial, sans-serif;
        font-weight: 700;
        letter-spacing: 0.06em;
        font-size: 96px;
      }}
      .label::after {{
        content: \"\";
        display: block;
        width: 240px;
        height: 3px;
        background: {accent};
        margin: 28px auto 0;
        opacity: 0.8;
      }}
"""
            js = "tl.from('.label', { y: 18, opacity: 0, duration: 0.35, ease: 'power2.out' }, 0);"
            return _wrap(inner, css, js)

        if scene_id == "sc01":
            clauses = [
                "The most advanced chips in the world —",
                "all come from one company.",
                "One factory.",
                "One island.",
            ]
            inner = (
                '<div class="coldopen">'
                + "".join(f'<div class="clause" id="c{i}">{self._escape_text(t)}</div>' for i, t in enumerate(clauses))
                + "</div>"
            )
            css = f"""
      .coldopen {{
        position: absolute; inset: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 160px 180px;
        gap: 26px;
      }}
      .clause {{
        font-size: 72px;
        font-weight: 400;
        letter-spacing: 0.02em;
        opacity: 0;
      }}
"""
            js_lines = []
            t = 0.0
            for i in range(len(clauses)):
                js_lines.append(f"tl.to('#c{i}', {{ opacity: 1, duration: 0.25, ease: 'power1.out' }}, {t});")
                js_lines.append(f"tl.to('#c{i}', {{ opacity: 0.45, duration: 0.25, ease: 'power1.out' }}, {t + 1.6});")
                t += 2.0
            js = "\n      ".join(js_lines)
            return _wrap(inner, css, js)

        if scene_id == "sc02":
            # Wafer hero (ported from assets/scenes/sc02-wafer-hero.html).
            inner = """
    <div id="scene">
      <div id="wafer-wrap">
        <svg viewBox="0 0 900 900" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <clipPath id="wafer-clip"><circle cx="450" cy="450" r="430"/></clipPath>
            <radialGradient id="wafer-grad" cx="45%" cy="45%" r="55%">
              <stop offset="0%"  stop-color="#2A3142"/>
              <stop offset="60%" stop-color="#11151C"/>
              <stop offset="100%" stop-color="#050608"/>
            </radialGradient>
          </defs>
          <circle cx="450" cy="450" r="430" fill="url(#wafer-grad)" stroke="#2A3142" stroke-width="1.5"/>
          <g clip-path="url(#wafer-clip)" opacity="0.18" stroke="#3F8FA3" stroke-width="0.7" fill="none">
            <line x1="20" y1="90"  x2="880" y2="90"/><line x1="20" y1="150" x2="880" y2="150"/><line x1="20" y1="210" x2="880" y2="210"/>
            <line x1="20" y1="270" x2="880" y2="270"/><line x1="20" y1="330" x2="880" y2="330"/><line x1="20" y1="390" x2="880" y2="390"/>
            <line x1="20" y1="450" x2="880" y2="450"/><line x1="20" y1="510" x2="880" y2="510"/><line x1="20" y1="570" x2="880" y2="570"/>
            <line x1="20" y1="630" x2="880" y2="630"/><line x1="20" y1="690" x2="880" y2="690"/><line x1="20" y1="750" x2="880" y2="750"/>
            <line x1="90"  y1="20" x2="90"  y2="880"/><line x1="150" y1="20" x2="150" y2="880"/><line x1="210" y1="20" x2="210" y2="880"/>
            <line x1="270" y1="20" x2="270" y2="880"/><line x1="330" y1="20" x2="330" y2="880"/><line x1="390" y1="20" x2="390" y2="880"/>
            <line x1="450" y1="20" x2="450" y2="880"/><line x1="510" y1="20" x2="510" y2="880"/><line x1="570" y1="20" x2="570" y2="880"/>
            <line x1="630" y1="20" x2="630" y2="880"/><line x1="690" y1="20" x2="690" y2="880"/><line x1="750" y1="20" x2="750" y2="880"/>
          </g>
        </svg>
      </div>

      <svg id="catchlight" viewBox="0 0 900 900" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="amber-glow" cx="50%" cy="40%" r="50%">
            <stop offset="0%" stop-color="#F5A400" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="#F5A400" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <ellipse id="catchlight-ellipse" cx="330" cy="280" rx="240" ry="180" fill="url(#amber-glow)"/>
      </svg>

      <div class="overlay-text" id="text-no-backup">There is no backup.</div>
      <div class="overlay-text" id="text-supply-chain">the most critical supply chain in the global economy</div>
    </div>
"""
            css = f"""
      #scene {{ position: relative; width: 1920px; height: 1080px; }}
      #wafer-wrap {{
        position: absolute; left: 140px; top: 90px;
        width: 900px; height: 900px;
        opacity: 0;
        transform-origin: center center;
      }}
      #catchlight {{
        position: absolute; left: 140px; top: 90px;
        width: 900px; height: 900px;
        pointer-events: none;
      }}
      #catchlight-ellipse {{ opacity: 0; }}
      .overlay-text {{
        position: absolute;
        right: 120px;
        color: {fg};
        font-size: 52px;
        font-weight: 300;
        letter-spacing: 0.04em;
        line-height: 1.3;
        max-width: 720px;
        text-align: right;
        opacity: 0;
        transform: translateY(8px);
      }}
      #text-no-backup {{ top: 320px; }}
      #text-supply-chain {{ top: 440px; font-size: 38px; color: {steel}; letter-spacing: 0.06em; }}
"""
            js = """
      const root = document.querySelector('[data-composition-id="sc02"]');
      const totalDuration = parseFloat(root?.getAttribute('data-duration') || '30');
      const cycle = 3;
      const repeats = Math.max(0, Math.floor((totalDuration - 1.3) / cycle) - 1);

      tl.to("#wafer-wrap", { opacity: 1, duration: 1.6, ease: "power2.out" }, 0)
        .to("#wafer-wrap", { scale: 1.03, duration: 22, ease: "none", transformOrigin: "center center" }, 0)
        .to("#catchlight-ellipse", { opacity: 1, duration: 1.0, ease: "power1.in" }, 1.0)
        .to("#catchlight-ellipse", { attr: { cx: 560, cy: 500 }, duration: 3, ease: "sine.inOut", repeat: repeats, yoyo: true }, 1.3)
        .to("#text-no-backup", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 6.0)
        .to("#text-no-backup", { opacity: 0.45, duration: 0.35, ease: "power1.out" }, 10.0)
        .to("#text-supply-chain", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 14.0);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc04":
            inner = """
    <div class="wrap">
      <div class="row">
        <div class="box" id="b0">Apple</div>
        <div class="box" id="b1">NVIDIA</div>
        <div class="box" id="b2">AMD</div>
        <div class="box" id="b3">Qualcomm</div>
        <div class="box" id="b4">Broadcom</div>
      </div>
      <div class="label">Fabless — Design Only</div>
    </div>
"""
            css = f"""
      .wrap {{ position: absolute; inset: 0; display:flex; flex-direction:column; justify-content:center; gap: 42px; padding: 140px 160px; }}
      .row {{ display:flex; gap: 22px; flex-wrap: wrap; }}
      .box {{
        width: 320px; height: 96px;
        border: 2px solid {accent};
        background: rgba(17, 21, 28, 0.55);
        display:flex; align-items:center; justify-content:center;
        font-size: 34px; letter-spacing: 0.05em;
        opacity: 0; transform: translateY(10px);
      }}
      .label {{
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 20px; letter-spacing: 0.12em;
        color: {steel};
        text-transform: uppercase;
        opacity: 0;
      }}
"""
            js = """
      tl.to(["#b0","#b1","#b2","#b3","#b4"], { opacity: 1, y: 0, duration: 0.35, stagger: 0.30, ease: "power2.out" }, 0)
        .to(".label", { opacity: 1, duration: 0.45, ease: "power1.out" }, 1.9);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc05":
            # EUV machine (ported; minimal, interface-driven).
            # Keep it abstract; cyan beam to amber dot + stat card.
            inner = """
    <div id="scene">
      <svg id="svg" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="steelGrad" x1="0" x2="1">
            <stop offset="0" stop-color="#11151C"/>
            <stop offset="1" stop-color="#050608"/>
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="1920" height="1080" fill="url(#steelGrad)"/>
        <rect x="220" y="220" width="900" height="560" rx="14" fill="rgba(17,21,28,0.65)" stroke="#2A3142" stroke-width="2"/>
        <rect x="280" y="280" width="360" height="200" rx="10" fill="rgba(5,6,8,0.55)" stroke="#2A3142" stroke-width="1.5"/>
        <rect x="680" y="280" width="380" height="200" rx="10" fill="rgba(5,6,8,0.55)" stroke="#2A3142" stroke-width="1.5"/>
        <rect x="280" y="520" width="780" height="200" rx="10" fill="rgba(5,6,8,0.55)" stroke="#2A3142" stroke-width="1.5"/>
        <line id="beam-line" x1="260" y1="500" x2="260" y2="500" stroke="#3F8FA3" stroke-width="6" opacity="0.9"/>
        <circle id="amber-dot" cx="1000" cy="500" r="0" fill="rgba(245,164,0,0.18)" stroke="#F5A400" stroke-width="2"/>
        <circle id="amber-dot-inner" cx="1000" cy="500" r="0" fill="#F5A400"/>
      </svg>

      <div id="stat-card">
        <div class="big">$20B+</div>
        <div class="small">EUV machine price (order of magnitude)</div>
      </div>
      <div id="text-beat">Decades of data. Not a blueprint.</div>
    </div>
"""
            css = f"""
      #scene {{ position:absolute; inset:0; }}
      #stat-card {{
        position:absolute; right: 140px; top: 240px;
        width: 520px; padding: 34px 34px 30px;
        border: 2px solid {accent};
        background: rgba(17, 21, 28, 0.82);
        opacity: 0; transform: translateY(10px);
      }}
      #stat-card .big {{ font-size: 74px; font-weight: 700; letter-spacing: 0.02em; }}
      #stat-card .small {{
        margin-top: 10px;
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 16px; letter-spacing: 0.12em;
        color: {steel};
        text-transform: uppercase;
      }}
      #text-beat {{
        position:absolute; right: 140px; top: 420px;
        width: 560px;
        color: {fg};
        font-size: 42px;
        font-weight: 300;
        letter-spacing: 0.04em;
        opacity: 0; transform: translateY(10px);
      }}
"""
            js = """
      tl.set("#beam-line", { attr: { x2: 260 } }, 0)
        .to("#beam-line", { attr: { x2: 1000 }, duration: 1.4, ease: "power2.inOut" }, 8.0)
        .to("#amber-dot", { attr: { r: 55 }, duration: 0.7, ease: "power3.out" }, 9.2)
        .to("#amber-dot-inner", { attr: { r: 12 }, duration: 0.5, ease: "power3.out" }, 9.2)
        .to("#amber-dot-inner", { attr: { r: 16 }, duration: 1.4, ease: "sine.inOut", repeat: 12, yoyo: true }, 10.0)
        .to("#stat-card", { opacity: 1, y: 0, duration: 0.55, ease: "power2.out" }, 16.0)
        .to("#stat-card", { opacity: 0.78, duration: 0.4, ease: "power1.out" }, 25.0)
        .to("#text-beat", { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }, 32.0)
        .to("#text-beat", { opacity: 0, duration: 0.6, ease: "power1.in" }, 37.5);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc06":
            inner = f'<div class="bridge"><div class="t">{self._escape_text("So they all go to the same place.")}</div></div>'
            css = f"""
      .bridge {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding: 160px; }}
      .t {{ font-size: 72px; font-weight: 400; letter-spacing: 0.02em; opacity: 0; }}
      .t::after {{ content:\"\"; display:block; height:2px; width: 220px; background:{primary}; margin: 28px auto 0; opacity: 0.55; }}
"""
            js = "tl.to('.t', { opacity: 1, duration: 0.35, ease: 'power1.out' }, 0);"
            return _wrap(inner, css, js)

        if scene_id == "sc08":
            # Supply chain diagram: EDA -> Fabless -> Foundry -> OSAT -> OEM.
            inner = """
    <div id="diagram">
      <svg id="arrows" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#3F8FA3"/>
          </marker>
        </defs>
        <path id="a0" d="M 440 540 L 610 540" stroke="#3F8FA3" stroke-width="4" fill="none" marker-end="url(#arrowhead)"/>
        <path id="a1" d="M 740 540 L 910 540" stroke="#3F8FA3" stroke-width="4" fill="none" marker-end="url(#arrowhead)"/>
        <path id="a2" d="M 1040 540 L 1210 540" stroke="#3F8FA3" stroke-width="4" fill="none" marker-end="url(#arrowhead)"/>
        <path id="a3" d="M 1340 540 L 1510 540" stroke="#3F8FA3" stroke-width="4" fill="none" marker-end="url(#arrowhead)"/>
      </svg>
      <div class="node" id="n0"><div class="label">EDA</div></div>
      <div class="node" id="n1"><div class="label">Fabless</div></div>
      <div class="node" id="n2"><div class="label">Foundry</div></div>
      <div class="node" id="n3"><div class="label">OSAT</div></div>
      <div class="node" id="n4"><div class="label">OEM</div></div>
      <div id="pulse"></div>
    </div>
"""
            css = f"""
      #diagram {{ position:absolute; inset:0; }}
      #arrows {{ position:absolute; inset:0; }}
      .node {{
        position:absolute;
        top: 476px;
        width: 220px; height: 128px;
        border: 2px solid {primary};
        background: rgba(17, 21, 28, 0.72);
        display:flex; align-items:center; justify-content:center;
        opacity: 0; transform: translateY(10px);
      }}
      .label {{ font-size: 30px; letter-spacing: 0.10em; font-weight: 500; }}
      #n0 {{ left: 220px; }}
      #n1 {{ left: 520px; }}
      #n2 {{ left: 820px; }}
      #n3 {{ left: 1120px; }}
      #n4 {{ left: 1420px; }}
      #pulse {{
        position:absolute;
        left: 930px;
        top: 540px;
        width: 18px; height: 18px;
        border-radius: 999px;
        border: 2px solid {accent};
        opacity: 0;
        transform: translate(-50%, -50%) scale(1);
      }}
"""
            js = """
      const arrows = ["#a0","#a1","#a2","#a3"];
      arrows.forEach((sel) => {
        const p = document.querySelector(sel);
        const len = p.getTotalLength();
        p.style.strokeDasharray = len;
        p.style.strokeDashoffset = len;
        p.style.opacity = 0.0;
      });
      tl.to("#n0", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 0.0)
        .to("#a0", { opacity: 0.9, duration: 0.01 }, 2.0)
        .to("#a0", { strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut" }, 2.0)
        .to("#n1", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 2.8)
        .to("#a1", { opacity: 0.9, duration: 0.01 }, 5.3)
        .to("#a1", { strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut" }, 5.3)
        .to("#n2", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 6.1)
        .to("#a2", { opacity: 0.9, duration: 0.01 }, 8.6)
        .to("#a2", { strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut" }, 8.6)
        .to("#n3", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 9.4)
        .to("#a3", { opacity: 0.9, duration: 0.01 }, 11.9)
        .to("#a3", { strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut" }, 11.9)
        .to("#n4", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 12.7)
        .to("#pulse", { opacity: 1, duration: 0.01 }, 14.4)
        .to("#pulse", { opacity: 0, scale: 1.12, duration: 0.7, ease: "power2.out" }, 14.42);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc09":
            # Chokepoint reveal: reuse sc08 layout but amber Foundry, dim others, pulse ring.
            inner = """
    <div id="diagram">
      <div class="node dim" id="n0"><div class="label">EDA</div></div>
      <div class="node dim" id="n1"><div class="label">Fabless</div></div>
      <div class="node" id="n2"><div class="label">Foundry</div></div>
      <div class="node dim" id="n3"><div class="label">OSAT</div></div>
      <div class="node dim" id="n4"><div class="label">OEM</div></div>
      <div id="ring"></div>
    </div>
"""
            css = f"""
      #diagram {{ position:absolute; inset:0; }}
      .node {{
        position:absolute;
        top: 476px;
        width: 220px; height: 128px;
        border: 2px solid {primary};
        background: rgba(17, 21, 28, 0.72);
        display:flex; align-items:center; justify-content:center;
        opacity: 1;
      }}
      .dim {{ opacity: 0.25; }}
      .label {{ font-size: 30px; letter-spacing: 0.10em; font-weight: 500; }}
      #n0 {{ left: 220px; }}
      #n1 {{ left: 520px; }}
      #n2 {{ left: 820px; border-color: {primary}; box-shadow: 0 0 0 rgba(245,164,0,0); }}
      #n3 {{ left: 1120px; }}
      #n4 {{ left: 1420px; }}
      #ring {{
        position:absolute;
        left: 930px; top: 540px;
        width: 28px; height: 28px;
        border-radius: 999px;
        border: 2px solid {accent};
        opacity: 0;
        transform: translate(-50%, -50%) scale(0.9);
      }}
"""
            js = f"""
      tl.to("#n2", {{ borderColor: {json.dumps(accent)}, duration: 0.8, ease: "power1.out" }}, 0.2)
        .to("#ring", {{ opacity: 1, duration: 0.01 }}, 1.2)
        .to("#ring", {{ opacity: 0, scale: 1.55, duration: 0.9, ease: "power2.out" }}, 1.22)
        .to("#ring", {{ opacity: 1, scale: 1.0, duration: 0.01 }}, 3.0)
        .to("#ring", {{ opacity: 0, scale: 1.55, duration: 0.9, ease: "power2.out" }}, 3.02);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc11":
            inner = """
    <div class="wrap">
      <div class="bg-node"></div>
      <div class="title" id="t0">TSMC</div>
      <div class="subtitle" id="t1">Taiwan Semiconductor Manufacturing Company</div>
      <div class="facts">
        <div class="fact" id="f0">Founded 1987 / Hsinchu, Taiwan</div>
        <div class="fact" id="f1">~60,000 employees</div>
        <div class="fact" id="f2">Revenue: ~$125B (2025)</div>
      </div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; padding: 140px 160px; }}
      .bg-node {{
        position:absolute;
        left: 220px; top: 340px;
        width: 520px; height: 520px;
        border-radius: 999px;
        border: 2px solid {accent};
        opacity: 0.12;
        filter: blur(0.2px);
      }}
      .title {{
        position: relative;
        margin-top: 200px;
        font-family: \"Space Grotesk\", Inter, Arial, sans-serif;
        font-weight: 800;
        font-size: 132px;
        letter-spacing: 0.02em;
        color: {accent};
        opacity: 0;
      }}
      .subtitle {{
        margin-top: 20px;
        font-size: 34px;
        font-weight: 300;
        letter-spacing: 0.03em;
        opacity: 0;
      }}
      .facts {{ margin-top: 44px; }}
      .fact {{
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 18px;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        color: {steel};
        opacity: 0;
        margin-top: 14px;
      }}
"""
            js = """
      tl.to("#t0", { opacity: 1, duration: 0.35, ease: "power1.out" }, 0.0)
        .to("#t1", { opacity: 1, duration: 0.35, ease: "power1.out" }, 0.35)
        .to("#f0", { opacity: 1, duration: 0.3, ease: "power1.out" }, 0.75)
        .to("#f1", { opacity: 1, duration: 0.3, ease: "power1.out" }, 1.15)
        .to("#f2", { opacity: 1, duration: 0.3, ease: "power1.out" }, 1.55)
        .to(["#t1", "#f0", "#f1", "#f2"], { opacity: 0.35, duration: 0.35, ease: "power1.out" }, 7.0);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc12":
            inner = """
    <div class="wrap">
      <div class="chain">
        <div class="node dim">EDA</div>
        <div class="arrow"></div>
        <div class="node dim">Fabless</div>
        <div class="arrow"></div>
        <div class="node amber">Foundry</div>
        <div class="arrow"></div>
        <div class="node dim">OSAT</div>
        <div class="arrow"></div>
        <div class="node dim">OEM</div>
      </div>
      <div class="stat" id="stat">
        <div class="big">90%+</div>
        <div class="small">advanced-node share <span class="qual">(analyst est.)</span></div>
      </div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; padding: 140px 140px; }}
      .chain {{ display:flex; align-items:center; justify-content:center; gap: 18px; margin-top: 340px; }}
      .node {{
        width: 200px; height: 120px;
        border: 2px solid {primary};
        background: rgba(17, 21, 28, 0.72);
        display:flex; align-items:center; justify-content:center;
        font-size: 26px; letter-spacing: 0.12em;
        text-transform: uppercase;
      }}
      .dim {{ opacity: 0.25; }}
      .amber {{ border-color: {accent}; box-shadow: 0 0 0 1px rgba(245,164,0,0.15) inset; }}
      .arrow {{ width: 54px; height: 2px; background: {primary}; opacity: 0.65; }}
      .stat {{
        position:absolute; right: 140px; top: 180px;
        width: 520px; padding: 32px 32px 28px;
        border: 2px solid {accent};
        background: rgba(17, 21, 28, 0.84);
        opacity: 0; transform: translateY(10px);
      }}
      .big {{ font-size: 86px; font-weight: 800; letter-spacing: 0.02em; }}
      .small {{
        margin-top: 10px;
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 16px; letter-spacing: 0.12em;
        color: {steel};
        text-transform: uppercase;
      }}
      .qual {{ color: {steel}; opacity: 0.9; }}
"""
            js = "tl.to('#stat', { opacity: 1, y: 0, duration: 0.55, ease: 'power2.out' }, 2.2);"
            return _wrap(inner, css, js)

        if scene_id == "sc13":
            inner = """
    <div class="wrap">
      <div class="title">Yield (directional)</div>
      <div class="bar tsmc"><div class="fill"></div><div class="label">TSMC — Industry-leading (~65–70% est.)</div></div>
      <div class="bar samsung"><div class="fill"></div><div class="label">Samsung — Lower yield (directional)</div></div>
      <div class="bar intel"><div class="fill"></div><div class="label">Intel — Catching up (directional)</div></div>
      <div class="note">Comparison is directional. Estimates stay labeled.</div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; padding: 160px 180px; }}
      .title {{
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 18px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: {steel};
      }}
      .bar {{
        margin-top: 48px;
        position: relative;
        height: 82px;
        border: 1px solid {graphite};
        background: rgba(17, 21, 28, 0.55);
        overflow: hidden;
      }}
      .fill {{
        position:absolute; left:0; top:0; bottom:0;
        width: 0%;
        opacity: 0.95;
      }}
      .tsmc .fill {{ background: {accent}; }}
      .samsung .fill {{ background: {primary}; opacity: 0.55; }}
      .intel .fill {{ background: {primary}; opacity: 0.35; }}
      .label {{
        position: relative;
        padding: 22px 24px;
        font-size: 26px;
        letter-spacing: 0.03em;
      }}
      .note {{
        margin-top: 56px;
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 14px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: {steel};
        opacity: 0.85;
      }}
"""
            js = """
      tl.to(".tsmc .fill", { width: "86%", duration: 0.9, ease: "power2.out" }, 0.6)
        .to(".samsung .fill", { width: "44%", duration: 0.9, ease: "power2.out" }, 1.1)
        .to(".intel .fill", { width: "58%", duration: 0.9, ease: "power2.out" }, 1.6);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc14":
            inner = """
    <div class="wrap">
      <div class="card" id="card">
        <div class="big">$35.90B</div>
        <div class="sub">+40.6% YoY (USD)</div>
        <div class="line">Q1 2026 — New Quarterly Record</div>
      </div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding: 160px; }}
      .card {{
        width: 900px;
        padding: 70px 70px 62px;
        border: 3px solid {accent};
        background: rgba(17, 21, 28, 0.86);
        box-shadow: 0 18px 70px rgba(0,0,0,0.55);
        opacity: 0;
        transform: translateY(14px);
      }}
      .big {{ font-size: 128px; font-weight: 800; letter-spacing: 0.01em; }}
      .sub {{
        margin-top: 16px;
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 18px; letter-spacing: 0.12em;
        color: {steel};
        text-transform: uppercase;
      }}
      .line {{ margin-top: 26px; font-size: 28px; letter-spacing: 0.04em; opacity: 0.95; }}
"""
            js = "tl.to('#card', { opacity: 1, y: 0, duration: 0.55, ease: 'power2.out' }, 0.4);"
            return _wrap(inner, css, js)

        if scene_id == "sc16":
            inner = """
    <div class="wrap">
      <div class="cols">
        <div class="col" id="c0"><div class="big">$52B</div><div class="small">US CHIPS Act</div></div>
        <div class="col" id="c1"><div class="big">€43B</div><div class="small">EU Chips Act</div></div>
        <div class="col" id="c2"><div class="big">¥3.9T</div><div class="small">Japan incentives</div></div>
      </div>
      <div class="note">Capital helps. The ecosystem is the moat.</div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; padding: 160px 160px; }}
      .cols {{ display:flex; gap: 26px; justify-content:center; margin-top: 220px; }}
      .col {{
        width: 460px;
        padding: 38px 38px 34px;
        border: 2px solid {graphite};
        background: rgba(17, 21, 28, 0.72);
        opacity: 0; transform: translateY(10px);
      }}
      .big {{ font-size: 86px; font-weight: 800; letter-spacing: 0.01em; }}
      .small {{
        margin-top: 10px;
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 16px; letter-spacing: 0.12em;
        color: {steel};
        text-transform: uppercase;
      }}
      .note {{
        margin-top: 80px;
        text-align:center;
        font-size: 34px;
        font-weight: 300;
        letter-spacing: 0.03em;
        opacity: 0.0;
      }}
"""
            js = """
      tl.to(["#c0","#c1","#c2"], { opacity: 1, y: 0, duration: 0.5, stagger: 0.5, ease: "power2.out" }, 0.0)
        .to(".note", { opacity: 0.9, duration: 0.55, ease: "power1.out" }, 2.1);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc17":
            # Arizona fab stat card (ported from assets/scenes/sc17-arizona-fab.html).
            inner = """
    <div id="scene">
      <div id="stat-card">
        <div class="title">TSMC Arizona</div>
        <div class="line" id="line-n4"><span class="k">N4</span><span class="v">In production</span></div>
        <div class="line" id="line-n3"><span class="k">N3</span><span class="v">2027 (planned)</span></div>
        <div class="line" id="line-n2"><span class="k">N2</span><span class="v">No date set</span></div>
        <div id="stat-divider"></div>
        <div id="arrow-caption">Node-generation framing: not leading-edge redundancy</div>
      </div>
    </div>
"""
            css = f"""
      #scene {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding: 160px; }}
      #stat-card {{
        width: 980px;
        padding: 64px 64px 56px;
        border: 2px solid {graphite};
        background: rgba(17, 21, 28, 0.86);
        opacity: 0; transform: translateY(12px);
      }}
      .title {{
        font-family: \"Space Grotesk\", Inter, Arial, sans-serif;
        font-weight: 800;
        font-size: 66px;
        letter-spacing: 0.02em;
        margin-bottom: 22px;
      }}
      .line {{
        display:flex; justify-content:space-between; align-items:baseline;
        font-size: 34px; letter-spacing: 0.03em;
        padding: 14px 0;
        opacity: 0; transform: translateY(8px);
      }}
      .k {{
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 18px; letter-spacing: 0.16em;
        color: {steel}; text-transform: uppercase;
      }}
      #line-n2 {{ opacity: 0; }}
      #stat-divider {{ height: 1px; background: {graphite}; margin: 22px 0; opacity: 0; }}
      #arrow-caption {{
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 14px; letter-spacing: 0.12em;
        color: {red};
        text-transform: uppercase;
        opacity: 0; transform: translateX(-6px);
      }}
"""
            js = """
      tl.to("#stat-card", { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }, 2.0)
        .to("#line-n4", { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }, 3.2)
        .to("#line-n3", { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }, 4.4)
        .to("#line-n2", { opacity: 0.7, y: 0, duration: 0.4, ease: "power2.out" }, 5.6)
        .to("#stat-divider", { opacity: 1, duration: 0.4, ease: "power1.out" }, 8.0)
        .to("#arrow-caption", { opacity: 1, x: 0, duration: 0.5, ease: "power2.out" }, 8.4);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc18":
            inner = """
    <div class="wrap">
      <div class="quote" id="q">\"A very expensive exercise in futility.\"</div>
      <div class="attr" id="a">Morris Chang</div>
    </div>
"""
            css = f"""
      [data-composition-id="{self._escape_attr(scene_id)}"] {{ background: {graphite}; }}
      .wrap {{ position:absolute; inset:0; display:flex; flex-direction:column; justify-content:center; padding: 160px 180px; gap: 28px; }}
      .quote {{
        font-size: 74px;
        font-weight: 400;
        font-style: italic;
        letter-spacing: 0.02em;
        opacity: 0;
      }}
      .attr {{
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 18px; letter-spacing: 0.18em;
        text-transform: uppercase;
        color: {steel};
        opacity: 0;
      }}
"""
            js = """
      tl.to("#q", { opacity: 1, duration: 0.5, ease: "power1.out" }, 0.0)
        .to("#a", { opacity: 0.9, duration: 0.4, ease: "power1.out" }, 1.5);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc20":
            inner = """
    <div class="wrap">
      <div class="node" id="core">Foundry</div>
      <div class="tag" id="t0">Pricing power</div>
      <div class="tag" id="t1">Schedule power</div>
      <div class="tag" id="t2">Strategic weight</div>
      <div class="ring" id="r"></div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; }}
      .node {{
        position:absolute; left: 960px; top: 520px;
        width: 260px; height: 150px;
        transform: translate(-50%, -50%);
        border: 3px solid {accent};
        background: rgba(17, 21, 28, 0.82);
        display:flex; align-items:center; justify-content:center;
        font-size: 30px; letter-spacing: 0.12em; text-transform: uppercase;
        box-shadow: 0 0 0 1px rgba(245,164,0,0.15) inset;
      }}
      .ring {{
        position:absolute; left: 960px; top: 520px;
        width: 420px; height: 420px;
        transform: translate(-50%, -50%);
        border-radius: 999px;
        border: 1px solid {graphite};
        opacity: 0.35;
      }}
      .tag {{
        position:absolute;
        padding: 14px 18px;
        border: 1px solid {graphite};
        background: rgba(5, 6, 8, 0.55);
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 14px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: {steel};
        opacity: 0;
      }}
      #t0 {{ left: 960px; top: 270px; transform: translate(-50%, -50%); }}
      #t1 {{ left: 1240px; top: 560px; transform: translate(-50%, -50%); }}
      #t2 {{ left: 700px; top: 720px; transform: translate(-50%, -50%); }}
"""
            js = """
      tl.to(["#t0","#t1","#t2"], { opacity: 1, duration: 0.45, stagger: 0.5, ease: "power2.out" }, 0.8)
        .to("#r", { opacity: 0.6, duration: 0.35, ease: "power1.out" }, 0.8);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc21":
            inner = """
    <div class="wrap">
      <div class="stack" id="stack">
        <div class="layer" id="l0"><div class="k">Wafer Fabrication</div></div>
        <div class="layer" id="l1"><div class="k">Advanced Packaging</div><div class="sub">CoWoS</div></div>
      </div>
      <div class="caption" id="cap">A second chokepoint inside the first.</div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; }}
      .stack {{
        width: 640px;
        border: 3px solid {accent};
        background: rgba(17, 21, 28, 0.86);
        box-shadow: 0 18px 70px rgba(0,0,0,0.55);
        overflow: hidden;
        opacity: 0; transform: translateY(14px);
      }}
      .layer {{
        height: 140px;
        display:flex;
        align-items:center;
        justify-content:center;
        flex-direction: column;
        gap: 8px;
        border-top: 1px solid rgba(42,49,66,0.8);
        opacity: 0;
      }}
      #l0 {{ border-top: none; }}
      .k {{ font-size: 28px; letter-spacing: 0.12em; text-transform: uppercase; }}
      .sub {{
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 16px; letter-spacing: 0.16em;
        text-transform: uppercase;
        color: {accent};
      }}
      .caption {{
        position:absolute;
        bottom: 130px;
        left: 0; right: 0;
        text-align:center;
        font-size: 34px;
        font-weight: 300;
        letter-spacing: 0.03em;
        opacity: 0;
      }}
"""
            js = """
      tl.to("#stack", { opacity: 1, y: 0, duration: 0.55, ease: "power2.out" }, 0.2)
        .to("#l0", { opacity: 1, duration: 0.4, ease: "power1.out" }, 0.8)
        .to("#l1", { opacity: 1, duration: 0.4, ease: "power1.out" }, 1.6)
        .to("#cap", { opacity: 0.9, duration: 0.55, ease: "power1.out" }, 2.6);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc22":
            inner = """
    <div class="wrap">
      <div class="card" id="card">
        <div class="big">~130K wpm</div>
        <div class="small">Projected CoWoS capacity end-2026 / Still sold out</div>
        <div class="bar"><div class="fill" id="fill"></div></div>
        <div class="small2">Capacity expansion is real. The backlog remains.</div>
      </div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding: 160px; }}
      .card {{
        width: 980px;
        padding: 64px 64px 56px;
        border: 2px solid {accent};
        background: rgba(17, 21, 28, 0.86);
        opacity: 0; transform: translateY(14px);
      }}
      .big {{ font-size: 96px; font-weight: 800; letter-spacing: 0.01em; }}
      .small {{
        margin-top: 14px;
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 14px; letter-spacing: 0.14em;
        text-transform: uppercase;
        color: {steel};
      }}
      .bar {{ margin-top: 28px; height: 14px; background: rgba(42,49,66,0.7); overflow:hidden; }}
      .fill {{ width: 0%; height: 100%; background: {accent}; opacity: 0.9; }}
      .small2 {{ margin-top: 26px; font-size: 28px; font-weight: 300; letter-spacing: 0.03em; opacity: 0.85; }}
"""
            js = """
      tl.to("#card", { opacity: 1, y: 0, duration: 0.55, ease: "power2.out" }, 0.2)
        .to("#fill", { width: "72%", duration: 0.9, ease: "power2.out" }, 1.0);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc23":
            # Abstract convergence diagram (ported from assets/scenes/sc23-convergence.html).
            inner = """
    <div id="scene">
      <svg id="routes" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
        <path id="r-apple" d="M 360 260 C 700 260 820 420 960 480" stroke="#3F8FA3" stroke-width="4" fill="none"/>
        <path id="r-nvidia" d="M 360 380 C 720 380 820 470 960 510" stroke="#3F8FA3" stroke-width="4" fill="none"/>
        <path id="r-amd" d="M 360 500 C 740 500 820 520 960 540" stroke="#3F8FA3" stroke-width="4" fill="none"/>
        <path id="r-qualcomm" d="M 360 620 C 700 620 820 600 960 570" stroke="#3F8FA3" stroke-width="4" fill="none"/>
        <path id="r-dc" d="M 360 740 C 660 740 820 690 960 600" stroke="#3F8FA3" stroke-width="4" fill="none"/>
      </svg>
      <div class="node" id="n-apple"><div class="label">Apple</div></div>
      <div class="node" id="n-nvidia"><div class="label">NVIDIA</div></div>
      <div class="node" id="n-amd"><div class="label">AMD</div></div>
      <div class="node" id="n-qualcomm"><div class="label">Qualcomm</div></div>
      <div class="node" id="n-dc"><div class="label">AI Data Centers</div></div>

      <div class="node" id="chokepoint">
        <div style="text-align:center">
          <div class="label">TSMC</div>
          <div class="sub">TAIWAN CHOKEPOINT</div>
        </div>
      </div>
      <div id="pulse"></div>
      <div id="final-sub">One factory. No backup.</div>
    </div>
"""
            css = f"""
      #scene {{ position: relative; width: 1920px; height: 1080px; }}
      #routes {{ position:absolute; inset:0; opacity: 0.9; }}
      .node {{
        position: absolute;
        width: 280px;
        height: 96px;
        border: 1px solid {graphite};
        background: rgba(17, 21, 28, 0.65);
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transform: translateY(10px);
      }}
      .label {{ color: {fg}; font-size: 28px; font-weight: 400; letter-spacing: 0.06em; }}
      #n-apple {{ left: 140px; top: 210px; }}
      #n-nvidia {{ left: 140px; top: 330px; }}
      #n-amd {{ left: 140px; top: 450px; }}
      #n-qualcomm {{ left: 140px; top: 570px; }}
      #n-dc {{ left: 140px; top: 690px; }}
      #chokepoint {{
        left: 1180px; top: 430px;
        width: 420px; height: 160px;
        border: 2px solid {accent};
        background: rgba(17, 21, 28, 0.88);
        box-shadow: 0 16px 60px rgba(0,0,0,0.55);
        transform: translateY(12px);
      }}
      #chokepoint .label {{
        font-family: \"Space Grotesk\", Inter, Arial, sans-serif;
        font-size: 42px;
        font-weight: 800;
        letter-spacing: 0.02em;
        color: {fg};
      }}
      #chokepoint .sub {{
        margin-top: 10px;
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 14px;
        letter-spacing: 0.12em;
        color: {steel};
        text-transform: uppercase;
        opacity: 0.95;
      }}
      #pulse {{
        position: absolute;
        left: 1390px; top: 510px;
        width: 16px; height: 16px;
        border-radius: 999px;
        border: 2px solid {accent};
        opacity: 0;
        transform: translate(-50%, -50%) scale(1.0);
      }}
      #final-sub {{
        position:absolute;
        right: 140px; bottom: 120px;
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 16px; letter-spacing: 0.14em;
        text-transform: uppercase;
        color: {steel};
        opacity: 0;
      }}
"""
            js = """
      const routes = ["#r-apple","#r-nvidia","#r-amd","#r-qualcomm","#r-dc"];
      for (const sel of routes) {
        const p = document.querySelector(sel);
        const len = p.getTotalLength();
        p.style.strokeDasharray = len;
        p.style.strokeDashoffset = len;
        p.style.opacity = 0.0;
      }
      const nodes = ["#n-apple","#n-nvidia","#n-amd","#n-qualcomm","#n-dc"];
      tl.to(nodes, { opacity: 1, y: 0, duration: 0.45, stagger: 0.16, ease: "power2.out" }, 0.0)
        .to("#chokepoint", { opacity: 1, y: 0, duration: 0.55, ease: "power2.out" }, 0.45);
      function pulseAmber(at) {
        tl.to("#pulse", { opacity: 1, scale: 1.0, duration: 0.01 }, at)
          .to("#pulse", { opacity: 0.0, scale: 1.10, duration: 0.70, ease: "power2.out" }, at + 0.02);
      }
      const start = 2.0;
      const gap = 2.6;
      routes.forEach((r, i) => {
        const at = start + i * gap;
        tl.to(r, { opacity: 0.9, duration: 0.01 }, at)
          .to(r, { strokeDashoffset: 0, duration: 1.0, ease: "power2.inOut" }, at);
        pulseAmber(at + 1.0);
        tl.to(nodes[i], { opacity: 0.55, duration: 0.45, ease: "power1.out" }, at + 1.05);
      });
      tl.to("#final-sub", { opacity: 1, duration: 0.6, ease: "power1.out" }, 15.8);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc25":
            inner = """
    <div class="wrap">
      <div class="core" id="core">TSMC</div>
      <div class="leaf" id="l0">AI Training Clusters</div>
      <div class="leaf" id="l1">Consumer Devices</div>
      <div class="leaf" id="l2">Cloud Infrastructure</div>
      <div class="leaf" id="l3">Defense Systems</div>
      <svg id="lines" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
        <path id="p0" d="M 960 360 C 820 470 760 560 720 650" stroke="#3F8FA3" stroke-width="3" fill="none"/>
        <path id="p1" d="M 960 360 C 900 480 910 600 960 700" stroke="#3F8FA3" stroke-width="3" fill="none"/>
        <path id="p2" d="M 960 360 C 1020 480 1020 600 960 820" stroke="#3F8FA3" stroke-width="3" fill="none"/>
        <path id="p3" d="M 960 360 C 1100 470 1160 560 1200 650" stroke="#3F8FA3" stroke-width="3" fill="none"/>
      </svg>
      <div class="swap" id="s0">Compute</div>
      <div class="swap" id="s1">AI</div>
      <div class="swap" id="s2">Semiconductors</div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; }}
      #lines {{ position:absolute; inset:0; opacity: 0.8; }}
      .core {{
        position:absolute; left: 960px; top: 300px;
        transform: translate(-50%, -50%);
        width: 420px; height: 160px;
        border: 3px solid {accent};
        background: rgba(17, 21, 28, 0.86);
        display:flex; align-items:center; justify-content:center;
        font-family: \"Space Grotesk\", Inter, Arial, sans-serif;
        font-size: 58px; font-weight: 800;
        letter-spacing: 0.02em;
        opacity: 0;
      }}
      .leaf {{
        position:absolute;
        width: 420px; height: 96px;
        border: 1px solid {graphite};
        background: rgba(17, 21, 28, 0.65);
        display:flex; align-items:center; justify-content:center;
        font-size: 24px; letter-spacing: 0.06em;
        opacity: 0; transform: translateY(10px);
      }}
      #l0 {{ left: 420px; top: 650px; }}
      #l1 {{ left: 740px; top: 760px; }}
      #l2 {{ left: 1160px; top: 860px; }}
      #l3 {{ left: 1500px; top: 650px; }}
      .swap {{
        position:absolute;
        left: 960px; top: 300px;
        transform: translate(-50%, -50%);
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 16px; letter-spacing: 0.18em;
        text-transform: uppercase;
        color: {steel};
        opacity: 0;
      }}
      #s0 {{ top: 410px; }}
      #s1 {{ top: 448px; }}
      #s2 {{ top: 486px; }}
"""
            js = """
      const paths = ["#p0","#p1","#p2","#p3"];
      paths.forEach((sel) => {
        const p = document.querySelector(sel);
        const len = p.getTotalLength();
        p.style.strokeDasharray = len;
        p.style.strokeDashoffset = len;
        p.style.opacity = 0.0;
      });
      tl.to("#core", { opacity: 1, duration: 0.55, ease: "power2.out" }, 0.2)
        .to(paths, { opacity: 0.9, duration: 0.01 }, 1.2)
        .to("#p0", { strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut" }, 1.2)
        .to("#l0", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 2.2)
        .to("#p1", { strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut" }, 3.0)
        .to("#l1", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 4.0)
        .to("#p2", { strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut" }, 4.8)
        .to("#l2", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 5.8)
        .to("#p3", { strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut" }, 6.6)
        .to("#l3", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 7.6)
        .to("#s0", { opacity: 1, duration: 0.35, ease: "power1.out" }, 9.2)
        .to("#s1", { opacity: 1, duration: 0.35, ease: "power1.out" }, 10.2)
        .to("#s2", { opacity: 1, duration: 0.35, ease: "power1.out" }, 11.2);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc26":
            inner = """
    <div class="wrap">
      <div class="card" id="card">
        <div class="line" id="l0">90%+ advanced-node share <span class="q">(analyst est.)</span></div>
        <div class="line" id="l1">Arizona: N4 now — N3 expected 2027</div>
        <div class="line" id="l2">CoWoS: still sold out through 2026</div>
      </div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding: 160px; }}
      .card {{
        width: 1100px;
        padding: 70px 70px 60px;
        border: 3px solid {accent};
        background: rgba(17, 21, 28, 0.88);
        box-shadow: 0 18px 70px rgba(0,0,0,0.55);
      }}
      .line {{
        font-size: 38px;
        font-weight: 400;
        letter-spacing: 0.02em;
        opacity: 0;
        transform: translateY(10px);
        margin-top: 18px;
      }}
      #l0 {{ margin-top: 0; }}
      .q {{
        font-family: \"IBM Plex Mono\", \"Courier New\", monospace;
        font-size: 16px; letter-spacing: 0.12em;
        text-transform: uppercase;
        color: {steel};
        margin-left: 10px;
      }}
"""
            js = """
      tl.to("#l0", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 0.4)
        .to("#l1", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 1.4)
        .to("#l2", { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, 2.4);
"""
            return _wrap(inner, css, js)

        if scene_id == "sc27":
            inner = """
    <div class="wrap">
      <div class="t" id="t">The research stack I use for this kind of mapping is linked in the description.</div>
      <div class="u" id="u"></div>
    </div>
"""
            css = f"""
      .wrap {{ position:absolute; inset:0; display:flex; flex-direction:column; justify-content:center; padding: 160px 180px; gap: 34px; }}
      .t {{ font-size: 46px; font-weight: 300; letter-spacing: 0.03em; max-width: 1200px; opacity: 0; }}
      .u {{ width: 420px; height: 3px; background: {accent}; opacity: 0; transform: scaleX(0.2); transform-origin: left center; }}
"""
            js = """
      tl.to("#t", { opacity: 1, duration: 0.6, ease: "power1.out" }, 0.2)
        .to("#u", { opacity: 0.9, duration: 0.01 }, 1.7)
        .to("#u", { scaleX: 1.0, duration: 0.6, ease: "power2.out" }, 1.72);
"""
            return _wrap(inner, css, js)

        # Generic fallback: designed text scene instead of a plain centered card.
        headline = text or scene_id.upper()
        sub = (scene.get("shot_intent") or scene.get("information_role") or "").strip()
        inner = f"""
    <div class="wrap">
      <div class="grid"></div>
      <div class="h" id="h">{self._escape_text(headline)}</div>
      <div class="s" id="s">{self._escape_text(sub)}</div>
    </div>
"""
        css = f"""
      .wrap {{ position:absolute; inset:0; padding: 150px 170px; display:flex; flex-direction:column; justify-content:center; gap: 30px; }}
      .grid {{
        position:absolute; inset:0;
        background:
          linear-gradient(rgba(42,49,66,0.28) 1px, transparent 1px),
          linear-gradient(90deg, rgba(42,49,66,0.20) 1px, transparent 1px);
        background-size: 84px 84px;
        opacity: 0.16;
      }}
      .h {{ position:relative; font-size: 86px; font-weight: 700; letter-spacing: 0.01em; opacity: 0; }}
      .s {{
        position:relative;
        max-width: 1200px;
        font-size: 28px;
        font-weight: 300;
        letter-spacing: 0.03em;
        color: {steel};
        opacity: 0;
      }}
"""
        js = """
      tl.to("#h", { opacity: 1, duration: 0.5, ease: "power2.out" }, 0.1)
        .to("#s", { opacity: 0.9, duration: 0.5, ease: "power2.out" }, 0.5);
"""
        return _wrap(inner, css, js)

    # ------------------------------------------------------------------
    # HTML generation (minimal, Phase 1)
    # ------------------------------------------------------------------

    def _generate_index_html(
        self,
        cuts: list[dict],
        audio_refs: dict[str, Any],
        width: int,
        height: int,
        total_duration: float,
        css_vars: dict[str, str],
        title: str,
    ) -> str:
        """Emit a HyperFrames-contract-compliant index.html.

        Phase 1 covers the minimum required for smoke-testing the runtime:
        - still images (img.clip)
        - video clips (video.clip, muted playsinline + separate audio if needed)
        - text cards (div.clip with styled <h1>)
        - narration segments (audio)
        - music bed (audio, lower volume)

        Richer scene types (registry blocks, kinetic typography) are authored
        by the agent directly into compositions/ — this generator just
        provides a functional starting skeleton.
        """
        vars_css = "\n      ".join(f"{k}: {v};" for k, v in css_vars.items())

        clip_html: list[str] = []
        entrance_tweens: list[str] = []
        for i, cut in enumerate(cuts):
            html, tween = self._cut_to_html(i, cut, width, height)
            clip_html.append(html)
            if tween:
                entrance_tweens.append(tween)

        audio_html: list[str] = []
        for j, nar in enumerate(audio_refs.get("narration") or []):
            src = self._rel_from_workspace(nar["src"])
            start = nar.get("start_seconds", 0)
            end = nar.get("end_seconds")
            duration = (end - start) if end and end > start else (total_duration - start)
            audio_html.append(
                f'<audio id="nar-{j}" class="clip audio-clip" '
                f'data-start="{self._f(start)}" data-duration="{self._f(duration)}" '
                f'data-track-index="2" src="{self._escape_attr(src)}" '
                f'data-volume="1"></audio>'
            )

        music = audio_refs.get("music")
        if music:
            src = self._rel_from_workspace(music["src"])
            audio_html.append(
                f'<audio id="music" class="clip audio-clip" '
                f'data-start="0" data-duration="{self._f(total_duration)}" '
                f'data-track-index="3" src="{self._escape_attr(src)}" '
                f'data-volume="{self._f(music["volume"])}"></audio>'
            )

        tween_block = "\n        ".join(entrance_tweens) if entrance_tweens else "// no tweens"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{self._escape_text(title)}</title>
  <style>
    :root {{
      {vars_css}
    }}
    body {{ margin: 0; background: var(--color-bg); color: var(--color-fg); font-family: var(--font-body); }}
    [data-composition-id="root"] {{
      position: relative;
      width: {width}px;
      height: {height}px;
      overflow: hidden;
    }}
    .clip {{ position: absolute; inset: 0; }}
    .clip.video-clip, .clip.image-clip {{ object-fit: cover; width: 100%; height: 100%; }}
    .clip.text-card {{ display: flex; align-items: center; justify-content: center; padding: 120px 160px; box-sizing: border-box; text-align: center; }}
    .clip.text-card h1 {{ font-family: var(--font-heading); font-weight: 700; font-size: 96px; line-height: 1.1; margin: 0; color: var(--color-fg); }}
    .clip.text-card .subtitle {{ font-size: 36px; margin-top: 24px; color: var(--color-accent); }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
</head>
<body>
  <div data-composition-id="root" data-start="0" data-duration="{self._f(total_duration)}" data-width="{width}" data-height="{height}">
    {"".join(clip_html)}
    {"".join(audio_html)}
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {tween_block}
      window.__timelines["root"] = tl;
    </script>
  </div>
</body>
</html>
"""

    def _cut_to_html(
        self, index: int, cut: dict, width: int, height: int
    ) -> tuple[str, Optional[str]]:
        """Render one cut + its entrance tween. Returns (html, tween or None)."""
        cut_id = f"cut-{index}"
        in_s = float(cut.get("in_seconds", 0) or 0)
        out_s = float(cut.get("out_seconds", 0) or 0)
        duration = max(0.1, out_s - in_s)

        source = cut.get("source") or ""
        cut_type = (cut.get("type") or "").lower()
        # NOTE: edit_decisions schema currently does not include `text`/`title` fields,
        # but it does include `reason`. Prefer explicit text/title when present, and
        # fall back to reason so schema-valid cuts can still drive meaningful cards.
        text = cut.get("text") or cut.get("title") or cut.get("reason") or ""

        # Prefer per-scene sub-compositions when a scene id is present. This
        # avoids rendering long episodes as simple text cards.
        scene_id = (cut.get("id") or "").strip()
        if scene_id and not source and cut_type not in {"text_card", "hero_title", "callout"}:
            html = (
                f'<div id="{cut_id}" class="clip scene-comp" '
                f'data-composition-id="{self._escape_attr(scene_id)}" '
                f'data-composition-src="compositions/{self._escape_attr(scene_id)}.html" '
                f'data-start="{self._f(in_s)}" data-duration="{self._f(duration)}" '
                f'data-track-index="1"></div>'
            )
            return html, None

        src_path = Path(source) if source else None
        ext = src_path.suffix.lower() if src_path else ""

        # Decide scene shape
        if cut_type in {"text_card", "hero_title", "callout"} or (not source and text):
            inner = f'<h1>{self._escape_text(text or f"Scene {index + 1}")}</h1>'
            subtitle = cut.get("subtitle") or cut.get("caption")
            if subtitle:
                inner += f'<div class="subtitle">{self._escape_text(subtitle)}</div>'
            html = (
                f'<div id="{cut_id}" class="clip text-card" '
                f'data-start="{self._f(in_s)}" data-duration="{self._f(duration)}" '
                f'data-track-index="1">{inner}</div>'
            )
            # Mild entrance — fade + lift.
            tween = (
                f'tl.from("#{cut_id} h1", {{ y: 40, opacity: 0, duration: 0.6, '
                f'ease: "power3.out" }}, {self._f(in_s + 0.1)});'
            )
            return html, tween

        if ext in _IMAGE_EXTENSIONS and src_path:
            rel = self._rel_from_workspace(str(src_path))
            html = (
                f'<img id="{cut_id}" class="clip image-clip" '
                f'src="{self._escape_attr(rel)}" '
                f'data-start="{self._f(in_s)}" data-duration="{self._f(duration)}" '
                f'data-track-index="1" alt="">'
            )
            tween = (
                f'tl.from("#{cut_id}", {{ scale: 1.05, opacity: 0, duration: 0.5, '
                f'ease: "power2.out" }}, {self._f(in_s)});'
            )
            return html, tween

        if ext in _VIDEO_EXTENSIONS and src_path:
            rel = self._rel_from_workspace(str(src_path))
            html = (
                f'<video id="{cut_id}" class="clip video-clip" '
                f'src="{self._escape_attr(rel)}" '
                f'data-start="{self._f(in_s)}" data-duration="{self._f(duration)}" '
                f'data-track-index="1" muted playsinline></video>'
            )
            return html, None

        # Unknown cut shape — render a placeholder text card so the render
        # still succeeds; lint/validate will surface the issue.
        placeholder = self._escape_text(text or cut.get("reason") or f"Scene {index + 1}")
        html = (
            f'<div id="{cut_id}" class="clip text-card" '
            f'data-start="{self._f(in_s)}" data-duration="{self._f(duration)}" '
            f'data-track-index="1"><h1>{placeholder}</h1></div>'
        )
        return html, None

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _run_hf(
        self,
        args: list[str],
        *,
        cwd: Optional[Path],
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess:
        """Invoke `npx hyperframes <args>` with the right Windows quirks.

        We intentionally bypass `self.run_command` here because we do NOT
        want to raise CalledProcessError on non-zero exits — the caller
        parses lint/validate/render exit codes itself.
        """
        cmd = ["npx", "--yes", "hyperframes", *args]
        # On Windows, resolve the .cmd wrapper so subprocess can find it
        # without shell=True.
        if os.name == "nt":
            resolved = shutil.which(cmd[0])
            if resolved:
                cmd[0] = resolved
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(cwd) if cwd else None,
                check=False,
            )
            # If npx tries to resolve a non-existent version (ETARGET), fall back
            # to a pinned known-good version.
            stderr = (proc.stderr or "")
            if proc.returncode != 0 and ("ETARGET" in stderr or "No matching version found" in stderr):
                fallback = ["npx", "--yes", f"{self._NPM_PACKAGE}@{self._NPM_FALLBACK_VERSION}", *args]
                if os.name == "nt":
                    resolved = shutil.which(fallback[0])
                    if resolved:
                        fallback[0] = resolved
                return subprocess.run(
                    fallback,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(cwd) if cwd else None,
                    check=False,
                )
            return proc
        except subprocess.TimeoutExpired as e:
            # Surface timeouts as a failed CompletedProcess so callers get a
            # uniform shape. The stderr tail will say timeout.
            stdout = e.stdout or b""
            stderr = e.stderr or b""
            # Despite text=True, TimeoutExpired stdout/stderr can be bytes.
            if isinstance(stdout, (bytes, bytearray)):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, (bytes, bytearray)):
                stderr = stderr.decode("utf-8", errors="replace")
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=124,
                stdout=stdout,
                stderr=(stderr or "") + f"\n[timeout after {timeout}s]",
            )

    @staticmethod
    def _parse_json_output(stdout: str) -> Optional[Any]:
        """Parse a `--json` report, tolerating surrounding banner lines."""
        if not stdout:
            return None
        start = stdout.find("{")
        end = stdout.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(stdout[start : end + 1])
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _f(v: float) -> str:
        return f"{float(v):.3f}".rstrip("0").rstrip(".")

    @staticmethod
    def _escape_text(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _escape_attr(s: str) -> str:
        return HyperFramesCompose._escape_text(s).replace('"', "&quot;")

    @staticmethod
    def _rel_from_workspace(path: str) -> str:
        """HyperFrames resolves src= relative to index.html. Our asset files
        live under workspace/assets/, so when we stage a copy we know the
        relative path is `assets/<name>`. For files already in the workspace
        tree, fall back to the file name.
        """
        p = Path(path)
        # If it's already a relative path starting with assets/, keep as-is.
        if not p.is_absolute():
            return str(p).replace("\\", "/")
        # Otherwise emit just the basename under assets/.
        return f"assets/{p.name}"
