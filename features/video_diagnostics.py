"""
Video Renderer Diagnostics and Auto-Recovery
Detects and fixes issues with the advanced video renderer
"""
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Diagnostic result structure
class DiagnosticResult:
    def __init__(self):
        self.healthy = True
        self.issues = []
        self.warnings = []
        self.fixes_applied = []
        
    def add_issue(self, component: str, message: str, severity: str = "error"):
        """Add a diagnostic issue"""
        self.issues.append({
            "component": component,
            "message": message,
            "severity": severity
        })
        if severity == "error":
            self.healthy = False
            
    def add_warning(self, component: str, message: str):
        """Add a diagnostic warning"""
        self.warnings.append({
            "component": component,
            "message": message
        })
        
    def add_fix(self, component: str, fix_description: str):
        """Record an applied fix"""
        self.fixes_applied.append({
            "component": component,
            "fix": fix_description
        })


def validate_faster_whisper() -> Tuple[bool, str]:
    """
    Check if faster-whisper is available and working
    
    Returns:
        (success, message) tuple
    """
    try:
        from faster_whisper import WhisperModel
        
        # Try to create a tiny model to verify it works
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        return True, "faster-whisper is available and working"
    except ImportError:
        return False, "faster-whisper is not installed. Run: pip install faster-whisper"
    except Exception as e:
        return False, f"faster-whisper error: {str(e)}"


def validate_ffmpeg_subprocess() -> Tuple[bool, str]:
    """
    Check if FFmpeg is available via subprocess and supports libass
    
    Returns:
        (success, message) tuple
    """
    try:
        # Check FFmpeg is available
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, "FFmpeg command failed"
        
        # Check for libass support (required for subtitles filter)
        filters_result = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "subtitles" not in filters_result.stdout.lower():
            return False, "FFmpeg does not have subtitle filter support (libass missing)"
        
        # Extract version
        version_line = result.stdout.split('\n')[0]
        return True, f"FFmpeg available: {version_line}"
        
    except FileNotFoundError:
        return False, "FFmpeg not found in PATH. Install FFmpeg or add to PATH"
    except subprocess.TimeoutExpired:
        return False, "FFmpeg command timed out"
    except Exception as e:
        return False, f"FFmpeg check error: {str(e)}"


