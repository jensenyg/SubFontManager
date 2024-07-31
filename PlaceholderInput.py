import tkinter as tk
from tkinter import ttk, font as tkfont


class PlaceholderEntry(ttk.Entry):
    def __init__(self, master=None, placeholder='', *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_fg_color = self['foreground']
        self.isblank = super().get() == ''

        # self.bind('<Key>', self.onKey)
        self.bind('<FocusIn>', self.onFocusIn)
        self.bind('<FocusOut>', self.onFocusOut)

        if self.placeholder:
            self.onFocusOut()

    def setStyle(self, nomal: bool):
        if nomal:
            self['foreground'] = self.default_fg_color
            self.configure(font=tkfont.Font(slant='roman'))
        else:
            self['foreground'] = self.placeholder_color
            self.configure(font=tkfont.Font(slant='italic'))

    def get(self):
        return '' if self.isblank else super().get()

    def insert(self, index, string):
        self.setStyle(True)
        super().insert(index, string)
        self.isblank = super().get() == ''

    def onKey(self, event):
        self.setStyle(True)
        self.isblank = super().get() == ''

    def onFocusIn(self, event=None):
        if self.isblank:
            self.delete(0, tk.END)
            self.setStyle(True)

    def onFocusOut(self, event=None):
        self.isblank = super().get() == ''
        if self.isblank:
            self.setStyle(False)
            super().insert(0, self.placeholder)


class PlaceholderCombobox(ttk.Combobox):
    def __init__(self, master=None, placeholder='', **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_fg_color = self['foreground']
        self.isblank = self.get() == ''

        self.bind('<FocusIn>', self.onFocusIn)
        self.bind('<FocusOut>', self.onFocusOut)
        # 禁用鼠标滚轮响应
        self.bind('<MouseWheel>', self.onMouseWheel)
        self.bind('<Button-4>', self.onMouseWheel)  # For Linux systems
        self.bind('<Button-5>', self.onMouseWheel)  # For Linux systems

        if self.placeholder:
            self.onFocusOut()

    def setStyle(self, nomal: bool):
        if nomal:
            self['foreground'] = self.default_fg_color
            self.configure(font=tkfont.Font(slant='roman'))
        else:
            self['foreground'] = self.placeholder_color
            self.configure(font=tkfont.Font(slant='italic'))

    def onFocusIn(self, event=None):
        if self.isblank:
            self.delete(0, tk.END)
            self.setStyle(True)

    def onFocusOut(self, event=None):
        self.isblank = super().get() == ''
        if self.isblank:
            self.setStyle(False)
            super().set(self.placeholder)

    def set(self, string):
        self.setStyle(True)
        super().set(string)
        self.isblank = self.get() == ''

    def onMouseWheel(self, e):
        # 让事件跳过本控件，直接传给父控件，即不滚动下拉菜单，直接滚动整个列表
        self.master.event_generate('<MouseWheel>', delta=e.delta)
        # 返回break可以阻止事件进一步传播
        return 'break'
