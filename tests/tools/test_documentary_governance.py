from __future__ import annotations

from pathlib import Path

from tools.base_tool import ToolStatus
from tools.tool_registry import ToolRegistry
from tools.video.corpus_builder import CorpusBuilder
from tools.video.video_compose import VideoCompose


class _DummySource:
    def __init__(self, name: str, available: bool) -> None:
        self.name = name
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def search(self, query: str, filters):  # pragma: no cover - protocol stub
        return []

    def download(self, candidate, out_path: Path):  # pragma: no cover - protocol stub
        return out_path


def test_corpus_builder_reports_source_level_discoverability(monkeypatch):
    import tools.video.stock_sources as stock_sources

    monkeypatch.setattr(
        stock_sources,
        "all_sources",
        lambda: [_DummySource("pexels", False), _DummySource("archive_org", True)],
    )
    monkeypatch.setattr(
        stock_sources,
        "available_sources",
        lambda: [_DummySource("archive_org", True)],
    )
    monkeypatch.setattr(
        stock_sources,
        "source_catalog",
        lambda: [
            {"name": "pexels", "status": "unavailable"},
            {"name": "archive_org", "status": "available"},
        ],
    )
    monkeypatch.setattr(
        stock_sources,
        "source_summary",
        lambda: {
            "configured": 1,
            "total": 2,
            "available_source_names": ["archive_org"],
            "unavailable_source_names": ["pexels"],
        },
    )

    tool = CorpusBuilder()
    assert tool.get_status() == ToolStatus.DEGRADED

    info = tool.get_info()
    assert info["source_provider_summary"]["configured"] == 1
    assert info["source_provider_summary"]["total"] == 2
    assert {entry["name"] for entry in info["source_provider_menu"]} == {
        "pexels",
        "archive_org",
    }


def test_corpus_builder_rejects_unavailable_pinned_sources(monkeypatch, tmp_path):
    import tools.video.stock_sources as stock_sources

    sources = {
        "pexels": _DummySource("pexels", False),
        "archive_org": _DummySource("archive_org", True),
    }

    monkeypatch.setattr(stock_sources, "all_sources", lambda: list(sources.values()))
    monkeypatch.setattr(
        stock_sources,
        "available_sources",
        lambda: [sources["archive_org"]],
    )
    monkeypatch.setattr(stock_sources, "get_source", lambda name: sources[name])
    monkeypatch.setattr(
        stock_sources,
        "source_summary",
        lambda: {
            "configured": 1,
            "total": 2,
            "available_source_names": ["archive_org"],
            "unavailable_source_names": ["pexels"],
        },
    )

    result = CorpusBuilder().execute({
        "corpus_dir": str(tmp_path / "corpus"),
        "queries": [{"query": "rain at night"}],
        "sources": ["pexels"],
    })

    assert not result.success
    assert "Requested stock sources are unavailable" in result.error
    assert "archive_org" in result.error


def test_documentary_renderer_family_maps_to_remotion():
    assert VideoCompose._get_composition_id("documentary-montage") == "CinematicRenderer"


def test_modern_archivist_renderer_family_maps_to_remotion_composition():
    assert VideoCompose._get_composition_id("modern-archivist") == "ModernArchivist"


def test_modern_archivist_props_materialize_current_audio_as_relative_static_file(tmp_path):
    audio = tmp_path / "assets" / "audio" / "narration.wav"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"RIFF....WAVEfmt ")

    edit_decisions = {
        "renderer_family": "modern-archivist",
        "render_runtime": "remotion",
        "episode_id": "demo",
        "title": "Demo",
        "duration_seconds": 3,
        "audio_src": "modern-archivist/narration.wav",
        "sections": [],
    }

    props = VideoCompose._prepare_remotion_props(
        edit_decisions,
        {
            "narration_audio_path": str(audio),
            "output_path": str(tmp_path / "renders" / "out.mp4"),
        },
    )

    assert props["audio_src"].startswith(".openmontage/demo/narration-")
    assert props["audio_src"].endswith(".wav")
    assert not props["audio_src"].startswith("/")
    assert not props["audio_src"].startswith("file://")
    assert props["audio_source_path"] == str(audio.resolve())
    assert (Path("remotion-composer/public") / props["audio_src"]).exists()


