import tkinter as tk
from tkinter import ttk, font as tkfont


class PlaceholderEntry(ttk.Entry):
    def __init__(self, master=None, placeholder='', *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_fg_color = self['foreground']
        self.isblank = super().get() == ''

        self.bind('<FocusIn>', self._onFocusIn)
        self.bind('<FocusOut>', self._onFocusOut)

        if self.placeholder:
            self._onFocusOut()

    def get(self):
        return '' if self.isblank else super().get()

    def insert(self, index, string):
        self['foreground'] = self.default_fg_color
        self.configure(font=tkfont.Font(slant='roman'))
        super().insert(index, string)
        self.isblank = super().get() == ''

    def _onFocusIn(self, event=None):
        if self.isblank:
            self.delete(0, tk.END)
            self['foreground'] = self.default_fg_color
            self.configure(font=tkfont.Font(slant='roman'))

    def _onFocusOut(self, event=None):
        self.isblank = self.get() == ''
        if self.isblank:
            self['foreground'] = self.placeholder_color
            self.configure(font=tkfont.Font(slant='italic'))
            super().insert(0, self.placeholder)


class PlaceholderCombobox(ttk.Combobox):
    def __init__(self, master=None, placeholder='', **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_fg_color = self['foreground']
        self.isblank = self.get() == ''

        self.bind('<FocusIn>', self._onFocusIn)
        self.bind('<FocusOut>', self._onFocusOut)
        # 禁用鼠标滚轮响应
        self.bind('<MouseWheel>', self.onMouseWheel)
        self.bind('<Button-4>', self.onMouseWheel)  # For Linux systems
        self.bind('<Button-5>', self.onMouseWheel)  # For Linux systems

        if self.placeholder:
            self._onFocusOut()

    def _onFocusIn(self, event=None):
        if self.isblank:
            self.delete(0, tk.END)
            self['foreground'] = self.default_fg_color
            self.configure(font=tkfont.Font(slant='roman'))

    def _onFocusOut(self, event=None):
        self.isblank = self.get() == ''
        if self.isblank:
            self['foreground'] = self.placeholder_color
            self.configure(font=tkfont.Font(slant='italic'))
            super().set(self.placeholder)

    def set(self, string):
        self['foreground'] = self.default_fg_color
        self.configure(font=tkfont.Font(slant='roman'))
        super().set(string)
        self.isblank = self.get() == ''

    def onMouseWheel(self, e):
        # 让事件跳过本控件，直接传给父控件
        self.master.event_generate('<MouseWheel>', delta=e.delta)
        # 返回break可以阻止事件进一步传播
        return 'break'
