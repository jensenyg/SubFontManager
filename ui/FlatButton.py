import tkinter as tk


class FlatButton(tk.Frame):
    """扁平按钮，没有边框没有底色，只有点击时会偏移一点点"""

    def __init__(self, master, text: str, command=None, **kwargs):
        super().__init__(master, width=26, height=26)
        self.pack_propagate(False)    # 阻止Frame自动调整尺寸
        self.label = tk.Label(self, text=text, font=('Arial', 26), **kwargs)
        self.label.pack(pady=(0, 3))
        self.label.bind("<ButtonPress-1>", self.onMouseDown)
        self.label.bind("<ButtonRelease-1>", self.onMouseUp)
        self.command = command

    def onMouseDown(self, event):
        self.label.pack(padx=(2, 0), pady=(0, 1))

    def onMouseUp(self, event):
        self.label.pack(padx=0, pady=(0, 3))
        if self.command:
            self.command(event)
