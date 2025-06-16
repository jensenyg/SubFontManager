import os
import sys
from . import version
from .ConfigParserWraper import ConfigParserWraper


class App:
    """程序的基本信息"""

    isMac = sys.platform == 'darwin'    # 当前是否macOS系统
    isWindows = sys.platform == 'win32' # 当前是否Windows系统
    name = version.__appname__  # 本程序的名称
    dirName, exeName = os.path.split(sys.argv[0])   # 程序文件的路径和名称
    inDev = exeName.endswith('.py')    # 程序是否处于IDE开发状态
    dpiScale = 1.0    # DPI缩放比例

    Config = ConfigParserWraper(    # 程序配置对象，可读写配置
        os.path.join('.' if inDev else
                     (os.path.join(os.path.expanduser('~/Library/Application Support'), name)
                      if isMac else sys._MEIPASS), 'config.ini')
    )

    @classmethod
    def setDpiAwareness(cls):
        if not cls.isWindows:
            return
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        hwnd = ctypes.windll.user32.GetDesktopWindow()  # 创建用户默认窗口
        hdc = ctypes.windll.user32.GetDC(hwnd)  # 获取屏幕的物理DPI
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # 88 是 LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(hwnd, hdc)
        cls.dpiScale = dpi / 96  # 获取缩放比例，通常标准DPI为96

    @classmethod
    def getResourcesDirectory(cls) -> str:
        """获取程序数据路径"""
        if cls.inDev:
            path = '.'
        elif cls.isMac:
            path = os.path.join(os.path.dirname(cls.dirName), 'Resources')
        else:
            path = sys._MEIPASS
        return path

    @classmethod
    def getSystemDataDirectory(cls) -> str:
        """获取操作系统中合适的配置文件路径，并加上本程序的名称作为目录名"""
        if cls.isMac:    # macOS
            path = os.path.join(os.path.expanduser('~/Library/Application Support'), cls.name)
        elif cls.isWindows:  # Windows
            path = os.path.join(os.getenv('APPDATA', ''), cls.name)
        # elif cls.isLinux:    # Linux
        #     path = os.path.join(os.path.expanduser('~/.cachelocal/share'), cls.name)
        else:   # 不识别的系统，无法支持
            path = ''
        return path
