# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for the Musinsa buyer app.

Build (from submission/src, with pyinstaller installed):

    pyinstaller packaging/musinsa_buyer_app.spec --noconfirm

Output: dist/MusinsaBuyerApp.exe (Windows) or dist/MusinsaBuyerApp (other OS).
Double-clicking it starts the local server and opens the app in the
default browser automatically. No console window is shown; runtime
errors go to musinsa_buyer_app.log next to the executable instead.
"""

import os

block_cipher = None

# This spec lives in submission/src/packaging/, so submission/src is one
# level up. All Analysis paths are anchored on that so the build works
# regardless of the current working directory pyinstaller is invoked from.
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), ".."))
SCRIPTS_DIR = os.path.join(SRC_ROOT, "scripts")

a = Analysis(
    [os.path.join(SCRIPTS_DIR, "musinsa_buyer_server.py")],
    pathex=[SCRIPTS_DIR],
    binaries=[],
    datas=[
        (os.path.join(SRC_ROOT, "app", "musinsa_buyer_app.html"), "app"),
        (os.path.join(SRC_ROOT, "config"), "config"),
    ],
    hiddenimports=[
        "musinsa_intent_parser",
        "musinsa_query_generator",
        "musinsa_live_buyer_app",
        "musinsa_recommendation_output",
        "musinsa_scoring_model",
        "musinsa_review_signal_schema",
        "musinsa_detail_schema",
        "musinsa_collection_planner",
        "musinsa_proxy_metrics",
        "musinsa_signal_catalog",
        "musinsa_keyword_learning",
        "musinsa_runtime_paths",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MusinsaBuyerApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