def test_modern_archivist_accepts_project_audio_with_output_outside_project_root(tmp_path):
    project_root = tmp_path / "project"
    audio = project_root / "assets" / "audio" / "narration.wav"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"RIFF....WAVEfmt ")

    edit_decisions = {
        "renderer_family": "modern-archivist",
        "render_runtime": "remotion",
        "episode_id": "outside-output",
        "title": "Demo",
        "duration_seconds": 3,
        "audio_src": "modern-archivist/narration.wav",
        "sections": [],
    }

    props = VideoCompose._prepare_remotion_props(
        edit_decisions,
        {
            "narration_audio_path": str(audio),
            "output_path": str(tmp_path / "shared-renders" / "out.mp4"),
        },
    )

    assert props["audio_src"].startswith(".openmontage/outside-output/narration-")
    assert props["audio_src"].endswith(".wav")
    assert props["audio_source_path"] == str(audio.resolve())


def test_modern_archivist_audio_cache_uses_content_hash_for_same_episode_and_name(tmp_path):
    first_audio = tmp_path / "first" / "assets" / "audio" / "narration.wav"
    second_audio = tmp_path / "second" / "assets" / "audio" / "narration.wav"
    first_audio.parent.mkdir(parents=True)
    second_audio.parent.mkdir(parents=True)
    first_audio.write_bytes(b"RIFF....WAVEfmt first")
    second_audio.write_bytes(b"RIFF....WAVEfmt second")

    edit_decisions = {
        "renderer_family": "modern-archivist",
        "render_runtime": "remotion",
        "episode_id": "same-episode",
        "title": "Demo",
        "duration_seconds": 3,
        "audio_src": "modern-archivist/narration.wav",
        "sections": [],
    }

    first_props = VideoCompose._prepare_remotion_props(
        edit_decisions,
        {"narration_audio_path": str(first_audio), "output_path": str(tmp_path / "out1.mp4")},
    )
    second_props = VideoCompose._prepare_remotion_props(
        edit_decisions,
        {"narration_audio_path": str(second_audio), "output_path": str(tmp_path / "out2.mp4")},
    )

    assert first_props["audio_src"] != second_props["audio_src"]
    first_cache = Path("remotion-composer/public") / first_props["audio_src"]
    second_cache = Path("remotion-composer/public") / second_props["audio_src"]
    assert first_cache.read_bytes() == first_audio.read_bytes()
    assert second_cache.read_bytes() == second_audio.read_bytes()


def test_modern_archivist_audio_materialization_reports_copy_failures(tmp_path, monkeypatch):
    audio = tmp_path / "assets" / "audio" / "narration.wav"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"RIFF....WAVEfmt copyfail")

    def fail_copy(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("tools.video.video_compose.shutil.copy2", fail_copy)

    image = tmp_path / "frame.png"
    image.write_bytes(b"not a real png but enough for pre-render path validation")

    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "modern-archivist",
                "render_runtime": "remotion",
                "episode_id": "copy-failure",
                "title": "Demo",
                "duration_seconds": 3,
                "sections": [],
                "cuts": [
                    {
                        "source": str(image),
                        "in_seconds": 0,
                        "out_seconds": 1,
                        "duration": 1,
                    }
                ],
            },
            "asset_manifest": {"assets": []},
            "narration_audio_path": str(audio),
            "output_path": str(tmp_path / "out.mp4"),
        }
    )

    assert not result.success
    assert "could not materialize" in (result.error or "").lower()


def test_modern_archivist_rejects_stale_public_audio_without_current_audio(tmp_path):
    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "modern-archivist",
                "render_runtime": "remotion",
                "episode_id": "demo",
                "title": "Demo",
                "duration_seconds": 3,
                "audio_src": "modern-archivist/narration.wav",
                "sections": [],
            },
            "asset_manifest": {"assets": []},
            "output_path": str(tmp_path / "out.mp4"),
        }
    )

    assert not result.success
    assert "stale public audio" in (result.error or "").lower()


