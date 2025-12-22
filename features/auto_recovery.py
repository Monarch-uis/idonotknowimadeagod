"""
Auto-Recovery Module
Intelligent self-healing system for EPUB automation project
Detects errors, proposes fixes, and applies them with user confirmation
Enhanced with pattern learning, severity classification, and analytics
"""
import os
import sys
import time
import json
import logging
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from collections import defaultdict

from core.utils import CP, logger

# Recovery log
recovery_logger = logging.getLogger('auto_recovery')
recovery_handler = logging.FileHandler('recovery.log')
recovery_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
recovery_logger.addHandler(recovery_handler)
recovery_logger.setLevel(logging.INFO)

# Pattern storage
PATTERN_FILE = "recovery_patterns.json"


class ErrorSeverity:
    """Error severity levels"""
    CRITICAL = "critical"  # Must fix immediately
    WARNING = "warning"    # Should fix but can continue
    INFO = "info"          # Minor issue, can ignore


class ErrorCategory:
    """Error classification categories"""
    TTS_FAILURE = "tts_failure"
    NETWORK_ERROR = "network_error"
    FFMPEG_ERROR = "ffmpeg_error"
    DEPENDENCY_MISSING = "dependency_missing"
    FILE_LOCK = "file_lock"
    PERMISSION_ERROR = "permission_error"
    DISK_SPACE = "disk_space"
    UNKNOWN = "unknown"


class RecoveryStrategy:
    """Defines a recovery strategy for an error"""
    
    def __init__(self, name: str, description: str, fix_function: Callable, safety_level: str = "safe"):
        """
        Args:
            name: Short name of the fix
            description: User-facing description
            fix_function: Function to apply the fix
            safety_level: 'safe' (no data loss) or 'risky' (may affect data)
        """
        self.name = name
        self.description = description
        self.fix_function = fix_function
        self.safety_level = safety_level


class PatternLearner:
    """Learns from error patterns and suggests preemptive fixes"""
    
    def __init__(self):
        self.patterns = self._load_patterns()
        self.session_errors = defaultdict(int)
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load historical error patterns"""
        if os.path.exists(PATTERN_FILE):
            try:
                with open(PATTERN_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {"error_counts": {}, "fix_success_rates": {}, "last_updated": None}
        return {"error_counts": {}, "fix_success_rates": {}, "last_updated": None}
    
    def _save_patterns(self):
        """Save patterns to disk"""
        self.patterns["last_updated"] = datetime.now().isoformat()
        try:
            with open(PATTERN_FILE, 'w') as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            recovery_logger.warning(f"Failed to save patterns: {e}")
    
    def record_error(self, category: str, engine: str = None):
        """Record an error occurrence"""
        key = f"{category}:{engine}" if engine else category
        
        if "error_counts" not in self.patterns:
            self.patterns["error_counts"] = {}
        
        self.patterns["error_counts"][key] = self.patterns["error_counts"].get(key, 0) + 1
        self.session_errors[key] += 1
        self._save_patterns()
    
    def record_fix_result(self, category: str, fix_name: str, success: bool):
        """Record whether a fix worked"""
        key = f"{category}:{fix_name}"
        
        if "fix_success_rates" not in self.patterns:
            self.patterns["fix_success_rates"] = {}
        
        if key not in self.patterns["fix_success_rates"]:
            self.patterns["fix_success_rates"][key] = {"successes": 0, "attempts": 0}
        
        self.patterns["fix_success_rates"][key]["attempts"] += 1
        if success:
            self.patterns["fix_success_rates"][key]["successes"] += 1
        
        self._save_patterns()
    
    def get_frequent_errors(self, threshold: int = 5) -> List[tuple]:
        """Get errors that occur frequently"""
        frequent = []
        for error, count in self.patterns.get("error_counts", {}).items():
            if count >= threshold:
                frequent.append((error, count))
        return sorted(frequent, key=lambda x: x[1], reverse=True)
    
    def suggest_preemptive_fix(self) -> Optional[str]:
        """Suggest preemptive action based on patterns"""
        frequent = self.get_frequent_errors(threshold=10)
        
        if not frequent:
            return None
        
        top_error, count = frequent[0]
        
        if "edge" in top_error.lower() and count > 15:
            return f"💡 Tip: Edge-TTS has failed {count} times. Consider using Piper as default."
        elif "network" in top_error.lower() and count > 10:
            return f"💡 Tip: Network errors detected {count} times. Consider offline mode."
        
        return None
    
    def is_cascading_failure(self, category: str, window: int = 3) -> bool:
        """Detect if we're in a cascading failure (3+ consecutive errors)"""
        return self.session_errors.get(category, 0) >= window


