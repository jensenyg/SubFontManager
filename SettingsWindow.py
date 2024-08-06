import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import __version__
from Global import AppInfo
from Lang import Lang
import ui


class SettingsWindow(ui.PopupWindow):
    """设置窗口类，包含一些程序基本信息和语言选择选项"""

    def __init__(self, master):
        super().__init__(master, Lang['Settings'])
        ui.placeWindow(self, width=400, height=380, yRatio=0.4)

        # 添加图标
        img_path = os.path.join(AppInfo.getResourcesDirectory(), 'icon', 'icon@128.png')
        img = tk.PhotoImage(file=img_path)
        tk.Label(self, image=img).pack(pady=(10, 0))

        # 添加程序名
        tk.Label(self, text=__version__.name, font=('Arial', 20, tk.font.BOLD)) \
            .pack(side=tk.TOP, padx=20, pady=(0, 10))

        # 添加版本号和作者名
        tk.Label(self, text='Version ' + __version__.version).pack(side=tk.TOP, padx=20)
        tk.Label(self, text='Developed by Jensen').pack(side=tk.TOP, padx=20)

        # 添加Email
        email_frame = tk.Frame(self)
        email_frame.pack(side=tk.TOP, padx=20)
        tk.Label(email_frame, text='Email:').pack(side=tk.LEFT)
        email_label = tk.Label(email_frame, text=__version__.email, fg="blue")
        email_label.pack(side=tk.LEFT)
        email_label.bind("<Button-1>", lambda e: webbrowser.open_new('mailto:' + __version__.email))

        # 添加Github
        github_frame = tk.Frame(self)
        github_frame.pack(side=tk.TOP, padx=20)
        tk.Label(github_frame, text='GitHub:').pack(side=tk.LEFT)
        github_label = tk.Label(github_frame, text=__version__.github, fg="blue")
        github_label.pack(side=tk.LEFT)
        github_label.bind("<Button-1>", lambda e: webbrowser.open_new(__version__.github))

        # 添加语言选择组合框
        lang_frame = tk.Frame(self)
        lang_frame.pack(side=tk.TOP, padx=10, pady=20)
        tk.Label(lang_frame, text=Lang['Language'] + ':').pack(side=tk.LEFT, padx=5)
        self.lang_var = tk.StringVar()
        self.lang_var.set(Lang.currentLang)
        lang_list = Lang.langList
        lang_cmb = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=lang_list, state='readonly')
        lang_cmb.pack(side=tk.LEFT, padx=5, fill=tk.X)

        # 添加OK按钮
        ok_btn = ttk.Button(self, text=Lang['OK'], command=self.close)
        ok_btn.pack()
        ok_btn.focus_set()

        master.wait_window(self)    # 本窗口关闭前父窗口等待

    def close(self):
        new_lang = self.lang_var.get()
        if new_lang != Lang.currentLang:
            Lang.saveSetting(new_lang)
        if new_lang != Lang.initLang:
            if messagebox.askyesno(Lang['Reminding'],
                                   Lang['Language changing requires restart to take effect, restart now?']):
                self.destroy()
                self.master.destroy()
                python = sys.executable
                os.execl(python, python, *sys.argv)
        self.destroy()
