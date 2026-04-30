from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.analysis.asymmetric_video_validator import validate_asymmetric_video


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def _device_manifest_fixture(tmp_path: Path) -> Path:
    devices_dir = tmp_path / "devices"
    devices_dir.mkdir(parents=True, exist_ok=True)

    device_ids = [
        "amber-pivot-marker",
        "chokepoint-ring",
        "route-trace",
        "collapse-to-one-node",
        "surface-vs-structure-split",
        "xray-layer-reveal",
        "blueprint-reveal",
        "under-the-hood-mechanism",
        "red-consequence-layer",
        "source-card-reveal",
        "final-leverage-map",
        "dependency-tree-stop-point",
    ]

    devices = []
    for did in device_ids:
        spec_path = devices_dir / did / "device.v1.spec.json"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            spec_path,
            {
                "device_id": did,
                "version": "1.0",
                "input_parameters": [],
            },
        )
        devices.append(
            {
                "device_id": did,
                "spec_path": str(spec_path),
                "template_path": str(devices_dir / did / "README.md"),
                "semantic_category": "test",
                "required_colors": [],
                "default_duration_range_seconds": [2.0, 4.0],
                "episode_importance": "optional",
            }
        )

    manifest_path = tmp_path / "device_manifest.json"
    _write_json(
        manifest_path,
        {
            "schema_version": 1,
            "package": {"name": "test-devices", "version": "0.0.0"},
            "devices": devices,
        },
    )
    return manifest_path


def _minimal_valid_scene_plan() -> dict:
    return {
        "version": "1.0",
        "style_playbook": "asymmetric",
        "scenes": [
            {
                "id": "s1",
                "type": "diagram",
                "description": "System map with route trace and dependency stop point.",
                "viewer_hook": "Where does the chain actually stop?",
                "tension_type": "bottleneck",
                "visual_event_cadence_seconds": 6.0,
                "retention_function": "mechanism + proof (route trace to the stop point)",
                "payoff_moment": "The stop-point node locks and the route trace terminates.",
                "next_open_loop": "So who controls that stop point?",
                "start_seconds": 0.0,
                "end_seconds": 8.0,
                "devices": [{"device_id": "route-trace"}, {"device_id": "dependency-tree-stop-point"}],
                "state_changes": [
                    {"t": 0.0, "beat": "start", "description": "map in", "visual_state_change": True},
                    {"t": 3.0, "beat": "trace", "device_id": "route-trace", "description": "trace", "visual_state_change": True},
                    {"t": 6.0, "beat": "stop", "device_id": "dependency-tree-stop-point", "description": "stop", "visual_state_change": True},
                ],
            },
            {
                "id": "s2",
                "type": "diagram",
                "description": "Chokepoint reveal with amber marker.",
                "viewer_hook": "What is the leverage point?",
                "tension_type": "mystery",
                "visual_event_cadence_seconds": 6.0,
                "retention_function": "reveal the chokepoint (visual consequence: everything routes through one control surface)",
                "payoff_moment": "The amber pivot marker lands and locks on the chokepoint.",
                "next_open_loop": "If that pivot fails, what breaks first?",
                "start_seconds": 8.0,
                "end_seconds": 14.0,
                "devices": [{"device_id": "amber-pivot-marker"}],
                "state_changes": [
                    {"t": 0.0, "beat": "start", "description": "in", "visual_state_change": True},
                    {"t": 2.5, "beat": "pivot", "device_id": "amber-pivot-marker", "description": "pivot", "visual_state_change": True},
                    {"t": 5.0, "beat": "lock", "description": "lock", "visual_state_change": True},
                ],
            },
            {
                "id": "s3",
                "type": "diagram",
                "description": "Surface vs structure split (xray).",
                "viewer_hook": "What is the public story vs the real mechanism?",
                "tension_type": "contradiction",
                "visual_event_cadence_seconds": 6.0,
                "retention_function": "contradiction reveal (surface claim vs structural reality)",
                "payoff_moment": "The split exposes the hidden structure layer under the surface.",
                "next_open_loop": "Can we prove this with a source on-screen?",
                "start_seconds": 14.0,
                "end_seconds": 20.0,
                "devices": [{"device_id": "surface-vs-structure-split"}],
                "state_changes": [
                    {"t": 0.0, "beat": "start", "description": "in", "visual_state_change": True},
                    {"t": 3.0, "beat": "split", "device_id": "surface-vs-structure-split", "description": "split", "visual_state_change": True},
                    {"t": 5.5, "beat": "hold", "description": "hold", "visual_state_change": True},
                ],
            },
            {
                "id": "s4",
                "type": "text_card",
                "description": "Source card reveal for major non-obvious claim.",
                "viewer_hook": "Is this claim actually documented?",
                "tension_type": "payoff",
                "visual_event_cadence_seconds": 6.0,
                "retention_function": "source proof (evidence card as consequence of the contradiction)",
                "payoff_moment": "The source-card-reveal lands with the citation visible.",
                "next_open_loop": "What does this imply for the final leverage map?",
                "start_seconds": 20.0,
                "end_seconds": 26.0,
                "devices": [{"device_id": "source-card-reveal"}],
                "state_changes": [
                    {"t": 0.0, "beat": "start", "description": "in", "visual_state_change": True},
                    {"t": 2.5, "beat": "reveal", "device_id": "source-card-reveal", "description": "reveal", "visual_state_change": True},
                    {"t": 5.0, "beat": "cite", "description": "cite", "visual_state_change": True},
                ],
            },
            {
                "id": "s5",
                "type": "diagram",
                "description": "Final leverage map.",
                "viewer_hook": "So what’s the actual leverage map?",
                "tension_type": "payoff",
                "visual_event_cadence_seconds": 6.0,
                "retention_function": "final synthesis (map the control surfaces and consequences)",
                "payoff_moment": "The final leverage map resolves the system into one view with the pivot marked.",
                "next_open_loop": "",
                "start_seconds": 26.0,
                "end_seconds": 32.0,
                "devices": [{"device_id": "final-leverage-map"}],
                "state_changes": [
                    {"t": 0.0, "beat": "start", "description": "in", "visual_state_change": True},
                    {"t": 3.0, "beat": "map", "device_id": "final-leverage-map", "description": "map", "visual_state_change": True},
                    {"t": 5.5, "beat": "exit", "description": "exit", "visual_state_change": True},
                ],
            },
        ],
    }


