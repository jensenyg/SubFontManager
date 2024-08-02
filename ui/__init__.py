from .FlatButton import FlatButton
from .WidgetTable import WidgetTable
from .StatusBar import StatusBar
from .PlaceholderInput import PlaceholderEntry, PlaceholderCombobox


def placeWindow(window, width: int = 500, height: int = 400, xRatio: float = 0.5, yRatio: float = 0.5):
    # 获取父窗口/屏幕宽高
    parent = window.master
    if parent:
        x, y = parent.winfo_x(), parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
    else:
        x, y = 0, 0
        parent_width = window.winfo_screenwidth()
        parent_height = window.winfo_screenheight()
    # 计算窗口左上角位置
    x += int((parent_width - width) * xRatio)
    y += int((parent_height - height) * yRatio)
    # 设置窗口大小和位置
    window.geometry(f'{width}x{height}+{x}+{y}')


from .Popup import PopupWindow, MessageBox


__all__ = ['FlatButton', 'WidgetTable', 'StatusBar', 'PlaceholderEntry', 'PlaceholderCombobox',
           'PopupWindow', 'MessageBox', 'placeWindow']
