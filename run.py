"""
CLI wrapper for epub_project_manager.py with profiling and logging support

This wrapper adds command-line arguments for:
- Performance profiling
- Logging configuration
- Config validation
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.profiler import enable_profiling, disable_profiling
from core.logging_config import setup_logging, get_logger
from core.config import validate_config_schema, CONFIG

def main():
    """Main entry point with CLI argument handling"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="EPUB to Audiobook/Video Converter")
    parser.add_argument("--profile", action="store_true", help="Enable performance profiling")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Set logging level")
    parser.add_argument("--log-format", choices=["text", "json"], default="text", help="Set log format")
    parser.add_argument("--validate-config", action="store_true", help="Validate config.json and exit")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level, log_format=args.log_format)
    logger = get_logger(__name__)
    
    # Config validation mode
    if args.validate_config:
        print("\\n🔍 Validating config.json...")
        is_valid, error_msg = validate_config_schema(CONFIG)
        if is_valid:
            print("✅ Configuration is valid!")
            sys.exit(0)
        else:
            print(f"❌ Configuration validation failed:\\n{error_msg}")
            sys.exit(1)
    
    # Enable profiling if requested
    profiler = None
    if args.profile:
        print("\\n📊 Performance profiling enabled")
        profiler = enable_profiling(name="epub_conversion")
    
    try:
        # Import and run the main application
        import epub_project_manager
        epub_project_manager.main()
    except KeyboardInterrupt:
        print("\\n\\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        try:
            input("\\nPress Enter to exit...")
        except:
            pass
        sys.exit(1)
    finally:
        # Disable profiling and generate report
        if profiler:
            report_path = disable_profiling(generate_report=True, format="html")
            if report_path:
                print(f"\\n📊 Performance report saved to: {report_path}")

if __name__ == "__main__":
    main()
