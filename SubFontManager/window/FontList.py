import os
from dataclasses import dataclass
from enum import Flag, auto
from functools import partial
import tkinter as tk
from tkinter import filedialog, messagebox, Event
from utils import App, Lang
import ui
from font import Font, FontManager
from sub import SubStationAlpha


class TaskType(Flag):
    """任务类型掩码枚举"""
    NONE = 0    # 无任务
    UNEMBEDDING = auto()# 删除内嵌
    EMBEDDING = auto()  # 内嵌
    EXTERNAL = auto()   # 从外部内嵌
    SUBSETTING = auto() # 子集化


@dataclass
class RowItem:
    """行条目类，用于记录列表中每一行的相关信息"""
    fontName: str   # 字幕文件中使用的引用字体名
    fontNameWidget: ui.Label | None   # 字体名Label控件
    styleName: str  # 字幕文件中使用的引用样式名
    isEmbed: bool   # 字体当前来自于字幕内嵌
    embed: tk.BooleanVar        # 是否内嵌
    embedWidget: ui.Checkbox | None   # embed复选框控件
    subset: tk.BooleanVar       # 是否子集化
    subsetWidget: ui.Checkbox | None  # 子集化复选框控件
    text: set[str]  # 字体覆盖的字幕文本
    source: tk.StringVar        # 文件源，注意此变量可能会取到占位符
    sourceOptions: list[str]    # 文件源下拉列表内容
    sourceWidget: ui.Combobox | None  # 文件源组合框控件
    bold: bool      # 是否粗体
    italic: bool    # 是否斜体
    matchedPath: str    # 匹配到的字体路径
    font: Font | None   # 字体对象
    valid: bool     # 字体是否有效，通常指内嵌字体
    modified: bool = False  # 字体内嵌状态是否被修改，用于决定该行显示为粗体
    taskType: TaskType = TaskType.NONE  # 任务类型，用于在检查行状态后填写


@dataclass
class EmbeddingInfo:
    """需要内嵌的字体信息"""
    fontName: str   # 字体的内嵌文件名，即fontname:行的内容
    refNames: list[str]  # 被引用的名字表，用于在子集化后的字体中保留这些名字
    text: set[str]  # 字体覆盖的字符
    subset: bool    # 是否进行子集化
    font: Font      # 字体对象

    def merge(self, refName: str, text: set[str], subset: bool):
        """合并新的内嵌字体"""
        self.refNames.append(refName.lower())  # 收集引用名字表
        self.text.update(text)  # 合并覆盖字符集
        self.subset &= subset  # 如果有一个不子集化则都不子集化


