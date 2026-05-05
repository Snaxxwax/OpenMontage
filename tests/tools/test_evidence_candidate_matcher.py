import json
import os
import pytest
import tempfile
from pathlib import Path
from jsonschema import validate
from tools.source.evidence_candidate_matcher import EvidenceCandidateMatcher

# Path to schemas and fixtures
SCHEMAS_DIR = Path("schemas/artifacts")
FIXTURES_DIR = Path("tests/fixtures/source-commentary/basic")

def load_schema(name):
    path = SCHEMAS_DIR / f"{name}.schema.json"
    with open(path, "r") as f:
        return json.load(f)

def test_evidence_candidate_matcher_basic_matching():
    """Test basic keyword matching logic."""
    matcher = EvidenceCandidateMatcher()
    
    claim_map = {
        "version": "1.0",
        "project_id": "test",
        "claims": [
            {
                "claim_id": "claim-1",
                "narration_text": "The reactor is eighty percent complete.",
                "claim_type": "factual",
                "evidence_need": "required",
                "visual_support_type": "direct_proof",
                "priority": 1
            }
        ]
    }
    
    transcript_index = {
        "version": "1.0",
        "project_id": "test",
        "source_segments": [
            {
                "source_id": "src-1",
                "segment_id": "seg-1",
                "start_seconds": 10.0,
                "end_seconds": 20.0,
                "text": "We have reached eighty percent completion of the reactor assembly."
            }
        ]
    }
    
    result = matcher.execute({
        "project_id": "test",
        "narration_claim_map": claim_map,
        "transcript_index": transcript_index
    })
    
    assert result.success
    assert len(result.data["candidates"]) == 1
    candidate = result.data["candidates"][0]
    assert candidate["claim_id"] == "claim-1"
    assert candidate["source_id"] == "src-1"
    assert candidate["clip_role"] == "primary_evidence"
    assert candidate["relevance_score"] > 0.5

def test_evidence_candidate_matcher_schema_validation():
    """Test that the output validates against the schema."""
    matcher = EvidenceCandidateMatcher()
    schema = load_schema("evidence_candidate_manifest")
    
    # Use existing fixtures
    with open(FIXTURES_DIR / "narration_claim_map.json", "r") as f:
        claim_map = json.load(f)
    with open(FIXTURES_DIR / "transcript_index.json", "r") as f:
        transcript_index = json.load(f)
        
    result = matcher.execute({
        "project_id": "project-x",
        "narration_claim_map": claim_map,
        "transcript_index": transcript_index
    })
    
    assert result.success
    validate(instance=result.data, schema=schema)

def test_evidence_candidate_matcher_clip_role_mapping():
    """Test various clip_role mappings."""
    matcher = EvidenceCandidateMatcher()
    
    def get_role(v_type, c_type):
        claim = {"visual_support_type": v_type, "claim_type": c_type}
        return matcher._map_clip_role(claim)
    
    assert get_role("direct_proof", "factual") == "primary_evidence"
    assert get_role("expert_quote", "factual") == "quote_support"
    assert get_role("document_scan", "factual") == "supporting_context"
    assert get_role("contextual_montage", "contradictory") == "counter_argument"
    assert get_role("contextual_montage", "historical") == "timeline_proof"
    assert get_role("contextual_montage", "reactionary") == "public_reaction"

def test_evidence_candidate_matcher_required_claim_fails_if_no_match():
    """Test that missing required claim causes failure."""
    matcher = EvidenceCandidateMatcher()
    
    claim_map = {
        "version": "1.0",
        "project_id": "test",
        "claims": [
            {
                "claim_id": "claim-required",
                "narration_text": "Non-existent keywords here",
                "claim_type": "factual",
                "evidence_need": "required",
                "visual_support_type": "direct_proof",
                "priority": 1
            }
        ]
    }
    
    transcript_index = {
        "version": "1.0",
        "project_id": "test",
        "source_segments": [
            {
                "source_id": "src-1",
                "segment_id": "seg-1",
                "start_seconds": 0,
                "end_seconds": 10,
                "text": "Something completely different."
            }
        ]
    }
    
    result = matcher.execute({
        "project_id": "test",
        "narration_claim_map": claim_map,
        "transcript_index": transcript_index,
        "min_relevance_score": 0.5
    })
    
    assert not result.success
    assert "claim-required" in result.error

def test_evidence_candidate_matcher_optional_claim_warns_on_success():
    """Test that optional claim with no match warns but returns success."""
    matcher = EvidenceCandidateMatcher()
    
    claim_map = {
        "version": "1.0",
        "project_id": "test",
        "claims": [
            {
                "claim_id": "claim-optional",
                "narration_text": "Non-existent keywords here",
                "claim_type": "factual",
                "evidence_need": "optional",
                "visual_support_type": "direct_proof",
                "priority": 1
            }
        ]
    }
    
    transcript_index = {
        "version": "1.0",
        "project_id": "test",
        "source_segments": []
    }
    
    result = matcher.execute({
        "project_id": "test",
        "narration_claim_map": claim_map,
        "transcript_index": transcript_index,
        "min_relevance_score": 0.5
    })
    
    assert result.success
    assert "Warnings:" in result.error
    assert "claim-optional" in result.error

def test_evidence_candidate_matcher_recommended_claim_warns_on_success():
    """Test that recommended claim with no match warns but returns success."""
    matcher = EvidenceCandidateMatcher()
    
    claim_map = {
        "version": "1.0",
        "project_id": "test",
        "claims": [
            {
                "claim_id": "claim-recommended",
                "narration_text": "Non-existent keywords here",
                "claim_type": "factual",
                "evidence_need": "recommended",
                "visual_support_type": "direct_proof",
                "priority": 1
            }
        ]
    }
    
    transcript_index = {
        "version": "1.0",
        "project_id": "test",
        "source_segments": []
    }
    
    result = matcher.execute({
        "project_id": "test",
        "narration_claim_map": claim_map,
        "transcript_index": transcript_index,
        "min_relevance_score": 0.5
    })
    
    assert result.success
    assert "Warnings:" in result.error
    assert "claim-recommended" in result.error

def test_evidence_candidate_matcher_no_media_created_recursive():
    """Test that the matcher does not create any media files recursively."""
    matcher = EvidenceCandidateMatcher()
    
    with open(FIXTURES_DIR / "narration_claim_map.json", "r") as f:
        claim_map = json.load(f)
    with open(FIXTURES_DIR / "transcript_index.json", "r") as f:
        transcript_index = json.load(f)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            matcher.execute({
                "project_id": "test-project",
                "narration_claim_map": claim_map,
                "transcript_index": transcript_index
            })
            
            media_extensions = {".mp4", ".mkv", ".webm", ".wav", ".mp3", ".srt", ".vtt"}
            for root, dirs, files in os.walk("."):
                for file in files:
                    assert Path(file).suffix not in media_extensions, f"Found media file: {file}"
        finally:
            os.chdir(old_cwd)
