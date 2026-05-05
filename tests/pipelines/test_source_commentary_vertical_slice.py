import json
import pytest
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

def test_source_commentary_vertical_slice(tmp_path):
    """End-to-end vertical slice test for source-commentary pipeline artifacts."""
    project_id = "vs-project"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # 1. Inputs
    source_manifest = {
        "version": "1.0",
        "project_id": project_id,
        "sources": [{
            "source_id": "src-1",
            "source_url": "https://youtube.com/watch?v=123",
            "source_title": "Title",
            "source_channel": "Channel",
            "metadata": {}
        }]
    }
    evidence_manifest = {
        "version": "1.0",
        "project_id": project_id,
        "candidates": [{
            "candidate_id": "cand-1",
            "claim_id": "claim-1",
            "source_id": "src-1",
            "in_seconds": 10.0,
            "out_seconds": 15.0,
            "duration_seconds": 5.0,
            "transcript_excerpt": "...",
            "relevance_score": 0.9,
            "rationale": "...",
            "clip_role": "primary_evidence"
        }]
    }
    claim_map = {
        "version": "1.0",
        "project_id": project_id,
        "claims": [{
            "claim_id": "claim-1",
            "narration_text": "The reactor is ready.",
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
    validate(instance=receipts, schema=load_schema("clip_use_receipts"), resolver=get_resolver(load_schema("clip_use_receipts")))

    # 3. Stage: Clip Acquisition (Mocked)
    with patch("tools.source.clip_acquisition_adapter.VideoDownloader") as MockDL, \
         patch("tools.source.clip_acquisition_adapter.VideoTrimmer") as MockTrim:
        
        # Mocking the physical media extraction
        mock_dl = MockDL.return_value
        temp_source_dir = output_dir / ".temp_acquisition" / "src-1"
        temp_source_dir.mkdir(parents=True, exist_ok=True)
        temp_source = temp_source_dir / "mock_source.mp4"
        
        import subprocess
        # Create a tiny valid mp4 instead of touch()
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=640x360:d=5",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(temp_source)
        ], check=True, capture_output=True)
        
        mock_dl.execute.return_value = ToolResult(success=True, data={"video_path": str(temp_source)})
        
        mock_trim = MockTrim.return_value
        def mock_trim_exec(inputs):
            out = Path(inputs["output_path"])
            out.parent.mkdir(parents=True, exist_ok=True)
            # Copy the dummy source as the "trimmed" output
            import shutil
            shutil.copy(temp_source, out)
            return ToolResult(success=True, data={})
        mock_trim.execute.side_effect = mock_trim_exec
        
        acquisition_adapter = ClipAcquisitionAdapter()
        acq_result = acquisition_adapter.execute({
            "project_id": project_id,
            "clip_use_receipts": receipts,
            "output_dir": str(output_dir),
            "dry_run": False
        })
        assert acq_result.success
        extracted_manifest = acq_result.data
        validate(instance=extracted_manifest, schema=load_schema("extracted_clip_manifest"))

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

    # Final logic checks
    timeline = edit_plan["timeline"]
    assert any(item["clip_type"] == "narration" for item in timeline)
    assert any(item["clip_type"] == "source_clip" for item in timeline)
    
    source_clip = next(item for item in timeline if item["clip_type"] == "source_clip")
    assert "receipt_id" in source_clip
    assert source_clip["claim_id"] == "claim-1"
    assert "source_label_plan" in source_clip
    assert source_clip["source_label_plan"]["text"] == "Source: Channel"
