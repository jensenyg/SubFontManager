import tkinter as tk
from tkinter import ttk, font as tkfont
from App import App
from .ToolTip import ToolTip
from .Widgets import Widget


class WidgetCell:
    def __init__(self, widget: Widget, padx=0, pady=0, columnSpan: int = 1):
        self.widget = widget
        padx = padx if type(padx) is tuple else (padx, padx)
        self.padx = (padx[0] * App.dpiScale, padx[1] * App.dpiScale)
        pady = pady if type(pady) is tuple else (pady, pady)
        self.pady = (pady[0] * App.dpiScale, pady[1] * App.dpiScale)
        self.columnSpan = columnSpan


class WidgetRow(tk.Frame):
    """行对象，继承自Frame，提供高亮功能，同时辅助WidgetTable.addRow函数进行类型检查"""
    HIGHLIGHT_COLOR = 'lightskyblue'

    def __init__(self, *args, **kwargs):
        kwargs['bg'] = Widget.bg
        super().__init__(*args, **kwargs)
        self.cells = []

    def addCell(self, widget: Widget, padx=0, pady=0, columnSpan: int = 1):
        self.cells.append(WidgetCell(widget, padx, pady, columnSpan))

    def setHighLight(self, highlight: bool = True):
        color = self.HIGHLIGHT_COLOR if highlight else Widget.bg
        self.configure(bg=color)
        for cell in self.cells:
            cell.widget.setBackground(color)


