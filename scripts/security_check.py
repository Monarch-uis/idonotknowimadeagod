#!/usr/bin/env python3
"""
Security Scanning Script for EPUB Converter
============================================

This script runs multiple security checks on the project:
1. pip-audit - Scan for known vulnerabilities in dependencies
2. bandit - Scan code for security issues
3. safety - Check for vulnerable packages (optional)

Usage:
    python scripts/security_check.py
    python scripts/security_check.py --install-tools
    python scripts/security_check.py --verbose

Requirements:
    pip install pip-audit bandit safety
"""

import subprocess
import sys
import argparse
from pathlib import Path


def print_header(text: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def run_command(name: str, cmd: list, verbose: bool = False) -> tuple[bool, str]:
    """
    Run a command and return success status and output
    
    Returns:
        (success: bool, output: str)
    """
    print(f"🔍 Running {name}...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output = result.stdout + result.stderr
        
        if verbose or result.returncode != 0:
            print(output)
        
        if result.returncode == 0:
            print(f"✅ {name} - PASSED\n")
            return True, output
        else:
            print(f"⚠️  {name} - FOUND ISSUES\n")
            return False, output
            
    except subprocess.TimeoutExpired:
        error_msg = f"❌ {name} - TIMEOUT (exceeded 5 minutes)"
        print(error_msg)
        return False, error_msg
    except FileNotFoundError:
        error_msg = f"❌ {name} - TOOL NOT INSTALLED"
        print(error_msg)
        print(f"   Install with: pip install {name.lower()}")
        return False, error_msg
    except Exception as e:
        error_msg = f"❌ {name} - ERROR: {str(e)}"
        print(error_msg)
        return False, error_msg


def install_security_tools():
    """Install all required security scanning tools"""
    print_header("Installing Security Tools")
    
    tools = [
        "pip-audit>=2.6.0",
        "bandit>=1.7.5",
        "safety>=2.3.5"
    ]
    
    print("Installing: " + ", ".join(tools))
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + tools,
            check=True
        )
        print("\n✅ All security tools installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to install tools: {e}")
        return False


def check_pip_audit(verbose: bool = False) -> tuple[bool, str]:
    """
    Check for known vulnerabilities in dependencies using pip-audit
    """
    print_header("Dependency Vulnerability Scan (pip-audit)")
    
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        return False, "requirements.txt not found"
    
    cmd = [
        sys.executable, "-m", "pip_audit",
        "-r", str(requirements_file),
        "--desc"  # Include vulnerability descriptions
    ]
    
    return run_command("pip-audit", cmd, verbose)


def check_bandit(verbose: bool = False) -> tuple[bool, str]:
    """
    Scan Python code for security issues using Bandit
    """
    print_header("Code Security Scan (Bandit)")
    
    # Scan core and features directories
    targets = ["core", "features", "epub_project_manager.py", "run.py"]
    existing_targets = [t for t in targets if Path(t).exists()]
    
    if not existing_targets:
        return False, "No Python files found to scan"
    
    cmd = [
        sys.executable, "-m", "bandit",
        "-r",  # Recursive
        "-ll",  # Only show medium and high severity
        "-f", "screen",  # Format output for terminal
    ] + existing_targets
    
    return run_command("Bandit", cmd, verbose)


def check_safety(verbose: bool = False) -> tuple[bool, str]:
    """
    Check for vulnerable packages using Safety
    Note: Safety requires API key for full database access
    """
    print_header("Package Safety Check (Safety)")
    
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        return False, "requirements.txt not found"
    
    cmd = [
        sys.executable, "-m", "safety",
        "check",
        "-r", str(requirements_file),
        "--json"  # JSON output for easier parsing
    ]
    
    return run_command("Safety", cmd, verbose)


def generate_report(results: dict, output_file: str = "security_report.txt"):
    """Generate a comprehensive security report"""
    print_header("Generating Security Report")
    
    report_lines = [
        "=" * 70,
        "SECURITY SCAN REPORT",
        "=" * 70,
        "",
        f"Total Checks: {len(results)}",
        f"Passed: {sum(1 for r in results.values() if r[0])}",
        f"Failed: {sum(1 for r in results.values() if not r[0])}",
        "",
    ]
    
    for check_name, (success, output) in results.items():
        report_lines.extend([
            "-" * 70,
            f"CHECK: {check_name}",
            f"STATUS: {'✅ PASSED' if success else '⚠️ FAILED'}",
            "-" * 70,
            output,
            "",
        ])
    
    report_text = "\n".join(report_lines)
    
    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    print(f"📄 Report saved to: {output_file}")
    return report_text


def main():
    """Main entry point for security scanning"""
    parser = argparse.ArgumentParser(
        description="Run security scans on the EPUB Converter project"
    )
    parser.add_argument(
        "--install-tools",
        action="store_true",
        help="Install required security scanning tools"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output from all scans"
    )
    parser.add_argument(
        "--skip-safety",
        action="store_true",
        help="Skip Safety check (requires API key)"
    )
    parser.add_argument(
        "--report",
        default="security_report.txt",
        help="Output file for security report (default: security_report.txt)"
    )
    
    args = parser.parse_args()
    
    # Install tools if requested
    if args.install_tools:
        if install_security_tools():
            print("\n✅ Tools installed. Run the script again without --install-tools to scan.")
        sys.exit(0)
    
    print_header("EPUB Converter - Security Scan")
    print("Starting comprehensive security checks...")
    
    # Run all security checks
    results = {}
    
    # 1. pip-audit
    results["pip-audit"] = check_pip_audit(args.verbose)
    
    # 2. Bandit
    results["Bandit"] = check_bandit(args.verbose)
    
    # 3. Safety (optional)
    if not args.skip_safety:
        results["Safety"] = check_safety(args.verbose)
    
    # Generate report
    generate_report(results, args.report)
    
    # Summary
    print_header("SECURITY SCAN SUMMARY")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r[0])
    failed = total - passed
    
    print(f"📊 Total Checks: {total}")
    print(f"✅ Passed: {passed}")
    print(f"⚠️  Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All security checks passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} security check(s) found issues!")
        print(f"📄 See detailed report: {args.report}")
        print("\nRecommended actions:")
        print("  1. Review the security report")
        print("  2. Update vulnerable dependencies")
        print("  3. Fix code security issues")
        print("  4. Re-run this script to verify fixes")
        sys.exit(1)


if __name__ == "__main__":
    main()
