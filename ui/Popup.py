import tkinter as tk
from tkinter import ttk, font as tkfont
from . import placeWindow


class PopupWindow(tk.Toplevel):
    def __init__(self, master, title: str = None):
        super().__init__(master)
        self.title(title)
        self.transient(master)  # 将弹窗设置为主窗口的临时窗口
        self.grab_set()  # 将弹窗设置为模态窗口（阻止与其他窗口的交互）
        self.attributes("-topmost", True)  # 让弹窗始终在前方
        # self.wm_attributes("-topmost", 1)
        self.resizable(False, False)


class MessageBox(PopupWindow):
    OK = 'ok'
    YESNO = 'yesno'
    Width = 400

    def __init__(self, master, title: str = None, message: str = None, type_: str = OK):
        super().__init__(master, title)
        self.returnValue = None
        # 添加弹窗内容
        gap = 10
        text_label = ttk.Label(self, text=message, wraplength=self.Width - 2 * gap,
                               font=tkfont.Font(size=14))
        text_label.pack(side=tk.TOP, padx=gap, pady=(gap, 0), fill=tk.X)
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.TOP, padx=gap, pady=gap)
        if type_ == self.YESNO:
            btn_1 = ttk.Button(btn_frame, text='是', width=5, command=lambda: self.destroy(True))
            btn_1.pack(side=tk.LEFT, padx=gap)
            btn_2 = ttk.Button(btn_frame, text='否', width=5, command=lambda: self.destroy(False))
            btn_2.pack(side=tk.LEFT, padx=gap)
        else:
            btn_1 = ttk.Button(btn_frame, text='确定', width=5, command=self.destroy)
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

