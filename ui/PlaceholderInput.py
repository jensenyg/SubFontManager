import tkinter as tk
from tkinter import ttk, font as tkfont


class PlaceholderEntry(ttk.Entry):
    """带有占位符的输入框，当内容为空时会显示灰色的占位符文字"""
    def __init__(self, master=None, placeholder: str = '', *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.isblank = True
        self._init(placeholder)

    def _init(self, placeholder):
        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_fg_color = self['foreground']
        self.bind('<FocusIn>', self.onFocusIn)
        self.bind('<FocusOut>', self.onFocusOut)
        if self.placeholder:
            self.onFocusOut()

    def setStyle(self, nomal: bool):
        if nomal:
            self['foreground'] = self.default_fg_color
            self.configure(font=tkfont.Font(slant=tkfont.ROMAN))
        else:
            self['foreground'] = self.placeholder_color
            self.configure(font=tkfont.Font(slant=tkfont.ITALIC))    # 中文斜体需要字体支持，可能无法显示

    def get(self):
        return '' if self.isblank else super().get()

    def getRaw(self):
        return super().get()

    def insert(self, index, string):
        self.setStyle(True)
        super().insert(index, string)
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


class PlaceholderCombobox(ttk.Combobox, PlaceholderEntry):
    """带有占位符的组合框，当内容为空时会显示灰色的占位符文字"""
    def __init__(self, master=None, placeholder='', *args, **kwargs):
        variable = kwargs.get('textvariable')
        super().__init__(master, *args, **kwargs)

        self.isblank = True
        # 保存初始值和通过set设置的当前值，以便在被下拉菜单自动改写后可以回填
        self.currentValue = variable.get() if variable else ''
        self._init(placeholder)
        # 禁用鼠标滚轮响应
        self.bind('<MouseWheel>', self.onMouseWheel)
        self.bind('<Button-4>', self.onMouseWheel)  # For Linux systems
        self.bind('<Button-5>', self.onMouseWheel)  # For Linux systems

    def set(self, string):
        self.isblank = string == ''
        self.setStyle(not self.isblank)
        super().set(self.placeholder if self.isblank else string)
        self.currentValue = self.get()

    def onMouseWheel(self, e):
        # 让事件跳过本控件，直接传给父控件，即不滚动下拉菜单，直接滚动整个列表
        self.master.event_generate('<MouseWheel>', delta=e.delta)
        # 返回break可以阻止事件进一步传播
        return 'break'
