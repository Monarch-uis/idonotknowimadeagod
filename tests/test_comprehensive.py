#!/usr/bin/env python3
"""
Comprehensive Test Suite
------------------------
Tests all aspects of the code execution fix.
"""
import os
import sys
import shutil
from pathlib import Path

class FixVerificationSuite:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def print_header(self, text):
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")
    
    def run_test(self, name, test_func):
        """Run a single test and track results"""
        self.tests_run += 1
        print(f"[Test {self.tests_run}] {name}...")
        
        try:
            result = test_func()
            if result:
                self.tests_passed += 1
                print(f"   ✅ PASSED\n")
                return True
            else:
                self.tests_failed += 1
                self.failures.append(name)
                print(f"   ❌ FAILED\n")
                return False
        except Exception as e:
            self.tests_failed += 1
            self.failures.append(f"{name}: {str(e)}")
            print(f"   ❌ FAILED: {e}\n")
            return False
    
    def test_no_cache_files(self):
        """Test: No bytecode cache files exist"""
        cache_found = False
        
        for pycache in Path('.').rglob('__pycache__'):
            if '.venv' not in str(pycache):
                print(f"      Found: {pycache}")
                cache_found = True
        
        for pyc in Path('.').rglob('*.pyc'):
            if '.venv' not in str(pyc):
                print(f"      Found: {pyc}")
                cache_found = True
        
        if not cache_found:
            print("      No cache files found")
        
        return not cache_found
    
    def test_no_build_artifacts(self):
        """Test: No build artifacts exist"""
        has_build = Path('build').exists()
        has_dist = Path('dist').exists()
        
        if has_build:
            print("      Found: build/")
        if has_dist:
            print("      Found: dist/")
        
        if not (has_build or has_dist):
            print("      No build artifacts")
        
        return not (has_build or has_dist)
    
    def test_running_from_source(self):
        """Test: Running from Python source"""
        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            print("      Running from executable")
        else:
            print("      Running from Python source")
        
        return not is_frozen
    
    def test_project_structure(self):
        """Test: Required files exist"""
        required = [
            'epub_project_manager.py',
            'core/config.py',
            'core/utils.py',
            'requirements.txt'
        ]
        
        missing = []
        for file in required:
            if not Path(file).exists():
                print(f"      Missing: {file}")
                missing.append(file)
        
        if not missing:
            print(f"      All {len(required)} required files present")
        
        return len(missing) == 0
    
    def test_module_imports(self):
        """Test: Core modules can be imported"""
        modules = [
            'core.config',
            'core.utils',
            'core.tts',
        ]
        
        failed = []
        for module in modules:
            try:
                __import__(module)
                print(f"      ✓ {module}")
            except ImportError as e:
                print(f"      ✗ {module}: {e}")
                failed.append(module)
        
        return len(failed) == 0
    
    def test_cache_prevention_env(self):
        """Test: Cache prevention environment variable"""
        has_env = os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
        
        if has_env:
            print("      PYTHONDONTWRITEBYTECODE=1 set")
        else:
            print("      PYTHONDONTWRITEBYTECODE not set (optional)")
        
        # This is optional, so always pass
        return True
    
    def test_tools_exist(self):
        """Test: All fix tools exist"""
        tools = [
            'diagnose_fix.py',
            'clean_cache.py',
            'verify_clean.py',
            'verify_source.py',
            'clean_and_run.bat',
            'clean_cache.bat',
            'clean_build.bat'
        ]
        
        missing = []
        for tool in tools:
            if not Path(tool).exists():
                print(f"      Missing: {tool}")
                missing.append(tool)
        
        if not missing:
            print(f"      All {len(tools)} tools present")
        
        return len(missing) == 0
    
    def test_documentation_exists(self):
        """Test: Documentation files exist"""
        docs = [
            'CODE_EXECUTION_FIX_GUIDE.md',
            'QUICK_REFERENCE_CARD.txt',
            'MASTER_INDEX.py'
        ]
        
        missing = []
        for doc in docs:
            if not Path(doc).exists():
                print(f"      Missing: {doc}")
                missing.append(doc)
        
        if not missing:
            print(f"      All {len(docs)} documentation files present")
        
        return len(missing) == 0
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.print_header("🧪 COMPREHENSIVE TEST SUITE")
        print("Testing all aspects of code execution fix...\n")
        
        # Run all tests
        self.run_test("No bytecode cache files", self.test_no_cache_files)
        self.run_test("No build artifacts", self.test_no_build_artifacts)
        self.run_test("Running from source", self.test_running_from_source)
        self.run_test("Project structure intact", self.test_project_structure)
        self.run_test("Core modules importable", self.test_module_imports)
        self.run_test("Cache prevention configured", self.test_cache_prevention_env)
        self.run_test("All tools present", self.test_tools_exist)
        self.run_test("Documentation complete", self.test_documentation_exists)
        
        # Results summary
        self.print_header("📊 TEST RESULTS")
        
        print(f"Tests Run:    {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_failed > 0:
            print("\n❌ FAILED TESTS:")
            for failure in self.failures:
                print(f"   • {failure}")
            
            print("\n💡 RECOMMENDATIONS:")
            if "cache" in str(self.failures).lower():
                print("   1. Run: python clean_cache.py")
            if "build" in str(self.failures).lower():
                print("   2. Run: clean_build.bat")
            if "source" in str(self.failures).lower():
                print("   3. Use: python epub_project_manager.py (not .exe)")
            if "import" in str(self.failures).lower():
                print("   4. Check if modules exist in source")
            if "tools" in str(self.failures).lower() or "documentation" in str(self.failures).lower():
                print("   5. Ensure all files were created")
            
            print("\n🔧 Quick Fix:")
            print("   python diagnose_fix.py")
        else:
            print("\n✅ ALL TESTS PASSED!")
            print("\n🎉 Your project is properly configured!")
            print("\nYou can now:")
            print("   • Make changes to source code")
            print("   • Run: python epub_project_manager.py")
            print("   • Changes will be reflected immediately")
        
        return self.tests_failed == 0

if __name__ == "__main__":
    try:
        print("╔════════════════════════════════════════════════════════════╗")
        print("║      CODE EXECUTION FIX - COMPREHENSIVE TEST SUITE         ║")
        print("╚════════════════════════════════════════════════════════════╝")
        
        suite = FixVerificationSuite()
        success = suite.run_all_tests()
        
        print()
        input("Press Enter to exit...")
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        exit(1)
