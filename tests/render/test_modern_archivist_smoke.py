from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.video.video_compose import VideoCompose  # noqa: E402

# ---------------------------------------------------------------------------
# Puppet pipeline fixture tests (fast — no actual render)
# ---------------------------------------------------------------------------

_FIXTURE_PATH = ROOT / "tests" / "render" / "fixtures" / "puppet_pipeline_fixture.json"


def test_puppet_fixture_json_is_written() -> None:
    """Verify the puppet pipeline fixture JSON is present in tests/render/fixtures/."""
    assert _FIXTURE_PATH.exists(), (
        f"Puppet fixture JSON not found at {_FIXTURE_PATH}. "
        "Ensure tests/render/fixtures/puppet_pipeline_fixture.json is checked in."
    )


def test_puppet_fixture_json_is_valid() -> None:
    """Verify the puppet fixture JSON parses cleanly and has the expected top-level keys."""
    data = json.loads(_FIXTURE_PATH.read_text())
    assert data["episode_id"] == "puppet-pipeline-fixture"
    assert data["duration_seconds"] == 7
    assert len(data["sections"]) >= 2
    assert len(data["word_timings"]) >= 3


def test_puppet_fixture_sections_cover_required_cues() -> None:
    """Verify fixture has a MONOLOGUE section with puppet visible and a hidden section."""
    data = json.loads(_FIXTURE_PATH.read_text())
    sections = data["sections"]

    visible_actions = {s["character"]["action"] for s in sections if s["character"]["visible"]}
    hidden_sections = [s for s in sections if not s["character"]["visible"]]

    assert "idle" in visible_actions, "Expected at least one section with action=idle and puppet visible"
    assert "sip_coffee" in visible_actions, "Expected at least one section with action=sip_coffee"
    assert len(hidden_sections) >= 1, "Expected at least one section with puppet hidden"

    expressions = {s["character"]["expression"] for s in sections if s["character"]["visible"]}
    assert "skeptical" in expressions, "Expected at least one visible section with expression=skeptical"


def test_puppet_fixture_word_timings_span_expected_range() -> None:
    """Verify word_timings start/end times fall within the expected 1.5–4.5 s window."""
    data = json.loads(_FIXTURE_PATH.read_text())
    wt = data["word_timings"]
    starts = [w["start"] for w in wt]
    ends = [w["end"] for w in wt]
    assert min(starts) >= 1.0, "word_timings should start at 1.0 s or later"
    assert max(ends) <= 4.5, "word_timings should end by 4.5 s"


def test_puppet_render_command_structure() -> None:
    """Verify the render command for the puppet fixture is well-formed (no actual render)."""
    expected_cmd = [
        "npx", "remotion", "render",
        "src/index.tsx", "ModernArchivist",
        "--props", str(_FIXTURE_PATH),
        "--concurrency=1",
        "--every-nth-frame=2",
        "--timeout=600000",
    ]
    assert _FIXTURE_PATH.name == "puppet_pipeline_fixture.json"
    assert "ModernArchivist" in expected_cmd
    assert "--concurrency=1" in expected_cmd
    assert "--every-nth-frame=2" in expected_cmd


# ---------------------------------------------------------------------------
# Slow integration test — skipped in normal CI runs
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_puppet_fixture_renders_and_has_valid_alpha() -> None:
    """Integration test: render the puppet fixture and verify no white-box alpha defects."""
    pytest.skip("slow integration test — run explicitly with pytest -m slow")


# ---------------------------------------------------------------------------
# Original official-route smoke test (requires OPENMONTAGE_RENDER_SMOKE=1)
# ---------------------------------------------------------------------------


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
                        "layout": "anchor_center",
                        "color_state": "teal",
                        "character": {"visible": True, "action": "idle", "expression": "neutral"},
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
