import tkinter as tk
from tkinter import ttk, font as tkfont
from App import App


class Widget:
    bg = 'white'    # 全局背景色
    style = None
    defaultFont = None

    @classmethod
    def initStyle(cls, style):
        cls.style = style
        cls.defaultFont = tkfont.nametofont("TkDefaultFont")
        # cls.defaultFont.configure(size=cls.defaultFont.actual('size') + 1)

    def setBackground(self, color: str = None):
        pass


class Button(ttk.Button):
    def __init__(self, master: tk.Misc, **kwargs):
        if 'width' in kwargs:
            kwargs['width'] = int(kwargs['width'])
        if 'height' in kwargs:
            kwargs['height'] = int(kwargs['height'])
        super().__init__(master, **kwargs)


class Label(tk.Label, Widget):
    """标签类，以统一的借口更改背景色"""

    def __init__(self, master: tk.Misc, **kwargs):
        kwargs['bg'] = kwargs.get('bg', self.bg)
        super().__init__(master, **kwargs)

    def setBackground(self, color: str = Widget.bg):
        self.configure(background=color)

    def setBold(self, bold: bool = True):
        new_font = self.defaultFont.copy()
        new_font.configure(weight=tkfont.BOLD if bold else tkfont.NORMAL)
        tk.Label.configure(self, font=new_font)


class Checkbox(ttk.Checkbutton, tk.Checkbutton, Widget):
    """复选框类，以统一的借口更改背景色"""

    @classmethod
    def initStyle(cls, style):
        Widget.initStyle(style)
        style.configure('TCheckbutton', background=Checkbox.bg)  # 设置复选框背景色

    def __init__(self, master: tk.Misc, **kwargs):
        self.isMac = App.platform == App.MACOS
        if self.isMac:
            kwargs['bg'] = kwargs.get('bg', self.bg)
            tk.Checkbutton.__init__(self, master, **kwargs)
        else:
            kwargs['style'] = kwargs.get('style', 'TCheckbutton')
            kwargs.pop('anchor', None)
            ttk.Checkbutton.__init__(self, master, **kwargs)

    def setBackground(self, color: str = Widget.bg):
        if self.isMac:
            tk.Checkbutton.configure(self, background=color)
        else:
            style_name = 'TCheckbutton' if color == self.bg else (color + '.TCheckbutton')
            self.style.configure(style_name, background=color)
            ttk.Checkbutton.configure(self, style=style_name)


class Entry(ttk.Entry, Widget):
    """输入框类，支持占位符，当内容为空时会显示灰色的占位符文字"""

    @classmethod
    def initStyle(cls, style):
        Widget.initStyle(style)
        style.map('TEntry', fieldbackground=[('!disabled', 'white')])  # 设置输入框非禁用内背景色为白色

    def __init__(self, master: tk.Misc = None, placeholder: str = '', *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._isblank = True
        self.focusIn = False
        self._init(placeholder)

    def _init(self, placeholder):
        self.placeholder = placeholder
        self.placeholder_color = 'darkgray'
        self.default_fg_color = self['foreground']
        self.bind('<FocusIn>', self.onFocusIn)
        self.bind('<FocusOut>', self.onFocusOut)
        if self.placeholder:
            self.onFocusOut()

    def setStyle(self, nomal: bool):
        new_font = self.defaultFont.copy()
        if nomal:
            self['foreground'] = self.default_fg_color
            new_font.configure(slant=tkfont.ROMAN)
        else:
            self['foreground'] = self.placeholder_color
            new_font.configure(slant=tkfont.ITALIC)    # 中文斜体需要字体支持，可能无法显示
        self.configure(font=new_font)

    def get(self):
        return '' if self._isblank else super().get()

    def getRaw(self):
        return super().get()

    @property
    def isblank(self):
        return self._isblank

    def insert(self, index, string):
        self.setStyle(True)
        super().insert(index, string)
        self._isblank = super().get() == ''

    def onFocusIn(self, event=None):
        self.focusIn = True
        if self._isblank:
            self.delete(0, tk.END)
            self.setStyle(True)

    def onFocusOut(self, event=None):
        self.focusIn = False
        self._isblank = super().get() == ''
        if self._isblank:
            self.setStyle(False)
            super().insert(0, self.placeholder)


class Combobox(ttk.Combobox, Entry):
    """组合框类，支持占位符，当内容为空时会显示灰色的占位符文字"""

    # @classmethod
    # def initStyle(cls, style):
    #     Widget.initStyle(style)
    #     style.map('TCombobox', fieldbackground=[('background', 'red')])  # 设置输入框外背景色为白色

    def __init__(self, master: tk.Misc = None, placeholder: str = '', *args, **kwargs):
        variable = kwargs.get('textvariable')
        super().__init__(master, *args, **kwargs)

        self._isblank = True
        # 保存初始值和通过set设置的当前值，以便在被下拉菜单自动改写后可以回填
        self.currentValue = variable.get() if variable else ''
        self._init(placeholder)
        # 禁用鼠标滚轮响应
        self.bind('<MouseWheel>', self.onMouseWheel)
        self.bind('<Button-4>', self.onMouseWheel)  # For Linux systems
        self.bind('<Button-5>', self.onMouseWheel)  # For Linux systems

    def set(self, string):
        self._isblank = string == ''
        self.setStyle(not self._isblank)
        super().set(self.placeholder if self._isblank else string)
        self.currentValue = self.get()

    @property
    def isblank(self):
        if self.focusIn:
            self._isblank = ttk.Combobox.get(self) == ''
        return self._isblank

    def onMouseWheel(self, event):
        # 让事件跳过本控件，直接传给父控件，即不滚动下拉菜单，直接滚动整个列表
        self.master.event_generate('<MouseWheel>', delta=event.delta)
        # 返回break可以阻止事件进一步传播
        return 'break'

    def setBackground(self, color: str = Widget.bg):
        style_name = 'TCombobox' if color == self.bg else (color + '.TCombobox')
        self.style.configure(style_name, background=color)
        ttk.Combobox.configure(self, style=style_name)
