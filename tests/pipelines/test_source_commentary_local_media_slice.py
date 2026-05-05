import json
import os
import subprocess
import pytest
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch
from jsonschema import validate
from tools.source.clip_use_receipt_builder import ClipUseReceiptBuilder
from tools.source.clip_acquisition_adapter import ClipAcquisitionAdapter
from tools.source.media_qc_adapter import MediaQCAdapter
from tools.source.source_commentary_edit_plan_builder import SourceCommentaryEditPlanBuilder
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

@pytest.fixture(scope="module")
def local_mp4_fixture(tmp_path_factory):
    """Create a 5-second dummy MP4 for testing."""
    tmp_dir = tmp_path_factory.mktemp("media")
    output_path = tmp_dir / "test_source.mp4"
    
    # Generate 5s black video with 1khz tone
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=640x360:r=24:d=5",
        "-f", "lavfi", "-i", "sine=f=1000:d=5",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path

def test_source_commentary_local_media_slice(local_mp4_fixture, tmp_path):
    """End-to-end vertical slice test using real local media extraction."""
    project_id = "local-media-slice"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # 1. Inputs
    source_manifest = {
        "version": "1.0",
        "project_id": project_id,
        "sources": [{
            "source_id": "src-local",
            "source_url": "file://" + str(local_mp4_fixture),
            "source_title": "Local Fixture",
            "source_channel": "TestChannel",
            "metadata": {}
        }]
    }
    evidence_manifest = {
        "version": "1.0",
        "project_id": project_id,
        "candidates": [{
            "candidate_id": "cand-local",
            "claim_id": "claim-local",
            "source_id": "src-local",
            "in_seconds": 1.0,
            "out_seconds": 3.0,
            "duration_seconds": 2.0,
            "transcript_excerpt": "...",
            "relevance_score": 1.0,
            "rationale": "Direct evidence from local file.",
            "clip_role": "primary_evidence"
        }]
    }
    claim_map = {
        "version": "1.0",
        "project_id": project_id,
        "claims": [{
            "claim_id": "claim-local",
            "narration_text": "The local media works.",
            "claim_type": "factual",
            "evidence_need": "required",
            "visual_support_type": "direct_proof",
            "priority": 1
        }]
    }

    # 2. Stage: Clip Use Receipts
    receipt_builder = ClipUseReceiptBuilder()
    receipt_result = receipt_builder.execute({
        "project_id": project_id,
        "source_candidate_manifest": source_manifest,
        "evidence_candidate_manifest": evidence_manifest,
        "auto_approve": True
    })
    assert receipt_result.success
    receipts = receipt_result.data

    # 3. Stage: Clip Acquisition (Physical Extraction)
    # Mock only the VideoDownloader, use real VideoTrimmer
    with patch("tools.source.clip_acquisition_adapter.VideoDownloader") as MockDL:
        mock_dl = MockDL.return_value
        
        # We need to simulate the source temp dir structure that the adapter expects
        # The adapter creates output_dir / .temp_acquisition / sid
        # We'll mock the downloader to "return" the local_mp4_fixture path, 
        # but the adapter checks if that path is INSIDE the temp dir.
        # So we actually need to copy the fixture into the temp dir for the safety check to pass.
        
        def mock_dl_exec(inputs):
            sid = Path(inputs["output_dir"]).name
            target_path = Path(inputs["output_dir"]) / "source.mp4"
            shutil.copy(local_mp4_fixture, target_path)
            return ToolResult(success=True, data={"video_path": str(target_path)})
        
        import shutil
        mock_dl.execute.side_effect = mock_dl_exec
        
        acquisition_adapter = ClipAcquisitionAdapter()
        acq_result = acquisition_adapter.execute({
            "project_id": project_id,
            "clip_use_receipts": receipts,
            "output_dir": str(output_dir),
            "dry_run": False,
            "keep_temp": False
        })
        
        assert acq_result.success, acq_result.error
        extracted_manifest = acq_result.data
        validate(instance=extracted_manifest, schema=load_schema("extracted_clip_manifest"))

        # Verify physical file existence and size
        clip_entry = extracted_manifest["clips"][0]
        clip_path = Path(clip_entry["local_clip_path"])
        assert clip_path.exists()
        assert clip_path.stat().st_size > 0
        assert "checksum_sha256" in clip_entry
        assert len(clip_entry["checksum_sha256"]) == 64

    # 4. Stage: Media QC
    qc_adapter = MediaQCAdapter()
    qc_result = qc_adapter.execute({
        "project_id": project_id,
        "extracted_clip_manifest": extracted_manifest,
        "clip_use_receipts": receipts
    })
    assert qc_result.success
    approved_manifest = qc_result.data
    validate(instance=approved_manifest, schema=load_schema("approved_clip_manifest"))
    assert approved_manifest["approved_clips"][0]["source_label_text"] == "Source: TestChannel"

    # 5. Stage: Edit Planning
    edit_builder = SourceCommentaryEditPlanBuilder()
    edit_result = edit_builder.execute({
        "project_id": project_id,
        "approved_clip_manifest": approved_manifest,
        "narration_claim_map": claim_map
    })
    assert edit_result.success
    edit_plan = edit_result.data
    validate(instance=edit_plan, schema=load_schema("source_commentary_edit_plan"))

    # Final timeline checks
    timeline = edit_plan["timeline"]
    source_clip = next(item for item in timeline if item["clip_type"] == "source_clip")
    assert source_clip["source_label_plan"]["text"] == "Source: TestChannel"
    assert Path(source_clip["local_clip_path"]).exists()
