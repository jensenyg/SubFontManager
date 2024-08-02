import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import __version__
import ui


class ConfigWindow(ui.PopupWindow):
    def __init__(self, master):
        super().__init__(master, '设置')
        ui.placeWindow(self, 400, 255, yRatio=0.4)

        # 添加弹窗内容 -----------------
        tk.Label(self, text=__version__.name, font=tkfont.Font(family='Arial', size=20, weight=tkfont.BOLD)) \
            .pack(side=tk.TOP, padx=20, pady=(20, 10))

        tk.Label(self, text='Version ' + __version__.version).pack(side=tk.TOP, padx=20)
        tk.Label(self, text='Developed by Jensen').pack(side=tk.TOP, padx=20)

        email_frame = tk.Frame(self)
        email_frame.pack(side=tk.TOP, padx=20)
        tk.Label(email_frame, text='Email:').pack(side=tk.LEFT)
        email_label = tk.Label(email_frame, text=__version__.email, fg="blue")
        email_label.pack(side=tk.LEFT)
        email_label.bind("<Button-1>", lambda e: webbrowser.open_new('mailto:' + __version__.email))

        github_frame = tk.Frame(self)
        github_frame.pack(side=tk.TOP, padx=20)
        tk.Label(github_frame, text='GitHub:').pack(side=tk.LEFT)
        github_label = tk.Label(github_frame, text=__version__.github, fg="blue")
        github_label.pack(side=tk.LEFT)
        github_label.bind("<Button-1>", lambda e: webbrowser.open_new(__version__.github))

        lang_frame = tk.Frame(self)
        lang_frame.pack(side=tk.TOP, padx=10, pady=20)
        tk.Label(lang_frame, text='语言:').pack(side=tk.LEFT, padx=5)
        lang_var = tk.StringVar()
        lang_list = ['English', '简体中文']
        lang_cmb = ttk.Combobox(lang_frame, textvariable=lang_var, values=lang_list, state='readonly')
        lang_cmb.pack(side=tk.LEFT, padx=5, fill=tk.X)
        lang_cmb.current(1)

        ttk.Button(self, text="确定", command=self.close).pack()

        master.wait_window(self)

    def close(self):
        if messagebox.askyesno('提示', '语言更改需重启生效，是否立刻重启？'):
            self.destroy()
            python = sys.executable
            os.execl(python, python, *sys.argv)
        else:
            self.destroy()
