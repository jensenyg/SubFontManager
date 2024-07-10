import tkinter as tk
from tkinter import ttk, font as tkfont


class PlaceholderEntry(ttk.Entry):
    def __init__(self, master=None, placeholder=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_fg_color = self['foreground']
        self.isblank = True

        self.bind("<FocusIn>", self._onFocusIn)
        self.bind("<FocusOut>", self._onFocusOut)

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
            super().insert(0, self.placeholder)

    def insert(self, index, string):
        self['foreground'] = self.default_fg_color
        self.configure(font=tkfont.Font(slant='roman'))
        super().insert(index, string)
        self.isblank = self.get() == ''
