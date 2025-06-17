from typing import Callable
import tkinter as tk
from tkinter import ttk, font as tkfont, Event
from utils import App
from .ToolTip import ToolTip
from .Widgets import StyledWidget


class Header(tk.Frame):
    """列标题类"""
    AdjusterWidth = 2   # 列宽调节器宽度

    def __init__(self, master, label: str, toolTip: str = None, **kwargs):
        super().__init__(master, **kwargs)
        self.width: int = 0     # 列宽度
        self.minWidth: int = 0  # 最小宽度
        self.weight: float = 0  # 列权重
        self.adjuster: tk.Frame | None = None   # 列宽调节器，可以用鼠标拖动的控件
        self.adjusterPos: str | None = None     # 列宽调节器的位置，可以为'left', 'right'或None
        self.sortKey: Callable[[WidgetRow], object] | None = None   # 排序函数
        self.orderDesc: bool = True  # 当前排序是否为降序
        self.onAdjust: Callable | None = None   # 列宽调节器拖放事件回调函数，需要返回实际移动距离
        self._cursorX: int = 0  # 列宽调节器拖放时的x基准坐标
        self._cursorY: int = 0  # 列宽调节器拖放时的y基准坐标

        self.label = tk.Label(self, text=label) # 列名标签控件
        self.toolTip = ToolTip(self.label, toolTip) if toolTip else None    # 气泡提示控件

    def setAdjuster(self, position: str | None, onAdjust: Callable | None = None):
        """
        设置宽度调节器，用于调节该列的宽度，放置在列标题的左侧或右侧
        :param position: 宽度调节器位置，可以设置为'left', 'right'来指定位置，None则不设置，列宽无法调整
        :param onAdjust: 拖动宽度调节器的事件监听函数，需要返回int，代表实际移动的距离
        """
        if position in (tk.LEFT, tk.RIGHT):
            self.adjuster = tk.Frame(self, width=self.AdjusterWidth, cursor='sb_h_double_arrow')
            self.adjuster.pack(side=position, fill=tk.Y)
            # tkinter在mac上拖动事件中鼠标坐标可能“乱飞”，这里通过监听两个事件来修正它
            self.adjuster.bind("<Button-1>", self._onClick)  # 绑定鼠标点击事件
            self.adjuster.bind("<B1-Motion>", self._onDrag)  # 绑定鼠标拖动事件
            self.adjusterPos = position
            self.onAdjust = onAdjust
        elif position is None and self.adjuster:
            self.adjuster.destroy()
            self.adjuster = None
            self.adjusterPos = None
            self.onAdjust = None

    def setText(self, text: str):
        """设置列标题文本"""
        self.label.config(text=text)

    def getText(self) -> str:
        """获取列标题文本"""
        return self.label.cget('text')

    def bind(self, sequence: str = None, func: Callable = None, add: str = None) -> str:
        """绑定事件"""
        self.label.bind(sequence, lambda e: e.widget.master.event_generate(sequence, x=e.x, y=e.y))
        return super().bind(sequence, func, add)

    def pack(self, *args, **kwargs):
        self.label.pack()
        super().pack(*args, **kwargs)

    def _onClick(self, event: Event):
        """点击事件响应，记录坐标"""
        self._cursorX = event.x_root
        self._cursorY = event.y_root

    def _onDrag(self, event: Event):
        """拖动事件响应"""
        # tkinter在mac上拖动事件中鼠标坐标可能“乱飞”，所以这里用x_root和点击时坐标的差值来修正它
        event.x = event.x_root - self._cursorX
        event.y = event.y_root - self._cursorY
        # 按照实际移动的距离修正基础坐标，因为列可能已经无法调整宽度了，这种机制可以让调节器移动时不会和鼠标错位
        self._cursorX += self.onAdjust(event)
        self._cursorY = event.y_root


class WidgetCell:
    """单元格类，可以基于Label, Checkbox, Combobox等不同类型"""

    def __init__(self, widget: tk.Widget, padx: int | tuple[int, int] = 0,
                 pady: int | tuple[int, int] = 0, columnSpan: int = 1):
        """
        :param widget: 控件
        :param padx: 两侧的空隙宽度
        :param pady: 上下的空隙高度
        :param columnSpan: 该单元格横跨几个列，默认为1
        """
        self.widget = widget
        if not isinstance(padx, tuple):
            padx = (padx, padx)
        if not isinstance(pady, tuple):
            pady = (pady, pady)
        self.padx = (padx[0] * App.dpiScale, padx[1] * App.dpiScale)
        self.pady = (pady[0] * App.dpiScale, pady[1] * App.dpiScale)
        self.columnSpan = columnSpan


