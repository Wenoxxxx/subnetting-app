# PyInstaller spec: builds backend to single exe for Electron packaging.
# Usage: pip install pyinstaller; pyinstaller build-cli.spec
# Output: dist/subnet-cli/subnet-cli.exe
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['src/subnet_calc/cli.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=['subnet_calc'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='subnet-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='subnet-cli',
)
