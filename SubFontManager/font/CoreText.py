import ctypes
from ctypes import c_void_p, c_char_p, c_bool, c_long
from ctypes.util import find_library


class CoreText:
    """
    基于ctypes直接调用系统C API，模拟Mac自带的CoreText库的部分接口，但不完全一样。
    这个类的目的是绕过臃肿的pyobjc，直接访问底层C接口实现了同样的功能。
    """

    # 加载CoreFoundation和CoreText
    _CF = ctypes.cdll.LoadLibrary(find_library("CoreFoundation"))
    _CT = ctypes.cdll.LoadLibrary(find_library("CoreText"))

    # 函数原型声明 -------
    # 用Python bytes创建CFStringRef的函数，它的返回值需要手动回收
    _CF.CFStringCreateWithCString.restype = c_void_p
    _CF.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_long]

    # 创建CF字典的函数，它的返回值需要手动回收
    _CF.CFDictionaryCreate.restype = c_void_p
    _CF.CFDictionaryCreate.argtypes = [
        c_void_p,   # allocator
        ctypes.POINTER(c_void_p),   # keys
        ctypes.POINTER(c_void_p),   # values
        c_long,     # count
        c_void_p,   # key callbacks
        c_void_p    # value callbacks
    ]

    # 从URL获取路径的函数
    _CF.CFURLGetFileSystemRepresentation.restype = c_bool
    _CF.CFURLGetFileSystemRepresentation.argtypes = [c_void_p, c_bool, c_char_p, c_long]

    # 从字体描述符创建属性对象的函数，它的返回值需要手动回收
    _CT.CTFontDescriptorCreateWithAttributes.restype = c_void_p
    _CT.CTFontDescriptorCreateWithAttributes.argtypes = [c_void_p]

    # 根据字体描述符匹配系统字体的函数，它的返回值需要手动回收
    _CT.CTFontDescriptorCreateMatchingFontDescriptor.restype = c_void_p
    _CT.CTFontDescriptorCreateMatchingFontDescriptor.argtypes = [c_void_p, c_void_p]

    # 从字体描述符拷贝出特定属性的函数，它的返回值需要手动回收
    _CT.CTFontDescriptorCopyAttribute.restype = c_void_p
    _CT.CTFontDescriptorCopyAttribute.argtypes = [c_void_p, c_void_p]

    # 回收资源的函数
    _CT.CFRelease.argtypes = [c_void_p]
    _CT.CFRelease.restype = None

    # 常量定义 -------
    kCTFontNameAttribute = "kCTFontNameAttribute"   # 字体名，可以匹配字体家族名、全名和Postscrip名
    kCTFontDisplayNameAttribute = "kCTFontDisplayNameAttribute"  # 字体全名
    kCTFontFamilyNameAttribute = "kCTFontFamilyNameAttribute"    # 字体家族名
    kCTFontStyleNameAttribute = "kCTFontStyleNameAttribute"      # 字体
    kCTFontURLAttribute = "kCTFontURLAttribute"     # 字体url，即字体路径

    kCFStringEncodingUTF8 = 0x08000100  # 编码方式常量（macOS特有）

    @classmethod
    def _GetCTAttribute(cls, att: str):
        """获取系统CoreText中的常量指针，注意该返回值不能被哈希"""
        return c_void_p.in_dll(cls._CT, att)

    @classmethod
    def CFString(cls, s: str) -> c_void_p:
        """用Python bytes创建CFStringRef"""
        return cls._CF.CFStringCreateWithCString(None, s.encode('utf-8'), cls.kCFStringEncodingUTF8)

    @classmethod
    def CFRelease(cls, *args):
        """回收资源，可批量回收"""
        for arg in args:
            if arg is not None:
                cls._CT.CFRelease(arg)

    @classmethod
    def CTFontDescriptorCreateWithAttributes(cls, attrs: dict):
        """按照属性值创建字体描述符，它的返回值需要手动回收"""
        keys = (c_void_p * len(attrs))(*list(cls._GetCTAttribute(key) for key in attrs.keys()))
        vals = (c_void_p * len(attrs))(*list(attrs.values()))
        attr_dict = cls._CF.CFDictionaryCreate(None, keys, vals, len(attrs), None, None)
        desc = cls._CT.CTFontDescriptorCreateWithAttributes(attr_dict)  # 创建字体描述符
        cls.CFRelease(attr_dict)    # 回收这个对desc没有影响，但此时回收vals不行
        return desc

    @classmethod
    def CTFontDescriptorCreateMatchingFontDescriptor(cls, desc, arg):
        """按字体描述符从系统中匹配合适的字体，它的返回值需要手动回收"""
        return cls._CT.CTFontDescriptorCreateMatchingFontDescriptor(desc, arg)

    @classmethod
    def CTFontDescriptorGetPath(cls, desc) -> str:
        """从字体描述符中读取即字体路径"""
        BUFFER_LENGTH = 512
        buffer = ctypes.create_string_buffer(BUFFER_LENGTH)
        res = cls._CT.CTFontDescriptorCopyAttribute(desc, cls._GetCTAttribute(cls.kCTFontURLAttribute))
        success = cls._CF.CFURLGetFileSystemRepresentation(res, True, buffer, BUFFER_LENGTH)
        if success:
            cls.CFRelease(res)
            return buffer.value.decode("utf-8")
        else:
            raise Exception('Get attribute failed.')

    @classmethod
    def GetMatchingFontPath(cls, attrs: dict[str, str]) -> str | None:
        ct_attrs = {key: cls.CFString(val) for key, val in attrs.items()}
        desc = CoreText.CTFontDescriptorCreateWithAttributes(ct_attrs)
        match_desc = CoreText.CTFontDescriptorCreateMatchingFontDescriptor(desc, None)  # 匹配结果
        path = None if match_desc is None else cls.CTFontDescriptorGetPath(match_desc)
        # desc中保有属性值的cfstring，不可在desc用完之前回收ct_attrs
        cls.CFRelease(match_desc, desc, *list(ct_attrs.values()))   # C变量必须手动回收
        return path

        # 苹果CoreText中读取其他字体信息的代码，在ctypes方法中无效 ------
        # postscriptName = str(CoreText.CTFontDescriptorCopyAttribute(match_desc, CoreText.kCTFontNameAttribute)),
        # fullName = str(CoreText.CTFontDescriptorCopyAttribute(match_desc, CoreText.kCTFontDisplayNameAttribute)),
        # familyName = str(CoreText.CTFontDescriptorCopyAttribute(match_desc, CoreText.kCTFontFamilyNameAttribute)),
        # styleName = str(CoreText.CTFontDescriptorCopyAttribute(match_desc, CoreText.kCTFontStyleNameAttribute)),
        # path = str(CoreText.CTFontDescriptorCopyAttribute(match_desc, CoreText.kCTFontURLAttribute).path())
