# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for EPUB Project Manager
# Run: pyinstaller epub_project_manager.spec

block_cipher = None

a = Analysis(
    ['epub_project_manager.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('background.mp3', '.') if os.path.exists('background.mp3') else None,
    ],
    hiddenimports=[
        'ebooklib',
        'PIL',
        'moviepy',
        'edge_tts',
        'pyttsx3',
        'imageio_ffmpeg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out None entries from datas
a.datas = [x for x in a.datas if x is not None]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='epub_project_manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console window for interactive use
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)

