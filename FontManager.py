import os
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
import matplotlib.font_manager as fm


class FontManager:
    cacheFilePath = './fontcache.json'
    systemFontsCache = []  # [{fontpath: str, familynames: str, fullnames: str, filesize: int}]
    systemFontsFamilyNames = {}     # {familyname, fontpath}
    systemFontsFullNames = {}       # {fullname, fontpath}

    @classmethod
    def initSystemFontList(cls):
        # 读取缓存文件
        if os.path.isfile(cls.cacheFilePath) and os.access(cls.cacheFilePath, os.R_OK):
            try:
                with open(cls.cacheFilePath, 'r') as file:
                    cache_str = file.read()
                cls.systemFontsCache = eval(cache_str)
            except Exception as e:
                print('Warning: 缓存文件错误，已删除重建.')

        # 比较缓存列表和系统实际列表的差异，查缺补漏 -----------
        system_font_paths = sorted(fm.findSystemFonts())    # 列出全部系统字体路径
        i, j = 0, 0
        cache_len = len(cls.systemFontsCache)   # 记录缓存数量，如果老缓存条目被删除，该数量应随之减少
        cache_modified = False    # 缓存修改标记，用于判断是否需要重新保存缓存
        while i < len(system_font_paths):
            path = system_font_paths[i]
            cache_item = cls.systemFontsCache[j] if j < cache_len else None
            file_size = os.path.getsize(path)
            if cache_item and cache_item['fontpath'] == path and cache_item['filesize'] == file_size:
                i += 1
                j += 1
            elif not cache_item or cache_item['fontpath'] > path:   # 系统中的字体是新增的，加入到缓存中
                res = cls.getFontNames(path)
                if res:
                    cls.systemFontsCache.append({'fontpath': path, 'familynames': res[0],
                                                 'fullnames': res[1], 'filesize': file_size})
                    cache_modified = True
                else:
                    print(f"Warning: 无法读取系统字体信息: {path}, 已忽略该字体.")
                i += 1
            else:    # 缓存中的字体已经无效，删除缓存条目
                cls.systemFontsCache.pop(j)
                cache_len -= 1    # 老缓存条目删除，缓存数量需减少，否则j会检索到新增条目上
                cache_modified = True

        # 如果缓存被修改，则更新缓存文件
        if cache_modified:
            # 稍微对缓存文本格式化一下
            cache_list = [str(fi) for fi in cls.systemFontsCache]
            cache_str = '[\n' + ',\n'.join(cache_list) + '\n]'
            with open(cls.cacheFilePath, 'w') as file:
                file.write(cache_str)

        # 基于systemFontsCache创建两个Name表
        for font in cls.systemFontsCache:
            cls.systemFontsFamilyNames.update({name: font['fontpath'] for name in font['familynames']})
            cls.systemFontsFullNames.update({name: font['fontpath'] for name in font['fullnames']})

    @staticmethod
    def getFontNames(path: str):
        try:
            family_names = set()
            full_names = set()
            if path.lower().endswith('.ttc'):
                font_collection = TTCollection(path)
            else:
                font_collection = [TTFont(path)]
            for font in font_collection:
                for record in font['name'].names:
                    if record.nameID == 1 or record.nameID == 4:
                        record_str = record.string.decode(record.getEncoding(), errors='ignore').lower()
                        if not record_str:
                            continue
                        elif record.nameID == 1:
                            family_names.add(record_str)
                        else:
                            full_names.add(record_str)
            return family_names, full_names
        except Exception as e:
            return None

    def __init__(self, path: str = None):
        self.localFontsFamilyNames = {}
        self.localFontsFullNames = {}
        if not path:
            return
        # 创建path（通常为字幕同目录）目录下所有字体的缓存
        for font_path in sorted(fm.findSystemFonts(fontpaths=path)):
            res = self.getFontNames(font_path)
            if not res:
                print(f"Warning: 无法读取字体信息: {font_path}, 已忽略该字体.")
                continue
            self.localFontsFamilyNames.update({name: font_path for name in res[0]})
            self.localFontsFullNames.update({name: font_path for name in res[1]})

    def findFont(self, fontName: str) -> str:
        fontName = fontName.lower()
        return self.localFontsFullNames.get(
            fontName, self.localFontsFamilyNames.get(
                fontName, self.systemFontsFullNames.get(
                    fontName, self.systemFontsFamilyNames.get(fontName))))


print('Indexing system fonts... ', end='')
FontManager.initSystemFontList()
print('Done.')
