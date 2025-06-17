import tkinter as tk
from tkinter import ttk, font as tkfont, Event
from utils import App


class StyledWidget:
    """统一样式基类，继承此类的控件可以调用同样的样式风格，用于让字体表内的所有控件背景色统一"""
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
    """按钮类，为了让width和height参数可以自动适应多种数据类型"""

    def __init__(self, master: tk.Misc, **kwargs):
        if 'width' in kwargs:
            kwargs['width'] = int(kwargs['width'])
        if 'height' in kwargs:
            kwargs['height'] = int(kwargs['height'])
        super().__init__(master, **kwargs)


class Label(tk.Label, StyledWidget):
    """标签类，以统一的接口更改背景色"""

    def __init__(self, master: tk.Misc, **kwargs):
        overstrike = kwargs.pop('overstrike', False)
        kwargs['bg'] = kwargs.get('bg', self.bg)
        super().__init__(master, **kwargs)
        self.font = StyledWidget.defaultFont.copy()
        if overstrike:
            self.font.configure(overstrike=overstrike)
            self.configure(font=self.font)

    def setBackground(self, color: str = StyledWidget.bg):
        self.configure(background=color)

    def setBold(self, bold: bool = True):
        self.font.configure(weight=tkfont.BOLD if bold else tkfont.NORMAL)
        self.configure(font=self.font)


class Checkbox(ttk.Checkbutton, tk.Checkbutton, StyledWidget):
    """复选框类，以统一的接口更改背景色"""

    @classmethod
    def initStyle(cls, style):
        StyledWidget.initStyle(style)
        style.configure('TCheckbutton', background=Checkbox.bg)  # 设置复选框背景色

    def __init__(self, master: tk.Misc, **kwargs):
        if App.isMac:
            kwargs['bg'] = kwargs.get('bg', self.bg)
            tk.Checkbutton.__init__(self, master, **kwargs)
        else:
            kwargs['style'] = kwargs.get('style', 'TCheckbutton')
            kwargs.pop('anchor', None)
            ttk.Checkbutton.__init__(self, master, **kwargs)

    def setBackground(self, color: str = StyledWidget.bg):
        if App.isMac:
            tk.Checkbutton.configure(self, background=color)
        else:
            style_name = 'TCheckbutton' if color == self.bg else (color + '.TCheckbutton')
            self.style.configure(style_name, background=color)
            ttk.Checkbutton.configure(self, style=style_name)


class Entry(ttk.Entry, StyledWidget):
    """输入框类，支持占位符，当内容为空时会显示灰色的占位符文字"""

    @classmethod
    def initStyle(cls, style):
        StyledWidget.initStyle(style)
        style.map('TEntry', fieldbackground=[('!disabled', 'white')])  # 设置输入框非禁用内背景色为白色

    def __init__(self, master: tk.Misc = None, placeholder: str = '', *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._isblank = True    # 框内是否为空，占位符不算
        self._focusIn = False   # 是否拥有焦点
        self._init(placeholder)

    def _init(self, placeholder):
        self.placeholder = placeholder
        self.placeholderColor = 'darkgray'
        self.defaultFgColor = self['foreground']
        self.bind('<FocusIn>', self.onFocusIn)
        self.bind('<FocusOut>', self.onFocusOut)
        if self.placeholder:
            self.onFocusOut()

    def setStyle(self, nomal: bool):
        new_font = self.defaultFont.copy()
        if nomal:
            self['foreground'] = self.defaultFgColor
            new_font.configure(slant=tkfont.ROMAN)
        else:
            self['foreground'] = self.placeholderColor
            new_font.configure(slant=tkfont.ITALIC)    # 中文斜体需要字体支持，可能无法显示
        self.configure(font=new_font)

    def get(self):
        """获取框内内容，占位符不算"""
        return '' if self._isblank else super().get()

    def getRaw(self):
        """获取框内原始内容，包括占位符"""
        return super().get()

    @property
    def isBlank(self):
        """框内是否为空，占位符不算"""
        return self._isblank

    def insert(self, index, string):
        """插入文字"""
        self.setStyle(True)
        super().insert(index, string)
        self._isblank = super().get() == ''

    def onFocusIn(self, event: Event = None):
        """焦点进入事件响应"""
        self._focusIn = True
        if self._isblank:
            self.delete(0, tk.END)
            self.setStyle(True)

    def onFocusOut(self, event: Event = None):
        """焦点离开事件响应"""
        self._focusIn = False
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
        # 初始化占位符输入框属性
        self._isblank = True    # 框内是否为空，占位符不算
        self._focusIn = False   # 是否拥有焦点
        self._init(placeholder)
        # 保存初始值和通过set设置的当前值，以便在被下拉菜单自动改写后可以回填
        self.currentValue = variable.get() if variable else ''
        # 禁用鼠标滚轮响应
        self.bind('<MouseWheel>', self.onMouseWheel)
        self.bind('<Button-4>', self.onMouseWheel)  # For Linux systems
        self.bind('<Button-5>', self.onMouseWheel)  # For Linux systems

    def set(self, string):
        """设置框内文字"""
        self._isblank = string == ''
        self.setStyle(not self._isblank)
        super().set(self.placeholder if self._isblank else string)
        self.currentValue = self.get()

    @property
    def isBlank(self):
        """框内是否为空，占位符不算"""
        if self._focusIn:
            self._isblank = ttk.Combobox.get(self) == ''
        return self._isblank

    def onMouseWheel(self, event: Event):
        """鼠标滚应事件响应"""
        # 让事件跳过本控件，直接传给父控件，即不滚动下拉菜单，直接滚动整个列表
        self.master.event_generate('<MouseWheel>', delta=event.delta)
        # 返回break可以阻止事件进一步传播
        return 'break'

    def setBackground(self, color: str = StyledWidget.bg):
        style_name = 'TCombobox' if color == self.bg else (color + '.TCombobox')
        self.style.configure(style_name, background=color)
        ttk.Combobox.configure(self, style=style_name)
