import json
import os
import pytest
import tempfile
from pathlib import Path
from jsonschema import validate
from tools.source.transcript_index_builder import TranscriptIndexBuilder

# Path to schemas and fixtures
SCHEMAS_DIR = Path("schemas/artifacts")
FIXTURES_DIR = Path("tests/fixtures/source-commentary/basic")

def load_schema(name):
    path = SCHEMAS_DIR / f"{name}.schema.json"
    with open(path, "r") as f:
        return json.load(f)

def test_transcript_index_builder_fixture_mode():
    """Test that the builder works in fixture mode without network."""
    builder = TranscriptIndexBuilder()
    fixture_path = FIXTURES_DIR / "transcript_index.json"
    
    inputs = {
        "project_id": "overridden-project",
        "transcript_fixture_path": str(fixture_path)
    }
    
    result = builder.execute(inputs)
    
    assert result.success
    assert result.data["project_id"] == "overridden-project"
    assert len(result.data["source_segments"]) > 0
    
    for segment in result.data["source_segments"]:
        assert "source_id" in segment
        assert "segment_id" in segment
        assert isinstance(segment["start_seconds"], (int, float))
        assert isinstance(segment["end_seconds"], (int, float))
        assert "text" in segment

def test_transcript_index_builder_schema_validation():
    """Test that the output validates against the transcript_index schema."""
    builder = TranscriptIndexBuilder()
    fixture_path = FIXTURES_DIR / "transcript_index.json"
    schema = load_schema("transcript_index")
    
    inputs = {
        "project_id": "test-project",
        "transcript_fixture_path": str(fixture_path)
    }
    
    result = builder.execute(inputs)
    assert result.success
    
    # Validate against schema
    validate(instance=result.data, schema=schema)

def test_transcript_index_builder_preserves_source_id():
    """Test that source_id is preserved from manifest."""
    manifest = {
        "version": "1.0",
        "project_id": "test-project",
        "sources": [
            {
                "source_id": "src-1",
                "source_url": "https://youtube.com/watch?v=123",
                "source_title": "Test",
                "source_channel": "Test Channel",
                "platform": "youtube",
                "transcript_available": True,
                "metadata_only_collected": True
            }
        ]
    }
    
    builder = TranscriptIndexBuilder()
    
    # We'll use a mock for _fetch_youtube_transcript since we don't want network
    def mock_fetch(source_id, url, max_segments):
        return [{
            "source_id": source_id,
            "segment_id": f"{source_id}-seg-0",
            "start_seconds": 0.0,
            "end_seconds": 10.0,
            "text": "Hello world"
        }], None
    
    builder._fetch_youtube_transcript = mock_fetch
    
    result = builder.execute({
        "project_id": "test-project",
        "source_candidate_manifest": manifest
    })
    
    assert result.success
    assert result.data["source_segments"][0]["source_id"] == "src-1"

def test_transcript_index_builder_no_media_created_recursive():
    """Test that the builder does not create any media files recursively."""
    builder = TranscriptIndexBuilder()
    fixture_path = FIXTURES_DIR / "transcript_index.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            builder.execute({
                "project_id": "test-project",
                "transcript_fixture_path": str(Path(old_cwd) / fixture_path)
            })
            
            media_extensions = {".mp4", ".mkv", ".webm", ".wav", ".mp3", ".srt", ".vtt"}
            for root, dirs, files in os.walk("."):
                for file in files:
                    assert Path(file).suffix not in media_extensions, f"Found media file: {file}"
        finally:
            os.chdir(old_cwd)

def test_transcript_index_builder_unavailable_transcript_warning():
    """Test that unavailable transcripts create warnings."""
    manifest = {
        "version": "1.0",
        "project_id": "test-project",
        "sources": [
            {
                "source_id": "src-fail",
                "source_url": "https://youtube.com/watch?v=fail",
                "platform": "youtube",
                "transcript_available": False,
                "metadata_only_collected": True
            }
        ]
    }
    
    builder = TranscriptIndexBuilder()
    
    def mock_fetch_fail(source_id, url, max_segments):
        return [], "Transcript disabled"
    
    builder._fetch_youtube_transcript = mock_fetch_fail
    
    result = builder.execute({
        "project_id": "test-project",
        "source_candidate_manifest": manifest
    })
    
    assert not result.success
    assert "Indexing failed" in result.error
    assert "warnings" in result.data