def test_modern_archivist_remotion_render_rejects_stale_public_audio_without_current_audio(tmp_path):
    result = VideoCompose().execute(
        {
            "operation": "remotion_render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "modern-archivist",
                "render_runtime": "remotion",
                "episode_id": "demo",
                "title": "Demo",
                "duration_seconds": 3,
                "audio_src": "modern-archivist/narration.wav",
                "sections": [],
            },
            "output_path": str(tmp_path / "out.mp4"),
        }
    )

    assert not result.success
    assert "stale public audio" in (result.error or "").lower()


def test_modern_archivist_rejects_missing_current_audio_path(tmp_path):
    missing_audio = tmp_path / "assets" / "audio" / "missing-narration.wav"

    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "modern-archivist",
                "render_runtime": "remotion",
                "episode_id": "demo",
                "title": "Demo",
                "duration_seconds": 3,
                "audio_src": "modern-archivist/narration.wav",
                "sections": [],
            },
            "asset_manifest": {"assets": []},
            "narration_audio_path": str(missing_audio),
            "output_path": str(tmp_path / "out.mp4"),
        }
    )

    assert not result.success
    assert "current project audio" in (result.error or "").lower()
    assert "does not exist" in (result.error or "").lower()


def test_modern_archivist_rejects_current_audio_outside_assets_audio(tmp_path):
    not_project_audio = tmp_path / "narration.wav"
    not_project_audio.write_bytes(b"RIFF....WAVEfmt ")

    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "modern-archivist",
                "render_runtime": "remotion",
                "episode_id": "demo",
                "title": "Demo",
                "duration_seconds": 3,
                "sections": [],
            },
            "asset_manifest": {"assets": []},
            "narration_audio_path": str(not_project_audio),
            "output_path": str(tmp_path / "out.mp4"),
        }
    )

    assert not result.success
    assert "assets/audio" in (result.error or "").lower()


def test_modern_archivist_rejects_non_audio_current_audio(tmp_path):
    not_audio = tmp_path / "assets" / "audio" / "narration.wav"
    not_audio.parent.mkdir(parents=True)
    not_audio.write_text("not audio", encoding="utf-8")

    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "modern-archivist",
                "render_runtime": "remotion",
                "episode_id": "demo",
                "title": "Demo",
                "duration_seconds": 3,
                "sections": [],
            },
            "asset_manifest": {"assets": []},
            "narration_audio_path": str(not_audio),
            "output_path": str(tmp_path / "out.mp4"),
        }
    )

    assert not result.success
    assert "supported audio file" in (result.error or "").lower()


def test_modern_archivist_rejects_absolute_public_audio_fixture_path(tmp_path):
    public_audio = Path("remotion-composer/public/modern-archivist/old-fixture.wav").resolve()

    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "modern-archivist",
                "render_runtime": "remotion",
                "episode_id": "demo",
                "title": "Demo",
                "duration_seconds": 3,
                "audio_src": str(public_audio),
                "sections": [],
            },
            "asset_manifest": {"assets": []},
            "output_path": str(tmp_path / "out.mp4"),
        }
    )

    assert not result.success
    assert "stale public audio" in (result.error or "").lower()


def test_remotion_dev_options_append_bounded_render_flags(tmp_path):
    cmd = VideoCompose._build_remotion_command(
        composer_dir=Path("/repo/remotion-composer"),
        composition_id="ModernArchivist",
        output_path=tmp_path / "out.mp4",
        props_path=tmp_path / "props.json",
        inputs={"options": {"concurrency": 99, "muted": True}},
    )

    assert cmd[:3] == ["npx", "remotion", "render"]
    assert "ModernArchivist" in cmd
    assert "--props" in cmd
    assert "--concurrency" in cmd
    assert cmd[cmd.index("--concurrency") + 1] == "8"
    assert "--muted" in cmd


