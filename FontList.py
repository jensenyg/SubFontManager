import tkinter as tk
from tkinter import ttk


class FontList(tk.Frame):
    def __init__(self, container):
        self.bg = 'white'
        self.columnWidth = []
        self.itemList = []   # [{fontname, isEmbed, isSubset, source}]

        super().__init__(container, bg=self.bg, bd=1, relief="sunken")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # 列标题 -----------------
        columnTitle = tk.Frame(self)
        columnTitle.grid(row=0, column=0, sticky='ew')
        relief = 'raised'
        label1 = tk.Label(columnTitle, text='内嵌', width=3, bd=1, relief=relief)
        label1.grid(row=0, column=0, sticky="ew")
        label2 = tk.Label(columnTitle, text='字体', bd=1, relief=relief)
        label2.grid(row=0, column=1, sticky="ew")
        label3 = tk.Label(columnTitle, text='字数', width=6, bd=1, relief=relief)
        label3.grid(row=0, column=2, sticky="ew")
        label4 = tk.Label(columnTitle, text='子集化', width=5, bd=1, relief=relief)
        label4.grid(row=0, column=3, sticky="ew")
        label5 = tk.Label(columnTitle, text='文件源', bd=1, relief=relief)
        label5.grid(row=0, column=4, sticky="ew")
        columnTitle.columnconfigure(0, weight=0)
        columnTitle.columnconfigure(1, weight=1, uniform="column")
        columnTitle.columnconfigure(2, weight=0)
        columnTitle.columnconfigure(3, weight=0)
        columnTitle.columnconfigure(4, weight=2, uniform="column")

        # 可滚动表 ----------------
        self.canvas = tk.Canvas(self, bg=self.bg)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky='nsew')
        self.scrollbar.grid(row=0, column=1, rowspan=2, sticky='ns')

        self.scrollableFrame = tk.Frame(self.canvas, bg=self.bg)
        self.scrollableFrame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.scrollableFrameId = self.canvas.create_window((0, 0), window=self.scrollableFrame, anchor="nw")

        self.scrollableFrame.columnconfigure(0, weight=0)
        self.scrollableFrame.columnconfigure(1, weight=1, uniform="column")
        self.scrollableFrame.columnconfigure(2, weight=0)
        self.scrollableFrame.columnconfigure(3, weight=0)
        self.scrollableFrame.columnconfigure(4, weight=2, uniform="column")

        # 绑定鼠标滚轮事件
        # Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)
        # Linux
        self.canvas.bind_all("<Button-4>", self.onMouseWheel)
        self.canvas.bind_all("<Button-5>", self.onMouseWheel)

        self.canvas.bind("<Configure>", self.onResize)

    def onMouseWheel(self, event):
        if self.scrollbar.get() == (0.0, 1.0):
            return
        if event.delta:  # Windows and MacOS
            self.canvas.yview("scroll", -event.delta, "units")
        elif event.num == 4:  # Linux scroll up
            self.canvas.yview("scroll", -1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview("scroll", 1, "units")

    def onResize(self, event):
        # 更新Frame的大小
        self.canvas.itemconfig(self.scrollableFrameId, width=event.width)

    def addRow(self, fontName: str, isEmbed: bool = False, isSubset: bool = True, charCount: int = 0,
               source: str = ''):
        row_index = len(self.itemList)
        row_item = {
            'fontname': fontName,
            'isEmbed': tk.BooleanVar(),
            'isSubset': tk.BooleanVar(),
            'source': tk.StringVar()
        }
        row_item['isEmbed'].set(isEmbed)
        row_item['isSubset'].set(isSubset)
        row_item['source'].set(source if source else '')
        self.itemList.append(row_item)

        check1 = tk.Checkbutton(self.scrollableFrame, variable=row_item['isEmbed'],
                                state=tk.NORMAL if source else tk.DISABLED)
        check1.configure(width=2)
        check1.grid(row=row_index, column=0, padx=(5, 1), sticky="w")
        label2 = tk.Label(self.scrollableFrame, text=fontName, anchor='w')
        label2.grid(row=row_index, column=1, pady=(0, 2), sticky='w')
        label3 = tk.Label(self.scrollableFrame, text=str(charCount) + ' ', width=6, anchor='e')
        label3.grid(row=row_index, column=2, padx=(0, 8), pady=(0, 2), sticky='e')
        check4 = tk.Checkbutton(self.scrollableFrame, variable=row_item['isSubset'], width=3,
                                state=tk.NORMAL if source else tk.DISABLED)
        check4.configure(width=3)
        check4.grid(row=row_index, column=3, padx=(0, 1), sticky="ew")
        entry5 = ttk.Entry(self.scrollableFrame, textvariable=row_item['source'])
        entry5.grid(row=row_index, column=4, sticky="ew")

    def clear(self):
        if self.itemList:
            self.itemList.clear()
            for widget in self.scrollableFrame.winfo_children():
                widget.destroy()