class WidgetTable(tk.Frame):
    """由自定义控件组成的列表，支持滚动，并可以自定义列标题和调整宽度"""
    def __init__(self, **kwargs):
        self.bd = 1
        self.bg = 'white'
        kwargs.update({'bd': self.bd, 'bg': self.bg})
        super().__init__(**kwargs, relief="sunken")

        self.adjusterWidth = 2
        self.headers = []
        self.headerBar = tk.Frame(self)
        self.headerBar.grid(row=0, column=0, sticky=tk.EW)
        self.rows = []    # [WidgetRow, WidgetRow, ...]
        self.cells = []   # [[widget, ...], [widget, ...], ...]
        self.selectedRow = None

        # 可滚动表 ----------------
        self.canvas = tk.Canvas(self, bg=self.bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=1, column=0, sticky=tk.NSEW)
        self.scrollbar.grid(row=0, column=1, rowspan=2, sticky=tk.NS)

        self.scrollableFrame = tk.Frame(self.canvas, bg=self.bg)
        self.scrollableFrame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.scrollableFrameId = self.canvas.create_window((0, 0), window=self.scrollableFrame, anchor=tk.NW)

        self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)    # 绑定鼠标滚轮事件, Windows and macOS
        self.canvas.bind_all("<Button-4>", self.onMouseWheel)   # 绑定鼠标滚轮事件, Linux
        self.canvas.bind_all("<Button-5>", self.onMouseWheel)   # 绑定鼠标滚轮事件, Linux
        self.canvas.bind("<Button-1>", self.onClick)

        self.bind("<Configure>", self.onResize)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.after(0, self.onResize)

    def addColumn(self, heading: str = None, width: int = 0, minWidth: int = 0, weight: int = 0,
                  adjuster: str = None, toolTip: str = None):
        """
        添加列，并设置列的基本属性
        :param heading: 列标题
        :param width: 列宽度
        :param minWidth: 列最小宽度，宽度调整时不会小于此宽度，为0则不限
        :param weight: 列宽度权重，控制其在宽度调整时被分配到宽度的比例，为0则宽度固定
        :param adjuster: 宽度调节器，用于调节该列的宽度，放置在列标题的左侧或右侧，
                         可以设置为'left', 'right'来指定，None则不设置，列宽无法调整
        :param toolTip: 气泡提示，鼠标悬浮后显示，None则没有
        """
        # 不管是否需adjuster，所有的都放在Frame里，通过结构一致保证pack后的高度一致
        widget = tk.Frame(self.headerBar, bd=1, relief='raised')
        if adjuster and adjuster in (tk.LEFT, tk.RIGHT):
            adjuster_frame = tk.Frame(widget, width=self.adjusterWidth, cursor='sb_h_double_arrow')
            adjuster_frame.pack(side=adjuster, fill=tk.Y)
            adjuster_frame.bind("<B1-Motion>", self.onAdjusterMouseMove)
        label = tk.Label(widget, text=heading)
        label.pack()
        if toolTip:
            ToolTip(label, toolTip)

        # 通过pack方法，让headerBar Frame自适应控件的尺寸，因为place方法无法自适应，
        # 当place覆盖pack的布局时，仍会保留其控件尺寸
        widget.pack(side=tk.LEFT)

        self.headers.append({
            'heading': heading,
            'width': width * App.dpiScale,
            'minWidth': max(minWidth * App.dpiScale, self.adjusterWidth),
            'weight': 0 if width else weight,
            'weighted': weight != 0,
            'adjuster': adjuster,
            'widget': widget
        })

    @staticmethod
    def _bindCallbackToFirst(widget, sequence, callback):
        """为控件bind事件和回调函数，但将回调函数添加到回调序列的第一位"""
        callbacks_tcl = widget.bind(sequence)    # 获取当前回调函数序列，该序列是一个“Tcl命令字符串”
        if callbacks_tcl:
            widget.unbind(sequence)
            widget.bind(sequence, callback)
            callback_tcl = widget.bind(sequence)    # 获取新的回调函数的Tcl命令
            widget.unbind(sequence)
            new_callbacks_tcl = callback_tcl + '\n' + callbacks_tcl    # 连接两个Tcl命令
            return widget.bind(sequence, new_callbacks_tcl)
        else:
            return widget.bind(sequence, callback)

    def newRow(self) -> WidgetRow:
        """生成一个新行对象，将行内元素插入到该对象后addRow即可创建新行"""
        return WidgetRow(self.scrollableFrame)

    def addRow(self, row: WidgetRow):
        """添加新行，row中的每一个对象将成为行内的一列"""
        if type(row) is not WidgetRow:
            raise TypeError('Only WidgetRow type (created by newRow() method) is accepted.')

        for cell in row.cells:
            cell.widget.pack(side=tk.LEFT, pady=cell.pady, anchor=tk.W)
            # 为每一个控件绑定激活事件，并插入到回调列表第一位，因为现有回调函数可能会返回'break'
            self._bindCallbackToFirst(cell.widget, '<Button-1>', self.onRowSelect)
        row.pack(fill=tk.X, expand=True)
        # 为行对象本身绑定激活事件，因为控件周围可能会有空隙
        self._bindCallbackToFirst(row, '<Button-1>', self.onRowSelect)
        
        self.rows.append(row)
        self.cells.append(row.cells)

    def addSeparateRow(self, sepText: str = None, indent: int = 0, padx=0, pady=0, lineLength: int = 300):
        """上右下左
        插入分隔行，包含一段文字和一条分隔线
        :param sepText: 行内文字
        :param indent: 文字与左边框的距离
        :param padx: 文字左右与线的距离
        :param pady: 文字上下与线的距离
        :param lineLength: 分隔线的长度
        """
        indent *= App.dpiScale
        padx = padx if type(padx) is tuple else (padx, padx)
        padx = (padx[0] * App.dpiScale, padx[1] * App.dpiScale)
        pady = pady if type(pady) is tuple else (pady, pady)
        pady = (pady[0] * App.dpiScale, pady[1] * App.dpiScale)

        # 绘制一个Canvas作为分隔行
        sep_row = tk.Canvas(self.scrollableFrame, bg=self.bg, highlightthickness=0)
        if sepText:    # 绘制字体
            font = Widget.defaultFont.copy()
            font.configure(slant=tkfont.ITALIC)    # 中文斜体需要字体支持，mac下可能无效
            sep_row.create_text(indent + padx[0], pady[0], text=sepText, anchor=tk.NW, fill="darkgray", font=font)
        x0, y0, x1, y1 = sep_row.bbox("all")  # 获取所有内容的边界框
        text_height = y1 - y0
        sep_row.config(height=text_height + pady[0] + pady[1])
        if lineLength:    # 绘制分隔线
            lineLength *= App.dpiScale
            center_y = text_height / 2 + pady[0]
            sep_row.create_line(5*App.dpiScale, center_y, indent, center_y, fill="darkgray")    # 绘制左侧线
            sep_row.create_line(x1 + padx[1], center_y, lineLength, center_y, fill="darkgray")    # 绘制右侧线
        sep_row.pack(fill=tk.X, expand=True)
        self.rows.append(sep_row)

    def clearRows(self):
        """清除列表内的所有行，但保留列设置"""
        for row in self.rows:
            row.master.pack_forget()
            row.pack_forget()
            # row.destroy()
        for row_cells in self.cells:
            for cell in row_cells:
                cell.widget.place_forget()
        for widget in self.scrollableFrame.winfo_children():
            widget.destroy()
        self.rows = []
        self.cells = []

    def onRowSelect(self, event):
        if self.selectedRow:
            self.selectedRow.setHighLight(False)
        self.selectedRow = event.widget if type(event.widget) is WidgetRow else event.widget.master
        self.selectedRow.setHighLight(True)
        self.selectedRow.focus_set()

    def onClick(self, event):
        if self.selectedRow:
            self.selectedRow.setHighLight(False)
            self.selectedRow = None
        self.focus_set()  # 获取焦点，以便让ComboBox等失去焦点

    def onAdjusterMouseMove(self, event):
        """拖动Adjuster时调节列宽度"""
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
        # 设置列标题宽度
        xOffset = 0
        for i, column in enumerate(self.headers):
            if column['weighted']:    # 权重优先
                column['width'] = max(remnant_width * column['weight'] / total_weight, column['minWidth'])
                remnant_width -= column['width']
                total_weight -= column['weight']
            column['widget'].place(x=xOffset, y=0, width=column['width'], anchor=tk.NW)
            xOffset += column['width']

        # 设置列元素宽度
        for row_cells in self.cells:
            xOffset = 0
            j = 0
            for i, cell in enumerate(row_cells):
                width = 0
                for k in range(j, j + cell.columnSpan):
                    if k >= len(self.headers):
                        break
                    width += self.headers[k]['width']
                j += cell.columnSpan
                h = cell.widget.master.winfo_height()
                cell.widget.place(
                    x=xOffset + cell.padx[0],
                    y=h * 0.5 + cell.pady[0] - cell.pady[1],
                    width=width - cell.padx[0] - cell.padx[1],
                    height=h - cell.pady[0] - cell.pady[1] - 2,    # 减去2px，切掉组合框上下各1px，主要为了mac下的效果
                    anchor=tk.W
                )
                xOffset += width

    def onMouseWheel(self, event):
        if self.scrollbar.get() == (0.0, 1.0):
            return
        if event.delta:  # Windows and macOS
            self.canvas.yview("scroll", -event.delta, "units")
        elif event.num == 4:  # Linux scroll up
            self.canvas.yview("scroll", -1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview("scroll", 1, "units")
