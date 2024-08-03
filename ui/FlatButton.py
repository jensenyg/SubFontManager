import tkinter as tk
from tkinter import font as tkfont


class FlatButton(tk.Frame):
    # 扁平按钮，没有边框没有底色，只有点击时会偏移一点
    Click_Offsets = (1, 1)    # 点击时x,y方向偏移的量

    def __init__(self, master, text: str, size: int = 26, command=None, **kwargs):
        super().__init__(master, width=22, height=22)
        self.label = tk.Label(self, text=text, font=tkfont.Font(family='Arial', size=size), **kwargs)
        self.label.place(x=0, y=-8)
        self.update_idletasks()
        self.label.bind("<ButtonPress-1>", self.onMouseDown)
        self.label.bind("<ButtonRelease-1>", self.onMouseUp)
        self.command = command

    def onMouseDown(self, event):
        self.label.place(x=self.Click_Offsets[0], y=self.Click_Offsets[1] - 9)

    def onMouseUp(self, event):
        self.label.place(x=0, y=-8)
        if self.command:
            self.command(event)
