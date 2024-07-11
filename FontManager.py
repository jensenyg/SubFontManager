from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
import matplotlib.font_manager as fm


class FontManager:
    systemFontsFamilyNames = {}
    systemFontsFullNames = {}

    @staticmethod
    def indexFontsInDirectory(path: str = None) -> tuple:
        family_names = {}
        full_names = {}
        paths = sorted(fm.findSystemFonts(fontpaths=path))
        for font_path in paths:
            try:
                if font_path.lower().endswith('.ttc'):
                    font_collection = TTCollection(font_path)
                else:
                    font_collection = [TTFont(font_path)]
                for font in font_collection:
                    for record in font['name'].names:
                        if record.nameID == 1 or record.nameID == 4:
                            record_str = record.string.decode(record.getEncoding(), errors='ignore').lower()
                            if record.nameID == 1:
                                family_names[record_str] = font_path
                            else:
                                full_names[record_str] = font_path
            except Exception as e:
                print(f"Warning: 无法读取系统字体信息: {font_path}, 已忽略该字体.")
        return family_names, full_names

    def __init__(self, path: str = None):
        if path:
            self.localFontsFamilyNames, self.localFontsFullNames = self.indexFontsInDirectory(path)
        else:
            localFontsFamilyNames, self.localFontsFullNames = {}, {}

    def findFont(self, fontName: str) -> str:
        fontName = fontName.lower()
        return self.localFontsFullNames.get(fontName,
            self.localFontsFamilyNames.get(fontName,
                self.systemFontsFullNames.get(fontName,
                    self.systemFontsFamilyNames.get(fontName))))


print('Indexing system fonts... ', end='')
FontManager.systemFontsFamilyNames, FontManager.systemFontsFullNames = FontManager.indexFontsInDirectory()
print('Done.')
