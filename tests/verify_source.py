#!/usr/bin/env python3
"""
Verify Execution Source
-----------------------
Checks if running from Python source or frozen executable.
"""
import sys
import os
from pathlib import Path

def check_execution_source():
    """Check if running from source or frozen executable"""
    print("🔍 Checking execution source...\n")
    
    print("="*60)
    print("EXECUTION ENVIRONMENT")
    print("="*60)
    
    # Check if frozen
    is_frozen = getattr(sys, 'frozen', False)
    
    if is_frozen:
        print("❌ RUNNING FROM FROZEN EXECUTABLE!")
        print(f"\n   Type: Frozen/Compiled")
        print(f"   Executable: {sys.executable}")
        print(f"   Base path: {getattr(sys, '_MEIPASS', 'N/A')}")
        print("\n⚠️  WARNING: Changes to source code will NOT be reflected!")
        print("   The executable uses code frozen at build time.")
        print("\n💡 SOLUTION:")
        print("   DO NOT run the .exe during development")
        print("   USE: python epub_project_manager.py")
        result = False
    else:
        print("✅ RUNNING FROM PYTHON SOURCE")
        print(f"\n   Python executable: {sys.executable}")
        print(f"   Script path: {sys.argv[0]}")
        print(f"   Working directory: {os.getcwd()}")
        print("\n✅ Source code changes will be reflected immediately")
        result = True
    
    print("\n" + "="*60)
    print("PYTHON VERSION")
    print("="*60)
    print(f"   Version: {sys.version}")
    print(f"   Platform: {sys.platform}")
    
    print("\n" + "="*60)
    print("MODULE PATHS")
    print("="*60)
    print("   First 5 paths:")
    for i, path in enumerate(sys.path[:5], 1):
        print(f"   {i}. {path}")
    
    # Check if running from correct directory
    print("\n" + "="*60)
    print("PROJECT STRUCTURE")
    print("="*60)
    
    required_files = [
        'epub_project_manager.py',
        'core/config.py',
        'core/utils.py',
        'core/tts.py',
        'requirements.txt'
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING!")
            missing.append(file)
    
    if missing:
        print(f"\n⚠️  WARNING: Missing {len(missing)} required files")
        print("   You may not be in the project root directory")
        result = False
    
    # Final verdict
    print("\n" + "="*60)
    print("VERDICT")
    print("="*60)
    
    if result and not missing:
        print("✅ Everything looks good!")
        print("   • Running from Python source")
        print("   • All required files present")
        print("   • Ready for development")
    elif not result:
        print("❌ Issue detected: Running from executable")
        print("   Action required: Use 'python epub_project_manager.py'")
    elif missing:
        print("❌ Issue detected: Missing files")
        print("   Action required: Navigate to project root directory")
    
    return result and not missing

if __name__ == "__main__":
    try:
        result = check_execution_source()
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
