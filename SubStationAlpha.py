import os
import re
from enum import Enum
from tkinter import messagebox
from FontManager import FontManager
from UUEncoding import UUDecode


class Section(Enum):
    """
    Section枚举类
    """
    INFO = 'info'
    STYLE = 'style'
    FONT = 'font'
    DIALOGUE = 'dialogue'
    OTHER = 'other'    # 如"[Aegisub Project Garbage]"


class StyleList:
    """
    用于维护所有Style的类，包括Style格式和多条Style内容
    """
    # ASS默认的格式
    DEFAULT_FORMAT = 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, ' \
                     'BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, ' \
                     'BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding'

    def __init__(self, fmtStr: str = None):
        self._styleDict = {}    # {styleName, [fields]}
        self.format = None
        self.format_lower = None
        self.__nameIndex = None
        self.setFormat(fmtStr)

    def setFormat(self, fmtStr: str = None):
        if not fmtStr:
            fmtStr = self.DEFAULT_FORMAT
        self.format = [s.strip() for s in fmtStr[7:].split(',')]    # 跨过开头的"Format:"
        self.format_lower = [s.lower() for s in self.format]    # 全小写格式名，用于查找和比较
        if 'name' not in self.format_lower or 'fontname' not in self.format_lower:
            raise ValueError("Subtitle format error!")
        self.__nameIndex = self.format_lower.index('name')

    def append(self, styleStr: str):
        fields = [s.strip() for s in styleStr[6:].split(',')]    # 跨过开头的"Style:"
        self._styleDict[fields[self.__nameIndex].lower()] = fields

    def getStyleFields(self, styleName: str, fieldNames: tuple):
        styleName = styleName.lower()
        # 找出Style行，如果没有则以Default行替代
        style_item = self._styleDict.get(styleName, self._styleDict.get('default', None))
        if style_item:
            return [style_item[self.format_lower.index(field.lower())] for field in fieldNames]
        else:
            return None

    def getStyleString(self, item) -> str:
        return 'Style: ' + ','.join(self._styleDict[item])

    def getFormatString(self) -> str:
        return 'Format: ' + ', '.join(self.format)

    def __iter__(self):
        return iter(self._styleDict)


class DialogueList:
    """
    用于维护所有Dialogue行的类，包括Dialogue格式和多条Dialogue内容
    """
    # ASS默认的格式
    DEFAULT_FORMAT = 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text'

    def __init__(self, fmtStr: str = None):
        self._dialogueList = []    # [[fields]]
        self.format = None
        self.format_lower = None
        self.setFormat(fmtStr)

    def setFormat(self, fmtStr: str = None):
        if not fmtStr:
            fmtStr = self.DEFAULT_FORMAT
        self.format = [s.strip() for s in fmtStr[7:].split(',')]    # 跨过开头的"Format:"
        self.format_lower = [s.lower() for s in self.format]    # 全小写格式名，用于查找和比较
        if 'name' not in self.format_lower or 'text' not in self.format_lower:
            raise ValueError("Subtitle format error!")

    def append(self, dialogueStr: str):
        fields = []
        i, j = 9, 9   # 起始为9，跨过开头的"Dialogue:"
        while i < len(dialogueStr):    # 将行按逗号分割，但分割数量按Format而定，最后一个Text内可以包含逗号
            if dialogueStr[i] == ',':
                fields.append(dialogueStr[j:i].strip())
                j = i + 1
                if len(fields) == len(self.format) - 1:    # 已经装满Text以前的所有字段，则后面的内容全是Text
                    fields.append(dialogueStr[j:].strip())
                    break
            i += 1
        else:    # 如果走到这里，说明格式不对，没有装满字段，则将后面剩余的文字都装在后一个字段中
            if j < len(dialogueStr):
                fields.append(dialogueStr[j:].strip())
        self._dialogueList.append(fields)

    def getDialogueField(self, index: int, fieldName: str):
        field_index = self.format_lower.index(fieldName.lower())
        return self._dialogueList[index][field_index]

    def getDialogueString(self, index) -> str:
        return 'Dialogue: ' + ','.join(self._dialogueList[index])

    def getFormatString(self):
        return 'Format: ' + ', '.join(self.format)

    def __len__(self):
        return len(self._dialogueList)


