import json
import jsonschema
import pytest
import yaml
from pathlib import Path

def test_retention_analysis_schema_exists():
    """Verify that the retention analysis schema exists."""
    schema_path = Path(__file__).parents[2] / 'channels/modern-archivist/schemas/retention_analysis.schema.json'
    assert schema_path.exists(), f"Retention analysis schema not found at {schema_path}"

def test_retention_analysis_schema_valid():
    """Verify the retention analysis schema is a valid JSON schema."""
    schema_path = Path(__file__).parents[2] / 'channels/modern-archivist/schemas/retention_analysis.schema.json'
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Basic JSON schema validation
    jsonschema.validators.Draft7Validator.check_schema(schema)

def test_retention_review_stage_in_pipeline():
    """Verify the retention_review stage exists in the pipeline."""
    pipeline_path = Path(__file__).parents[2] / 'channels/modern-archivist/pipeline.yaml'
    
    with open(pipeline_path, 'r') as f:
        pipeline_config = yaml.safe_load(f)
    
    stages = pipeline_config.get('stages', [])
    assert any(stage.get('name') == 'retention_review' for stage in stages), \
        "retention_review stage not found in pipeline configuration"