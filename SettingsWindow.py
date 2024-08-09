import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import __version__
from App import App
from Lang import Lang
import ui


class SettingsWindow(ui.PopupWindow):
    """设置窗口类，包含一些程序基本信息和语言选择选项"""

    def __init__(self, master):
        super().__init__(master, Lang['Settings'])
        gap = 10 * App.dpiScale
        height = 0    # 手动统计高度，以便在各种DPI下窗口大小都能自动适应

        # 添加图标
        img_path = os.path.join(App.getResourcesDirectory(), 'icon',
                                'icon@256.png' if App.dpiScale > 1 else 'icon@128.png')
        img = tk.PhotoImage(file=img_path)
        text = tk.Label(self, image=img)
        text.pack(pady=(gap, 0))
        height += text.winfo_reqheight() + gap

        # 添加程序名
        text = tk.Label(self, text=__version__.name, font=('Arial', 20, tk.font.BOLD))
        text.pack(side=tk.TOP, padx=gap, pady=(0, gap))
        height += text.winfo_reqheight() + gap

        # 添加版本号和作者名
        tk.Label(self, text='Version ' + __version__.version).pack(side=tk.TOP, padx=gap)
        text = tk.Label(self, text='Developed by Jensen')
        text.pack(side=tk.TOP, padx=gap)
        height += text.winfo_reqheight()

        # 添加Email
        email_frame = tk.Frame(self)
        email_frame.pack(side=tk.TOP, padx=gap)
        tk.Label(email_frame, text='Email:').pack(side=tk.LEFT)
        email_label = tk.Label(email_frame, text=__version__.email, fg="blue")
        email_label.pack(side=tk.LEFT)
        email_label.bind("<Button-1>", lambda e: webbrowser.open_new('mailto:' + __version__.email))
        height += text.winfo_reqheight()

        # 添加Github
        github_frame = tk.Frame(self)
        github_frame.pack(side=tk.TOP, padx=gap)
        tk.Label(github_frame, text='GitHub:').pack(side=tk.LEFT)
        github_label = tk.Label(github_frame, text=__version__.github, fg="blue")
        github_label.pack(side=tk.LEFT)
        github_label.bind("<Button-1>", lambda e: webbrowser.open_new(__version__.github))
        height += text.winfo_reqheight()

        # 添加语言选择组合框
        lang_frame = tk.Frame(self)
        lang_frame.pack(side=tk.TOP, padx=gap, pady=2*gap)
        tk.Label(lang_frame, text=Lang['Language'] + ':').pack(side=tk.LEFT, padx=gap/2)
        self.lang_var = tk.StringVar()
        self.lang_var.set(Lang.currentLang)
        lang_list = Lang.langList
        lang_cmb = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=lang_list, state='readonly')
        lang_cmb.pack(side=tk.LEFT, padx=gap/2, fill=tk.X)
        height += lang_cmb.winfo_reqheight() + 4 * gap

        # 添加OK按钮
        ok_btn = ttk.Button(self, text=Lang['OK'], command=self.close)
        ok_btn.pack()
        ok_btn.focus_set()
        height += ok_btn.winfo_reqheight() + 4 * gap
        
        ui.placeWindow(self, width=400*App.dpiScale, height=height, yRatio=0.4)
        master.wait_window(self)    # 本窗口关闭前父窗口等待

    def close(self):
        new_lang = self.lang_var.get()
        if new_lang != Lang.currentLang:
            Lang.saveSetting(new_lang)
        if new_lang != Lang.initLang and \
            messagebox.askyesno(Lang['Reminding'],
                                Lang['Language changing requires restart to take effect, restart now?'],
                                parent=self):
            self.destroy()
            self.master.destroy()
            python = sys.executable
            os.execl(python, python, *sys.argv)
        self.destroy()
