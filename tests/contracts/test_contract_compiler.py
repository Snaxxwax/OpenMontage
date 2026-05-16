import hashlib
import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.contract.sources import discover_sources, hash_file, hash_sources
from tools.contract.drift import (
    DriftIssue,
    check_bootstrap_gap,
    check_pipeline_stage_skills,
    check_missing_schemas,
    check_agent_skills_refs,
    check_path_overlaps,
    run_all_checks,
)
from tools.contract.compiler import compile_contract
from tools.contract.checker import check_contract


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_minimal_repo(tmp_path: Path) -> Path:
    """Minimal repo skeleton sufficient for all compiler tests."""
    (tmp_path / "AGENTS.md").write_text(
        "# AGENTS\nread .agent_contract/agent_boot_packet.md\n"
    )
    (tmp_path / "AGENT_GUIDE.md").write_text("# Guide\n")
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()
    (agent_dir / "allowed_paths.yaml").write_text(
        "allowed_write_paths:\n  - docs/\nforbidden_write_paths:\n  - .git/\n"
    )
    (agent_dir / "repo_policy.yaml").write_text("repo_name: test\n")
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "INDEX.md").write_text("# INDEX\n")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "tool_registry.py").write_text("# registry\n")
    return tmp_path


# ── sources ───────────────────────────────────────────────────────────────────

def test_discover_sources_finds_agents_md(tmp_path):
    _make_minimal_repo(tmp_path)
    sources = discover_sources(tmp_path)
    names = [s.name for s in sources]
    assert "AGENTS.md" in names


def test_discover_sources_skips_missing_fixed(tmp_path):
    # Only AGENTS.md present — no AGENT_GUIDE.md etc.
    (tmp_path / "AGENTS.md").write_text("content")
    sources = discover_sources(tmp_path)
    assert all(s.exists() for s in sources)


def test_hash_file_returns_sha256_hex(tmp_path):
    f = tmp_path / "x.txt"
    f.write_bytes(b"hello")
    assert hash_file(f) == hashlib.sha256(b"hello").hexdigest()


def test_hash_sources_returns_str_dict(tmp_path):
    _make_minimal_repo(tmp_path)
    hashes = hash_sources(tmp_path)
    assert isinstance(hashes, dict)
    assert "AGENTS.md" in hashes
    assert len(hashes["AGENTS.md"]) == 64
    assert ".agent/repo_policy.yaml" in hashes
    assert ".agent/allowed_paths.yaml" in hashes


def test_hash_sources_keys_are_relative_paths(tmp_path):
    _make_minimal_repo(tmp_path)
    hashes = hash_sources(tmp_path)
    for key in hashes:
        assert not Path(key).is_absolute()


def test_discover_sources_deduplicates(tmp_path):
    _make_minimal_repo(tmp_path)
    # Create a pipeline_defs dir with a YAML that matches the glob
    pipeline_dir = tmp_path / "pipeline_defs"
    pipeline_dir.mkdir()
    (pipeline_dir / "test.yaml").write_text("stages: []\n")
    sources = discover_sources(tmp_path)
    resolved = [s.resolve() for s in sources]
    assert len(resolved) == len(set(resolved)), "discover_sources returned duplicates"


# ── drift checks ─────────────────────────────────────────────────────────────

