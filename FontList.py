import os
import io
import tkinter as tk
from tkinter import filedialog, messagebox, font as tkfont
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
import ui
from FontManager import FontManager
from SubStationAlpha import SubStationAlpha


class FontList(ui.WidgetTable):
    SrcCmbOptions = {  # Source Combobox Options
        'EMBED': '<使用内嵌字体>',
        'SYSTEMFONT': '<使用系统字体>',
        'SRCDIR': '<使用同目录下的字体>',
        'BROWSE': '<手动选择路径...>',
        'EXTRACT': '<提取内嵌字体...>'
    }
    Placeholder_NOSRC = '<无来源>'
    EMBED_NAME_PREFIX = 'embed:/'  # 嵌入字体名的前缀
    STYLE_TEXTS = {'regular': '常规', 'bold': '粗体', 'italic': '斜体', 'bold italic': '粗斜体'}   # 样式名称表

    def __init__(self, master):
        super().__init__(master=master)
        self.columnWidth = []
        self.itemList = []  # [{fontName, isEmbed, isSubset, source, ...}]
        self.fontMgr = FontManager()
        self.subtitleObj = None

        # 列设置 -----------------
        self.addColumn('内嵌', width=30)
        self.addColumn('字体', weight=1, minWidth=100, adjuster='right')
        self.addColumn('样式', width=60)
        self.addColumn('字数', width=60, minWidth=40, adjuster='right')
        self.addColumn('子集', width=30)
        self.addColumn('文件源', weight=2, minWidth=80, adjuster='left')

    def loadSubtitle(self, subObj: SubStationAlpha = None):
        """载入字体文件并将其中的字体和信息添加到列表"""
        # 清空列表 -------
        self.subtitleObj = subObj
        if self.itemList:
            self.itemList.clear()
            self.clearRows()
        if subObj is None:
            return

        # 创建FontManager并索引同目录下的字体文件
        self.fontMgr = FontManager(os.path.dirname(self.subtitleObj.filePath))
        fontList = self.subtitleObj.gatherFonts()
        if not fontList:
            return

        fontList.sort(key=lambda x: x['embedName'] != '')    # 将内嵌字体排到列表后面
        adding_embed_items = False

        for item in fontList:
            # 开始添加内嵌字体条目时，插入一个分隔行
            if not adding_embed_items and item['embedName'] != '':
                adding_embed_items = True
                self.addSeparateRow('内嵌字体')

            # 保存行所有信息和变量的dict
            row_item = {
                'fontName': item['fontname'],       # 字体名
                'fontNameWidget': None,             # 字体名Label控件
                'style': item['style'],             # 样式名
                'embedName': item['embedName'],     # 已内嵌字体的内嵌文件名
                'embed': tk.BooleanVar(),           # 是否内嵌
                'embedWidget': None,                # embed复选框控件
                'subset': tk.BooleanVar(),          # 是否子集化
                'subsetWidget': None,               # 子集化复选框控件
                'text': item['text'],               # 字体覆盖的文本
                'source': tk.StringVar(),           # 文件源
                'sourceOptions': list(self.SrcCmbOptions.values()),     # 文件源下拉列表内容
                'sourceWidget': None,       # 文件源组合框控件，在添加行时填写
                'modified': False           # 字体内嵌状态是否被修改
            }
            self.itemList.append(row_item)

            if row_item['embedName']:  # 如果是内嵌字体
                row_item['embed'].set(True)
                row_item['subset'].set(False)    # 内嵌字体默认不勾选子集化
                row_item['source'].set(self.EMBED_NAME_PREFIX + row_item['embedName'])
            else:
                row_item['embed'].set(False)
                row_item['subset'].set(True)
                row_item['source'].set(self.fontMgr.findFont(row_item['fontName'])[0])
                # 无内嵌字体的条目也不应该有提取内嵌字体的选项
                row_item['sourceOptions'].remove(self.SrcCmbOptions['EMBED'])
                row_item['sourceOptions'].remove(self.SrcCmbOptions['EXTRACT'])
            # 这里使用了一个闭包技巧，利用函数的默认参数是在定义时计算的特点，将此时的row_item传给回调函数
            row_item['source'].trace_add('write', lambda v, t, m, r=row_item: self.onSourceChange(r))

            # 添加行和行内控件 --------------
            row_frame = self.newRow()
            # 复选框：是否内嵌
            row_item['embedWidget'] = tk.Checkbutton(row_frame, variable=row_item['embed'], bg=self.bg)
            row_item['embedWidget'].bind("<Button-1>", lambda e, r=row_item: self.onEmbedClicked(r))
            # 文本：字体名
            row_item['fontNameWidget'] = tk.Label(row_frame, text=row_item['fontName'], anchor='w', bg=self.bg)
            # 文本：样式名
            tk.Label(row_frame, text=self.STYLE_TEXTS.get(row_item['style'], ''), anchor='center', bg=self.bg)
            # 文本：字数统计
            tk.Label(row_frame, text=str(len(row_item['text'])) + ' ', anchor='e', bg=self.bg)
            # 复选框：子集化
            row_item['subsetWidget'] = tk.Checkbutton(row_frame, variable=row_item['subset'], bg=self.bg)
            row_item['subsetWidget'].bind("<Button-1>", lambda e, r=row_item: self.onSubsetClicked(r))
            # 组合框：文件源
            row_item['sourceWidget'] = ui.PlaceholderCombobox(
                row_frame, placeholder=self.Placeholder_NOSRC, textvariable=row_item['source'],
                values=row_item['sourceOptions'], background=self.bg)
            row_item['sourceWidget'].bind("<<ComboboxSelected>>", lambda e, r=row_item: self.onSourceComboSelect(r))

            self.addRow(row_frame)
            self.setRowStatus(row_item)

        self.update_idletasks()  # 强制重绘，否则可能导致布局错误
        self.onResize()

    def applyEmbedding(self, savePath: str = None) -> int:
        """
        应用字体内嵌
        :param savePath: 保存路径，缺省则写入到源文件
        :return: 0: 成功，1: 列表参数错误，未执行内嵌，2: 仅部分文件内嵌成功
        """
        warnings = []
        have_task = False

        # 检查是否有可做的任务、文件是否存在，以及文件内是否都包含指定的字体 -------------
        for row_item in self.itemList:
            # 检查是否有可做的任务 -------------
            if row_item['embed'].get():
                if row_item['embedName'] and not row_item['subset'].get():   # 原内嵌字体再次子集化
                    continue
                else:
                    have_task = True
            else:     # 未勾选的字体不用检查
                if row_item['embedName']:   # 原内嵌字体未勾选内嵌，意味着要删除内嵌
                    have_task = True
                continue

            # 文件是否存在以及文件内是否都包含指定的字体 -------------
            src = row_item['sourceWidget'].get()
            index = None
            if src.startswith(self.EMBED_NAME_PREFIX):
                filename = src[len(self.EMBED_NAME_PREFIX):]
                if filename in self.subtitleObj.fontList:
                    index = self.subtitleObj.embedFontMgr.indexOfFontInPath(
                        filename, row_item['fontName'], row_item['style'])
                else:
                    warnings.append(f"内嵌文件 {src} 不存在。")
            elif not os.path.isfile(src):
                warnings.append("'%s %s'的文件源'%s'不存在。" %
                                (row_item['fontName'], self.STYLE_TEXTS.get(row_item['style'], ''), src))
            elif not os.access(src, os.R_OK):
                warnings.append("'%s %s'的文件源'%s'无法读取。" %
                                (row_item['fontName'], self.STYLE_TEXTS.get(row_item['style'], ''), src))
            else:
                index = self.fontMgr.indexOfFontInPath(src, row_item['fontName'], row_item['style'])

            if index == -1:
                warnings.append("文件 %s 中不包含字体 %s %s。" % (src, row_item['fontName'], row_item['style']))
            elif index is not None:
                row_item['index'] = index

        if not have_task:
            messagebox.showerror("错误", '没有可执行的任务。')
            return 1
        elif warnings:
            messagebox.showerror("错误", '\n'.join(warnings))
            return 1

        # 检查大字体的子集化是否勾选 -------------
        for row_item in self.itemList:
            if not row_item['embedName'] and not row_item['subset'].get()\
                    and os.path.getsize(row_item['sourceWidget'].get()) > 1024000:    # 不子集化且文件>100K
                warnings.append(f"{row_item['fontName']} {row_item['style']} 的文件源较大且未选择子集化，")
        if warnings:
            if not messagebox.askyesno("提示", "%s\n将它%s直接内嵌可能会导致字幕文件体积显著增大，你确定要这样做？" %
                                             ('\n'.join(warnings), '们' if len(warnings) > 1 else '')):
                return 1

        # 执行内嵌 -------------
        for row_item in self.itemList:
            if row_item['embed'].get():
                src = row_item['sourceWidget'].get()
                # 读取文件 -------------
                if src.startswith(self.EMBED_NAME_PREFIX):  # 内嵌字体源
                    if not row_item['subset'].get():  # 已经内嵌且不需要子集化的字体，直接跳过
                        continue
                    # 内嵌文件名直接用指定的，可能会重复，重复就覆盖，也就是重新嵌入了
                    embed_name = src[len(self.EMBED_NAME_PREFIX):]
                    ttf_bytes = self.subtitleObj.getEmbedFont(embed_name, row_item['index'])
                    ttf_font = TTFont(ttf_bytes)
                else:
                    # 拆解出文件名和后缀名
                    _, file_name = os.path.split(src)
                    file_name, ext = os.path.splitext(file_name)
                    # 生成一个不重复的内嵌文件名
                    embed_name = file_name + '_subset'
                    i = 2
                    while embed_name + '.ttf' in self.subtitleObj.fontList:
                        embed_name += f'_{i}'
                        i += 1
                    embed_name += '.ttf'
                    # 打开文件
                    if ext.lower() == '.ttc':  # TTC文件
                        font_collection = TTCollection(src)
                        ttf_font = [font_collection[row_item['index']]]
                        # for i, font in enumerate(font_collection):
                        #     if i != row_item['index']:
                        #         font.close()
                    else:  # TTF文件
                        ttf_font = TTFont(src)

                # 子集化 -------------
                if row_item['subset'].get():
                    # 找出与引用名称匹配的字体名称，子集化可能会把它删掉，导致无法匹配
                    name_record = None    # 字体名称记录
                    name_list = ttf_font['name'].names
                    for record in name_list:
                        if record.nameID == 1 and \
                                FontManager.decodeNameRecord(record).lower() == row_item['fontName'].lower():
                            name_record = record
                            break
                    else:
                        for record in name_list:
                            if record.nameID == 4 and \
                                    FontManager.decodeNameRecord(record).lower() == row_item['fontName'].lower():
                                name_record = record
                                break

                    FontManager.fontSubset(ttf_font, row_item['text'])    # 子集化

                    # 检查名表，如果匹配的字体名称被删掉了，将它加回来
                    for record in ttf_font['name'].names:
                        if record.nameID == name_record.nameID and record.platformID == name_record.platformID \
                                and record.langID == name_record.langID and record.string == name_record.string:
                            break
                    else:
                        ttf_font['name'].names.append(name_record)

                # 保存字体文件到内存并内嵌到字幕文件 -------------
                ttf_bytes_subset = io.BytesIO()
                ttf_font.save(ttf_bytes_subset)  # 保存到内存
                ttf_bytes_subset.seek(0)
                self.subtitleObj.embedFont(embed_name, ttf_bytes_subset, overwrite=True, index=row_item['index'])
                ttf_font.close()  # 关闭字体资源
                ttf_bytes_subset.close()

            elif row_item['embedName']:    # 原内嵌字体未勾选内嵌，意味着要删除内嵌
                font_codes = self.subtitleObj.fontList[row_item['embedName']]
                if len(font_codes) == 1:
                    self.subtitleObj.fontList.pop(row_item['embedName'])
                else:
                    font_codes.pop(row_item['index'])

        self.subtitleObj.save(savePath)    # 保存字幕文件

    @classmethod
    def setRowStatus(cls, rowItem: dict):
        """根据当前行的填写情况设置行内各控件的状态"""
        if rowItem['sourceWidget'].isblank:
            rowItem['embed'].set(False)    # 文件源为空时强制取消内嵌勾选
            rowItem['embedWidget'].configure(state=tk.DISABLED)    # 并禁用内嵌复选框
        else:
            rowItem['embedWidget'].configure(state=tk.NORMAL)
        # 条目修改状态逻辑
        if rowItem['embedName']:
            rowItem['modified'] = (not rowItem['embed'].get() or rowItem['subset'].get()
                                   or rowItem['sourceWidget'].get() != cls.EMBED_NAME_PREFIX + rowItem['embedName'])
        else:
            rowItem['modified'] = rowItem['embed'].get()
        # 根据修改状态设置粗体
        rowItem['fontNameWidget'].configure(font=tkfont.Font(
            weight=tkfont.BOLD if rowItem['modified'] else tkfont.NORMAL))

    def onEmbedClicked(self, rowItem: dict):
        if rowItem['embedWidget'].cget('state') == 'disabled':  # 禁用的控件不用响应
            return
        checked = not rowItem['embed'].get()
        char_count = len(rowItem['text'])
        if not rowItem['embed'].get() and (char_count > 99 or char_count == 0):
            self.update_idletasks()    # 重绘界面，否则在下面的弹窗期间行选择状态不会更新
            checked = ((char_count > 99 and messagebox.askokcancel(
                '提示', f"{rowItem['fontName']} 字体覆盖了{char_count}个字符，"
                        f"将它内嵌可能会导致字幕文件显著增大，你确定要这样做？"))
                       or (char_count == 0 and messagebox.askokcancel(
                        '提示', f"{rowItem['fontName']} 字体不覆盖任何字符，你确定要将它内嵌？")))
            rowItem['embedWidget'].focus_set()   # 弹窗之后需手动取回焦点

        # 绑定变量此时尚未更新，只有手动设置值，这样才能立刻生效，但因此必须返回break
        rowItem['embed'].set(checked)
        self.setRowStatus(rowItem)    # 当内嵌复选框状态变化时，重设置行状态
        return 'break'  # 阻断事件继续传播，否则会导致复选框状态错乱

    def onSubsetClicked(self, rowItem: dict):
        if rowItem['embedWidget'].cget('state') == 'disabled':  # 禁用的控件不用响应
            return
        # 绑定变量此时尚未更新，只有手动设置值，这样才能立刻生效，但因此必须返回break
        rowItem['subset'].set(not rowItem['subset'].get())
        self.setRowStatus(rowItem)    # 当子集复选框状态变化时，重设置行状态
        return 'break'  # 阻断事件继续传播，否则会导致复选框状态错乱

    def onSourceChange(self, rowItem: dict):
        # 在控件初始化阶段和下拉菜单填写临时值的瞬间都不需要响应
        if rowItem['sourceWidget'] and rowItem['source'].get() not in self.SrcCmbOptions.values():
            self.setRowStatus(rowItem)    # 当文件源变化时，重设置行状态

    def onSourceComboSelect(self, rowItem: dict):
        cmb_src = rowItem['sourceWidget']
        src_text = cmb_src.getRaw()
        filename = ''

        if src_text == self.SrcCmbOptions['EMBED']:         # 内嵌字体
            if rowItem['embedName']:
                filename = self.EMBED_NAME_PREFIX + rowItem['embedName']
        elif src_text == self.SrcCmbOptions['SYSTEMFONT']:  # 系统字体
            filename = self.fontMgr.findFont(rowItem['fontName'], _range=FontManager.SYSTEM)[0]
        elif src_text == self.SrcCmbOptions['SRCDIR']:      # 同目录下的字体
            filename = self.fontMgr.findFont(rowItem['fontName'], _range=FontManager.LOCAL)[0]
        elif src_text == self.SrcCmbOptions['BROWSE']:      # 手动选择路径
            filename = filedialog.askopenfilename(
                filetypes=[("Font File", "*.ttf *.ttc *.otf"), ("All files", "*.*")])
            cmb_src.focus_force()
            if not filename:
                filename = cmb_src.currentValue
        elif src_text == self.SrcCmbOptions['EXTRACT']:     # 提取内嵌字体
            if not rowItem['embedName']:  # 正常情况下不会进入该分支
                return
            file_path = filedialog.asksaveasfilename(
                initialdir=os.path.dirname(self.subtitleObj.filePath),
                initialfile=rowItem['embedName'],
                defaultextension=".ttf",
                filetypes=[("TrueType Font", "*.ttf"), ("All files", "*.*")]
            )
            cmb_src.master.focus_set()
            if file_path:
                res = self.subtitleObj.extractFont(
                    rowItem['embedName'], file_path, rowItem['fontName'], rowItem['style'])
                if res != 0:
                    raise Exception(f'保存到{file_path}文件失败!')
            filename = cmb_src.currentValue

        cmb_src.set(filename)
        cmb_src.selection_clear()   # 清除组合框中的选区，否则框内会有半截选区
        cmb_src.icursor(tk.END)     # 将光标移动到末尾
        if not filename:    # 如果为空，则移走焦点，否则占位符（"<无来源>"）不显示
            cmb_src.master.focus_set()
