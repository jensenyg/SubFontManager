import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PlaceholderInput import PlaceholderCombobox
from WidgetTable import WidgetTable
from FontManager import FontManager
from SubStationAlpha import SubStationAlpha


class FontList(WidgetTable):
    SrcCmbOptions = {   # Source Combobox Options
        'EMBED': '<使用内嵌字体>',
        'SRCDIR': '<使用同目录下的字体>',
        'SYSTEMFONT': '<使用系统字体>',
        'BROWSE': '<手动选择路径...>',
        'EXTRACT': '<提取内嵌字体...>'
    }
    Placeholder_NOSRC = '<无来源>'
    EMBED_NAME_FMT = 'embed:/%s'    # 嵌入字体名的显示格式

    def __init__(self, master):
        super().__init__(master=master)
        self.columnWidth = []
        self.itemList = []   # [{fontName, isEmbed, isSubset, source, ...}]
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
        # 清空列表
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

        # 样式名称表
        style_texts = {'regular': '常规', 'bold': '粗体', 'italic': '斜体', 'bold italic': '粗斜体'}

        for item in fontList:
            # 保存行所有信息和变量的dict
            row_item = {
                'index': len(self.itemList),
                'fontName': item['fontname'],
                'style': item['style'],
                'embedName': item['embedName'],    # 已内嵌字体的内嵌文件名
                'embed': tk.BooleanVar(),
                'embedWidget': None,
                'subset': tk.BooleanVar(),
                'text': item['text'],
                'source': tk.StringVar(),
                'sourceVarName': None,
                'sourceBakValue': None,  # 为了能够在某些临时的<...>值之后把原值填回去，需要对原值保存一个备份
                'sourceOptions': list(self.SrcCmbOptions.values()),
                'sourceWidget': None,   # 由addRow函数填写
                'state': tk.NORMAL if item['text'] else tk.DISABLED    # 一些控件的禁用状态
            }
            self.itemList.append(row_item)

            if row_item['embedName']:  # 如果是内嵌字体
                row_item['embed'].set(True)
                row_item['subset'].set(False)   # 内嵌字体默认不勾选子集化
                row_item['source'].set(self.EMBED_NAME_FMT % row_item['embedName'])
            else:
                row_item['embed'].set(False)
                row_item['subset'].set(True)
                row_item['source'].set(self.fontMgr.findFont(row_item['fontName'])[0])
                # 无内嵌字体的条目也不应该有提取内嵌字体的选项
                row_item['sourceOptions'].remove(self.SrcCmbOptions['EMBED'])
                row_item['sourceOptions'].remove(self.SrcCmbOptions['EXTRACT'])
            row_item['source'].trace_add('write', self.onSourceChange)
            row_item['sourceVarName'] = row_item['source']._name    # 保存这个_name用来在事件回调时查找触发控件
            row_item['sourceBakValue'] = row_item['source'].get()

            # 添加行 ------------------
            row_frame = self.newRow()
            # 复选框：是否内嵌
            chk_embed = tk.Checkbutton(row_frame, variable=row_item['embed'], bg=self.bg)
            chk_embed.bind("<Button-1>", self.onEmbedClicked)
            row_item['embedWidget'] = chk_embed
            # 文本：字体名
            tk.Label(row_frame, text=row_item['fontName'], anchor='w', bg=self.bg)
            # 文本：样式名
            tk.Label(row_frame, text=style_texts.get(row_item['style'], ''), anchor='center', bg=self.bg)
            # 文本：字数统计
            tk.Label(row_frame, text=str(len(row_item['text'])) + ' ', anchor='e', bg=self.bg)
            # 复选框：子集化
            tk.Checkbutton(row_frame, variable=row_item['subset'], state=row_item['state'], bg=self.bg)
            # 组合框：文件源
            cmb_src = PlaceholderCombobox(row_frame, placeholder=self.Placeholder_NOSRC, state=row_item['state'],
                                          textvariable=row_item['source'], values=row_item['sourceOptions'], background=self.bg)
            cmb_src.bind("<<ComboboxSelected>>", self.onSourceComboSelect)
            row_item['sourceWidget'] = cmb_src

            self.addRow(row_frame)
            self.setRowStatus(row_item)

        self.update_idletasks()    # 强制重绘，否则可能导致布局错误
        self.onResize()

    def onEmbedClicked(self, event):
        # 寻找响应的控件
        for row_item in self.itemList:
            if row_item['embedWidget'] == event.widget:
                break
        else:
            return
        char_count = len(row_item['text'])
        if not row_item['embed'].get() and char_count > 99:
            if messagebox.askokcancel('警告', f"{row_item['fontName']} 字体覆盖了{char_count}个字符，"
                                            f"将它内嵌可能会导致字幕文件体积显著增大，你确定要这样做？"):
                row_item['embed'].set(True)
            row_item['embedWidget'].focus_force()
            return 'break'

    @classmethod
    def setRowStatus(cls, rowItem: dict):
        source = rowItem['sourceBakValue']
        if rowItem['text'] and source != cls.Placeholder_NOSRC:
            rowItem['embedWidget'].configure(state=tk.NORMAL)
        else:
            rowItem['embed'].set(False)
            rowItem['embedWidget'].configure(state=tk.DISABLED)

    def onSourceChange(self, *args):
        # 寻找响应的控件，这里的args[0]就是StringVar的_name
        for row_item in self.itemList:
            if row_item['sourceVarName'] == args[0]:
                break
        else:
            return
        new_value = row_item['source'].get()
        # 浏览和提取两种操作的内容文本是临时的，此时并不覆盖备份值，备份值将用于回填原值
        if new_value not in (self.SrcCmbOptions['BROWSE'], self.SrcCmbOptions['EXTRACT']):
            row_item['sourceBakValue'] = new_value
        self.setRowStatus(row_item)

    def onSourceComboSelect(self, event):
        cmb_src = event.widget
        # 寻找响应的控件
        for row_item in self.itemList:
            if row_item['sourceWidget'] == cmb_src:
                break
        else:
            return

        filename = ''
        src_text = cmb_src.get()
        if src_text == self.SrcCmbOptions['EMBED']:
            if row_item['embedName']:
                filename = self.EMBED_NAME_FMT % row_item['embedName']
        elif src_text == self.SrcCmbOptions['SRCDIR']:
            filename = self.fontMgr.findFont(row_item['fontName'], _range=FontManager.LOCAL)[0]
        elif src_text == self.SrcCmbOptions['SYSTEMFONT']:
            filename = self.fontMgr.findFont(row_item['fontName'], _range=FontManager.SYSTEM)[0]
        elif src_text == self.SrcCmbOptions['BROWSE']:
            filename = filedialog.askopenfilename(
                filetypes=[("Font File", "*.ttf *.ttc *.otf"), ("All files", "*.*")])
            cmb_src.focus_force()
            if not filename and row_item['sourceBakValue'] != cmb_src.placeholder:
                filename = row_item['sourceBakValue']
        elif src_text == self.SrcCmbOptions['EXTRACT']:
            if not row_item['embedName']:   # 正常情况下不会进入该分支
                return
            file_path = filedialog.asksaveasfilename(
                initialdir=os.path.dirname(self.subtitleObj.filePath),
                initialfile=row_item['embedName'],
                defaultextension=".ttf",
                filetypes=[("TrueType Font", "*.ttf"), ("All files", "*.*")]
            )
            cmb_src.focus_force()
            if file_path:
                res = self.subtitleObj.extractFont(row_item['embedName'], row_item['fontName'], file_path)
                if res != 0:
                    raise Exception(f'保存到{file_path}文件失败!')
            if row_item['sourceBakValue'] != cmb_src.placeholder:
                filename = row_item['sourceBakValue']

        cmb_src.set(filename)
        cmb_src.selection_clear()   # 清除组合框中的选区，否则框内会有半截选区
        cmb_src.icursor(tk.END)     # 将光标移动到末尾
        if not filename:    # 如果当前显示的占位符（"无来源"），则移走焦点，否则占位符不显示
            self.focus_set()
