from __future__ import annotations

import json
import yaml
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = ROOT / "channels" / "modern-archivist"
STYLES_FILE = ROOT / "styles" / "modern-archivist.yaml"

def test_motion_performance_metrics_exist() -> None:
    """Verify that motion performance metrics are defined in the styles."""
    with open(STYLES_FILE, 'r') as f:
        styles = yaml.safe_load(f)
    
    motion_keys = [
        "total_motion_changes_per_minute",
        "visual_beat_frequency_seconds",
        "source_artifact_coverage_percent",
        "critical_error_time_limit_seconds"
    ]
    
    for key in motion_keys:
        assert key in styles['motion']['pacing_rules'], f"Missing performance key: {key}"

def test_audio_performance_metrics_exist() -> None:
    """Verify that audio performance metrics are defined in the styles."""
    with open(STYLES_FILE, 'r') as f:
        styles = yaml.safe_load(f)
    
    audio_keys = [
        "words_per_minute",
        "pause_frequency_seconds",
        "dynamic_range_db"
    ]
    
    for key in audio_keys:
        assert key in styles['audio']['narration'], f"Missing narration performance key: {key}"

def test_render_is_not_finish_line() -> None:
    """Verify that the retention doctrine emphasizes post-render steps."""
    doctrine_path = CHANNEL_DIR / "design" / "retention-doctrine.md"
    with open(doctrine_path, 'r') as f:
        doctrine_text = f.read()
    
    post_render_markers = [
        "Render is NOT the Finish Line",
        "No episode is considered complete",
        "Packaging: Metadata, thumbnails, chapter markers",
        "Post-Publish Review"
    ]
    
    for marker in post_render_markers:
        assert marker in doctrine_text, f"Missing post-render emphasis: {marker}"

def test_playbook_performance_constraints() -> None:
    """Validate hardcoded performance constraints."""
    # Validate specific values
    constraints = {
        'motion.pacing_rules.total_motion_changes_per_minute': (10, 15),  # 12 is the current value
        'motion.pacing_rules.source_artifact_coverage_percent': (60, 85),
        'motion.pacing_rules.critical_error_time_limit_seconds': (5, 15),
        'audio.narration.words_per_minute': (100, 140),
        'audio.narration.pause_frequency_seconds': (30, 60)
    }
    
    with open(STYLES_FILE, 'r') as f:
        styles = yaml.safe_load(f)
    
    for key, (min_val, max_val) in constraints.items():
        # Navigate nested dict
        keys = key.split('.')
        value = styles
        for subkey in keys:
            value = value[subkey]
        
        assert min_val <= value <= max_val, f"Value for {key} not within expected range"

def test_red_state_constraints() -> None:
    """Verify red state usage constraints."""
    quality_rules = [
        "Red state (STATE_CRITICAL_ERROR) is scarce: 3–12 seconds maximum unless operator approves longer"
    ]
    
    with open(STYLES_FILE, 'r') as f:
        styles = yaml.safe_load(f)
    
    for rule in quality_rules:
        assert rule in styles['quality_rules'], f"Missing rule: {rule}"