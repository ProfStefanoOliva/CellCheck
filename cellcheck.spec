# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH or ".").resolve()

datas = [
    (str(PROJECT_ROOT / "assets" / "branding" / "cellcheck_logo_square.png"), "assets/branding"),
    (str(PROJECT_ROOT / "assets" / "branding" / "cellcheck_logo_horizontal.png"), "assets/branding"),
    (str(PROJECT_ROOT / "assets" / "branding" / "cellcheck_icon.ico"), "assets/branding"),
    (str(PROJECT_ROOT / "LICENSE"), "."),
    (str(PROJECT_ROOT / "NOTICE"), "."),
    (str(PROJECT_ROOT / "TRADEMARKS.md"), "."),
    (str(PROJECT_ROOT / "BRAND_GUIDELINES.md"), "."),
    (str(PROJECT_ROOT / "DISCLAIMER.md"), "."),
    (str(PROJECT_ROOT / "README.md"), "."),
]


a = Analysis(
    ["packaging/pyinstaller_entry.py"],
    pathex=[str(PROJECT_ROOT / "src")],
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
    a.binaries,
    a.datas,
    [],
    name="CellCheck",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(PROJECT_ROOT / "assets" / "branding" / "cellcheck_icon.ico"),
)
