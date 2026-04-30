import json
from pathlib import Path
import pytest
from tools.analysis.asymmetric_video_validator import validate_asymmetric_video

def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")

@pytest.fixture
def device_manifest(tmp_path):
    manifest_path = tmp_path / "device_manifest.json"
    device_ids = ["route-trace", "amber-pivot-marker", "blueprint-reveal", "source-card-reveal", "final-leverage-map", "dependency-tree-stop-point", "chokepoint-ring", "collapse-to-one-node", "surface-vs-structure-split", "xray-layer-reveal"]
    devices = [{"device_id": did, "spec_path": ""} for did in device_ids]
    _write_json(manifest_path, {"devices": devices})
    return manifest_path

def test_script_retention_valid(tmp_path, device_manifest):
    script_path = tmp_path / "script.json"
    scene_plan_path = tmp_path / "scene_plan.json"
    
    # 40s target @ 145 WPM = ~96 words. 
    # Current text is ~96 words.
    script = {
        "version": "1.0",
        "title": "TSMC Retention Test",
        "total_duration_seconds": 40,
        "sections": [
            {
                "id": "s1",
                "text": "NVIDIA is worth trillions. Apple sells the phone. OpenAI sells the future. But none of them control the factory that makes the chips. They all depend on one building in Hsinchu. If that building stops, the entire global economy stops with it. This is the ultimate chokepoint.",
                "start_seconds": 0,
                "end_seconds": 20,
                "viewer_question": "Who controls the chips?",
                "tension_type": "mystery",
                "open_loop": "A trillion dollar industry depends on one building.",
                "proof_moment": "TSMC market cap vs others.",
                "consequence": "Single point of failure for global tech.",
                "payoff": "It's TSMC.",
                "next_open_loop": "But building a fab isn't just about money.",
                "visual_event_plan": [
                    {"t": 2, "event": "reveal", "description": "NVIDIA logo"},
                    {"t": 7, "event": "node_lock", "description": "TSMC factory"},
                    {"t": 14, "event": "route_trace", "description": "Hsinchu location"}
                ],
                "source_claim_ids": ["c1"]
            },
            {
                "id": "s2",
                "text": "Intel tried to catch up. Samsung tried to catch up. But building a modern fab costs twenty billion dollars and takes five years of perfect execution. It is not just about the money; it is about the yield. One speck of dust can ruin a twenty billion dollar investment.",
                "start_seconds": 20,
                "end_seconds": 40,
                "viewer_question": "Why is it so expensive?",
                "tension_type": "bottleneck",
                "open_loop": "Physics is the ultimate barrier.",
                "proof_moment": "$20B per fab.",
                "consequence": "No competitors can enter.",
                "payoff": "Extreme precision meets extreme capital.",
                "next_open_loop": "",
                "visual_event_plan": [
                    {"t": 3, "event": "comparison_slam", "description": "$20B wall"},
                    {"t": 8, "event": "collapse", "description": "Competitors falling away"},
                    {"t": 15, "event": "source_proof", "description": "Yield data"}
                ],
                "source_claim_ids": ["c2"]
            }
        ]
    }
    
    scene_plan = {
        "version": "1.0",
        "scenes": [
            {
                "id": "sc1", "type": "diagram", "description": "test", 
                "viewer_hook": "Where is the chokepoint?",
                "tension_type": "mystery",
                "visual_event_cadence_seconds": 6.0,
                "retention_function": "mechanism + proof (trace to the control point)",
                "payoff_moment": "The chokepoint is visibly marked and locked.",
                "next_open_loop": "What happens if it fails?",
                "start_seconds": 0, "end_seconds": 40,
                "devices": [
                    {"device_id": "route-trace"},
                    {"device_id": "amber-pivot-marker"},
                    {"device_id": "blueprint-reveal"},
                    {"device_id": "source-card-reveal"},
                    {"device_id": "final-leverage-map"}
                ],
                "texture_keywords": ["state_change_exempt"]
            }
        ]
    }
    
    _write_json(script_path, script)
    _write_json(scene_plan_path, scene_plan)
    
    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True
    )
    
    assert receipt["passed"], f"Validation failed: {receipt['errors']}"

