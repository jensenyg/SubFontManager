import os
from utils.App import App
from .Font import Font
from .SectionLines import FontDict

if App.isWindows:  # Windows 系统字体匹配库
    from .WinFontMatch import WinFontmatch as FontMatch
elif App.isMac:  # MacOS 系统字体匹配库
    from .MacFontMatch import MacFontMatch as FontMatch
else:
    raise Exception("Unsupported system!")


class FontManager:
    """字体管理类，提供一个路径内所有字体的信息缓存、查询、子集化等操作"""
    # 搜索范围标志码 -------
    EMBED = 0b001
    LOCAL = 0b010
    SYSTEM = 0b100

    FONT_EXTS = ['.otf', '.ttc', '.ttf', '.otc']  # 支持的字体文件后缀名

    def __init__(self, embedFonts: FontDict = None, path: str = None):
        """
        根据给定的字体位置初始化类，path和fontDict分别指定外部和内嵌字体源，
        在搜索时fontDict源会优先于path源.
        :param embedFonts: 内嵌字体字典，将读取其中的字体作为本地缓存
        :param path: 指定"当前目录"，该方法会创建当前目录内的字体索引
        """
        self._embedFonts: list[Font] = []   # 内嵌字体列表
        self._localFonts: list[Font] = []   # 本地路径字体列表

        if embedFonts:
            for font_name in embedFonts:
                for i in range(len(embedFonts[font_name])):  # 字幕文件内可能有重名内嵌字体，都要遍历一遍
                    font_stream = embedFonts.getStream(font_name, i)
                    if font_stream:
                        font = Font.createFontFromBytes(font_stream, font_name, i)
                        if font:  # 如果无法获取名称，则是无效字体
                            self._embedFonts.append(font)    # 内嵌字体只能是TTF，必然只包含一个字体对象
                            continue
                    print(f"Warning: Unable to read embed font info: {font_name}, font ignored.")

        if path:
            # 检索path（通常为字幕同目录）目录下所有字体的信息 ----------
            if os.path.isdir(path):
                with os.scandir(path) as entries:
                    font_files = [entry.path for entry in entries if entry.is_file()]
            elif os.path.isfile(path):
                font_files = [path]
            else:
                print(f"Path '{path}' is invalid.")
                return
            # 过滤后缀名
            font_files = [path for path in font_files if os.path.splitext(path)[1].lower() in self.FONT_EXTS]
            for font_path in sorted(font_files):
                fonts = Font.createFontsFromFile(font_path)
                if fonts:
                    self._localFonts.extend(fonts)
                else:
                    print(f"Warning: Unable to read font info: {font_path}, font ignored.")

    @classmethod
    def _matchSystemFont(cls, fontName: str, bold: bool = False, italic: bool = False) -> str | None:
        """
        在系统中根据字体描述查找系统中合适的字体，支持各种名字和语言匹配
        :param fontName: 字体名，可以是PostScript Name，Full Name或Family Name，按确切程度匹配
        :param bold: 是否粗体
        :param italic: 是否斜体，包括Italic和Oblique
        :return: 匹配到则返回字体文件路径，匹配不到则返回None
        """
        path = FontMatch.getMatchingFontPath(fontName, bold, italic)    # 调用接口匹配系统字体
        return path if path and os.path.splitext(path)[1].lower() in cls.FONT_EXTS else None

    @staticmethod
    def _matchInFonts(fonts: list[Font], fontName: str, bold: bool = False, italic: bool = False) -> Font | None:
        """
        从给定字体列表中找到最匹配给定描述的字体，模拟系统匹配字体的逻辑，但不一定完全一致
        :param fonts: 字体列表
        :param fontName: 字体名，可以是PostScript Name，Family Name或Full Name，按确切程度匹配
        :param bold: 是否粗体
        :param italic: 是否斜体，包括Italic和Oblique
        :return: Font，找不到则返回None
        """
        fontName = fontName.lower()  # 转换为小写匹配
        font: Font | None = next((f for f in fonts if fontName == f.postscriptName), None)  # 匹配Postscript名

        # 先尝试严格匹配 -------
        if font is None:    # 匹配家族名
            family_fonts = [f for f in fonts if fontName in f.familyNames]  # 找出字体全家
            if family_fonts:    # 匹配粗体斜体
                font = next((f for f in family_fonts if f.isBold == bold and f.isItalic == italic), None)
        else:
            family_fonts = None

        if font is None:    # 匹配全名
            font = next((f for f in fonts if fontName in f.fullNames
                         and f.isBold == bold and f.isItalic == italic), None)

        # 如果严格匹配失败，则试试家族内粗体斜体模糊匹配 -------
        if font is None and family_fonts:
            font = next((f for f in family_fonts if f.isBold == bold),  # 忽略斜体尝试匹配粗体符合的
                        next((f for f in family_fonts if f.isItalic == italic), # 忽略粗体尝试匹配斜体符合的
                             family_fonts[0]))  # 都没有就用第一个吧

        return font

    def match(self, fontName: str, bold: bool = False, italic: bool = False, scope: int = None) -> Font | None:
        """
        根据字体名称查找字体文件，先搜索系统安装字体再搜索当前目录字体
        :param fontName: 字体名
        :param bold: 是否粗体
        :param italic: 是否斜体，包括Italic和Oblique
        :param scope: 搜索范围限定.
                      FontManager.EMBED：在内嵌字体中搜索，
                      FontManager.LOCAL：在当前目录搜索，
                      FontManager.SYSTEM：在系统字体中搜索.
                      缺省：先内嵌再当前目录再系统字体.
        :return: Font，找不到则返回None
        """
        font: Font | None = None
        if scope is None:
            scope = self.EMBED | self.LOCAL | self.SYSTEM

        if scope & self.EMBED:  # 在内嵌字体中查找
            font = self._matchInFonts(self._embedFonts, fontName, bold, italic)

        if font is None and scope & self.LOCAL:     # 在本地字体中查找
            font = self._matchInFonts(self._localFonts, fontName, bold, italic)

        if font is None and scope & self.SYSTEM:    # 在系统字体中查找
            path = self._matchSystemFont(fontName, bold, italic)
            if path:    # 如果找到，创建Font对象
                font = self.__class__(path=path).match(fontName, bold, italic, self.LOCAL)
                if font is None:        # 如果系统匹配到字体的这里却匹配不上，说明本类的匹配逻辑不对
                    font = Font(path)   # 这种情况发生的概率不大，如果发生，则直接取文件内的第一个字体吧

        return font

    def getAll(self, scope: int = None) -> list[Font]:
        """
        获取所有本地字体对象
        :param scope: 筛选范围，可以是FontManager.EMBED和FontManager.LOCAL的组合
        :return: 字体列表
        """
        fonts: list[Font] = []
        if scope is None:
            scope = self.EMBED | self.LOCAL
        if scope & self.EMBED:  # 内嵌字体
            fonts.extend(self._embedFonts.copy())
        if not fonts and scope & self.LOCAL:  # 本地字体
            fonts.extend(self._localFonts.copy())
        return fonts