class ErrorDetector:
    """Analyzes exceptions and classifies them"""
    
    @staticmethod
    def classify_error(exception: Exception, context: Dict[str, Any] = None) -> str:
        """
        Classify an exception into an error category
        
        Args:
            exception: The caught exception
            context: Additional context (engine, operation, etc.)
            
        Returns:
            Error category string
        """
        error_msg = str(exception).lower()
        exc_type = type(exception).__name__
        
        # TTS-related errors
        if context and context.get('operation') == 'tts':
            if 'timeout' in error_msg or 'timed out' in error_msg:
                # Distinguish between transient timeout and hard failure (R-02 logic)
                return ErrorCategory.NETWORK_ERROR
            if 'connection' in error_msg or '403' in error_msg or 'rate limit' in error_msg:
                return ErrorCategory.NETWORK_ERROR
            if 'piper' in error_msg and 'not found' in error_msg:
                return ErrorCategory.DEPENDENCY_MISSING
            return ErrorCategory.TTS_FAILURE
        
        # Network errors
        if any(keyword in error_msg for keyword in ['network', 'connection', 'timeout', 'dns', 'unreachable']):
            return ErrorCategory.NETWORK_ERROR
        
        # FFmpeg/video errors
        if 'ffmpeg' in error_msg or 'codec' in error_msg or 'video' in error_msg:
            return ErrorCategory.FFMPEG_ERROR
        
        # File access errors
        if exc_type in ['PermissionError', 'FileNotFoundError']:
            return ErrorCategory.PERMISSION_ERROR
        if 'winerror' in error_msg and '32' in error_msg:  # File in use
            return ErrorCategory.FILE_LOCK
        if 'permission denied' in error_msg or 'access denied' in error_msg:
            return ErrorCategory.PERMISSION_ERROR
        
        # Dependency errors
        if exc_type == 'ModuleNotFoundError' or 'no module named' in error_msg:
            return ErrorCategory.DEPENDENCY_MISSING
        
        # Disk space
        if 'no space' in error_msg or 'disk full' in error_msg:
            return ErrorCategory.DISK_SPACE
        
        return ErrorCategory.UNKNOWN
    
    @staticmethod
    def classify_severity(category: str, context: Dict[str, Any] = None) -> str:
        """
        Classify error severity
        
        Returns:
            ErrorSeverity level (CRITICAL, WARNING, INFO)
        """
        # Critical errors that must be fixed
        if category in [ErrorCategory.TTS_FAILURE, ErrorCategory.FFMPEG_ERROR]:
            return ErrorSeverity.CRITICAL
        
        # Warnings that should be fixed but can continue
        if category in [ErrorCategory.NETWORK_ERROR, ErrorCategory.FILE_LOCK]:
            return ErrorSeverity.WARNING
        
        # Info-level issues that can be ignored
        if category in [ErrorCategory.DEPENDENCY_MISSING, ErrorCategory.PERMISSION_ERROR]:
            return ErrorSeverity.INFO
        
        return ErrorSeverity.WARNING


