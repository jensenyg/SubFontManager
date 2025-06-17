import os
import sys
from . import version
from .ConfigParserWraper import ConfigParserWraper


class App:
    """程序的基本信息"""

    isWindows = sys.platform == 'win32' # 当前是否Windows系统
    isMac = sys.platform == 'darwin'    # 当前是否macOS系统
    name = version.__appname__  # 本程序的名称
    dirName, exeName = os.path.split(sys.argv[0])   # 程序文件的路径和名称
    inDev = exeName.endswith('.py') # 程序是否处于IDE开发状态
    lang: str = 'en_US' # 系统语言
    dpiScale = 1.0  # DPI缩放比例，macOS下可以自动适应

    if isWindows:
        import locale
        from ctypes import windll
        lang = locale.windows_locale.get(windll.kernel32.GetUserDefaultUILanguage())
        # Windows下，开启DPI感知，可以进行高DPI渲染而不是模糊的图像放大 -----
        windll.shcore.SetProcessDpiAwareness(1)
        hwnd = windll.user32.GetDesktopWindow() # 创建用户默认窗口
        hdc = windll.user32.GetDC(hwnd)  # 获取屏幕的物理DPI
        dpi = windll.gdi32.GetDeviceCaps(hdc, 88)   # 88 是 LOGPIXELSX
        windll.user32.ReleaseDC(hwnd, hdc)
        dpiScale = dpi / 96  # 获取缩放比例，通常标准DPI为96
    else:   # Mac / Linux
        lang_str = os.environ.get('LANG')   # 通过环境变量获取系统语言，例：'zh_CN.UTF-8'
        if lang_str:
            lang = lang_str.split('.')[0]
        elif isMac: # pyinstaller打包程序一般不会继承系统环境变量，所以还得靠命令行
            import subprocess
            lang = subprocess.check_output(['defaults', 'read', '-g', 'AppleLocale']).decode().strip()

    # 从特定路径初始化程序配置对象，可读写配置 -----
    Config = ConfigParserWraper(
        os.path.join('.' if inDev else
                     (os.path.join(os.path.expanduser('~/Library/Application Support'), name)
                      if isMac else sys._MEIPASS), 'config.ini')
    )

    @classmethod
    def getResourcesDirectory(cls) -> str:
        """获取程序数据路径"""
        if cls.inDev:
            path = '.'
        elif cls.isMac:
            path = os.path.join(os.path.dirname(cls.dirName), 'Resources')
        else:
            path = sys._MEIPASS # 由pyinstaller打包后设置的当前执行程序目录
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
