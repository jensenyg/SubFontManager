import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import __version__
from Lang import Lang
import ui


class ConfigWindow(ui.PopupWindow):
    def __init__(self, master):
        super().__init__(master, Lang['Settings'])
        ui.placeWindow(self, width=400, height=255, yRatio=0.4)

        # 添加弹窗内容 -----------------
        tk.Label(self, text=__version__.name, font=('Arial', 20, tk.font.BOLD)) \
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
        tk.Label(lang_frame, text=Lang['Language'] + ':').pack(side=tk.LEFT, padx=5)
        self.lang_var = tk.StringVar()
        self.lang_var.set(Lang.currentLang)
        lang_list = Lang.langList
        lang_cmb = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=lang_list, state='readonly')
        lang_cmb.pack(side=tk.LEFT, padx=5, fill=tk.X)

        ttk.Button(self, text=Lang['OK'], command=self.close).pack()

        master.wait_window(self)

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
