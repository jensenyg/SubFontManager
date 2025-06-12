import sys
import subprocess

python = sys.executable # 当前运行的Python路径

# Windows下，编译fontmatch.dll文件
if sys.platform == 'win32':
    print('\nCompiling fontmatch.dll...')
    subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass',
                    '-File', '.\\fontmatch_dll\\build.ps1'])

# 编译Cython UU.pyx文件
subprocess.run([python, 'SubFontManager/build.py'])

print('\nAll builds Complete!')
