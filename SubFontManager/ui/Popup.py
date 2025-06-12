import tkinter as tk
from tkinter import ttk


def placeWindow(window, x = None, y = None, width = 500, height = 400,
                xRatio: float = 0.5, yRatio: float = 0.5):
    """将窗口放置在指定位置"""
    # 获取父窗口/屏幕宽高
    parent = window.master
    width = int(width)
    height = int(height)
    if x is None:
        if parent:
            x = parent.winfo_x()
            parent_width = parent.winfo_width()
        else:
            x = 0
            parent_width = window.winfo_screenwidth()
        # 计算窗口左边缘位置
        x += int((parent_width - width) * xRatio)
    elif not isinstance(x, int):
        x = int(x)
    if y is None:
        if parent:
            y = parent.winfo_y()
            parent_height = parent.winfo_height()
        else:
            y = 0
            parent_height = window.winfo_screenheight()
        # 计算窗口上边缘位置
        y += int((parent_height - height) * yRatio)
    elif not isinstance(y, int):
        y = int(y)
    # 设置窗口大小和位置
    window.geometry(f'{width}x{height}+{x}+{y}')


class PopupWindow(tk.Toplevel):
    """弹出窗口类"""
    def __init__(self, master, title: str = None):
        super().__init__(master)
        self.title(title)
        self.transient(master)  # 将弹窗设置为主窗口的临时窗口
        self.grab_set()  # 将弹窗设置为模态窗口（阻止与其他窗口的交互）
        self.attributes("-topmost", True)  # 让弹窗始终在前方
        self.wm_attributes("-topmost", 1)
        self.resizable(False, False)


# 自制消息框，暂未启用
class MessageBox(PopupWindow):
    OK = 'ok'
    YESNO = 'yesno'
    Width = 400

    def __init__(self, master, title: str = None, message: str = None, type_: str = OK):
        super().__init__(master, title)
        self.returnValue = None
        # 添加弹窗内容
        gap = 10
        text_label = ttk.Label(self, text=message, wraplength=self.Width - 2 * gap, font=(None, 14))
        text_label.pack(side=tk.TOP, padx=gap, pady=(gap, 0), fill=tk.X)
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.TOP, padx=gap, pady=gap)
        if type_ == self.YESNO:
            btn_1 = ttk.Button(btn_frame, text='Yes', width=5, command=lambda: self.destroy(True))
            btn_1.pack(side=tk.LEFT, padx=gap)
            btn_2 = ttk.Button(btn_frame, text='No', width=5, command=lambda: self.destroy(False))
            btn_2.pack(side=tk.LEFT, padx=gap)
        else:
            btn_1 = ttk.Button(btn_frame, text='OK', width=5, command=self.destroy)
            btn_1.pack(padx=gap)
        height = text_label.winfo_reqheight() + btn_1.winfo_reqheight() + gap * 3
        placeWindow(self, self.Width, height, yRatio=0.4)

    def destroy(self, returnValue=None):
        self.returnValue = returnValue
        super().destroy()

    @classmethod
    def showInfo(cls, master, title: str = None, message: str = None):
        popup = cls(master, title, message, cls.OK)
        master.wait_window(popup)
        return popup.returnValue

    @classmethod
    def askYesNo(cls, master, title: str = None, message: str = None):
        popup = cls(master, title, message, cls.YESNO)
        master.wait_window(popup)
        return popup.returnValue
