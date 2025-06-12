import tkinter as tk
from utils import App


class FlatButton(tk.Frame):
    """扁平按钮，没有边框没有底色，只有点击时会偏移一点点"""

    def __init__(self, master, text: str, command=None, **kwargs):
        super().__init__(master, width=26*App.dpiScale, height=26*App.dpiScale)
        self.pack_propagate(False)    # 阻止Frame自动调整尺寸
        if App.isMac:
            self.label = tk.Label(self, text=text, font=('Arial', 26), **kwargs)
            self.label.pack(pady=(0, 3))
        else:
            self.label = tk.Label(self, text=text, font=('Segoe UI Symbol', 16), **kwargs)
            self.label.pack(pady=(0, 4))
        self.label.bind("<ButtonPress-1>", self.onMouseDown)
        self.label.bind("<ButtonRelease-1>", self.onMouseUp)
        self.command = command

    def onMouseDown(self, event):
        self.label.pack_configure(padx=(2, 0), pady=(0, 1) if App.isMac else (0, 3))

    def onMouseUp(self, event):
        self.label.pack_configure(padx=0, pady=(0, 3) if App.isMac else (0, 4))
        if self.command:
            self.command(event)
