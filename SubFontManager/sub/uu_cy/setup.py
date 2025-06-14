"""
编译UU.pyx文件，并将生成的.pyd文件放在上一层目录内
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import os
import sys


# 当前py文件路径
this_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    sys.argv.extend([
        'build_ext',
        # '--inplace',
        f'--build-lib={os.path.dirname(this_dir)}', # .pyd文件导出路径
        f'--build-temp={os.path.join(this_dir, "temp")}'    # 临时文件路径
    ])

setup(
    name="UU",
    ext_modules=cythonize(Extension(name="UU", sources=[os.path.join(this_dir, "UU.pyx")]))
)
