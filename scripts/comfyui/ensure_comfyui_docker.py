#!/usr/bin/env python3
"""Ensure pipeline-managed Dockerized ComfyUI is available safely.

This helper is intentionally conservative:
- It reuses a healthy existing ComfyUI API/container.
- It inspects GPU users before launching a managed Docker service.
- It never kills unknown GPU processes.
- It only stops allowlisted Docker containers, and only when policy allows it.

Typical usage:
    python3 scripts/comfyui/ensure_comfyui_docker.py status
    python3 scripts/comfyui/ensure_comfyui_docker.py ensure --dry-run
    python3 scripts/comfyui/ensure_comfyui_docker.py ensure
    python3 scripts/comfyui/ensure_comfyui_docker.py free
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency normally present in repo
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "pipeline_defs" / "support" / "comfyui-gpu-lifecycle.yaml"
DEFAULT_COMPOSE = ROOT / "docker-compose.comfyui.yml"


@dataclass
class Cmd:
    code: int
    stdout: str
    stderr: str


def run(cmd: list[str], *, timeout: int = 30, check: bool = False, env: dict[str, str] | None = None) -> Cmd:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    result = Cmd(proc.returncode, proc.stdout.strip(), proc.stderr.strip())
    if check and result.code != 0:
        raise RuntimeError(f"command failed ({result.code}): {' '.join(cmd)}\n{result.stderr}")
    return result


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    text = os.path.expandvars(text)
    return yaml.safe_load(text)


def http_json(url: str, *, timeout: int = 5, method: str = "GET", data: dict[str, Any] | None = None) -> tuple[bool, Any]:
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw:
                return True, None
            try:
                return True, json.loads(raw)
            except json.JSONDecodeError:
                return True, raw
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        return False, str(exc)


def docker_available() -> bool:
    return run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=10).code == 0


def docker_compose_cmd() -> list[str]:
    if run(["docker", "compose", "version"], timeout=10).code == 0:
        return ["docker", "compose"]
    if run(["docker-compose", "version"], timeout=10).code == 0:
        return ["docker-compose"]
    raise RuntimeError("docker compose is not available")


def docker_containers() -> list[dict[str, str]]:
    fmt = "{{json .}}"
    out = run(["docker", "ps", "-a", "--format", fmt], timeout=20)
    if out.code != 0 or not out.stdout:
        return []
    rows = []
    for line in out.stdout.splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def managed_container(config: dict[str, Any]) -> dict[str, str] | None:
    name = config["comfyui"].get("container_name", "openmontage-comfyui")
    for row in docker_containers():
        names = row.get("Names", "")
        if names == name:
            return row
    return None


def comfy_api_healthy(config: dict[str, Any]) -> tuple[bool, Any]:
    base = config["comfyui"].get("base_url") or f"http://{config['comfyui'].get('host','127.0.0.1')}:{config['comfyui'].get('port',8188)}"
    ok, payload = http_json(base.rstrip("/") + config["comfyui"].get("health_endpoint", "/system_stats"), timeout=5)
    if not ok:
        return False, payload
    queue_ok, queue_payload = http_json(base.rstrip("/") + config["comfyui"].get("queue_endpoint", "/queue"), timeout=5)
    return bool(queue_ok), {"system_stats": payload, "queue": queue_payload if queue_ok else None}


def gpu_summary() -> dict[str, Any]:
    gpu = run([
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.used,memory.free",
        "--format=csv,noheader,nounits",
    ], timeout=10)
    apps = run([
        "nvidia-smi",
        "--query-compute-apps=pid,process_name,used_memory",
        "--format=csv,noheader,nounits",
    ], timeout=10)
    result: dict[str, Any] = {"available": gpu.code == 0, "gpus": [], "apps": []}
    if gpu.code == 0 and gpu.stdout:
        for line in gpu.stdout.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                result["gpus"].append({
                    "name": parts[0],
                    "memory_total_mb": int(parts[1]),
                    "memory_used_mb": int(parts[2]),
                    "memory_free_mb": int(parts[3]),
                })
    if apps.code == 0 and apps.stdout:
        for line in apps.stdout.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3 and parts[0].isdigit():
                result["apps"].append({"pid": int(parts[0]), "process_name": parts[1], "used_memory_mb": int(parts[2])})
    return result


def process_details(pid: int) -> dict[str, str]:
    out = run(["ps", "-o", "pid=,ppid=,user=,comm=,args=", "-p", str(pid)], timeout=10)
    return {"pid": str(pid), "ps": out.stdout}


def classify_gpu_apps(config: dict[str, Any], apps: list[dict[str, Any]]) -> dict[str, Any]:
    never = [re.compile(re.escape(x), re.I) for x in config.get("gpu_never_kill", [])]
    allow = config.get("gpu_unload_allowlist", []) or []
    classified = {"never": [], "allowlisted": [], "unknown": []}
    for app in apps:
        name = app.get("process_name", "")
        detail = process_details(app["pid"])
        haystack = f"{name}\n{detail.get('ps','')}"
        if any(rx.search(haystack) for rx in never):
            classified["never"].append({**app, "detail": detail})
            continue
        matched = None
        for rule in allow:
            pattern = str(rule.get("match", ""))
            if pattern and re.search(re.escape(pattern), haystack, re.I):
                matched = rule
                break
        if matched:
            classified["allowlisted"].append({**app, "detail": detail, "rule": matched})
        else:
            classified["unknown"].append({**app, "detail": detail})
    return classified


def stop_allowlisted_docker_containers(classified: dict[str, Any], *, allow_preserved: bool, dry_run: bool) -> list[dict[str, Any]]:
    actions = []
    containers = docker_containers()
    for app in classified["allowlisted"]:
        rule = app["rule"]
        action = rule.get("action", "report_only")
        preserved = bool(rule.get("preserve_by_default", False))
        if action == "report_only":
            actions.append({"pid": app["pid"], "rule": rule.get("name"), "action": "report_only", "status": "skipped"})
            continue
        if preserved and not allow_preserved:
            actions.append({"pid": app["pid"], "rule": rule.get("name"), "action": action, "status": "preserved_abort"})
            continue
        if action != "docker_stop":
            actions.append({"pid": app["pid"], "rule": rule.get("name"), "action": action, "status": "unsupported_action"})
            continue
        ps_text = app.get("detail", {}).get("ps", "")
        matches = []
        for c in containers:
            ident = f"{c.get('ID','')} {c.get('Names','')} {c.get('Image','')}"
            if c.get("Names") and c.get("Names") in ps_text:
                matches.append(c)
            elif rule.get("match") and re.search(re.escape(str(rule["match"])), ident, re.I):
                matches.append(c)
        if not matches:
            actions.append({"pid": app["pid"], "rule": rule.get("name"), "action": action, "status": "no_container_match"})
            continue
        for c in matches:
            item = {"container": c.get("Names"), "id": c.get("ID"), "rule": rule.get("name"), "action": "docker_stop"}
            if dry_run:
                item["status"] = "dry_run"
            else:
                res = run(["docker", "stop", c.get("ID", c.get("Names", ""))], timeout=60)
                item["status"] = "stopped" if res.code == 0 else "failed"
                item["stderr"] = res.stderr
            actions.append(item)
    return actions


def ensure(config: dict[str, Any], *, dry_run: bool, allow_preserved: bool) -> dict[str, Any]:
    status = collect_status(config)
    if status["comfyui_api_healthy"]:
        return {"status": "ready", "reused_existing": True, "details": status}
    if not status["docker_available"]:
        return {"status": "error", "error": "Docker is not available", "details": status}
    gpu = status["gpu"]
    if not gpu.get("available"):
        return {"status": "error", "error": "nvidia-smi is not available or no NVIDIA GPU visible", "details": status}
    required = str(config["comfyui"].get("required_gpu_name_contains", "")).strip()
    if required and not any(required.lower() in g["name"].lower() for g in gpu.get("gpus", [])):
        return {"status": "error", "error": f"Required GPU marker {required!r} not found", "details": status}
    min_free_mb = int(config["comfyui"].get("min_free_vram_mb_before_launch", 0) or 0)
    free_mb = max((int(g.get("memory_free_mb", 0)) for g in gpu.get("gpus", [])), default=0)
    classified = classify_gpu_apps(config, gpu.get("apps", []))
    if classified["unknown"]:
        return {"status": "blocked", "error": "Unknown GPU processes are active; refusing to stop them", "classified_gpu_apps": classified, "details": status}
    actions = stop_allowlisted_docker_containers(classified, allow_preserved=allow_preserved, dry_run=dry_run)
    hard_fail_statuses = {"preserved_abort", "failed", "unsupported_action", "no_container_match"}
    if any(a.get("status") in hard_fail_statuses for a in actions):
        return {"status": "blocked", "error": "Allowlisted GPU workload could not be safely unloaded", "actions": actions, "classified_gpu_apps": classified, "details": status}
    report_only_actions = [a for a in actions if a.get("status") == "skipped" and a.get("action") == "report_only"]
    never_kill_active = classified.get("never", [])
    if min_free_mb and free_mb < min_free_mb and (report_only_actions or never_kill_active):
        return {
            "status": "blocked",
            "error": "Insufficient free VRAM and active protected/report-only GPU workloads remain; refusing to launch ComfyUI",
            "min_free_vram_mb_before_launch": min_free_mb,
            "current_free_vram_mb": free_mb,
            "actions": actions,
            "classified_gpu_apps": classified,
            "details": status,
        }
    if min_free_mb and free_mb < min_free_mb and not actions:
        return {
            "status": "blocked",
            "error": "Insufficient free VRAM for ComfyUI launch",
            "min_free_vram_mb_before_launch": min_free_mb,
            "current_free_vram_mb": free_mb,
            "details": status,
        }
    if dry_run:
        return {"status": "dry_run", "would_launch": True, "actions": actions, "details": status, "current_free_vram_mb": free_mb, "min_free_vram_mb_before_launch": min_free_mb}
    compose = docker_compose_cmd()
    compose_file = ROOT / config["comfyui"].get("compose_file", "docker-compose.comfyui.yml")
    env = os.environ.copy()
    env.setdefault("OPENMONTAGE_ROOT", str(ROOT))
    env.setdefault("COMFYUI_CONTAINER_NAME", config["comfyui"].get("container_name", "openmontage-comfyui"))
    env.setdefault("COMFYUI_PORT", str(config["comfyui"].get("port", 8188)))
    env.setdefault("COMFYUI_WORKSPACE", config["comfyui"].get("workspace", "/home/pop/comfy/ComfyUI"))
    launch = run(compose + ["-f", str(compose_file), "up", "-d", config["comfyui"].get("service", "comfyui")], timeout=300, env=env)
    if launch.code != 0:
        return {"status": "error", "error": "docker compose launch failed", "stderr": launch.stderr, "actions": actions}
    timeout = int(config["comfyui"].get("startup_timeout_seconds", 180))
    interval = int(config["comfyui"].get("poll_interval_seconds", 2))
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        ok, payload = comfy_api_healthy(config)
        if ok:
            return {"status": "ready", "reused_existing": False, "actions": actions, "system_stats": payload}
        last = payload
        time.sleep(interval)
    logs = run(["docker", "logs", "--tail=200", config["comfyui"].get("container_name", "openmontage-comfyui")], timeout=20)
    return {"status": "error", "error": "ComfyUI did not become healthy before timeout", "last_health_error": last, "logs": logs.stdout or logs.stderr}


def free(config: dict[str, Any]) -> dict[str, Any]:
    base = config["comfyui"].get("base_url") or f"http://{config['comfyui'].get('host','127.0.0.1')}:{config['comfyui'].get('port',8188)}"
    ok, payload = http_json(base.rstrip("/") + config["comfyui"].get("free_endpoint", "/free"), method="POST", data={"unload_models": True, "free_memory": True}, timeout=20)
    return {"status": "success" if ok else "error", "response": payload}


def collect_status(config: dict[str, Any]) -> dict[str, Any]:
    healthy, payload = comfy_api_healthy(config)
    return {
        "docker_available": docker_available(),
        "managed_container": managed_container(config),
        "comfyui_api_healthy": healthy,
        "comfyui_api_payload": payload,
        "gpu": gpu_summary(),
    }


def stop(config: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    row = managed_container(config)
    if not row:
        return {"status": "noop", "message": "managed container not found"}
    if dry_run:
        return {"status": "dry_run", "would_stop": row}
    res = run(["docker", "stop", row.get("ID", row.get("Names", ""))], timeout=60)
    return {"status": "stopped" if res.code == 0 else "error", "stderr": res.stderr, "container": row}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "ensure", "free", "stop"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-preserved-stop", action="store_true", help="Allow stopping allowlisted services marked preserve_by_default")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.command == "status":
        result = collect_status(config)
    elif args.command == "ensure":
        result = ensure(config, dry_run=args.dry_run, allow_preserved=args.allow_preserved_stop)
    elif args.command == "free":
        result = free(config)
    elif args.command == "stop":
        result = stop(config, dry_run=args.dry_run)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") not in {"error", "blocked"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
