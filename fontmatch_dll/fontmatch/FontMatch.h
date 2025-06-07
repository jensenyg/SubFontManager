#pragma once
#include <unordered_map>
#include <set>
#include <string>
#include <wrl/client.h> // ComPtr智能指针
#include <dwrite_3.h>   // DirectWrite3 API
#include "FontProperty.h"

/**
 * 基于DirectWrite1的字体匹配类，支持Windows7系统
 */
class FontMatch
{
public:
    // DirectWrite1工厂
    static Microsoft::WRL::ComPtr<IDWriteFactory> factory;

    // 系统是否支持本类型工作
    static bool IsSupported();

    // 初始化
    virtual bool Init();

    // 匹配字体
    virtual const std::wstring GetMatchingFont(std::unordered_map<FONT_PROPERTY, std::wstring>& propDict, bool strict = false);

protected:
    // 系统字体集
    Microsoft::WRL::ComPtr<IDWriteFontCollection> systemFontCollection;
    // 缓存 map<Postscript名: 字体对象>
    std::unordered_map<std::wstring, Microsoft::WRL::ComPtr<IDWriteFont>> postScriptDict;
    // 缓存 map<全名: set<字体对象>>
    std::unordered_map<std::wstring, std::set<Microsoft::WRL::ComPtr<IDWriteFont>>> fullNameDict;

    /**
     * 给字体的匹配程度打分。评分体系基于以下原则：
     * 字重>风格>拉伸；
     * 两项准确匹配>一项准确匹配；
     * 两项替补匹配>一项替补匹配（Normal）；
     * 一项准确匹配>三项替补匹配。
     * @param font 字体指针
     * @param weight 字重
     * @param weightIsDefault 字重是否是缺省值
     * @param style 风格
     * @param styleIsDefault 风格是否是缺省值
     * @param stretch 拉伸
     * @param stretchIsDefault 拉伸是否是缺省值
     * @return 分值
     */
    template<typename T>
    static int CalculateMatchingScore(T font,
        DWRITE_FONT_WEIGHT weight, bool weightIsDefault,
        DWRITE_FONT_STYLE style, bool styleIsDefault,
        DWRITE_FONT_STRETCH stretch, bool stretchIsDefault)
    {
        int score = 0;
        if (font->GetWeight() == weight)
            score += weightIsDefault ? 4 : 12;
        if (font->GetStyle() == style)
            score += styleIsDefault ? 3 : 11;
        if (font->GetStretch() == stretch)
            score += stretchIsDefault ? 2 : 10;
        return score;
    }
};
