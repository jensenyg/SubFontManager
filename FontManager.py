import os
import sys
import io
import json
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
from fontTools.subset import Subsetter, Options
from FindSystemFonts import findSystemFonts
# from matplotlib.font_manager import findSystemFonts
from ui import StatusBar


def get_cache_dir(mkdir: bool = False) -> Path:
    """
    获取一个可用于保存字体缓存的路径.
    在Windows和Linux下可以保存在程序目录中，在macOS不能，所以保存到~/Library/Caches中
    """
    dir_name, app_name = os.path.split(sys.argv[0])    # 整个程序的路径和名称
    home = Path.home()
    if sys.platform == 'darwin' and not app_name.endswith('.py'):  # macOS且非调试阶段
        cache_dir = home / "Library" / "Caches" / app_name
        if mkdir:
            cache_dir.mkdir(exist_ok=True)
    # elif sys.platform == 'win32':     # Windows
    #     cache_dir = Path(os.getenv('LOCALAPPDATA', '')) / app_name
    else:   # Linux
        # cache_dir = home / ".cache" / app_name
        cache_dir = Path(dir_name)
    return cache_dir


class FontManager:
    """字体管理类，提供字体缓存、查询、子集化等操作"""

    LOCAL = 'local'
    SYSTEM = 'system'
    cacheFilePath = get_cache_dir(mkdir=True) / 'fontcache.json'    # 字体缓存文件路径

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
                if file:
                    file.close()
                print('Warning: 缓存文件错误，已删除重建.')

        if stopEvent and stopEvent.is_set():
            return

        # 比较缓存列表和系统实际列表的差异，查缺补漏 -----------
        system_font_paths = sorted(findSystemFonts())    # 列出全部系统字体路径
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

        # 基于systemFontsInfo创建字体Name索引表
        cls.systemFontsFamilyNames, cls.systemFontsFullNames = cls._buildFontIndex(cls.systemFontsInfo)

        if stopEvent and stopEvent.is_set():
            return

        # 如果缓存被修改，则更新缓存文件
        save_failed = False
        if cache_modified:
            if os.access(os.path.dirname(cls.cacheFilePath), os.R_OK):
                # 对cache进行排序再保存，这有利于每次载入缓存后减少排序时间
                cls.systemFontsInfo = {key: cls.systemFontsInfo[key]
                                       for key in sorted(cls.systemFontsInfo.keys())}
                # 稍微对缓存文本格式化一下
                cache_list = [f'"{path}": {json.dumps(info, ensure_ascii=False)}'
                              for path, info in cls.systemFontsInfo.items()]
                cache_str = '{\n' + ',\n'.join(cache_list) + '\n}'
                try:
                    with open(cls.cacheFilePath, 'w') as file:
                        file.write(cache_str)
                except Exception as e:
                    if file:
                        file.close()
                    save_failed = True
            else:
                save_failed = True

        if save_failed:
            StatusBar.append('缓存保存失败.', 3)
        elif statusbar_indexing_flag:
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

    @staticmethod
    def decodeNameRecord(record):
        return record.string.decode(record.getEncoding(), errors='ignore')

    def getFontNames(self, file: (str, io.BytesIO), ignoreCache: bool = False) -> list:
        """
        获取指定字体文件内的所有字体名，包括家族（系列）名称、全称和样式名称，优先从缓存中读取
        :param file: 字体文件路径、内嵌字体文件名或BytesIO对象
        :param ignoreCache: 忽略缓存，读取源文件
        :return: [{'familynames':[], 'fullnames':[], 'style':str}]
        """
        font = None
        if type(file) is str:
            if not ignoreCache:    # 搜索缓存
                if file in self.localFontsInfo:
                    return self.localFontsInfo[file]['fontnames']
                elif file in self.systemFontsInfo:
                    return self.systemFontsInfo[file]['fontnames']
            if not os.path.isfile(file) or not os.access(file, os.R_OK):    # 检查路径
                return []

        try:
            # 读取文件
            if type(file) is str and os.path.splitext(file)[1].lower().endswith('.ttc'):
                font_collection = TTCollection(file)
            else:   # 这里有ttf、otf和内存BytesIO对象
                font_collection = [TTFont(file)]

            font_names = []
            for font in font_collection:
                family_names = set()
                full_names = set()
                subfamily_name = None   # 子家族名，即样式名，只取英文的
                for record in font['name'].names:
                    if record.nameID not in (1, 2, 4):
                        continue
                    record_str = self.decodeNameRecord(record).lower()
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

    def __init__(self, path: str = None, assSub=None):
        """
        根据给定的字体位置初始化类，其中path和embedFonts只能二选一，path优先。
        :param path: 指定"当前目录"，该方法会创建当前目录内的字体索引
        :param assSub: SubStationAlpha对象，将读取其中的内嵌字体作为本地缓存
        """
        self.localFontsInfo = {}
        self.localFontsFamilyNames = {}
        self.localFontsFullNames = {}

        if path:
            # 检索path（通常为字幕同目录）目录下所有字体的信息
            for font_path in sorted(findSystemFonts(fontpaths=path)):
                font_names = self.getFontNames(font_path)
                if not font_names:
                    print(f"Warning: 无法读取字体信息: {font_path}, 已忽略该字体.")
                    continue
                self.localFontsInfo[font_path] = {'fontnames': font_names}
        elif assSub:
            for font_name in assSub.fontList:
                embed_font_names = []
                for ttf_bytes in assSub.getEmbedFont(font_name):
                    font_names = self.getFontNames(ttf_bytes)
                    ttf_bytes.close()
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
        根据字体名称查找字体文件，先搜索系统安装字体再搜索当前目录字体
        :param fontName: 字体名
        :param style: 字体样式名，如regular, bold, italic, bold italic
        :param _range: 搜索范围限定，FontManager.LOCAL：在当前目录搜索，FontManager.SYSTEM：在系统字体中搜索，
                       (familyNames, fullNames)：在该索引中搜索，缺省：先当前目录再系统字体
        :return: (path, i)，path：字体文件路径，找不到则返回''，i：当路径为TTC或重复的内嵌字体名时，该数字指代目标字体的次序号
        """
        fontName = fontName.lower()
        style = style.lower() if style else 'regular'
        res = None

        if _range is None or _range == self.SYSTEM:
            if fontName in self.systemFontsFamilyNames:
                font_family = self.systemFontsFamilyNames[fontName]
                res = font_family.get(style, font_family.get('regular', next(iter(font_family.values()))))
            elif fontName in self.systemFontsFullNames:
                res = self.systemFontsFullNames[fontName]

        if (_range is None or _range == self.LOCAL) and res is None:
            if fontName in self.localFontsFamilyNames:
                font_family = self.localFontsFamilyNames[fontName]
                res = font_family.get(style, font_family.get('regular', next(iter(font_family.values()))))
            elif fontName in self.localFontsFullNames:
                res = self.localFontsFullNames[fontName]

        return res if res else ('', 0)

    def indexOfFontInPath(self, path: str, fontName: str, style: str = 'regular') -> int:
        """从指定路径（如TTC或重复内嵌字体文件名）中定位给定的字体名称在第几个位置，找不到则返回-1"""
        family_names, full_names = self._buildFontIndex({path: {'fontnames': self.getFontNames(path)}})
        if fontName in family_names:
            font_family = family_names[fontName]
            res = font_family.get(style, font_family.get('regular', next(iter(font_family.values()))))
        elif fontName in full_names:
            res = full_names[fontName]
        else:
            return -1
        return res[1]

    @staticmethod
    def fontSubset(font: TTFont, text: str, options: dict = None):
        """
        对字体文件取子集
        :param font: 目标TTF字体对象
        :param text: 子集内需要保留的字符集
        :param options: 额外选项
        :return: io.BytesIO
        """
        subsetter = Subsetter(options=Options(
            ignore_missing_glyphs=True    # 忽略缺失字形错误
        ))
        subsetter.populate(text=text)
        subsetter.subset(font)
