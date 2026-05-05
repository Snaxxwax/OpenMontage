"""Tests for SourceCommentaryAssetStager tool."""

import json
import os
import shutil
import pytest
from pathlib import Path
from tools.video.source_commentary_asset_stager import SourceCommentaryAssetStager


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with source assets and staging area."""
    # Artifact bus
    source_dir = tmp_path / "artifacts"
    source_dir.mkdir()
    
    # Staging area
    public_root = tmp_path / "remotion-composer" / "public"
    public_root.mkdir(parents=True)
    
    # Create minimal binary fixtures (MP4-like and WAV-like)
    video_path = source_dir / "clip1.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom")
    
    audio_path = source_dir / "narration.wav"
    audio_path.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00")
    
    return {
        "source_dir": source_dir,
        "public_root": public_root,
        "video_path": video_path,
        "audio_path": audio_path
    }


def test_source_commentary_asset_stager_success(temp_workspace):
    stager = SourceCommentaryAssetStager()
    
    project_id = "test-project"
    asset_manifest = {
        "assets": [
            {
                "id": "video-1",
                "type": "video",
                "local_path": str(temp_workspace["video_path"]),
                "staged_public_path": "source-commentary/test-project/clip1.mp4"
            },
            {
                "id": "audio-1",
                "type": "audio",
                "local_path": str(temp_workspace["audio_path"]),
                "staged_public_path": "source-commentary/test-project/narration.wav"
            }
        ]
    }
    
    inputs = {
        "project_id": project_id,
        "asset_manifest": asset_manifest,
        "remotion_public_root": str(temp_workspace["public_root"])
    }
    
    result = stager.execute(inputs)
    
    assert result.success is True
    assert len(result.data["staged_assets"]) == 2
    
    # Verify physical files
    staged_video = temp_workspace["public_root"] / "source-commentary/test-project/clip1.mp4"
    staged_audio = temp_workspace["public_root"] / "source-commentary/test-project/narration.wav"
    
    assert staged_video.exists()
    assert staged_audio.exists()
    assert staged_video.read_bytes().startswith(b"\x00\x00\x00\x18ftyp")
    
    # Verify deterministic receipt
    assert "timestamp" not in result.data
    asset1 = result.data["staged_assets"][0]
    assert asset1["source_checksum_sha256"] == asset1["staged_checksum_sha256"]


def test_source_commentary_asset_stager_empty_fails(temp_workspace):
    stager = SourceCommentaryAssetStager()
    inputs = {
        "project_id": "test",
        "asset_manifest": {"assets": []},
        "remotion_public_root": str(temp_workspace["public_root"])
    }
    result = stager.execute(inputs)
    assert result.success is False
    assert "no assets to stage" in result.error


def test_source_commentary_asset_stager_path_traversal_fails(temp_workspace):
    stager = SourceCommentaryAssetStager()
    bad_manifest = {
        "assets": [{
            "id": "bad",
            "type": "video",
            "local_path": str(temp_workspace["video_path"]),
            "staged_public_path": "../../etc/passwd"
        }]
    }
    inputs = {
        "project_id": "test",
        "asset_manifest": bad_manifest,
        "remotion_public_root": str(temp_workspace["public_root"])
    }
    result = stager.execute(inputs)
    assert result.success is False
    assert "Path traversal detected" in result.error or "escapes public root" in result.error


def test_source_commentary_asset_stager_absolute_dest_fails(temp_workspace):
    stager = SourceCommentaryAssetStager()
    bad_manifest = {
        "assets": [{
            "id": "bad",
            "type": "video",
            "local_path": str(temp_workspace["video_path"]),
            "staged_public_path": "/tmp/evil.mp4"
        }]
    }
    inputs = {
        "project_id": "test",
        "asset_manifest": bad_manifest,
        "remotion_public_root": str(temp_workspace["public_root"])
    }
    result = stager.execute(inputs)
    assert result.success is False
    assert "must be relative" in result.error


def test_source_commentary_asset_stager_escape_root_fails(temp_workspace, tmp_path):
    stager = SourceCommentaryAssetStager()
    # Attempt to point to a sibling of public root
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    
    bad_manifest = {
        "assets": [{
            "id": "bad",
            "type": "video",
            "local_path": str(temp_workspace["video_path"]),
            "staged_public_path": "../other/stolen.mp4"
        }]
    }
    inputs = {
        "project_id": "test",
        "asset_manifest": bad_manifest,
        "remotion_public_root": str(temp_workspace["public_root"])
    }
    result = stager.execute(inputs)
    assert result.success is False
    assert "escapes public root" in result.error or "Path traversal" in result.error


def test_source_commentary_asset_stager_deterministic_receipt(temp_workspace):
    stager = SourceCommentaryAssetStager()
    asset_manifest = {
        "assets": [{
            "id": "v1",
            "type": "video",
            "local_path": str(temp_workspace["video_path"]),
            "staged_public_path": "v1.mp4"
        }]
    }
    inputs = {
        "project_id": "test",
        "asset_manifest": asset_manifest,
        "remotion_public_root": str(temp_workspace["public_root"])
    }
    
    res1 = stager.execute(inputs)
    res2 = stager.execute(inputs)
    
    assert res1.data == res2.data
