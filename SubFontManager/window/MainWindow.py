import os.path
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from utils import App, Lang
import ui
from font import SubStationAlpha
from .FontList import FontList
from .SettingsWindow import SettingsWindow


class MainWindow:
    """主界面窗口类"""

    def __init__(self, root: TkinterDnD.Tk):
        self.root = root
        ui.init()   # 初始化全局控件样式
        gap = 2 * App.dpiScale        # 控件垂直间距
        padding = 5 * App.dpiScale    # 窗口边缘距离

        # 文件打开和保存区 ---------------
        file_frame = ttk.Frame(root)
        file_frame.grid(row=0, padx=2*padding, pady=(2*padding, padding), sticky=tk.EW)

        ttk.Label(file_frame, text=Lang['Input file'] + ':').grid(row=0, column=0, pady=gap, sticky=tk.W)
        # 这里如果不放在self下，函数执行完后file_entry_text就会被回收，导致事件监听失效
        self.fileEntryText = tk.StringVar()
        self.srcEntry = ttk.Entry(file_frame, textvariable=self.fileEntryText)
        self.srcEntry.grid(row=0, column=1, columnspan=2, padx=(padding, gap), pady=(1, 0), sticky=tk.EW)
        self.srcEntry.bind('<Return>', self.onFileEntryEnter)
        self.fileEntryText.trace_add('write', self.onFileEntryInsert)
        btn_width = 0 if App.isMac else 2 * App.dpiScale
        ui.Button(file_frame, text="...", width=btn_width, command=self.openFile).grid(row=0, column=3, pady=(0, 2))

        ttk.Label(file_frame, text=Lang['Output file'] + ':').grid(row=1, column=0, pady=gap, sticky=tk.W)
        self.saveMode = tk.IntVar()  # 与输出文件位置单选按钮绑定的变量
        self.saveMode.set(0)
        ttk.Radiobutton(file_frame, text=Lang['Modify source file'], variable=self.saveMode, value=0,
                        command=self.onSwitchSaveMode).grid(row=1, column=1, padx=padding, sticky=tk.W)

        # "另存为"Frame，包括一个Radio和一个Entry ----------
        saveas_frame = ttk.Frame(file_frame)
        saveas_frame.grid(row=2, column=1, columnspan=3, sticky=tk.EW)
        ttk.Radiobutton(saveas_frame, text=Lang['Save as'] + ':', variable=self.saveMode, value=1,
                        command=self.onSwitchSaveMode).pack(side=tk.LEFT, padx=padding, pady=gap)
        self.dstEntry = ui.Entry(saveas_frame, placeholder=Lang['Leave blank to save to source directory.'])
        self.dstEntry.configure(state=tk.DISABLED)
        self.dstEntry.pack(side=tk.LEFT, padx=(padding, gap), pady=(1, 0), fill=tk.X, expand=True)
        self.openDstBtn = ui.Button(saveas_frame, text="...", width=btn_width, state=tk.DISABLED,
                                    command=self.openSaveAs)
        self.openDstBtn.pack(side=tk.RIGHT, pady=(0, 2))

        # 配置列权重，使输入框能够随窗口大小变化而变化
        file_frame.columnconfigure(1, weight=1)

        # 字体列表和"载入"按钮 ---------------
        fontlist_frame = ttk.Frame(root)    # "字体列表"Label和"载入"按钮
        fontlist_frame.grid(row=1, padx=padding, sticky=tk.EW)
        ttk.Label(fontlist_frame, text=Lang['Fonts in the subtitle'] + ':').pack(side=tk.LEFT, padx=padding)
        self.loadBtn = ui.Button(fontlist_frame, text=Lang['Load'], width=(6 if App.isMac else 7)*App.dpiScale,
                                 state=tk.DISABLED, command=self.onLoadBtn)
        self.loadBtn.pack(side=tk.RIGHT, padx=5)

        self.fontList = FontList(root)    # 字体列表
        self.fontList.grid(row=2, padx=2*padding, pady=padding, sticky=tk.NSEW)

        # 底部的状态栏和应用关闭按钮区 --------------
        bottom_frame = ttk.Frame(root)
        bottom_frame.grid(row=3, padx=2*padding, pady=(0, 2*padding), sticky=tk.EW)
        self.statusBar = ui.StatusBar(bottom_frame)
        self.statusBar.pack(side=tk.LEFT, padx=(0, padding), fill=tk.X, expand=True)

        ui.Button(bottom_frame, text=Lang['Close'], width=(5 if App.isMac else 7)*App.dpiScale, command=root.destroy)\
            .pack(side=tk.RIGHT, padx=padding)
        self.applyBtn = ui.Button(bottom_frame, text=Lang['Apply'], width=(5 if App.isMac else 7)*App.dpiScale,
                                  state=tk.DISABLED, command=self.onApplyBtn)
        self.applyBtn.pack(side=tk.RIGHT, padx=padding)
        config_btn = ui.FlatButton(bottom_frame, text='⚙', fg='#645D56', command=self.showSettings)
        config_btn.pack(side=tk.RIGHT, padx=padding)
        ui.ToolTip(config_btn, Lang['Settings'])

        # 配置列权重，使列表框能够随窗口大小变化而变化
        root.rowconfigure(2, weight=1)
        root.columnconfigure(0, weight=1)

        # 绑定拖放事件到窗口
        root.drop_target_register(DND_FILES)
        root.dnd_bind('<<Drop>>', self.onDrop)

    def openFile(self):
        """点击打开文件"""
        file_name = filedialog.askopenfilename(
            filetypes=[("[Advanced] SubStation Alpha", ".ass .ssa"), ("All files", "*.*")])
        if file_name:
            self.srcEntry.delete(0, tk.END)
            self.srcEntry.insert(0, file_name)
            self.onLoadBtn()
        self.srcEntry.focus_set()

    def openSaveAs(self):
        """点击另存为"""
        base_path = self.dstEntry.get()
        if not base_path:
            base_path = self.srcEntry.get()
        file_path = filedialog.asksaveasfilename(
            initialdir=os.path.dirname(base_path),
            initialfile="newsubtitle",
            defaultextension=".ass",
            filetypes=[("[Advanced] SubStation Alpha", ".ass .ssa"), ("All files", "*.*")]
        )
        self.dstEntry.focus_set()
        if file_path:
            self.dstEntry.delete(0, tk.END)
            self.dstEntry.insert(0, file_path)

    def onDrop(self, event):
        """拖放文件响应"""
        file_paths = self.root.tk.splitlist(event.data) # 切分多个路径并去掉两边的{}
        if not file_paths:
            return
        file_path = os.path.normpath(file_paths[0]) # 转换为OS习惯格式（用\还是/）
        if file_path.endswith(('.ass', '.ssa')):
            self.srcEntry.delete(0, tk.END)
            self.srcEntry.insert(0, file_path)
            self.onLoadBtn()
        else:
            obj = self.root.focus_get()
            messagebox.showerror(Lang['Error'], Lang['Only .ass and .ssa files are supported.'])
            obj.focus_set()

    def onSwitchSaveMode(self):
        """点击切换保存位置"""
        self.dstEntry.configure(state=tk.DISABLED if self.saveMode.get() == 0 else tk.NORMAL)
        self.openDstBtn.configure(state=tk.DISABLED if self.saveMode.get() == 0 else tk.NORMAL)

    def onFileEntryInsert(self, *args):
        """输入文件框值改变响应"""
        self.loadBtn.configure(state=tk.NORMAL if self.srcEntry.get() else tk.DISABLED)

    def onFileEntryEnter(self, *args):
        """输入文件框回车响应"""
        if self.srcEntry.get():
            self.onLoadBtn()

    def onLoadBtn(self, updateStatus: bool = True):
        """
        载入按钮点击响应
        :param updateStatus: 是否更新状态栏信息
        """
        self.statusBar.set(Lang["Opening..."])
        self.statusBar.update()  # 立刻刷新界面，否则就卡住看不到了
        try:
            file_path = self.srcEntry.get()
            subtitleObj = SubStationAlpha.load(file_path)   # 读取字幕文件
            is_reload = self.fontList.subtitleObj and file_path == self.fontList.subtitleObj.filePath
            self.fontList.loadSubtitle(subtitleObj) # 载入字体列表
        except Exception as e:  # 载入出错，弹窗告知
            traceback.print_exc()   # 打印异常信息到控制台
            messagebox.showerror(Lang['Error'], f"{Lang['Subtitle file reading error:']}\n{str(e)}")
            self.loadBtn.focus_force()  # 手动取回焦点
            self.fontList.clearRows()   # 清除可能已经载入的部分行
            self.statusBar.set(Lang["Open failed."], duration=3)    # 设置状态栏文字
        else:   # 载入成功
            if subtitleObj.ignoredFonts:    # 检查是否有忽略的内嵌字体并弹窗提示
                messagebox.showerror(Lang['Warning'], Lang['Embedded fonts {ff} file error, ignored.']
                                                      .format(ff=f'"{'", "'.join(subtitleObj.ignoredFonts)}"'))
            self.applyBtn.configure(state=tk.NORMAL)    # 解开"应用"按钮禁用
            if self.loadBtn.cget('text') != Lang['Reload']: # 设置"载入"按钮为"重新载入"
                self.loadBtn.configure(text=Lang['Reload'], state=tk.NORMAL)
            if updateStatus:    # 设置状态栏文字
                self.statusBar.set(Lang['File reloaded.'] if is_reload else Lang['File loaded.'], duration=3)

    def onApplyBtn(self):
        """点击应用按钮"""
        try:
            if self.fontList.checkTaskValidity():   # 检查任务配置是否正确
                self.statusBar.set(Lang["Executing..."])
                self.statusBar.update()  # 立刻刷新界面，否则就卡住看不到了
                self.fontList.applyEmbedding(self.dstEntry.get())   # 执行嵌入
            else:   # 任务无法执行或者被取消
                self.applyBtn.focus_force()  # 出现过弹窗，需手动取回焦点
                return
        except Exception as e:  # 嵌入出错
            traceback.print_exc()   # 打印异常信息到控制台
            messagebox.showerror(Lang['Error'], f"{Lang['Execution error:']}\n{str(e)}")
            self.applyBtn.focus_force()  # 弹窗后，需手动取回焦点
            self.statusBar.set(Lang["Execution failed."], duration=3)
        else:   # 嵌入成功
            if not self.dstEntry.isblank:   # 如果另存框里有内容，打开另存路径的文件
                self.srcEntry.delete(0, tk.END)
                self.srcEntry.insert(0, self.dstEntry.get())    # 则将内容拷贝到输入文件框
                self.saveMode.set(0)        # radio按钮重新选择到源文件
                self.onSwitchSaveMode()     # 设置两个输入框的可用性
            self.onLoadBtn(updateStatus=False)  # 重新载入文件，不更新状态栏
            self.statusBar.set(Lang["Finished, file reloaded"], duration=3)

    def showSettings(self, event):
        """点击设置按钮"""
        SettingsWindow(self.root)   # 打开设置窗口