# ASS字幕类，维护字幕的所有Style、Font、Dialogue内容和读写操作
class SubStationAlpha:
    def __init__(self, path: str):
        self.filePath = path
        # self.lines = None
        self.infoList = []
        self.styleList = StyleList()
        self.fontList = {}  # {fontname: [fontcode]}]，fontname可能有重复，重复的放在一个list内
        self.dialogueList = DialogueList()
        self.otherList = []
        self._load()
        self.embedFontMgr = FontManager(embedFonts=self.fontList)    # 为内嵌字体创建Name索引

    @classmethod
    def load(cls, path: str):
        if not os.path.isfile(path):
            messagebox.showerror("错误", f"文件 {path} 不存在。")
            return
        elif not os.access(path, os.R_OK):
            messagebox.showerror("错误", f"文件 {path} 无法读取。")
            return
        return cls(path)

    def _load(self):
        with open(self.filePath, 'r') as file:
            section = None
            section_pattern = re.compile(r'^\[.*\]')
            font_name = None    # 用于在循环中将Font多行编码连接起来
            while True:
                line_str = file.readline()
                if not line_str:
                    break
                elif line_str in ['\n', '\r\n']:  # 不要空行
                    continue

                # 去掉开头的不可打印字符
                for i, c in enumerate(line_str):
                    if c.isprintable():
                        line_str = line_str[i:]
                        break
                line_str = line_str.rstrip('\r\n')

                # 检查是否是Section行
                matchObj = section_pattern.match(line_str)
                if matchObj:  # 中括号行出现，切换行类型
                    section_str = matchObj.group(0).lower()
                    if section_str.startswith('[script info]'):
                        section = Section.INFO
                    elif section_str.startswith('[v4 styles]') or section_str.startswith('[v4+ styles]'):
                        section = Section.STYLE
                    elif section_str.startswith('[fonts]'):
                        section = Section.FONT
                    elif section_str.startswith('[events]'):
                        section = Section.DIALOGUE
                    else:
                        section = Section.OTHER
                elif section == Section.INFO:   # Info Section
                    self.infoList.append(line_str)
                else:
                    line_str_lower = line_str[:9].lower()
                    if section == Section.STYLE:    # Style Section
                        if line_str_lower.startswith('format:'):
                            self.styleList.setFormat(line_str)
                        elif line_str_lower.startswith('style:'):
                            self.styleList.append(line_str)
                    elif section == Section.FONT:    # Font Section
                        if line_str_lower.startswith('fontname:'):
                            font_name = line_str[9:].strip()
                            if font_name in self.fontList:
                                self.fontList[font_name].append('')
                            else:
                                self.fontList[font_name] = ['']
                        else:
                            self.fontList[font_name][-1] += line_str    # 合并多行内嵌字体
                    elif section == Section.DIALOGUE:   # Dialogue Section
                        if line_str_lower.startswith('format:'):
                            self.dialogueList.setFormat(line_str)
                        elif line_str_lower.startswith('dialogue:'):
                            self.dialogueList.append(line_str)

    def save(self, path: str = None):
        """
        保存文件到路径
        :param path: 保持路径，缺省则写入到源文件
        :return:
        """
        if path is None:
            path = self.filePath
        if not os.access(os.path.dirname(path), os.W_OK):
            messagebox.showerror("错误", f"文件 {path} 无法写入。")
            return

        with open(path, 'w') as file:
            # 写入Info
            file.write('[Script Info]\n')
            file.write('\n'.join(self.infoList) + '\n')

            # 写入Style
            file.write('\n[V4+ Styles]\n')
            file.write(self.styleList.getFormatString() + '\n')
            for style in self.styleList:
                file.write(self.styleList.getStyleString(style) + '\n')

            # 写入Font
            file.write('\n[Fonts]')
            for font_name, font_codes in self.fontList.items():
                for font_code in font_codes:
                    file.write(f"\nfontname: {font_name}\n")
                    i = 0
                    while i < len(font_code):
                        file.write(font_code[i:i + 80] + '\n')
                        i += 80

            # 写入Dialogue
            file.write('\n[Events]\n')
            file.write(self.dialogueList.getFormatString() + '\n')
            i = 0
            while i < len(self.dialogueList):
                file.write(self.dialogueList.getDialogueString(i) + '\n')
                i += 1

    @staticmethod
    def __addTextToDict(d: dict, key1, key2, text: str):
        if key1 in d:
            if key2 in d[key1]:
                d[key1][key2]['text'] += text
            else:
                d[key1][key2] = {'text': text}
        else:
            d[key1] = {key2: {'text': text}}

    @staticmethod
    def __getStyleText(bold, italic) -> str:
        style = 'bold' if int(bold) else ''    # 非0都判断为真，如1、-1等
        style += (' italic' if style else '') if int(italic) else ''
        if not style:
            style = 'regular'
        return style

    def gatherFonts(self) -> list:
        """
        搜集字幕中所有出现过的字体，以及每种字体覆盖的文字数量
        :return: [{'fontname': str, 'style': str, 'text': str, 'embedName': str}]
        """
        allFontsDict = {}   # 出现过的所有字体的列表：{fontname: {style: {'text': str, 'embedName': str}}}
        # 收集Style中出现的字体. 这一步的目的是因为有些Style可能覆盖字符数为0，但仍应该显示于界面列表中
        for style in self.styleList:
            fontname, bold, italic = self.styleList.getStyleFields(style, ('fontname', 'bold', 'italic'))
            self.__addTextToDict(allFontsDict, fontname, self.__getStyleText(bold, italic), '')

        # 收集Dialogue中出现的字体
        inlineStyle_ptn = re.compile(r'\{.*?\}')    # 用于查找行内样式{}的内容
        inlineFont_ptn = re.compile(r'\\fn(.*?)[\\,\}]')    # 用于查找{}内的\fn内容并提取字体名
        inlineBold_ptn = re.compile(r'\\b(\d)')      # 用于查找{}内的\b并提取后面的数字
        inlineItalic_ptn = re.compile(r'\\i(\d)')    # 用于查找{}内的\i并提取后面的数字
        for i in range(len(self.dialogueList)):
            style = self.dialogueList.getDialogueField(i, 'style').lstrip('*')    # 获取样式名，去掉开头可能存在的*号
            text = self.dialogueList.getDialogueField(i, 'text')
            res = self.styleList.getStyleFields(style, ('fontname', 'bold', 'italic'))
            if not res or not res[0]:    # 如果res为None，说明样式找不到且Default样式也没有
                continue
            fontname, bold, italic = res
            font_style = self.__getStyleText(bold, italic)
            # 查找行内样式{}
            match_iter = inlineStyle_ptn.finditer(text)
            pos = 0    # 文字位置指针
            for m_obj in match_iter:
                # 将{}之前的文字都划归给上一种样式
                self.__addTextToDict(allFontsDict, fontname, font_style, text[pos: m_obj.start()])
                pos = m_obj.end()
                inline_style_str = m_obj.group().lower()    # {}以及内部的文字
                # 处理{}中的\fn
                pos2 = inline_style_str.rfind('\\fn')
                if pos2 != -1:
                    m = inlineFont_ptn.match(inline_style_str[pos2:])
                    fontname = m.group(1)    # 提取\fn后面的字体名
                # 处理{}中的\b
                pos2 = inline_style_str.rfind('\\b')
                if pos2 != -1:
                    m = inlineBold_ptn.match(inline_style_str[pos2:])
                    if m:
                        bold = m.group(1)    # 提取\b后面的一个数字
                # 处理{}中的\i
                pos2 = inline_style_str.rfind('\\i')
                if pos2 != -1:
                    m = inlineItalic_ptn.match(inline_style_str[pos2:])
                    if m:
                        italic = m.group(1)    # 提取\i后面的一个数字
                font_style = self.__getStyleText(bold, italic)
            # 将最后一个{}（或没有）之后的文字都划归给最后一个样式
            self.__addTextToDict(allFontsDict, fontname, font_style, text[pos:])

        # 加入内嵌的字体
        embed_fonts_included = set()
        for fontname, font_styles in allFontsDict.items():
            for font_style, style_obj in font_styles.items():
                embedName, index = self.embedFontMgr.findFont(fontname, font_style, FontManager.LOCAL)
                style_obj['embedName'] = embedName
                if embedName:
                    embed_fonts_included.add((embedName, index))
        # 查找未被引用的内嵌字体
        for fontname, font_codes in self.fontList.items():
            for i in range(len(font_codes)):
                if (fontname, i) not in embed_fonts_included:   # 如果文字未被使用，仍需要加入一个条目
                    font_names = self.embedFontMgr.getFontNames(fontname)
                    if font_names:
                        allFontsDict[font_names[i]['fullnames'][0]] = \
                            {font_names[i]['style']: {'text': '', 'embedName': fontname}}

        # 构造一个font info列表以供返回
        font_info = []
        for fontname, font_styles in allFontsDict.items():
            for font_style, style_obj in font_styles.items():
                font_info.append({
                    'fontname': fontname,
                    'style': font_style,
                    'text': style_obj['text'],
                    'embedName': style_obj['embedName']
                })
        return font_info

    def embedFonts(self, *paths):
        """
        嵌入字体文件到字幕的Font Section中
        :param paths:
        :return:
        """
        pass

    def extractFont(self, embedName: str, fontName: str, savePath: str) -> int:
        """
        提取内嵌的字体，通过内嵌文件名（可能重复）提取给定名称的字体
        :param embedName: 字体内部文件名，可能重复
        :param fontName: 字体名称
        :param savePath: 保存的路径
        :return: 0:成功，1:字体名无法匹配到文件，2:文件保持失败
        """
        index = self.embedFontMgr.indexOfFontInPath(fontName, embedName)
        # 找到提取的目标字体
        if index == -1:
            return 1
        if not os.access(os.path.dirname(savePath), os.W_OK):
            messagebox.showerror("错误", f"文件 {savePath} 无法写入。")
        try:
            with open(savePath, 'wb') as file:
                file.write(UUDecode(self.fontList[embedName][index]))
            return 0
        except Exception as e:
            return 2