class WidgetRow(tk.Frame):
    """列表行类，继承自Frame，提供高亮功能，同时辅助WidgetTable.addRow函数进行类型检查"""
    HIGHLIGHT_COLOR = 'lightskyblue'  # 高亮背景色

    def __init__(self, *args, isSep: bool = False, **kwargs):
        """
        :param isSep: 是否是分隔行
        """
        kwargs['bg'] = StyledWidget.bg
        super().__init__(*args, **kwargs)
        self.cells = []
        self.data = None    # 可以由外部赋值的任意数据，一般是RowItem
        self.isSep = isSep

    def addCell(self, widget: tk.Widget, padx=0, pady=0, columnSpan: int = 1):
        """添加单元格，注意第一个格的高度将决定整个行的高度"""
        cell = WidgetCell(widget, padx, pady, columnSpan)
        self.cells.append(cell)
        if len(self.cells) == 1:
            # 必须先将cell都pack到row并刷新，才可以让row获得最大尺寸，但cell最终是靠place布局的，这会导致界面闪烁。
            # 这里先只加入第一个cell，它的pack位置和place位置一样，可以减少错位闪烁，但要求其他cell不能比第一个高。
            cell.widget.pack(side=tk.LEFT, padx=cell.padx, pady=cell.pady, anchor=tk.W)
            self.pack(fill=tk.X, expand=True)
        self._bindCallbackToFirst(cell.widget, '<Button-1>', self.onCellClicked)    # 绑定点击事件(高亮)

    def setHighLight(self, highlight: bool = True):
        """设置行高亮状态"""
        color = self.HIGHLIGHT_COLOR if highlight else StyledWidget.bg
        self.configure(bg=color)
        for cell in self.cells:
            cell.widget.setBackground(color)

    def onCellClicked(self, event: Event):
        """绑定事件响应，直接传到父控件，即行对象"""
        self.event_generate('<Button-1>', x=event.x, y=event.y)

    @staticmethod
    def _bindCallbackToFirst(widget: tk.Widget, sequence: str, callback: Callable):
        """为控件bind事件和回调函数，但将回调函数添加到回调序列的第一位"""
        callbacks_tcl = widget.bind(sequence)  # 获取当前回调函数序列，该序列是一个“Tcl命令字符串”
        if callbacks_tcl:
            widget.unbind(sequence)
            widget.bind(sequence, callback)
            callback_tcl = widget.bind(sequence)  # 获取新的回调函数的Tcl命令
            widget.unbind(sequence)
            new_callbacks_tcl = callback_tcl + '\n' + callbacks_tcl  # 连接两个Tcl命令
            return widget.bind(sequence, new_callbacks_tcl)
        else:
            return widget.bind(sequence, callback)


