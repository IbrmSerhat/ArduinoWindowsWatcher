# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['finalProject.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('LinkTreeler(1).png', '.'),
        ('deskupper-4a86b-firebase-adminsdk-wvl1f-54277bff6b.json', '.')
    ],
    hiddenimports=['win32gui', 'win32process', 'psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DeskUpper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='LinkTreeler(1).png'
) 