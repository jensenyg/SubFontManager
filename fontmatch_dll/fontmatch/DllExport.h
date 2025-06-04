#pragma once
#include "FontProperty.h"
#include <dwrite_3.h>   // DirectWrite3 API

/**
 * DLL的所有导出接口
 */
extern "C"
{
    // 字体检索的属性名常量，注意const变量必须加extern才能导出，否则会被编译器优化掉 -------
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_POSTSCRIPT_NAME = (int)FONT_PROPERTY::POSTSCRIPT_NAME;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_FULL_NAME =       (int)FONT_PROPERTY::FULL_NAME;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_FAMILY_NAME =     (int)FONT_PROPERTY::FAMILY_NAME;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_SUBFAMILY_NAME =  (int)FONT_PROPERTY::SUBFAMILY_NAME;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_WEIGHT =          (int)FONT_PROPERTY::WEIGHT;
    __declspec(dllexport) extern const int FONT_PROPERTY_ID_STYLE =           (int)FONT_PROPERTY::STYLE;

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

    /**
     * 初始化DLL环境
     * @return 成功则返回true，失败（系统不支持）则返回false
     */
    __declspec(dllexport) bool Init();

    /**
     * 按照搜索条件匹配合适的字体
     * @param json_str JSON字符串，包含字体搜索条件。
     *  FONT_PROPERTY_POSTSCRIPT_NAME：Postscrit名字；
     *  FONT_PROPERTY_FULL_NAME：全名；
     *  FONT_PROPERTY_FAMILY_NAME：家族名；
     *  FONT_PROPERTY_WEIGHT：字重，字符串表示的数值，如"700"(粗体)，当字体家族重找不到准确匹配的字重时，会选择最接近的一个；
     *  FONT_PROPERTY_STYLE：字体风格，"0"代表Normal，"1"代表Oblique(倾斜)，"2"代表Italic(斜体)。
     * @return 匹配字体的路径字串，找不到则返回nullptr，注意返回的路径字串需要用ReleaseArray()释放
     */
    __declspec(dllexport) const char* GetMatchingFont(const char* json_str);
}
