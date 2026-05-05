import pytest
import json
from pathlib import Path
from tools.video.source_commentary_render_adapter import SourceCommentaryRenderAdapter

def test_adapter_valid_plan():
    adapter = SourceCommentaryRenderAdapter()
    
    plan = {
        "version": "1.0",
        "project_id": "test-project",
        "timeline": [
            {
                "clip_type": "source_clip",
                "receipt_id": "rcpt-1",
                "claim_id": "claim-1",
                "local_clip_path": "assets/test.mp4",
                "duration_seconds": 5.0,
                "source_label_plan": {
                    "text": "Source: Test Clip",
                    "position": "bottom-right"
                }
            }
        ]
    }
    
    inputs = {
        "project_id": "test-project",
        "source_commentary_edit_plan": plan
    }
    
    result = adapter.execute(inputs)
    
    assert result.success is True
    data = result.data
    
    assert "edit_decisions" in data
    assert "asset_manifest" in data
    
    ed = data["edit_decisions"]
    am = data["asset_manifest"]
    
    assert ed["render_runtime"] == "remotion"
    assert ed["renderer_family"] == "explainer-data"
    assert len(ed["cuts"]) == 1
    assert ed["cuts"][0]["source"] == "source-commentary/test-project/test.mp4"
    assert ed["cuts"][0]["out_seconds"] == 5.0
    
    # Narration src check
    assert "audio" in ed
    assert "narration" in ed["audio"]
    # We didn't include a narration clip in this basic plan, so segments is empty
    
    assert len(ed["overlays"]) == 1
    assert ed["overlays"][0]["text"] == "Source: Test Clip"
    assert ed["overlays"][0]["position"] == "bottom-left"

    assert len(am["assets"]) == 1
    assert am["assets"][0]["id"] == "source-clip-0"
    assert am["assets"][0]["local_path"].endswith("assets/test.mp4")
    assert am["assets"][0]["staged_public_path"] == "source-commentary/test-project/test.mp4"

def test_adapter_with_file_path(tmp_path):
    adapter = SourceCommentaryRenderAdapter()
    
    plan = {
        "version": "1.0",
        "project_id": "test-project",
        "timeline": []
    }
    
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))
    
    inputs = {
        "project_id": "test-project",
        "source_commentary_edit_plan": str(plan_file)
    }
    
    result = adapter.execute(inputs)
    assert result.success is True
    assert result.data["edit_decisions"]["metadata"]["project_id"] == "test-project"

def test_adapter_cumulative_timing():
    adapter = SourceCommentaryRenderAdapter()
    
    plan = {
        "version": "1.0",
        "project_id": "test-project",
        "timeline": [
            {
                "clip_type": "source_clip",
                "local_clip_path": "clip1.mp4",
                "duration_seconds": 2.0,
                "source_label_plan": {"text": "Label 1", "position": "top-left"}
            },
            {
                "clip_type": "narration",
                "duration_seconds": 3.0
            },
            {
                "clip_type": "source_clip",
                "local_clip_path": "clip2.mp4",
                "duration_seconds": 4.0,
                "source_label_plan": {"text": "Label 2", "position": "top-left"}
            }
        ]
    }
    
    inputs = {
        "project_id": "test-project",
        "source_commentary_edit_plan": plan
    }
    
    result = adapter.execute(inputs)
    ed = result.data["edit_decisions"]
    
    assert len(ed["cuts"]) == 2
    assert ed["cuts"][0]["in_seconds"] == 0.0
    assert ed["cuts"][0]["out_seconds"] == 2.0
    
    # Narration added 3.0s gap
    assert ed["cuts"][1]["in_seconds"] == 5.0
    assert ed["cuts"][1]["out_seconds"] == 9.0
    
    assert len(ed["overlays"]) == 2
    assert ed["overlays"][0]["in_seconds"] == 0.0
    assert ed["overlays"][1]["in_seconds"] == 5.0
