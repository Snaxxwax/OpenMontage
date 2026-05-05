import json
import os
import pytest
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from jsonschema import validate
from tools.source.clip_acquisition_adapter import ClipAcquisitionAdapter
from tools.base_tool import ToolResult

# Path to schemas
SCHEMAS_DIR = Path("schemas/artifacts")

def load_schema(name):
    path = SCHEMAS_DIR / f"{name}.schema.json"
    with open(path, "r") as f:
        return json.load(f)

def get_resolver(schema):
    from jsonschema import RefResolver
    base_uri = f"file://{SCHEMAS_DIR.absolute()}/"
    return RefResolver(base_uri=base_uri, referrer=schema)

@pytest.fixture
def sample_receipts():
    return {
        "version": "1.0",
        "project_id": "test-project",
        "receipts": [
            {
                "version": "1.0",
                "project_id": "test-project",
                "receipt_id": "receipt-1",
                "claim_id": "claim-1",
                "source_id": "src-1",
                "source_url": "https://youtube.com/watch?v=123",
                "source_title": "Source 1",
                "source_channel": "Channel 1",
                "clip_role": "primary_evidence",
                "in_seconds": 10.0,
                "out_seconds": 15.0,
                "duration_seconds": 5.0,
                "rationale": "Rationale",
                "why_this_clip_is_needed": "Reason",
                "commentary_attached": True,
                "source_label_required": True,
                "decorative_broll": False,
                "original_audio_use": "ducked",
                "approved_for_edit": True,
                "status": "approved"
            }
        ]
    }

@pytest.fixture
def output_dir(tmp_path):
    d = tmp_path / "output"
    d.mkdir()
    return d

def test_clip_acquisition_adapter_dry_run_schema(sample_receipts, output_dir):
    """Test that dry_run output is schema-valid."""
    adapter = ClipAcquisitionAdapter()
    schema = load_schema("extracted_clip_manifest")
    
    result = adapter.execute({
        "project_id": "test-project",
        "clip_use_receipts": sample_receipts,
        "output_dir": str(output_dir),
        "dry_run": True
    })
    
    assert result.success
    resolver = get_resolver(schema)
    validate(instance=result.data, schema=schema, resolver=resolver)
    assert result.data["clips"] == []

def test_clip_acquisition_adapter_pending_fails(sample_receipts, output_dir):
    """Test that pending receipts cause failure."""
    adapter = ClipAcquisitionAdapter()
    sample_receipts["receipts"][0]["status"] = "pending"
    sample_receipts["receipts"][0]["approved_for_edit"] = False
    
    result = adapter.execute({
        "project_id": "test-project",
        "clip_use_receipts": sample_receipts,
        "output_dir": str(output_dir),
        "dry_run": True
    })
    
    assert not result.success
    assert "Offending receipt_ids" in result.error
    assert "receipt-1" in result.error

def test_clip_acquisition_adapter_unsafe_receipt_id(sample_receipts, output_dir):
    """Test that unsafe receipt_id fails."""
    adapter = ClipAcquisitionAdapter()
    sample_receipts["receipts"][0]["receipt_id"] = "../malicious"
    
    result = adapter.execute({
        "project_id": "test-project",
        "clip_use_receipts": sample_receipts,
        "output_dir": str(output_dir),
        "dry_run": True
    })
    
    assert not result.success
    assert "Unsafe receipt_id" in result.error

def test_clip_acquisition_adapter_unsafe_source_id(sample_receipts, output_dir):
    """Test that unsafe source_id fails."""
    adapter = ClipAcquisitionAdapter()
    sample_receipts["receipts"][0]["source_id"] = "/etc/passwd"
    
    result = adapter.execute({
        "project_id": "test-project",
        "clip_use_receipts": sample_receipts,
        "output_dir": str(output_dir),
        "dry_run": True
    })
    
    assert not result.success
    assert "Unsafe source_id" in result.error

def test_clip_acquisition_adapter_conflicting_urls(sample_receipts, output_dir):
    """Test that conflicting URLs for the same source_id fails."""
    adapter = ClipAcquisitionAdapter()
    sample_receipts["receipts"].append({
        **sample_receipts["receipts"][0],
        "receipt_id": "receipt-2",
        "source_url": "https://youtube.com/watch?v=different"
    })
    
    result = adapter.execute({
        "project_id": "test-project",
        "clip_use_receipts": sample_receipts,
        "output_dir": str(output_dir),
        "dry_run": False
    })
    
    assert not result.success
    assert "Conflicting URLs for source_id" in result.error

@patch("tools.source.clip_acquisition_adapter.VideoDownloader")
@patch("tools.source.clip_acquisition_adapter.VideoTrimmer")
def test_clip_acquisition_adapter_path_safety_mocked(MockTrimmer, MockDownloader, sample_receipts, output_dir):
    """Test that output paths are strictly within output_dir."""
    adapter = ClipAcquisitionAdapter()
    
    mock_dl = MockDownloader.return_value
    # Downloader returns a path OUTSIDE its output_dir (malicious mock)
    mock_dl.execute.return_value = ToolResult(
        success=True,
        data={"video_path": "/etc/shadow"}
    )
    
    result = adapter.execute({
        "project_id": "test-project",
        "clip_use_receipts": sample_receipts,
        "output_dir": str(output_dir),
        "dry_run": False
    })
    
    assert not result.success
    assert "Path safety violation" in result.error

@patch("tools.source.clip_acquisition_adapter.VideoDownloader")
@patch("tools.source.clip_acquisition_adapter.VideoTrimmer")
def test_clip_acquisition_adapter_mocked_execution(MockTrimmer, MockDownloader, sample_receipts, output_dir):
    """Test full execution with mocked downloader and trimmer."""
    adapter = ClipAcquisitionAdapter()
    schema = load_schema("extracted_clip_manifest")
    
    # Mock Downloader
    mock_dl = MockDownloader.return_value
    temp_source = output_dir / ".temp_acquisition" / "src-1" / "video.mp4"
    temp_source.parent.mkdir(parents=True, exist_ok=True)
    temp_source.touch()
    
    mock_dl.execute.return_value = ToolResult(
        success=True,
        data={"video_path": str(temp_source)}
    )
    
    # Mock Trimmer
    mock_trim = MockTrimmer.return_value
    def mock_trim_side_effect(inputs):
        out = Path(inputs["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.touch()
        return ToolResult(success=True, data={})
    
    mock_trim.execute.side_effect = mock_trim_side_effect
    
    result = adapter.execute({
        "project_id": "test-project",
        "clip_use_receipts": sample_receipts,
        "output_dir": str(output_dir),
        "dry_run": False,
        "keep_temp": False
    })
    
    assert result.success
    resolver = get_resolver(schema)
    validate(instance=result.data, schema=schema, resolver=resolver)
    
    assert len(result.data["clips"]) == 1
    clip = result.data["clips"][0]
    assert clip["receipt_id"] == "receipt-1"
    assert "checksum_sha256" in clip
    assert Path(clip["local_clip_path"]).exists()
    assert str(Path(clip["local_clip_path"])).startswith(str(output_dir))
    
    # Check cleanup
    assert not (output_dir / ".temp_acquisition").exists()