class WidgetTable(tk.Frame):
    """由自定义控件组成的列表，支持滚动，并可以自定义列标题和调整宽度，以及按分隔行分组排序功能"""
    HEADIND_ASC_SURFIX = '△'    # 列标题升序排列符号
    HEADIND_DESC_SURFIX = '▽'   # 列标题降序排列符号

    def __init__(self, **kwargs):
        self.bd = 1  # border宽度
        self.bg = StyledWidget.bg   # background背景色
        kwargs.update({'bd': self.bd, 'bg': self.bg})
        super().__init__(**kwargs, relief=tk.SUNKEN)

        self._headers: list[Header] = []    # 列标题控件列表
        self._headerBar = tk.Frame(self)    # 列标题栏，列标题控件的容器
        self._headerBar.grid(row=0, column=0, sticky=tk.EW)
        self._rows: list[WidgetRow] = []    # 行控件列表
        self._cells: list[list[WidgetCell]] = []    # 所有单元格控件，为二维列表
        self._selectedRow: WidgetRow | None = None  # 当前选择的行控件
        self._currentSortedHeader: Header | None = None # 当前排序列的序号
        self._suspendedResizing: bool = False

        # 可滚动列表 ----------------
        self._scrollableCanvas = tk.Canvas(self, bg=self.bg, highlightthickness=0)  # 一个高度有限的Canvas，用于滚动显示
        self._scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._scrollableCanvas.yview) # 滚动条
        self._scrollbar.grid(row=0, column=1, rowspan=2, sticky=tk.NS)
        self._scrollableCanvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollableCanvas.grid(row=1, column=0, sticky=tk.NSEW)

        self._tableFrame = tk.Frame(self._scrollableCanvas, bg=self.bg)     # 一个高度无限的Frame，用于包含所有行
        self._tableFrame.bind("<Configure>",
            lambda e: self._scrollableCanvas.configure(scrollregion=self._scrollableCanvas.bbox(tk.ALL)))
        self._tableFrameId = self._scrollableCanvas.create_window((0, 0), window=self._tableFrame, anchor=tk.NW)

        self._scrollableCanvas.bind_all("<MouseWheel>", self.onMouseWheel)  # 绑定鼠标滚轮事件, Windows and macOS
        self._scrollableCanvas.bind_all("<Button-4>", self.onMouseWheel)    # 绑定鼠标滚轮事件, Linux
        self._scrollableCanvas.bind_all("<Button-5>", self.onMouseWheel)    # 绑定鼠标滚轮事件, Linux
        self._scrollableCanvas.bind("<Button-1>", self.onClick) # 点击空白区，取消行高亮

        self.bind("<Configure>", self.onResize)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        # self.after_idle(self.onResize, None)

    def addColumn(self, heading: str = None, width: int = 0, minWidth: int = 0, weight: float = 0,
                  adjuster: str = None, sortKey: Callable = None, toolTip: str = None) -> Header:
        """
        添加列，并设置列的基本属性
        :param heading: 列标题
        :param width: 列宽度
        :param minWidth: 列最小宽度，宽度调整时不会小于此宽度，为0则不限
        :param weight: 列宽度权重，控制其在宽度调整时被分配到宽度的比例，为0则宽度固定
        :param adjuster: 宽度调节器，用于调节该列的宽度，放置在列标题的左侧或右侧，
                         可以设置为'left', 'right'来指定，None则不设置，列宽无法调整
        :param sortKey: 排序函数，点击列标题时的排序依据，输入参数为行对象（不包括分隔行）
        :param toolTip: 气泡提示，鼠标悬浮后显示，None则没有
        """
        if not weight: # 非权重列
            if minWidth:    # 有最小值则以最小值为宽度
                width = minWidth
            else:   # 无最小值则当前宽度就是最小值
                minWidth = width

        # 不管是否需adjuster，所有的Header都放在Frame里，通过结构一致保证pack后的高度一致
        header = Header(self._headerBar, heading, toolTip, bd=1, relief=tk.RAISED)
        header.setAdjuster(adjuster, self.onAdjusterMove)   # 设置宽度调节器的位置和回调函数
        header.width = round(width * App.dpiScale)
        header.minWidth = max(round(minWidth * App.dpiScale), Header.AdjusterWidth)
        header.weight = 0 if width else weight
        header.sortKey = sortKey
        header.bind("<ButtonRelease-1>", self.onHeaderClick)    # 绑定列头点击排序函数
        # 通过pack方法，让headerBar Frame自适应控件的尺寸，因为place方法无法自适应，
        # 当place覆盖pack的布局时，仍会保留其控件尺寸
        header.pack(side=tk.LEFT)
        self._headers.append(header)
        return header

    def newRow(self) -> WidgetRow:
        """向表内添加一个新行并返回行对象，可以将行内元素插入到该行对象"""
        row = WidgetRow(self._tableFrame)
        row.bind('<Button-1>', self.onRowSelect)   # 绑定点击事件(高亮)
        self._rows.append(row)
        self._cells.append(row.cells)
        return row

    def addSeparateRow(self, sepText: str = None, indent: int = 0, padx=0, pady=0, lineLength: int = 300):
        """
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
        sep_row = WidgetRow(self._tableFrame, isSep=True)
        canvas = tk.Canvas(sep_row, bg=self.bg, highlightthickness=0)   # 在行内加一层Canvas用于绘制分隔行
        if sepText:  # 绘制字体
            font = StyledWidget.defaultFont.copy()
            font.configure(slant=tkfont.ITALIC)  # 中文斜体需要字体支持，mac下可能无效
            canvas.create_text(indent + padx[0], pady[0], text=sepText, anchor=tk.NW, fill="darkgray", font=font)
        x0, y0, x1, y1 = canvas.bbox("all")  # 获取所有内容的边界框
        text_height = y1 - y0
        canvas.config(height=text_height + pady[0] + pady[1])
        if lineLength:  # 绘制分隔线
            lineLength *= App.dpiScale
            center_y = text_height / 2 + pady[0]
            canvas.create_line(5 * App.dpiScale, center_y, indent - 2, center_y, fill="darkgray")  # 绘制左侧线
            canvas.create_line(x1 + padx[1], center_y, lineLength, center_y, fill="darkgray")  # 绘制右侧线
        canvas.pack(fill=tk.X, expand=True)
        sep_row.pack(fill=tk.X, expand=True)
        self._rows.append(sep_row)

    def isEmpty(self) -> bool:
        """列表是否为空"""
        return len(self._rows) == 0

    def clearRows(self):
        """清除列表内的所有行，但保留列设置"""
        for widget in self._tableFrame.winfo_children():
            widget.destroy()
        self._selectedRow = None
        if self._currentSortedHeader:
            self._currentSortedHeader.setText(self._currentSortedHeader.getText()[:-1])
            self._currentSortedHeader = None
        self._rows.clear()
        self._cells.clear()

    def onRowSelect(self, event: Event):
        """行选择响应，高亮行，获取焦点"""
        if self._selectedRow:
            self._selectedRow.setHighLight(False)
        self._selectedRow = event.widget if type(event.widget) is WidgetRow else event.widget.master
        self._selectedRow.setHighLight(True)
        self._selectedRow.focus_set()

    def onClick(self, event: Event):
        """点击列表空白处响应，取消行高亮，获取焦点"""
        if self._selectedRow:
            self._selectedRow.setHighLight(False)
            self._selectedRow = None
        self.focus_set()    # 获取焦点，以便让ComboBox等失去焦点

    def onAdjusterMove(self, event: Event) -> int:
        """
        拖动Adjuster时调节列宽度
        :return: 实际移动的距离
        """
        if event.x == 0:    # y方向的动作没必要响应
            return 0

        index, target_col = next(((i, c) for i, c in enumerate(self._headers) if c == event.widget.master)) # 目标列
        isRight = target_col.adjusterPos == tk.RIGHT    # 是哪一侧的调节器，意味着那一侧的列将被重新计算宽度
        cols_after = self._headers[index+1:] if isRight else self._headers[:index]  # 左/右侧的列
        width_inc: int = min(   # 当前列宽度增量
            max(
                event.x if isRight else -event.x,   # 右侧调节器则鼠标坐标增加代表要增加列宽，左侧相反
                target_col.minWidth - target_col.width  # 当前列宽下限为自己的最小宽度
            ),
            sum(h.width - h.minWidth for h in cols_after)   # 上限为把左/右侧列挤到最小宽度
        )
        if width_inc == 0:
            return 0

        target_col.width += width_inc   # 调整目标列宽度
        total_weight_after = sum(h.weight for h in cols_after)    # 左/右侧的列的总权重

        # 将宽度变化量按权重分配给左/右侧的列，因为目标列宽度变化，其他列就要消化掉这些变化量，才能保证窗口总宽度不变 ------
        width_to_alloc = -width_inc # 待分配的变化量，初值为目标列变化量的负值
        for col in cols_after:
            if col.weight:  # 有权重列才调整宽度
                inc = max(round(width_to_alloc * col.weight / total_weight_after), col.minWidth - col.width) # 列宽增量
                col.width += inc
                width_to_alloc -= inc   # 一边分配一遍调整剩余宽度和权重，这样能保证小数宽度不会累积，最后不会剩余宽度
                total_weight_after -= col.weight

        # 重新计算所有列的权重 ------
        total_weighted_width = sum(h.width for h in self._headers if h.weight)    # 所有权重列总宽度
        for column in self._headers:
            if column.weight:   # 无权重列始终保持无权重
                column.weight = column.width / total_weighted_width

        if not self._suspendedResizing:
            self._suspendedResizing = True  # 标记已有挂起的重绘动作
            self.after_idle(self.onResize, None)    # 重新布局所有列

        return width_inc if isRight else -width_inc # 返回实际移动的距离

    def onResize(self, event: Event = None):
        """窗口尺寸变化"""
        if self.winfo_width() <= 1: # 没有宽度，说明还未载入界面
            return
        widget_width = self.winfo_width() - self._scrollbar.winfo_width() - 2 * self.bd # 去掉边框的控件宽度
        self._scrollableCanvas.itemconfig(self._tableFrameId, width=widget_width)   # 更新tableFrame的大小

        # 所有权重列新的总宽度，要把这个宽度分配给各个权重列
        width_to_alloc = max(widget_width - sum(h.width for h in self._headers if h.weight == 0), 0)
        total_weight = sum(h.weight for h in self._headers) # 总权重
        xOffset = 0
        for col in self._headers:   # 重新计算各列的宽度
            if col.weight:  # 权重列调整宽度，非权重列永远不变
                col.width = max(round(width_to_alloc * col.weight / total_weight), col.minWidth)
                width_to_alloc -= col.width # 一边分配一遍调整剩余宽度和权重，这样能保证小数宽度不会累积，最后不会剩余宽度
                total_weight -= col.weight
            col.place(x=xOffset, y=0, width=col.width, anchor=tk.NW)    # 设置列宽
            xOffset += col.width

        # 设置列元素宽度 -------
        for row_cells in self._cells:   # 遍历每一行
            xOffset = 0
            column_index = 0  # 当前列号
            for cell in row_cells:  # 遍历每个单元格
                width = sum(h.width for h in self._headers[column_index: column_index + cell.columnSpan]) # 列宽
                height = cell.widget.master.winfo_height()
                cell.widget.place(
                    x=xOffset + cell.padx[0],
                    y=height * 0.5 + cell.pady[0] - cell.pady[1],   # 以垂直方向中线为起始
                    width=width - cell.padx[0] - cell.padx[1],
                    height=height - cell.pady[0] - cell.pady[1] - 2, # 减去2px，切掉组合框上下各1px，主要为了mac下的效果
                    anchor=tk.W # 靠左且垂直居中
                )
                xOffset += width
                column_index += cell.columnSpan

        self._suspendedResizing = False # 标记挂起的重绘已完成

    def onMouseWheel(self, event: Event):
        """滚轮响应"""
        if self._scrollbar.get() == (0.0, 1.0):
            return
        if event.delta:         # Windows and macOS
            self._scrollableCanvas.yview(tk.SCROLL, -event.delta, tk.UNITS)
        elif event.num == 4:    # Linux scroll up
            self._scrollableCanvas.yview(tk.SCROLL, -1, tk.UNITS)
        elif event.num == 5:    # Linux scroll down
            self._scrollableCanvas.yview(tk.SCROLL, 1, tk.UNITS)

    def onHeaderClick(self, event: Event):
        """列标题被点击，执行排序"""
        if not self._rows:
            return
        header = event.widget
        header.orderDesc = not header.orderDesc if self._currentSortedHeader == header else False   # 设置顺序

        # 以分隔行为界，按组分别排序 -------
        sorted_rows = []
        pos = 0
        i, row = -1, True   # type: int, WidgetRow | bool
        row_iter = enumerate(self._rows)
        while row:
            i, row = next(row_iter, (i + 1, None))
            if row is None or row.isSep:   # 分隔行或超出最后一行，把前面的一组排序并加入到新列表
                sorted_rows.extend(sorted(self._rows[pos:i], key=header.sortKey, reverse=header.orderDesc))
                pos = i + 1
            if row and row.isSep:   # 分隔行原位插入
                sorted_rows.append(row)

        for row in self._rows:  # 清空所有行
            row.pack_forget()
        self._rows.clear()
        for row in sorted_rows: # 按新顺序重新添加所有行
            row.pack(fill=tk.X, expand=True)
            self._rows.append(row)

        # 设置列标题箭头 ------
        if self._currentSortedHeader:   # 把上一个排序列的箭头删掉
            self._currentSortedHeader.setText(self._currentSortedHeader.getText()[:-1])
        header.setText(header.getText() + (self.HEADIND_DESC_SURFIX if header.orderDesc else self.HEADIND_ASC_SURFIX))
        self._currentSortedHeader = header

        self._tableFrame.update_idletasks()  # 重绘挂起修改，否则可能不立刻更新
