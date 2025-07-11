import io
from typing import Self
from . import UU    # 导入Cython版本UUEncoding库


class SectionLines:
    """Section内的行列表，管理Section内的所有行，提供append和toString方法"""

    def __init__(self, section: str, continuous: bool = False):
        """
        :param section: 段的名字，如[Script Info], [V4+ Styles]等
        :param continuous: 是否是连贯行，连贯行会把多次append连接为一行
        """
        self.sectionName: str = section # 段名
        self.continuous: bool = continuous  # 是否是连贯行
        self.__lineList = []  # 本段内的行文本列表

    def append(self, lineStr: str) -> bool:
        """
        添加条目
        :param lineStr: 行文本，可能为空
        :return: False代表下一行可以是别的Section，True代表下一行也必须是本Section.
                 因为内嵌字体段中可能会出现[...]开头的行内容，但却不是新Section.
        """
        if lineStr:
            self.__lineList.append(lineStr)
            return self.continuous
        else:   # 出现空行则可以进入下一Section
            return False

    def toString(self) -> str:
        """把整个Section段都输出为字幕文本"""
        if self.__lineList:
            return '\n'.join([self.sectionName, *self.__lineList])
        else:
            return ''

    @staticmethod
    def _splitLineString(lineStr: str, sep: str = ':') -> tuple[str, str]:
        """
        以':'为界切分行字串，并去除结果段首尾空格
        :param lineStr: 行字串
        :return: 前部字串和后部字串组，如果找不到分隔符，则返回None和原字串
        """
        pos = lineStr.find(sep)
        return ('', lineStr) if pos == -1 else (lineStr[:pos].strip(), lineStr[pos + 1:].strip())


