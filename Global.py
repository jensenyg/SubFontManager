import os
import sys
from __version__ import name as appName
from ConfigParserWraper import ConfigParserWraper


class AppInfo:
    """程序的基本信息"""
    MACOS = 'macOS'
    WINDOWS = 'windows'
    LINUX = 'linux'

    platform = MACOS if sys.platform == 'darwin' else (WINDOWS if sys.platform == 'win32' else LINUX)
    name = appName   # 程序的名称
    shortName = name.replace(' ', '')   # 去掉空格的名称，用来做目录名
    dirName, exeName = os.path.split(sys.argv[0])   # 程序文件的路径和名称
    isInDev = exeName.endswith('.py')    # 程序是否处于IDE开发状态

    @classmethod
    def getSystemCacheDirectory(cls) -> str:
        """获取操作系统中合适的缓存路径，并加上本程序的名称作为目录名"""
        if cls.platform == cls.MACOS:    # macOS
            path = os.path.join(os.path.expanduser('~/Library/Caches'), cls.shortName)
        elif cls.platform == cls.WINDOWS:   # Windows
            path = os.path.join(os.getenv('LOCALAPPDATA', ''), cls.shortName)
        else:   # Linux
            path = os.path.join(os.path.expanduser('~/.cache'), cls.shortName)
        return path

    @classmethod
    def getSystemDataDirectory(cls) -> str:
        """获取操作系统中合适的程序数据路径，并加上本程序的名称作为目录名"""
        if cls.platform == cls.MACOS:    # macOS
            path = os.path.join(os.path.expanduser('~/Library/Application Support'), AppInfo.shortName)
        elif cls.platform == cls.WINDOWS:   # Windows
            path = os.path.join(os.getenv('APPDATA', ''), cls.shortName)
        else:   # Linux
            path = os.path.join(os.path.expanduser('~/.cachelocal/share'), cls.shortName)
        return path


# 设置ini配置文件路径
_ini_path = AppInfo.getSystemDataDirectory() if AppInfo.platform == AppInfo.MACOS and not AppInfo.isInDev else '.'
_ini_path = os.path.join(_ini_path, 'config.ini')

# 程序配置对象，可读写
Config = ConfigParserWraper(_ini_path)
