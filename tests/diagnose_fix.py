#!/usr/bin/env python3
"""
Complete Diagnostic and Fix Tool
---------------------------------
Diagnoses and fixes code execution issues caused by bytecode cache.
"""
import os
import sys
import shutil
from pathlib import Path
import subprocess

class DiagnosticTool:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.fixed = []
        
    def print_header(self, text):
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")
    
    def check_cache_files(self):
        """Check for bytecode cache files"""
        self.print_header("STEP 1: Checking Bytecode Cache")
        
        pycache_dirs = []
        pyc_files = []
        
        for pycache in Path('.').rglob('__pycache__'):
            if '.venv' not in str(pycache):
                pycache_dirs.append(pycache)
        
        for pyc in Path('.').rglob('*.pyc'):
            if '.venv' not in str(pyc):
                pyc_files.append(pyc)
        
        if pycache_dirs or pyc_files:
            self.issues.append("Bytecode cache files found")
            print(f"   ❌ Found {len(pycache_dirs)} __pycache__ directories")
            print(f"   ❌ Found {len(pyc_files)} .pyc files")
            return False, (pycache_dirs, pyc_files)
        else:
            print("   ✅ No bytecode cache found")
            return True, ([], [])
    
    def check_build_artifacts(self):
        """Check for PyInstaller build artifacts"""
        self.print_header("STEP 2: Checking Build Artifacts")
        
        has_build = Path('build').exists()
        has_dist = Path('dist').exists()
        
        if has_build or has_dist:
            self.warnings.append("Build artifacts found")
            if has_build:
                print("   ⚠️  build/ directory exists")
            if has_dist:
                print("   ⚠️  dist/ directory exists")
            return False, (has_build, has_dist)
        else:
            print("   ✅ No build artifacts found")
            return True, (False, False)
    
    def check_execution_source(self):
        """Check if running from source or executable"""
        self.print_header("STEP 3: Checking Execution Source")
        
        if getattr(sys, 'frozen', False):
            self.issues.append("Running from frozen executable")
            print("   ❌ RUNNING FROM EXECUTABLE")
            print("      This diagnostic tool is running from compiled code!")
            print("      Run: python diagnose_fix.py")
            return False
        else:
            print("   ✅ Running from Python source")
            return True
    
    def check_project_structure(self):
        """Check project structure"""
        self.print_header("STEP 4: Checking Project Structure")
        
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
                print(f"   ❌ {file}")
                missing.append(file)
        
        if missing:
            self.issues.append(f"Missing {len(missing)} required files")
            return False, missing
        
        return True, []
    
    def check_import_issues(self):
        """Check for import issues"""
        self.print_header("STEP 5: Checking Module Imports")
        
        modules_to_test = [
            'core.config',
            'core.utils',
            'core.epub_io',
            'core.tts',
            'core.video_pipeline',
            'core.subtitle_generator',
        ]
        
        failed = []
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"   ✅ {module_name}")
            except ImportError as e:
                print(f"   ❌ {module_name}: {e}")
                failed.append((module_name, str(e)))
        
        if failed:
            self.issues.append(f"{len(failed)} modules failed to import")
            return False, failed
        
        return True, []
    
    def clean_cache(self, pycache_dirs, pyc_files):
        """Clean bytecode cache"""
        self.print_header("FIXING: Cleaning Bytecode Cache")
        
        removed_dirs = 0
        removed_files = 0
        
        for pycache in pycache_dirs:
            try:
                shutil.rmtree(pycache)
                removed_dirs += 1
                print(f"   ✅ Removed {pycache}")
            except Exception as e:
                print(f"   ❌ Failed to remove {pycache}: {e}")
        
        for pyc in pyc_files:
            try:
                pyc.unlink()
                removed_files += 1
            except Exception as e:
                print(f"   ❌ Failed to remove {pyc}: {e}")
        
        if removed_dirs > 0 or removed_files > 0:
            self.fixed.append(f"Removed {removed_dirs} dirs, {removed_files} files")
            print(f"\n   ✅ Cleaned {removed_dirs} directories, {removed_files} files")
            return True
        
        return False
    
    def clean_build(self, has_build, has_dist):
        """Clean build artifacts"""
        self.print_header("FIXING: Cleaning Build Artifacts")
        
        cleaned = []
        
        if has_build:
            try:
                shutil.rmtree('build')
                cleaned.append('build/')
                print("   ✅ Removed build/")
            except Exception as e:
                print(f"   ❌ Failed to remove build/: {e}")
        
        if has_dist:
            try:
                shutil.rmtree('dist')
                cleaned.append('dist/')
                print("   ✅ Removed dist/")
            except Exception as e:
                print(f"   ❌ Failed to remove dist/: {e}")
        
        if cleaned:
            self.fixed.append(f"Removed {', '.join(cleaned)}")
            return True
        
        return False
    
    def run_full_diagnostic(self):
        """Run complete diagnostic"""
        self.print_header("🔍 COMPREHENSIVE DIAGNOSTIC AND FIX TOOL")
        print("Analyzing project for code execution issues...")
        
        # Run all checks
        cache_ok, cache_data = self.check_cache_files()
        build_ok, build_data = self.check_build_artifacts()
        source_ok = self.check_execution_source()
        structure_ok, missing = self.check_project_structure()
        import_ok, failed_imports = self.check_import_issues()
        
        # Summary
        self.print_header("📊 DIAGNOSTIC SUMMARY")
        
        all_ok = cache_ok and build_ok and source_ok and structure_ok and import_ok
        
        if all_ok:
            print("✅ ALL CHECKS PASSED!")
            print("\n   • No bytecode cache issues")
            print("   • No build artifacts")
            print("   • Running from source")
            print("   • Project structure intact")
            print("   • All modules import successfully")
            print("\n🎉 Your project is clean and ready!")
            return True
        
        # Show issues
        if self.issues:
            print("❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"   • {issue}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        # Offer to fix
        print(f"\n{'='*70}")
        fix = input("\n🔧 Attempt to fix issues automatically? (y/n): ").strip().lower()
        
        if fix == 'y':
            self.print_header("🔧 APPLYING FIXES")
            
            # Fix cache
            if not cache_ok:
                self.clean_cache(*cache_data)
            
            # Fix build artifacts
            if not build_ok:
                self.clean_build(*build_data)
            
            # Show what was fixed
            if self.fixed:
                self.print_header("✅ FIXES APPLIED")
                for fix in self.fixed:
                    print(f"   • {fix}")
                
                print("\n💡 RECOMMENDATIONS:")
                print("   1. Restart your IDE")
                print("   2. Run: python verify_source.py")
                print("   3. Run: python epub_project_manager.py")
                print("   4. Always use 'python' command, never run .exe during development")
            
            return True
        else:
            print("\n⚠️  No fixes applied. Issues remain.")
            return False

if __name__ == "__main__":
    try:
        tool = DiagnosticTool()
        tool.run_full_diagnostic()
        
        print()
        input("Press Enter to exit...")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        exit(1)
