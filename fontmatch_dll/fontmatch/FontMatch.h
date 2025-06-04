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
    virtual const std::wstring GetMatchingFont(std::unordered_map<FONT_PROPERTY, std::wstring>& propDict);

protected:
    // 系统字体集
    Microsoft::WRL::ComPtr<IDWriteFontCollection> systemFontCollection;
    // 缓存 map<Postscript名: 字体对象>
    std::unordered_map<std::wstring, Microsoft::WRL::ComPtr<IDWriteFont>> postScriptDict;
    // 缓存 map<全名: set<字体对象>>
    std::unordered_map<std::wstring, std::set<Microsoft::WRL::ComPtr<IDWriteFont>>> fullNameDict;

    // 获取字体文件
    static Microsoft::WRL::ComPtr<IDWriteFontFile> GetFontFile(Microsoft::WRL::ComPtr<IDWriteFont> font);

    // 从字体中取出各个名字
    static std::vector<std::wstring> GetFontNames(Microsoft::WRL::ComPtr<IDWriteFont> font, DWRITE_INFORMATIONAL_STRING_ID stringId);

    // 字体的指定名字类型中是否包含指定的名字
    static bool FontHasName(Microsoft::WRL::ComPtr<IDWriteFont> font, DWRITE_INFORMATIONAL_STRING_ID stringId, std::wstring& name);

    // 获取文件路径
    static std::wstring GetFontPath(Microsoft::WRL::ComPtr<IDWriteFontFile> file);

    // 从FONT_PROPERTY中获取字重
    static DWRITE_FONT_WEIGHT GetWeightFromFontProperty(std::unordered_map<FONT_PROPERTY, std::wstring>& propDict);

    // 从FONT_PROPERTY中获取风格（斜体）
    static DWRITE_FONT_STYLE GetStyleFromFontProperty(std::unordered_map<FONT_PROPERTY, std::wstring>& propDict);

    // 从map中尝试获取值，如果key存在，则值写入到value，并返回true，如果key不存在，则不修改value，并返回false。
    template<typename MAP, typename T1, typename T2>
    static bool TryGetFromMap(MAP& _map, T1& key, T2*& value);
};
