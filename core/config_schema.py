"""
JSON Schema for config.json validation

Defines the complete schema for validating the EPUB converter configuration file.
"""

CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "EPUB to Audiobook/Video Converter Configuration",
    "description": "Configuration schema for the EPUB converter application",
    "type": "object",
    "required": ["audio_settings", "system_limits", "video_settings"],
    "properties": {
        "audio_settings": {
            "type": "object",
            "description": "Audio and TTS configuration",
            "required": ["voice", "tts_speed_default"],
            "properties": {
                "voice": {
                    "type": "string",
                    "description": "Edge-TTS voice name",
                    "examples": ["en-US-GuyNeural", "en-US-AriaNeural"]
                },
                "background_volume": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.1,
                    "description": "Background music volume (0.0 to 1.0)"
                },
                "background_music_path": {
                    "type": "string",
                    "description": "Path to background music file"
                },
                "tts_speed_default": {
                    "type": "string",
                    "pattern": "^[+-]\\d+%$",
                    "description": "TTS speed adjustment (e.g., '+0%', '+10%', '-5%')",
                    "examples": ["+0%", "+10%", "-5%"]
                },
                "max_concurrent_tts": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 4,
                    "description": "Maximum concurrent TTS requests"
                },
                "retry_attempts": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Number of retry attempts for failed TTS"
                },
                "retry_delay": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 60,
                    "default": 3,
                    "description": "Delay between retries in seconds"
                },
                "edge_tts_request_delay": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 5,
                    "default": 0.8,
                    "description": "Delay between Edge-TTS requests in seconds"
                },
                "min_audio_size_mb": {
                    "type": "number",
                    "minimum": 0,
                    "default": 0.5,
                    "description": "Minimum expected audio file size in MB"
                },
                "piper_model_path": {
                    "type": "string",
                    "description": "Path to Piper TTS model file"
                },
                "piper_speaker_id": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0,
                    "description": "Piper speaker ID"
                },
                "piper_noise_scale": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 0.667,
                    "description": "Piper noise scale parameter"
                },
                "piper_length_scale": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 3.0,
                    "default": 1.0,
                    "description": "Piper length scale (speed adjustment)"
                },
                "export_bitrate": {
                     "type": "string", 
                     "pattern": "^\\d+k$"
                },
                "chatterbox_enabled": {"type": "boolean"},
                "chatterbox_model": {"type": "string"},
                "chatterbox_tier": {"type": "string"}
            }
        },
        "system_limits": {
            "type": "object",
            "description": "System resource limits and thresholds",
            "properties": {
                "max_batch_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 50,
                    "description": "Maximum batch size for processing"
                },
                "ram_warning_threshold_mb": {
                    "type": "integer",
                    "minimum": 100,
                    "default": 1500,
                    "description": "RAM usage warning threshold in MB"
                },
                "enable_memory_monitoring": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable memory usage monitoring"
                },
                "min_disk_space_gb": {
                    "type": "number",
                    "minimum": 0.1,
                    "default": 2.0,
                    "description": "Minimum required disk space in GB"
                },
                "max_chapter_length_chars": {
                    "type": "integer",
                    "minimum": 1000,
                    "default": 50000,
                    "description": "Maximum chapter length in characters"
                }
            }
        },
        "branding": {
            "type": "object",
            "description": "Branding and messaging configuration",
            "properties": {
                "intro": {
                    "type": "string",
                    "description": "Introduction message for audiobooks"
                },
                "outro": {
                    "type": "string",
                    "description": "Outro message for audiobooks"
                },
                "tagline": {
                    "type": "string",
                    "description": "Channel or brand tagline"
                },
                "intro_disclaimer_delay": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 10,
                    "default": 0,
                    "description": "Delay between intro and disclaimer in seconds"
                }
            }
        },
        "video_settings": {
            "type": "object",
            "description": "Video rendering configuration",
            "required": ["quality_presets"],
            "properties": {
                "enable_text_overlay": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable text overlay on videos"
                },
                "enable_chapter_markers": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable chapter markers in videos"
                },
                "enable_subtitles": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable subtitle generation"
                },
                "embed_subtitles": {
                    "type": "boolean",
                    "default": True,
                    "description": "Embed subtitles in video file"
                },
                "subtitle_max_chars": {
                    "type": "integer",
                    "minimum": 20,
                    "maximum": 200,
                    "default": 60,
                    "description": "Maximum characters per subtitle line"
                },
                "subtitle_reading_speed_wps": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 10.0,
                    "default": 2.5,
                    "description": "Subtitle reading speed in words per second"
                },
                "text_overlay_font_size": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 200,
                    "default": 36,
                    "description": "Font size for text overlay"
                },
                "text_overlay_bottom_margin": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 500,
                    "default": 40,
                    "description": "Bottom margin for text overlay in pixels"
                },
                "use_advanced_renderer": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use advanced FFmpeg renderer"
                },
                "current_quality_preset": {
                    "type": "string",
                    "enum": ["Fast", "Balanced", "High"],
                    "default": "Fast",
                    "description": "Current quality preset to use"
                },
                "quality_presets": {
                    "type": "object",
                    "description": "Video quality presets",
                    "required": ["Fast", "Balanced", "High"],
                    "properties": {
                        "Fast": {
                            "$ref": "#/definitions/quality_preset"
                        },
                        "Balanced": {
                            "$ref": "#/definitions/quality_preset"
                        },
                        "High": {
                            "$ref": "#/definitions/quality_preset"
                        }
                    }
                },
                "caption_style": {
                    "type": "object",
                    "description": "Caption styling configuration",
                    "properties": {
                        "preset": {
                            "type": "string",
                            "description": "Caption style preset name"
                        },
                        "font": {
                            "type": "string",
                            "description": "Font family name"
                        },
                        "font_size": {
                            "type": "integer",
                            "minimum": 10,
                            "maximum": 200,
                            "description": "Font size"
                        },
                        "bold": {
                            "type": "boolean",
                            "description": "Use bold font"
                        },
                        "color": {
                            "type": "string",
                            "pattern": "^#[0-9A-Fa-f]{6}$",
                            "description": "Text color in hex format"
                        },
                        "stroke_color": {
                            "type": "string",
                            "pattern": "^#[0-9A-Fa-f]{6}$",
                            "description": "Stroke color in hex format"
                        },
                        "stroke_width": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 20,
                            "description": "Stroke width in pixels"
                        }
                    }
                }
            }
        },
        "cleanup_settings": {
            "type": "object",
            "description": "Cleanup and maintenance settings",
            "properties": {
                "auto_cleanup_on_startup": {
                    "type": "boolean",
                    "default": True,
                    "description": "Automatically cleanup old files on startup"
                },
                "max_temp_age_days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 5,
                    "description": "Maximum age of temporary files in days"
                },
                "min_size_for_cleanup_mb": {
                    "type": "number",
                    "minimum": 0,
                    "default": 5,
                    "description": "Minimum file size for cleanup in MB"
                },
                "warn_threshold_mb": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 800,
                    "description": "Warning threshold for cleanup in MB"
                }
            }
        },
        "recovery_settings": {
            "type": "object",
            "description": "Auto-recovery configuration",
            "properties": {
                "enable_auto_recovery": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable automatic error recovery"
                },
                "auto_approve_safe_fixes": {
                    "type": "boolean",
                    "default": False,
                    "description": "Automatically approve safe fixes"
                },
                "silent_mode": {
                    "type": "boolean",
                    "default": False,
                    "description": "Run recovery in silent mode"
                },
                "max_recovery_attempts": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3,
                    "description": "Maximum recovery attempts"
                },
                "recovery_log": {
                    "type": "string",
                    "default": "logs/recovery.log",
                    "description": "Path to recovery log file"
                },
                "notify_on_recovery": {
                    "type": "boolean",
                    "default": True,
                    "description": "Notify user on recovery actions"
                }
            }
        },
        "banned_words": {
            "type": "array",
            "description": "List of regex patterns for banned words",
            "items": {
                "type": "string"
            },
            "default": []
        },
        "pronunciation_fixes": {
            "type": "object",
            "description": "Word pronunciation corrections",
            "additionalProperties": {
                "type": "string"
            },
            "default": {}
        },
        "fandom_tags": {
            "type": "object",
            "description": "Fandom-specific tags for categorization",
            "additionalProperties": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "default": {}
        }
    },
    "definitions": {
        "quality_preset": {
            "type": "object",
            "required": ["height", "crf", "preset"],
            "properties": {
                "height": {
                    "type": "integer",
                    "minimum": 240,
                    "maximum": 2160,
                    "description": "Video height in pixels"
                },
                "crf": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 51,
                    "description": "Constant Rate Factor (lower = better quality)"
                },
                "preset": {
                    "type": "string",
                    "enum": ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
                    "description": "FFmpeg encoding preset"
                }
            }
        }
    }
}
