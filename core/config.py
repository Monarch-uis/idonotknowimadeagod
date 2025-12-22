"""
Configuration management module
Handles loading, validation, and default settings
"""
import os
import json
import copy
import re
import logging
from typing import TypedDict, List, Dict, Any, Union, Optional

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logging.warning("jsonschema not installed - schema validation disabled")


# ---------------------------
# CONSTANTS
# ---------------------------
INPUT_ZONE = "_NEW_EPUBS_HERE"
HISTORY_DIR = os.path.join(os.path.expanduser("~"), ".epub_project_history")
HISTORY_FILE = os.path.join(HISTORY_DIR, "global_database.json")
CONFIG_FILE = "config.json"

MASTER_NOVEL_DIR = "Novels"
ACTIVE_NOVELS_DIR = os.path.join(MASTER_NOVEL_DIR, "Active Novels")
ARCHIVED_NOVELS_DIR = os.path.join(MASTER_NOVEL_DIR, "Archived Novels")

# Module logger
logger = logging.getLogger(__name__)

# [Rest of the config.py file content - keeping it identical]
# Type definitions and default config remain the same...

class AudioSettings(TypedDict):
    voice: str
    background_volume: float
    background_music_path: str
    tts_speed_default: str
    max_concurrent_tts: int
    retry_attempts: int
    retry_delay: int
    edge_tts_request_delay: float
    min_audio_size_mb: float
    piper_model_path: str
    piper_speaker_id: int
    piper_noise_scale: float
    piper_length_scale: float
    enable_audio_crossfade: bool

class SystemLimits(TypedDict):
    max_batch_size: int
    ram_warning_threshold_mb: int
    enable_memory_monitoring: bool
    min_disk_space_gb: float
    max_chapter_length_chars: int

class Branding(TypedDict):
    intro: str
    outro: str
    tagline: str

class VideoPreset(TypedDict):
    height: int
    crf: int
    preset: str

class VideoSettings(TypedDict):
    enable_text_overlay: bool
    enable_chapter_markers: bool
    enable_subtitles: bool
    embed_subtitles: bool
    use_advanced_renderer: bool
    subtitle_max_chars: int
    subtitle_reading_speed_wps: float
    caption_model_size: str
    caption_compute_type: str
    caption_language: Optional[str]
    caption_fragment_max_duration: float
    caption_fragment_max_words: int
    preview_fps: int
    caption_style: Dict[str, Any]
    default_effects: List[Dict[str, Any]]
    text_overlay_font_size: int
    text_overlay_bottom_margin: int
    current_quality_preset: str
    quality_presets: Dict[str, VideoPreset]
    enable_dynamic_background: bool
    background_animation_style: str
    rendering_preset: str

class CaptionStyle(TypedDict):
    preset: str
    font: str
    font_size: int
    bold: bool
    color: str
    stroke_color: str
    stroke_width: int
    shadow: int
    alignment: int
    margin_v_percent: float
    margin_h_percent: float
    responsive_scaling: bool
    min_font_size: int
    max_font_size: int
    outline_thickness: int
    shadow_depth: int


class CleanupSettings(TypedDict):
    auto_cleanup_on_startup: bool
    max_temp_age_days: int
    min_size_for_cleanup_mb: int
    warn_threshold_mb: int

class RecoverySettings(TypedDict):
    enable_auto_recovery: bool
    auto_approve_safe_fixes: bool
    silent_mode: bool
    max_recovery_attempts: int
    recovery_log: str
    notify_on_recovery: bool

class ConfigType(TypedDict):
    audio_settings: AudioSettings
    system_limits: SystemLimits
    branding: Branding
    video_settings: VideoSettings
    cleanup_settings: CleanupSettings
    recovery_settings: RecoverySettings
    banned_words: List[str]
    pronunciation_fixes: Dict[str, str]
    fandom_tags: Dict[str, List[str]]