def test_script_no_retention_valid_for_default_style(tmp_path, device_manifest):
    script_path = tmp_path / "script.json"
    scene_plan_path = tmp_path / "scene_plan.json"
    
    # 10s @ 145 WPM = ~24 words.
    script = {
        "version": "1.0",
        "title": "Default Style Test",
        "total_duration_seconds": 10,
        "sections": [
            {
                "id": "s1",
                "text": "This is a normal script without retention fields. It has enough words to satisfy the default duration alignment check that runs for all scripts.",
                "start_seconds": 0,
                "end_seconds": 10
            }
        ]
    }
    
    _write_json(script_path, script)
    _write_json(scene_plan_path, {"version": "1.0", "scenes": [{"id": "sc1", "type": "t", "description": "d", "start_seconds": 0, "end_seconds": 10, "texture_keywords": ["state_change_exempt"]}]})
    
    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="default",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True
    )
    
    assert receipt["passed"], f"Validation failed: {receipt['errors']}"

def test_script_retention_invalid_hook(tmp_path, device_manifest):
    script_path = tmp_path / "script.json"
    scene_plan_path = tmp_path / "scene_plan.json"
    
    script = {
        "version": "1.0",
        "title": "Bad Hook Test",
        "total_duration_seconds": 10,
        "sections": [
            {
                "id": "s1",
                "text": "Today we're going to look at TSMC.",
                "start_seconds": 0,
                "end_seconds": 10,
                "viewer_question": "q", "tension_type": "mystery", "open_loop": "l",
                "proof_moment": "p", "consequence": "c", "payoff": "pay",
                "next_open_loop": "", 
                "visual_event_plan": [{"t": 5, "event": "reveal", "description": "d"}]
            }
        ]
    }
    
    _write_json(script_path, script)
    _write_json(scene_plan_path, {"version": "1.0", "scenes": [{"id": "sc1", "type": "t", "description": "d", "start_seconds": 0, "end_seconds": 10, "texture_keywords": ["state_change_exempt"]}]})
    
    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True
    )
    
    assert not receipt["passed"]
    assert any("forbidden throat-clearing" in e for e in receipt["errors"])

def test_script_understanding_hook_allowed(tmp_path, device_manifest):
    script_path = tmp_path / "script.json"
    scene_plan_path = tmp_path / "scene_plan.json"
    
    # 10s @ 145 WPM = ~24 words.
    script = {
        "version": "1.0",
        "title": "Understanding Hook Allowed Test",
        "total_duration_seconds": 10,
        "sections": [
            {
                "id": "s1",
                "text": "Understanding physics is the key to this building. It is not just about the money. It is about the extreme precision of the machines.",
                "start_seconds": 0,
                "end_seconds": 10,
                "viewer_question": "q", "tension_type": "mystery", "open_loop": "l",
                "proof_moment": "p", "consequence": "c", "payoff": "pay",
                "next_open_loop": "", 
                "visual_event_plan": [{"t": 5, "event": "reveal", "description": "d"}],
                "source_claim_ids": ["c1"]
            }
        ]
    }

    scene_plan = {
        "version": "1.0",
        "scenes": [
            {
                "id": "sc1",
                "type": "diagram",
                "description": "d",
                "viewer_hook": "What is the mechanism?",
                "tension_type": "mystery",
                "visual_event_cadence_seconds": 6.0,
                "retention_function": "mechanism (keep viewer moving)",
                "payoff_moment": "The mechanism is revealed as a system map.",
                "next_open_loop": "",
                "start_seconds": 0,
                "end_seconds": 10,
                "devices": [
                    {"device_id": "route-trace"},
                    {"device_id": "amber-pivot-marker"},
                    {"device_id": "blueprint-reveal"},
                    {"device_id": "source-card-reveal"},
                    {"device_id": "final-leverage-map"},
                ],
                "texture_keywords": ["state_change_exempt"],
            }
        ],
    }
    
    _write_json(script_path, script)
    _write_json(scene_plan_path, scene_plan)
    
    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True
    )
    
    assert receipt["passed"], f"Validation failed: {receipt['errors']}"

