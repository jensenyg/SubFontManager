import os
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from utils import Version, App, Lang
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
        text = tk.Label(self, text=Version.__appname__, font=('Arial', 20, tk.font.BOLD))
        text.pack(side=tk.TOP, padx=gap, pady=(0, gap))
        height += text.winfo_reqheight() + gap

        # 添加版本号和作者名
        tk.Label(self, text='Version ' + Version.__version__).pack(side=tk.TOP, padx=gap)
        text = tk.Label(self, text='Developed by Jensen')
        text.pack(side=tk.TOP, padx=gap)
        height += text.winfo_reqheight()

        # 添加Email
        email_frame = tk.Frame(self)
        email_frame.pack(side=tk.TOP, padx=gap)
        tk.Label(email_frame, text='Email:').pack(side=tk.LEFT)
        email_label = tk.Label(email_frame, text=Version.__email__, fg="blue")
        email_label.pack(side=tk.LEFT)
        email_label.bind("<Button-1>", lambda e: webbrowser.open_new('mailto:' + Version.__email__))
        height += text.winfo_reqheight()

        # 添加主页
        homepage_frame = tk.Frame(self)
        homepage_frame.pack(side=tk.TOP, padx=gap)
        tk.Label(homepage_frame, text='GitHub:').pack(side=tk.LEFT)
        homepage_label = tk.Label(homepage_frame, text=Version.__homepage__, fg="blue")
        homepage_label.pack(side=tk.LEFT)
        homepage_label.bind("<Button-1>", lambda e: webbrowser.open_new(Version.__homepage__))
        height += text.winfo_reqheight()

        # 添加语言选择组合框
        lang_frame = tk.Frame(self)
        lang_frame.pack(side=tk.TOP, padx=gap, pady=2*gap)
        tk.Label(lang_frame, text=Lang['Language'] + ':').pack(side=tk.LEFT, padx=gap/2)
        self.langVar = tk.StringVar()
        self.langVar.set(Lang.nameInConfig)
        lang_cmb = ttk.Combobox(lang_frame, textvariable=self.langVar, values=list(Lang.allLangs.keys()),
                                state='readonly')
        lang_cmb.pack(side=tk.LEFT, padx=gap/2, fill=tk.X)
        height += lang_cmb.winfo_reqheight() + 4 * gap

        # 添加OK按钮
        ok_btn = ttk.Button(self, text=Lang['OK'], command=self.onOkBtn)
        ok_btn.pack()
        ok_btn.focus_set()
        height += ok_btn.winfo_reqheight() + 4 * gap
        
        ui.placeWindow(self, width=400*App.dpiScale, height=height, yRatio=0.4)
        master.wait_window(self)    # 本窗口关闭前父窗口等待

    def onOkBtn(self):
        new_name = self.langVar.get()
        if new_name != Lang.nameInConfig:
            Lang.Switch(new_name)
        if new_name != Lang.name:
            messagebox.showinfo(Lang['Reminding'], Lang['Language changing takes effect after restart.'], parent=self)
            # 这里不重启，因为tkinter软重启问题多多，os.execl会导致拖放事件失效，subprocess.Popen会导致弹出messagebox时直接崩溃
        self.destroy()