DEFAULT_CONFIG: ConfigType = {
    "audio_settings": {
        "voice": "en-US-GuyNeural",
        "background_volume": 0.10,
        "background_music_path": "background.mp3",
        "tts_speed_default": "+0%",
        "max_concurrent_tts": 5,  # Reduced from 10 for safety
        "retry_attempts": 5,      # Increased from 3
        "retry_delay": 5,         # Increased from 2
        "edge_tts_request_delay": 1.0, # Increased from 0.8
        "min_audio_size_mb": 0.5,
        "piper_model_path": "en_US-lessac-medium.onnx",
        "piper_speaker_id": 0,
        "piper_noise_scale": 0.667,
        "piper_length_scale": 1.0,
        "enable_audio_crossfade": True
    },
    "system_limits": {
        "max_batch_size": 50,
        "ram_warning_threshold_mb": 1500,
        "enable_memory_monitoring": True,
        "min_disk_space_gb": 2.0,
        "max_chapter_length_chars": 50000
    }, 
    "branding": {
        "intro": "Yo legends! Welcome to Fanfiction Legend! Grab your headphones, because today's story is about to hit different.",
        "outro": "Alright legends, that's it for today! Like, subscribe, and I'll meet you in the next audiobook.",
        "tagline": "For fans… by a legend."
    },
    "video_settings": {
        "enable_text_overlay": True,
        "enable_chapter_markers": True,
        "enable_subtitles": True,
        "embed_subtitles": True,
        "use_advanced_renderer": False,
        "subtitle_max_chars": 60,
        "subtitle_reading_speed_wps": 2.5,
        "caption_model_size": "small",
        "caption_compute_type": "float16",
        "caption_language": None,
        "caption_fragment_max_duration": 3.0,
        "caption_fragment_max_words": 12,
        "preview_fps": 30,
        "caption_style": {
            "preset": "Modern",
            "font": "Montserrat-Bold",
            "font_size": 70,
            "bold": True,
            "color": "#FFFFFF",
            "stroke_color": "#000000",
            "stroke_width": 5,
            "shadow": 2,
            "alignment": 2,
            "margin_v_percent": 7.0,
            "margin_h_percent": 2.5,
            "responsive_scaling": True,
            "min_font_size": 45,
            "max_font_size": 90,
            "outline_thickness": 5,
            "shadow_depth": 2
        },
        "default_effects": [],
        "text_overlay_font_size": 36,
        "text_overlay_bottom_margin": 40,
        "current_quality_preset": "Balanced",
        "quality_presets": {
            "Fast": {"height": 480, "crf": 30, "preset": "ultrafast"},
            "Balanced": {"height": 720, "crf": 23, "preset": "medium"},
            "High": {"height": 1080, "crf": 20, "preset": "slow"}
        },
        "enable_dynamic_background": True,
        "background_animation_style": "pulse",
        "rendering_preset": "ultrafast"
    },
    "cleanup_settings": {
        "auto_cleanup_on_startup": True,
        "max_temp_age_days": 7,
        "min_size_for_cleanup_mb": 500,
        "warn_threshold_mb": 1000
    },
    "recovery_settings": {
        "enable_auto_recovery": True,
        "auto_approve_safe_fixes": False,
        "silent_mode": False,
        "max_recovery_attempts": 3,
        "recovery_log": "recovery.log",
        "notify_on_recovery": True
    },
    "banned_words": [
        r"\bfuck\w*", r"\bshit\w*", r"\bbitch\w*", r"\bcunt\w*",
        r"\bwhore\w*", r"\brape\w*", r"\bnigg\w*", r"\bfagg\w*",
        r"\bretard\w*", r"\bslut\w*", r"\bpussy\w*", r"\bdick\w*",
        r"\bcock\w*", r"\bsex\b", r"\bmotherfucker\w*"
    ],
    "pronunciation_fixes": {
        "Sasuke": "Soss-kay", "Uchiha": "Oo-chee-ha", "Naruto": "Na-roo-toe",
        "Hokage": "Ho-kah-gay", "Kakashi": "Kah-kah-she", "Sharingan": "Shar-in-gone",
        "Chakra": "Cha-kra", "Jutsu": "Joot-soo", "Konoha": "Ko-no-ha",
        "Akatsuki": "A-kot-ski", "Luffy": "Loo-fee", "Zoro": "Zoh-row",
        "Sanji": "Sahn-jee", "Nakama": "Nah-kah-mah", "Saiyan": "Sigh-an",
        "Goku": "Go-koo", "Vegeta": "Va-gee-ta", "Kamehameha": "Ka-may-ha-may-ha",
        "Hermione": "Her-my-oh-nee", "Voldemort": "Vol-de-more",
        "Gryffindor": "Griff-in-door", "Slytherin": "Slith-er-in",
        "Isekai": "Ee-seh-kai", "Cultivation": "Cul-ti-vay-shun", "Mana": "Mah-nah"
    },
    "fandom_tags": {
        "one piece": ["#OnePiece", "#Luffy", "#Zoro", "#Sanji", "#StrawHatPirates"],
        "naruto": ["#Naruto", "#NarutoShippuden", "#Konoha", "#Ninja", "#Anime"],
        "fairy tail": ["#FairyTail", "#Natsu", "#Lucy", "#DragonSlayer", "#Anime"],
        "dragon ball": ["#DragonBall", "#DBZ", "#DBS", "#Goku", "#Vegeta"],
        "pokemon": ["#Pokemon", "#Trainer", "#Pikachu", "#Nintendo"],
        "marvel": ["#Marvel", "#MCU", "#Avengers", "#Superhero"],
        "dc": ["#DCComics", "#JusticeLeague", "#Batman", "#Superman"],
        "harry potter": ["#HarryPotter", "#Hogwarts", "#WizardingWorld"],
        "bleach": ["#Bleach", "#Ichigo", "#SoulSociety", "#Shinigami"],
        "system": ["#System", "#LevelUp", "#Gamer", "#LitRPG"],
        "cultivation": ["#Cultivation", "#Xianxia", "#Wuxia"],
        "reincarnat": ["#Reincarnation", "#Isekai"],
        "transmigrat": ["#Transmigration", "#Isekai"],
        "villain": ["#Villain", "#AntiHero"],
        "harem": ["#Harem", "#Romance"],
        "overpowered": ["#OpMc", "#GodLike"]
    }
}

