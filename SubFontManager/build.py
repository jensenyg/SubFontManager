import os
import sys
import subprocess

python = sys.executable # 当前运行的Python路径
this_dir = os.path.dirname(os.path.abspath(__file__))   # 当前py文件路径
this_parent_dir = os.path.dirname(this_dir) # 当前py文件路径的上级路径

# 编译Cython UU.pyx文件
print('\nCompiling Cython files...')
subprocess.run([python, os.path.join(this_dir, 'font/uu_cy/setup.py')])

# 打包整个项目
print('\nPackaging the whole project...')
subprocess.run([
    python, '-m', 'PyInstaller', '--clean', '--noconfirm',
    '--distpath', os.path.join(this_parent_dir, 'dist'),
    '--workpath', os.path.join(this_parent_dir, 'build'),
    os.path.join(this_dir, 'SubFontManager.spec')
])
