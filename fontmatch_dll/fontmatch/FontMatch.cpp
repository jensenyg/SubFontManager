#include "pch.h"
#include <vector>
#include "FontMatch.h"
#include "utils.h"

#pragma comment(lib, "dwrite.lib")
#pragma comment(lib, "shlwapi.lib")

using Microsoft::WRL::ComPtr;
using namespace std;

// FONT_PROPERTY和DWRITE_INFORMATIONAL_STRING_ID之间的映射表
static unordered_map<FONT_PROPERTY, DWRITE_INFORMATIONAL_STRING_ID> FONT_PROPERTY_TO_STRING_ID = {
    { FONT_PROPERTY::POSTSCRIPT_NAME, DWRITE_INFORMATIONAL_STRING_POSTSCRIPT_NAME },
    { FONT_PROPERTY::FULL_NAME, DWRITE_INFORMATIONAL_STRING_FULL_NAME },
    { FONT_PROPERTY::FAMILY_NAME, DWRITE_INFORMATIONAL_STRING_WIN32_FAMILY_NAMES },
    { FONT_PROPERTY::WEIGHT, DWRITE_INFORMATIONAL_STRING_NONE },
    { FONT_PROPERTY::STYLE, DWRITE_INFORMATIONAL_STRING_NONE },
};


Microsoft::WRL::ComPtr<IDWriteFactory> FontMatch::factory = nullptr;    // 静态变量初始化

bool FontMatch::IsSupported()
{   // 尝试创建DW1工厂
    return factory || SUCCEEDED(DWriteCreateFactory(DWRITE_FACTORY_TYPE_SHARED, __uuidof(IDWriteFactory), &factory));
}

bool FontMatch::Init()
{   // 创建系统字体信息缓存
    if (FAILED(factory->GetSystemFontCollection(&this->systemFontCollection)))  // 获取系统字体集
        return false;

    for (UINT32 i = 0; i < this->systemFontCollection->GetFontFamilyCount(); ++i) { // 遍历每个字体家族
        ComPtr<IDWriteFontFamily> family;
        if (FAILED(this->systemFontCollection->GetFontFamily(i, &family)))    // 获取字体家族对象
            continue;
        
        // 构建字体Postscript名和全名到字体对象的缓存字典 -------
        for (UINT32 j = 0; j < family->GetFontCount(); ++j) {   // 遍历家族内的每个字体
            ComPtr<IDWriteFont> font;
            if (FAILED(family->GetFont(j, &font)))   // 获取字体对象
                continue;

            // 写入postScriptDict缓存字典 -------
            for (auto& name : GetFontNames(font, FONT_PROPERTY_TO_STRING_ID[FONT_PROPERTY::POSTSCRIPT_NAME]))
                this->postScriptDict.emplace(name, font);   // 将名字和字体对象都添加到缓存字典

            // 写入fullNameDict缓存字典 -------
            for (auto& name : GetFontNames(font, FONT_PROPERTY_TO_STRING_ID[FONT_PROPERTY::FULL_NAME])) {
                auto p_fonts = GetFromMap(this->fullNameDict, name);    // 同名字体集合，为合并重复，使用set
                if (p_fonts) {
                    auto p = GetFontPath(GetFontFile(font));
                    p_fonts->emplace(font);
                }
                else  // 创建新set并插入新元素
                    this->fullNameDict.emplace(name, set<ComPtr<IDWriteFont>>{})
                        .first->second.emplace(font);
            }
        }
    }

    return true;
}

