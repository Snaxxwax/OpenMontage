from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.video.video_compose import VideoCompose  # noqa: E402

# Official-route smoke test (requires OPENMONTAGE_RENDER_SMOKE=1).


@pytest.mark.skipif(
    os.environ.get("OPENMONTAGE_RENDER_SMOKE") != "1",
    reason="Set OPENMONTAGE_RENDER_SMOKE=1 to run Remotion smoke renders",
)
def test_modern_archivist_official_video_compose_smoke(tmp_path):
    output_path = tmp_path / "modern-archivist-smoke.mp4"

    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "modern-archivist",
                "render_runtime": "remotion",
                "episode_id": "modern-archivist-smoke",
                "title": "Modern Archivist Smoke",
                "duration_seconds": 1.25,
                "sections": [
                    {
                        "id": "s1",
                        "start": 0,
                        "end": 1.25,
                        "text": "Official route smoke render.",
                        "narration": "Official route smoke render.",
                        "tags": [],
                        "visual_mode": "case_file",
                        "layout": "media_full",
                        "color_state": "teal",
                    }
                ],
                "cuts": [
                    {
                        "id": "s1",
                        "type": "text_card",
                        "source": "",
                        "in_seconds": 0,
                        "out_seconds": 1.25,
                        "reason": "Minimal official-route smoke render fixture.",
                    }
                ],
            },
            "asset_manifest": {"assets": []},
            "scene_plan": [
                {
                    "type": "case_file",
                    "description": "Minimal official-route Modern Archivist smoke render.",
                    "shot_language": {"shot_size": "medium", "camera_movement": "push_in"},
                    "shot_intent": "Verify official video_compose routing reaches the ModernArchivist Remotion composition.",
                    "narrative_role": "technical_validation",
                    "information_role": "render_smoke",
                }
            ],
            "output_path": str(output_path),
            "options": {"muted": True, "concurrency": 2},
            "proposal_packet": {"production_plan": {"render_runtime": "remotion"}},
        }
    )

    assert result.success, result.error
    assert output_path.exists()
    assert result.data["operation"] == "remotion_render"

    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert float(probe.stdout.strip()) >= 1.0
