import json
import os
import pytest
from jsonschema import validate, ValidationError

# Schema directory
SCHEMAS_DIR = os.path.abspath("schemas/artifacts")
FIXTURES_DIR = os.path.abspath("tests/fixtures/source-commentary")

def load_schema(name):
    path = os.path.join(SCHEMAS_DIR, f"{name}.schema.json")
    with open(path, "r") as f:
        return json.load(f)

def load_fixture(subdir, name):
    path = os.path.join(FIXTURES_DIR, subdir, f"{name}.json")
    with open(path, "r") as f:
        return json.load(f)

def get_resolver(schema):
    from jsonschema import RefResolver
    # Use a file URL base for local resolution of relative $refs
    base_uri = f"file://{SCHEMAS_DIR}/"
    return RefResolver(base_uri=base_uri, referrer=schema)

# --- Valid Fixture Tests ---

@pytest.mark.parametrize("artifact", [
    "research_brief",
    "narration_claim_map",
    "source_candidate_manifest",
    "transcript_index",
    "evidence_candidate_manifest",
    "clip_use_receipts",
    "extracted_clip_manifest",
    "approved_clip_manifest",
    "source_commentary_edit_plan",
    "source_commentary_render_report",
    "source_commentary_qc_report"
])
def test_valid_fixtures(artifact):
    schema = load_schema(artifact)
    fixture = load_fixture("basic", artifact)
    resolver = get_resolver(schema)
    validate(instance=fixture, schema=schema, resolver=resolver)

# --- Invalid Fixture Tests ---

def test_approved_receipt_marked_decorative_broll_fails():
    schema = load_schema("clip_use_receipts")
    fixture = load_fixture("invalid", "approved_receipt_marked_decorative_broll")
    resolver = get_resolver(schema)
    
    with pytest.raises(ValidationError) as excinfo:
        validate(instance=fixture, schema=schema, resolver=resolver)
    assert "decorative_broll" in str(excinfo.value)

def test_source_candidate_with_local_media_path_fails():
    schema = load_schema("source_candidate_manifest")
    fixture = load_fixture("invalid", "source_candidate_with_local_media_path")
    
    with pytest.raises(ValidationError) as excinfo:
        validate(instance=fixture, schema=schema)
    assert "local_media_path" in str(excinfo.value)

def test_edit_plan_missing_receipt_id_fails():
    schema = load_schema("source_commentary_edit_plan")
    fixture = load_fixture("invalid", "edit_plan_missing_receipt_id")
    
    with pytest.raises(ValidationError) as excinfo:
        validate(instance=fixture, schema=schema)
    assert "receipt_id" in str(excinfo.value)

def test_approved_clip_without_source_label_fails():
    schema = load_schema("approved_clip_manifest")
    fixture = load_fixture("invalid", "approved_clip_without_source_label")
    
    with pytest.raises(ValidationError) as excinfo:
        validate(instance=fixture, schema=schema)
    assert "source_label_required" in str(excinfo.value)
