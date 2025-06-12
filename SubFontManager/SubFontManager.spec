# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import site

is_macos = sys.platform=='darwin'
icon_names = {'darwin': 'icon.icns', 'win32': 'icon.ico', 'linux': 'icon.png', 'linux2': 'icon.png'}

tkdnd_path = None
for path in site.getsitepackages():
    tkdnd_path = os.path.join(path, 'tkinterdnd2')
    print(tkdnd_path)
    if os.path.exists(tkdnd_path):
        break
else:
    raise ImportError("Can not find path to 'tkinterdnd2'.")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('fontmatch.dll', '.')] if sys.platform == 'win32' else [],
    datas=[
        (tkdnd_path, 'tkinterdnd2'),
        ('icon/icon@128.png' if is_macos else 'icon/icon@256.png', 'icon'),
        ('lang', 'lang')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Indispensables: xml, inspect, logging, setuptools, distutils, email, http
    excludes=['test', 'unittest', 'doctest', 'pydoc', 'pdb', 'cProfile', 'cgi', 'venv', 'asyncio', 'pip',
              'html', 'turtle', 'idlelib', 'lib2to3', 'cgitb', 'concurrent', 'sqlite3', 'Cython'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Sub Font Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=sys.platform!='win32',    # 官方不建议Windows下使用strip
    upx=False,
    console=False,  # 是否显示调试控制台窗口
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
    name='Sub Font Manager',
)

app = BUNDLE(
    coll,
    name='Sub Font Manager.app',
    icon=os.path.join('icon', icon_names[sys.platform]),
    bundle_identifier=None,
)
