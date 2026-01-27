# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['loadouttool.py'],
    pathex=[],
    binaries=[],
    datas=[('componentStats.csv', '.'), ('brandslist.csv','.'), ('chassis.csv', '.'), ('fcprograms.csv', '.'), ('ordnance.csv', '.'), ('lootGroups.csv', '.'), ('lootTables.csv', '.'), ('shipTable.csv', '.'), ('shipTypes.csv', '.'), ('SLT_Icon.ico', '.'), ('Fonts','Fonts'), ('tesseract','tesseract'), ('tessdemo.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['scipy','PySimpleGUI','PyQt6','Flask','Django','pygame'],
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
    name="""Seraph's Loadout Tool Version 2.16.2""",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='SLT_Icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

