"""Regression tests for VideoDownloader._find_downloaded.

Tests the private file-finder helper through the smallest stable surface.
Covers all common video container extensions including the ogv regression
discovered during the Phase 7 acquisition dry run (archive.org returned .ogv
but the old finder only searched mp4/mkv/webm).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tools.analysis.video_downloader import VideoDownloader


@pytest.fixture()
def downloader():
    return VideoDownloader()


@pytest.fixture()
def tmp(tmp_path):
    return tmp_path


def _touch(directory: Path, filename: str) -> Path:
    p = directory / filename
    p.write_bytes(b"dummy")
    return p


class TestFindDownloaded:
    def test_detects_mp4(self, downloader, tmp):
        _touch(tmp, "reference_video.mp4")
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is not None
        assert result.endswith(".mp4")

    def test_detects_webm(self, downloader, tmp):
        _touch(tmp, "reference_video.webm")
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is not None
        assert result.endswith(".webm")

    def test_detects_ogv(self, downloader, tmp):
        _touch(tmp, "reference_video.ogv")
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is not None
        assert result.endswith(".ogv")

    def test_returns_none_when_no_supported_file(self, downloader, tmp):
        _touch(tmp, "reference_video.flv")
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is None

    def test_returns_none_when_directory_empty(self, downloader, tmp):
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is None

    def test_detects_avi(self, downloader, tmp):
        _touch(tmp, "reference_video.avi")
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is not None
        assert result.endswith(".avi")

    def test_detects_mov(self, downloader, tmp):
        _touch(tmp, "reference_video.mov")
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is not None
        assert result.endswith(".mov")

    def test_detects_m4v(self, downloader, tmp):
        _touch(tmp, "reference_video.m4v")
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is not None
        assert result.endswith(".m4v")

    def test_prefix_isolation(self, downloader, tmp):
        # A file with a different prefix should not be returned
        _touch(tmp, "other_video.ogv")
        result = downloader._find_downloaded(tmp, "reference_video", ["mp4", "mkv", "webm", "ogv", "avi", "mov", "m4v"])
        assert result is None


class TestDownloadVideoUsesExtendedExtensions:
    """Verify that _download_video passes the extended extension list to _find_downloaded."""

    def test_ogv_found_after_download(self, downloader, tmp, monkeypatch):
        """Simulate a download that produces an .ogv file — finder must return it."""
        # Stub out yt_dlp so no real network call happens
        import types

        fake_ydl = types.SimpleNamespace(
            download=lambda urls: None,
            __enter__=lambda s: s,
            __exit__=lambda s, *a: False,
        )

        monkeypatch.setattr(
            "tools.analysis.video_downloader.VideoDownloader._download_video",
            lambda self, url, output_dir, max_res: (
                _touch(output_dir, "reference_video.ogv") and None
                or (str(output_dir / "reference_video.ogv"), None)
            ),
        )

        result = downloader._download_video.__func__(
            downloader, "http://fake", tmp, "720p"
        )
        # The monkeypatched version plants the file and returns it
        video_path, audio_path = result
        assert video_path is not None
        assert video_path.endswith(".ogv")
