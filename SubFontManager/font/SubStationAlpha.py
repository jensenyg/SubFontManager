import os
import re
from dataclasses import dataclass
from charset_normalizer import from_path
from utils import Lang
from .SectionLines import *
from .Font import Font
from .FontManager import FontManager


@dataclass
class SubFontDesc:
    """SubStationAlpha.gatherFonts返回的字体描述类"""
    fontName: str   # 字体被引用的名字
    text: set[str]  # 字体覆盖的（不重复）字符
    bold: bool      # 字体是否是粗体
    italic: bool    # 字体是否是斜体
    isEmbed: bool = False   # 当前字体对象是否是内嵌字体
    font: Font | None = None    # 字体对象，可能为None


class SubFontDescDict(dict[tuple[str, bool, bool], SubFontDesc]):
    """用于收集字幕中出现过字体以及其覆盖的字符，结构为{(fontName, bold, italic): chars}"""

    def __init__(self, fontMgr: FontManager):
        super().__init__()
        self.fontMgr = fontMgr

    def addTextToFont(self, fontName: str, bold: str | bool, italic: str | bool, text: str = '', font: Font = None):
        """向字典中加入字体并合并覆盖的文字"""
        bold = bool(int(bold))  # 非0都判断为真，如1、-1、2等
        italic = bool(int(italic))
        # 向字典中加入字体覆盖的文字 ----------
        key = (fontName, bold, italic)  # 字典的访问键
        chars = set(c for c in text)    # 将每一个字符单独加入set，合并重复字符
        if key in self:
            self[key].text.update(chars)
        else:   # 新字体，搜索文件源，注意搜索结果可能为None
            if font is None:
                font = self.fontMgr.match(fontName, bold, italic)
            is_embed = bool(font and font.isInMemory)
            self[key] = SubFontDesc(fontName, chars, bold, italic, is_embed, font)


