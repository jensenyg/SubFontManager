from .FlatButton import FlatButton
from .WidgetTable import WidgetTable
from .StatusBar import StatusBar
from .PlaceholderInput import PlaceholderEntry, PlaceholderCombobox
from .ToolTip import ToolTip


def placeWindow(window, x: int = None, y: int = None, width: int = 500, height: int = 400,
                xRatio: float = 0.5, yRatio: float = 0.5):
    # 获取父窗口/屏幕宽高
    parent = window.master
    if x is None:
        if parent:
            x = parent.winfo_x()
            parent_width = parent.winfo_width()
        else:
            x = 0
            parent_width = window.winfo_screenwidth()
        # 计算窗口左边缘位置
        x += int((parent_width - width) * xRatio)
    if y is None:
        if parent:
            y = parent.winfo_y()
            parent_height = parent.winfo_height()
        else:
            y = 0
            parent_height = window.winfo_screenheight()
        # 计算窗口上边缘位置
        y += int((parent_height - height) * yRatio)
    # 设置窗口大小和位置
    window.geometry(f'{width}x{height}+{x}+{y}')


from .Popup import PopupWindow, MessageBox


__all__ = ['FlatButton', 'WidgetTable', 'StatusBar', 'PlaceholderEntry', 'PlaceholderCombobox',
           'ToolTip', 'PopupWindow', 'MessageBox', 'placeWindow']
