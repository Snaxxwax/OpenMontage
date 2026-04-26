"""Shared ComfyUI REST client.

This is the backend abstraction for running arbitrary ComfyUI workflows from
OpenMontage tools. It supports:

- Server health + system stats (/system_stats)
- Queue inspection (/queue)
- Workflow submit/poll/download (/prompt, /history/{id}, /view)
- Optional image upload for I2V workflows (/upload/image)
- Best-effort model discovery via /object_info/{NodeClass}

NOTE: ComfyUI is the execution layer. VRAM/RAM management is primarily handled
by the ComfyUI server configuration (e.g. --lowvram/offload). This client
adds lightweight governance: optional queue/resource gating + clear errors.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

import requests


class ComfyUIError(RuntimeError):
    """Raised when ComfyUI returns an error or violates expected contracts."""


@dataclass(frozen=True)
class ComfyUIArtifact:
    node_id: str
    filename: str
    subfolder: str
    file_type: str

    @property
    def suffix(self) -> str:
        return Path(self.filename).suffix


def _resolve_server_url(explicit: str | None, *, capability: str | None = None) -> tuple[str, bool]:
    """Resolve the ComfyUI base URL and whether it's a default.

    Precedence:
      1) explicit argument
      2) per-capability env vars (COMFYUI_IMAGE_SERVER_URL, etc)
      3) global env vars (COMFYUI_SERVER_URL, COMFYUI_BASE_URL legacy)
      4) default http://127.0.0.1:8188
    """
    if explicit:
        return explicit.rstrip("/"), False

    cap_map = {
        "image_generation": "COMFYUI_IMAGE_SERVER_URL",
        "video_generation": "COMFYUI_VIDEO_SERVER_URL",
        "music_generation": "COMFYUI_AUDIO_SERVER_URL",
    }
    if capability and cap_map.get(capability) and os.environ.get(cap_map[capability]):
        return os.environ[cap_map[capability]].rstrip("/"), False

    if os.environ.get("COMFYUI_SERVER_URL"):
        return os.environ["COMFYUI_SERVER_URL"].rstrip("/"), False

    # Legacy name kept for backward compatibility with earlier OpenMontage checkouts.
    if os.environ.get("COMFYUI_BASE_URL"):
        return os.environ["COMFYUI_BASE_URL"].rstrip("/"), False

    return "http://127.0.0.1:8188", True


class ComfyUIClient:
    """Thin client for the ComfyUI REST API."""

    def __init__(self, server_url: str | None = None, *, capability: str | None = None) -> None:
        url, is_default = _resolve_server_url(server_url, capability=capability)
        self.server_url = url
        self._is_default_url = is_default
        self._models_cache: dict[str, list[str]] | None = None
        self._models_cache_at: float | None = None

    @property
    def is_default_url(self) -> bool:
        return self._is_default_url

    # ------------------------------------------------------------------
    # Health / stats / queue
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.server_url}/system_stats", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def get_system_stats(self) -> dict[str, Any]:
        resp = requests.get(f"{self.server_url}/system_stats", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_queue(self) -> dict[str, Any]:
        resp = requests.get(f"{self.server_url}/queue", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def unavailable_reason(self) -> str:
        if self.is_default_url:
            return (
                f"No ComfyUI server reachable at {self.server_url} (default).\n"
                f"Start ComfyUI and/or set COMFYUI_SERVER_URL (or legacy COMFYUI_BASE_URL) in `.env`."
            )
        return (
            f"ComfyUI server not reachable at {self.server_url}.\n"
            f"Check that ComfyUI is running and the URL is correct."
        )

    def wait_for_queue(
        self,
        *,
        max_running: int = 0,
        max_pending: int = 0,
        timeout_s: int = 60,
        interval_s: float = 2.0,
    ) -> None:
        """Block until the queue is below thresholds (or timeout)."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            q = self.get_queue()
            running = len(q.get("queue_running") or [])
            pending = len(q.get("queue_pending") or [])
            if running <= max_running and pending <= max_pending:
                return
            time.sleep(interval_s)
        raise ComfyUIError(
            f"ComfyUI queue did not drain within {timeout_s}s "
            f"(running={running}, pending={pending})."
        )

    def wait_for_resources(
        self,
        *,
        min_vram_free_mb: int | None = None,
        min_ram_free_mb: int | None = None,
        timeout_s: int = 60,
        interval_s: float = 2.0,
    ) -> None:
        """Best-effort gating based on /system_stats free RAM/VRAM."""
        if min_vram_free_mb is None and min_ram_free_mb is None:
            return

        deadline = time.time() + timeout_s
        last_stats: dict[str, Any] | None = None
        while time.time() < deadline:
            stats = self.get_system_stats()
            last_stats = stats
            ram_free = int(stats.get("system", {}).get("ram_free") or 0) // (1024 * 1024)
            vram_free = 0
            devices = stats.get("devices") or []
            if devices:
                vram_free = int(devices[0].get("vram_free") or 0) // (1024 * 1024)

            ok = True
            if min_ram_free_mb is not None and ram_free < min_ram_free_mb:
                ok = False
            if min_vram_free_mb is not None and vram_free < min_vram_free_mb:
                ok = False
            if ok:
                return
            time.sleep(interval_s)

        snapshot = {}
        if last_stats:
            snapshot = {
                "ram_free_mb": int(last_stats.get("system", {}).get("ram_free") or 0) // (1024 * 1024),
                "vram_free_mb": int((last_stats.get("devices") or [{}])[0].get("vram_free") or 0) // (1024 * 1024),
            }
        raise ComfyUIError(
            f"ComfyUI resources did not meet requested minimums within {timeout_s}s. "
            f"Snapshot: {snapshot}"
        )

    # ------------------------------------------------------------------
    # Model discovery (best-effort)
    # ------------------------------------------------------------------

    def list_models(self, *, cache_ttl_s: int = 30) -> dict[str, list[str]]:
        """Query ComfyUI for available model filenames (grouped by type)."""
        now = time.time()
        if self._models_cache and self._models_cache_at and (now - self._models_cache_at) < cache_ttl_s:
            return self._models_cache

        node_to_key: dict[str, tuple[str, str]] = {
            "CheckpointLoaderSimple": ("ckpt_name", "checkpoints"),
            "UNETLoader": ("unet_name", "diffusion_models"),
            "VAELoader": ("vae_name", "vae"),
            "CLIPLoader": ("clip_name", "clip"),
            "LoraLoaderModelOnly": ("lora_name", "loras"),
        }

        result: dict[str, list[str]] = {}
        for node_class, (field, group) in node_to_key.items():
            try:
                resp = requests.get(f"{self.server_url}/object_info/{node_class}", timeout=10)
                resp.raise_for_status()
                data = resp.json()
                options = (
                    data.get(node_class, {})
                    .get("input", {})
                    .get("required", {})
                    .get(field, [[]])[0]
                )
                if isinstance(options, list):
                    result[group] = list(options)
                else:
                    result[group] = []
            except Exception:
                result[group] = []

        self._models_cache = result
        self._models_cache_at = now
        return result

    def check_models(self, required: Iterable[str]) -> tuple[list[str], list[str]]:
        """Check which required model filenames are available (best-effort)."""
        all_models: set[str] = set()
        for names in self.list_models().values():
            all_models.update(names)
        found = [m for m in required if m in all_models]
        missing = [m for m in required if m not in all_models]
        return found, missing

    @staticmethod
    def infer_required_models_from_workflow(workflow: dict[str, Any]) -> list[str]:
        """Best-effort scan of a workflow JSON for referenced model filenames."""
        # class_type -> list of input keys that usually contain model filenames
        model_fields: dict[str, list[str]] = {
            "CheckpointLoaderSimple": ["ckpt_name"],
            "UNETLoader": ["unet_name"],
            "VAELoader": ["vae_name"],
            "CLIPLoader": ["clip_name"],
            "LoraLoaderModelOnly": ["lora_name"],
            # Common custom-node conventions (not always discoverable via object_info)
            "WanVideoModelLoader": ["model"],
            "WanVideoVAELoader": ["model_name"],
            "LoadWanVideoT5TextEncoder": ["model_name"],
        }

        required: list[str] = []
        for node in workflow.values():
            if not isinstance(node, dict):
                continue
            class_type = str(node.get("class_type", ""))
            keys = model_fields.get(class_type)
            if not keys:
                continue
            inputs = node.get("inputs") or {}
            if not isinstance(inputs, dict):
                continue
            for key in keys:
                value = inputs.get(key)
                if isinstance(value, str) and value:
                    required.append(value)
        # Preserve order while de-duping
        seen: set[str] = set()
        out: list[str] = []
        for item in required:
            if item not in seen:
                out.append(item)
                seen.add(item)
        return out

    # ------------------------------------------------------------------
    # Workflow helpers
    # ------------------------------------------------------------------

    @staticmethod
    def load_workflow(path: Path) -> dict[str, Any]:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def workflow_hash(workflow: dict[str, Any]) -> str:
        raw = json.dumps(workflow, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def patch_workflow(workflow: dict[str, Any], patches: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Deep-copy workflow and apply node input patches (node_id -> inputs)."""
        w = copy.deepcopy(workflow)
        for node_id, values in patches.items():
            if node_id not in w:
                raise ComfyUIError(
                    f"Node {node_id!r} not found in workflow. Available: {list(w.keys())}"
                )
            node = w[node_id]
            node.setdefault("inputs", {})
            if not isinstance(node["inputs"], dict):
                raise ComfyUIError(f"Node {node_id!r} has non-dict inputs.")
            for key, val in values.items():
                node["inputs"][key] = val
        return w

    @staticmethod
    def random_seed() -> int:
        return random.randint(0, 2**32 - 1)

    # ------------------------------------------------------------------
    # Core submit/poll/download
    # ------------------------------------------------------------------

    def submit(self, workflow: dict[str, Any], *, client_id: str | None = None) -> str:
        payload: dict[str, Any] = {"prompt": workflow}
        payload["client_id"] = client_id or str(uuid.uuid4())

        resp = requests.post(f"{self.server_url}/prompt", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("node_errors"):
            raise ComfyUIError(f"Node errors: {json.dumps(data['node_errors'])}")
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyUIError(f"No prompt_id in response: {data}")
        return str(prompt_id)

    def poll(
        self,
        prompt_id: str,
        *,
        timeout_s: int = 600,
        interval_s: float = 5.0,
    ) -> dict[str, Any]:
        deadline = time.time() + timeout_s
        last_status: str | None = None
        while time.time() < deadline:
            resp = requests.get(f"{self.server_url}/history/{prompt_id}", timeout=15)
            resp.raise_for_status()
            history = resp.json()
            entry = history.get(prompt_id)
            if not entry:
                time.sleep(interval_s)
                continue

            status = (entry.get("status") or {}).get("status_str")
            last_status = status or last_status
            if status == "error":
                msgs = (entry.get("status") or {}).get("messages", [])
                raise ComfyUIError(f"ComfyUI execution error: {msgs}")
            if status != "success":
                time.sleep(interval_s)
                continue
            return entry

        raise ComfyUIError(
            f"Prompt {prompt_id} did not complete within {timeout_s}s (last_status={last_status})"
        )

    def download(self, *, filename: str, subfolder: str = "", file_type: str = "output", dest: Path) -> Path:
        resp = requests.get(
            f"{self.server_url}/view",
            params={"filename": filename, "subfolder": subfolder, "type": file_type},
            timeout=180,
        )
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        return dest

    def upload_image(self, *, local_path: Path, name: str, overwrite: bool = True) -> str:
        with open(local_path, "rb") as f:
            resp = requests.post(
                f"{self.server_url}/upload/image",
                files={"image": (name, f, "application/octet-stream")},
                data={"overwrite": "true" if overwrite else "false"},
                timeout=60,
            )
        resp.raise_for_status()
        payload = resp.json()
        if "name" not in payload:
            raise ComfyUIError(f"Unexpected upload response: {payload}")
        return str(payload["name"])

    # ------------------------------------------------------------------
    # Output extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_file_dicts(value: Any) -> Iterator[dict[str, Any]]:
        if isinstance(value, dict):
            if isinstance(value.get("filename"), str) and value["filename"]:
                yield value
                return
            for v in value.values():
                yield from ComfyUIClient._iter_file_dicts(v)
        elif isinstance(value, list):
            for item in value:
                yield from ComfyUIClient._iter_file_dicts(item)

    @staticmethod
    def extract_artifacts(entry: dict[str, Any], *, output_node: str | None = None) -> list[ComfyUIArtifact]:
        outputs = entry.get("outputs") or {}
        if not isinstance(outputs, dict):
            return []

        node_ids: Iterable[str]
        if output_node is not None:
            node_ids = [output_node]
        else:
            node_ids = outputs.keys()

        artifacts: list[ComfyUIArtifact] = []
        for node_id in node_ids:
            node_output = outputs.get(str(node_id)) or {}
            for file_dict in ComfyUIClient._iter_file_dicts(node_output):
                artifacts.append(
                    ComfyUIArtifact(
                        node_id=str(node_id),
                        filename=str(file_dict.get("filename", "")),
                        subfolder=str(file_dict.get("subfolder", "")),
                        file_type=str(file_dict.get("type", "output") or "output"),
                    )
                )

        # De-dupe
        seen: set[tuple[str, str, str, str]] = set()
        unique: list[ComfyUIArtifact] = []
        for a in artifacts:
            key = (a.node_id, a.filename, a.subfolder, a.file_type)
            if key in seen:
                continue
            unique.append(a)
            seen.add(key)
        return unique

    def download_artifacts(self, artifacts: list[ComfyUIArtifact], *, dest: Path) -> list[Path]:
        """Download artifacts to dest.

        If dest is a directory, writes each artifact under that directory using
        its original filename.
        If dest is a file path and multiple artifacts exist, dest is treated as
        a base stem and artifacts are enumerated.
        """
        if not artifacts:
            return []

        dest = dest.expanduser()
        is_dir = dest.exists() and dest.is_dir()
        if not is_dir and str(dest).endswith(("/", os.sep)):
            is_dir = True

        paths: list[Path] = []
        if is_dir:
            dest.mkdir(parents=True, exist_ok=True)
            for a in artifacts:
                target = dest / Path(a.filename).name
                self.download(filename=a.filename, subfolder=a.subfolder, file_type=a.file_type, dest=target)
                paths.append(target)
            return paths

        if len(artifacts) == 1:
            a = artifacts[0]
            target = dest
            # If caller didn't specify a suffix, preserve the server suffix.
            if target.suffix == "" and a.suffix:
                target = target.with_suffix(a.suffix)
            self.download(filename=a.filename, subfolder=a.subfolder, file_type=a.file_type, dest=target)
            return [target]

        # Multiple artifacts → enumerate with server suffixes.
        base = dest
        base.parent.mkdir(parents=True, exist_ok=True)
        for i, a in enumerate(artifacts):
            suffix = a.suffix or base.suffix
            target = base.with_suffix("").with_name(f"{base.stem}_{i:03d}").with_suffix(suffix)
            self.download(filename=a.filename, subfolder=a.subfolder, file_type=a.file_type, dest=target)
            paths.append(target)
        return paths

    # ------------------------------------------------------------------
    # High-level helper
    # ------------------------------------------------------------------

    def run_workflow(
        self,
        workflow: dict[str, Any],
        *,
        dest: Path,
        output_node: str | None = None,
        timeout_s: int = 600,
        poll_interval_s: float = 5.0,
        wait_for_queue: bool = False,
        queue_timeout_s: int = 60,
        min_vram_free_mb: int | None = None,
        min_ram_free_mb: int | None = None,
        resource_timeout_s: int = 60,
    ) -> dict[str, Any]:
        """Submit → poll → download. Returns metadata + local artifact paths."""
        if not self.is_available():
            raise ComfyUIError(self.unavailable_reason())

        if wait_for_queue:
            self.wait_for_queue(timeout_s=queue_timeout_s)
        self.wait_for_resources(
            min_vram_free_mb=min_vram_free_mb,
            min_ram_free_mb=min_ram_free_mb,
            timeout_s=resource_timeout_s,
        )

        prompt_id = self.submit(workflow)
        entry = self.poll(prompt_id, timeout_s=timeout_s, interval_s=poll_interval_s)
        artifacts = self.extract_artifacts(entry, output_node=output_node)
        if not artifacts:
            available_nodes = sorted((entry.get("outputs") or {}).keys())
            raise ComfyUIError(
                f"No output artifacts found. output_node={output_node!r}. Available output nodes: {available_nodes}"
            )

        local_paths = self.download_artifacts(artifacts, dest=dest)
        return {
            "prompt_id": prompt_id,
            "output_node": output_node,
            "output_nodes": sorted({a.node_id for a in artifacts}),
            "artifacts": [
                {
                    "node_id": a.node_id,
                    "filename": a.filename,
                    "subfolder": a.subfolder,
                    "type": a.file_type,
                    "local_path": str(p),
                }
                for a, p in zip(artifacts, local_paths)
            ],
        }
