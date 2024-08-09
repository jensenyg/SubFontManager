import os.path
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES
from App import App
from Lang import Lang
import ui
from FontList import FontList
from FontManager import FontManager
from SubStationAlpha import SubStationAlpha
from SettingsWindow import SettingsWindow


class MainUI:
    def __init__(self, root):
        self.root = root
        self.stopEvent = threading.Event()    # 程序即将关闭事件
        gap = 2 * App.dpiScale        # 控件垂直间距
        padding = 5 * App.dpiScale    # 窗口边缘距离
        ui.init()

        # 文件打开和保存区 ---------------
        file_frame = ttk.Frame(root)
        file_frame.grid(row=0, padx=2*padding, pady=(2*padding, padding), sticky="we")

        ttk.Label(file_frame, text=Lang['Input file'] + ':').grid(row=0, column=0, pady=gap, sticky="w")
        # 这里如果不放在self下，函数执行完后file_entry_text就会被回收，导致事件监听失效
        self.fileEntryText = tk.StringVar()
        self.fileEntry = ttk.Entry(file_frame, textvariable=self.fileEntryText)
        self.fileEntry.grid(row=0, column=1, columnspan=2, padx=(padding, gap), pady=(1, 0), sticky="ew")
        self.fileEntry.bind('<Return>', self.onFileEntryEnter)
        self.fileEntryText.trace_add('write', self.onFileEntryInsert)
        btn_width = 0 if App.platform == App.MACOS else 2 * App.dpiScale
        ui.Button(file_frame, text="...", width=btn_width, command=self.openFile).grid(row=0, column=3, pady=(0, 2))

        ttk.Label(file_frame, text=Lang['Output file'] + ':').grid(row=1, column=0, pady=gap, sticky="w")
        self.saveMode = tk.IntVar()
        self.saveMode.set(0)
        ttk.Radiobutton(file_frame, text=Lang['Modify source file'], variable=self.saveMode, value=0,
                        command=self.onSwitchSaveMode).grid(row=1, column=1, padx=padding, sticky="w")

        # "另存为"Frame，包括一个Radio和一个Entry ----------
        saveas_frame = ttk.Frame(file_frame)
        saveas_frame.grid(row=2, column=1, columnspan=3, sticky="ew")
        ttk.Radiobutton(saveas_frame, text=Lang['Save as'] + ':', variable=self.saveMode, value=1,
                        command=self.onSwitchSaveMode).pack(side=tk.LEFT, padx=padding, pady=gap)
        self.dirEntry = ui.Entry(saveas_frame, placeholder=Lang['Leave blank to save to source directory.'])
        self.dirEntry.configure(state=tk.DISABLED)
        self.dirEntry.pack(side=tk.LEFT, padx=(padding, gap), pady=(1, 0), fill=tk.X, expand=True)
        self.openDirBtn = ui.Button(saveas_frame, text="...", width=btn_width, state=tk.DISABLED,
                                    command=self.openSaveAs)
        self.openDirBtn.pack(side=tk.RIGHT, pady=(0, 2))

        # 配置列权重，使输入框能够随窗口大小变化而变化
        file_frame.columnconfigure(1, weight=1)

        # 字体列表和"载入"按钮 ---------------
        fontlist_frame = ttk.Frame(root)    # "字体列表"Label和"载入"按钮
        fontlist_frame.grid(row=1, padx=padding, sticky="we")
        ttk.Label(fontlist_frame, text=Lang['Fonts in the subtitle'] + ':').pack(side=tk.LEFT, padx=padding)
        self.loadBtn = ui.Button(fontlist_frame, text=Lang['Load'], width=6*App.dpiScale, state=tk.DISABLED,
                                 command=self.onLoadBtn)
        self.loadBtn.pack(side=tk.RIGHT, padx=5)

        self.fontList = FontList(root)    # 字体列表
        self.fontList.grid(row=2, padx=2*padding, pady=padding, sticky="nswe")

        # 底部的状态栏和应用关闭按钮区 --------------
        bottom_frame = ttk.Frame(root)
        bottom_frame.grid(row=3, padx=2*padding, pady=(0, 2*padding), sticky="ew")
        status_label = ttk.Label(bottom_frame)
        status_label.pack(side=tk.LEFT, padx=(0, padding), fill=tk.X, expand=True)
        ui.StatusBar.setLabel(status_label)

        ui.Button(bottom_frame, text=Lang['Close'], width=5*App.dpiScale, command=root.destroy) \
            .pack(side=tk.RIGHT, padx=padding)
        ui.Button(bottom_frame, text=Lang['Apply'], width=5*App.dpiScale, command=self.onApplyBtn) \
            .pack(side=tk.RIGHT, padx=padding)
        config_btn = ui.FlatButton(bottom_frame, text='⚙', fg='#645D56', command=self.showSettings)
        config_btn.pack(side=tk.RIGHT, padx=padding)
        ui.ToolTip(config_btn, Lang['Settings'])

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
        """点击打开文件"""
        file_name = filedialog.askopenfilename(
            filetypes=[("[Advanced] SubStation Alpha", ".ass .ssa"), ("All files", "*.*")])
        if file_name:
            self.fileEntry.delete(0, tk.END)
            self.fileEntry.insert(0, file_name)
            self.onLoadBtn()
        self.fileEntry.focus_set()

    def openSaveAs(self):
        """点击另存为"""
        base_path = self.dirEntry.get()
        if not base_path:
            base_path = self.fileEntry.get()
        file_path = filedialog.asksaveasfilename(
            initialdir=os.path.dirname(base_path),
            initialfile="newsubtitle",
            defaultextension=".ass",
            filetypes=[("[Advanced] SubStation Alpha", ".ass .ssa"), ("All files", "*.*")]
        )
        self.dirEntry.focus_set()
        if file_path:
            self.dirEntry.delete(0, tk.END)
            self.dirEntry.insert(0, file_path)

    def onDrop(self, event):
        """拖放文件响应"""
        file_path = event.data.strip('{}')
        if not file_path.endswith(('.ass', '.ssa')):
            messagebox.showerror(Lang['Error'], Lang['Only .ass and .ssa file are supported.'])
            self.root.focus_set()
            return
        self.fileEntry.delete(0, tk.END)
        self.fileEntry.insert(0, event.data)
        self.onLoadBtn()

    def onSwitchSaveMode(self):
        """点击切换保存位置"""
        self.dirEntry.configure(state=tk.DISABLED if self.saveMode.get() == 0 else tk.NORMAL, background='red')
        self.openDirBtn.configure(state=tk.DISABLED if self.saveMode.get() == 0 else tk.NORMAL)

    def onFileEntryInsert(self, *args):
        """输入文件框值改变响应"""
        self.loadBtn.configure(state=tk.NORMAL if self.fileEntry.get() else tk.DISABLED)

    def onFileEntryEnter(self, *args):
        """输入文件框回车响应"""
        if self.fileEntry.get():
            self.onLoadBtn()

    def onLoadBtn(self, status: bool = True):
        """status: 是否输出状态栏信息"""
        subtitleObj = SubStationAlpha.load(self.fileEntry.get())
        if subtitleObj:
            self.fontList.loadSubtitle(subtitleObj)
            self.loadBtn.configure(text=Lang['Load'] if subtitleObj is None else Lang['Reload'], state=tk.NORMAL)
            if status and not FontManager.isIndexing:   # 索引字体时不输出状态栏，否则会冲掉“正在索引”的信息
                ui.StatusBar.set(Lang['File loaded'] + '.', 3)
        else:
            self.root.focus_set()   # load中可能有弹窗，需手动取回焦点

    def onApplyBtn(self, status: bool = True):
        """
        点击应用按钮。
        status: 是否输出状态栏信息
        """
        res = self.fontList.applyEmbedding(self.dirEntry.get())
        if res != 0:
            self.root.focus_set()  # applyEmbeding中可能会有弹窗，需手动取回焦点
        if res != 1:    # 如果有字体嵌入成功
            if status:
                ui.StatusBar.set(Lang['Finished'] + '. ', 3)
            if self.dirEntry.isblank:    # 如果覆盖原文件，则重新载入
                self.onLoadBtn()
                if status:
                    ui.StatusBar.append(Lang['File reloaded'] + '.', 3)

    def showSettings(self, event):
        """点击设置按钮"""
        SettingsWindow(self.root)

    def onDestroy(self, event):
        """关闭窗口响应"""
        if event.widget is self.root:   # Destroy事件也会冒泡上浮，需要筛选响应
            self.stopEvent.set()    # 设置停止事件，让可能正在检索字体的线程尽快停止
