import os
import io
from typing import Self
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
from fontTools.subset import Subsetter, Options
from utils import Lang


class Font:
    """字体类，每个实例代表一个TTF，拥有唯一的Postscript Name"""
    # TTF名表中几种名字的ID号 -----
    FamilyNameID = 1
    SubfamilyNameID = 2
    FullNameID = 4
    PostscriptNameID = 6
    # Weight和Style常量 -----
    WEIGHT_NORMAL = 400
    WEIGHT_BOLD = 700
    STYLE_NORMAL = 0
    STYLE_OBLIQUE = 1
    STYLE_ITALIC = 2

    def __init__(self, path: str, index: int = 0, inMemory: bool = False, openNow: bool = True):
        self.path: str = path   # 字体文件路径，内存字体则此值随意指定
        self.index: int = index # 字体在路径内的编号
        self.inTTC: bool = os.path.splitext(path)[1].lower().endswith('.ttc')   # 字体是否在TTC文件内
        self.postscriptName: str = ''       # Postscript名，是字体的唯一标识
        self.familyNames: set[str] = set()  # 字体家族名，包括各种语言的版本
        self.fullNames: set[str] = set()    # 字体全名，包括各种语言的版本
        self.styleNames: set[str] = set()   # 字体样式名，包括各种语言的版本
        self.weight: int = 400  # 字重，1-999, 常见如 400 (normal), 700 (bold)
        self.style: int = 0     # 风格，0: Normal，1: Oblique，2: Italic
        self.inMemory: bool = inMemory      # 是否内存字体，即字幕内嵌字体
        self._byteStream: io.BytesIO | None = None  # 字体的数据字节流

        if openNow and os.path.isfile(self.path) and os.access(self.path, os.R_OK):  # 检查路径
            with self.open() as ttf_font:   # 打开字体并读取信息
                self._readInfo(ttf_font)

    def _readInfo(self, ttFont: TTFont):
        """读取字体信息，包括各种名表"""
        for record in ttFont['name'].names:  # 遍历名表
            if record.nameID not in (self.FamilyNameID, self.SubfamilyNameID, self.FullNameID, self.PostscriptNameID):
                continue
            record_str = self.decodeNameRecord(record).lower()  # 全部使用小写匹配
            if not record_str:
                continue
            if record.nameID == self.FamilyNameID:
                self.familyNames.add(record_str)
            # elif record.nameID == self.SubfamilyNameID:  # Style Name
                # 不同系统下的英文ID
                # Unicode: platformID=0, langID=1033; Mac: platformID=1, langID=0; Win: platformID=3, langID=1033.
            elif record.nameID == self.FullNameID:
                self.fullNames.add(record_str)
            elif record.nameID == self.PostscriptNameID:
                self.postscriptName = record_str

        if "OS/2" in ttFont:
            os2 = ttFont["OS/2"]
            self.weight = os2.usWeightClass
            fs_selection = os2.fsSelection
            if fs_selection & 0x01:     # ITALIC flag
                self.style = 2  # Italic
            elif fs_selection & 0x200:  # OBLIQUE flag
                self.style = 1  # Oblique

    @property
    def isBold(self) -> bool:
        """是否粗体"""
        return self.weight == self.WEIGHT_BOLD

    @property
    def isItalic(self) -> bool:
        """是否斜体"""
        return self.style == self.STYLE_ITALIC or self.style == self.STYLE_OBLIQUE

    @classmethod
    def createFontsFromFile(cls, path: str) -> list[Self]:
        """从指定的字体文件内读取所有的字体并创建实例，读取错误的字体将被忽略"""
        font_collection: TTCollection | None = None
        fonts: list[cls] = []
        try:
            # 打开文件 -------
            if not os.path.isfile(path) or not os.access(path, os.R_OK):  # 检查路径
                return []
            if os.path.splitext(path)[1].lower().endswith('.ttc'):
                font_collection = TTCollection(path)
            else:
                font_collection = TTCollection()
                font_collection.fonts.append(TTFont(path))

            for i, ttf_font in enumerate(font_collection):  # type: int, TTFont
                font = cls(path, i, openNow=False)
                font._readInfo(ttf_font)
                fonts.append(font)
        except Exception:
            fonts = []
        finally:
            font_collection.close()  # 关闭文件

        return fonts

    @classmethod
    def createFontFromBytes(cls, file: io.BytesIO, path: str = '', index: int = 0) -> Self | None:
        """从指定的字节流读取字体数据并创建实例，读取错误则返回None"""
        try:
            font = cls(path, index, inMemory=True, openNow=False)
            font._byteStream = file  # 保存字节流，用于未来打开字体
            with TTFont(file) as ttf_font:
                font._readInfo(ttf_font)
            return font
        except Exception:
            return None

    @staticmethod
    def decodeNameRecord(record) -> str:
        """解码二进制表名记录"""
        return record.string.decode(record.getEncoding(), errors='ignore')

    def open(self) -> TTFont:
        """打开字体，返回TTFont"""
        if self.inMemory:
            self._byteStream.seek(0)
            return TTFont(self._byteStream)
        if not os.access(self.path, os.R_OK):
            raise Exception(Lang['Unable to read file {p}.'].format(p=self.path))
        if self.inTTC:
            return TTCollection(self.path, lazy=True)[self.index]   # lazy模式，只打开访问过的TTFont
        else:  # ttf、otf
            return TTFont(self.path)

    def read(self, size: int = None) -> bytes:
        """以二进制方式读取字体数据"""
        if self._byteStream:    # 内存字体，返回内存数据
            self._byteStream.seek(0)
            return self._byteStream.read(size)
        elif self.inTTC:    # 来自TTC文件，从里面提取TTF
            with self.open() as ttf_font:
                buffer = io.BytesIO()
                ttf_font.save(buffer)
                return buffer.getvalue()
        else:   # 来自TTF文件，直接读源文件数据
            with open(self.path, 'rb') as file:
                return file.read()

    def subset(self, text: str, reserveNames: list[str] = None, **kwargs):
        """
        字体子集化
        :param text: 子集字符集合
        :param reserveNames: 名表中需要保留的引用名字
        :param kwargs: Subsetter子集化参数
        """
        name_ids = [self.PostscriptNameID, self.FullNameID, self.FamilyNameID]  # 查找名字的类型范围和顺序
        with self.open() as ttf_font:
            if reserveNames:
                # 找出与需要保留的字体名称，子集化可能会把它删掉，导致无法匹配
                name_list = ttf_font['name'].names  # 字体名表
                name_records = []  # 保留名称记录
                for name in reserveNames:
                    for name_id in name_ids:
                        name_record = next((record for record in name_list if record.nameID == name_id
                                            and self.decodeNameRecord(record).lower() == name), None)
                        if name_record: # 把相同的名字记录保存下来
                            name_records.append(name_record)

            # 子集化 ---------
            if 'ignore_missing_glyphs' not in kwargs:
                kwargs['ignore_missing_glyphs'] = True  # 忽略缺失字形错误
            subsetter = Subsetter(options=Options(**kwargs))
            subsetter.populate(text=text)
            subsetter.subset(ttf_font)

            if reserveNames:
                # 检查名表，如果需要保留的字体名称被删掉了，将它加回来
                name_list = ttf_font['name'].names
                for name_record in name_records:
                    for record in name_list:
                        if (record.nameID == name_record.nameID and record.platformID == name_record.platformID
                                and record.langID == name_record.langID and record.string == name_record.string):
                            break  # 如果名字没删掉，那就不用加了
                    else:  # 如果名字删掉了，加回来
                        name_list.append(name_record)

            out_stream = io.BytesIO()
            ttf_font.save(out_stream)  # 保存到内存字节流

        if self._byteStream:
            self._byteStream.close()
        self._byteStream = out_stream
        self.inMemory = True  # 子集化后字体自动变内存字体

    def save(self, path: str):
        """保存字体到路径"""
        if not os.access(os.path.dirname(path), os.W_OK):
            raise Exception(Lang['Unable to write file {p}.'].format(p=path))
        if self.inMemory:
            self._byteStream.seek(0)
            with open(path, 'wb') as file:
                file.write(self._byteStream.read())
        else:
            with self.open() as ttf_font:
                ttf_font.save(path)

    def __del__(self):
        """析构函数，关闭流"""
        if self._byteStream:
            self._byteStream.close()
