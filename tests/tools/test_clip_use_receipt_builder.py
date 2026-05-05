import json
import pytest
import uuid
from pathlib import Path
from jsonschema import validate
from tools.source.clip_use_receipt_builder import ClipUseReceiptBuilder

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
def sample_inputs():
    project_id = "test-project"
    source_manifest = {
        "version": "1.0",
        "project_id": project_id,
        "sources": [
            {
                "source_id": "src-1",
                "source_url": "https://youtube.com/watch?v=123",
                "source_title": "Source 1",
                "source_channel": "Channel 1",
                "metadata": {}
            }
        ]
    }
    evidence_manifest = {
        "version": "1.0",
        "project_id": project_id,
        "candidates": [
            {
                "candidate_id": "cand-1",
                "claim_id": "claim-1",
                "source_id": "src-1",
                "in_seconds": 10.0,
                "out_seconds": 15.0,
                "duration_seconds": 5.0,
                "transcript_excerpt": "Hello world",
                "relevance_score": 0.9,
                "rationale": "Strong match",
                "clip_role": "primary_evidence"
            }
        ]
    }
    return {
        "project_id": project_id,
        "source_candidate_manifest": source_manifest,
        "evidence_candidate_manifest": evidence_manifest
    }

def test_clip_use_receipt_builder_pending_validation(sample_inputs):
    """Test that pending receipts validate against schema."""
    builder = ClipUseReceiptBuilder()
    schema = load_schema("clip_use_receipts")
    
    result = builder.execute({
        **sample_inputs,
        "auto_approve": False
    })
    
    assert result.success
    resolver = get_resolver(schema)
    validate(instance=result.data, schema=schema, resolver=resolver)
    receipt = result.data["receipts"][0]
    assert receipt["status"] == "pending"
    assert receipt["approved_for_edit"] is False

def test_clip_use_receipt_builder_auto_approved_validation(sample_inputs):
    """Test that auto-approved receipts validate against schema."""
    builder = ClipUseReceiptBuilder()
    schema = load_schema("clip_use_receipts")
    
    result = builder.execute({
        **sample_inputs,
        "auto_approve": True
    })
    
    assert result.success
    resolver = get_resolver(schema)
    validate(instance=result.data, schema=schema, resolver=resolver)
    receipt = result.data["receipts"][0]
    assert receipt["status"] == "approved"
    assert receipt["approved_for_edit"] is True
    assert receipt["decorative_broll"] is False

def test_clip_use_receipt_builder_missing_source_fails(sample_inputs):
    """Test that missing source_id in source manifest causes failure."""
    builder = ClipUseReceiptBuilder()
    sample_inputs["source_candidate_manifest"]["sources"] = []
    
    result = builder.execute(sample_inputs)
    
    assert not result.success
    assert "references missing source" in result.error

def test_clip_use_receipt_builder_over_duration_flagged(sample_inputs):
    """Test that candidates exceeding max_duration are flagged."""
    builder = ClipUseReceiptBuilder()
    sample_inputs["evidence_candidate_manifest"]["candidates"][0]["duration_seconds"] = 20.0
    
    result = builder.execute({
        **sample_inputs,
        "max_duration_seconds": 10.0,
        "auto_approve": True
    })
    
    assert result.success
    assert "Warnings:" in result.error
    receipt = result.data["receipts"][0]
    assert receipt["status"] == "flagged"
    assert receipt["approved_for_edit"] is False

def test_clip_use_receipt_builder_metadata_preservation(sample_inputs):
    """Test that source metadata is correctly preserved in receipt."""
    builder = ClipUseReceiptBuilder()
    
    result = builder.execute(sample_inputs)
    
    assert result.success
    receipt = result.data["receipts"][0]
    source = sample_inputs["source_candidate_manifest"]["sources"][0]
    assert receipt["source_url"] == source["source_url"]
    assert receipt["source_title"] == source["source_title"]
    assert receipt["source_channel"] == source["source_channel"]

def test_clip_use_receipt_builder_audio_mapping(sample_inputs):
    """Test audio_use mapping logic."""
    builder = ClipUseReceiptBuilder()
    
    # primary_evidence -> ducked
    result = builder.execute(sample_inputs)
    assert result.data["receipts"][0]["original_audio_use"] == "ducked"
    
    # quote_support -> quote_audio
    sample_inputs["evidence_candidate_manifest"]["candidates"][0]["clip_role"] = "quote_support"
    result = builder.execute(sample_inputs)
    assert result.data["receipts"][0]["original_audio_use"] == "quote_audio"
    
    # other -> muted
    sample_inputs["evidence_candidate_manifest"]["candidates"][0]["clip_role"] = "supporting_context"
    result = builder.execute(sample_inputs)
    assert result.data["receipts"][0]["original_audio_use"] == "muted"

def test_clip_use_receipt_builder_determinism(sample_inputs):
    """Test that receipt IDs are deterministic."""
    builder = ClipUseReceiptBuilder()
    
    result1 = builder.execute(sample_inputs)
    result2 = builder.execute(sample_inputs)
    
    assert result1.data["receipts"][0]["receipt_id"] == result2.data["receipts"][0]["receipt_id"]

def test_clip_use_receipt_builder_no_media_created(sample_inputs, tmp_path):
    """Test that no media files are created during execution."""
    import os
    builder = ClipUseReceiptBuilder()
    
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        builder.execute(sample_inputs)
        
        media_extensions = {".mp4", ".mkv", ".webm", ".wav", ".mp3", ".srt", ".vtt"}
        for root, dirs, files in os.walk("."):
            for file in files:
                assert Path(file).suffix not in media_extensions, f"Found media file: {file}"
    finally:
        os.chdir(old_cwd)
