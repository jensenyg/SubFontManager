"""提供基本UI控件"""

from tkinter import ttk
from .Widgets import Button, Label, Checkbox, Entry, Combobox
from .FlatButton import FlatButton
from .WidgetTable import WidgetTable
from .StatusBar import StatusBar
from .ToolTip import ToolTip
from .Popup import PopupWindow, placeWindow


def init():
    """初始化几类控件的统一样式"""
    style = ttk.Style()
    # Label.initStyle(style)
    Checkbox.initStyle(style)
    Combobox.initStyle(style)


__all__ = ['Button', 'Label', 'Checkbox', 'FlatButton', 'WidgetTable', 'StatusBar', 'Entry',
           'Combobox', 'ToolTip', 'PopupWindow', 'placeWindow', 'init']
