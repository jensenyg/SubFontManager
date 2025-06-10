import sys
import subprocess
from SubFontManager.utils import App

python = sys.executable # 当前运行的Python路径

# Windows下，编译fontmatch.dll文件
if App.isWindows:
    print('\nCompiling fontmatch.dll...')
    subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass',
                    '-File', '.\\fontmatch_dll\\build.ps1'])

# 编译Cython UU.pyx文件
subprocess.run([python, 'SubFontManager/build.py'])

print('\nAll builds Complete!')
