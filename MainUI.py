import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES
from Lang import Lang
import ui
from FontList import FontList
from FontManager import FontManager
from SubStationAlpha import SubStationAlpha
from ConfigWindow import ConfigWindow


class MainUI:
    def __init__(self, root):
        self.root = root
        self.stopEvent = threading.Event()    # 程序即将关闭事件
        gapy = 2    # 控件垂直间距
        style = ttk.Style()
        style.map('TEntry', fieldbackground=[('!disabled', 'white')])   # 设置所有输入框非禁用内背景色为白色
        # style.map('TCombobox', fieldbackground=[('background', 'red')])   # 设置所有输入框外背景色为白色

        # 文件打开和保存区 ---------------
        file_frame = ttk.Frame(root)
        file_frame.grid(row=0, padx=10, pady=10, sticky="we")

        ttk.Label(file_frame, text=Lang['Input file'] + ':').grid(row=0, column=0, pady=gapy, sticky="w")
        # 这里如果不放在self下，函数执行完后file_entry_text就会被回收，导致事件监听失效
        self.fileEntryText = tk.StringVar()
        self.fileEntry = ttk.Entry(file_frame, textvariable=self.fileEntryText)
        self.fileEntry.grid(row=0, column=1, columnspan=2, padx=(5, 2), pady=(1, 0), sticky="ew")
        self.fileEntry.bind('<Return>', self.onFileEntryEnter)
        self.fileEntryText.trace_add('write', self.onFileEntryInsert)
        tk.Button(file_frame, text="...", command=self.openFile).grid(row=0, column=3, pady=(0, 2))

        ttk.Label(file_frame, text=Lang['Output file'] + ':').grid(row=1, column=0, pady=gapy, sticky="w")
        self.saveMode = tk.IntVar()
        self.saveMode.set(0)
        ttk.Radiobutton(file_frame, text=Lang['Modify source file'], variable=self.saveMode, value=0,
                        command=self.onSwitchSaveMode).grid(row=1, column=1, padx=5, sticky="w")

        # "另存为"Frame，包括一个Radio和一个Entry ----------
        saveas_frame = ttk.Frame(file_frame)
        saveas_frame.grid(row=2, column=1, columnspan=3, sticky="ew")
        ttk.Radiobutton(saveas_frame, text=Lang['Save as'] + ':', variable=self.saveMode, value=1,
                        command=self.onSwitchSaveMode).pack(side=tk.LEFT, padx=5, pady=gapy)
        self.dirEntry = ui.PlaceholderEntry(saveas_frame, placeholder=Lang['Leave blank to save to source directory.'])
        self.dirEntry.configure(state=tk.DISABLED)
        self.dirEntry.pack(side=tk.LEFT, padx=(5, 2), pady=(1, 0), fill=tk.X, expand=True)
        self.openDirBtn = tk.Button(saveas_frame, text="...", state=tk.DISABLED, command=self.openSaveAs)
        self.openDirBtn.pack(side=tk.RIGHT, pady=(0, 2))

        # 配置列权重，使输入框能够随窗口大小变化而变化
        file_frame.columnconfigure(1, weight=1)

        # 字体列表和"载入"按钮 ---------------
        fontlist_frame = ttk.Frame(root)    # "字体列表"Label和"载入"按钮
        fontlist_frame.grid(row=1, padx=5, sticky="we")
        ttk.Label(fontlist_frame, text=Lang['Fonts in the subtitle'] + ':').pack(side=tk.LEFT, padx=5)
        self.loadBtn = tk.Button(fontlist_frame, text=Lang['Load'], width=6, command=self.onLoadBtn, state=tk.DISABLED)
        self.loadBtn.pack(side=tk.RIGHT, padx=5)

        self.fontList = FontList(root)    # 字体列表
        self.fontList.grid(row=2, padx=10, pady=5, sticky="nswe")

        # 底部的状态栏和应用关闭按钮区 --------------
        bottom_frame = ttk.Frame(root)
        bottom_frame.grid(row=3, padx=10, pady=(0, 10), sticky="ew")
        status_label = ttk.Label(bottom_frame)
        status_label.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        ui.StatusBar.setLabel(status_label)

        ttk.Button(bottom_frame, text=Lang['Close'], width=5, command=root.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text=Lang['Apply'], width=5, command=self.onApplyBtn).pack(side=tk.RIGHT, padx=5)
        ui.FlatButton(bottom_frame, text='⚙', fg='#645D56', command=self.showConfig).pack(side=tk.RIGHT, padx=10)

        # 配置列权重，使列表框能够随窗口大小变化而变化
        root.rowconfigure(2, weight=1)
        root.columnconfigure(0, weight=1)

        # 绑定拖放事件到窗口
        root.drop_target_register(DND_FILES)
        root.dnd_bind('<<Drop>>', self.onDrop)

        # 绑定<Destroy>事件
        root.bind("<Destroy>", self.onDestroy)

        # 用新线程索引系统字体
        threading.Thread(target=FontManager.initSystemFontList, kwargs={'stopEvent': self.stopEvent}).start()

    def openFile(self):
        file_name = filedialog.askopenfilename(
            filetypes=[("[Advanced] SubStation Alpha", ".ass .ssa"), ("All files", "*.*")])
        if file_name:
            self.fileEntryText.set(file_name)
        self.root.focus_force()    # 不用force有时焦点抢不回来
        self.onLoadBtn()

    def openSaveAs(self):
        file_path = filedialog.asksaveasfilename(
            initialdir=".",
            initialfile="newsubtitle",
            defaultextension=".ass",
            filetypes=[("[Advanced] SubStation Alpha", ".ass .ssa"), ("All files", "*.*")]
        )
        if file_path:
            self.dirEntry.delete(0, tk.END)
            self.dirEntry.insert(0, file_path)
        self.root.focus_force()    # 不用force有时焦点抢不回来

    def onDrop(self, event):
        file_path = event.data.strip('{}')
        if not file_path.endswith(('.ass', '.ssa')):
            messagebox.showerror(Lang['Error'], Lang['Only .ass and .ssa file are supported.'])
            return
        self.fileEntry.delete(0, tk.END)
        self.fileEntry.insert(0, event.data)
        self.onLoadBtn()

    def onSwitchSaveMode(self):
        self.dirEntry.configure(state=tk.DISABLED if self.saveMode.get() == 0 else tk.NORMAL, background='red')
        self.openDirBtn.configure(state=tk.DISABLED if self.saveMode.get() == 0 else tk.NORMAL)

    def onFileEntryInsert(self, *args):
        self.loadBtn.configure(state=tk.NORMAL if self.fileEntry.get() else tk.DISABLED)

    def onFileEntryEnter(self, *args):
        self.onLoadBtn()

    def onLoadBtn(self, *args):
        path = self.fileEntry.get()
        # StatusBar.set('正在解析文件...')
        subtitleObj = SubStationAlpha.load(path)
        if subtitleObj:
            # StatusBar.set('正在查找字体文件...')
            self.fontList.loadSubtitle(subtitleObj)
            self.loadBtn.configure(text=Lang['Load'] if subtitleObj is None else Lang['Reload'], state=tk.NORMAL)
        # StatusBar.set('文件载入完成.', 3)

    def onApplyBtn(self, *args):
        res = self.fontList.applyEmbedding(self.dirEntry.get())
        self.root.focus_set()   # applyEmbeding中可能会有弹窗，需手动取回焦点
        if res != 1 and self.dirEntry.isblank:    # 如果嵌入成功且是覆盖原文件，则重新载入
            self.onLoadBtn()

    def showConfig(self, event):
        ConfigWindow(self.root)

    def onDestroy(self, event):
        if self.stopEvent.is_set():    # 窗口关闭时Destroy事件会被触发很多次，只响应一次即可
            return
        self.stopEvent.set()    # 设置停止事件，让可能正在检索字体的线程尽快停止
