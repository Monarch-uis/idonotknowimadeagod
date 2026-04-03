"""
System Validator - Comprehensive system validation and health checks
Merged from: health_check.py + system_check.py + system_validator.py

Validates dependencies, syntax, imports, and component health
Includes pre-flight disk space checks
"""
import sys
import os
import py_compile
import importlib
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from core.utils import CP

# ==========================================
# SYSTEM ENVIRONMENT VALIDATION
# ==========================================
class SystemValidator:
    """Validates system dependencies and tools"""
    
    def __init__(self):
        self.results = {}
    
    def check_disk_space(self, min_gb: float = 2.0) -> Tuple[bool, str]:
        """Check available disk space
        
        Args:
            min_gb: Minimum required free space in GB (default: 2.0)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get disk usage for current working directory
            total, used, free = shutil.disk_usage(os.getcwd())
            free_gb = free / (1024 ** 3)
            
            if free_gb >= min_gb:
                return True, f"Disk space OK: {free_gb:.2f} GB free (minimum: {min_gb} GB)"
            else:
                return False, f"Low disk space: {free_gb:.2f} GB free (minimum: {min_gb} GB required)"
        except Exception as e:
            return False, f"Disk space check failed: {str(e)}"
    
    def check_ffmpeg(self) -> Tuple[bool, str]:
        """Check if FFmpeg is available and working"""
        try:
            from imageio_ffmpeg import get_ffmpeg_exe
            ffmpeg_path = get_ffmpeg_exe()
            
            # Test FFmpeg execution
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return True, f"FFmpeg found: {ffmpeg_path}"
            else:
                return False, "FFmpeg not responding"
        except ImportError:
            return False, "imageio-ffmpeg not installed"
        except Exception as e:
            return False, f"FFmpeg error: {str(e)}"
    
    def check_tts_engines(self) -> Dict[str, Tuple[bool, str]]:
        """Check availability of TTS engines"""
        results = {}
        
        # Check Edge-TTS
        try:
            import edge_tts
            results['edge'] = (True, "Edge-TTS available")
        except ImportError:
            results['edge'] = (False, "Edge-TTS not installed (pip install edge-tts)")
        
        # Check pyttsx3
        try:
            import pyttsx3
            try:
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                if voices:
                    results['pyttsx3'] = (True, f"pyttsx3 available ({len(voices)} voices)")
                else:
                    results['pyttsx3'] = (False, "pyttsx3 installed but no voices detected")
            except Exception as e:
                results['pyttsx3'] = (False, f"pyttsx3 init failed: {e}")
        except ImportError:
            results['pyttsx3'] = (False, "pyttsx3 not installed")
        
        # Check Piper
        piper_locs = [
            os.path.join("piper", "piper.exe"),
            os.path.join("piper", "piper"),
            "piper"
        ]
        piper_found = False
        piper_path = ""
        
        for p in piper_locs:
            try:
                subprocess.run([p, '--version'], capture_output=True, timeout=2)
                piper_found = True
                piper_path = p
                break
            except (FileNotFoundError, PermissionError, Exception):
                continue

        if piper_found:
            results['piper'] = (True, f"Piper found: {piper_path}")
        else:
            results['piper'] = (False, "Piper executable not found")
        
        return results
    
    def check_python_libraries(self) -> Dict[str, Tuple[bool, str]]:
        """Check required Python libraries"""
        required = {
            'ebooklib': 'EPUB parsing',
            'bs4': 'HTML parsing (beautifulsoup4)',
            'moviepy': 'Video creation',
            'PIL': 'Image processing (Pillow)'
        }
        
        results = {}
        for lib, purpose in required.items():
            try:
                importlib.import_module(lib)
                results[lib] = (True, f"{purpose} - OK")
            except ImportError:
                results[lib] = (False, f"{purpose} - MISSING")
        return results
    
    def suggest_fixes(self):
        """Suggest fixes for detected issues"""
        if not self.results:
            return
        
        suggestions = []
        
        # FFmpeg
        if not self.results.get('ffmpeg'):
            suggestions.append("Install FFmpeg: pip install imageio-ffmpeg")
        
        # TTS
        for engine, (ok, msg) in self.results.get('tts', {}).items():
            if not ok:
                if engine == 'edge':
                    suggestions.append("Install Edge-TTS: pip install edge-tts")
                elif engine == 'pyttsx3':
                    suggestions.append("Install pyttsx3: pip install pyttsx3")
                elif engine == 'piper':
                    suggestions.append("Download Piper from: https://github.com/rhasspy/piper/releases")
        
        # Libraries
        for lib, (ok, msg) in self.results.get('libraries', {}).items():
            if not ok:
                suggestions.append(f"Install {lib}: pip install {lib}")
        
        if suggestions:
            print(CP("\n💡 Suggested Fixes:", 'yellow'))
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
            print()

# ==========================================
# CODEBASE INTEGRITY VALIDATION
# ==========================================
class CodebaseIntegrity:
    """Checks the integrity of the project code"""
    
    CORE_MODULES = [
        "core.config",
        "features.chapter_merger",
        "features.queue_manager",
        "features.memory_manager",
        "features.checkpoint_manager",
        "epub_project_manager",
        "core.utils",
        "features.auto_recovery",
        "core.tts",
        "core.epub_io",
        "core.ui_manager"
    ]

    def check_syntax(self) -> List[str]:
        """Compile files to check for syntax errors"""
        print("\n[Codebase] 📝 Checking Syntax...")
        errors = []
        # Convert dotted paths to file paths
        files = []
        for m in self.CORE_MODULES:
            path = m.replace(".", os.sep) + ".py"
            files.append(path)
        
        for f in files:
            if not os.path.exists(f):
                print(f"   ⚠️  {f}: MISSING")
                continue
                
            try:
                py_compile.compile(f, doraise=True)
                print(f"   ✅ {f}: OK")
            except py_compile.PyCompileError as e:
                print(f"   ❌ {f}: SYNTAX ERROR")
                errors.append(str(e))
        return errors

    def check_imports(self) -> Tuple[List[str], Dict]:
        """Try importing modules to check for runtime import errors"""
        print("\n[Codebase] 📦 Checking Internal Imports...")
        errors = []
        loaded = {}
        
        for mod in self.CORE_MODULES:
            try:
                m = importlib.import_module(mod)
                loaded[mod] = m
                print(f"   ✅ {mod}: IMPORTED")
            except Exception as e:
                print(f"   ❌ {mod}: FAILED - {e}")
                errors.append(mod)
        
        return errors, loaded

    def check_component_health(self, loaded_modules: Dict) -> List[str]:
        """Verify key components are initialized correctly"""
        print("\n[Codebase] 🩺 Checking Component Health...")
        health_errors = []

        # Config Check
        if "core.config" in loaded_modules:
            c = loaded_modules["core.config"]
            if hasattr(c, "CONFIG") and "video_settings" in c.CONFIG:
                q = c.CONFIG["video_settings"].get("quality_presets")
                if q:
                    print(f"   ✅ Config: OK (Presets: {len(q)})")
                else:
                    print("   ❌ Config: Missing 'quality_presets'")
                    health_errors.append("config_presets")
            else:
                print("   ❌ Config: Malformed structure")
                health_errors.append("config_structure")

        # EPUB Manager Signature Check
        if "epub_project_manager" in loaded_modules:
            epm = loaded_modules["epub_project_manager"]
            import inspect
            if hasattr(epm, "create_video_with_recovery"):
                sig = inspect.signature(epm.create_video_with_recovery)
                if "quality_preset" in sig.parameters:
                    print("   ✅ EPUB Manager: Signature OK")
                else:
                    print("   ❌ EPUB Manager: create_video_with_recovery outdated")
                    health_errors.append("epm_signature")
            else:
                print("   ⚠️  EPUB Manager: create_video_with_recovery not found")

        # Memory Manager Check
        if "features.memory_manager" in loaded_modules:
            try:
                mm = loaded_modules["features.memory_manager"]
                mem = mm.MemoryManager()
                free = mem.get_free_memory_mb()
                print(f"   ✅ Memory Manager: OK ({free} MB free)")
            except Exception as e:
                print(f"   ❌ Memory Manager Failed: {e}")
                health_errors.append("memory_manager")

        return health_errors

# ==========================================
# UNIFIED HEALTH CHECK
# ==========================================
def run_full_health_check(verbose: bool = True) -> bool:
    """
    Run comprehensive system health check
    
    Args:
        verbose: Print detailed output
        
    Returns:
        True if all checks pass, False otherwise
    """
    if verbose:
        print(CP("\n" + "="*60, 'cyan'))
        print(CP("🩺 COMPREHENSIVE SYSTEM HEALTH CHECK", 'cyan'))
        print(CP("="*60, 'cyan'))

    overall_success = True

    # Phase 1: Environment & Tools
    if verbose:
        print("\n" + "-"*30)
        print("PHASE 1: ENVIRONMENT & TOOLS")
        print("-"*30)
    
    validator = SystemValidator()
    
    # Disk Space Check (Pre-flight)
    disk_ok, disk_msg = validator.check_disk_space(min_gb=2.0)
    if verbose:
        print(f"   {'✅' if disk_ok else '❌'} {disk_msg}")
    overall_success &= disk_ok
    
    # FFmpeg
    ffmpeg_ok, ffmpeg_msg = validator.check_ffmpeg()
    if verbose:
        print(f"   {'✅' if ffmpeg_ok else '❌'} {ffmpeg_msg}")
    overall_success &= ffmpeg_ok
    
    # TTS
    tts_results = validator.check_tts_engines()
    if verbose:
        print("\n   TTS Engines:")
        for eng, (ok, msg) in tts_results.items():
            print(f"   {'✅' if ok else '⚠️'} {eng}: {msg}")
    
    # Python Libs
    lib_results = validator.check_python_libraries()
    if verbose:
        print("\n   Libraries:")
        for lib, (ok, msg) in lib_results.items():
            print(f"   {'✅' if ok else '❌'} {lib}: {msg}")
            overall_success &= ok

    validator.results = {
        'ffmpeg': ffmpeg_ok,
        'tts': tts_results,
        'libraries': lib_results
    }

    # Phase 2: Codebase Integrity
    if verbose:
        print("\n" + "-"*30)
        print("PHASE 2: CODEBASE INTEGRITY")
        print("-"*30)
    
    integrity = CodebaseIntegrity()
    
    syntax_errors = integrity.check_syntax()
    if syntax_errors:
        if verbose:
            print("\n   ⛔ SYNTAX ERRORS DETECTED")
        overall_success = False
    
    if not syntax_errors:
        import_errors, loaded = integrity.check_imports()
        if import_errors:
            if verbose:
                print("\n   ⛔ IMPORT ERRORS DETECTED")
            overall_success = False
        else:
            health_errors = integrity.check_component_health(loaded)
            if health_errors:
                if verbose:
                    print("\n   ⛔ COMPONENT HEALTH ISSUES")
                overall_success = False

    if verbose:
        print("\n" + "="*60)
        if overall_success:
            print(CP("✅ SYSTEM HEALTHY - READY TO RUN", 'green'))
        else:
            print(CP("❌ DEGRADED STATE - FIX ISSUES ABOVE", 'red'))
            validator.suggest_fixes()
        print("="*60)

    return overall_success


def run_quick_check() -> bool:
    """Quick validation - just essentials"""
    validator = SystemValidator()
    
    ffmpeg_ok, _ = validator.check_ffmpeg()
    lib_results = validator.check_python_libraries()
    
    all_libs_ok = all(ok for ok, _ in lib_results.values())
    
    return ffmpeg_ok and all_libs_ok


def run_preflight_check() -> bool:
    """Pre-flight check before processing"""
    return run_full_health_check(verbose=True)


if __name__ == "__main__":
    success = run_full_health_check()
    sys.exit(0 if success else 1)