class FontList(ui.WidgetTable):
    """界面中的字体列表类，负责维护所有字体状态和操作"""

    class SrcCmbOptions:
        """Source Combobox Options"""
        EMBED = '<%s>' % Lang['Use embedded font']
        SYSTEMFONT = '<%s>' % Lang['Use system font']
        SRCDIR = '<%s>' % Lang['Use font from same directory']
        BROWSE = '<%s...>' % Lang['Select font path manually']
        EXTRACT = '<%s...>' % Lang['Extract embedded font']
        NOSRC = '<%s>' % Lang['No source']
        All = (EMBED, SYSTEMFONT, SRCDIR, BROWSE, EXTRACT)

    EMBED_NAME_PREFIX = 'embed:/' if App.isMac else 'embed:\\'  # 嵌入字体名的前缀
    WARNING_MAX_CHAR_COUNT = 500    # 警告内嵌字数过多的门槛
    WARNING_MAX_FONT_SIZE = 1024000 # 警告内嵌字幕文件过大的门槛

    def __init__(self, master):
        super().__init__(master=master)
        self.subtitleObj: SubStationAlpha | None = None

        # 内嵌列
        self.addColumn(Lang['Emb'], width=40, sortKey=lambda r: r.data.embed.get(), toolTip=Lang['Embedding'])
        # 字体名列
        weight = float(App.Config.get('General', 'font_column_weight', 1))
        self.addColumn(Lang['Font'], weight=weight, sortKey=lambda r: r.data.fontName,
                       minWidth=100, adjuster=tk.RIGHT)
        # 样式列
        self.addColumn(Lang['Style'], width=60, sortKey=lambda r: r.data.styleName)
        # 字数列
        width = int(App.Config.get('General', 'count_column_width', 55))
        self.addColumn(Lang['Count'], width=width, sortKey=lambda r: len(r.data.text),
                       minWidth=50, adjuster=tk.RIGHT, toolTip=Lang['Non-repeating characters count'])
        # 子集化列
        self.addColumn(Lang['Sub'], width=40, sortKey=lambda r: r.data.subset.get(), toolTip=Lang['Subsetting'])
        # 文件源列
        weight = float(App.Config.get('General', 'source_column_weight', 2))
        self.addColumn(Lang['File source'], weight=weight, sortKey=lambda r: r.data.sourceWidget.get(),
                       minWidth=80, adjuster=tk.LEFT)

        self.bind("<Destroy>", self.onDestroy)  # 绑定关闭事件响应

    def loadSubtitle(self, subObj: SubStationAlpha):
        """载入字体文件并将其中的字体和信息添加到列表"""
        # 清空列表 -------
        self.subtitleObj = subObj
        if self._rows:
            self.clearRows()

        # 收集字幕中出现过的所有字体
        subFontDescs = self.subtitleObj.gatherFonts()
        if not subFontDescs:
            return
        subFontDescs.sort(key=lambda f: f.isEmbed)  # 将内嵌字体排到列表后面，以便插入分隔行
        adding_embed_items = False  # 是否已经开始添加内嵌字体行

        # 向列表内添加一个个字体行 -----------
        for fontDesc in subFontDescs:
            if not adding_embed_items and fontDesc.isEmbed:  # 开始添加内嵌字体条目时，插入一个分隔行
                adding_embed_items = True
                self.addSeparateRow(Lang['Embedded fonts'], indent=38 if App.isMac else 36, padx=5, pady=4)

            # 生成用于显示的样式名字，如Bold, Italic, Bold Italic ------
            style_name = 'Bold' if fontDesc.bold else ''
            style_name += (' Italic' if style_name else 'Italic') if fontDesc.italic else ''
            style_name = Lang[style_name] if style_name else Lang['Regular']

            # 该行字体的所有相关属性 ------
            row_item = RowItem(  # 保存行的所有信息和变量
                fontName=fontDesc.fontName, # 字体名
                fontNameWidget=None,        # 字体名Label控件
                styleName=style_name,       # 样式名
                embed=tk.BooleanVar(),      # 是否内嵌
                embedWidget=None,           # embed复选框控件
                subset=tk.BooleanVar(),     # 是否子集化
                subsetWidget=None,          # 子集化复选框控件
                source=tk.StringVar(),      # 字体文件源，注意此变量可能会取到占位符
                sourceOptions=list(self.SrcCmbOptions.All),  # 文件源下拉列表内容，默认全有
                sourceWidget=None,          # 文件源组合框控件，在添加行时填写
                # 以下是不直接参与显示的属性 -----
                text=fontDesc.text,         # 字体覆盖的文本
                isEmbed=fontDesc.isEmbed,   # 当前找到的字体源是否是内嵌字体
                bold=fontDesc.bold,         # 是否粗体
                italic=fontDesc.italic,     # 是否斜体
                matchedPath='' if fontDesc.font is None else fontDesc.font.path,    # 按系统逻辑匹配到的字体路径
                font=fontDesc.font,         # 行关联的字体对象，可根据用户选择重新匹配
                valid=fontDesc.valid        # 字体是否有效
            )

            if row_item.isEmbed:  # 如果是内嵌字体
                row_item.embed.set(row_item.valid)  # 对有效字体勾上内嵌复选框
                row_item.subset.set(False)  # 内嵌字体默认不勾选子集化复选框
                row_item.source.set(self.EMBED_NAME_PREFIX + row_item.matchedPath)  # 文件源设置为embed:/...
            else:
                row_item.embed.set(False)   # 不勾内嵌复选框
                row_item.subset.set(True)   # 勾上集化复选框
                row_item.source.set(row_item.matchedPath)  # 填写文件源组合框
                # 非内嵌字体的条目不应该有使用提取内嵌字体的选项，去掉两个列表选项
                row_item.sourceOptions.remove(self.SrcCmbOptions.EMBED)
                row_item.sourceOptions.remove(self.SrcCmbOptions.EXTRACT)

            # 添加行和行内控件 --------------
            row_frame = self.newRow()   # 新行
            # Checkbox：是否内嵌
            row_item.embedWidget = ui.Checkbox(row_frame, variable=row_item.embed, text='')
            # row_item.embedWidget.bind("<ButtonRelease-1>", partial(self.onEmbedClicked, rowItem=row_item))
            row_item.embedWidget.bind("<ButtonRelease-1>", partial(self.onEmbedClicked, rowItem=row_item))
            row_frame.addCell(row_item.embedWidget, padx=(8 if App.isMac else 11, 0))
            # Label：字体名，无效字体加删除线和后缀，因为Mac下不支持文字删除线
            row_item.fontNameWidget = ui.Label(row_frame, overstrike=not row_item.valid, anchor=tk.W,
                text=row_item.fontName + (f' {Lang['(Corrupted)']}' if not row_item.valid else ''))
            row_frame.addCell(row_item.fontNameWidget, pady=(0, 1))
            # Label：样式名
            row_frame.addCell(ui.Label(row_frame, text=row_item.styleName, overstrike=not row_item.valid,
                                       anchor=tk.CENTER), pady=(0, 1))
            # Label：字数统计
            row_frame.addCell(ui.Label(row_frame, text=str(len(row_item.text)), anchor=tk.E), padx=(0, 2), pady=(0, 1))
            # Checkbox：子集化
            row_item.subsetWidget = ui.Checkbox(row_frame, variable=row_item.subset,
                                                state=tk.NORMAL if row_item.valid else tk.DISABLED)
            row_item.subsetWidget.bind("<ButtonRelease-1>", partial(self.onSubsetClicked, rowItem=row_item))
            row_frame.addCell(row_item.subsetWidget, padx=(8 if App.isMac else 11, 0))
            # Combobox：文件源
            row_item.sourceWidget = ui.Combobox(row_frame, placeholder=self.SrcCmbOptions.NOSRC, background=self.bg,
                                                state=tk.NORMAL if row_item.valid else tk.DISABLED,
                                                textvariable=row_item.source, values=row_item.sourceOptions)
            row_item.sourceWidget.bind("<<ComboboxSelected>>", partial(self.onSourceComboSelect, rowItem=row_item))
            row_item.source.trace_add('write', partial(self.onSourceChange, rowItem=row_item))
            row_frame.addCell(row_item.sourceWidget)

            row_frame.data = row_item   # 让row_item跟着行走
            # self.addRow(row_frame)      # 添加行
            self.setRowStatus(row_item) # 设置行内各个控件的启用禁用状态

        self.update_idletasks()  # 应用挂起的控件修改，否则可能不立刻更新
        self._suspendedResizing = True  # 标记已有挂起的重绘动作
        self.after_idle(self.onResize, None)  # 给新增的行控件设置好布局位置

    def checkTaskValidity(self) -> bool:
        """检查表中任务设置是否正确可执行，必要时弹窗询问，同时会给每一行找到任务类型和新字体源"""
        row_items: list[RowItem] = [r.data for r in self._rows if not r.isSep]  # 去掉分割行，获取所有的行信息
        warnings: list[str] = []  # 警告文本列表

        # 检查是否有多个同家族字体未全部内嵌 -------------
        row_dict: dict[str, list[RowItem]] = {} # 用字体名索引行信息，用于合并同字体的多个行
        for row_item in row_items:  # 合并同家族名的字体行
            if not row_item.isEmbed:    # 仅限外部字体源
                if row_item.fontName in row_dict:
                    row_dict[row_item.fontName].append(row_item)
                else:
                    row_dict[row_item.fontName] = [row_item]

        problematic_font_names = [] # 有问题的字体名表
        for name, items in row_dict.items():
            if len(items) > 1:  # 同家族多个字体，且嵌入选择不一致的
                embed = items[0].embed.get()
                if next((row_item for row_item in items if row_item.embed.get() != embed), None):
                    problematic_font_names.append(name)

        if problematic_font_names:
            answer = messagebox.askyesnocancel(Lang['Reminding'],   # 弹窗询问
                Lang["Fonts {ff} contain multiple styles, but not all of them have been selected for embedding. "
                     "This may cause subtitle display issues, as unembedded styles will still reference the "
                     "embedded styles as their source during playback, resulting in incorrect rendering. "
                     "Do you want to embed all other styles of these font?"]
                     .format(ff=f'"{'", "'.join(problematic_font_names)}"'))
            if answer is None:  # 选择取消
                return False    # 表示操作取消
            elif answer:    # 选择是，把同字体的其他行都勾选上
                for name in problematic_font_names:
                    for row_item in row_dict[name]:
                        if not row_item.sourceWidget.isBlank:   # 文件源为空的不勾选
                            row_item.embed.set(True)    # 勾选同字体的其他行
            # else # 选择否，原样不动

        # 确定每行的任务类型、文件是否存在，以及文件内是否都包含指定的字体 -------------
        for row_item in row_items:
            file_path = row_item.sourceWidget.get() # 文件源组合款内的值
            row_item.taskType = TaskType.NONE   # taskType可能保留了上一轮未成功的执行中检查的结果，所以要先置空

            if row_item.isEmbed:    # 内嵌字体
                if row_item.embed.get():    # 已勾选内嵌框
                    if file_path.startswith(self.EMBED_NAME_PREFIX):    # 填写的内嵌路径
                        file_path = file_path[len(self.EMBED_NAME_PREFIX):] # 切掉路径头的embed:/
                        if file_path == row_item.matchedPath:   # 填写路径和现有匹配路径相同
                            if row_item.subset.get():   # 子集化勾选
                                row_item.taskType = TaskType.SUBSETTING | TaskType.EMBEDDING    # 内嵌字体子集化
                        else:   # 这是从一个内嵌源改为另一个，无意义的
                            warnings.append(Lang['Embedded file path {p} invalid.'].format(p=file_path))
                        continue
                    else:   # 内嵌字体填写的外部路径，删除内嵌字体再嵌入外部字体
                        row_item.taskType = TaskType.UNEMBEDDING | TaskType.EMBEDDING | TaskType.EXTERNAL
                else:   # 未勾选内嵌框
                    row_item.taskType = TaskType.UNEMBEDDING    # 删除内嵌字体
                    continue
            elif not row_item.embed.get():  # 非内嵌字体，未勾选内嵌框
                continue
            elif file_path.startswith(self.EMBED_NAME_PREFIX):  # 非内嵌字体，勾选内嵌框，填写的内嵌路径
                warnings.append(Lang['Embedded file path {p} cannot be used as the source for external embedding.']
                                .format(p=file_path))
                continue
            else:   # 非内嵌字体，勾选内嵌框，填写的外部路径
                row_item.taskType = TaskType.EMBEDDING | TaskType.EXTERNAL  # 外部字体嵌入

            if row_item.subset.get():   # 判断是否需要子集化
                row_item.taskType |= TaskType.SUBSETTING

            # 检查文件源路径是否存在以及路径是否包含指定的字体，并找到相应的字体对象 -------------
            if row_item.font and file_path == row_item.font.path:   # 填写路径和现有路径相同
                continue    # 路径已知，无需检查了
            if not os.path.isfile(file_path): # 路径不是文件
                warnings.append(Lang["File {p} does not exist."].format(p=file_path))
            elif not os.access(file_path, os.R_OK): # 路径不可访问
                warnings.append(Lang["Unable to read file {p}."].format(p=file_path))
            else:   # 正常外部路径
                font = FontManager(path=file_path).match(
                    row_item.fontName, row_item.bold, row_item.italic, FontManager.LOCAL)
                if font is None:   # 在路径中没找到字体
                    warnings.append(Lang['File {p} does not contain font "{fs}".']
                                    .format(p=file_path, fs=f"{row_item.fontName} {Lang[row_item.styleName]}"))
                else:   # 这里将字体匹配结果保存到row_item，如果本次执行失败，在下次执行时还会有效
                    row_item.font = font

        if warnings:  # 检查是否有警告消息
            messagebox.showerror(Lang['Error'], '\n'.join(warnings))
            return False  # 表示操作取消
        elif not next((ri for ri in row_items if ri.taskType), None): # 检查是否有任务可以执行
            messagebox.showerror(Lang['Error'], Lang['No task to execute.'])
            return False    # 表示操作取消

        # 检查大字体的子集化是否已勾选 -------------
        problematic_fonts = [] # 有问题的字体表
        for row_item in row_items:
            if (TaskType.EXTERNAL in row_item.taskType and TaskType.SUBSETTING not in row_item.taskType
                    and os.path.getsize(row_item.sourceWidget.get()) > self.WARNING_MAX_FONT_SIZE):  # 文件过大且不子集化
                problematic_fonts.append(row_item)

        if problematic_fonts:
            answer = messagebox.askyesnocancel(Lang['Reminding'],   # 弹窗询问
                Lang["File source of {ff} is large and subsetting is not selected, "
                     "embedding them directly may significantly increase the file size of subtitle. "
                     "Do you want to subset the fonts before embedding it?"]
                     .format(ff=', '.join(f'"{r.fontName} {Lang[r.styleName]}"' for r in problematic_fonts)))
            if answer is None:  # 选择取消
                return False    # 表示操作取消
            elif answer:    # 选择是，把字体的子集化都勾选上
                for row_item in problematic_fonts:
                    row_item.subset.set(True)   # 勾字体的子集化复选框
            # else # 选择否，原样不动

        return True

    def applyEmbedding(self, savePath: str = None):
        """
        执行列表内配置的字体内嵌任务
        :param savePath: 新字幕保存路径，缺省则写入到源文件
        """
        # 去掉分割行，去掉无任务行，获取其他所有行的信息
        row_items: list[RowItem] = [r.data for r in self._rows if not r.isSep and r.data.taskType]
        fontList_bak = self.subtitleObj.fontDict.copy()  # 万一写入错误时用来恢复的备份

        # 合并重复的需要内嵌的字体，删除需要删除的内嵌字体 -------------
        fonts_to_embed: dict[str, EmbeddingInfo] = {}  # 按文件路径索引的待内嵌字体，用于合并重复的字体源
        for row_item in row_items:
            font = row_item.font
            # 如果任务包括删除内嵌操作 -------
            if TaskType.UNEMBEDDING in row_item.taskType:
                # 内嵌字体可能是多个行的文件源，所以该字体可能已经被删除过了，因此需要检查一下
                font_codes = self.subtitleObj.fontDict.get(row_item.matchedPath, [])
                if len(font_codes) == 1:
                    self.subtitleObj.fontDict.pop(row_item.matchedPath)
                elif font_codes:
                    font_codes.pop(font.index)

            # 如果任务包括内嵌操作 -------
            if TaskType.EMBEDDING in row_item.taskType:
                # 生成一个不重复的内嵌字体名 -------
                if TaskType.EXTERNAL in row_item.taskType:  # 外部文件字体源
                    file_name = os.path.splitext(os.path.split(font.path)[1])[0]    # 拆解出无后缀文件名
                    if row_item.subset.get() and not file_name.endswith('_subset'): # 如果不是_subset结尾，加一个_subset
                        file_name += '_subset'
                    i = 2
                    embed_name = file_name
                    while embed_name + '.ttf' in self.subtitleObj.fontDict:
                        embed_name = file_name + f'_{i}'    # 字体名后面加_编号
                        i += 1
                    embed_name += '.ttf'
                else:   # 内嵌字体源（走到这里都是需要子集化）
                    embed_name = font.path  # 直接保留原内嵌名字不变

                # 合并到待嵌入字体表 -------
                if font.path in fonts_to_embed: # 如果字体已存在，合并多次引用
                    fonts_to_embed[font.path].merge(row_item.fontName, row_item.text, row_item.subset.get())
                else:   # 如果不存在，新建内嵌字体信息
                    fonts_to_embed[font.path] = EmbeddingInfo(
                        embed_name, [row_item.fontName.lower()], row_item.text, row_item.subset.get(), font)

        # 执行内嵌 -------------
        try:
            for embed_info in fonts_to_embed.values():  # 遍历每一个待内嵌字体并执行内嵌
                font = embed_info.font
                if embed_info.subset:   # 子集化
                    font.subset(''.join(embed_info.text), embed_info.refNames)
                    font.path = embed_info.fontName # 子集化之后字体会变内存字体，原路径失去意义，换成内嵌名
                self.subtitleObj.fontDict.add(font.read(), embed_info.fontName, font.index, True)   # 内嵌
            self.subtitleObj.save(savePath)  # 保存字幕文件
        except Exception as e:   # 内嵌或删除内嵌或保存文件出错
            self.subtitleObj.fontDict = fontList_bak
            raise e

    @classmethod
    def setRowStatus(cls, rowItem: RowItem):
        """根据当前行的填写情况设置行内各控件的状态"""
        if rowItem.sourceWidget.isBlank:
            rowItem.embed.set(False)    # 文件源为空时强制取消内嵌勾选
            rowItem.embedWidget.configure(state=tk.DISABLED)    # 并禁用内嵌复选框
        else:
            rowItem.embedWidget.configure(state=tk.NORMAL)
        # 条目修改状态逻辑
        if rowItem.isEmbed:
            rowItem.modified = (not rowItem.embed.get() or rowItem.subset.get()
                                or rowItem.sourceWidget.get() != cls.EMBED_NAME_PREFIX + rowItem.matchedPath)
        else:
            rowItem.modified = rowItem.embed.get()
        # 根据修改状态设置粗体
        rowItem.fontNameWidget.setBold(rowItem.modified)

    def onEmbedClicked(self, event: Event, rowItem: RowItem):
        """内嵌复选框状态改变"""
        if (not (0 <= event.x <= event.widget.winfo_width() and 0 <= event.y <= event.widget.winfo_height())
                and str(rowItem.embedWidget.cget('state')) == 'disabled'):  # 禁用的控件和控件区域之外的事件不用响应
            return

        if not rowItem.embed.get(): # 注意这里能获得的是变更之前的状态
            char_count = len(rowItem.text)
            font_name_style = f"{rowItem.fontName} {Lang[rowItem.styleName]}"
            checked: bool | None = None
            if not rowItem.valid:   # 无效内嵌行警告
                checked = messagebox.askokcancel(Lang['Reminding'],
                    Lang['Embedded font file "{f}" is corrupted, are you sure you want to keep it in the subtitle file?']
                        .format(f=rowItem.fontName))
            elif char_count == 0:   # 覆盖字符为0警告
                checked = messagebox.askokcancel(Lang['Reminding'],
                    Lang['Font "{fs}" does not cover any charactor, are you sure you want to embed it?']
                        .format(fs=font_name_style))
            elif char_count >= self.WARNING_MAX_CHAR_COUNT: # 覆盖字符过多警告
                checked = messagebox.askokcancel(Lang['Reminding'],
                    Lang['Font "{fs}" covers {c} charactors, embedding it may significantly increase '
                         'the size of the subtitle file, are you sure you want to proceed?']
                        .format(fs=font_name_style, c=char_count))

            if checked is not None:     # 如果弹出过警告
                rowItem.embedWidget.focus_set() # 弹窗之后需手动取回焦点
                if checked is False:    # 如果用户选择了否
                    return 'break'  # 返回break阻止复选框状态改变

        # 内嵌复选框状态变化后，需要更新行状态，但要等新值生效后再更新
        self.after_idle(self.setRowStatus, rowItem)

    def onSubsetClicked(self, event: Event, rowItem: RowItem):
        """子集化复选框状态改变"""
        if (not (0 <= event.x <= event.widget.winfo_width() and 0 <= event.y <= event.widget.winfo_height())
                and str(rowItem.embedWidget.cget('state')) == 'disabled'):  # 禁用的控件和控件区域之外的事件不用响应
            return
        self.after_idle(self.setRowStatus, rowItem)

    def onSourceChange(self, var_name, index, mode, rowItem: RowItem):
        """文件源组合框内容改变"""
        # 在控件初始化阶段和下拉菜单填写临时值的瞬间都不需要响应
        if rowItem.sourceWidget and rowItem.source.get() not in self.SrcCmbOptions.All:
            self.setRowStatus(rowItem)    # 当文件源变化时，重设置行状态

    def onSourceComboSelect(self, event: Event, rowItem: RowItem):
        """文件源组合框选项选择"""
        cmb_src = rowItem.sourceWidget  # 组合框对象
        src_text = cmb_src.getRaw() # 组合框内的文本
        src_text_new = ''   # 组合款内的新内容

        if src_text == self.SrcCmbOptions.EMBED:         # 使用内嵌字体，能选择这个选项的都是内嵌字体
            src_text_new = self.EMBED_NAME_PREFIX + rowItem.matchedPath    # 将文件源内的路径设置为embed:/...
        elif src_text == self.SrcCmbOptions.SYSTEMFONT:  # 使用系统字体
            font = self.subtitleObj.fontMgr.match(rowItem.fontName, rowItem.bold, rowItem.italic, FontManager.SYSTEM)
            src_text_new = font.path if font else ''
        elif src_text == self.SrcCmbOptions.SRCDIR:      # 使用同目录下的字体
            font = self.subtitleObj.fontMgr.match(rowItem.fontName, rowItem.bold, rowItem.italic, FontManager.LOCAL)
            src_text_new = font.path if font else ''
        elif src_text == self.SrcCmbOptions.BROWSE:      # 手动选择路径
            src_text_new = filedialog.askopenfilename(
                filetypes=[(Lang["Font File"], "*.ttf *.ttc *.otf"), (Lang["All files"], "*.*")])
            cmb_src.focus_force()
            if not src_text_new:
                src_text_new = cmb_src.currentValue
        elif src_text == self.SrcCmbOptions.EXTRACT:     # 提取内嵌字体，能选择这个选项的都是内嵌字体
            save_path = filedialog.asksaveasfilename(
                initialdir=os.path.dirname(self.subtitleObj.filePath),
                initialfile=rowItem.font.path,
                defaultextension=".ttf",
                filetypes=[(Lang["TrueType Font"], "*.ttf"), (Lang["All files"], "*.*")]
            )
            if save_path:   # 如果选择了路径，则执行保存
                try:
                    rowItem.font.save(save_path)
                except Exception as e:
                    messagebox.showerror(Lang['Error'], str(e))
            cmb_src.master.focus_set()
            src_text_new = cmb_src.currentValue

        cmb_src.set(src_text_new)
        cmb_src.selection_clear()   # 清除组合框中的选区，否则框内会有半截选区
        cmb_src.icursor(tk.END)     # 将光标移动到末尾
        if not src_text_new:    # 如果为空，则移走焦点，否则占位符（"<无来源>"）不显示
            cmb_src.master.focus_set()

    def onDestroy(self, event: Event):
        """关闭窗口响应，保存列宽配置"""
        if event.widget is not self:
            return None
        # 保存三个可调宽度列的宽度
        App.Config.set('General', 'font_column_weight', self._headers[1].weight)
        App.Config.set('General', 'count_column_width', self._headers[3].width)
        App.Config.set('General', 'source_column_weight', self._headers[5].weight)
        return 'break'  # 阻止Destroy事件继续无意义的冒泡上浮