class StyleDict(SectionLines):
    """用于维护所有Style的类，包括Style格式和所有Style内容"""

    STYLE = 'Style'
    FORMAT = 'Format'
    SECTION_NAMES = ('[V4+ Styles]', '[V4 Styles]') # Style段有两个合法的名字
    DEFAULT_FORMATS = {
        # V4+ Styles的默认的字段格式
        '[v4+ styles]': ('Name', 'Fontname', 'Fontsize', 'PrimaryColour', 'SecondaryColour', 'OutlineColour',
                         'BackColour', 'Bold', 'Italic', 'Underline', 'StrikeOut', 'ScaleX', 'ScaleY', 'Spacing',
                         'Angle', 'BorderStyle', 'Outline', 'Shadow', 'Alignment', 'MarginL', 'MarginR', 'MarginV',
                          'Encoding'),
        # V4 Styles的默认的字段格式
        '[v4 styles]': ('Name', 'Fontname', 'Fontsize', 'PrimaryColour', 'SecondaryColour', 'TertiaryColour',
                        'BackColour', 'Bold', 'Italic', 'BorderStyle', 'Outline', 'Shadow', 'Alignment', 'MarginL',
                        'MarginR', 'MarginV', 'AlphaLevel', 'Encoding')
    }
    DEFAULT_FORMAT_CAPS: dict[str, str] = {s.lower(): s for fs in DEFAULT_FORMATS.values() for s in fs} # 大小写映射字典
    DEFAULT_FORMAT_CAPS.update({s.lower(): s for s in SECTION_NAMES})   # 将段名也加入字典
    INVALID_KEY = 'invalid,'    # 无效行的key，为防止key冲突，使用了正常语法中不会出现的','

    def __init__(self, name: str = '[V4+ Styles]'):
        """
        :param name: 段名字，为[V4+ Styles]或[V4 Styles]
        """
        super().__init__('')
        self._fieldNames: list[str] = []   # 样式名表 ['Name', 'Fontname',...]
        self._fieldNameIndexes: dict[str, int] = {}  # 小写格式字段名和序号的映射 {'name': 0, 'fontname': 1,...}
        self._styles: dict[str, list[str]] = {}  # 样式值表 {'Default': ['Default','Arial','26',...]}
        self._nameIndex: int = 0     # 'Name'字段在Format中的位置序号
        self.__invalidLineNo: int = 0
        self.init(name) # 初始化默认格式

    def init(self, name: str):
        """初始化段名和默认格式"""
        name = name.lower()
        self.sectionName = self.DEFAULT_FORMAT_CAPS.get(name, name)
        self._setFormat(self.DEFAULT_FORMATS[name])   # 设置默认格式

    def _setFormat(self, fieldNames: list[str] | tuple[str, ...] = None):
        """
        设置样式行的格式
        :param fieldNames: 字段名表，如[Name, Fontname,...]
        """
        if not fieldNames:
            fieldNames = next(iter(self.DEFAULT_FORMATS.values()))
        self._fieldNames.clear()
        self._fieldNameIndexes.clear()
        for i, f in enumerate(fieldNames):
            f = f.lower()   # 全小写格式名，保存名字和序号，用于查找和比较
            self._fieldNames.append(f)
            self._fieldNameIndexes[f] = i
        if 'name' in self._fieldNameIndexes and 'fontname' in self._fieldNameIndexes:
            self._nameIndex = self._fieldNameIndexes['name']
        else:
            raise ValueError("Subtitle format error.")

    def append(self, lineStr: str) -> bool:
        """加入行，必须先加入Format行后才能加入Style行"""
        if lineStr:
            # 切分行，如前段Style，后段Default,...
            line_name, line_content = self._splitLineString(lineStr)
            field_values = [s.strip() for s in line_content.split(',')]
            if line_name == self.FORMAT:    # Format行
                self._setFormat(field_values)
            elif line_name == self.STYLE and self._fieldNameIndexes:    # Style行
                # 用小写样式名索引，方便匹配'default'，并去掉前面可能有的*，*号不参与匹配
                self._styles[field_values[self._nameIndex].lstrip('*')] = field_values
            else:   # 无效行，原样保存在字典中，用于未来导出，
                self._styles[f'{self.INVALID_KEY}{self.__invalidLineNo}'] = [lineStr]
                self.__invalidLineNo += 1
        return False

    def get(self, styleName: str | list[str] | tuple[str], fieldName: str) -> str | None:
        """
        获取指定样式名中的指定字段值。如果样式名是单一字串，则按样式名查找字段值，找不到则用Default替代；
        如果样式名是列表，将会按顺序尝试查找字段值，如果都找不到字段值，则返回None
        :param styleName: 样式名或样式名列表
        :param fieldName: 样式字段名
        :return: 样式字段值，找不到则返回None
        """
        # 用小写样式名去掉前面可能有的*来查找样式值，找不到则用Default替代
        if not self._fieldNameIndexes:
            return None

        field_values = None
        if isinstance(styleName, str):
            field_values = self._styles.get(styleName.lstrip('*'))
            if not field_values:
                field_values = self._styles.get('Default')
        elif isinstance(styleName, (list, tuple)):
            for style_name in styleName:
                field_values = self._styles.get(style_name.lstrip('*'))
                if field_values:
                    break
        # 注意字段名大小写不敏感而样式名大小写敏感
        return field_values[self._fieldNameIndexes[fieldName.lower()]] if field_values else None

    def toString(self) -> str:
        """把整个样式段都输出为字幕文本"""
        if self._styles:
            return '\n'.join([
                self.sectionName,   # 段名，如[V4+ Styles]
                # 格式行，如Format: Name, Fontname,...，大小写标准化
                f"{self.FORMAT}: {', '.join(self.DEFAULT_FORMAT_CAPS.get(f, f) for f in self._fieldNames)}",
                # 样式行，如Style: Default,...
                *[v[0] if k.startswith(self.INVALID_KEY) else f"{self.STYLE}: {','.join(v)}"
                  for k, v in self._styles.items()]
            ])
        else:
            return ''

    def __iter__(self):
        # 返回迭代器时排除无效的行
        return iter(k for k in self._styles if not k.startswith(self.INVALID_KEY))


