#pragma once
#include "FontMatch.h"

/**
 * 基于DirectWrite3的字体匹配类，仅在Windows10 1607后被支持，该类不需要缓存Postscript名和全名的字体索引
 */
class FontMatch3 : public FontMatch
{
public:
    // DirectWrite3工厂
    static Microsoft::WRL::ComPtr<IDWriteFactory3> factory3;

    // 系统是否支持本类型工作
    static bool IsSupported();

    // 初始化
    bool Init() override;

    // 匹配字体
    const std::wstring GetMatchingFont(std::unordered_map<FONT_PROPERTY, std::wstring>& propDict) override;

protected:
    // 系统字体集
    Microsoft::WRL::ComPtr<IDWriteFontSet> systemFontSet;
};
