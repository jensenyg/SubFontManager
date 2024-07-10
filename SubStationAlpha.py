import os
import re
from enum import Enum
from tkinter import messagebox
from UUEncoding import UUEncode, UUDecode


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

    def getStyleField(self, styleName: str, fieldName: str):
        field_index = self.format_lower.index(fieldName.lower())
        return self._styleDict[styleName.lower()][field_index]

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
        self.fontList = []  # [{'fontname', 'fontcode'}]
        self.dialogueList = DialogueList()
        self.otherList = []
        self._load()

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
            font_obj = None    # 用于在循环中将Font多行编码连接起来
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
                            font_obj = {'fontname': line_str[9:].strip(), 'fontcode': ''}
                            self.fontList.append(font_obj)
                        else:
                            font_obj['fontcode'] += line_str    # 合并多行内嵌字体
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
        if not os.access(path, os.W_OK):
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
            file.write('\n[Fonts]\n')
            for font in self.fontList:
                file.write(f"fontname: {font['fontname']}\n")
                font_code = font['fontcode']
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

    def gatherFonts(self) -> dict:
        """
        搜集字幕中所有出现过的字体，以及每种字体覆盖的文字数量
        :return: {fontname: count}
        """
        fontUsedList = {}   # 出现过的所有字体的列表
        for style in self.styleList:
            fontUsedList[self.styleList.getStyleField(style, 'fontname')] = 0

        inlineStyle_pattern = re.compile(r'\{.*?\}')    # 用于查找行内样式{}的内容
        inlineFont_pattern = re.compile(r'\\fn(.*?)[\\,\}]')    # 用于查找{}内的\fn内容并提取字体名
        i = 0
        while i < len(self.dialogueList):
            style = self.dialogueList.getDialogueField(i, 'style').lstrip('*')    # 获取样式名，去掉开头可能存在的*号
            text = self.dialogueList.getDialogueField(i, 'text')
            fontname = self.styleList.getStyleField(style, 'fontname')
            # 查找行内样式{}
            miter = inlineStyle_pattern.finditer(text)
            pos = 0    # 文字位置指针
            for m in miter:
                if fontname not in fontUsedList:
                    fontUsedList[fontname] = 0
                fontUsedList[fontname] += m.start() - pos
                pos = m.end()
                style_str = m.group().lower()
                # 查找{}中的"\fn"字样
                fn_pos = style_str.rfind('\\fn')
                if fn_pos != -1:
                    m_font = inlineFont_pattern.match(style_str[fn_pos:])
                    fontname = m_font.group(1)    # 提取\fn后面的字体名
            if fontname not in fontUsedList:
                fontUsedList[fontname] = 0
            fontUsedList[fontname] += len(text) - pos
            i += 1

        return fontUsedList

    def embedFonts(self, *args):
        """
        嵌入字体文件到字幕的Font Section中
        :param args:
        :return:
        """
        for path in args:
            with open(path, 'rb') as file:
                self.fontList.append({
                    'fontname': os.path.basename(path),
                    'fontcode': UUEncode(file.read())
                })
        return len(args)
