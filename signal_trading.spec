# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

# Collecting data files for pyfiglet
a = Analysis(
    ['signal_trading.py'],
    pathex=['./'],
    binaries=[],
    datas=[('venv/lib/python3.11/site-packages/pyfiglet/fonts', 'pyfiglet/fonts')],
    hiddenimports=['pyfiglet', 'pyfiglet.fonts', 'colorama'],
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
    a.binaries,
    a.datas,
    [],
    name='signal_trading',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
