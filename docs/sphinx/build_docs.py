#!/usr/bin/env python3
"""
Sphinx Documentation Builder
Builds HTML documentation from source files
"""
import os
import sys
import subprocess
from pathlib import Path


def build_docs(builder='html', clean=False):
    """
    Build documentation using Sphinx
    
    Args:
        builder: Output format (html, pdf, epub)
        clean: Clean build directory before building
    """
    docs_dir = Path(__file__).parent
    source_dir = docs_dir
    build_dir = docs_dir / '_build'
    
    # Clean if requested
    if clean and build_dir.exists():
        import shutil
        print("🧹 Cleaning build directory...")
        shutil.rmtree(build_dir)
    
    # Build command
    cmd = [
        'sphinx-build',
        '-b', builder,
        '-d', str(build_dir / 'doctrees'),
        str(source_dir),
        str(build_dir / builder)
    ]
    
    print(f"\n📚 Building Sphinx documentation ({builder})...")
    print(f"📂 Source: {source_dir}")
    print(f"📂 Output: {build_dir / builder}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"\n✅ Documentation built successfully!")
        print(f"📖 Open: {build_dir / builder / 'index.html'}")
    else:
        print(f"\n❌ Build failed with code {result.returncode}")
    
    return result.returncode


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Sphinx documentation")
    parser.add_argument(
        '--builder', '-b',
        default='html',
        choices=['html', 'pdf', 'epub', 'latex'],
        help='Documentation builder to use'
    )
    parser.add_argument(
        '--clean', '-c',
        action='store_true',
        help='Clean build directory before building'
    )
    parser.add_argument(
        '--open', '-o',
        action='store_true',
        help='Open documentation in browser after building'
    )
    
    args = parser.parse_args()
    
    returncode = build_docs(args.builder, args.clean)
    
    if returncode == 0 and args.open and args.builder == 'html':
        import webbrowser
        docs_dir = Path(__file__).parent
        index_file = docs_dir / '_build' / 'html' / 'index.html'
        webbrowser.open(f'file://{index_file}')
    
    return returncode


if __name__ == '__main__':
    sys.exit(main())