def test_validator_passes_minimal_valid_scene_plan(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, _minimal_valid_scene_plan())

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is True
    assert receipt["errors"] == []


def test_validator_fails_when_scene_plan_duration_conflicts_with_target(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, _minimal_valid_scene_plan())

    proposal_packet_path = tmp_path / "proposal_packet.json"
    _write_json(
        proposal_packet_path,
        {
            "version": "1.0",
            "concept_options": [{"id": "c1", "target_duration_seconds": 780}],
            "selected_concept": {"concept_id": "c1", "target_duration_seconds": 780},
            "production_plan": {},
            "cost_estimate": {"total_estimated_usd": 0.0},
            "approval": {"status": "approved"},
        },
    )

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=None,
        proposal_packet_path=proposal_packet_path,
        project_config_path=None,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("scene_plan duration" in e for e in receipt["errors"])


def test_validator_fails_when_script_word_count_too_short_for_target(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)

    # Scene plan claims to be longform but is exempted from per-scene state-change enforcement for this unit test.
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(
        scene_plan_path,
        {
            "version": "1.0",
            "style_playbook": "asymmetric",
            "scenes": [
                {
                    "id": "s1",
                    "type": "diagram",
                    "description": "Longform placeholder scene (test-only).",
                    "viewer_hook": "What is the mechanism, end-to-end?",
                    "tension_type": "mystery",
                    "visual_event_cadence_seconds": 6.0,
                    "retention_function": "placeholder (test-only) — keep viewer moving through the map",
                    "payoff_moment": "placeholder payoff (test-only)",
                    "next_open_loop": "",
                    "start_seconds": 0.0,
                    "end_seconds": 780.0,
                    "texture_keywords": ["state_change_exempt"],
                    "devices": [
                        {"device_id": "route-trace"},
                        {"device_id": "dependency-tree-stop-point"},
                        {"device_id": "amber-pivot-marker"},
                        {"device_id": "surface-vs-structure-split"},
                        {"device_id": "source-card-reveal"},
                        {"device_id": "final-leverage-map"},
                    ],
                }
            ],
        },
    )

    proposal_packet_path = tmp_path / "proposal_packet.json"
    _write_json(
        proposal_packet_path,
        {
            "version": "1.0",
            "concept_options": [{"id": "c1", "target_duration_seconds": 780}],
            "selected_concept": {"concept_id": "c1", "target_duration_seconds": 780},
            "production_plan": {},
            "cost_estimate": {"total_estimated_usd": 0.0},
            "approval": {"status": "approved"},
        },
    )

    # Script is only 545 words for a 780s target (should fail).
    script_path = tmp_path / "script.json"
    short_text = ("word " * 545).strip()
    _write_json(
        script_path,
        {
            "version": "1.0",
            "title": "t",
            "total_duration_seconds": 780,
            "sections": [{"id": "s01", "text": short_text, "start_seconds": 0, "end_seconds": 780}],
        },
    )

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        script_path=script_path,
        proposal_packet_path=proposal_packet_path,
        project_config_path=None,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("Script word count" in e for e in receipt["errors"])


