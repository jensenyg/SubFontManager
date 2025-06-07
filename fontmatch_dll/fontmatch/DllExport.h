#pragma once
#include "FontProperty.h"
#include <dwrite_3.h>   // DirectWrite3 API

/**
 * DLL的所有导出接口
 */
extern "C"
{   // 注意const变量必须加extern才能导出，否则会被编译器优化掉
    // 字体检索的属性名常量 -------
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_POSTSCRIPT_NAME = (int)FONT_PROPERTY::POSTSCRIPT_NAME;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_FULL_NAME =       (int)FONT_PROPERTY::FULL_NAME;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_FAMILY_NAME =     (int)FONT_PROPERTY::FAMILY_NAME;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_SUBFAMILY_NAME =  (int)FONT_PROPERTY::SUBFAMILY_NAME;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_WEIGHT =          (int)FONT_PROPERTY::WEIGHT;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_STYLE =           (int)FONT_PROPERTY::STYLE;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_STRETCH =         (int)FONT_PROPERTY::STRETCH;

    // 字重的可选数值（也可以使用其他数值，只要在0~999之间） -------
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_THIN =        (int)DWRITE_FONT_WEIGHT_THIN;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_EXTRA_LIGHT = (int)DWRITE_FONT_WEIGHT_EXTRA_LIGHT;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_ULTRA_LIGHT = (int)DWRITE_FONT_WEIGHT_ULTRA_LIGHT;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_LIGHT =       (int)DWRITE_FONT_WEIGHT_LIGHT;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_SEMI_LIGHT =  (int)DWRITE_FONT_WEIGHT_SEMI_LIGHT;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_NORMAL =      (int)DWRITE_FONT_WEIGHT_NORMAL;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_REGULAR =     (int)DWRITE_FONT_WEIGHT_REGULAR;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_MEDIUM =      (int)DWRITE_FONT_WEIGHT_MEDIUM;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_DEMI_BOLD =   (int)DWRITE_FONT_WEIGHT_DEMI_BOLD;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_SEMI_BOLD =   (int)DWRITE_FONT_WEIGHT_SEMI_BOLD;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_BOLD =        (int)DWRITE_FONT_WEIGHT_BOLD;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_EXTRA_BOLD =  (int)DWRITE_FONT_WEIGHT_EXTRA_BOLD;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_ULTRA_BOLD =  (int)DWRITE_FONT_WEIGHT_ULTRA_BOLD;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_BLACK =       (int)DWRITE_FONT_WEIGHT_BLACK;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_HEAVY =       (int)DWRITE_FONT_WEIGHT_HEAVY;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_EXTRA_BLACK = (int)DWRITE_FONT_WEIGHT_EXTRA_BLACK;
    __declspec(dllexport) extern const int FONT_PROPERTY_WEIGHT_ULTRA_BLACK = (int)DWRITE_FONT_WEIGHT_ULTRA_BLACK;

    // 字体风格的枚举值 -------
    __declspec(dllexport) extern const int FONT_PROPERTY_STYLE_NORMAL =  (int)DWRITE_FONT_STYLE_NORMAL;
    __declspec(dllexport) extern const int FONT_PROPERTY_STYLE_OBLIQUE = (int)DWRITE_FONT_STYLE_OBLIQUE;
    __declspec(dllexport) extern const int FONT_PROPERTY_STYLE_ITALIC =  (int)DWRITE_FONT_STYLE_ITALIC;

    // 字重拉伸的枚举值 -------
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_UNDEFINED =       (int)DWRITE_FONT_STRETCH_UNDEFINED;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_ULTRA_CONDENSED = (int)DWRITE_FONT_STRETCH_ULTRA_CONDENSED;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_EXTRA_CONDENSED = (int)DWRITE_FONT_STRETCH_EXTRA_CONDENSED;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_CONDENSED =       (int)DWRITE_FONT_STRETCH_CONDENSED;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_SEMI_CONDENSED =  (int)DWRITE_FONT_STRETCH_SEMI_CONDENSED;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_NORMAL =          (int)DWRITE_FONT_STRETCH_NORMAL;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_MEDIUM =          (int)DWRITE_FONT_STRETCH_MEDIUM;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_SEMI_EXPANDED =   (int)DWRITE_FONT_STRETCH_SEMI_EXPANDED;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_EXPANDED =        (int)DWRITE_FONT_STRETCH_EXPANDED;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_EXTRA_EXPANDED =  (int)DWRITE_FONT_STRETCH_EXTRA_EXPANDED;
    __declspec(dllexport) extern const int FONT_PROPERTY_STRETCH_ULTRA_EXPANDED =  (int)DWRITE_FONT_STRETCH_ULTRA_EXPANDED;

    /**
     * 初始化DLL环境
     * @param version 使用的DirectWrite版本，可以为1(Win7)或3(Win10 1607+)，缺省则自动判断。
     * @return 成功则返回true，失败（系统不支持）则返回false。
     */
    __declspec(dllexport) bool Init(const int version = 0);

    /**
     * 按照搜索条件匹配合适的字体
     * @param json_str JSON字符串，包含字体搜索条件，其中名字均为严格匹配，字重、风格和拉伸可以使用模糊匹配。
     *  FONT_PROPERTY_ID_POSTSCRIPT_NAME：Postscrit名字；
     *  FONT_PROPERTY_ID_FULL_NAME：全名；
     *  FONT_PROPERTY_ID_FAMILY_NAME：家族名；
     *  FONT_PROPERTY_ID_SUBFAMILY_NAME：子族名（"Bold"、"斜体"等）；
     *  FONT_PROPERTY_ID_WEIGHT：字重，字符串表示的数值，如"700"(粗体)；
     *  FONT_PROPERTY_ID_STYLE：字体风格，字符串表示的数值，如"2"(斜体)；
     *  FONT_PROPERTY_ID_STRETCH：字体拉伸，字符串表示的数值，如"5"(正常)。
     * @param strict 严格模式，true则字重、风格和拉伸严格匹配，false则模糊匹配。
     * @return 匹配字体的路径字串，找不到则返回nullptr，返回的指针无需释放。
     */
    __declspec(dllexport) const char* GetMatchingFont(const char* json_str, bool strict = false);
}
