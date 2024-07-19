import tkinter as tk
from tkinter import ttk


class WidgetTable(tk.Frame):
    def __init__(self, **kwargs):
        self.bd = 1
        self.bg = 'white'
        kwargs.update({'bd': self.bd, 'bg': self.bg})
        super().__init__(**kwargs, relief="sunken")

        self.adjusterWidth = 2
        self.headers = []
        self.headerBar = tk.Frame(self)
        self.headerBar.grid(row=0, column=0, sticky=tk.EW)
        self.rows = []    # [[widget, ...], [widget, ...], ...]
        self.cells = []

        # 可滚动表 ----------------
        self.canvas = tk.Canvas(self, bg=self.bg)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky=tk.NSEW)
        self.scrollbar.grid(row=0, column=1, rowspan=2, sticky=tk.NS)

        self.scrollableFrame = tk.Frame(self.canvas, bg=self.bg)
        self.scrollableFrame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.scrollableFrameId = self.canvas.create_window((0, 0), window=self.scrollableFrame, anchor=tk.NW)

        # 绑定鼠标滚轮事件
        # Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)
        # Linux
        self.canvas.bind_all("<Button-4>", self.onMouseWheel)
        self.canvas.bind_all("<Button-5>", self.onMouseWheel)

        self.canvas.bind("<Configure>", self.onResize)

        self.bind("<Configure>", self.onResize)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.after(0, self.onResize)

    def addColumn(self, heading: str = None, width: int = 0, minWidth: int = 0, weight: int = 0, adjuster: str = None):
        # 不管是否需adjuster，所有的都放在Frame里，通过结构一致保证pack后的高度一致
        widget = tk.Frame(self.headerBar, bd=1, relief='groove')
        if adjuster and adjuster in ('left', 'right'):
            adjuster_frame = tk.Frame(widget, width=self.adjusterWidth, cursor='sb_h_double_arrow')
            adjuster_frame.pack(side=adjuster, fill='y')
            adjuster_frame.bind("<B1-Motion>", self.onAdjusterMouseMove)
        tk.Label(widget, text=heading).pack()
        # 通过pack方法，让headerBar Frame自适应控件的尺寸，因为place方法无法自适应，
        # 当place覆盖pack的布局时，仍会保留其控件尺寸
        widget.pack(side='left')

        self.headers.append({
            'heading': heading,
            'width': width,
            'minWidth': max(minWidth, self.adjusterWidth),
            'weight': 0 if width else weight,
            'weighted': weight != 0,
            'adjuster': adjuster,
            'widget': widget
        })

    def newRow(self):
        return tk.Frame(self.scrollableFrame, bg=self.bg)

    def addRow(self, row: tk.Frame):
        row_cells = list(row.children.values())
        for cell in row_cells:
            cell.pack(side='left')
        row.pack(fill='x', expand=True)
        self.rows.append(row)
        self.cells.append(row_cells)

    def clearRows(self):
        for row in self.rows:
            row.pack_forget()
            # row.destroy()
        for row_cells in self.cells:
            for cell in row_cells:
                cell.place_forget()
        for widget in self.scrollableFrame.winfo_children():
            widget.destroy()
        self.rows = []
        self.cells = []

    def onAdjusterMouseMove(self, event):
        if event.x == 0:    # y方向的动作没必要响应
            return

        total_weight_width = 0
        for i, target_col in enumerate(self.headers):
            if target_col['weighted']:    # 统计总权重值
                total_weight_width += target_col['width']
            if target_col['widget'] == event.widget.master:    # 寻找目标列
                # 调整哪一个方向的列宽度
                direction = 1 if target_col['adjuster'] == 'right' else -1
                event_x = event.x * direction
                if target_col['width'] == target_col['minWidth'] and event_x < 0:    # 宽度不能小于最小宽度
                    return
                if target_col['width'] + event_x < target_col['minWidth']:
                    event_x = target_col['minWidth'] - target_col['width']
                target_col['width'] += event_x
                break
        else:
            return

        total_weight_after = 0
        # 统计前/后方列总权重
        j = i + direction
        while 0 < j < len(self.headers):
            total_weight_after += self.headers[j]['weight']
            j += direction

        # 将宽度变化量按权重分配给前/后方的列
        remnant_width = event_x
        j = i + direction
        while 0 < j < len(self.headers):
            column = self.headers[j]
            if column['weighted']:
                diff = remnant_width * column['weight'] / total_weight_after
                if column['width'] - diff < column['minWidth']:
                    diff = column['width'] - column['minWidth']
                column['width'] -= diff
                remnant_width -= diff
                total_weight_width += column['width']
                total_weight_after -= column['weight']
            j += direction
        target_col['width'] -= remnant_width    # 无处分配的宽度，放回原列，宽度无法继续增加

        # 重新计算所有列的权重
        for column in self.headers:
            if column['weighted']:
                column['weight'] = column['width'] / total_weight_width

        self.onResize()

    def onResize(self, event=None):
        if self.winfo_width() <= 1:    # 没有宽度，说明还未载入界面
            return
        widget_width = self.winfo_width() - self.scrollbar.winfo_width() - 2 * self.bd
        # 更新scrollableFrame的大小
        self.canvas.itemconfig(self.scrollableFrameId, width=widget_width)

        # 重新计算各列的宽度
        remnant_width = widget_width    # 用于给权重列分配的总宽度
        total_weight = 0
        for column in self.headers:
            # 必须有权重，并且宽度未到最小宽度，这样才可以继续缩小
            if column['weighted'] == 0:
                remnant_width -= column['width']
            total_weight += column['weight']

        remnant_width = max(remnant_width, 0)
        xOffset = 0
        for i, column in enumerate(self.headers):
            if column['weighted']:    # 权重优先
                column['width'] = max(remnant_width * column['weight'] / total_weight, column['minWidth'])
                remnant_width -= column['width']
                total_weight -= column['weight']
            column['widget'].place(x=xOffset, y=0, width=column['width'], anchor=tk.NW)
            for row_cells in self.cells:
                if i < len(row_cells):
                    row_cells[i].place(x=xOffset, y=0, width=column['width'], anchor=tk.NW)
            xOffset += column['width']

    def onMouseWheel(self, event):
        if self.scrollbar.get() == (0.0, 1.0):
            return
        if event.delta:  # Windows and MacOS
            self.canvas.yview("scroll", -event.delta, "units")
        elif event.num == 4:  # Linux scroll up
            self.canvas.yview("scroll", -1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview("scroll", 1, "units")