def test_validator_fails_state_change_gap_over_4s(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    sp = _minimal_valid_scene_plan()
    sp["scenes"][0]["state_changes"] = [
        {"t": 0.0, "beat": "start", "description": "in", "visual_state_change": True},
        {"t": 6.0, "beat": "late", "description": "late", "visual_state_change": True},
    ]
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, sp)

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("holds" in e for e in receipt["errors"])


def test_validator_fails_unknown_device_id(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    sp = _minimal_valid_scene_plan()
    sp["scenes"][0]["devices"].append({"device_id": "unknown-device"})
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, sp)

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("unknown" in e.lower() for e in receipt["errors"])


def test_validator_fails_missing_required_device_coverage(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    sp = _minimal_valid_scene_plan()
    # Remove final leverage map coverage.
    sp["scenes"] = [s for s in sp["scenes"] if s["id"] != "s5"]
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, sp)

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("Missing required Asymmetric device coverage" in e for e in receipt["errors"])


def test_validator_fails_stat_scene_missing_source_claim_id(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    sp = _minimal_valid_scene_plan()
    sp["scenes"][3]["description"] = "Stat card: 60% of X (hard claim)."
    sp["scenes"][3].pop("source_claim_ids", None)
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, sp)

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("missing source_claim_ids" in e for e in receipt["errors"])


def test_validator_fails_analyst_sourced_hard_stat_without_qualifier(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    sp = _minimal_valid_scene_plan()
    sp["scenes"][3]["description"] = "Stat card: 60% of X (hard claim)."
    sp["scenes"][3]["source_claim_ids"] = ["c1"]

    source_map_path = tmp_path / "source_map.json"
    _write_json(
        source_map_path,
        {"claims": [{"id": "c1", "source_type": "analyst", "confidence": "high", "hard_stat_card_permitted": True}]},
    )

    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, sp)

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=source_map_path,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("requires qualifier_required" in e for e in receipt["errors"])


def test_validator_passes_generated_image_with_svg_css_fallback(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    sp = _minimal_valid_scene_plan()
    sp["scenes"][0]["required_assets"] = [
        {
            "type": "image",
            "description": "Generated image of system map (if needed).",
            "source": "generate",
            "fallback_type": "svg_css",
            "fallback_path": "planned:channel_assets/asymmetric/objects/svg/system_map.svg",
            "fallback_required": True,
        }
    ]

    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, sp)

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt["passed"] is True