def test_remotion_dev_options_append_explicit_port(tmp_path):
    cmd = VideoCompose._build_remotion_command(
        composer_dir=Path("/repo/remotion-composer"),
        composition_id="ModernArchivist",
        output_path=tmp_path / "out.mp4",
        props_path=tmp_path / "props.json",
        inputs={"options": {"port": 3767}},
    )

    assert "--port" in cmd
    assert cmd[cmd.index("--port") + 1] == "3767"


def test_remotion_command_ignores_unsafe_extra_args(tmp_path):
    cmd = VideoCompose._build_remotion_command(
        composer_dir=Path("/repo/remotion-composer"),
        composition_id="ModernArchivist",
        output_path=tmp_path / "out.mp4",
        props_path=tmp_path / "props.json",
        inputs={"options": {"remotion_extra_args": ["--config", "evil.ts"]}},
    )

    assert "--config" not in cmd
    assert "evil.ts" not in cmd


def test_video_compose_surfaces_all_three_runtimes():
    """Preflight must see remotion, hyperframes, and ffmpeg as separate engines."""
    info = VideoCompose().get_info()
    engines = info["render_engines"]
    assert set(engines.keys()) == {"remotion", "hyperframes", "ffmpeg"}
    assert engines["ffmpeg"] is True  # always true on this machine
    assert "hyperframes_note" in info
    assert "runtime_governance" in info


def test_video_compose_blocks_silent_hyperframes_swap(tmp_path, monkeypatch):
    """Governance: if render_runtime='hyperframes' is locked but runtime
    is missing, the tool MUST return a structured blocker and NOT route to
    Remotion or FFmpeg."""
    monkeypatch.setattr(
        VideoCompose, "_hyperframes_available", lambda self: False, raising=True
    )
    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "animation-first",
                "render_runtime": "hyperframes",
                "cuts": [
                    {"id": "c1", "source": "x", "in_seconds": 0, "out_seconds": 2}
                ],
            },
            "asset_manifest": {"assets": [{"id": "x", "path": "missing.png"}]},
            "output_path": str(tmp_path / "out.mp4"),
        }
    )
    assert not result.success
    err = (result.error or "").lower()
    assert "hyperframes" in err
    # Error MUST mention it's a blocker, not silently pick a different engine.
    assert ("blocker" in err) or ("not available" in err)


def test_video_compose_rejects_unknown_render_runtime(tmp_path):
    result = VideoCompose().execute(
        {
            "operation": "render",
            "edit_decisions": {
                "version": "1.0",
                "renderer_family": "explainer-data",
                "render_runtime": "bogus-runtime",
                "cuts": [
                    {"id": "c1", "source": "x", "in_seconds": 0, "out_seconds": 2}
                ],
            },
            "asset_manifest": {"assets": []},
            "output_path": str(tmp_path / "out.mp4"),
        }
    )
    assert not result.success
    assert "unknown render_runtime" in (result.error or "").lower()


def test_provider_menu_preserves_tool_discovery_metadata(monkeypatch):
    import tools.video.stock_sources as stock_sources

    monkeypatch.setattr(stock_sources, "all_sources", lambda: [_DummySource("archive_org", True)])
    monkeypatch.setattr(stock_sources, "available_sources", lambda: [_DummySource("archive_org", True)])
    monkeypatch.setattr(
        stock_sources,
        "source_catalog",
        lambda: [{"name": "archive_org", "status": "available"}],
    )
    monkeypatch.setattr(
        stock_sources,
        "source_summary",
        lambda: {
            "configured": 1,
            "total": 1,
            "available_source_names": ["archive_org"],
            "unavailable_source_names": [],
        },
    )

    registry = ToolRegistry()
    registry.register(CorpusBuilder())
    menu = registry.provider_menu()
    entry = menu["corpus_population"]["available"][0]

    assert entry["name"] == "corpus_builder"
    assert entry["source_provider_summary"]["configured"] == 1
    assert entry["source_provider_menu"][0]["name"] == "archive_org"
