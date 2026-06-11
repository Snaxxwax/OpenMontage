import json
import jsonschema
import pytest
from pathlib import Path

def test_publish_packet_schema_exists():
    schema_path = Path('/home/pop/repos/openmontage-asymmetric/channels/modern-archivist/schemas/publish_packet.schema.json')
    assert schema_path.exists(), "Publish packet schema file is missing"

def test_publish_packet_schema_validation():
    schema_path = Path('/home/pop/repos/openmontage-asymmetric/channels/modern-archivist/schemas/publish_packet.schema.json')
    
    # Ensure schema is valid JSON
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Validate schema structure
    assert isinstance(schema, dict), "Schema must be a JSON object"
    assert '$schema' in schema, "Schema must have a $schema key"
    assert 'type' in schema and schema['type'] == 'object', "Schema must define an object type"
    
    # Validate required fields for publish packet
    required_fields = [
        'title_variants', 
        'thumbnail_selection', 
        'chapters', 
        'description', 
        'pinned_comment', 
        'end_screen_target', 
        'teaser',
        'ai_disclosure_review'
    ]
    
    assert 'properties' in schema, "Schema must have properties defined"
    assert all(field in schema['properties'] for field in required_fields), \
        f"Missing one or more required fields: {required_fields}"
    
    # Example validation to ensure the schema can reject invalid data
    invalid_packets = [
        {},  # Empty packet
        {
            'title_variants': [],  # Must have at least one title
            'thumbnail_selection': None,
            'chapters': [],
            'description': '',
            'pinned_comment': '',
            'end_screen_target': '',
            'teaser': ''
        }
    ]
    
    for invalid_packet in invalid_packets:
        with pytest.raises(jsonschema.ValidationError), \
             open(schema_path, 'r') as f:
            schema = json.load(f)
            jsonschema.validate(instance=invalid_packet, schema=schema)

def test_publish_prep_contract():
    # Verify pipeline configuration requires publish_prep stage
    import yaml

    pipeline_path = Path('/home/pop/repos/openmontage-asymmetric/channels/modern-archivist/pipeline.yaml')

    with open(pipeline_path, 'r') as f:
        pipeline_config = yaml.safe_load(f)
    
    assert 'stages' in pipeline_config, "Pipeline must define stages"
    stages = pipeline_config.get('stages', [])
    
    publish_prep_stage = next((stage for stage in stages if stage.get('name') == 'publish_prep'), None)
    assert publish_prep_stage is not None, "Pipeline must have a publish_prep stage"
    assert 'checkpoint_required' in publish_prep_stage and publish_prep_stage['checkpoint_required'] is True, \
                "publish_prep stage must be marked as checkpoint_required"