class AutoRecovery:
    """Main auto-recovery orchestrator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize auto-recovery system
        
        Args:
            config: Configuration dict with recovery settings
        """
        self.config = config or {
            "enable_auto_recovery": True,
            "auto_approve_safe_fixes": False,
            "max_recovery_attempts": 3
        }
        self.recovery_count = 0
        self.detector = ErrorDetector()
        self.pattern_learner = PatternLearner()
        self.strategies = self._load_strategies()
        self.session_history = []  # Track recovery events
        self.MAX_HISTORY = 100     # Cap history to prevent memory leak (R-06)
        self.rollback_stack = []  # Stack for undo/rollback
        self.quality_chain = ['edge', 'piper', 'pyttsx3']  # Quality degradation chain
    
    def _load_strategies(self) -> Dict[str, RecoveryStrategy]:
        """Load all available recovery strategies"""
        return {
            ErrorCategory.TTS_FAILURE: RecoveryStrategy(
                name="TTS Engine Fallback",
                description="Switch to offline TTS engine (Piper or pyttsx3)",
                fix_function=self._fix_tts_fallback,
                safety_level="safe"
            ),
            ErrorCategory.NETWORK_ERROR: RecoveryStrategy(
                name="Network Retry & Fallback",
                description="Retry connection (exp backoff) or switch to offline mode (R-02)",
                fix_function=self._fix_network_resilience,
                safety_level="safe"
            ),
            ErrorCategory.FILE_LOCK: RecoveryStrategy(
                name="Retry with Backoff",
                description="Wait and retry the operation (up to 3 attempts)",
                fix_function=self._fix_file_lock,
                safety_level="safe"
            ),
            ErrorCategory.FFMPEG_ERROR: RecoveryStrategy(
                name="Codec Fallback",
                description="Try alternative video codec or lower quality",
                fix_function=self._fix_ffmpeg,
                safety_level="safe"
            ),
            ErrorCategory.DEPENDENCY_MISSING: RecoveryStrategy(
                name="Installation Guide",
                description="Show installation instructions",
                fix_function=self._fix_missing_dependency,
                safety_level="safe"
            ),
            ErrorCategory.DISK_SPACE: RecoveryStrategy(
                name="Cleanup Temp Files",
                description="Remove temporary files to free space",
                fix_function=self._fix_disk_space,
                safety_level="safe"
            )
        }
    
    def can_fix(self, exception: Exception, context: Dict[str, Any] = None) -> bool:
        """Check if we have a recovery strategy for this error"""
        if not self.config.get("enable_auto_recovery", True):
            return False
        
        category = self.detector.classify_error(exception, context)
        return category in self.strategies and category != ErrorCategory.UNKNOWN
    
    def ask_user_permission(self, exception: Exception, context: Dict[str, Any] = None) -> bool:
        """
        Ask user if they want to apply the fix
        
        Returns:
            True if user approves, False otherwise
        """
        category = self.detector.classify_error(exception, context)
        strategy = self.strategies.get(category)
        
        if not strategy:
            return False
        
        # Get severity for color coding
        severity = self.detector.classify_severity(category, context)
        
        # Silent mode - auto-approve safe fixes
        silent_mode = self.config.get("silent_mode", False)
        if silent_mode and strategy.safety_level == "safe":
            print(CP(f"\n🔇 Silent mode: Auto-applying {strategy.name}", 'cyan'))
            recovery_logger.info(f"Silent mode auto-approved: {strategy.name}")
            return True
        
        # Auto-approve safe fixes if configured
        if self.config.get("auto_approve_safe_fixes") and strategy.safety_level == "safe":
            print(CP(f"\n🔧 Auto-applying safe fix: {strategy.name}", 'cyan'))
            return True
        
        # Severity-based color coding
        severity_colors = {
            ErrorSeverity.CRITICAL: 'red',
            ErrorSeverity.WARNING: 'yellow',
            ErrorSeverity.INFO: 'cyan'
        }
        severity_color = severity_colors.get(severity, 'yellow')
        
        # Ask user
        print("\n" + "=" * 60)
        print(CP(f"🚨 PROBLEM DETECTED [{severity.upper()}]", severity_color))
        print("=" * 60)
        print(f"\n❌ Error: {type(exception).__name__}")
        print(f"   Message: {str(exception)[:100]}")
        print(f"\n💡 Proposed Fix: {strategy.name}")
        print(f"   Description: {strategy.description}")
        print(f"   Safety: {strategy.safety_level.upper()}")
        print(f"   Severity: {severity.upper()}")
        
        choice = input("\n👉 Apply this fix? (y/n, default n): ").strip().lower()
        print("=" * 60)
        
        approved = choice == 'y'
        recovery_logger.info(f"Fix {'approved' if approved else 'rejected'} by user: {strategy.name}")
        return approved
    
    def apply_fix(self, exception: Exception, context: Dict[str, Any] = None) -> Any:
        """
        Apply the recovery strategy
        
        Returns:
            Result of the fix function (could be new engine, retry success, etc.)
        """
        if self.recovery_count >= self.config.get("max_recovery_attempts", 3):
            print(CP(f"\n⚠️  Max recovery attempts ({self.recovery_count}) reached", 'yellow'))
            recovery_logger.warning("Max recovery attempts reached")
            return None
        
        category = self.detector.classify_error(exception, context)
        strategy = self.strategies.get(category)
        
        if not strategy:
            return None
        
        self.recovery_count += 1
        
        try:
            print(CP(f"\n🔧 Applying fix: {strategy.name}...", 'cyan'))
            recovery_logger.info(f"Applying fix: {strategy.name} (attempt {self.recovery_count})")
            
            start_time = time.time()
            result = strategy.fix_function(exception, context)
            fix_time = time.time() - start_time
            
            success = result is not None
            
            # Record in session history with capping (R-06)
            self.session_history.append({
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "fix_name": strategy.name,
                "success": success,
                "duration": fix_time,
                "engine": context.get('engine') if context else None
            })
            if len(self.session_history) > self.MAX_HISTORY:
                self.session_history.pop(0)
            
            # Record in pattern learner
            engine = context.get('engine') if context else None
            self.pattern_learner.record_error(category, engine)
            self.pattern_learner.record_fix_result(category, strategy.name, success)
            
            if result:
                print(CP(f"✅ Fix applied successfully!", 'green'))
                recovery_logger.info(f"Fix successful: {strategy.name}")
            else:
                print(CP(f"⚠️  Fix completed but may need verification", 'yellow'))
                recovery_logger.warning(f"Fix uncertain: {strategy.name}")
            
            return result
            
        except Exception as fix_error:
            print(CP(f"❌ Fix failed: {fix_error}", 'red'))
            recovery_logger.error(f"Fix failed: {strategy.name} - {fix_error}")
            
            # Record failure
            self.session_history.append({
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "fix_name": strategy.name,
                "success": False,
                "error": str(fix_error),
                "engine": context.get('engine') if context else None
            })
            
            return None
    
    def display_recovery_dashboard(self):
        """Display summary of all recovery actions taken in this session"""
        if not self.session_history:
            return
        
        print("\n" + "=" * 60)
        print(CP("📊 RECOVERY DASHBOARD", 'cyan'))
        print("=" * 60)
        
        total_fixes = len(self.session_history)
        successful = sum(1 for h in self.session_history if h.get('success', False))
        failed = total_fixes - successful
        total_time = sum(h.get('duration', 0) for h in self.session_history)
        
        print(f"\n✅ Successful Fixes: {successful}/{total_fixes}")
        print(f"❌ Failed Fixes: {failed}/{total_fixes}")
        print(f"⏱️  Total Recovery Time: {total_time:.1f}s")
        
        # Breakdown by error type
        by_category = defaultdict(int)
        for h in self.session_history:
            if h.get('success'):
                by_category[h['category']] += 1
        
        if by_category:
            print(f"\n📋 Fixes by Type:")
            for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {cat}: {count}")
        
        # Show preemptive suggestions
        suggestion = self.pattern_learner.suggest_preemptive_fix()
        if suggestion:
            print(f"\n{suggestion}")
        
        print("=" * 60 + "\n")
    
    def generate_recovery_report(self, output_file: str = None):
        """Generate markdown report of recovery session"""
        if not self.session_history:
            return
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"recovery_report_{timestamp}.md"
        
        total_fixes = len(self.session_history)
        successful = sum(1 for h in self.session_history if h.get('success', False))
        failed = total_fixes - successful
        total_time = sum(h.get('duration', 0) for h in self.session_history)
        
        # Build report
        report = []
        report.append("# Recovery Session Report\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("---\n")
        
        # Summary
        report.append("## Summary\n")
        report.append(f"- **Total Fixes Applied:** {total_fixes}")
        report.append(f"- **Successful:** {successful} ({successful/total_fixes*100:.1f}%)")
        report.append(f"- **Failed:** {failed} ({failed/total_fixes*100:.1f}%)")
        report.append(f"- **Total Recovery Time:** {total_time:.1f}s\n")
        
        # Timeline
        report.append("## Recovery Timeline\n")
        for i, event in enumerate(self.session_history, 1):
            status_icon = "✅" if event.get('success') else "❌"
            timestamp = event.get('timestamp', 'Unknown')
            fix_name = event.get('fix_name', 'Unknown')
            category = event.get('category', 'Unknown')
            duration = event.get('duration', 0)
            
            report.append(f"{i}. {status_icon} **{fix_name}** ({category}) - {duration:.2f}s")
            report.append(f"   - Time: {timestamp}")
            if event.get('engine'):
                report.append(f"   - Engine: {event['engine']}")
            if not event.get('success') and event.get('error'):
                report.append(f"   - Error: {event['error']}")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations\n")
        suggestion = self.pattern_learner.suggest_preemptive_fix()
        if suggestion:
            report.append(f"- {suggestion}")
        
        # Save report
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report))
            print(CP(f"\n📄 Recovery report saved: {output_file}", 'green'))
        except Exception as e:
            print(CP(f"\n⚠️  Failed to save report: {e}", 'yellow'))
    
    def save_state(self, context: Dict[str, Any]):
        """Save current state for potential rollback"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "engine": context.get('engine'),
            "context": context.copy()
        }
        self.rollback_stack.append(state)
        
        # Keep only last 5 states
        if len(self.rollback_stack) > 5:
            self.rollback_stack.pop(0)
    
    def rollback(self) -> Optional[Dict[str, Any]]:
        """Rollback to previous state"""
        if not self.rollback_stack:
            return None
        
        previous_state = self.rollback_stack.pop()
        print(CP(f"\n↩️  Rolling back to previous state...", 'yellow'))
        print(f"   Engine: {previous_state.get('engine')}")
        return previous_state
    
    def get_next_quality_engine(self, current_engine: str) -> Optional[str]:
        """Get next engine in quality degradation chain"""
        try:
            current_idx = self.quality_chain.index(current_engine)
            if current_idx < len(self.quality_chain) - 1:
                next_engine = self.quality_chain[current_idx + 1]
                print(CP(f"\n⬇️  Quality degradation: {current_engine} → {next_engine}", 'yellow'))
                return next_engine
        except ValueError:
            pass
        
        return None
    
    # ========== FIX IMPLEMENTATIONS ==========
    
    def _fix_tts_fallback(self, exception: Exception, context: Dict[str, Any]) -> Optional[str]:
        """Switch to offline TTS engine"""
        current_engine = context.get('engine', 'edge')
        
        # Import here to avoid circular dependency
        from core.tts import PIPER_AVAILABLE, PYTTSX3_AVAILABLE
        
        if current_engine == 'edge':
            if PIPER_AVAILABLE:
                print("   → Switching to Piper (offline, fast)")
                return 'piper'
            elif PYTTSX3_AVAILABLE:
                print("   → Switching to pyttsx3 (offline)")
                return 'pyttsx3'
        elif current_engine == 'piper':
            if PYTTSX3_AVAILABLE:
                print("   → Switching to pyttsx3")
                return 'pyttsx3'
        
        print(CP("   ⚠️  No fallback TTS engine available", 'yellow'))
        return None
    
    def _fix_network_resilience(self, exception: Exception, context: Dict[str, Any]) -> Optional[str]:
        """Implement network retry with backoff before falling back to offline (R-02)"""
        import time
        error_msg = str(exception).lower()
        
        # Only retry on timeout/transient issues, not on hard 403 or logic errors
        is_transient = any(k in error_msg for k in ['timeout', 'timed out', 'connection', 'disconnected'])
        
        if is_transient:
            max_retries = 3
            delays = [5, 12, 25]  # Progressive backoff
            
            print(f"   ℹ️  Transient network issue detected. Retrying with backoff...")
            for attempt, delay in enumerate(delays, 1):
                print(f"   ⏳ Retry {attempt}/{max_retries} in {delay}s...")
                time.sleep(delay)
                # Note: The caller handles the actual re-execution. 
                # We return 'retry' as a signal if the operation supports it.
                # If we're here, we're signaling "try again with current settings"
                return context.get('engine', 'edge') # Return current to trigger retry

        # Fallback to offline if retry failed or not transient
        print("   ℹ️  Network unavailable, switching to offline mode")
        from core.tts import PIPER_AVAILABLE, PYTTSX3_AVAILABLE
        
        if PIPER_AVAILABLE:
            print("   → Using Piper (offline, neural)")
            return 'piper'
        elif PYTTSX3_AVAILABLE:
            print("   → Using pyttsx3 (offline)")
            return 'pyttsx3'
        
        print(CP("   ❌ No offline TTS engines available", 'red'))
        return None
    
    def _fix_file_lock(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Retry operation with exponential backoff"""
        max_retries = 5
        base_delay = 2
        
        print(f"   ℹ️  File is locked, will retry up to {max_retries} times")
        
        for attempt in range(1, max_retries + 1):
            delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
            print(f"   ⏳ Attempt {attempt}/{max_retries} in {delay}s...")
            time.sleep(delay)
            
            # The caller should retry their operation after this returns
            print(f"   → Ready for retry (caller should retry operation)")
        
        return True  # Signal that retry is ready
    
    def _fix_ffmpeg(self, exception: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to alternative codec or settings"""
        print("   ℹ️  FFmpeg issue detected")
        print("   → Suggesting quality reduction")
        
        return {
            'codec': 'libx264',
            'crf': 35,  # Lower quality (was 32)
            'preset': 'ultrafast',
            'suggestion': 'Try reducing video quality or reinstalling ffmpeg'
        }
    
    def _fix_missing_dependency(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Show installation guide for missing dependency"""
        error_msg = str(exception).lower()
        
        print("\n   📦 Missing Dependency Detected")
        
        if 'piper' in error_msg:
            print("\n   To install Piper:")
            print("   1. Download from: https://github.com/rhasspy/piper/releases")
            print("   2. Extract to './piper/' folder")
            print("   3. Download a model (.onnx + .json)")
        elif 'edge' in error_msg or 'edge_tts' in error_msg:
            print("\n   To install Edge-TTS:")
            print("   → Run: pip install edge-tts")
        elif 'pyttsx3' in error_msg:
            print("\n   To install pyttsx3:")
            print("   → Run: pip install pyttsx3")
        elif 'moviepy' in error_msg:
            print("\n   To install MoviePy:")
            print("   → Run: pip install moviepy")
        else:
            module_name = error_msg.split("'")[1] if "'" in error_msg else 'missing-package'
            print(f"\n   → Run: pip install {module_name}")
        
        return False  # Can't auto-fix, just provide guidance
    
    def _fix_disk_space(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Attempt to free disk space"""
        print("   💾 Low disk space detected")
        print("   → Checking for temporary files to clean...")
        
        # Import cleanup functions
        from epub_project_manager import cleanup_old_temp_files
        
        cleaned, freed, failed = cleanup_old_temp_files(max_age_days=0, min_size_mb=0)
        
        if cleaned > 0:
            print(CP(f"   ✅ Freed {freed:.1f} MB from {cleaned} folders", 'green'))
            return True
        else:
            print("   ⚠️  No temp files to clean")
            print("   💡 Please free up disk space manually")
            return False


# Convenience function for quick recovery attempts
def try_auto_recover(exception: Exception, context: Dict[str, Any] = None, config: Dict[str, Any] = None):
    """
    Quick wrapper to attempt auto-recovery
    
    Example:
        try:
            generate_audio(...)
        except Exception as e:
            new_engine = try_auto_recover(e, {'operation': 'tts', 'engine': 'edge'})
            if new_engine:
                generate_audio(..., engine=new_engine)
    
    Returns:
        Recovery result (could be new engine, retry signal, etc.) or None
    """
    recovery = AutoRecovery(config)
    
    if recovery.can_fix(exception, context):
        if recovery.ask_user_permission(exception, context):
            return recovery.apply_fix(exception, context)
    
    return None
