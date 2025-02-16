import os
import io
import re
from charset_normalizer import from_path
from tkinter import messagebox
from Lang import Lang
from FontManager import FontManager
from UUEncoding import UUEncode, UUDecode


class SectionLines:
    """Section内的行列表，管理Section内的所有行，提供append和toString方法"""

    def __init__(self, section: str, continuous: bool = False):
        self.sectionName = section
        self.lineList = []
        self.continuous = continuous

    def append(self, lineStr: str) -> bool:
        """
        添加条目
        :param lineStr: 行文本，可能为空
        :return: False代表下一行可以是别的Section，True代表下一行也必须是本Section
        """
        if lineStr:
            self.lineList.append(lineStr)
            return self.continuous
        else:
            return False

    def toString(self):
        if self.lineList:
            return '\n'.join([self.sectionName] + self.lineList)
        else:
            return ''


class StyleList(SectionLines):
    """用于维护所有Style的类，包括Style格式和所有Style内容"""

    # ASS默认的格式
    DEFAULT_FORMAT = 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, ' \
                     'BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, ' \
                     'BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding'

    def __init__(self, fmtStr: str = None):
        super().__init__('[V4+ Styles]')
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

    def append(self, lineStr: str) -> bool:
        if lineStr:
            line_str_lower = lineStr[:7].lower()
            if line_str_lower.startswith('format:'):
                self.setFormat(lineStr)
            elif line_str_lower.startswith('style:'):
                fields = [s.strip() for s in lineStr[6:].split(',')]    # 跨过开头的"Style:"
                self._styleDict[fields[self.__nameIndex].lower()] = fields
        return False

    def getStyleFields(self, styleName: str, fieldNames: tuple):
        styleName = styleName.lower()
        # 找出Style行，如果没有则以Default行替代
        style_item = self._styleDict.get(styleName, self._styleDict.get('default', None))
        if style_item:
            return [style_item[self.format_lower.index(field.lower())] for field in fieldNames]
        else:
            return None

    def toString(self):
        if not self._styleDict:
            return ''
        str_list = [self.sectionName, 'Format: ' + ', '.join(self.format)]
        str_list.extend(['Style: ' + ','.join(self._styleDict[style]) for style in self._styleDict])
        return '\n'.join(str_list)

    def __iter__(self):
        return iter(self._styleDict)


class FontList(dict, SectionLines):
    """用于维护所有内嵌字体的类，包括字体名和二进制字体内容"""

    def __init__(self):
        super().__init__()
        SectionLines.__init__(self, '[Fonts]', continuous=True)
        self.currentFontname = None

    def append(self, lineStr: str) -> bool:
        if lineStr:
            line_str_lower = lineStr[:9].lower()
            if line_str_lower.startswith('fontname:'):
                self.currentFontname = lineStr[9:].strip()
                if self.currentFontname in self:
                    self[self.currentFontname].append('')
                else:
                    self[self.currentFontname] = ['']
            elif self.currentFontname:
                self[self.currentFontname][-1] += lineStr  # 合并多行内嵌字体
            return True    # 出现空行才代表可以进入下一个Section
        else:
            return False

    def toString(self) -> str:
        if not self:
            return ''
        str_list = [self.sectionName]
        for font_name, font_codes in self.items():
            for font_code in font_codes:
                str_list.append(f"fontname: {font_name}")
                i = 0
                while i < len(font_code):
                    str_list.append(font_code[i:i + 80])
                    i += 80
                str_list.append('')
        str_list.pop()    # 去掉最后一个多余的空行
        return '\n'.join(str_list)

    def copy(self):
        new_self = self.__class__()
        for key in self:
            new_self[key] = self[key].copy()
        return new_self


class DialogueList(SectionLines):
    """用于维护所有Dialogue行的类，包括Dialogue格式和所有Dialogue内容"""

    # ASS默认的格式
    DEFAULT_FORMAT = 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text'

    def __init__(self, fmtStr: str = None):
        super().__init__('[Events]')
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
            raise ValueError(Lang['Subtitle format error!'])

    def append(self, lineStr: str) -> bool:
        if lineStr:
            line_str_lower = lineStr[:9].lower()
            if line_str_lower.startswith('format:'):
                self.setFormat(lineStr)
            elif line_str_lower.startswith('dialogue:'):
                fields = []
                i = j = 9   # 起始为9，跨过开头的"Dialogue:"
                while i < len(lineStr):    # 将行按逗号分割，但分割数量按Format而定，最后一个Text内可以包含逗号
                    if lineStr[i] == ',':
                        fields.append(lineStr[j:i].strip())
                        j = i + 1
                        if len(fields) == len(self.format) - 1:    # 已经装满Text以前的所有字段，则后面的内容全是Text
                            fields.append(lineStr[j:].strip())
                            break
                    i += 1
                else:    # 如果走到这里，说明格式不对，没有装满字段，则将后面剩余的文字都装在后一个字段中
                    if j < len(lineStr):
                        fields.append(lineStr[j:].strip())
                self._dialogueList.append(fields)
        return False

    def getDialogueField(self, index: int, fieldName: str):
        field_index = self.format_lower.index(fieldName.lower())
        return self._dialogueList[index][field_index]

    def toString(self):
        if not self._dialogueList:
            return ''
        str_list = [self.sectionName, 'Format: ' + ', '.join(self.format)]
        str_list.extend(['Dialogue: ' + ','.join(dlg) for dlg in self._dialogueList])
        return '\n'.join(str_list)

    def __len__(self):
        return len(self._dialogueList)