class FontDict(dict[str, list[str]], SectionLines):
    """
    用于维护所有内嵌字体的类，包括字体名和二进制字体内容. 注意ASS内嵌字体只支持TTF，不支持TTC.
    其中键为内嵌字体名，值为所有同名字体的数据字串列表，字幕文件中保存的多行数据被合并为一行保存.
    """
    FONTNAME_PREFIX = 'fontname:'   # 字体编码数据前一行的名字前缀，规定全小写
    LINE_LENGTH = 80    # 内嵌字体数据自动折行长度

    def __init__(self):
        super().__init__()
        SectionLines.__init__(self, '[Fonts]', continuous=True)
        self._currentFontname = None    # 当前正在插入数据的字体名
        self._currentFontLines = []     # 当前正在插入数据的行列表，用于提高字符串拼接效率

    def append(self, lineStr: str) -> bool:
        """加入行，每个字体以fontname行起始，下一个fontname行或空行结束"""
        if not lineStr:   # 空行，进入下一字体或下一Section
            self._switchFont(None)
            return False
        if lineStr.startswith(self.FONTNAME_PREFIX):    # 字体名行，UUEncoding中不会出现小写字母，所以fontname可以用于判断新字体
            self._switchFont(lineStr[len(self.FONTNAME_PREFIX):].strip())
        elif self._currentFontname:    # 字体数据行
            self._currentFontLines.append(lineStr)  # 暂存行内容到列表，待全部加入之后再join，以提高字符串拼接效率
        # else:   # 没有当前字体名，也不是字体名行，那是无效行
        return True    # 下一个必须还是本Section，直到出现空行为止

    def _switchFont(self, fontName: str | None) -> None:
        """切换字体文件，将上一个文件的数据字串全部拼接成一行"""
        if self._currentFontname:
            if self._currentFontname not in self:
                self[self._currentFontname] = []
            self[self._currentFontname].append(''.join(self._currentFontLines)) # 合并多行内嵌字体
        self._currentFontname = fontName
        self._currentFontLines = []

    def add(self, fontBytes: bytes, fontName: str, index: int = 0, overwrite: bool = False) -> int:
        """
        添加（嵌入）字体文件
        :param fontBytes: 嵌入字体的字节流
        :param fontName: 嵌入字体的文件名，即fontname:行的内容
        :param index: 嵌入字体在同名字体中的序号，仅在overwrite为True时有意义
        :param overwrite: 覆盖现有的同名同序号字体
        :return: 字体实际嵌入的位置序号
        """
        font_code = UU.Encode(fontBytes)
        if fontName in self:
            font_codes = self[fontName]
            if overwrite and index < len(font_codes):
                font_codes[index] = font_code
                return index
            else:
                font_codes.append(font_code)
                return len(font_codes) - 1
        else:
            self[fontName] = [font_code]
            return 0

    def getStream(self, name: str, index: int = 0) -> io.BytesIO | None:
        """
        获取字体对象数据流
        :param name: 内嵌文件名
        :param index: 重复文件名中的编号
        :return: BytesIO，找不到则返回None
        """
        font_code = self.get(name)
        if font_code is None:
            return None
        try:
            ttf_bytes = io.BytesIO(UU.Decode(font_code[index]))
            ttf_bytes.seek(0)
            return ttf_bytes
        except Exception:
            return None

    def toString(self) -> str:
        """把整个内嵌字体段都输出为字幕文本"""
        if self:
            str_list = [self.sectionName]
            for font_name, font_codes in self.items():
                for font_code in font_codes:
                    str_list.append(f"{self.FONTNAME_PREFIX} {font_name}")
                    i = 0
                    while i < len(font_code):   # 拆分为多行写入
                        str_list.append(font_code[i:i + self.LINE_LENGTH])
                        i += self.LINE_LENGTH
                    str_list.append('')  # 空行，代表上一个字体数据结束
            str_list.pop()    # 去掉最后一个多余的空行
            return '\n'.join(str_list)
        else:
            return ''

    def copy(self) -> Self:
        """拷贝实例"""
        new_self = self.__class__()
        for key in self:
            new_self[key] = self[key].copy()
        return new_self