const wstring FontMatch::GetMatchingFont(const unordered_map<FONT_PROPERTY, wstring>& propDict, bool strict) const
{
    // Postscript名匹配 -------
    auto p_ps_name = GetFromMap(propDict, FONT_PROPERTY::POSTSCRIPT_NAME);
    auto p_psname_font = p_ps_name ? GetFromMap(this->postScriptDict, *p_ps_name) : nullptr;
    if (p_ps_name && !p_psname_font)
        return wstring();   // 系统中不存在，匹配失败

    // 全名匹配 -------
    auto p_full_name = GetFromMap(propDict, FONT_PROPERTY::FULL_NAME);
    auto p_fullname_fonts = p_full_name ? GetFromMap(this->fullNameDict, *p_full_name) : nullptr;
    if (p_fullname_fonts && !p_full_name)
        return wstring();   // 系统中不存在，匹配失败

    // 合并p_psname_font和p_fullname_fonts -------
    set<ComPtr<IDWriteFont>> matching_fonts;    // 合并后PS名和全名的联合筛选结果，通常最多就一个了
    if (p_psname_font) {
        if (p_fullname_fonts && p_fullname_fonts->find(*p_psname_font) == p_fullname_fonts->end())
            return wstring();
        matching_fonts.emplace(*p_psname_font);
    }
    else if (p_fullname_fonts)
        matching_fonts = move(*p_fullname_fonts);

    // 从matching_fonts中筛选子族 -------
    auto p_subfamily_name = GetFromMap(propDict, FONT_PROPERTY::SUBFAMILY_NAME);    // 子族名（"Bold", "Italic"等）
    if (p_subfamily_name && !matching_fonts.empty()) {
        set<ComPtr<IDWriteFont>> matching_fonts2;
        for (auto& font : matching_fonts) { // 遍历每个字体，检查是否包含指定的子族名
            if (FontHasName(font, DWRITE_INFORMATIONAL_STRING_WIN32_SUBFAMILY_NAMES, *p_subfamily_name))
                matching_fonts2.emplace(font);
        }
        if (matching_fonts2.empty())    // 没有找到子族名，匹配失败
            return wstring();
        matching_fonts = move(matching_fonts2);
    }

    // 家族名匹配 -------
    ComPtr<IDWriteFontFamily> matched_family = nullptr;   // 目标家族
    auto p_family_name = GetFromMap(propDict, FONT_PROPERTY::FAMILY_NAME);
    if (p_family_name) { // 查询属性中包含家族名
        BOOL exists = FALSE;
        UINT32 family_index;    // 家族在系统家族表中的序号
        if (FAILED(this->systemFontCollection->FindFamilyName(p_family_name->c_str(), &family_index, &exists)) || !exists
            || FAILED(this->systemFontCollection->GetFontFamily(family_index, &matched_family))) // 系统中找到该家族名并获取家族对象
            return wstring();   // 系统中不存在家族名，那匹配失败
    }

    // 合并matched_family和matching_fonts -------
    if (matched_family && !matching_fonts.empty()) {
        // 构建matching_font的FontFace集合，因为只有FontFace之间的比较才能正确判断字体是否相等
        set<ComPtr<IDWriteFontFace>> matching_font_faces;
        for (auto& font : matching_fonts) {
            ComPtr<IDWriteFontFace> face;
            font->CreateFontFace(&face);    // 构建FontFace
            matching_font_faces.emplace(face);
        }
        // 遍历家族中的每个字体，检查是否有和matching_font重合的
        ComPtr<IDWriteFont> font;
        for (UINT32 i = 0; i < matched_family->GetFontCount(); i++) {
            ComPtr<IDWriteFontFace> family_font_face;
            if (SUCCEEDED(matched_family->GetFont(i, &font)) // 获取字体对象
                && SUCCEEDED(font->CreateFontFace(&family_font_face))    // 构造FontFace
                && matching_font_faces.find(family_font_face) != matching_font_faces.end()) // 在集合中查找家族字体
            {   // 绝大多数情况下，一个家族内不会出现重复的PS名和全名，所以匹配到第一个就成功
                matching_fonts.clear();
                matching_fonts.emplace(font);
                break;  // 有家族筛选和PS名/全名筛选时，同样忽略weight和style筛选，因为它们是模糊筛选
            }
        }
    }

    // 三种字体样式信息 -------
    bool weight_exists, style_exists, stretch_exists;
    auto font_weight = GetEnumFromMap(propDict, FONT_PROPERTY::WEIGHT, DWRITE_FONT_WEIGHT_REGULAR, &weight_exists); // 字重
    auto font_style = GetEnumFromMap(propDict, FONT_PROPERTY::STYLE, DWRITE_FONT_STYLE_NORMAL, &style_exists); // 风格（斜体）
    auto font_stretch = GetEnumFromMap(propDict, FONT_PROPERTY::STRETCH, DWRITE_FONT_STRETCH_NORMAL, &stretch_exists); // 拉伸

    // 进行字重风格和子族的筛选，并选出一个匹配的字体 -------
    ComPtr<IDWriteFont> matched_font = nullptr; // 最终匹配上的字体
    if (strict) {   // 严格模式
        if (matched_family && matching_fonts.empty()) { // 仅有家族筛选
            // 如果还需要进行其他筛选，则需要将家族转换为集合
            if (weight_exists || style_exists || p_subfamily_name) {
                ComPtr<IDWriteFont> font;
                for (UINT32 i = 0; i < matched_family->GetFontCount(); i++)
                    if (SUCCEEDED(matched_family->GetFont(i, &font)))   // 获取字体对象
                        matching_fonts.emplace(font);
            }
            // 如果没有其他筛选了，则重新使用模糊匹配的方式匹配一个最普通的
            else if (FAILED(matched_family->GetFirstMatchingFont(font_weight, font_stretch, font_style, &matched_font)))
                matched_family->GetFont(0, &matched_font);  // 要是家族内模糊匹配也匹配不到，这种概率不大，就取第一个吧
        }
        // 筛选字重、风格和子族信息
        if (!matching_fonts.empty()) {
            int max_score = 0;  // 当前匹配上的字体的评分
            for (auto& font : matching_fonts) {
                if (weight_exists && font->GetWeight() != font_weight ||
                    style_exists && font->GetStyle() != font_style ||
                    stretch_exists && font->GetStretch() != font_stretch ||
                    p_subfamily_name && !FontHasName(font, DWRITE_INFORMATIONAL_STRING_WIN32_SUBFAMILY_NAMES, *p_subfamily_name))
                    continue;
                int score = this->CalculateMatchingScore(font,  // 计算字体匹配分值
                    font_weight, !weight_exists, font_style, !style_exists, font_stretch, !stretch_exists);
                if (score > max_score) {
                    matched_font = font;
                    max_score = score;
                }
            }
        }
    }
    else {
        if (matched_family && matching_fonts.empty()) {   // 仅有家族筛选
            // 有子族筛选，从家族选出按匹配程度排序的列表，从中选出第一个符合子族筛选的字体
            ComPtr<IDWriteFont> font;
            if (p_subfamily_name) {
                ComPtr<IDWriteFontList> ordered_family_fonts;   // 按属性匹配程度排序的列表
                if (FAILED(matched_family->GetMatchingFonts(
                    font_weight, DWRITE_FONT_STRETCH_NORMAL, font_style, &ordered_family_fonts)))
                    return wstring();

                for (UINT32 i = 0; i < ordered_family_fonts->GetFontCount(); i++) {
                    if (SUCCEEDED(ordered_family_fonts->GetFont(i, &font))
                        && FontHasName(font, DWRITE_INFORMATIONAL_STRING_WIN32_SUBFAMILY_NAMES, *p_subfamily_name)) {
                        matched_font = font;    // 选出第一个符合子族筛选条件的字体
                        break;  // 有家族筛选和子族筛选时，忽略weight和style筛选，因为它们是模糊筛选，怎么都能匹配上
                    }
                }
            }
            // 没有子族筛选，直接返回家族中最符合的一个
            else if (FAILED(matched_family->GetFirstMatchingFont(font_weight, font_stretch, font_style, &matched_font)))
                matched_family->GetFont(0, &matched_font);  // 要是家族内模糊匹配也匹配不到，这种概率不大，就取第一个吧
        }
        else if (!matching_fonts.empty())   // 没有家族筛选，同样忽略weight和style筛选
            matched_font = *matching_fonts.begin();
    }

    return matched_font == nullptr ? wstring() : GetFontPath(GetFontFile(matched_font));
}