class SubStationAlpha:
    """ASS字幕类，维护字幕的所有Style、Font、Dialogue内容和读写操作"""

    def __init__(self, path: str, encoding: str = None):
        self.filePath = path
        self.infoList = SectionLines('[Script Info]')
        self.styleList = StyleList()
        self.fontList = FontList()    # {fontname: [fontcode]}]，fontname可能有重复，重复的放在一个list内
        self.graphicList = SectionLines('[Graphics]', continuous=True)   # 这里只存字串行，不做任何处理
        self.dialogueList = DialogueList()
        self.sectionsDict = {
            self.infoList.sectionName.lower(): self.infoList,
            self.styleList.sectionName.lower(): self.styleList,
            self.fontList.sectionName.lower(): self.fontList,
            self.graphicList.sectionName.lower(): self.graphicList,
            self.dialogueList.sectionName.lower(): self.dialogueList
        }
        self.sectionsInOrder = []     # 保存各个SectonLines并记录它们的顺序，以便重建文件时不会搞混
        self._load(path, encoding)
        self.embedFontMgr = FontManager(assSub=self)    # 为内嵌字体创建Name索引

    @classmethod
    def load(cls, path: str, encoding: str = None):
        if not os.path.isfile(path):
            messagebox.showerror(Lang['Error'], Lang["File {p} doesn't exist."].format(p=path))
            return
        elif not os.access(path, os.R_OK):
            messagebox.showerror(Lang['Error'], Lang['Unable to read file {p}.'].format(p=path))
            return
        return cls(path, encoding)

    def _load(self, path: str, encoding: str = None):
        if not encoding:    # 如果没有指定编码，则自动判断
            encoding = from_path(path).best().encoding
        with open(path, 'r', encoding=encoding) as file:
            section_pattern = re.compile(r'^\[.*\]')
            section_lines = None
            continuous_section = False

            while True:
                line_str = file.readline()
                if not line_str:
                    break

                # 去掉开头的不可打印字符
                for i, c in enumerate(line_str):
                    if c.isprintable():
                        line_str = line_str[i:]
                        break
                line_str = line_str.rstrip('\r\n')   # 去掉回车

                # 检查是否是Section行
                if not continuous_section:
                    matchObj = section_pattern.match(line_str)   # 检查是否以[*]开头
                    if matchObj:    # 中括号行出现，切换行类型
                        section_name = matchObj.group(0).lower()
                        # 对于非标准的Section，如"[Aegisub Project Garbage]"，临时新建一个SectonLines保存
                        section_lines = self.sectionsDict.get(section_name, SectionLines(section_name.title()))
                        if section_lines not in self.sectionsInOrder:   # 如果标准Section有重复的，以第一个的位置为准
                            self.sectionsInOrder.append(section_lines)  # 保存入顺序表
                        continue
                # 向Section List插入新行
                continuous_section = section_lines.append(line_str)

    def save(self, path: str = None, encoding: str = None) -> bool:
        """
        保存文件到路径
        :param path: 保存路径，缺省则写入到源文件
        :param encoding: 写入编码
        :return: True为成功，False失败
        """
        if not path:
            path = self.filePath
        path_exists = os.path.exists(path)
        path_dir = os.path.dirname(path)
        if not path_dir:
            path_dir = '.'
        if (path_exists and not os.access(path, os.W_OK)) or \
                (not path_exists and not os.access(path_dir, os.W_OK)):
            messagebox.showerror(Lang['Error'], Lang['Unable to write file {p}.'].format(p=path))
            return False
        if not encoding:
            encoding = 'utf-8'    # 默认使用UTF-8编码

        # 检查Fonts段是否被删除或新增
        if self.fontList in self.sectionsInOrder:
            if not len(self.fontList):
                self.sectionsInOrder.remove(self.fontList)
        elif len(self.fontList):
            self.sectionsInOrder.insert(self.sectionsInOrder.index(self.styleList) + 1, self.fontList)

        # 写入文件
        with open(path, 'w', encoding=encoding) as file:
            for section_lines in self.sectionsInOrder:
                file.write(section_lines.toString())
                file.write('\n\n')
        return True

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

        # 收集Dialogue中出现的字体 ---------
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
            # 查找行内样式{} ---------
            match_iter = inlineStyle_ptn.finditer(text)
            pos = 0    # 文字位置指针
            for m_obj in match_iter:
                # 将{}之前的文字都划归给上一种样式
                self.__addTextToDict(allFontsDict, fontname, font_style, text[pos: m_obj.start()])
                pos = m_obj.end()
                inline_style_str = m_obj.group().lower()    # {}以及内部的文字
                # 处理{}中的\fn ---------
                pos2 = inline_style_str.rfind('\\fn')
                if pos2 != -1:
                    m = inlineFont_ptn.match(inline_style_str[pos2:])
                    fontname = m.group(1)    # 提取\fn后面的字体名
                # 处理{}中的\b ----------
                pos2 = inline_style_str.rfind('\\b')
                if pos2 != -1:
                    m = inlineBold_ptn.match(inline_style_str[pos2:])
                    if m:
                        bold = m.group(1)    # 提取\b后面的一个数字
                # 处理{}中的\i ----------
                pos2 = inline_style_str.rfind('\\i')
                if pos2 != -1:
                    m = inlineItalic_ptn.match(inline_style_str[pos2:])
                    if m:
                        italic = m.group(1)    # 提取\i后面的一个数字
                font_style = self.__getStyleText(bold, italic)
            # 将最后一个{}（或没有）之后的文字都划归给最后一个样式
            self.__addTextToDict(allFontsDict, fontname, font_style, text[pos:])

        # 加入内嵌的字体 ---------
        embed_fonts_included = set()
        for fontname, font_styles in allFontsDict.items():
            for font_style, style_obj in font_styles.items():
                embedName, index = self.embedFontMgr.findFont(fontname, font_style, FontManager.LOCAL)
                style_obj['embedName'] = embedName
                if embedName:
                    embed_fonts_included.add((embedName, index))
        # 查找未被引用的内嵌字体 ---------
        for fontname, font_codes in self.fontList.items():
            for i in range(len(font_codes)):
                if (fontname, i) not in embed_fonts_included:   # 如果文字未被使用，仍需要加入一个条目
                    font_names = self.embedFontMgr.getFontNames(fontname)
                    if font_names:
                        allFontsDict[font_names[i]['fullnames'][0]] = \
                            {font_names[i]['style']: {'text': '', 'embedName': fontname}}

        # 构造一个font info列表以供返回 ---------
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

    def getEmbedFont(self, embedName: str, index: int = None) -> (io.BytesIO, list):
        """
        获取内嵌字体对象
        :param embedName: 内嵌文件名
        :param index: 重复文件名中的编号，缺省则返回所有字体对象的列表
        :return: TTFont或[TTFont]
        """
        if embedName not in self.fontList:
            return None
        font_codes = self.fontList[embedName]
        if index is None:
            # return [MTTFont.fromFontCode(font_code) for font_code in font_codes]
            font_list = []
            for font_code in font_codes:
                ttf_bytes = io.BytesIO()
                ttf_bytes.write(UUDecode(font_code))
                ttf_bytes.seek(0)
                font_list.append(ttf_bytes)
            return font_list
        else:
            # return MTTFont.fromFontCode(font_codes[index])
            ttf_bytes = io.BytesIO()
            ttf_bytes.write(UUDecode(font_codes[index]))
            ttf_bytes.seek(0)
            return ttf_bytes

    def embedFont(self, fontname: str, ttf_bytes: io.BytesIO, overwrite: bool = False, index: int = 0):
        """
        嵌入字体文件到字幕的Font Section中
        :param fontname: 嵌入文件名
        :param ttf_bytes: TTF数据的BytesIO
        :param overwrite: 覆盖现有的同名字体
        :param index: 已有在同名字体中指定被覆盖的序号
        """
        font_code = UUEncode(ttf_bytes.read())
        if fontname in self.fontList:
            if overwrite:
                self.fontList[fontname][index] = font_code
            else:
                self.fontList[fontname].append(font_code)
        else:
            self.fontList[fontname] = [font_code]

    def extractFont(self, embedName: str, savePath: str, fontName: str, style: str = 'regular') -> int:
        """
        提取内嵌的字体，通过内嵌文件名（可能重复）提取给定名称的字体
        :param savePath: 保存的路径
        :param embedName: 字体内部文件名，可能重复
        :param fontName: 字体名称
        :param style: 字体样式名称，缺省则默认Regular
        :return: 0:成功，1:字体名无法匹配到文件，2:文件保存失败
        """
        # 从文件中查找目标字体的序号
        index = self.embedFontMgr.indexOfFontInPath(embedName, fontName, style)
        if index == -1:   # 没找到要提取的字体
            messagebox.showerror(Lang['Error'], "Can not find embeded font {f} in subtitle.".format(f=embedName))
            return 1
        try:
            if not os.access(os.path.dirname(savePath), os.W_OK):
                raise ValueError()
            with open(savePath, 'wb') as file:
                file.write(UUDecode(self.fontList[embedName][index]))
            return 0
        except Exception as e:
            messagebox.showerror(Lang['Error'], "Unable to write file {p}.".format(p=savePath))
            return 2
