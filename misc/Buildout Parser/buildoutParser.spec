# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['buildoutParser.py'],
    pathex=[],
    binaries=[],
    datas=[('Fonts','Fonts'),('squads.tab', '.'),('Buildouts','Buildouts')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['scipy','PySimpleGUI','PyQt6','pygame'],
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
    name='buildoutParser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
