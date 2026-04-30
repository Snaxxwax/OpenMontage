from __future__ import annotations

import json
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass

try:
    import fcntl  # Linux/macOS only
except Exception:  # pragma: no cover
    fcntl = None


_LOCK_PATH = os.path.join(tempfile.gettempdir(), "openmontage_gpu.lock")
_FAIL_STATE_TTL_S = 15 * 60  # 15 minutes


@dataclass(frozen=True)
class GpuLockInfo:
    tool_name: str
    pid: int
    acquired_at: float


_failed_after_isolation: dict[str, float] = {}


def mark_failed_after_isolation(tool_name: str) -> None:
    _failed_after_isolation[tool_name] = time.time()


def is_failed_after_isolation(tool_name: str) -> bool:
    ts = _failed_after_isolation.get(tool_name)
    if ts is None:
        return False
    if (time.time() - ts) > _FAIL_STATE_TTL_S:
        _failed_after_isolation.pop(tool_name, None)
        return False
    return True


def _read_lock_metadata() -> dict[str, object] | None:
    try:
        with open(_LOCK_PATH, "r", encoding="utf-8") as f:
            return json.loads(f.read() or "{}")
    except Exception:
        return None


def current_lock_holder() -> GpuLockInfo | None:
    meta = _read_lock_metadata()
    if not meta:
        return None
    try:
        return GpuLockInfo(
            tool_name=str(meta.get("tool_name") or ""),
            pid=int(meta.get("pid") or 0),
            acquired_at=float(meta.get("acquired_at") or 0.0),
        )
    except Exception:
        return None


@contextmanager
def gpu_lock(*, tool_name: str, timeout_s: float = 0.0):
    """Best-effort cross-process GPU mutex.

    Minimal governance: keep local GPU providers mutually exclusive unless
    the caller explicitly opts out. This does not attempt to kill/unload any
    GPU services; it only serializes OpenMontage-initiated runs.
    """
    if fcntl is None:  # pragma: no cover
        yield {"acquired": True, "holder": None}
        return

    start = time.time()
    fh = open(_LOCK_PATH, "a+", encoding="utf-8")
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                fh.seek(0)
                fh.truncate()
                fh.write(
                    json.dumps(
                        {"tool_name": tool_name, "pid": os.getpid(), "acquired_at": time.time()},
                        ensure_ascii=True,
                    )
                )
                fh.flush()
                os.fsync(fh.fileno())
                break
            except BlockingIOError:
                if timeout_s <= 0 or (time.time() - start) >= timeout_s:
                    break
                time.sleep(0.1)

        yield {"acquired": acquired, "holder": (current_lock_holder() if not acquired else None)}
    finally:
        if acquired:
            try:
                fh.seek(0)
                fh.truncate()
                fh.flush()
            except Exception:
                pass
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
        try:
            fh.close()
        except Exception:
            pass
