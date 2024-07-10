import tkinter as tk
from tkinter import ttk


class ScrollableFrame(tk.Frame):
    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)
        self.bg = kwargs.get('background', kwargs.get('bg'))

        self.canvas = tk.Canvas(self, bg=self.bg)
        self.canvas.config(highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.scrollableFrame = None
        self.windowsId = None
        self.createScrollableFrame()

        # 绑定鼠标滚轮事件
        # Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)
        # Linux
        self.canvas.bind_all("<Button-4>", self.onMouseWheel)
        self.canvas.bind_all("<Button-5>", self.onMouseWheel)

    def createScrollableFrame(self):
        self.scrollableFrame = tk.Frame(self.canvas, bg=self.bg)
        self.scrollableFrame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.windowsId = self.canvas.create_window((0, 0), window=self.scrollableFrame, anchor="nw")

    def reset(self):
        self.canvas.delete(self.windowsId)
        self.scrollableFrame.destroy()
        self.createScrollableFrame()

    def onMouseWheel(self, event):
        if self.scrollbar.get() == (0.0, 1.0):
            return
        if event.delta:  # Windows and MacOS
            self.canvas.yview("scroll", -event.delta, "units")
        elif event.num == 4:  # Linux scroll up
            self.canvas.yview("scroll", -1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview("scroll", 1, "units")


class FontList(ScrollableFrame):
    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)
        self.columnWidth = []
        self.setColumnWidth([1, 2, 3])
        self.itemList = []   # [{fontname, isEmbed, isSubset, source}]

    def setColumnWidth(self, *args):
        if len(args) == 1 and args is list:
            self.columnWidth = args[0]
        elif len(args) == 2:
            self.columnWidth[args[0]] = args[1]
        self.scrollableFrame.columnconfigure(0, weight=1)

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
        row_item['source'].set(source)
        self.itemList.append(row_item)

        check1 = tk.Checkbutton(self.scrollableFrame, text=fontName, variable=row_item['isEmbed'], bg='white')
        check1.grid(row=row_index, column=0, pady=1, sticky="w")

        charcount_label = tk.Label(self.scrollableFrame, text=str(charCount), bg="white")
        charcount_label.grid(row=row_index, column=1, padx=5, sticky='e')

        check2 = tk.Checkbutton(self.scrollableFrame, text="Subset", variable=row_item['isSubset'], bg='white')
        check2.grid(row=row_index, column=2, padx=(5, 0), pady=1, sticky="e")

        check2 = ttk.Entry(self.scrollableFrame, textvariable=row_item['source'])
        check2.grid(row=row_index, column=3, padx=(5, 0), pady=1, sticky="e")

    def clearRows(self):
        if self.itemList:
            self.itemList.clear()
            self.reset()
