# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


ROOT = Path.cwd()

datas = [
    (str(ROOT / "backend"), "backend"),
    (str(ROOT / "mlapp" / "migrations"), "mlapp/migrations"),
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "static"), "static"),
    (str(ROOT / "models_store" / "trained" / ".gitkeep"), "models_store/trained"),
    (str(ROOT / "models_store" / "metadata" / ".gitkeep"), "models_store/metadata"),
]
datas += collect_data_files("django")
datas += collect_data_files("rest_framework")

hiddenimports = [
    "backend",
    "backend.settings",
    "backend.urls",
    "backend.wsgi",
    "mlapp",
    "mlapp.admin",
    "mlapp.apps",
    "mlapp.models",
    "mlapp.services",
    "mlapp.urls",
    "mlapp.views",
]

a = Analysis(
    [str(ROOT / "desktop_main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.datas = [
    item
    for item in a.datas
    if "db.sqlite3" not in str(item[0]).replace("\\", "/").lower()
    and "db.sqlite3" not in str(item[1]).replace("\\", "/").lower()
    and "__pycache__" not in str(item[0]).replace("\\", "/").lower()
    and "__pycache__" not in str(item[1]).replace("\\", "/").lower()
    and "/tests/" not in str(item[0]).replace("\\", "/").lower()
    and "/tests/" not in str(item[1]).replace("\\", "/").lower()
]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GenericMLPlatform",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name="GenericMLPlatform",
)
