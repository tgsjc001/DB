
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
import os
project_dir = Path(os.getcwd())

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        ('assets/fonts/*.ttf', 'assets/fonts'),
        ('gui', 'gui'),
        ('models', 'models'),
        ('utils', 'utils'),
	('converted_icons/*.png', 'converted_icons'),
    ],
    hiddenimports=[],
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
    name='VendorManager',
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
    name='VendorManager'
)
