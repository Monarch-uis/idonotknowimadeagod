#!/usr/bin/env python3
"""
Integration Test Runner
Runs all integration tests with proper reporting
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_integration_tests(verbose=False, coverage=True, markers=None):
    """
    Run integration tests with specified options
    
    Args:
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        markers: pytest markers to filter tests
    """
    cmd = ["pytest", "tests/integration/"]
    
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=core",
            "--cov=features",
            "--cov-report=html",
            "--cov-report=term"
        ])
    
    if markers:
        cmd.extend(["-m", markers])
    
    # Add output options
    cmd.extend([
        "--tb=short",
        "--color=yes"
    ])
    
    print(f"\n🧪 Running Integration Tests")
    print(f"📋 Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "-m", "--markers",
        help="Run tests matching given mark expression (e.g., 'not slow')"
    )
    parser.add_argument(
        "--audiobook-only",
        action="store_true",
        help="Run only audiobook tests"
    )
    parser.add_argument(
        "--video-only",
        action="store_true",
        help="Run only video tests"
    )
    
    args = parser.parse_args()
    
    # Determine which tests to run
    if args.audiobook_only:
        test_file = "tests/integration/test_epub_to_audiobook.py"
        cmd = ["pytest", test_file]
    elif args.video_only:
        test_file = "tests/integration/test_epub_to_video.py"
        cmd = ["pytest", test_file]
    else:
        cmd = ["pytest", "tests/integration/"]
    
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    if not args.no_coverage:
        cmd.extend([
            "--cov=core",
            "--cov=features",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    cmd.extend(["--tb=short", "--color=yes"])
    
    print("\n" + "="*70)
    print("🧪 EPUB CONVERTER - INTEGRATION TEST SUITE")
    print("="*70)
    print(f"\n📋 Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    print("\n" + "="*70)
    if result.returncode == 0:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
    print("="*70 + "\n")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