class SubStationAlpha:
    """ASS字幕类，维护字幕的所有Style、Font、Dialogue内容和读写操作"""

    # 分析对白文本中内联样式的正则式 ---------
    _inlineStyle_ptn = re.compile(r'\{.+?}')    # 用于查找行内样式{}的内容
    _inlineFont_ptn = re.compile(r'\\fn(.+?)[\\,}]')# 用于查找{}内的\fn内容并提取字体名
    _inlineBold_ptn = re.compile(r'\\b\s*(\d+)')    # 用于查找{}内的\b并提取后面的数字，注意不要跟\bord混淆
    _inlineItalic_ptn = re.compile(r'\\i\s*(\d+)')  # 用于查找{}内的\i并提取后面的数字
    _section_ptn = re.compile(r'^\[.*]')    # 匹配中括号行[...]

    def __init__(self, path: str, encoding: str = None):
        self.filePath = path    # 文件路径

        self.infoList = SectionLines('[Script Info]') # Script Info段
        self.styleDict = StyleDict()    # Style段
        self.fontDict = FontDict()      # 内嵌字体段，结构为{fontname: [fontcode]}，fontname可能有重复，所以值是一个list
        self.graphicList = SectionLines('[Graphics]', continuous=True)   # 内嵌图片段，这里只存行字串，不做任何处理
        self.dialogueList = DialogueList()  # 对白段

        self.sectionsInOrder: list[SectionLines] = []   # 保存各个SectonLines并记录它们的顺序，以便重建文件时不会搞混
        self._load(path, encoding)  # 载入文件
        self.fontMgr = FontManager(embedFonts=self.fontDict, path=os.path.dirname(self.filePath))  # 管理内嵌字体
        self.ignoredFonts: list[str] = []   # 内嵌字体中的无效项

        # 检查内嵌字体中是否有无效的项，将无效项从fontDict转移到ignoredFonts ---------
        valid_fonts = [(f.path, f.index) for f in self.fontMgr.getAll(FontManager.EMBED)]
        if len(valid_fonts) < len(self.fontDict):  # 如果有效字体的数量少了，说明有无效的内嵌字体
            for font_name, font_codes in list(self.fontDict.items()):
                for i in range(len(font_codes)):
                    if (font_name, i) not in valid_fonts:
                        if len(font_codes) == 1:
                            self.ignoredFonts.append(font_name)
                            self.fontDict.pop(font_name)
                        else:
                            self.ignoredFonts.append(f"{font_name}#{i+1}")
                            font_codes.pop(i)

    @classmethod
    def load(cls, path: str, encoding: str = None) -> Self:
        """
        载入字幕文件并构造实例
        :param path: 文件路径
        :param encoding: 读取编码
        :return: SubStationAlpha实例
        """
        if not os.path.isfile(path):
            raise Exception(Lang["File {p} doesn't exist."].format(p=path))
        elif not os.access(path, os.R_OK):
            raise Exception(Lang['Unable to read file {p}.'].format(p=path))
        else:
            return cls(path, encoding)

    def _load(self, path: str, encoding: str = None):
        """载入字幕文件"""
        if not encoding:    # 如果没有指定编码，则自动判断
            match = from_path(path).best()
            if match:
                encoding = match.encoding
            else:
                raise Exception(Lang["Subtitle encoding cannot be recognized."])

        sections: dict[str, SectionLines] = {   # Section按名索引表
            self.infoList.sectionName.lower(): self.infoList,
            self.styleDict.sectionName.lower(): self.styleDict,
            self.fontDict.sectionName.lower(): self.fontDict,
            self.graphicList.sectionName.lower(): self.graphicList,
            self.dialogueList.sectionName.lower(): self.dialogueList
        }

        section_lines: SectionLines | None = None   # 当前行所在的Section对象
        continuous_section = False  # 是否正在读取连贯Section

        with (open(path, 'r', encoding=encoding) as file):  # 打开文件
            for i, line in enumerate(file):   # 读取每一行
                first_printable_pos = next((j for j, c in enumerate(line) if c.isprintable()), len(line))
                line = line[first_printable_pos:].rstrip('\r\n')    # 去掉开头的不可打印字符和尾部的回车
                if not continuous_section:  # 非连贯段，即这一行可以开始一个新的Section
                    match_obj = self._section_ptn.match(line)   # 检查是否以[*]开头的Section行
                    if match_obj:    # 中括号行出现，切换行类型
                        section_name = match_obj.group(0).lower()
                        # 对于非标准的Section，如"[Aegisub Project Garbage]"，临时新建一个SectonLines保存
                        section_lines = sections.get(section_name, SectionLines(section_name.title()))
                        if section_lines not in self.sectionsInOrder:   # 如果标准Section有重复的，以第一个的位置为准
                            self.sectionsInOrder.append(section_lines)  # 保存入顺序表
                        continue
                try:
                    continuous_section = section_lines.append(line) # 向SectionLines插入新行
                except ValueError:
                    raise Exception(Lang["Subtitle line {d} format error."].format(d=i+1))

    def save(self, path: str = None, encoding: str = None):
        """
        保存文件到路径
        :param path: 保存路径，缺省则写入到源文件
        :param encoding: 写入编码
        """
        if not path:
            path = self.filePath
        path_exists = os.path.exists(path)  # 路径是否已存在，不存在说明是要保存为新文件
        if (path_exists and not os.access(path, os.W_OK) or  # 原地保存却无法访问文件
                not path_exists and not os.access(os.path.dirname(path) or '..', os.W_OK)):  # 新建文件却目录无法访问
            raise Exception(Lang['Unable to write file {p}.'].format(p=path))
        if not encoding:
            encoding = 'utf-8'    # 默认使用UTF-8编码

        # 检查Fonts段是否被删除或新增 -----
        if self.fontDict in self.sectionsInOrder:   # 原来就有，看删除了没，如果删了就不用输出[Fonts]了
            if not len(self.fontDict):
                self.sectionsInOrder.remove(self.fontDict)
        elif len(self.fontDict):    # 原来没有，看现在有了没，如果又了就要输出[Fonts]段
            self.sectionsInOrder.insert(self.sectionsInOrder.index(self.styleDict) + 1, self.fontDict)

        # 写入文件 -----
        with open(path, 'w', encoding=encoding) as file:
            for section_lines in self.sectionsInOrder:
                file.write(section_lines.toString())
                file.write('\n\n')

    def gatherFonts(self) -> list[SubFontDesc]:
        """搜集字幕中所有出现过的字体，包括样式字体、内联样式字体和内嵌字体，以及每种字体覆盖的文字数量"""
        fontDescDict = SubFontDescDict(self.fontMgr)
        # 收集Style中出现的字体. 这一步的目的是因为有些Style可能覆盖字符数为0，但仍应该显示于界面列表中
        for style_name in self.styleDict:
            fontDescDict.addTextToFont(
                self.styleDict.get(style_name, 'fontname'),
                self.styleDict.get(style_name, 'bold'),
                self.styleDict.get(style_name, 'italic')
            )

        # 收集Dialogue中出现的字体 ---------
        for i in range(len(self.dialogueList)):  # 遍历每一行对白
            # 获取该行的样式名，去掉开头可能存在的*号
            style_name = self.dialogueList.get(i, 'style').lstrip('*')  # 样式名，如：Default
            fontname = self.styleDict.get(style_name, 'fontname')       # 该样式的字体名
            if not fontname:    # 样式找不到且Default样式也没有
                continue
            bold = self.styleDict.get(style_name, 'bold')       # 是否粗体，如"0"
            italic = self.styleDict.get(style_name, 'italic')   # 是否斜体，如"1"
            # 查找行内样式{} ---------
            text = self.dialogueList.get(i, 'text')  # 对白文本部分，里面可能还有{}内联样式
            match_iter = self._inlineStyle_ptn.finditer(text)  # {}正则匹配
            pos = 0    # 字符位置指针
            for m_obj in match_iter:    # 遍历每一个{}中的内容
                # 将{}之前的文字都划归给上一种样式
                fontDescDict.addTextToFont(fontname, bold, italic, text[pos: m_obj.start()])
                pos = m_obj.end()
                inline_style_str = m_obj.group().lower()    # {}以及内部的文字
                # 处理{}中的\fn ---------
                all_match = self._inlineFont_ptn.findall(inline_style_str)
                if all_match:   # 提取最后一个\fn后面的字体名
                    fontname = all_match[-1].strip()
                # 处理{}中的\b ----------
                all_match = self._inlineBold_ptn.findall(inline_style_str)
                if all_match:   # 提取最后一个\b后面的数字
                    bold = all_match[-1]
                # 处理{}中的\i ----------
                all_match = self._inlineItalic_ptn.findall(inline_style_str)
                if all_match:   # 提取最后一个\i后面的数字
                    italic = all_match[-1]
            # 将最后一个{}（或没有）之后的文字都划归给最后一个样式
            fontDescDict.addTextToFont(fontname, bold, italic, text[pos:])

        # 查找未被引用的内嵌字体 ---------
        all_fonts = [font_desc.font for font_desc in fontDescDict.values() if font_desc.font]   # 所有找到的字体
        for font in self.fontMgr.getAll(FontManager.EMBED):  # 所有内嵌字体
            if font not in all_fonts:   # 未被引用的内嵌字体，但仍然应该显示在界面列表中
                fontDescDict.addTextToFont(font.path, font.isBold, font.isItalic, '', font)

        return list(fontDescDict.values())
