import json
import pytest
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from jsonschema import validate
from tools.base_tool import ToolResult
from tools.source.clip_use_receipt_builder import ClipUseReceiptBuilder
from tools.source.clip_acquisition_adapter import ClipAcquisitionAdapter
from tools.source.media_qc_adapter import MediaQCAdapter
from tools.source.source_commentary_edit_plan_builder import SourceCommentaryEditPlanBuilder
from tools.video.source_commentary_render_adapter import SourceCommentaryRenderAdapter
from tools.video.video_compose import VideoCompose

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

def is_remotion_available():
    """Check if npx is available and remotion-composer/node_modules exists."""
    if not shutil.which("npx"):
        return False
    composer_dir = Path(__file__).resolve().parent.parent.parent / "remotion-composer"
    node_modules = composer_dir / "node_modules"
    return node_modules.exists()

def test_source_commentary_agent_handoff_demo(tmp_path):
    """
    Simulates a multi-agent handoff using the Artifact Bus.
    Agent A (Gemini) starts, Agent B (Claude) finishes.
    """
    project_slug = "agent-handoff-local"
    # Using shared_studio/projects/ as requested
    project_root = tmp_path / "shared_studio" / "projects" / project_slug
    
    # 1. Create artifact bus directories
    bus = {
        "artifacts": project_root / "artifacts",
        "receipts": project_root / "receipts",
        "clips": project_root / "clips",
        "renders": project_root / "renders",
        "qc": project_root / "qc"
    }
    for folder in bus.values():
        folder.mkdir(parents=True, exist_ok=True)

    # --- SIMULATE AGENT A (identity: gemini) ---
    agent_a_identity = "gemini"
    
    narration_claim_map = {
        "version": "1.0",
        "project_id": project_slug,
        "claims": [{
            "claim_id": "claim-handoff",
            "narration_text": "This project was started by Gemini and finished by Claude.",
            "claim_type": "factual",
            "evidence_need": "required",
            "visual_support_type": "direct_proof",
            "priority": 1
        }]
    }
    source_candidate_manifest = {
        "version": "1.0",
        "project_id": project_slug,
        "sources": [{
            "source_id": "src-handoff",
            "source_url": "https://example.com/handoff",
            "source_title": "Handoff Source",
            "source_channel": "Handoff Channel",
            "metadata": {}
        }]
    }
    evidence_candidate_manifest = {
        "version": "1.0",
        "project_id": project_slug,
        "candidates": [{
            "candidate_id": "cand-handoff",
            "claim_id": "claim-handoff",
            "source_id": "src-handoff",
            "in_seconds": 1.0,
            "out_seconds": 4.0,
            "duration_seconds": 3.0,
            "transcript_excerpt": "...",
            "relevance_score": 1.0,
            "rationale": "Handoff proof.",
            "clip_role": "primary_evidence"
        }]
    }
    
    # Agent A writes initial artifacts
    (bus["artifacts"] / "narration_claim_map.json").write_text(json.dumps(narration_claim_map))
    (bus["artifacts"] / "source_candidate_manifest.json").write_text(json.dumps(source_candidate_manifest))
    (bus["artifacts"] / "evidence_candidate_manifest.json").write_text(json.dumps(evidence_candidate_manifest))

    # Agent A runs receipt builder
    receipt_builder = ClipUseReceiptBuilder()
    receipt_res = receipt_builder.execute({
        "project_id": project_slug,
        "source_candidate_manifest": source_candidate_manifest,
        "evidence_candidate_manifest": evidence_candidate_manifest,
        "auto_approve": True
    })
    receipts_artifact = receipt_res.data
    
    # Agent A persists artifacts and receipts
    (bus["artifacts"] / "clip_use_receipts.json").write_text(json.dumps(receipts_artifact))
    for r in receipts_artifact.get("receipts", []):
        (bus["receipts"] / f"{r['receipt_id']}.json").write_text(json.dumps(r))
    
    # Agent A writes checkpoint
    agent_a_checkpoint = {
        "agent": agent_a_identity,
        "stages_completed": ["research", "claim_map", "source_discovery", "transcript_index", "evidence_candidates", "clip_use_gate"],
        "timestamp": "2026-05-04T12:00:00Z"
    }
    (bus["artifacts"] / "agent_a_checkpoint.json").write_text(json.dumps(agent_a_checkpoint))

    # --- CLEAR MEMORY ---
    del narration_claim_map
    del source_candidate_manifest
    del evidence_candidate_manifest
    del receipts_artifact
    del receipt_res

    # --- SIMULATE AGENT B (identity: claude) ---
    agent_b_identity = "claude"
    
    # Agent B reads from the artifact bus
    receipts_path = bus["artifacts"] / "clip_use_receipts.json"
    assert receipts_path.exists()
    
    with open(receipts_path, "r") as f:
        loaded_receipts = json.load(f)
    
    # Validate existing artifact
    validate(instance=loaded_receipts, schema=load_schema("clip_use_receipts"), resolver=get_resolver(load_schema("clip_use_receipts")))
    
    # Agent B Stage: Clip Acquisition
    # Create a real local MP4 fixture
    fixture_source = tmp_path / "handoff_source.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=green:s=640x360:d=5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(fixture_source)
    ], check=True, capture_output=True)

    with patch("tools.source.clip_acquisition_adapter.VideoDownloader") as MockDL:
        mock_dl = MockDL.return_value
        def mock_dl_exec(inputs):
            target_path = Path(inputs["output_dir"]) / "source.mp4"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(fixture_source, target_path)
            return ToolResult(success=True, data={"video_path": str(target_path)})
        mock_dl.execute.side_effect = mock_dl_exec
        
        acquisition_adapter = ClipAcquisitionAdapter()
        acq_res = acquisition_adapter.execute({
            "project_id": project_slug,
            "clip_use_receipts": loaded_receipts,
            "output_dir": str(bus["clips"]),
            "dry_run": False
        })
        assert acq_res.success
        extracted_manifest = acq_res.data
    
    # Persist extracted manifest
    (bus["artifacts"] / "extracted_clip_manifest.json").write_text(json.dumps(extracted_manifest))
    
    # Agent B Stage: Media QC
    qc_adapter = MediaQCAdapter()
    qc_res = qc_adapter.execute({
        "project_id": project_slug,
        "extracted_clip_manifest": extracted_manifest,
        "clip_use_receipts": loaded_receipts
    })
    assert qc_res.success
    approved_manifest = qc_res.data
    (bus["artifacts"] / "approved_clip_manifest.json").write_text(json.dumps(approved_manifest))
    (bus["qc"] / "media_qc_report.json").write_text(json.dumps(approved_manifest))

    # Agent B Stage: Edit Plan
    # Agent B needs the claim map too
    with open(bus["artifacts"] / "narration_claim_map.json", "r") as f:
        loaded_claim_map = json.load(f)
    
    edit_builder = SourceCommentaryEditPlanBuilder()
    edit_res = edit_builder.execute({
        "project_id": project_slug,
        "approved_clip_manifest": approved_manifest,
        "narration_claim_map": loaded_claim_map
    })
    assert edit_res.success
    edit_plan = edit_res.data
    (bus["artifacts"] / "source_commentary_edit_plan.json").write_text(json.dumps(edit_plan))

    # Agent B Stage: Render Adapter
    render_adapter = SourceCommentaryRenderAdapter()
    adapter_res = render_adapter.execute({
        "project_id": project_slug,
        "source_commentary_edit_plan": edit_plan
    })
    assert adapter_res.success
    render_contract = adapter_res.data
    (bus["artifacts"] / "edit_decisions.json").write_text(json.dumps(render_contract["edit_decisions"]))
    (bus["artifacts"] / "asset_manifest.json").write_text(json.dumps(render_contract["asset_manifest"]))

    # Agent B Stage: Composition
    render_attempted = False
    render_output_path = None
    if is_remotion_available():
        render_attempted = True
        composer = VideoCompose()
        output_file = bus["renders"] / "final_handoff.mp4"
        composer_res = composer.execute({
            "operation": "render",
            "edit_decisions": render_contract["edit_decisions"],
            "asset_manifest": render_contract["asset_manifest"],
            "output_path": str(output_file),
            "options": {"subtitle_burn": False}
        })
        assert composer_res.success
        assert output_file.exists()
        render_output_path = str(output_file)

    # Agent B writes checkpoint and handoff log
    agent_b_checkpoint = {
        "agent": agent_b_identity,
        "stages_completed": ["clip_acquisition", "media_qc", "edit_plan", "render_adapter", "compose"],
        "timestamp": "2026-05-04T13:00:00Z"
    }
    (bus["artifacts"] / "agent_b_checkpoint.json").write_text(json.dumps(agent_b_checkpoint))

    handoff_log = {
        "project_slug": project_slug,
        "handoffs": [
            {"agent": agent_a_identity, "stages": agent_a_checkpoint["stages_completed"]},
            {"agent": agent_b_identity, "stages": agent_b_checkpoint["stages_completed"]}
        ],
        "render_attempted": render_attempted,
        "render_output_path": render_output_path,
        "artifact_bus_path": str(project_root)
    }
    (bus["artifacts"] / "agent_handoff_log.json").write_text(json.dumps(handoff_log, indent=2))

    # Assertions
    assert len(list(bus["receipts"].glob("*.json"))) == 1
    assert len(list(bus["clips"].rglob("*.mp4"))) == 1
    if render_attempted:
        assert Path(render_output_path).exists()
    
    # Final check: No artifacts leaked to root (test root is tmp_path)
    root_artifacts = list(tmp_path.glob("*.json"))
    assert len(root_artifacts) == 0, f"Artifacts leaked to root: {root_artifacts}"
