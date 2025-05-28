import os
from utils.App import App
from .CoreText import CoreText
from .Font import Font
from .SectionLines import FontDict


class FontManager:
    """字体管理类，提供一个路径内所有字体的信息缓存、查询、子集化等操作"""
    # 搜索范围标志码 -------
    EMBED = 0b00000001
    LOCAL = 0b00000010
    SYSTEM = 0b00000100

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
    def _matchMacFont(cls, fontName: str = None, fullName: str = None,
                      familyName: str = None, styleName: str = None) -> str | None:
        """
        在MacOS中根据字体描述查找系统中合适的字体
        :param fontName: 字体名，可以是PostScript Name，Full Name或Family Name，按确切程度匹配
        :param fullName: 字体全名
        :param familyName: 字体家族名
        :param styleName: 字体样式名
        :return: 匹配到则返回字体文件路径，匹配不到则返回None
        """
        attrs = {}   # 用于筛选的字体描述字典
        if fontName is not None:
            attrs[CoreText.kCTFontNameAttribute] = fontName
        if fullName is not None:
            attrs[CoreText.kCTFontDisplayNameAttribute] = fullName
        if familyName is not None:
            attrs[CoreText.kCTFontFamilyNameAttribute] = familyName
        if styleName is not None:
            attrs[CoreText.kCTFontStyleNameAttribute] = styleName
        if not attrs:
            return None
        path = CoreText.GetMatchingFontPath(attrs)  # 匹配字体路径
        return path if path and os.path.splitext(path)[1].lower() in cls.FONT_EXTS else None

    @classmethod
    def _matchWindowsFont(cls, fontName: str = None, fullName: str = None,
                          familyName: str = None, styleName: str = None) -> str | None:
        pass

    @classmethod
    def _matchSystemFont(cls, fontName: str, styleName: str = None) -> str | None:
        """
        在系统中根据字体描述查找系统中合适的字体，支持各种名字和语言匹配
        :param fontName: 字体名，可以是PostScript Name，Full Name或Family Name，按确切程度匹配
        :param styleName: 字体样式名，找不到会以Regular或家族内第一个样式替代
        :return: 匹配到则返回字体文件路径，匹配不到则返回None
        """
        if App.isWindows:   # Windows
            matchFunc = cls._matchWindowsFont
        elif App.isMac:     # MacOS
            matchFunc = cls._matchMacFont
        else:
            raise Exception("Unsupported system!")

        path = matchFunc(fontName, styleName=styleName)  # 按样式查找
        if path is None:    # 找不到则放弃样式限定
            path = matchFunc(fontName)
        return path

    @staticmethod
    def _findInFonts(fonts: list[Font], fontName: str, styleName: str = None) -> Font | None:
        """
        从给定字体列表中找到最匹配给定描述的字体，模拟系统匹配字体的逻辑，但不一定完全一致
        :param fonts: 字体列表
        :param fontName: 字体名，可以是PostScript Name，Family Name或Full Name，按确切程度匹配
        :param styleName: 字体样式名
        :return: Font，找不到则返回None
        """
        fontName = fontName.lower()  # 转换为小写匹配
        if styleName is not None:
            styleName = styleName.lower()    # 转换为小写匹配

        font: Font | None = next((f for f in fonts if fontName == f.postscriptName), None)  # 匹配Postscript名

        if font is None:    # 匹配家族名
            family_fonts = [f for f in fonts if fontName in f.familyNames]  # 找出字体全家
            if family_fonts:
                font = None if styleName is None else (  # 匹配样式名
                    next((f for f in family_fonts if styleName in f.styleNames), None))
        else:
            family_fonts = None

        if font is None:    # 匹配全名
            font = next((f for f in fonts if fontName in f.fullNames), None)

        if font is None and family_fonts:   # 同家族regular做样式替补，要是regular也没有就用第一个
            font = next((f for f in family_fonts if 'regular' in f.styleNames), family_fonts[0])
        return font

    def find(self, fontName: str, styleName: str = None, scope: int = None) -> Font | None:
        """
        根据字体名称查找字体文件，先搜索系统安装字体再搜索当前目录字体
        :param fontName: 字体名
        :param styleName: 字体样式名，如regular, bold, italic, bold italic
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
            font = self._findInFonts(self._embedFonts, fontName, styleName)

        if font is None and scope & self.LOCAL:     # 在本地字体中查找
            font = self._findInFonts(self._localFonts, fontName, styleName)

        if font is None and scope & self.SYSTEM:    # 在系统字体中查找
            path = self._matchSystemFont(fontName, styleName)
            if path:    # 如果找到，创建Font对象
                font = self.__class__(path=path).find(fontName, styleName, self.LOCAL)
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
