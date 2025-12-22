#!/usr/bin/env python3
"""
Verify Cache is Clean
---------------------
Checks that no bytecode cache files remain in the project.
"""
import os
from pathlib import Path

def check_cache():
    """Check for any remaining cache files"""
    print("🔍 Checking for bytecode cache files...\n")
    
    issues = []
    
    # Check for __pycache__ directories
    print("📂 Checking for __pycache__ directories...")
    pycache_found = False
    for pycache in Path('.').rglob('__pycache__'):
        # Skip virtual environment
        if '.venv' in str(pycache):
            continue
        pycache_found = True
        issues.append(f"Found: {pycache}")
        print(f"   ❌ {pycache}")
    
    if not pycache_found:
        print("   ✅ No __pycache__ directories found")
    
    # Check for .pyc files
    print("\n📄 Checking for .pyc files...")
    pyc_found = False
    for pyc in Path('.').rglob('*.pyc'):
        # Skip virtual environment
        if '.venv' in str(pyc):
            continue
        pyc_found = True
        issues.append(f"Found: {pyc}")
        print(f"   ❌ {pyc}")
    
    if not pyc_found:
        print("   ✅ No .pyc files found")
    
    # Check for build artifacts
    print("\n🏗️  Checking for build artifacts...")
    build_issues = []
    
    if Path('build').exists():
        build_issues.append("build/")
        print("   ❌ build/ directory exists")
    else:
        print("   ✅ build/ directory not found")
    
    if Path('dist').exists():
        build_issues.append("dist/")
        print("   ❌ dist/ directory exists")
    else:
        print("   ✅ dist/ directory not found")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 VERIFICATION SUMMARY")
    print(f"{'='*60}")
    
    if issues:
        print(f"❌ Found {len(issues)} cache issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"   • {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more")
        print("\n💡 Run: python clean_cache.py")
        return False
    elif build_issues:
        print(f"⚠️  Found build artifacts: {', '.join(build_issues)}")
        print("\n💡 Run: clean_build.bat")
        return False
    else:
        print("✅ No cache files found!")
        print("✅ Project is clean and ready to run from source")
        return True

if __name__ == "__main__":
    try:
        result = check_cache()
        print()
        input("Press Enter to exit...")
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        exit(1)
