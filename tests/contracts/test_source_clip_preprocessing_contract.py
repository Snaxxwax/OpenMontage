from __future__ import annotations

import json
from pathlib import Path

from scripts.preprocess_source_clips import build_ffmpeg_command, enrich_source_assets, public_render_path


def test_public_render_path_mirrors_project_source_clip_under_remotion_public() -> None:
    root = Path("/repo")
    local_path = "projects/demo/assets/source/video/raw_demo.mp4"

    output = public_render_path(root, local_path)

    assert output == root / "remotion-composer" / "public" / "projects" / "demo" / "assets" / "source" / "video" / "raw_demo_remotion_h264.mp4"


def test_ffmpeg_command_produces_video_only_remotion_safe_h264() -> None:
    command = build_ffmpeg_command(Path("in.mp4"), Path("out.mp4"))

    assert command[:5] == ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    assert "-map" in command and "0:v:0" in command
    assert "-an" in command
    assert ["-c:v", "libx264"] == command[command.index("-c:v"): command.index("-c:v") + 2]
    assert "fps=30" in command[command.index("-vf") + 1]
    assert "format=yuv420p" in command[command.index("-vf") + 1]
    assert command[-1] == "out.mp4"


def test_enrich_source_assets_marks_video_assets_as_remotion_safe(tmp_path: Path) -> None:
    root = tmp_path
    raw = root / "projects/demo/assets/source/video/raw_demo.mp4"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"not real mp4; dry run does not execute ffmpeg")
    source_assets_path = root / "projects/demo/artifacts/source_assets.json"
    source_assets_path.parent.mkdir(parents=True)
    source_assets_path.write_text(json.dumps({
        "project": "demo",
        "assets": [{
            "asset_id": "clip-001",
            "source_url": "https://example.test/video",
            "source_owner": "Example",
            "local_path": "projects/demo/assets/source/video/raw_demo.mp4",
            "asset_type": "video_clip",
            "duration_sec": "4.0",
            "rights_status": "limited_transformative_fair_use",
        }],
    }), encoding="utf-8")

    enriched, jobs = enrich_source_assets(root, source_assets_path, execute=False)

    asset = enriched["assets"][0]
    assert len(jobs) == 1
    assert asset["render_src"] == "projects/demo/assets/source/video/raw_demo_remotion_h264.mp4"
    assert asset["poster_src"] == "projects/demo/assets/source/video/raw_demo_remotion_h264_poster.jpg"
    assert asset["preprocessed"]["remotion_safe"] is True
    assert asset["preprocessed"]["video_codec"] == "h264"
    assert asset["preprocessed"]["audio"] == "stripped_for_narration_mix"


def test_source_sequence_uses_timed_offthread_video_only_for_preprocessed_clips() -> None:
    source = (Path(__file__).resolve().parents[2] / "channels/modern-archivist/remotion/src/components/media/SourceSequence.tsx").read_text(encoding="utf-8")

    assert "OffthreadVideo" in source
    assert "Sequence" in source
    assert "remotion_safe" in source
    assert "from={Math.round(cue.at * fps)}" in source
    assert "durationInFrames={Math.max(1, Math.round((cue.end - cue.at) * fps))}" in source
