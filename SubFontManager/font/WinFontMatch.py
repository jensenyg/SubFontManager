import ctypes
import json


class WinFontmatch:
    """基于自己实现的fontmatch.dll封装的Windows系统字体匹配库"""

    _dll = ctypes.cdll.LoadLibrary("./fontmatch.dll")   # 加载 DLL
    if _dll is None:
        raise Exception('"fontmatch.dll" load failed!')

    # Inin函数定义 ------
    _dll.Init.argtypes = []
    _dll.Init.restype = ctypes.c_bool

    # GetMatchingFont函数定义 ------
    _dll.GetMatchingFont.argtypes = [ctypes.c_char_p, ctypes.c_bool]
    _dll.GetMatchingFont.restype = ctypes.c_char_p

    if not _dll.Init():
        raise Exception('"fontmatch.dll" initialization failed!')

    @staticmethod
    def _GetDllValue(dll, valName: str) -> int:
        return ctypes.c_int.in_dll(dll, valName).value

    # 字体匹配属性名 ------
    FONT_PROPERTY_ID_POSTSCRIPT_NAME: int = _GetDllValue(_dll, "FONT_PROPERTY_ID_POSTSCRIPT_NAME")
    FONT_PROPERTY_ID_FULL_NAME: int = _GetDllValue(_dll, "FONT_PROPERTY_ID_FULL_NAME")
    FONT_PROPERTY_ID_FAMILY_NAME: int = _GetDllValue(_dll, "FONT_PROPERTY_ID_FAMILY_NAME")
    FONT_PROPERTY_ID_SUBFAMILY_NAME: int = _GetDllValue(_dll, "FONT_PROPERTY_ID_SUBFAMILY_NAME")
    FONT_PROPERTY_ID_WEIGHT: int = _GetDllValue(_dll, "FONT_PROPERTY_ID_WEIGHT")
    FONT_PROPERTY_ID_STYLE: int = _GetDllValue(_dll, "FONT_PROPERTY_ID_STYLE")

    # 字重匹配预设 ------
    FONT_PROPERTY_WEIGHT_NORMAL: int = _GetDllValue(_dll, "FONT_PROPERTY_WEIGHT_NORMAL")
    FONT_PROPERTY_WEIGHT_BOLD: int = _GetDllValue(_dll, "FONT_PROPERTY_WEIGHT_BOLD")

    # 样式匹配枚举 ------
    FONT_PROPERTY_STYLE_NORMAL: int = _GetDllValue(_dll, "FONT_PROPERTY_STYLE_NORMAL")
    # FONT_PROPERTY_STYLE_OBLIQUE: int = cls._GetDllValue("FONT_PROPERTY_STYLE_OBLIQUE")
    FONT_PROPERTY_STYLE_ITALIC: int = _GetDllValue(_dll, "FONT_PROPERTY_STYLE_ITALIC")

    # 属性名匹配的优先级顺序 ------
    PROPERTY_MATCHING_ORDER = [
        FONT_PROPERTY_ID_POSTSCRIPT_NAME,
        FONT_PROPERTY_ID_FULL_NAME,
        FONT_PROPERTY_ID_FAMILY_NAME
    ]

    @classmethod
    def matchFont(cls, attrs: dict[int, str], strict: bool = False) -> str | None:
        """
        调用DLL匹配字体
        :param attrs: 筛选属性
        :param strict: 严格模式
        :return: 匹配到的字体的路径
        """
        json_str = json.dumps(attrs).encode('utf-8')    # 序列化为JSON字符串并按UTF8编码
        raw_str = cls._dll.GetMatchingFont(json_str, strict)    # 调用 DLL 函数
        return raw_str.decode("utf-8") if raw_str else None

    @classmethod
    def _matchAnyName(cls, fontName: str, otherProps: dict[int, int | str], strict: bool = True) -> str | None:
        """
        使用任意名字属性匹配字体
        :param fontName: 字体名，将分别尝试使用Postscript名、全名和家族名来匹配它
        :param otherProps: 其他筛选属性
        :param strict: 严格模式
        :return: 匹配到的字体的路径
        """
        for prop_name in cls.PROPERTY_MATCHING_ORDER:
            otherProps[prop_name] = fontName
            path = cls.matchFont(otherProps, strict)  # 查找匹配字体
            otherProps.pop(prop_name)
            if path:
                return path
        return None

    @classmethod
    def getMatchingFontPath(cls, fontName: str = None, bold: bool = False, italic: bool = False) -> str | None:
        """
        根据条件匹配字体并返回字体的路径
        :param fontName: 字体名，将分别尝试使用Postscript名、全名和家族名来匹配它
        :param bold: 是否粗体
        :param italic: 是否斜体
        :return: 匹配到的字体的路径
        """
        weight = cls.FONT_PROPERTY_WEIGHT_BOLD if bold else cls.FONT_PROPERTY_WEIGHT_NORMAL
        style = cls.FONT_PROPERTY_STYLE_ITALIC if italic else cls.FONT_PROPERTY_STYLE_NORMAL

        font_props = {   # 用于筛选的字体描述字典
            cls.FONT_PROPERTY_ID_WEIGHT: weight,
            cls.FONT_PROPERTY_ID_STYLE: style
        }
        path = cls._matchAnyName(fontName, font_props)
        if not path:
            path = cls._matchAnyName(fontName, { cls.FONT_PROPERTY_ID_WEIGHT: weight })
        if not path:
            path = cls._matchAnyName(fontName, { cls.FONT_PROPERTY_ID_STYLE: style })
        if not path:
            path = cls._matchAnyName(fontName, font_props, strict=False)

        return path