def test_validator_warns_or_fails_generated_image_without_fallback(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    sp = _minimal_valid_scene_plan()
    sp["scenes"][0]["required_assets"] = [
        {
            "type": "image",
            "description": "Generated image of system map (no fallback).",
            "source": "generate",
            "fallback_type": "generated_image",
        }
    ]
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, sp)

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=False,
    )
    assert receipt["passed"] is True
    assert receipt["warnings"]

    receipt_strict = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=None,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="scene_plan",
        strict=True,
    )
    assert receipt_strict["passed"] is False


def test_validator_detects_suspected_fish_speech_truncation_from_asset_manifest(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, _minimal_valid_scene_plan())

    # Build a minimal project root + missing file to avoid failing on missing file.
    project_root = tmp_path / "projects" / "p1"
    (project_root / "assets" / "audio").mkdir(parents=True, exist_ok=True)
    (project_root / "artifacts").mkdir(parents=True, exist_ok=True)
    (project_root / "assets" / "audio" / "narration.wav").write_bytes(b"RIFF")  # existence only

    asset_manifest_path = project_root / "artifacts" / "asset_manifest.json"
    _write_json(
        asset_manifest_path,
        {
            "version": "1.0",
            "assets": [
                {
                    "id": "n1",
                    "type": "narration",
                    "path": "assets/audio/narration.wav",
                    "source_tool": "fish_speech_tts",
                    "scene_id": "s1",
                    "duration_seconds": 47.5,
                }
            ],
            "provider_blocks": [
                {
                    "block_id": "b1",
                    "provider": "fish_speech",
                    "tool_name": "fish_speech_tts",
                    "runtime": "local_gpu",
                    "status": "success",
                    "lock_acquired": True,
                    "artifacts_produced": ["n1"],
                }
            ],
            "tts_chunk_receipts": [
                {
                    "section_id": "s1",
                    "provider": "fish_speech",
                    "final_output_path": "assets/audio/narration.wav",
                    "final_duration_seconds": 120.0,
                    "chunk_count": 2,
                    "chunks": [
                        {
                            "chunk_id": "c01",
                            "output_path": "assets/audio/narration_c01.wav",
                            "word_count": 200,
                            "estimated_seconds": 70.0,
                            "duration_seconds": 47.8,
                            "wall_time_seconds": 30.0,
                            "realtime_factor": 0.63,
                            "suspected_truncation": True,
                        },
                        {
                            "chunk_id": "c02",
                            "output_path": "assets/audio/narration_c02.wav",
                            "word_count": 120,
                            "estimated_seconds": 45.0,
                            "duration_seconds": 46.0,
                            "wall_time_seconds": 26.0,
                            "realtime_factor": 0.57,
                            "suspected_truncation": False,
                        },
                    ],
                }
            ],
        },
    )

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=asset_manifest_path,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="assets",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("Suspected Fish Speech truncation" in e for e in receipt["errors"])


def test_validator_asset_manifest_provider_blocks_and_tts_receipts_pass_when_clean(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, _minimal_valid_scene_plan())

    project_root = tmp_path / "projects" / "p2"
    (project_root / "assets" / "audio").mkdir(parents=True, exist_ok=True)
    (project_root / "artifacts").mkdir(parents=True, exist_ok=True)
    (project_root / "assets" / "audio" / "narration.wav").write_bytes(b"RIFF")

    asset_manifest_path = project_root / "artifacts" / "asset_manifest.json"
    _write_json(
        asset_manifest_path,
        {
            "version": "1.0",
            "provider_blocks": [
                {
                    "block_id": "b1",
                    "provider": "fish_speech",
                    "tool_name": "tts_selector",
                    "runtime": "local_gpu",
                    "status": "success",
                    "lock_acquired": True,
                    "artifacts_produced": ["n1"],
                }
            ],
            "tts_chunk_receipts": [
                {
                    "section_id": "s1",
                    "provider": "fish_speech",
                    "final_output_path": "assets/audio/narration.wav",
                    "final_duration_seconds": 32.0,
                    "chunk_count": 2,
                    "chunks": [
                        {
                            "chunk_id": "c01",
                            "output_path": "assets/audio/narration_c01.wav",
                            "word_count": 180,
                            "estimated_seconds": 64.0,
                            "duration_seconds": 16.0,
                            "wall_time_seconds": 18.0,
                            "realtime_factor": 0.55,
                            "suspected_truncation": False,
                        },
                        {
                            "chunk_id": "c02",
                            "output_path": "assets/audio/narration_c02.wav",
                            "word_count": 140,
                            "estimated_seconds": 50.0,
                            "duration_seconds": 16.0,
                            "wall_time_seconds": 19.0,
                            "realtime_factor": 0.56,
                            "suspected_truncation": False,
                        },
                    ],
                }
            ],
            "assets": [
                {
                    "id": "n1",
                    "type": "narration",
                    "path": "assets/audio/narration.wav",
                    "source_tool": "tts_selector",
                    "scene_id": "s1",
                    "duration_seconds": 32.0,
                }
            ],
        },
    )

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=asset_manifest_path,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="assets",
        strict=True,
    )
    assert receipt["passed"] is True


