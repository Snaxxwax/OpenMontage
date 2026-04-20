"""Phase 0 contract tests — infrastructure layer.

Tests config, schemas, checkpoints, pipeline manifests, tools, cost tracker,
and media profiles. The intelligence layer (orchestrator, reviewer, checkpoint
policy, handlers) has been replaced by instruction-driven architecture:
pipeline manifests + stage director skills + meta skills.
"""

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.config_model import OpenMontageConfig
from lib.checkpoint import (
    CheckpointValidationError,
    STAGES,
    get_next_stage,
    read_checkpoint,
    write_checkpoint,
)
from lib.media_profiles import get_profile, ffmpeg_output_args, ALL_PROFILES
from lib.pipeline_loader import (
    get_required_tools,
    get_stage_order,
    get_stage_skill,
    get_stage_sub_stages,
    get_stage_review_focus,
    list_pipelines,
    load_pipeline,
    pipeline_supports_reference_input,
)
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolStatus
from tools.tool_registry import ToolRegistry
from tools.cost_tracker import CostTracker, BudgetMode, BudgetExceededError, ApprovalRequiredError
from schemas.artifacts import load_schema, validate_artifact, list_schemas


def sample_artifact(name: str) -> dict:
    """Return a minimal schema-valid artifact for tests."""
    if name == "research_brief":
        return {
            "version": "1.0",
            "topic": "Test Topic",
            "research_date": "2026-03-27",
            "landscape": {
                "existing_content": [
                    {"title": "Existing Video 1", "source": "youtube", "angle": "tutorial", "what_it_covers": "basics"},
                    {"title": "Existing Video 2", "source": "blog", "angle": "deep dive", "what_it_covers": "advanced"},
                    {"title": "Existing Video 3", "source": "youtube", "angle": "comparison", "what_it_covers": "alternatives"},
                ],
                "saturated_angles": ["basic tutorial"],
                "underserved_gaps": ["misconceptions about topic"],
            },
            "data_points": [
                {"claim": "73% of users prefer X", "source_url": "https://example.com/study", "credibility": "primary_source"},
                {"claim": "Market grew 40% in 2025", "source_url": "https://example.com/report", "credibility": "secondary_source"},
                {"claim": "Most experts agree on Y", "source_url": "https://example.com/survey", "credibility": "primary_source"},
            ],
            "audience_insights": {
                "common_questions": ["What is X?", "How does X work?", "Why is X important?"],
                "misconceptions": [{"myth": "X is slow", "reality": "X is fast"}],
                "knowledge_level": "Beginner to intermediate",
            },
            "angles_discovered": [
                {"name": "The Surprising Truth", "hook": "You think X is slow. It's not.", "type": "contrarian", "why_now": "New benchmark data", "grounded_in": ["data_point_1"]},
                {"name": "X From Scratch", "hook": "Build X in 5 minutes.", "type": "evergreen", "why_now": "Audience demand", "grounded_in": ["audience_q1"]},
                {"name": "Why X Matters Now", "hook": "X just changed everything.", "type": "trending", "why_now": "Recent announcement", "grounded_in": ["trending_1"]},
            ],
            "sources": [
                {"url": "https://example.com/study", "title": "Study on X", "used_for": "data_points"},
                {"url": "https://example.com/report", "title": "Market Report", "used_for": "data_points"},
                {"url": "https://example.com/survey", "title": "Expert Survey", "used_for": "data_points"},
                {"url": "https://example.com/reddit", "title": "Reddit Discussion", "used_for": "audience_insights"},
                {"url": "https://example.com/blog", "title": "Tech Blog", "used_for": "landscape"},
            ],
        }
    if name == "proposal_packet":
        return {
            "version": "1.0",
            "concept_options": [
                {
                    "id": "c1", "title": "The Surprising Truth About X", "hook": "You think X is slow.",
                    "narrative_structure": "myth_busting", "visual_approach": "animated diagrams",
                    "target_duration_seconds": 60, "why_this_works": "Strong misconception found in research",
                },
                {
                    "id": "c2", "title": "X From Scratch", "hook": "Build X in 5 minutes.",
                    "narrative_structure": "tutorial", "visual_approach": "code walkthrough",
                    "target_duration_seconds": 90, "why_this_works": "High demand in audience questions",
                },
                {
                    "id": "c3", "title": "Why X Matters Now", "hook": "X just changed everything.",
                    "narrative_structure": "timeline", "visual_approach": "motion graphics",
                    "target_duration_seconds": 75, "why_this_works": "Recent announcement creates timeliness",
                },
            ],
            "selected_concept": {"concept_id": "c1", "rationale": "Strongest research backing"},
            "production_plan": {
                "pipeline": "animated-explainer",
                "stages": [
                    {"stage": "script", "tools": [], "approach": "Write from research"},
                    {"stage": "assets", "tools": [{"tool_name": "tts_selector", "role": "narration", "available": True}], "approach": "Generate assets"},
                ],
            },
            "cost_estimate": {
                "total_estimated_usd": 0.52,
                "line_items": [{"tool": "elevenlabs_tts", "operation": "narration", "estimated_usd": 0.18}],
                "budget_verdict": "within_budget",
            },
            "approval": {"status": "approved"},
        }
    if name == "intent_contract":
        return {
            "version": "1.0",
            "anchor_title": "AI Video Production in 60 Seconds",
            "anchor_hook": "What if video production took less than a minute?",
            "target_audience": "Creators and marketers",
            "temporal_update_policy": "supporting_facts_only",
            "must_keep": [
                "AI video production framing",
                "Speed/automation value proposition",
            ],
            "can_change": [
                "current examples",
                "tool availability",
            ],
        }
    if name == "brief":
        return {
            "version": "1.0",
            "title": "Test Brief",
            "hook": "Did you know?",
            "key_points": ["point 1"],
            "tone": "casual",
            "style": "clean-professional",
            "target_platform": "youtube",
            "target_duration_seconds": 60,
        }
    if name == "script":
        return {
            "version": "1.0",
            "title": "Test Script",
            "total_duration_seconds": 60,
            "sections": [
                {
                    "id": "s1",
                    "text": "Hello world",
                    "start_seconds": 0,
                    "end_seconds": 10,
                    "source_ref": "https://example.com/source",
                }
            ],
        }
    if name == "editorial_qa":
        return {
            "version": "1.0",
            "status": "pass",
            "recommended_action": "proceed",
            "checks": {
                "title_alignment": {
                    "anchor_title": "Test Script",
                    "script_title": "Test Script",
                    "similarity_score": 1.0,
                    "policy_compliant": True,
                    "issues": [],
                },
                "temporal_alignment": {
                    "temporal_update_policy": "supporting_facts_only",
                    "allowed_scope_respected": True,
                    "issues": [],
                },
                "citation_coverage": {
                    "total_sections": 1,
                    "sections_with_sources": 1,
                    "coverage_ratio": 1.0,
                    "issues": [],
                },
                "compliance": {
                    "topic_risk": "low",
                    "financial_advice_disclaimer_present": False,
                    "outcome_overstatement_detected": False,
                    "issues": [],
                },
            },
            "issues_found": [],
        }
    if name == "scene_plan":
        return {
            "version": "1.0",
            "scenes": [
                {
                    "id": "scene-1",
                    "type": "talking_head",
                    "description": "Host on camera",
                    "start_seconds": 0,
                    "end_seconds": 10,
                }
            ],
        }
    if name == "asset_manifest":
        return {
            "version": "1.0",
            "assets": [
                {
                    "id": "asset-1",
                    "type": "video",
                    "path": "assets/clip.mp4",
                    "source_tool": "ffmpeg",
                    "scene_id": "scene-1",
                    "duration_seconds": 10,
                    "provider": "pixabay",
                }
            ],
            "quality_gate": {
                "passed": True,
                "fallback_video_count": 0,
                "total_video_count": 1,
                "fallback_runtime_seconds": 0,
                "total_video_runtime_seconds": 10,
                "fallback_runtime_ratio": 0,
                "max_consecutive_fallback_scenes": 0,
                "thresholds": {
                    "max_fallback_runtime_ratio": 0.2,
                    "max_consecutive_fallback_scenes": 2,
                },
                "blocked_reasons": [],
            },
        }
    if name == "edit_decisions":
        return {
            "version": "1.0",
            "cuts": [
                {
                    "id": "cut-1",
                    "source": "asset-1",
                    "in_seconds": 0,
                    "out_seconds": 10,
                }
            ],
        }
    if name == "render_report":
        return {
            "version": "1.0",
            "outputs": [
                {
                    "path": "renders/output.mp4",
                    "format": "mp4",
                    "resolution": "1920x1080",
                    "duration_seconds": 60,
                }
            ],
        }
    if name == "final_review":
        return {
            "version": "1.0",
            "output_path": "renders/output.mp4",
            "status": "pass",
            "checks": {
                "technical_probe": {
                    "valid_container": True,
                    "duration_seconds": 60,
                    "resolution": "1920x1080",
                    "fps": 30,
                    "has_audio": True,
                    "codec": "h264",
                    "file_size_bytes": 1000000,
                    "issues": [],
                },
                "visual_spotcheck": {
                    "frames_sampled": 4,
                    "frame_paths": ["f1.png", "f2.png", "f3.png", "f4.png"],
                    "black_frames_detected": False,
                    "broken_overlays": False,
                    "missing_assets": False,
                    "unreadable_text": False,
                    "issues": [],
                },
                "audio_spotcheck": {
                    "narration_present": True,
                    "music_present": False,
                    "unexpected_silence": False,
                    "clipping_detected": False,
                    "mix_intelligible": True,
                    "issues": [],
                },
                "promise_preservation": {
                    "delivery_promise_honored": True,
                    "renderer_family_used": "explainer-data",
                    "motion_ratio_actual": 0.6,
                    "silent_downgrade_detected": False,
                    "issues": [],
                },
                "subtitle_check": {
                    "subtitles_expected": True,
                    "subtitles_present": True,
                    "coverage_ratio": 1.0,
                    "timing_drift_detected": False,
                    "issues": [],
                },
            },
            "issues_found": [],
            "recommended_action": "present_to_user",
        }
    if name == "publish_log":
        return {
            "version": "1.0",
            "entries": [
                {
                    "platform": "youtube",
                    "status": "draft",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }
    if name == "video_analysis_brief":
        return {
            "version": "1.0",
            "source": {
                "type": "youtube",
                "url": "https://example.com/watch?v=abc123def45",
                "title": "Reference Video",
                "duration_seconds": 60,
            },
            "content_analysis": {
                "summary": "A fast explainer reference.",
                "topics": ["quantum computing"],
                "target_audience": "general",
            },
            "structure_analysis": {
                "total_scenes": 3,
                "scenes": [
                    {
                        "scene_index": 0,
                        "start_time": 0,
                        "end_time": 5,
                        "description": "Hook",
                    },
                    {
                        "scene_index": 1,
                        "start_time": 5,
                        "end_time": 20,
                        "description": "Setup",
                    },
                    {
                        "scene_index": 2,
                        "start_time": 20,
                        "end_time": 60,
                        "description": "Payoff",
                    },
                ],
                "pacing_profile": {
                    "avg_scene_duration_seconds": 20,
                    "cuts_per_minute": 3,
                    "pacing_style": "steady_educational",
                },
            },
        }
    raise KeyError(f"Unknown artifact sample: {name}")


# ---- Config ----

class TestConfig:
    def test_load_defaults(self):
        config = OpenMontageConfig()
        assert config.llm.provider == "anthropic"
        assert config.research_agent.provider is None
        assert config.research_agent.prompt_mode == "headless"
        assert config.routing.video_providers_allowed == []
        assert config.budget.mode.value == "warn"
        assert config.checkpoint.policy.value == "guided"

    def test_load_from_yaml(self):
        config = OpenMontageConfig.load()
        assert config.llm.provider == "ollama"
        assert config.llm.model == "qwen3-coder:latest"
        assert config.research_agent.provider is None
        assert config.research_agent.executable == "gemini"
        assert config.research_agent.approval_mode == "plan"
        assert config.routing.video_providers_allowed == ["pexels", "pixabay"]
        assert config.budget.total_usd == 10.0


# ---- Schemas ----

class TestSchemas:
    def test_all_schemas_loadable(self):
        names = list_schemas()
        assert len(names) >= 7
        for name in names:
            schema = load_schema(name)
            assert "$schema" in schema

    def test_brief_validates(self):
        validate_artifact("brief", sample_artifact("brief"))

    def test_brief_rejects_invalid(self):
        with pytest.raises(Exception):
            validate_artifact("brief", {"version": "1.0"})

    def test_video_analysis_brief_validates(self):
        validate_artifact("video_analysis_brief", sample_artifact("video_analysis_brief"))

    def test_intent_contract_validates(self):
        validate_artifact("intent_contract", sample_artifact("intent_contract"))

    def test_editorial_qa_validates(self):
        validate_artifact("editorial_qa", sample_artifact("editorial_qa"))


# ---- Checkpoint ----

class TestCheckpoint:
    def test_write_read_roundtrip(self, tmp_path):
        write_checkpoint(
            tmp_path, "test_project", "research", "completed",
            {"research_brief": sample_artifact("research_brief")},
        )
        cp = read_checkpoint(tmp_path, "test_project", "research")
        assert cp is not None
        assert cp["stage"] == "research"
        assert cp["status"] == "completed"
        assert cp["artifacts"]["research_brief"]["topic"] == "Test Topic"

    def test_get_next_stage(self, tmp_path):
        assert get_next_stage(tmp_path, "proj") == "research"
        write_checkpoint(
            tmp_path,
            "proj",
            "research",
            "completed",
            {"research_brief": sample_artifact("research_brief")},
        )
        assert get_next_stage(tmp_path, "proj") == "proposal"

    def test_invalid_stage_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            write_checkpoint(tmp_path, "proj", "invalid_stage", "completed", {})

    def test_invalid_canonical_artifact_rejected(self, tmp_path):
        with pytest.raises(CheckpointValidationError):
            write_checkpoint(
                tmp_path,
                "proj",
                "research",
                "completed",
                {"research_brief": {"topic": "missing schema fields"}},
            )

    def test_missing_canonical_artifact_rejected(self, tmp_path):
        with pytest.raises(CheckpointValidationError):
            write_checkpoint(tmp_path, "proj", "research", "completed", {})

    def test_invalid_status_rejected(self, tmp_path):
        with pytest.raises(CheckpointValidationError):
            write_checkpoint(
                tmp_path,
                "proj",
                "research",
                "mystery",
                {"research_brief": sample_artifact("research_brief")},
            )

    def test_supplementary_video_analysis_brief_is_validated(self, tmp_path):
        write_checkpoint(
            tmp_path,
            "proj",
            "proposal",
            "completed",
            {
                "proposal_packet": sample_artifact("proposal_packet"),
                "intent_contract": sample_artifact("intent_contract"),
                "video_analysis_brief": sample_artifact("video_analysis_brief"),
            },
        )
        cp = read_checkpoint(tmp_path, "proj", "proposal")
        assert cp is not None
        assert "video_analysis_brief" in cp["artifacts"]

    def test_proposal_requires_intent_contract(self, tmp_path):
        with pytest.raises(CheckpointValidationError):
            write_checkpoint(
                tmp_path,
                "proj",
                "proposal",
                "completed",
                {"proposal_packet": sample_artifact("proposal_packet")},
            )

    def test_script_requires_editorial_qa(self, tmp_path):
        with pytest.raises(CheckpointValidationError):
            write_checkpoint(
                tmp_path,
                "proj",
                "script",
                "completed",
                {"script": sample_artifact("script")},
            )

    def test_script_editorial_qa_must_pass(self, tmp_path):
        editorial_qa = sample_artifact("editorial_qa")
        editorial_qa["status"] = "review"
        editorial_qa["recommended_action"] = "await_human"
        with pytest.raises(CheckpointValidationError):
            write_checkpoint(
                tmp_path,
                "proj",
                "script",
                "completed",
                {
                    "script": sample_artifact("script"),
                    "editorial_qa": editorial_qa,
                },
            )

    def test_assets_quality_gate_rejects_fallback_heavy_manifest(self, tmp_path):
        asset_manifest = sample_artifact("asset_manifest")
        asset_manifest["assets"] = [
            {
                "id": "asset-1",
                "type": "video",
                "path": "assets/fallback1.mp4",
                "source_tool": "project_recovery",
                "scene_id": "scene-1",
                "duration_seconds": 8,
                "provider": "local_fallback",
                "generation_summary": "Stock query failed; generated local fallback card.",
            },
            {
                "id": "asset-2",
                "type": "video",
                "path": "assets/fallback2.mp4",
                "source_tool": "project_recovery",
                "scene_id": "scene-2",
                "duration_seconds": 8,
                "provider": "local_fallback",
                "generation_summary": "Stock query failed; generated local fallback card.",
            },
        ]
        asset_manifest["quality_gate"] = {
            "passed": False,
            "fallback_video_count": 2,
            "total_video_count": 2,
            "fallback_runtime_seconds": 16,
            "total_video_runtime_seconds": 16,
            "fallback_runtime_ratio": 1.0,
            "max_consecutive_fallback_scenes": 2,
            "thresholds": {
                "max_fallback_runtime_ratio": 0.2,
                "max_consecutive_fallback_scenes": 1,
            },
            "blocked_reasons": [
                "Fallback runtime ratio 100.0% exceeds threshold 20%",
                "Fallback run length 2 exceeds threshold 1",
            ],
        }
        with pytest.raises(CheckpointValidationError):
            write_checkpoint(
                tmp_path,
                "proj",
                "assets",
                "completed",
                {"asset_manifest": asset_manifest},
            )

    def test_compose_requires_passing_final_review(self, tmp_path):
        with pytest.raises(CheckpointValidationError):
            write_checkpoint(
                tmp_path,
                "proj",
                "compose",
                "completed",
                {"render_report": sample_artifact("render_report")},
            )


# ---- Pipeline manifests ----

class TestPipelineManifests:
    def test_framework_smoke_manifest_loads(self):
        manifest = load_pipeline("framework-smoke")
        assert manifest["name"] == "framework-smoke"
        assert get_stage_order(manifest) == ["research", "script"]
        assert get_required_tools(manifest) == set()

    def test_framework_smoke_manifest_listed(self):
        assert "framework-smoke" in list_pipelines()

    def test_reference_sub_stage_helpers(self):
        manifest = load_pipeline("animated-explainer")
        assert pipeline_supports_reference_input(manifest) is True
        assert "video_analyzer" in get_required_tools(manifest)

        all_units = get_stage_order(manifest, include_sub_stages=True)
        assert "proposal.sample" in all_units

        active_sub_stages = get_stage_sub_stages(
            manifest,
            "proposal",
            context={"video_analysis_brief_exists": True},
            include_inactive=False,
        )
        assert any(s["name"] == "sample" for s in active_sub_stages)


# ---- BaseTool ----

class DummyTool(BaseTool):
    name = "dummy"
    version = "0.1.0"
    tier = ToolTier.CORE
    capabilities = ["test"]
    dependencies = []

    def execute(self, inputs):
        return ToolResult(success=True, data={"echo": inputs})


class TestBaseTool:
    def test_get_info(self):
        tool = DummyTool()
        info = tool.get_info()
        assert info["name"] == "dummy"
        assert info["tier"] == "core"
        assert info["status"] == "available"

    def test_execute(self):
        tool = DummyTool()
        result = tool.execute({"msg": "hello"})
        assert result.success

    def test_unavailable_when_deps_missing(self):
        class MissingDepTool(BaseTool):
            name = "missing"
            dependencies = ["cmd:nonexistent_binary_xyz"]
            def execute(self, inputs):
                return ToolResult(success=True)

        tool = MissingDepTool()
        assert tool.get_status() == ToolStatus.UNAVAILABLE


# ---- ToolRegistry ----

class TestToolRegistry:
    def test_register_and_find(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        assert reg.get("dummy") is not None
        assert "dummy" in reg.list_all()
        assert len(reg.get_by_tier(ToolTier.CORE)) == 1
        assert len(reg.find_by_capability("test")) == 1

    def test_support_envelope(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        envelope = reg.support_envelope()
        assert "dummy" in envelope
        assert envelope["dummy"]["status"] == "available"

    def test_discovers_concrete_tools_from_package(self, tmp_path, monkeypatch):
        package_dir = tmp_path / "demo_tools"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (package_dir / "demo_tool.py").write_text(
            "\n".join(
                [
                    "from tools.base_tool import BaseTool, ToolResult, ToolTier",
                    "",
                    "class DiscoveredTool(BaseTool):",
                    "    name = 'discovered'",
                    "    tier = ToolTier.CORE",
                    "    capabilities = ['discover']",
                    "    dependencies = []",
                    "",
                    "    def execute(self, inputs):",
                    "        return ToolResult(success=True, data=inputs)",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        monkeypatch.syspath_prepend(str(tmp_path))
        importlib.invalidate_caches()

        reg = ToolRegistry()
        discovered = reg.discover("demo_tools")

        assert discovered == ["discovered"]
        assert reg.get("discovered") is not None
        assert reg.find_by_capability("discover")[0].name == "discovered"


# ---- CostTracker ----

class TestCostTracker:
    def test_estimate_reserve_reconcile(self):
        tracker = CostTracker(budget_total_usd=10.0, mode=BudgetMode.OBSERVE)
        entry_id = tracker.estimate("image_selector", "generate", 0.05)
        tracker.reserve(entry_id)
        assert tracker.budget_reserved_usd == 0.05
        tracker.reconcile(entry_id, 0.04, success=True)
        assert tracker.budget_spent_usd == 0.04
        assert tracker.budget_reserved_usd == 0.0

    def test_cap_mode_blocks_overspend(self):
        tracker = CostTracker(
            budget_total_usd=1.0,
            mode=BudgetMode.CAP,
            single_action_approval_usd=10.0,  # raise threshold so budget check triggers
        )
        tracker.approve_tool("expensive")
        eid = tracker.estimate("expensive", "op", 5.0)
        with pytest.raises(BudgetExceededError):
            tracker.reserve(eid)

    def test_persistence(self, tmp_path):
        log_path = tmp_path / "cost_log.json"
        t1 = CostTracker(budget_total_usd=10.0, mode=BudgetMode.OBSERVE, cost_log_path=log_path)
        eid = t1.estimate("tool", "op", 0.10)
        t1.reserve(eid)
        t1.reconcile(eid, 0.08)

        t2 = CostTracker(cost_log_path=log_path)
        assert t2.budget_spent_usd == 0.08

    def test_reference_estimate_falls_back_when_scene_types_are_unclassified(self):
        tracker = CostTracker(mode=BudgetMode.OBSERVE)
        brief = {
            "source": {"type": "shorts", "duration_seconds": 60},
            "structure_analysis": {
                "total_scenes": 12,
                "pacing_profile": {"pacing_style": "rapid_fire"},
                "scenes": [{"visual_type": "other"} for _ in range(12)],
            },
            "narration_transcript": {"word_count": 180},
            "replication_guidance": {"motion_required": True, "suggested_pipeline": "animation"},
        }
        plan = {
            "video_generation": {"tool": "kling_fal", "cost_per_unit": 0.3, "clip_duration_seconds": 5},
            "image_generation": {"tool": "flux_fal", "cost_per_unit": 0.05},
            "tts": {"tool": "elevenlabs_tts", "cost_per_word": 0.00003},
            "music": {"tool": "music_gen", "cost_per_track": 0.1},
        }

        estimate = tracker.estimate_from_reference(brief, 60, plan)

        assert estimate["motion_ratio"] >= 0.6
        assert estimate["estimated_clips"] >= 7
        assert any(
            "scene visual types have not been enriched yet" in note
            for note in estimate["assumptions"]
        )


# ---- Pipeline Instruction Architecture ----

class TestPipelineInstructionArchitecture:
    """Verify that the instruction-driven architecture is in place:
    manifests reference skills, not Python handlers."""

    def test_animated_explainer_stages_have_skills(self):
        try:
            manifest = load_pipeline("animated-explainer")
        except FileNotFoundError:
            pytest.skip("animated-explainer manifest not yet created")
        for stage in manifest["stages"]:
            assert "skill" in stage, f"Stage {stage['name']} missing skill field"

    def test_stage_skill_lookup(self):
        manifest = load_pipeline("framework-smoke")
        # framework-smoke may not have skills yet — just verify the function works
        result = get_stage_skill(manifest, "idea")
        assert result is None or isinstance(result, str)

    def test_stage_review_focus_lookup(self):
        manifest = load_pipeline("framework-smoke")
        result = get_stage_review_focus(manifest, "idea")
        assert isinstance(result, list)


# ---- Agent context files ----

class TestAgentContextFiles:
    def test_agent_guide_contains_canonical_sections(self):
        contents = (PROJECT_ROOT / "AGENT_GUIDE.md").read_text(encoding="utf-8")
        for header in (
            "## Orchestrator",
            "## Stage Agents",
            "## Reviewer Protocol",
            "## Communication Protocol",
            "## Human Checkpoint Protocol",
        ):
            assert header in contents

    def test_platform_wrappers_reference_agent_guide(self):
        for path in ("CLAUDE.md", "CODEX.md", "CURSOR.md", "COPILOT.md", "AGENTS.md"):
            contents = (PROJECT_ROOT / path).read_text(encoding="utf-8")
            assert "AGENT_GUIDE.md" in contents


# ---- Media Profiles ----

class TestMediaProfiles:
    def test_all_profiles_exist(self):
        assert len(ALL_PROFILES) >= 9

    def test_get_profile(self):
        p = get_profile("youtube_landscape")
        assert p.width == 1920
        assert p.height == 1080

    def test_ffmpeg_args(self):
        args = ffmpeg_output_args(get_profile("tiktok"))
        assert "-c:v" in args
        assert "1080" in args[-1]

    def test_unknown_profile_raises(self):
        with pytest.raises(ValueError):
            get_profile("nonexistent")
