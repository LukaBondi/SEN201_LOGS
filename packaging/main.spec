# -*- mode: python ; coding: utf-8 -*-

import sys, os
from PyInstaller.utils.hooks import collect_data_files

# --- Determine platform-specific icon ---
if sys.platform.startswith('win'):
    app_icon = os.path.abspath('assets/icon.ico')
elif sys.platform.startswith('linux'):
    app_icon = os.path.abspath('assets/icon.png')  # Linux prefers PNG
else:
    app_icon = None  # Fallback if on other OS

# --- Collect all assets (icons, images, etc.) ---
datas = [(os.path.abspath("assets"), "assets")]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you need a console window
    icon=app_icon,  # <-- Platform-aware icon
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