def test_validator_asset_manifest_generated_image_failure_with_svg_css_fallback_passes(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, _minimal_valid_scene_plan())

    project_root = tmp_path / "projects" / "p3"
    (project_root / "assets" / "images").mkdir(parents=True, exist_ok=True)
    (project_root / "artifacts").mkdir(parents=True, exist_ok=True)
    (project_root / "assets" / "images" / "fallback.svg").write_text("<svg/>", encoding="utf-8")

    asset_manifest_path = project_root / "artifacts" / "asset_manifest.json"
    _write_json(
        asset_manifest_path,
        {
            "version": "1.0",
            "provider_blocks": [
                {
                    "block_id": "b1",
                    "provider": "comfyui",
                    "tool_name": "comfyui_image",
                    "runtime": "local_gpu",
                    "status": "compatibility_failure",
                    "lock_acquired": True,
                    "artifacts_produced": [],
                    "failure_reason": "allocator failure",
                }
            ],
            "assets": [
                {
                    "id": "img1",
                    "type": "image",
                    "path": "assets/images/img1.png",
                    "source_tool": "comfyui_image",
                    "scene_id": "s1",
                    "generation_status": "failed",
                    "fallback_type": "svg_css",
                    "fallback_path": str(project_root / "assets" / "images" / "fallback.svg"),
                }
            ],
        },
    )

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=asset_manifest_path,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="assets",
        strict=True,
    )
    assert receipt["passed"] is True


def test_validator_asset_manifest_generated_image_failure_no_fallback_fails_strict(tmp_path: Path) -> None:
    device_manifest = _device_manifest_fixture(tmp_path)
    scene_plan_path = tmp_path / "scene_plan.json"
    _write_json(scene_plan_path, _minimal_valid_scene_plan())

    project_root = tmp_path / "projects" / "p4"
    (project_root / "artifacts").mkdir(parents=True, exist_ok=True)

    asset_manifest_path = project_root / "artifacts" / "asset_manifest.json"
    _write_json(
        asset_manifest_path,
        {
            "version": "1.0",
            "provider_blocks": [
                {
                    "block_id": "b1",
                    "provider": "comfyui",
                    "tool_name": "comfyui_image",
                    "runtime": "local_gpu",
                    "status": "failed",
                    "lock_acquired": True,
                    "artifacts_produced": [],
                }
            ],
            "assets": [
                {
                    "id": "img1",
                    "type": "image",
                    "path": "assets/images/img1.png",
                    "source_tool": "comfyui_image",
                    "scene_id": "s1",
                    "generation_status": "failed",
                    "fallback_type": "generated_image",
                }
            ],
        },
    )

    receipt = validate_asymmetric_video(
        scene_plan_path=scene_plan_path,
        source_map_path=None,
        asset_manifest_path=asset_manifest_path,
        style_playbook="asymmetric",
        device_manifest_path=device_manifest,
        stage="assets",
        strict=True,
    )
    assert receipt["passed"] is False
    assert any("missing svg_css/hyperframes_native fallback_type" in e for e in receipt["errors"])
