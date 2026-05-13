#!/usr/bin/env python3
"""Run the Asymmetric ComfyUI audio-to-roughcut MVP.

The MVP intentionally stays outside the full OpenMontage pipeline contract:
it proves the local production spine first, then later work can promote the
pieces into formal tools/stages.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools._comfyui.client import ComfyUIClient, ComfyUIError  # noqa: E402


DEFAULT_COMFY_HOST = "http://127.0.0.1:8188"
DEFAULT_COMFY_CONTAINER = "comfyui"
DEFAULT_COMFY_INPUT = "/workspace/ComfyUI/input"
DEFAULT_COMFY_OUTPUT = "/workspace/ComfyUI/output"
DEFAULT_FISH_WORKFLOW = REPO_ROOT / "tools/_comfyui/workflows/asymmetric_fish_speech_api.json"
DEFAULT_ACE_WORKFLOW = REPO_ROOT / "tools/_comfyui/workflows/asymmetric_ace_step_api.json"

REQUIRED_NODE_CLASSES = {
    "fish": {"FishS2TTS", "SaveAudioMP3"},
    "ace": {
        "UNETLoader",
        "DualCLIPLoader",
        "TextEncodeAceStepAudio1.5",
        "EmptyAceStep1.5LatentAudio",
        "KSampler",
        "VAELoader",
        "VAEDecodeAudio",
        "SaveAudioMP3",
    },
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


class MVPError(RuntimeError):
    """Expected operator-facing failure."""


@dataclass
class StageResult:
    name: str
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MVPError(f"Missing workflow JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MVPError(f"Invalid JSON in {path}: {exc}") from exc


def read_narration(args: argparse.Namespace) -> str:
    if args.narration_text:
        text = args.narration_text
    elif args.narration_text_file:
        text = Path(args.narration_text_file).read_text(encoding="utf-8")
    else:
        raise MVPError("Provide --narration-text or --narration-text-file.")
    text = text.strip()
    if not text:
        raise MVPError("Narration text is empty.")
    return text


def resolve_storyboard_dir(raw: str, comfy_input_dir: Path) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return comfy_input_dir / path


def local_storyboard_frames(storyboard_dir: Path) -> list[Path]:
    if not storyboard_dir.exists():
        raise MVPError(f"Storyboard directory does not exist: {storyboard_dir}")
    if not storyboard_dir.is_dir():
        raise MVPError(f"Storyboard path is not a directory: {storyboard_dir}")
    frames = sorted(
        p for p in storyboard_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )
    if not frames:
        raise MVPError(f"Storyboard directory has no PNG/JPG frames: {storyboard_dir}")
    if not 3 <= len(frames) <= 10:
        raise MVPError(
            f"Storyboard must contain 3-10 PNG/JPG frames for MVP; found {len(frames)} in {storyboard_dir}"
        )
    return frames


def docker_exec(container: str, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "exec", container, "bash", "-lc", script],
        text=True,
        capture_output=True,
    )


def docker_cp_from(container: str, src: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    run_cmd(["docker", "cp", f"{container}:{src}", str(dst)])


def docker_cp_to(container: str, src: Path, dst: str) -> None:
    run_cmd(["docker", "cp", str(src), f"{container}:{dst}"])


def container_path_access(container: str, path: Path, *, readable: bool = False, writable: bool = False) -> tuple[bool, str]:
    tests = [f"test -e {shlex.quote(str(path))}"]
    if readable:
        tests.append(f"test -r {shlex.quote(str(path))}")
    if writable:
        tests.append(f"test -w {shlex.quote(str(path))}")
    proc = docker_exec(container, " && ".join(tests))
    if proc.returncode == 0:
        return True, "container"
    return False, (proc.stderr or proc.stdout or f"path check failed in container {container}").strip()


def container_storyboard_names(container: str, storyboard_dir: Path) -> list[str]:
    quoted = shlex.quote(str(storyboard_dir))
    proc = docker_exec(
        container,
        "find "
        + quoted
        + " -maxdepth 1 -type f \\( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \\) -printf '%f\\n' | sort",
    )
    if proc.returncode != 0:
        raise MVPError((proc.stderr or proc.stdout or f"Could not list storyboard in container: {storyboard_dir}").strip())
    names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not names:
        raise MVPError(f"Storyboard directory has no PNG/JPG frames: {storyboard_dir}")
    if not 3 <= len(names) <= 10:
        raise MVPError(
            f"Storyboard must contain 3-10 PNG/JPG frames for MVP; found {len(names)} in {storyboard_dir}"
        )
    return names


def materialize_storyboard_frames(
    *,
    storyboard_dir: Path,
    output_dir: Path,
    container: str,
    overwrite: bool,
) -> list[Path]:
    try:
        return local_storyboard_frames(storyboard_dir)
    except Exception:
        pass

    cache_dir = output_dir / "_storyboard_frames"
    if cache_dir.exists():
        if not overwrite:
            raise MVPError(f"Storyboard cache exists; pass --overwrite to refresh it: {cache_dir}")
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    docker_cp_from(container, str(storyboard_dir) + "/.", cache_dir)
    return local_storyboard_frames(cache_dir)


def workflow_node_classes(workflow: dict[str, Any]) -> set[str]:
    classes: set[str] = set()
    for node in workflow.values():
        if isinstance(node, dict) and node.get("class_type"):
            classes.add(str(node["class_type"]))
    return classes


def validate_workflow(path: Path, object_info: dict[str, Any]) -> dict[str, Any]:
    workflow = load_json(path)
    if not isinstance(workflow, dict) or not workflow:
        raise MVPError(f"Workflow must be a non-empty API-format object: {path}")
    classes = workflow_node_classes(workflow)
    missing = sorted(c for c in classes if c not in object_info)
    if missing:
        raise MVPError(f"Workflow {path} references missing ComfyUI node classes: {missing}")
    return workflow


def check_path(path: Path, *, readable: bool = False, writable: bool = False, label: str, container: str) -> str:
    if path.exists():
        if readable and not os.access(path, os.R_OK):
            raise MVPError(f"{label} is not readable: {path}")
        if writable and not os.access(path, os.W_OK):
            raise MVPError(f"{label} is not writable: {path}")
        return "host"

    ok, reason = container_path_access(container, path, readable=readable, writable=writable)
    if ok:
        return "container"
    raise MVPError(f"{label} is unavailable on host and container: {path}; {reason}")


def run_cmd(cmd: list[str], *, log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "$ " + " ".join(cmd) + "\n\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr,
            encoding="utf-8",
        )
    if proc.returncode != 0:
        raise MVPError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc


def ffprobe_duration(path: Path) -> float:
    proc = run_cmd([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    try:
        duration = float(proc.stdout.strip())
    except ValueError as exc:
        raise MVPError(f"Could not parse audio duration for {path}: {proc.stdout!r}") from exc
    if duration <= 0:
        raise MVPError(f"Audio duration must be > 0 for {path}; got {duration}")
    return duration


def free_comfy_memory(comfy_host: str) -> dict[str, Any]:
    url = comfy_host.rstrip("/") + "/free"
    try:
        response = requests.post(
            url,
            json={"unload_models": True, "free_memory": True},
            timeout=10,
        )
        return {"ok": response.ok, "status_code": response.status_code, "body": response.text[:500]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def patch_fish_workflow(workflow: dict[str, Any], *, text: str, episode_id: str) -> dict[str, dict[str, Any]]:
    return {
        "1": {"text": text, "keep_model_loaded": False},
        "2": {"filename_prefix": f"audio/{episode_id}_narration"},
    }


def patch_ace_workflow(
    workflow: dict[str, Any],
    *,
    prompt: str,
    duration: float,
    episode_id: str,
) -> dict[str, dict[str, Any]]:
    patches = {
        "3": {"tags": prompt, "duration": duration},
        "4": {"duration": duration},
        "5": {"seconds": duration},
        "9": {"filename_prefix": f"audio/{episode_id}_music_raw"},
    }
    if "6" in workflow:
        patches["6"] = {"seed": int(time.time()) % (2**32)}
    return patches


def run_comfy_audio_stage(
    *,
    client: ComfyUIClient,
    workflow_path: Path,
    patches: dict[str, dict[str, Any]],
    output_node: str,
    dest: Path,
    timeout: int,
    poll_interval: float,
) -> dict[str, Any]:
    workflow = client.load_workflow(workflow_path)
    workflow = client.patch_workflow(workflow, patches)
    return client.run_workflow(
        workflow,
        dest=dest,
        output_node=output_node,
        timeout_s=timeout,
        poll_interval_s=poll_interval,
        wait_for_queue=True,
        queue_timeout_s=120,
    )


def first_audio_output(run: dict[str, Any], expected_path: Path) -> Path:
    outputs = [Path(a["local_path"]) for a in run.get("artifacts", []) if a.get("local_path")]
    audio = [p for p in outputs if p.suffix.lower() in {".mp3", ".wav", ".ogg", ".flac"}]
    if not audio:
        raise MVPError(f"ComfyUI run produced no audio artifacts: {run}")
    src = audio[0]
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != expected_path.resolve():
        shutil.copy2(src, expected_path)
    return expected_path


def copy_to_comfy_input(src: Path, comfy_input_dir: Path, stable_name: str, container: str) -> str:
    if not src.exists():
        raise MVPError(f"Generated audio does not exist: {src}")
    dst = comfy_input_dir / stable_name
    if comfy_input_dir.exists() and os.access(comfy_input_dir, os.W_OK):
        shutil.copy2(src, dst)
        return str(dst)
    docker_cp_to(container, src, str(dst))
    return f"{container}:{dst}"


def write_frame_concat(frames: list[Path], target_duration: float, list_path: Path) -> None:
    per_frame = max(target_duration / len(frames), 0.25)
    lines: list[str] = []
    for frame in frames:
        escaped = str(frame.resolve()).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
        lines.append(f"duration {per_frame:.6f}")
    escaped_last = str(frames[-1].resolve()).replace("'", "'\\''")
    lines.append(f"file '{escaped_last}'")
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_roughcut(
    *,
    narration: Path,
    music: Path,
    frames: list[Path],
    output_dir: Path,
    episode_id: str,
    logs_dir: Path,
    overwrite: bool,
) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    narration = narration.resolve()
    music = music.resolve()
    frames = [frame.resolve() for frame in frames]
    for path, label in [(narration, "narration"), (music, "music")]:
        if not path.exists():
            raise MVPError(f"Missing {label} audio: {path}")

    duration = ffprobe_duration(narration)
    mix_path = output_dir / f"{episode_id}_mix.mp3"
    video_path = output_dir / f"{episode_id}_roughcut.mp4"
    concat_path = output_dir / f"{episode_id}_frames.txt"

    for path in [mix_path, video_path, concat_path]:
        if path.exists() and not overwrite:
            raise MVPError(f"Refusing to overwrite existing output without --overwrite: {path}")

    write_frame_concat(frames, duration, concat_path)
    overwrite_flag = "-y" if overwrite else "-n"

    run_cmd(
        [
            "ffmpeg",
            overwrite_flag,
            "-i",
            str(narration),
            "-stream_loop",
            "-1",
            "-i",
            str(music),
            "-filter_complex",
            "[1:a]volume=0.16[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map",
            "[a]",
            "-t",
            f"{duration:.3f}",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(mix_path),
        ],
        log_path=logs_dir / "ffmpeg_mix.log",
    )

    run_cmd(
        [
            "ffmpeg",
            overwrite_flag,
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-i",
            str(mix_path),
            "-vf",
            "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(video_path),
        ],
        log_path=logs_dir / "ffmpeg_roughcut.log",
    )

    return {
        "duration_seconds": duration,
        "mix_mp3": str(mix_path),
        "roughcut_mp4": str(video_path),
        "frame_concat": str(concat_path),
    }


def preflight(args: argparse.Namespace) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def ok(name: str, **data: Any) -> None:
        checks.append({"name": name, "ok": True, **data})

    def fail(name: str, error: str, **data: Any) -> None:
        checks.append({"name": name, "ok": False, "error": error, **data})

    comfy_input_dir = Path(args.comfy_input_dir).expanduser()
    comfy_output_dir = Path(args.comfy_output_dir).expanduser()
    storyboard_dir = resolve_storyboard_dir(args.storyboard_dir, comfy_input_dir)
    output_dir = Path(args.output_dir).expanduser()
    fish_workflow = Path(args.fish_workflow).expanduser()
    ace_workflow = Path(args.ace_workflow).expanduser()

    if REPO_ROOT.exists():
        ok("repo_path", repo_root=str(REPO_ROOT))
    else:
        fail("repo_path", f"Repo root not found: {REPO_ROOT}")

    ok("python", version=sys.version.split()[0])

    for cmd in ["ffmpeg", "ffprobe"]:
        found = shutil.which(cmd)
        if found:
            ok(cmd, path=found)
        else:
            fail(cmd, f"{cmd} not found on PATH")

    client = ComfyUIClient(args.comfy_host)
    object_info: dict[str, Any] | None = None
    try:
        stats = client.get_system_stats()
        device = (stats.get("devices") or [{}])[0]
        ok(
            "comfy_system_stats",
            server=args.comfy_host,
            device=device.get("name"),
            vram_free=device.get("vram_free"),
        )
    except Exception as exc:
        fail("comfy_system_stats", str(exc), server=args.comfy_host)

    try:
        queue = client.get_queue()
        ok(
            "comfy_queue",
            running=len(queue.get("queue_running") or []),
            pending=len(queue.get("queue_pending") or []),
        )
    except Exception as exc:
        fail("comfy_queue", str(exc))

    try:
        response = requests.get(args.comfy_host.rstrip("/") + "/object_info", timeout=20)
        response.raise_for_status()
        object_info = response.json()
        ok("comfy_object_info", node_class_count=len(object_info))
    except Exception as exc:
        fail("comfy_object_info", str(exc))

    if object_info is not None:
        required = sorted(REQUIRED_NODE_CLASSES["fish"] | REQUIRED_NODE_CLASSES["ace"])
        missing_required = [name for name in required if name not in object_info]
        if missing_required:
            fail("required_node_classes", f"Missing required node classes: {missing_required}")
        else:
            ok("required_node_classes", count=len(required))

        for label, path in [("fish_workflow", fish_workflow), ("ace_workflow", ace_workflow)]:
            try:
                workflow = validate_workflow(path, object_info)
                ok(label, path=str(path), nodes=len(workflow), classes=sorted(workflow_node_classes(workflow)))
            except Exception as exc:
                fail(label, str(exc), path=str(path))
    else:
        fail("workflow_validation", "Skipped because /object_info failed")

    for label, path, readable, writable in [
        ("comfy_input_dir", comfy_input_dir, True, True),
        ("comfy_output_dir", comfy_output_dir, True, False),
    ]:
        try:
            mode = check_path(path, readable=readable, writable=writable, label=label, container=args.comfy_container)
            ok(label, path=str(path), access=mode)
        except Exception as exc:
            fail(label, str(exc), path=str(path))

    try:
        try:
            frames = local_storyboard_frames(storyboard_dir)
            ok("storyboard_frames", path=str(storyboard_dir), count=len(frames), frames=[p.name for p in frames], access="host")
        except Exception:
            names = container_storyboard_names(args.comfy_container, storyboard_dir)
            ok("storyboard_frames", path=str(storyboard_dir), count=len(names), frames=names, access="container")
    except Exception as exc:
        fail("storyboard_frames", str(exc), path=str(storyboard_dir))

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(output_dir)
        free_gb = usage.free / (1024**3)
        if free_gb < 2:
            fail("disk_space", f"Less than 2 GB free in output dir: {free_gb:.2f} GB", path=str(output_dir))
        else:
            ok("disk_space", free_gb=round(free_gb, 2), path=str(output_dir))
    except Exception as exc:
        fail("disk_space", str(exc), path=str(output_dir))

    outputs = [
        output_dir / f"{args.episode_id}_narration.mp3",
        output_dir / f"{args.episode_id}_music_raw.mp3",
        output_dir / f"{args.episode_id}_mix.mp3",
        output_dir / f"{args.episode_id}_roughcut.mp4",
        output_dir / "run_manifest.json",
    ]
    existing = [str(p) for p in outputs if p.exists()]
    if existing and not args.overwrite:
        fail("overwrite_guard", "Existing outputs require --overwrite", existing=existing)
    else:
        ok("overwrite_guard", existing=existing, overwrite=args.overwrite)

    return {
        "ok": all(item["ok"] for item in checks),
        "checks": checks,
        "normalized": {
            "repo_root": str(REPO_ROOT),
            "comfy_host": args.comfy_host,
            "comfy_container": args.comfy_container,
            "comfy_input_dir": str(comfy_input_dir),
            "comfy_output_dir": str(comfy_output_dir),
            "storyboard_dir": str(storyboard_dir),
            "output_dir": str(output_dir),
            "fish_workflow": str(fish_workflow),
            "ace_workflow": str(ace_workflow),
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    pre = preflight(args)
    if not pre["ok"]:
        return {"status": "error", "stage": "preflight", "preflight": pre}
    if args.dry_run:
        return {"status": "success", "stage": "dry_run", "preflight": pre}

    text = read_narration(args)
    output_dir = Path(args.output_dir).expanduser()
    logs_dir = output_dir / "logs"
    comfy_input_dir = Path(args.comfy_input_dir).expanduser()
    storyboard_dir = resolve_storyboard_dir(args.storyboard_dir, comfy_input_dir)
    frames = materialize_storyboard_frames(
        storyboard_dir=storyboard_dir,
        output_dir=output_dir,
        container=args.comfy_container,
        overwrite=args.overwrite,
    )
    fish_workflow = Path(args.fish_workflow).expanduser()
    ace_workflow = Path(args.ace_workflow).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "episode_id": args.episode_id,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inputs": {
            "music_prompt": args.music_prompt,
            "music_duration": args.music_duration,
            "storyboard_dir": str(storyboard_dir),
            "frame_count": len(frames),
        },
        "stages": [],
    }

    def record(result: StageResult) -> None:
        manifest["stages"].append({
            "name": result.name,
            "ok": result.ok,
            "data": result.data,
            "error": result.error,
        })
        (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    client = ComfyUIClient(args.comfy_host)

    narration = output_dir / f"{args.episode_id}_narration.mp3"
    music = output_dir / f"{args.episode_id}_music_raw.mp3"

    try:
        if args.reuse_existing_audio and narration.exists():
            narration_input = copy_to_comfy_input(narration, comfy_input_dir, f"{args.episode_id}_narration.mp3", args.comfy_container)
            record(StageResult("fish_narration", True, {"reused": True, "output": str(narration), "comfy_input_copy": narration_input}))
        else:
            narration_run = run_comfy_audio_stage(
                client=client,
                workflow_path=fish_workflow,
                patches=patch_fish_workflow(load_json(fish_workflow), text=text, episode_id=args.episode_id),
                output_node="2",
                dest=output_dir / f"{args.episode_id}_narration_from_comfy",
                timeout=args.timeout,
                poll_interval=args.poll_interval,
            )
            narration = first_audio_output(narration_run, narration)
            narration_input = copy_to_comfy_input(
                narration,
                comfy_input_dir,
                f"{args.episode_id}_narration.mp3",
                args.comfy_container,
            )
            record(StageResult("fish_narration", True, {"run": narration_run, "output": str(narration), "comfy_input_copy": str(narration_input)}))
    except Exception as exc:
        record(StageResult("fish_narration", False, error=str(exc)))
        return {"status": "error", "stage": "fish_narration", "error": str(exc), "manifest": str(output_dir / "run_manifest.json")}

    if args.free_between_stages and not (args.reuse_existing_audio and music.exists()):
        record(StageResult("free_after_fish", True, free_comfy_memory(args.comfy_host)))

    try:
        if args.reuse_existing_audio and music.exists():
            music_input = copy_to_comfy_input(music, comfy_input_dir, f"{args.episode_id}_music_raw.mp3", args.comfy_container)
            record(StageResult("ace_music", True, {"reused": True, "output": str(music), "comfy_input_copy": music_input}))
        else:
            music_run = run_comfy_audio_stage(
                client=client,
                workflow_path=ace_workflow,
                patches=patch_ace_workflow(
                    load_json(ace_workflow),
                    prompt=args.music_prompt,
                    duration=float(args.music_duration),
                    episode_id=args.episode_id,
                ),
                output_node="9",
                dest=output_dir / f"{args.episode_id}_music_raw_from_comfy",
                timeout=args.timeout,
                poll_interval=args.poll_interval,
            )
            music = first_audio_output(music_run, music)
            music_input = copy_to_comfy_input(
                music,
                comfy_input_dir,
                f"{args.episode_id}_music_raw.mp3",
                args.comfy_container,
            )
            record(StageResult("ace_music", True, {"run": music_run, "output": str(music), "comfy_input_copy": str(music_input)}))
    except Exception as exc:
        record(StageResult("ace_music", False, error=str(exc)))
        return {"status": "error", "stage": "ace_music", "error": str(exc), "manifest": str(output_dir / "run_manifest.json")}

    if args.free_between_stages:
        record(StageResult("free_after_ace", True, free_comfy_memory(args.comfy_host)))

    try:
        roughcut = make_roughcut(
            narration=output_dir / f"{args.episode_id}_narration.mp3",
            music=output_dir / f"{args.episode_id}_music_raw.mp3",
            frames=frames,
            output_dir=output_dir,
            episode_id=args.episode_id,
            logs_dir=logs_dir,
            overwrite=args.overwrite,
        )
        record(StageResult("roughcut_ffmpeg", True, roughcut))
    except Exception as exc:
        record(StageResult("roughcut_ffmpeg", False, error=str(exc)))
        return {"status": "error", "stage": "roughcut_ffmpeg", "error": str(exc), "manifest": str(output_dir / "run_manifest.json")}

    manifest["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "status": "success",
        "episode_id": args.episode_id,
        "narration_mp3": str(output_dir / f"{args.episode_id}_narration.mp3"),
        "music_mp3": str(output_dir / f"{args.episode_id}_music_raw.mp3"),
        "mix_mp3": str(output_dir / f"{args.episode_id}_mix.mp3"),
        "roughcut_mp4": str(output_dir / f"{args.episode_id}_roughcut.mp4"),
        "manifest": str(output_dir / "run_manifest.json"),
    }


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--narration-text")
    parser.add_argument("--narration-text-file")
    parser.add_argument("--music-prompt", default="dark investigative documentary underscore, ambient tension, restrained, sparse percussion, low pulse, cinematic, no vocals")
    parser.add_argument("--music-duration", type=float, default=20.0)
    parser.add_argument("--storyboard-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--comfy-host", default=os.environ.get("COMFYUI_SERVER_URL", DEFAULT_COMFY_HOST))
    parser.add_argument("--comfy-container", default=os.environ.get("COMFYUI_CONTAINER", DEFAULT_COMFY_CONTAINER))
    parser.add_argument("--comfy-input-dir", default=os.environ.get("COMFYUI_INPUT_DIR", DEFAULT_COMFY_INPUT))
    parser.add_argument("--comfy-output-dir", default=os.environ.get("COMFYUI_OUTPUT_DIR", DEFAULT_COMFY_OUTPUT))
    parser.add_argument("--fish-workflow", default=str(DEFAULT_FISH_WORKFLOW))
    parser.add_argument("--ace-workflow", default=str(DEFAULT_ACE_WORKFLOW))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--free-between-stages", action="store_true")
    parser.add_argument("--reuse-existing-audio", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Asymmetric MVP ComfyUI audio + ffmpeg roughcut runner")
    sub = parser.add_subparsers(dest="command", required=True)
    preflight_parser = sub.add_parser("preflight", help="Validate host, ComfyUI, workflows, and storyboard inputs")
    add_common_args(preflight_parser)
    run_parser = sub.add_parser("run", help="Run narration, music, and roughcut assembly")
    add_common_args(run_parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "preflight":
            result = preflight(args)
            print_json(result)
            return 0 if result["ok"] else 2
        result = run(args)
        print_json(result)
        return 0 if result.get("status") == "success" else 1
    except MVPError as exc:
        print_json({"status": "error", "error": str(exc)})
        return 1
    except KeyboardInterrupt:
        print_json({"status": "error", "error": "Interrupted"})
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
