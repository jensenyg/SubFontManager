import ctypes
from ctypes import c_void_p, c_char_p, c_bool, c_long, c_int32, c_float
from ctypes.util import find_library


class MacFontMatch:
    """
    macOS下的字体匹配库，基于ctypes直接调用系统CoreText库的C API。
    这个类的目的是绕过臃肿的pyobjc，直接访问底层C接口实现了同样的功能。
    """

    # 加载CoreFoundation和CoreText
    _cf = ctypes.cdll.LoadLibrary(find_library("CoreFoundation"))
    _ct = ctypes.cdll.LoadLibrary(find_library("CoreText"))
    if _cf is None or _ct is None:
        raise Exception('CoreText initialization failed!')

    # 函数原型声明 -------
    # 用Python bytes创建CFStringRef的函数，返回值需要手动回收
    _cf.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_long]
    _cf.CFStringCreateWithCString.restype = c_void_p

    # 创建CF数值，返回值需要手动回收
    _cf.CFNumberCreate.argtypes = [c_void_p, ctypes.c_int32, c_void_p]
    _cf.CFNumberCreate.restype = c_void_p

    # 创建CF字典的函数，返回值需要手动回收
    _cf.CFDictionaryCreate.argtypes = [
        c_void_p,   # allocator
        ctypes.POINTER(c_void_p),   # keys
        ctypes.POINTER(c_void_p),   # values
        c_long,     # count
        c_void_p,   # key callbacks
        c_void_p    # value callbacks
    ]
    _cf.CFDictionaryCreate.restype = c_void_p

    # 从URL获取路径的函数
    _cf.CFURLGetFileSystemRepresentation.argtypes = [c_void_p, c_bool, c_char_p, c_long]
    _cf.CFURLGetFileSystemRepresentation.restype = c_bool

    # 从字体描述符创建属性对象的函数，它的返回值需要手动回收
    _ct.CTFontDescriptorCreateWithAttributes.argtypes = [c_void_p]
    _ct.CTFontDescriptorCreateWithAttributes.restype = c_void_p

    # 根据字体描述符匹配系统字体的函数，它的返回值需要手动回收
    _ct.CTFontDescriptorCreateMatchingFontDescriptor.argtypes = [c_void_p, c_void_p]
    _ct.CTFontDescriptorCreateMatchingFontDescriptor.restype = c_void_p

    # 从字体描述符拷贝出特定属性的函数，它的返回值需要手动回收
    _ct.CTFontDescriptorCopyAttribute.argtypes = [c_void_p, c_void_p]
    _ct.CTFontDescriptorCopyAttribute.restype = c_void_p

    # 回收资源的函数
    _ct.CFRelease.argtypes = [c_void_p]
    _ct.CFRelease.restype = None

    # 常量定义 -------
    kCTFontNameAttribute = "kCTFontNameAttribute"   # 字体名，可以匹配字体家族名、全名和Postscrip名
    kCTFontDisplayNameAttribute = "kCTFontDisplayNameAttribute" # 字体全名
    kCTFontFamilyNameAttribute = "kCTFontFamilyNameAttribute"   # 字体家族名
    kCTFontStyleNameAttribute = "kCTFontStyleNameAttribute"     # 字体样式名（子族名）
    kCTFontTraitsAttribute = "kCTFontTraitsAttribute"   # 字体特征，包括weight,italic,slant
    kCTFontWeightTrait = "kCTFontWeightTrait"       # 字重
    kCTFontSymbolicTrait = "kCTFontSymbolicTrait"   # 斜体，是否Italic
    _kCTFontURLAttribute = "kCTFontURLAttribute"     # 字体url，即字体路径

    kCTFontItalicTrait = 0x01   # CoreText Symbolic Trait Flags（斜体在bit 0位置）
    _kCFNumberFloatType = 2     # 浮点数类型
    _kCFNumberSInt32Type = 3    # int32类型
    _kCFStringEncodingUTF8 = 0x08000100 # 编码方式常量（macOS特有）

    @classmethod
    def _ctAttribute(cls, att: str):
        """获取系统CoreText中的常量指针，注意该返回值不能被哈希"""
        return c_void_p.in_dll(cls._ct, att)

    @classmethod
    def _cfRelease(cls, *args):
        """回收资源，可批量回收"""
        for arg in args:
            if arg is not None:
                cls._ct.CFRelease(arg)

    @classmethod
    def _createCFDictionary(cls, attrs: dict) -> tuple[object, list[object]]:
        """
        创建CF字典对象
        :param attrs: 筛选属性
        :return: (字典对象, [字典中包含的需要手动Release的对象])
        """
        keys = []
        values = []
        cf_garbage = [] # 需要手动Release的对象
        for key, val in attrs.items():
            keys.append(cls._ctAttribute(key))
            if isinstance(val, str):
                cf_val = cls._cf.CFStringCreateWithCString(None, val.encode('utf-8'), cls._kCFStringEncodingUTF8)
            elif isinstance(val, int):
                cf_val = cls._cf.CFNumberCreate(None, cls._kCFNumberSInt32Type, ctypes.byref(c_int32(val)))
            elif isinstance(val, float):
                cf_val = cls._cf.CFNumberCreate(None, cls._kCFNumberFloatType, ctypes.byref(c_float(val)))
            elif isinstance(val, dict):
                cf_val, cf_gbg = cls._createCFDictionary(val)
                cf_garbage.extend(cf_gbg)
            else:
                raise Exception('Unrecognized value type!')
            values.append(cf_val)
            cf_garbage.append(cf_val)

        count = len(attrs)
        array_type = c_void_p * count
        return (cls._cf.CFDictionaryCreate(None, array_type(*keys), array_type(*values), count, None, None),
                cf_garbage) # 同时返回cf_garbage以供Release

    @classmethod
    def matchFont(cls, attrs: dict[str, str]) -> str | None:
        """
        调用CoreText接口匹配字体
        :param attrs: 筛选属性
        :return: 匹配到的字体的路径
        """
        cf_dict, cf_garbage = cls._createCFDictionary(attrs) # 创建属性字典
        desc = cls._ct.CTFontDescriptorCreateWithAttributes(cf_dict)  # 创建字体描述符
        cls._cfRelease(cf_dict)    # 回收这个对desc没有影响，但此时回收cf_garbage不行

        path = None
        if desc:
            match_desc = cls._ct.CTFontDescriptorCreateMatchingFontDescriptor(desc, None)  # 匹配结果
            if match_desc:
                # 获取字体路径 ------
                BUFFER_LENGTH = 1024  # macOS最大路径长度
                buffer = ctypes.create_string_buffer(BUFFER_LENGTH)
                url_ref = cls._ct.CTFontDescriptorCopyAttribute(
                    match_desc, cls._ctAttribute(cls._kCTFontURLAttribute))
                success = cls._cf.CFURLGetFileSystemRepresentation(url_ref, True, buffer, BUFFER_LENGTH)
                cls._cfRelease(url_ref, match_desc)
                path = buffer.value.decode("utf-8") if success else None

        # desc中保有属性值的cfstring，不可在desc用完之前回收ct_attrs
        cls._cfRelease(desc, *cf_garbage)   # C变量必须手动回收
        return path

    @classmethod
    def getMatchingFontPath(cls, fontName: str = None, bold: bool = False, italic: bool = False) -> str | None:
        """
        根据条件匹配字体并返回字体的路径
        :param fontName: 字体名，将分别尝试使用Postscript名、全名和家族名来匹配它
        :param bold: 是否粗体
        :param italic: 是否斜体
        :return: 匹配到的字体的路径
        """
        attrs = {   # 字体筛选属性
            cls.kCTFontNameAttribute: fontName, # kCTFontNameAttribute，可以匹配Postscrip名、全名和家族名
            cls.kCTFontTraitsAttribute: {   # 字体特征
                cls.kCTFontWeightTrait: 0.4 if bold else 0.0,   # mac中weight取值-1~1，其中0为Regular，0.4~0.6为Bold
                cls.kCTFontSymbolicTrait: cls.kCTFontItalicTrait if italic else 0   # 是否斜体
            }
        }
        return cls.matchFont(attrs)