class DialogueList(SectionLines):
    """用于维护所有Dialogue行的类，包括Dialogue格式和所有Dialogue内容"""

    FORMAT = 'Format'
    DIALOGUE = 'Dialogue'
    # ASS默认的格式
    DEFAULT_FORMAT = ('Layer', 'Start', 'End', 'Style', 'Name', 'MarginL', 'MarginR', 'MarginV', 'Effect', 'Text')
    DEFAULT_FORMAT_CAPS: dict[str, str] = {s.lower(): s for s in DEFAULT_FORMAT}    # 默认格式的大小写映射

    def __init__(self):
        super().__init__('[Events]')
        self._fieldNames: list[str] = []   # 样式名表 ['Name', 'Fontname',...]
        self._fieldNameIndexes: dict[str, int] = {}  # 小写样式名和序号的映射 {'name': 0, 'fontname': 1,...}
        # 对Dialogue行，保存拆分的字段值，对其他行如Comment，原文保存
        self._dialogueList: list[list[str] | str] = []  # [[fields] | str]
        self._setFormat()   # 设置格式

    def _setFormat(self, fieldNames: list[str] = None):
        """
        设置对话行的格式
        :param fieldNames: 字段名表，如[Name, Fontname,...]
        """
        if not fieldNames:
            fieldNames = self.DEFAULT_FORMAT
        self._fieldNames.clear()
        self._fieldNameIndexes.clear()
        for i, f in enumerate(fieldNames):
            f = f.lower()   # 格式字段名全用小写，保存名字和序号，用于查找和比较
            self._fieldNames.append(f)
            self._fieldNameIndexes[f] = i
        if 'style' not in self._fieldNameIndexes or 'text' not in self._fieldNameIndexes:
            raise ValueError("Subtitle format error.")

    def append(self, lineStr: str) -> bool:
        """加入行，必须先加入Format行后才能加入Dialogue行"""
        if lineStr:
            # 切分行，如前段Style，后段Default,...
            line_name, line_content = self._splitLineString(lineStr)
            if line_name == self.FORMAT:    # Format行
                field_values = [s.strip() for s in line_content.split(',')]
                self._setFormat(field_values)
            elif line_name == self.DIALOGUE and self._fieldNameIndexes:    # Dialogue行
                # 切分字段值，最多切分为字段名数量分组，最后一个字段值（即Text）内可包含','
                field_values = [s.strip() for s in line_content.split(',', len(self._fieldNameIndexes) - 1)]
                self._dialogueList.append(field_values)
            else:   # 其他行任意名，如Comment，直接保存字串，与Dialogue行的list以类型区分
                self._dialogueList.append(lineStr)
        return False

    def get(self, index: int, fieldName: str) -> str:
        """获取序号指定的Dialogue行的字段值，只能对Dialogue行执行，其他行名的不行"""
        return self._dialogueList[index][self._fieldNameIndexes[fieldName.lower()]]

    def isValid(self, index: int):
        """返回序号指定的行是否是有效的Dialogue行"""
        return isinstance(self._dialogueList[index], list)  # 用数据类型来区分行类型

    def toString(self) -> str:
        if self._dialogueList:
            return '\n'.join([
                self.sectionName,  # 段名，[Events]
                # 格式行，如Format: Name, Fontname,...，大小写标准化
                f"{self.FORMAT}: {', '.join(self.DEFAULT_FORMAT_CAPS.get(f, f) for f in self._fieldNames)}",
                # 对白行，如Dialogue:...
                *[f"{self.DIALOGUE}: {','.join(content)}" if isinstance(content, list) else content
                  for content in self._dialogueList]
            ])
        else:
            return ''

    def __len__(self):
        return len(self._dialogueList)
