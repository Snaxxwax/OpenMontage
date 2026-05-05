import pytest
import subprocess
import json
from pathlib import Path
from tools.source.media_qc_adapter import MediaQCAdapter

@pytest.fixture
def valid_mp4(tmp_path):
    path = tmp_path / "valid.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=640x360:d=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)
    ], check=True, capture_output=True)
    return path

@pytest.fixture
def zero_byte_file(tmp_path):
    path = tmp_path / "empty.mp4"
    path.write_bytes(b"")
    return path

def test_media_qc_adapter_success(valid_mp4):
    adapter = MediaQCAdapter()
    
    extracted = {
        "clips": [
            {
                "receipt_id": "rcpt-1",
                "local_clip_path": str(valid_mp4),
                "duration_seconds": 1.0
            }
        ]
    }
    
    receipts = {
        "receipts": [
            {
                "receipt_id": "rcpt-1",
                "claim_id": "claim-1",
                "source_channel": "Test Channel",
                "duration_seconds": 1.0
            }
        ]
    }
    
    result = adapter.execute({
        "project_id": "test",
        "extracted_clip_manifest": extracted,
        "clip_use_receipts": receipts
    })
    
    assert result.success is True
    assert len(result.data["approved_clips"]) == 1
    assert len(result.data["rejected_clips"]) == 0
    assert result.data["approved_clips"][0]["source_label_text"] == "Source: Test Channel"

def test_media_qc_adapter_missing_file():
    adapter = MediaQCAdapter()
    
    extracted = {
        "clips": [{"receipt_id": "rcpt-1", "local_clip_path": "missing.mp4"}]
    }
    receipts = {
        "receipts": [{"receipt_id": "rcpt-1", "claim_id": "c1"}]
    }
    
    result = adapter.execute({
        "project_id": "test",
        "extracted_clip_manifest": extracted,
        "clip_use_receipts": receipts
    })
    
    assert len(result.data["approved_clips"]) == 0
    assert len(result.data["rejected_clips"]) == 1
    assert "File not found" in result.data["rejected_clips"][0]["reason"]

def test_media_qc_adapter_zero_byte(zero_byte_file):
    adapter = MediaQCAdapter()
    
    extracted = {
        "clips": [{"receipt_id": "rcpt-1", "local_clip_path": str(zero_byte_file)}]
    }
    receipts = {
        "receipts": [{"receipt_id": "rcpt-1", "claim_id": "c1"}]
    }
    
    result = adapter.execute({
        "project_id": "test",
        "extracted_clip_manifest": extracted,
        "clip_use_receipts": receipts
    })
    
    assert len(result.data["approved_clips"]) == 0
    assert "Zero-byte file" in result.data["rejected_clips"][0]["reason"]

def test_media_qc_adapter_no_receipt(valid_mp4):
    adapter = MediaQCAdapter()
    
    extracted = {
        "clips": [{"receipt_id": "rcpt-unknown", "local_clip_path": str(valid_mp4)}]
    }
    receipts = {"receipts": []}
    
    result = adapter.execute({
        "project_id": "test",
        "extracted_clip_manifest": extracted,
        "clip_use_receipts": receipts
    })
    
    assert len(result.data["approved_clips"]) == 0
    assert "No matching receipt" in result.data["rejected_clips"][0]["reason"]

def test_media_qc_adapter_duration_mismatch(valid_mp4):
    adapter = MediaQCAdapter()
    
    # Fixture is 1.0s, we claim it should be 5.0s
    extracted = {
        "clips": [
            {
                "receipt_id": "rcpt-1",
                "local_clip_path": str(valid_mp4),
                "duration_seconds": 5.0
            }
        ]
    }
    receipts = {
        "receipts": [{"receipt_id": "rcpt-1", "claim_id": "c1", "duration_seconds": 5.0}]
    }
    
    result = adapter.execute({
        "project_id": "test",
        "extracted_clip_manifest": extracted,
        "clip_use_receipts": receipts
    })
    
    assert len(result.data["approved_clips"]) == 0
    assert "Duration mismatch" in result.data["rejected_clips"][0]["reason"]

def test_media_qc_adapter_source_label_from_url(valid_mp4):
    adapter = MediaQCAdapter()
    
    extracted = {
        "clips": [{"receipt_id": "rcpt-1", "local_clip_path": str(valid_mp4)}]
    }
    receipts = {
        "receipts": [
            {
                "receipt_id": "rcpt-1",
                "claim_id": "c1",
                "source_url": "https://www.youtube.com/watch?v=123"
            }
        ]
    }
    
    result = adapter.execute({
        "project_id": "test",
        "extracted_clip_manifest": extracted,
        "clip_use_receipts": receipts
    })
    
    assert result.data["approved_clips"][0]["source_label_text"] == "Source: www.youtube.com"