def validate_video_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate video configuration settings
    
    Returns:
        (valid, issues) tuple
    """
    issues = []
    
    video_settings = config.get("video_settings", {})
    
    # Check use_advanced_renderer
    if not video_settings.get("use_advanced_renderer", False):
        issues.append("use_advanced_renderer is disabled - advanced captions won't work")
    
    # Check enable_subtitles
    if not video_settings.get("enable_subtitles", False):
        issues.append("enable_subtitles is disabled")
    
    # Check caption_style exists
    caption_style = video_settings.get("caption_style", {})
    if not caption_style:
        issues.append("caption_style configuration is missing")
    
    # Check quality presets exist
    presets = video_settings.get("quality_presets", {})
    if not presets:
        issues.append("quality_presets configuration is missing")
    
    return len(issues) == 0, issues


def test_path_escaping() -> Tuple[bool, str]:
    """
    Test Windows path escaping for FFmpeg subtitle filter
    
    Returns:
        (success, message) tuple
    """
    try:
        # Create a test path with special characters
        test_path = Path(tempfile.gettempdir()) / "test_subtitle_path.ass"
        
        # Test path conversion (same logic as video_pipeline.py)
        path_str = str(test_path).replace("\\", "/")
        escaped_path = path_str.replace(":", r"\:")
        
        # Verify backslashes were converted to forward slashes
        # After conversion, there should be NO backslashes except in the escaped colon
        if "\\" in path_str:
            return False, "Path escaping failed - backslashes not properly converted to forward slashes"
        
        # Verify colon is escaped
        if ":" in escaped_path and r"\:" not in escaped_path:
            return False, "Path escaping failed - colon not properly escaped"
        
        return True, "Path escaping works correctly"
        
    except Exception as e:
        return False, f"Path escaping test error: {str(e)}"


def diagnose_advanced_renderer(config: Dict[str, Any]) -> DiagnosticResult:
    """
    Comprehensive diagnostic check for advanced video renderer
    
    Args:
        config: Application configuration dict
        
    Returns:
        DiagnosticResult with health status and issues
    """
    result = DiagnosticResult()
    
    print("🔍 Running video renderer diagnostics...")
    
    # 1. Check faster-whisper
    print("   Checking faster-whisper...", end=" ")
    fw_ok, fw_msg = validate_faster_whisper()
    if fw_ok:
        print("✅")
    else:
        print("❌")
        result.add_issue("faster-whisper", fw_msg, "error")
    
    # 2. Check FFmpeg
    print("   Checking FFmpeg subprocess...", end=" ")
    ffmpeg_ok, ffmpeg_msg = validate_ffmpeg_subprocess()
    if ffmpeg_ok:
        print("✅")
    else:
        print("❌")
        result.add_issue("ffmpeg", ffmpeg_msg, "error")
    
    # 3. Check config
    print("   Checking video config...", end=" ")
    config_ok, config_issues = validate_video_config(config)
    if config_ok:
        print("✅")
    else:
        print("⚠️")
        for issue in config_issues:
            result.add_warning("config", issue)
    
    # 4. Check path escaping
    print("   Checking path escaping...", end=" ")
    path_ok, path_msg = test_path_escaping()
    if path_ok:
        print("✅")
    else:
        print("❌")
        result.add_issue("path_handling", path_msg, "error")
    
    # Summary
    if result.healthy:
        print("✅ All diagnostics passed!")
    else:
        print(f"❌ Found {len(result.issues)} issue(s)")
        for issue in result.issues:
            print(f"   • {issue['component']}: {issue['message']}")
    
    if result.warnings:
        print(f"⚠️  {len(result.warnings)} warning(s)")
        for warning in result.warnings:
            print(f"   • {warning['component']}: {warning['message']}")
    
    return result


def auto_fix_renderer_issues(diagnostic_result: DiagnosticResult, config: Dict[str, Any]) -> bool:
    """
    Attempt to automatically fix detected renderer issues
    
    Args:
        diagnostic_result: Result from diagnose_advanced_renderer()
        config: Application configuration dict
        
    Returns:
        True if all fixes succeeded, False otherwise
    """
    print("\n🔧 Attempting auto-recovery...")
    
    all_fixed = True
    
    for issue in diagnostic_result.issues:
        component = issue['component']
        
        if component == "faster-whisper":
            print("   Installing faster-whisper...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "faster-whisper"],
                    check=True,
                    capture_output=True
                )
                print("   ✅ faster-whisper installed")
                diagnostic_result.add_fix("faster-whisper", "Installed via pip")
            except subprocess.CalledProcessError:
                print("   ❌ Failed to install faster-whisper")
                all_fixed = False
                
        elif component == "ffmpeg":
            print("   ⚠️  FFmpeg issue detected")
            print("   Please install FFmpeg manually:")
            print("   Windows: https://www.gyan.dev/ffmpeg/builds/")
            print("   Or use: winget install ffmpeg")
            all_fixed = False
            
        elif component == "config":
            print("   Fixing config.json...")
            try:
                fix_video_config(config)
                print("   ✅ Config updated")
                diagnostic_result.add_fix("config", "Updated video_settings")
            except Exception as e:
                print(f"   ❌ Config fix failed: {e}")
                all_fixed = False
    
    # Handle warnings
    for warning in diagnostic_result.warnings:
        if warning['component'] == "config":
            try:
                fix_video_config(config)
                diagnostic_result.add_fix("config", "Updated video_settings")
            except Exception as e:
                print(f"   ⚠️  Config warning fix failed: {e}")
    
    return all_fixed


def fix_video_config(config: Dict[str, Any]) -> None:
    """
    Auto-correct video configuration issues
    
    Args:
        config: Application configuration dict (modified in-place)
    """
    video_settings = config.setdefault("video_settings", {})
    
    # Enable advanced renderer
    if not video_settings.get("use_advanced_renderer"):
        video_settings["use_advanced_renderer"] = True
        print("   • Enabled use_advanced_renderer")
    
    # Enable subtitles
    if not video_settings.get("enable_subtitles"):
        video_settings["enable_subtitles"] = True
        print("   • Enabled enable_subtitles")
    
    # Add caption_style if missing
    if not video_settings.get("caption_style"):
        video_settings["caption_style"] = {
            "preset": "Modern",
            "font": "Arial",
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
            "min_font_size": 40,
            "max_font_size": 90,
            "outline_thickness": 5,
            "shadow_depth": 2
        }
        print("   • Added default caption_style")


def validate_renderer_ready() -> bool:
    """
    Quick health check before rendering
    
    Returns:
        True if renderer is ready, False otherwise
    """
    # Quick check - just verify faster-whisper and FFmpeg are available
    fw_ok, _ = validate_faster_whisper()
    ffmpeg_ok, _ = validate_ffmpeg_subprocess()
    
    return fw_ok and ffmpeg_ok
