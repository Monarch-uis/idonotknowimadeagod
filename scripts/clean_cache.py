#!/usr/bin/env python3
"""
Clean Cache Utility
-------------------
Removes all __pycache__ directories and .pyc files.
"""
import os
import shutil
from pathlib import Path

def clean_cache():
    print("🧹 Cleaning bytecode cache...")
    
    # Remove __pycache__ directories
    count_dirs = 0
    for pycache in Path('.').rglob('__pycache__'):
        try:
            shutil.rmtree(pycache)
            print(f"   Deleted: {pycache}")
            count_dirs += 1
        except Exception as e:
            print(f"   ❌ Failed to delete {pycache}: {e}")
            
    # Remove .pyc files
    count_files = 0
    for pyc in Path('.').rglob('*.pyc'):
        try:
            pyc.unlink()
            print(f"   Deleted: {pyc}")
            count_files += 1
        except Exception as e:
            print(f"   ❌ Failed to delete {pyc}: {e}")
            
    print(f"\n✅ Cleaned {count_dirs} directories and {count_files} files.")
    
    # Check for build/ and dist/
    if Path('build').exists():
        try:
            shutil.rmtree('build')
            print("   Deleted: build/")
        except OSError:
            pass
        
    if Path('dist').exists():
        try:
            shutil.rmtree('dist')
            print("   Deleted: dist/")
        except OSError:
            pass

if __name__ == "__main__":
    clean_cache()
