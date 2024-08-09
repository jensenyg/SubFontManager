import os
import sys
import ctypes
from __version__ import name as appName
from ConfigParserWraper import ConfigParserWraper


class App:
    """程序的基本信息"""
    MACOS = 'macOS'
    WINDOWS = 'windows'
    LINUX = 'linux'

    # 操作系统类型
    platform = MACOS if sys.platform == 'darwin' else (WINDOWS if sys.platform == 'win32' else LINUX)
    name = appName   # 本程序的名称
    shortName = name.replace(' ', '')   # 去掉空格的名称，用来做目录名
    dirName, exeName = os.path.split(sys.argv[0])   # 程序文件的路径和名称
    isInDev = exeName.endswith('.py')    # 程序是否处于IDE开发状态
    dpiScale = 1.0    # DPI缩放比例
    Config: ConfigParserWraper = None    # 程序配置对象，可读写配置

    @classmethod
    def setDpiAwareness(cls):
        if cls.platform != cls.WINDOWS:
            return
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        hwnd = ctypes.windll.user32.GetDesktopWindow()  # 创建用户默认窗口
        hdc = ctypes.windll.user32.GetDC(hwnd)  # 获取屏幕的物理DPI
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # 88 是 LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(hwnd, hdc)
        cls.dpiScale = dpi / 96  # 获取缩放比例，通常标准DPI为96

    @classmethod
    def getResourcesDirectory(cls) -> str:
        """获取操作系统中合适的程序数据路径，并加上本程序的名称作为目录名"""
        if cls.platform == cls.MACOS and not cls.isInDev:    # macOS and not in dev
            path = os.path.join(os.path.dirname(cls.dirName), 'Resources')
        else:
            path = '.'
        return path

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
            path = os.path.join(os.path.expanduser('~/Library/Application Support'), App.shortName)
        elif cls.platform == cls.WINDOWS:   # Windows
            path = os.path.join(os.getenv('APPDATA', ''), cls.shortName)
        else:   # Linux
            path = os.path.join(os.path.expanduser('~/.cachelocal/share'), cls.shortName)
        return path


# ini配置文件路径
_ini_path = App.getSystemDataDirectory() if App.platform == App.MACOS and not App.isInDev else '.'
_ini_path = os.path.join(_ini_path, 'config.ini')
App.Config = ConfigParserWraper(_ini_path)
