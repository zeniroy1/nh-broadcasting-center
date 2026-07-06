# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\codding\\new folder\\웹크롤링\\tools\\installer_runtime.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\codding\\new folder\\웹크롤링\\_installer_build\\payload.zip', '.')],
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
    a.binaries,
    a.datas,
    [],
    name='LH_HUG_통합프로그램_설치',
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
