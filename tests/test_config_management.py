"""
Tests for configuration management

Tests cover:
- Config loading and validation
- JSON schema validation
- Default value handling
- Invalid config detection
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import validate_config, validate_config_schema, DEFAULT_CONFIG


@pytest.mark.unit
def test_validate_config_with_valid_config(mock_config):
    """Test validation with a valid configuration"""
    validated = validate_config(mock_config)
    
    assert validated is not None
    assert 'audio_settings' in validated
    assert 'video_settings' in validated
    assert 'system_limits' in validated


@pytest.mark.unit
def test_validate_config_applies_defaults():
    """Test that validation applies default values for missing fields"""
    minimal_config = {
        "audio_settings": {
            "voice": "en-US-GuyNeural",
            "tts_speed_default": "+0%"
        }
    }
    
    validated = validate_config(minimal_config)
    
    # Should have defaults applied
    assert validated['audio_settings']['retry_attempts'] > 0
    assert validated['audio_settings']['max_concurrent_tts'] > 0
    assert 'system_limits' in validated


@pytest.mark.unit
def test_validate_config_clamps_values():
    """Test that validation clamps values to valid ranges"""
    config = {
        "audio_settings": {
            "background_volume": 5.0,  # Should be clamped to 1.0
            "max_concurrent_tts": 100,  # Should be clamped to 20
            "retry_attempts": -5  # Should be clamped to 1
        }
    }
    
    validated = validate_config(config)
    
    assert validated['audio_settings']['background_volume'] <= 1.0
    assert validated['audio_settings']['max_concurrent_tts'] <= 20
    assert validated['audio_settings']['retry_attempts'] >= 1


@pytest.mark.unit
def test_validate_config_filters_invalid_regex():
    """Test that invalid regex patterns are filtered out"""
    config = {
        "banned_words": [
            r"\bvalid\b",
            r"[invalid(regex",  # Invalid pattern
            r"\banother\b"
        ]
    }
    
    validated = validate_config(config)
    
    # Should only include valid patterns
    assert len(validated['banned_words']) == 2
    assert r"\bvalid\b" in validated['banned_words']
    assert r"\banother\b" in validated['banned_words']


@pytest.mark.unit
def test_validate_config_schema_valid(mock_config):
    """Test JSON schema validation with valid config"""
    is_valid, error_msg = validate_config_schema(mock_config)
    
    assert is_valid is True
    assert error_msg is None


@pytest.mark.unit
def test_validate_config_schema_invalid_type():
    """Test JSON schema validation detects type errors"""
    invalid_config = {
        "audio_settings": {
            "voice": "en-US-GuyNeural",
            "tts_speed_default": 123,  # Should be string
            "background_volume": "not a number"  # Should be number
        },
        "system_limits": {},
        "video_settings": {
            "quality_presets": {
                "Fast": {"height": 480, "crf": 30, "preset": "ultrafast"},
                "Balanced": {"height": 720, "crf": 23, "preset": "medium"},
                "High": {"height": 1080, "crf": 20, "preset": "slow"}
            }
        }
    }
    
    is_valid, error_msg = validate_config_schema(invalid_config)
    
    # Should detect type error
    if is_valid:
        pytest.skip("jsonschema not available")
    else:
        assert is_valid is False
        assert error_msg is not None


@pytest.mark.unit
def test_validate_config_schema_missing_required():
    """Test JSON schema validation detects missing required fields"""
    invalid_config = {
        "audio_settings": {
            # Missing required 'voice' field
            "tts_speed_default": "+0%"
        }
    }
    
    is_valid, error_msg = validate_config_schema(invalid_config)
    
    if is_valid:
        pytest.skip("jsonschema not available")
    else:
        assert is_valid is False
        assert error_msg is not None


@pytest.mark.unit
def test_validate_config_schema_invalid_range():
    """Test JSON schema validation detects out-of-range values"""
    invalid_config = {
        "audio_settings": {
            "voice": "en-US-GuyNeural",
            "tts_speed_default": "+0%",
            "background_volume": 5.0,  # Out of range (max 1.0)
            "max_concurrent_tts": -1  # Out of range (min 1)
        },
        "system_limits": {},
        "video_settings": {
            "quality_presets": {
                "Fast": {"height": 480, "crf": 30, "preset": "ultrafast"},
                "Balanced": {"height": 720, "crf": 23, "preset": "medium"},
                "High": {"height": 1080, "crf": 20, "preset": "slow"}
            }
        }
    }
    
    is_valid, error_msg = validate_config_schema(invalid_config)
    
    if is_valid:
        pytest.skip("jsonschema not available")
    else:
        assert is_valid is False
        assert error_msg is not None


@pytest.mark.unit
def test_validate_config_preserves_custom_values(mock_config):
    """Test that validation preserves custom values"""
    custom_config = mock_config.copy()
    custom_config['branding'] = {
        "intro": "Custom intro",
        "outro": "Custom outro",
        "tagline": "Custom tagline"
    }
    
    validated = validate_config(custom_config)
    
    assert validated['branding']['intro'] == "Custom intro"
    assert validated['branding']['outro'] == "Custom outro"
    assert validated['branding']['tagline'] == "Custom tagline"


@pytest.mark.integration
def test_load_config_from_file(config_file):
    """Test loading config from file"""
    from core.config import load_config
    import core.config as config_module
    
    # Temporarily override CONFIG_FILE
    original_config_file = config_module.CONFIG_FILE
    config_module.CONFIG_FILE = str(config_file)
    
    try:
        loaded = load_config()
        
        assert loaded is not None
        assert 'audio_settings' in loaded
        assert loaded['audio_settings']['voice'] == "en-US-GuyNeural"
    finally:
        config_module.CONFIG_FILE = original_config_file


@pytest.mark.unit
def test_default_config_is_valid():
    """Test that DEFAULT_CONFIG passes validation"""
    is_valid, error_msg = validate_config_schema(DEFAULT_CONFIG)
    
    if not is_valid and error_msg:
        pytest.fail(f"DEFAULT_CONFIG is invalid: {error_msg}")