def test_script_retention_missing_fields(tmp_path, device_manifest):
    script_path = tmp_path / "script.json"
    scene_plan_path = tmp_path / "scene_plan.json"
    
    script = {
        "version": "1.0",
        "title": "Missing Fields Test",
        "total_duration_seconds": 10,
        "sections": [
            {
                "id": "s1",
                "text": "NVIDIA is worth trillions.",
                "start_seconds": 0,
                "end_seconds": 10,
                # Missing all retention fields
            }
        ]
    }
    
    _write_json(script_path, script)
    _write_json(scene_plan_path, {"version": "1.0", "scenes": [{"id": "sc1", "type": "t", "description": "d", "start_seconds": 0, "end_seconds": 10, "texture_keywords": ["state_change_exempt"]}]})
    
    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True
    )
    
    assert not receipt["passed"]
    assert any("missing required retention field 'viewer_question'" in e for e in receipt["errors"])

def test_script_retention_visual_cadence(tmp_path, device_manifest):
    script_path = tmp_path / "script.json"
    scene_plan_path = tmp_path / "scene_plan.json"
    
    script = {
        "version": "1.0",
        "title": "Visual Cadence Test",
        "total_duration_seconds": 20,
        "sections": [
            {
                "id": "s1",
                "text": "Long text with no visual events.",
                "start_seconds": 0,
                "end_seconds": 20,
                "viewer_question": "q", "tension_type": "mystery", "open_loop": "l",
                "proof_moment": "p", "consequence": "c", "payoff": "pay",
                "next_open_loop": "", 
                "visual_event_plan": [
                    {"t": 1, "event": "reveal", "description": "d"}
                    # Large gap between t=1 and end=20 (19s)
                ]
            }
        ]
    }
    
    _write_json(script_path, script)
    _write_json(scene_plan_path, {"version": "1.0", "scenes": [{"id": "sc1", "type": "t", "description": "d", "start_seconds": 0, "end_seconds": 20, "texture_keywords": ["state_change_exempt"]}]})
    
    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True
    )
    
    assert not receipt["passed"]
    assert any("visual event gap too large" in e for e in receipt["errors"])

def test_script_invalid_tension_type(tmp_path, device_manifest):
    script_path = tmp_path / "script.json"
    scene_plan_path = tmp_path / "scene_plan.json"
    
    script = {
        "version": "1.0",
        "title": "Invalid Tension Test",
        "total_duration_seconds": 10,
        "sections": [
            {
                "id": "s1",
                "text": "NVIDIA is worth trillions.",
                "start_seconds": 0,
                "end_seconds": 10,
                "viewer_question": "q", 
                "tension_type": "invalid_tension", 
                "open_loop": "l",
                "proof_moment": "p", "consequence": "c", "payoff": "pay",
                "next_open_loop": "", 
                "visual_event_plan": [{"t": 5, "event": "reveal", "description": "d"}]
            }
        ]
    }
    
    _write_json(script_path, script)
    _write_json(scene_plan_path, {"version": "1.0", "scenes": [{"id": "sc1", "type": "t", "description": "d", "start_seconds": 0, "end_seconds": 10, "texture_keywords": ["state_change_exempt"]}]})
    
    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True
    )
    
    assert not receipt["passed"]
    assert any("invalid tension_type 'invalid_tension'" in e for e in receipt["errors"])