def validate_config_schema(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate configuration against JSON schema
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not JSONSCHEMA_AVAILABLE:
        return True, None
    
    try:
        from core.config_schema import CONFIG_SCHEMA
        validate(instance=config, schema=CONFIG_SCHEMA)
        return True, None
    except ValidationError as e:
        # Format detailed error message
        error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        error_msg = f"Config validation error at '{error_path}': {e.message}"
        
        if e.validator == 'type':
            error_msg += f"\n  Expected type: {e.validator_value}"
            error_msg += f"\n  Actual value: {e.instance}"
        elif e.validator in ['minimum', 'maximum']:
            error_msg += f"\n  Constraint: {e.validator} = {e.validator_value}"
            error_msg += f"\n  Actual value: {e.instance}"
        elif e.validator == 'pattern':
            error_msg += f"\n  Expected pattern: {e.validator_value}"
            error_msg += f"\n  Actual value: {e.instance}"
        
        return False, error_msg
    except Exception as e:
        return False, f"Schema validation failed: {str(e)}"

def validate_config(config):

    """Validate and sanitize configuration"""
    validated = copy.deepcopy(DEFAULT_CONFIG)
    
    # Audio settings
    if "audio_settings" in config:
        audio = config["audio_settings"]
        if isinstance(audio.get("background_volume"), (int, float)):
            vol = max(0, min(1, audio["background_volume"]))
            validated["audio_settings"]["background_volume"] = vol
        if isinstance(audio.get("tts_speed_default"), str):
            validated["audio_settings"]["tts_speed_default"] = audio["tts_speed_default"]
        if audio.get("voice"):
            validated["audio_settings"]["voice"] = audio["voice"]
        if isinstance(audio.get("max_concurrent_tts"), int):
            validated["audio_settings"]["max_concurrent_tts"] = max(1, min(20, audio["max_concurrent_tts"]))
        if isinstance(audio.get("retry_attempts"), int):
            validated["audio_settings"]["retry_attempts"] = max(1, min(10, audio["retry_attempts"]))
        if isinstance(audio.get("retry_delay"), (int, float)):
            validated["audio_settings"]["retry_delay"] = max(1, min(30, audio["retry_delay"]))
        if isinstance(audio.get("edge_tts_request_delay"), (int, float)):
            validated["audio_settings"]["edge_tts_request_delay"] = max(0.1, min(5.0, audio["edge_tts_request_delay"]))
        if isinstance(audio.get("min_audio_size_mb"), (int, float)):
            validated["audio_settings"]["min_audio_size_mb"] = max(0.1, audio["min_audio_size_mb"])
        if isinstance(audio.get("background_music_path"), str):
            validated["audio_settings"]["background_music_path"] = audio["background_music_path"]
        if isinstance(audio.get("enable_audio_crossfade"), bool):
            validated["audio_settings"]["enable_audio_crossfade"] = audio["enable_audio_crossfade"]
    
    # System limits
    if "system_limits" in config:
        limits = config["system_limits"]
        if isinstance(limits.get("max_batch_size"), int):
            validated["system_limits"]["max_batch_size"] = max(1, min(200, limits["max_batch_size"]))
        if isinstance(limits.get("ram_warning_threshold_mb"), (int, float)):
            validated["system_limits"]["ram_warning_threshold_mb"] = max(100, limits["ram_warning_threshold_mb"])
        if isinstance(limits.get("enable_memory_monitoring"), bool):
            validated["system_limits"]["enable_memory_monitoring"] = limits["enable_memory_monitoring"]
    
    # Cleanup settings
    if "cleanup_settings" in config:
        cleanup = config["cleanup_settings"]
        if isinstance(cleanup.get("auto_cleanup_on_startup"), bool):
            validated["cleanup_settings"]["auto_cleanup_on_startup"] = cleanup["auto_cleanup_on_startup"]
        if isinstance(cleanup.get("max_temp_age_days"), (int, float)):
            validated["cleanup_settings"]["max_temp_age_days"] = max(1, cleanup["max_temp_age_days"])
        if isinstance(cleanup.get("min_size_for_cleanup_mb"), (int, float)):
            validated["cleanup_settings"]["min_size_for_cleanup_mb"] = max(0, cleanup["min_size_for_cleanup_mb"])
        if isinstance(cleanup.get("warn_threshold_mb"), (int, float)):
            validated["cleanup_settings"]["warn_threshold_mb"] = max(0, cleanup["warn_threshold_mb"])
    
    # Banned words
    if "banned_words" in config and isinstance(config["banned_words"], list):
        valid_patterns = []
        for pattern in config["banned_words"]:
            try:
                re.compile(pattern)
                valid_patterns.append(pattern)
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
        validated["banned_words"] = valid_patterns
    
    # Pronunciation fixes
    if "pronunciation_fixes" in config and isinstance(config["pronunciation_fixes"], dict):
        validated["pronunciation_fixes"] = {
            k: v for k, v in config["pronunciation_fixes"].items()
            if isinstance(k, str) and isinstance(v, str)
        }
    
    # Branding
    if "branding" in config:
        branding = config["branding"]
        for key in ["intro", "outro", "tagline"]:
            if isinstance(branding.get(key), str):
                validated["branding"][key] = branding[key]
    
    # Video settings
    if "video_settings" in config:
        video = config["video_settings"]
        if isinstance(video.get("enable_text_overlay"), bool):
            validated["video_settings"]["enable_text_overlay"] = video["enable_text_overlay"]
        if isinstance(video.get("enable_chapter_markers"), bool):
            validated["video_settings"]["enable_chapter_markers"] = video["enable_chapter_markers"]
        if isinstance(video.get("enable_subtitles"), bool):
            validated["video_settings"]["enable_subtitles"] = video["enable_subtitles"]
        if isinstance(video.get("embed_subtitles"), bool):
            validated["video_settings"]["embed_subtitles"] = video["embed_subtitles"]
        if isinstance(video.get("use_advanced_renderer"), bool):
            validated["video_settings"]["use_advanced_renderer"] = video["use_advanced_renderer"]
        if isinstance(video.get("subtitle_max_chars"), int):
            validated["video_settings"]["subtitle_max_chars"] = max(20, min(140, video["subtitle_max_chars"]))
        if isinstance(video.get("subtitle_reading_speed_wps"), (int, float)):
            validated["video_settings"]["subtitle_reading_speed_wps"] = max(0.5, min(10.0, float(video["subtitle_reading_speed_wps"])) )
        if isinstance(video.get("caption_model_size"), str):
            validated["video_settings"]["caption_model_size"] = video["caption_model_size"]
        if isinstance(video.get("caption_compute_type"), str):
            validated["video_settings"]["caption_compute_type"] = video["caption_compute_type"]
        if isinstance(video.get("caption_language"), str) or video.get("caption_language") is None:
            validated["video_settings"]["caption_language"] = video.get("caption_language")
        if isinstance(video.get("caption_fragment_max_duration"), (int, float)):
            validated["video_settings"]["caption_fragment_max_duration"] = max(0.5, float(video["caption_fragment_max_duration"]))
        if isinstance(video.get("caption_fragment_max_words"), int):
            validated["video_settings"]["caption_fragment_max_words"] = max(1, video["caption_fragment_max_words"])
        if isinstance(video.get("preview_fps"), int):
            validated["video_settings"]["preview_fps"] = max(12, min(120, video["preview_fps"]))
        if isinstance(video.get("caption_style"), dict):
            # Validate nested caption style fields
            style = video["caption_style"]
            def_style = validated["video_settings"]["caption_style"]
            
            # Helper to validate and set if type matches
            for key, val in style.items():
                if key in def_style and isinstance(val, type(def_style[key])):
                     validated["video_settings"]["caption_style"][key] = val
                # Handle special cases (int/float compatibility)
                if key in ["margin_v_percent", "margin_h_percent"] and isinstance(val, (int, float)):
                    validated["video_settings"]["caption_style"][key] = float(val)
                if key == "bold" and isinstance(val, bool):
                    validated["video_settings"]["caption_style"][key] = val

        if isinstance(video.get("default_effects"), list):
            validated["video_settings"]["default_effects"] = [
                item for item in video["default_effects"] if isinstance(item, dict)
            ]
        if isinstance(video.get("text_overlay_font_size"), int):
            validated["video_settings"]["text_overlay_font_size"] = max(10, min(100, video["text_overlay_font_size"]))
        if isinstance(video.get("text_overlay_bottom_margin"), int):
            validated["video_settings"]["text_overlay_bottom_margin"] = max(0, min(200, video["text_overlay_bottom_margin"]))
        if isinstance(video.get("current_quality_preset"), str):
            validated["video_settings"]["current_quality_preset"] = video["current_quality_preset"]
        if isinstance(video.get("quality_presets"), dict):
             validated["video_settings"]["quality_presets"] = video["quality_presets"]
    
    # Fandom tags
    if "fandom_tags" in config and isinstance(config["fandom_tags"], dict):
        validated["fandom_tags"] = {
            k: [tag for tag in v if isinstance(tag, str)]
            for k, v in config["fandom_tags"].items()
            if isinstance(k, str) and isinstance(v, list)
        }
    
    # Dynamic background and rendering settings
    if "video_settings" in config:
        video = config["video_settings"]
        if isinstance(video.get("enable_dynamic_background"), bool):
            validated["video_settings"]["enable_dynamic_background"] = video["enable_dynamic_background"]
        if isinstance(video.get("background_animation_style"), str):
            validated["video_settings"]["background_animation_style"] = video["background_animation_style"]
        if isinstance(video.get("rendering_preset"), str):
            validated["video_settings"]["rendering_preset"] = video["rendering_preset"]
    
    return validated

def load_config():
    """Load and validate configuration"""
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            logger.info("✅ Created default config.json")
            return DEFAULT_CONFIG
        except (OSError, IOError) as e:
            logger.error(f"Config creation failed: {e}")
            return DEFAULT_CONFIG
    else:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            # Validate against JSON schema first
            is_valid, error_msg = validate_config_schema(loaded)
            if not is_valid:
                logger.error(f"❌ {error_msg}")
                logger.error("Using default configuration instead")
                logger.info("Fix your config.json or delete it to regenerate")
                return DEFAULT_CONFIG
            
            # Then apply additional validation and defaults
            validated = validate_config(loaded)
            logger.info("✅ Configuration loaded and validated successfully")
            return validated
        except json.JSONDecodeError as e:
            logger.error(f"Config JSON invalid: {e}")
            return DEFAULT_CONFIG
        except (OSError, IOError) as e:
            logger.error(f"Config load failed: {e}")
            return DEFAULT_CONFIG

def save_config(config: Optional[Dict[str, Any]] = None):
    """Save configuration to config.json"""
    logger = logging.getLogger(__name__)
    to_save = config or CONFIG
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4)
        logger.info(f"✅ Configuration saved to {CONFIG_FILE}")
        return True
    except (OSError, IOError) as e:
        logger.error(f"Config save failed: {e}")
        return False

# Global config instance
CONFIG = load_config()
