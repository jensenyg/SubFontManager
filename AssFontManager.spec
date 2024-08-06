# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import site

icon_names = {'darwin': 'icon.icns', 'win32': 'icon.ico', 'linux': 'icon.png', 'linux2': 'icon.png'}

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(site.getsitepackages()[0], 'tkinterdnd2'), 'tkinterdnd2'),
        ('icon/icon@128.png', 'icon'),
        ('lang', 'lang')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['unittest', 'pydoc', 'pdb', 'cProfile', 'cgi', 'cgitb', 'asyncio'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AssFontManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=sys.platform!='win32',    # 官方不建议Windows下使用strip
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('icon', icon_names[sys.platform])
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=sys.platform!='win32',
    upx=False,
    upx_exclude=[],
    name='AssFontManager',
)

app = BUNDLE(
    coll,
    name='AssFontManager.app',
    icon=os.path.join('icon', icon_names[sys.platform]),
    bundle_identifier=None,
)