def test_bootstrap_gap_detected_when_missing_reference(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# AGENTS\nno boot packet reference here\n")
    issues = check_bootstrap_gap(tmp_path)
    assert len(issues) == 1
    assert issues[0].check == "BOOTSTRAP GAP"
    assert issues[0].is_blocking


def test_no_bootstrap_gap_when_reference_present(tmp_path):
    (tmp_path / "AGENTS.md").write_text(
        "read `.agent_contract/agent_boot_packet.md` before acting\n"
    )
    assert check_bootstrap_gap(tmp_path) == []


def test_bootstrap_gap_blocking_when_agents_md_missing(tmp_path):
    issues = check_bootstrap_gap(tmp_path)
    assert len(issues) == 1
    assert issues[0].is_blocking


def test_missing_stage_skill_detected(tmp_path):
    (tmp_path / "pipeline_defs").mkdir()
    manifest = {
        "stages": [{"name": "research", "skill": "skills/pipelines/test/research-director.md"}]
    }
    (tmp_path / "pipeline_defs" / "test.yaml").write_text(yaml.dump(manifest))
    issues = check_pipeline_stage_skills(tmp_path)
    assert any(i.check == "MISSING STAGE SKILL" for i in issues)
    assert all(i.is_blocking for i in issues)


def test_valid_stage_skill_no_issue(tmp_path):
    (tmp_path / "pipeline_defs").mkdir()
    skill_dir = tmp_path / "skills" / "pipelines" / "test"
    skill_dir.mkdir(parents=True)
    (skill_dir / "research-director.md").write_text("# director\n")
    manifest = {
        "stages": [{"name": "research", "skill": "skills/pipelines/test/research-director.md"}]
    }
    (tmp_path / "pipeline_defs" / "test.yaml").write_text(yaml.dump(manifest))
    assert check_pipeline_stage_skills(tmp_path) == []


def test_stage_skill_resolves_missing_skills_prefix(tmp_path):
    """Path 'pipelines/foo/bar.md' (no skills/) resolves to 'skills/pipelines/foo/bar.md'."""
    (tmp_path / "pipeline_defs").mkdir()
    skill_dir = tmp_path / "skills" / "pipelines" / "test"
    skill_dir.mkdir(parents=True)
    (skill_dir / "research-director.md").write_text("# director\n")
    manifest = {"stages": [{"name": "research", "skill": "pipelines/test/research-director.md"}]}
    (tmp_path / "pipeline_defs" / "test.yaml").write_text(yaml.dump(manifest))
    assert check_pipeline_stage_skills(tmp_path) == []


def test_stage_skill_resolves_missing_md_extension(tmp_path):
    """Path 'skills/pipelines/foo/bar' (no .md) resolves to 'skills/pipelines/foo/bar.md'."""
    (tmp_path / "pipeline_defs").mkdir()
    skill_dir = tmp_path / "skills" / "pipelines" / "test"
    skill_dir.mkdir(parents=True)
    (skill_dir / "research-director.md").write_text("# director\n")
    manifest = {"stages": [{"name": "research", "skill": "skills/pipelines/test/research-director"}]}
    (tmp_path / "pipeline_defs" / "test.yaml").write_text(yaml.dump(manifest))
    assert check_pipeline_stage_skills(tmp_path) == []


def test_stage_skill_resolves_missing_prefix_and_extension(tmp_path):
    """Shorthand 'pipelines/foo/bar' (no skills/, no .md) resolves to 'skills/pipelines/foo/bar.md'."""
    (tmp_path / "pipeline_defs").mkdir()
    skill_dir = tmp_path / "skills" / "pipelines" / "test"
    skill_dir.mkdir(parents=True)
    (skill_dir / "research-director.md").write_text("# director\n")
    manifest = {"stages": [{"name": "research", "skill": "pipelines/test/research-director"}]}
    (tmp_path / "pipeline_defs" / "test.yaml").write_text(yaml.dump(manifest))
    assert check_pipeline_stage_skills(tmp_path) == []


def test_truly_missing_stage_skill_still_blocking(tmp_path):
    """A stage skill absent under all four resolution candidates remains BLOCKING."""
    (tmp_path / "pipeline_defs").mkdir()
    manifest = {"stages": [{"name": "research", "skill": "pipelines/nonexistent/ghost-director"}]}
    (tmp_path / "pipeline_defs" / "test.yaml").write_text(yaml.dump(manifest))
    issues = check_pipeline_stage_skills(tmp_path)
    assert len(issues) == 1
    assert issues[0].check == "MISSING STAGE SKILL"
    assert issues[0].is_blocking


def test_missing_schema_detected(tmp_path):
    (tmp_path / "pipeline_defs").mkdir()
    manifest = {
        "stages": [{"name": "research", "output_schema": "schemas/artifacts/research.json"}]
    }
    (tmp_path / "pipeline_defs" / "test.yaml").write_text(yaml.dump(manifest))
    issues = check_missing_schemas(tmp_path)
    assert any(i.check == "MISSING SCHEMA" for i in issues)
    assert all(i.is_blocking for i in issues)


def test_valid_schema_no_issue(tmp_path):
    (tmp_path / "pipeline_defs").mkdir()
    schema_dir = tmp_path / "schemas" / "artifacts"
    schema_dir.mkdir(parents=True)
    (schema_dir / "research.json").write_text("{}")
    manifest = {
        "stages": [{"name": "research", "output_schema": "schemas/artifacts/research.json"}]
    }
    (tmp_path / "pipeline_defs" / "test.yaml").write_text(yaml.dump(manifest))
    assert check_missing_schemas(tmp_path) == []


def test_path_overlap_detected(tmp_path):
    (tmp_path / ".agent").mkdir()
    data = {
        "allowed_write_paths": ["docs/", "shared/"],
        "forbidden_write_paths": ["docs/"],
    }
    (tmp_path / ".agent" / "allowed_paths.yaml").write_text(yaml.dump(data))
    issues = check_path_overlaps(tmp_path)
    assert any(i.check == "PATH POLICY OVERLAP" for i in issues)
    assert issues[0].is_blocking


def test_no_path_overlap_when_clean(tmp_path):
    (tmp_path / ".agent").mkdir()
    data = {
        "allowed_write_paths": ["docs/"],
        "forbidden_write_paths": [".git/"],
    }
    (tmp_path / ".agent" / "allowed_paths.yaml").write_text(yaml.dump(data))
    assert check_path_overlaps(tmp_path) == []


def test_drift_issue_format_md_includes_severity():
    issue = DriftIssue("BLOCKING", "TEST CHECK", "some detail", source="AGENTS.md")
    rendered = issue.format_md()
    assert "BLOCKING" in rendered
    assert "TEST CHECK" in rendered
    assert "AGENTS.md" in rendered


def test_run_all_checks_returns_bootstrap_issue_on_empty_repo(tmp_path):
    # An empty repo has no AGENTS.md → run_all_checks should return at least one issue
    issues = run_all_checks(tmp_path)
    checks = {i.check for i in issues}
    assert "MISSING SOURCE FILE" in checks or "BOOTSTRAP GAP" in checks


def test_broken_agent_skills_ref_detected(tmp_path):
    tool_file = tmp_path / "tools" / "audio" / "tts.py"
    tool_file.parent.mkdir(parents=True)
    tool_file.write_text(
        'agent_skills = [".agents/skills/nonexistent/SKILL.md"]\n'
    )
    issues = check_agent_skills_refs(tmp_path)
    assert any(i.check == "BROKEN AGENT_SKILLS REF" for i in issues)
    assert all(not i.is_blocking for i in issues)  # WARNING, not BLOCKING


def test_broken_agent_skills_ref_detected_single_quotes(tmp_path):
    tool_file = tmp_path / "tools" / "audio" / "tts.py"
    tool_file.parent.mkdir(parents=True)
    tool_file.write_text(
        "agent_skills = ['.agents/skills/nonexistent/SKILL.md']\n"
    )
    issues = check_agent_skills_refs(tmp_path)
    assert any(i.check == "BROKEN AGENT_SKILLS REF" for i in issues)
    assert all(not i.is_blocking for i in issues)


def test_valid_agent_skills_ref_no_issue(tmp_path):
    skill_path = tmp_path / ".agents" / "skills" / "elevenlabs" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("# skill\n")
    tool_file = tmp_path / "tools" / "audio" / "tts.py"
    tool_file.parent.mkdir(parents=True)
    tool_file.write_text(
        'agent_skills = [".agents/skills/elevenlabs/SKILL.md"]\n'
    )
    assert check_agent_skills_refs(tmp_path) == []


# ── compiler integration ──────────────────────────────────────────────────────

def test_compile_emits_three_files(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    contract_dir = tmp_path / ".agent_contract"
    assert (contract_dir / "agent_boot_packet.md").exists()
    assert (contract_dir / "contract_status.yaml").exists()
    assert (contract_dir / "drift_report.md").exists()


def test_compile_contract_status_has_required_keys(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    status = yaml.safe_load((tmp_path / ".agent_contract" / "contract_status.yaml").read_text())
    for key in ("compiled_at", "sources", "stale", "missing_sources", "blocking_conflicts", "bootstrap_ok"):
        assert key in status, f"Missing key: {key}"


def test_compile_stale_is_false_immediately_after_compile(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    status = yaml.safe_load((tmp_path / ".agent_contract" / "contract_status.yaml").read_text())
    assert status["stale"] is False


def test_compile_bootstrap_ok_true_when_reference_present(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    status = yaml.safe_load((tmp_path / ".agent_contract" / "contract_status.yaml").read_text())
    assert status["bootstrap_ok"] is True


def test_compile_bootstrap_ok_false_when_reference_absent(tmp_path):
    _make_minimal_repo(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# AGENTS\nno boot packet reference\n")
    compile_contract(root=tmp_path)
    status = yaml.safe_load((tmp_path / ".agent_contract" / "contract_status.yaml").read_text())
    assert status["bootstrap_ok"] is False
    assert status["blocking_conflicts"] is True


def test_compile_boot_packet_contains_operational_rules(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    content = (tmp_path / ".agent_contract" / "agent_boot_packet.md").read_text()
    assert "Stop Conditions" in content
    assert "Operational Rules" in content
    assert "tool_registry" in content


def test_compile_boot_packet_contains_extracted_paths(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    content = (tmp_path / ".agent_contract" / "agent_boot_packet.md").read_text()
    assert "docs/" in content    # from _make_minimal_repo's allowed_paths.yaml
    assert ".git/" in content    # from forbidden


def test_compile_does_not_write_outside_agent_contract(tmp_path):
    _make_minimal_repo(tmp_path)
    before = set(tmp_path.rglob("*"))
    compile_contract(root=tmp_path)
    after = set(tmp_path.rglob("*"))
    new_files = after - before
    for f in new_files:
        assert ".agent_contract" in str(f), f"Compiler wrote outside .agent_contract/: {f}"


def test_compile_drift_report_lists_blocking_issues(tmp_path):
    _make_minimal_repo(tmp_path)
    # Remove boot packet reference → triggers BOOTSTRAP GAP (BLOCKING)
    (tmp_path / "AGENTS.md").write_text("# AGENTS\nno boot reference\n")
    compile_contract(root=tmp_path)
    report = (tmp_path / ".agent_contract" / "drift_report.md").read_text()
    assert "Blocking" in report
    assert "BOOTSTRAP GAP" in report


def test_compile_drift_report_clean_when_no_issues(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    report = (tmp_path / ".agent_contract" / "drift_report.md").read_text()
    assert "No issues detected" in report


# ── checker ───────────────────────────────────────────────────────────────────

def test_check_fails_when_status_missing(tmp_path):
    assert check_contract(root=tmp_path) == 1


def test_check_fails_when_boot_packet_missing(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    (tmp_path / ".agent_contract" / "agent_boot_packet.md").unlink()
    assert check_contract(root=tmp_path) == 1


def test_check_fails_when_drift_report_missing(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    (tmp_path / ".agent_contract" / "drift_report.md").unlink()
    assert check_contract(root=tmp_path) == 1


def test_check_returns_2_when_status_malformed(tmp_path):
    contract_dir = tmp_path / ".agent_contract"
    contract_dir.mkdir()
    (contract_dir / "contract_status.yaml").write_text("- not\n- a\n- dict\n")
    (contract_dir / "agent_boot_packet.md").write_text("# boot\n")
    (contract_dir / "drift_report.md").write_text("# drift\n")
    assert check_contract(root=tmp_path) == 2


def test_check_passes_after_clean_compile(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    assert check_contract(root=tmp_path) == 0


def test_check_fails_when_source_modified_after_compile(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        "# AGENTS modified\nread .agent_contract/agent_boot_packet.md\n"
    )
    assert check_contract(root=tmp_path) == 1


def test_check_stale_new_file_not_double_counted(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    # Add a new source file that wasn't present at compile time
    new_schema = tmp_path / "schemas" / "artifacts"
    new_schema.mkdir(parents=True, exist_ok=True)
    (new_schema / "new_artifact.json").write_text("{}")
    result = check_contract(root=tmp_path)
    assert result == 1  # stale, but new file should only appear once in the list


def test_check_fails_when_blocking_conflicts(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    status_path = tmp_path / ".agent_contract" / "contract_status.yaml"
    status = yaml.safe_load(status_path.read_text())
    status["blocking_conflicts"] = True
    status["bootstrap_ok"] = True
    status["missing_sources"] = []
    status_path.write_text(yaml.dump(status))
    assert check_contract(root=tmp_path) == 1


def test_check_fails_when_bootstrap_not_ok(tmp_path):
    _make_minimal_repo(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# AGENTS\nno boot reference\n")
    compile_contract(root=tmp_path)
    status = yaml.safe_load(
        (tmp_path / ".agent_contract" / "contract_status.yaml").read_text()
    )
    assert status["bootstrap_ok"] is False
    assert check_contract(root=tmp_path) == 1


def test_check_fails_when_missing_sources(tmp_path):
    _make_minimal_repo(tmp_path)
    compile_contract(root=tmp_path)
    # Inject a missing_sources entry into the status file
    status_path = tmp_path / ".agent_contract" / "contract_status.yaml"
    status = yaml.safe_load(status_path.read_text())
    status["missing_sources"] = ["skills/INDEX.md"]
    status_path.write_text(yaml.dump(status))
    assert check_contract(root=tmp_path) == 1
