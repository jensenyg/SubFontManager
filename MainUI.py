import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES
from FontList import FontList
from PlaceholderEntry import PlaceholderEntry
from SubStationAlpha import SubStationAlpha


class MainUI:
    def __init__(self, root):
        self.root = root
        gapy = 2    # 控件垂直间距
        style = ttk.Style()
        style.map('TEntry', fieldbackground=[('!disabled', 'white')])   # 设置输入框非禁用背景色为白色

        # 文件打开和保存区 ---------------
        frame1 = ttk.Frame(root)
        frame1.grid(row=0, padx=10, pady=10, sticky="we")

        ttk.Label(frame1, text="输入文件:").grid(row=0, column=0, pady=gapy, sticky="w")
        # 这里如果不放在self下，函数执行完后file_entry_text就会被回收，导致事件监听失效
        self.file_entry_text = tk.StringVar()
        self.file_entry = ttk.Entry(frame1, textvariable=self.file_entry_text)
        self.file_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=(1, 0), sticky="ew")
        self.file_entry.bind("<Return>", self.onFileEntryEnter)
        self.file_entry_text.trace("w", self.onFileEntryInsert)
        open_file_btn = tk.Button(frame1, text="...", command=self.openFile)
        open_file_btn.grid(row=0, column=3, pady=(0, 2))

        ttk.Label(frame1, text="输出文件:").grid(row=1, column=0, pady=gapy, sticky="w")
        self.save_mode = tk.IntVar()
        self.save_mode.set(0)
        ttk.Radiobutton(frame1, text="修改源文件", variable=self.save_mode, value=0, command=self.onSwitchSaveMode)\
            .grid(row=1, column=1, padx=5, sticky="w")

        # "另存为"Frame，包括一个Radio和一个Entry ----------
        saveas_frame = ttk.Frame(frame1)
        saveas_frame.grid(row=2, column=1, columnspan=3, sticky="ew")
        ttk.Radiobutton(saveas_frame, text="另存为:", variable=self.save_mode, value=1, command=self.onSwitchSaveMode)\
            .pack(side='left', padx=5, pady=gapy)
        self.dir_entry = PlaceholderEntry(saveas_frame, placeholder="Leave blank to save to source directory.")
        self.dir_entry.configure(state=tk.DISABLED)
        self.dir_entry.pack(side='left', padx=5, pady=(1, 0), fill="x", expand=True)
        self.open_dir_btn = tk.Button(saveas_frame, text="...", state=tk.DISABLED, command=self.openDirectory)
        self.open_dir_btn.pack(side='right', pady=(0, 2))

        # 配置列权重，使输入框能够随窗口大小变化而变化
        frame1.columnconfigure(1, weight=1)

        # 字体列表和"载入"按钮 ---------------
        frame2 = ttk.Frame(root)
        frame2.grid(row=1, padx=5, sticky="we")
        ttk.Label(frame2, text="字幕中包含的字体:").pack(side='left', padx=5)
        self.load_btn = tk.Button(frame2, text="载入", width=6, command=self.onLoadBtn, state=tk.DISABLED)
        self.load_btn.pack(side='right', padx=5)

        self.font_table = FontList(root, bg='#FFF', bd=1, relief="sunken")
        self.font_table.grid(row=2, padx=10, pady=5, sticky="nswe")

        # 底部的确定和取消按钮区 --------------
        button_frame = ttk.Frame(root)
        button_frame.grid(row=3, pady=(5, 10))

        ok_button = ttk.Button(button_frame, text="确定", command=self.onOkBtn)
        ok_button.pack(side="left", padx=5)
        cancel_button = ttk.Button(button_frame, text="取消", command=root.destroy)
        cancel_button.pack(side="right", padx=5)

        # 配置列权重，使列表框能够随窗口大小变化而变化
        root.rowconfigure(2, weight=1)
        root.columnconfigure(0, weight=1)

        # 绑定拖放事件到窗口
        root.drop_target_register(DND_FILES)
        root.dnd_bind('<<Drop>>', self.onDrop)

    def openFile(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Advanced SubStation Alpha", "*.ass"), ("SubStation Alpha", "*.ssa"), ("All files", "*.*")])
        if filename:
            self.file_entry_text.set(filename)
        self.root.focus_force()
        self.onLoadBtn()

    def openDirectory(self):
        filepath = filedialog.asksaveasfilename(
            initialdir=".",
            initialfile="newsubtitle",
            defaultextension=".ass",
            filetypes=[("Advanced SubStation Alpha", "*.ass"), ("SubStation Alpha", "*.ssa"), ("All files", "*.*")]
        )
        if filepath:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, filepath)
        self.root.focus_force()

    def onDrop(self, event):
        file_path = event.data.strip('{}')
        if not file_path.endswith(('.ass', '.ssa')):
            messagebox.showerror("错误", "仅支持 .ass 和 .ssa 文件")
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, event.data)

    def onSwitchSaveMode(self):
        self.dir_entry.configure(state=tk.DISABLED if self.save_mode.get() == 0 else tk.NORMAL, background='red')
        self.open_dir_btn.configure(state=tk.DISABLED if self.save_mode.get() == 0 else tk.NORMAL)

    def onFileEntryInsert(self, *args):
        self.load_btn.configure(state=tk.NORMAL if self.file_entry.get() else tk.DISABLED)

    def onFileEntryEnter(self, *args):
        self.onLoadBtn()

    def onLoadBtn(self, *args):
        path = self.file_entry.get()
        subtitleObj = SubStationAlpha.load(path)
        if not subtitleObj:
            return
        fontList = subtitleObj.gatherFonts()
        self.font_table.clearRows()
        for item in fontList:
            self.font_table.addRow(
                fontName=item['fontname'], isEmbed=item['isEmbed'], isSubset=True, charCount=item['count'])
        # subtitleObj.save(self.dir_entry.get())
        self.load_btn.configure(text="重新载入" if subtitleObj else "载入", state=tk.NORMAL)

    def onOkBtn(self, event):
        pass
