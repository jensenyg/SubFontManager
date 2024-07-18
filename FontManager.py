import os
import io
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
from fontTools.subset import Subsetter, Options
import matplotlib.font_manager as fm
from StatusBar import StatusBar
from UUEncoding import UUDecode


class FontManager:
    LOCAL = 'local'
    SYSTEM = 'system'
    cacheFilePath = './fontcache.json'

    # 对于多字体的文件（如TTC），每个字体对象的名称分别保存在'fontnames'列表内
    # {fontpath: {'fontnames': [{'familynames': str, 'fullnames': str, 'style': str}], 'filesize': int}}
    systemFontsInfo = {}
    systemFontsFamilyNames = {}     # {familyname: {style: (fontpath, index)}}
    systemFontsFullNames = {}       # {fullname: (fontpath, index)}

    @classmethod
    def initSystemFontList(cls, ignoreCache: bool = False, stopEvent=None):
        """
        初始化类，索引系统字体并创建缓存文件，如果发现了缓存，则读取缓存，并和系统字体进行比较，然后查缺补漏.
        :param ignoreCache: 忽略缓存文件，重新扫描系统字体库
        :param stopEvent: 停止事件，用于在异步执行时通知函数停止执行。
        """
        if stopEvent and stopEvent.is_set():
            return

        # 读取缓存文件
        if not ignoreCache and os.path.isfile(cls.cacheFilePath) and os.access(cls.cacheFilePath, os.R_OK):
            try:
                with open(cls.cacheFilePath, 'r') as file:
                    cache_str = file.read()
                cls.systemFontsInfo = eval(cache_str)
                # cls.systemFontsCache.sort(key=lambda e: e['fontpath'])
            except Exception as e:
                print('Warning: 缓存文件错误，已删除重建.')

        if stopEvent and stopEvent.is_set():
            return

        # 比较缓存列表和系统实际列表的差异，查缺补漏 -----------
        system_font_paths = sorted(fm.findSystemFonts())    # 列出全部系统字体路径
        cache_font_paths = sorted(cls.systemFontsInfo.keys())
        cache_modified = False    # 缓存修改标记，用于判断是否需要重新保存缓存
        fontMgr = cls()
        statusbar_indexing_flag = False     # 状态栏"正在索引"标记
        i, j = 0, 0
        while i < len(system_font_paths):
            if stopEvent and stopEvent.is_set():
                return
            system_path = system_font_paths[i]
            cache_path = cache_font_paths[j] if j < len(cache_font_paths) else None
            system_file_size = os.path.getsize(system_path)
            if cache_path == system_path and cls.systemFontsInfo[cache_path]['filesize'] == system_file_size:
                i += 1
                j += 1
            elif not cache_path or cache_path > system_path:   # 系统中的字体是新增的，加入到缓存中
                if not statusbar_indexing_flag:
                    StatusBar.set('正在索引系统字体... ')
                    statusbar_indexing_flag = True
                font_names = fontMgr.getFontNames(system_path, ignoreCache=True)
                if font_names:
                    cls.systemFontsInfo[system_path] = {'fontnames': font_names, 'filesize': system_file_size}
                    cache_modified = True
                else:
                    print(f"Warning: 无法读取系统字体信息: {system_path}, 已忽略该字体.")
                i += 1
            else:    # 缓存中的字体已经无效，删除缓存条目
                cls.systemFontsInfo.pop(cache_path)
                cache_modified = True

        if stopEvent and stopEvent.is_set():
            return

        # 如果缓存被修改，则更新缓存文件
        if cache_modified:
            # 对cache进行排序再保存，这有利于每次载入缓存后减少排序时间
            cls.systemFontsInfo = {key: cls.systemFontsInfo[key] for key in sorted(cls.systemFontsInfo.keys())}
            # 稍微对缓存文本格式化一下
            cache_list = [f'\'{key}\': {str(cls.systemFontsInfo[key])}' for key in cls.systemFontsInfo]
            cache_str = '{\n' + ',\n'.join(cache_list) + '\n}'
            with open(cls.cacheFilePath, 'w') as file:
                file.write(cache_str)

        if stopEvent and stopEvent.is_set():
            return

        # 基于systemFontsInfo创建字体Name索引表
        cls.systemFontsFamilyNames, cls.systemFontsFullNames = cls._buildFontIndex(cls.systemFontsInfo)

        if statusbar_indexing_flag:
            StatusBar.append('完成.', 3)

    @staticmethod
    def _buildFontIndex(fontsInfo: dict) -> tuple:
        family_names = {}
        full_names = {}
        for font_path, font_obj in fontsInfo.items():
            for i, font_names in enumerate(font_obj['fontnames']):
                for name in font_names['familynames']:
                    if name in family_names:
                        family_names[name][font_names['style']] = (font_path, i)
                    else:
                        family_names[name] = {font_names['style']: (font_path, i)}
                full_names.update({name: (font_path, i) for name in font_names['fullnames']})
        return family_names, full_names

    def getFontNames(self, path: (str, io.BytesIO), ignoreCache: bool = False) -> list:
        """
        获取指定字体文件内的所有字体名，包括家族（系列）名称、全称和样式名称，优先从缓存中读取
        :param path: 字体文件路径、内嵌字体文件名或BytesIO对象
        :param ignoreCache: 忽略缓存，读取源文件
        :return: [{'familynames':[], 'fullnames':[], 'style':str}]
        """
        font = None
        if type(path) is str:
            if not ignoreCache:    # 搜索缓存
                if path in self.localFontsInfo:
                    return self.localFontsInfo[path]['fontnames']
                elif path in self.systemFontsInfo:
                    return self.systemFontsInfo[path]['fontnames']
            if not os.path.isfile(path) or not os.access(path, os.R_OK):    # 检查路径
                return []

        try:
            # 读取文件
            if type(path) is str and path.lower().endswith('.ttc'):
                font_collection = TTCollection(path)
            else:   # 这里有ttf、otf和内存BytesIO对象
                font_collection = [TTFont(path)]

            font_names = []
            for font in font_collection:
                family_names = set()
                full_names = set()
                subfamily_name = None   # 子家族名，即样式名，只取英文的
                for record in font['name'].names:
                    if record.nameID not in (1, 2, 4):
                        continue
                    record_str = record.string.decode(record.getEncoding(), errors='ignore').lower()
                    if not record_str:
                        continue
                    elif record.nameID == 1:    # Family Name
                        family_names.add(record_str)
                    elif record.nameID == 2:    # Subfamily Name (Style)，只取英文样式名
                        # 不同系统下的英文ID：Unicode: platformID=0, langID=1033,
                        # Mac: platformID=1, langID=0, Win: platformID=3, langID=1033
                        if (record.platformID, record.langID) in ((0, 1033), (1, 0), (3, 1033)):
                            subfamily_name = record_str
                    elif record.nameID == 4:    # Full Name
                        full_names.add(record_str)
                    # elif record.nameID == 6:    # PostScript Name，在系统字体匹配规则中貌似没有用到
                font.close()    # 关闭字体资源
                font_names.append({
                    'familynames': list(family_names),
                    'fullnames': list(full_names),
                    'style': subfamily_name if subfamily_name else 'regular'    # 如果样式为空则补regular
                })

            return font_names
        except Exception as e:
            if font:    # 关闭可能未来得及关闭的字体文件
                font.close()
            return []

    def __init__(self, path: str = None, embedFonts: dict = None):
        """
        根据给定的字体位置初始化类，其中path和embedFonts只能二选一，path优先。
        :param path: 指定"当前目录"，该方法会创建当前目录内的字体索引
        :param embedFonts: 内嵌字体列表，[{'fontname': str, 'fontcode': str, 'names': []}]
        """
        self.localFontsInfo = {}
        self.localFontsFamilyNames = {}
        self.localFontsFullNames = {}

        if path:
            # 检索path（通常为字幕同目录）目录下所有字体的信息
            for font_path in sorted(fm.findSystemFonts(fontpaths=path)):
                font_names = self.getFontNames(font_path)
                if not font_names:
                    print(f"Warning: 无法读取字体信息: {font_path}, 已忽略该字体.")
                    continue
                self.localFontsInfo[font_path] = {'fontnames': font_names}
        elif embedFonts:
            for font_name, font_codes in embedFonts.items():
                embed_font_names = []
                for i, font_code in enumerate(font_codes):
                    # 将内嵌字体数据解码，还原为TTF文件并读取其名称
                    memory_ttf = io.BytesIO()
                    memory_ttf.write(UUDecode(font_code))
                    memory_ttf.seek(0)
                    font_names = self.getFontNames(memory_ttf)
                    memory_ttf.close()
                    if not font_names:  # 如果无法获取名称，则是无效字体
                        print(f"Warning: 无法读取内嵌字体信息: {font_name}, 已忽略该字体.")
                        # embedFonts.remove(font_obj)
                        continue
                    embed_font_names.append(font_names[0])    # 内嵌字体只能是TTF，必然只包含一个字体对象
                self.localFontsInfo[font_name] = {'fontnames': embed_font_names}
        else:
            return

        # 创建字体Name索引
        self.localFontsFamilyNames, self.localFontsFullNames = self._buildFontIndex(self.localFontsInfo)

    def findFont(self, fontName: str, style: str = None, _range=None) -> tuple:
        """
        根据字体名称查找字体文件，先后搜索系统安装字体和当前目录字体
        :param fontName: 字体名
        :param style: 字体样式名，如regular, bold, italic, bold italic
        :param _range: 搜索范围限定，FontManager.LOCAL：在当前目录搜索，FontManager.SYSTEM：在系统字体中搜索，
                       (familyNames, fullNames)：在该索引中搜索，缺省：先当前目录再系统字体
        :return: (path, i)，path：字体文件路径，找不到则返回''，i：当路径为TTC或重复的内嵌字体名时，该数字指代目标字体的次序号
        """
        fontName = fontName.lower()
        style = style.lower() if style else 'regular'
        res = None

        if _range is None or _range == self.LOCAL:
            if fontName in self.localFontsFamilyNames:
                font_family = self.localFontsFamilyNames[fontName]
                res = font_family.get(style, font_family.get('regular', next(iter(font_family.values()))))
            elif fontName in self.localFontsFullNames:
                res = self.localFontsFullNames[fontName]

        if (_range is None or _range == self.SYSTEM) and res is None:
            if fontName in self.systemFontsFamilyNames:
                font_family = self.systemFontsFamilyNames[fontName]
                res = font_family.get(style, font_family.get('regular', next(iter(font_family.values()))))
            elif fontName in self.systemFontsFullNames:
                res = self.systemFontsFullNames[fontName]

        return res if res else ('', 0)

    def indexOfFontInPath(self, fontName: str, path: str) -> int:
        """从指定路径（如TTC或重复内嵌字体文件名）中定位给定的字体名称在第几个位置，找不到则返回-1"""
        font_names = self.getFontNames(path)
        for i, names in enumerate(font_names):
            if fontName in names['familynames']:
                return i
        for i, names in enumerate(font_names):
            if fontName in names['fullnames']:
                return i
        return -1

    @staticmethod
    def fontSubset(path, text: str, options: dict = None) -> io.BytesIO:
        """
        对字体文件取子集
        :param path: 目标字体文件路径，或者io.BytesIO
        :param text: 子集内需要保留的字符集
        :param options: 额外选项
        :return: io.BytesIO
        """
        font = TTFont(path)
        subsetter = Subsetter(options=Options(
            glyph_names=True,   # 保留字形名称
            ignore_missing_glyphs=True    # 忽略缺失字形错误
        ))
        subsetter.populate(text=text)
        subsetter.subset(font)
        memory_ttf = io.BytesIO()
        font.save(memory_ttf)
        return memory_ttf
