#include "pch.h"
#include "FontMatch3.h"
#include "utils.h"

using Microsoft::WRL::ComPtr;
using namespace std;

// FONT_PROPERTY和DWRITE_INFORMATIONAL_STRING_ID以及DWRITE_FONT_PROPERTY_ID之前的映射表
static unordered_map<FONT_PROPERTY, DWRITE_FONT_PROPERTY_ID> FONT_PROPERTY_TO_PROPERTY_ID = {
    { FONT_PROPERTY::POSTSCRIPT_NAME, DWRITE_FONT_PROPERTY_ID_POSTSCRIPT_NAME },
    { FONT_PROPERTY::FULL_NAME, DWRITE_FONT_PROPERTY_ID_FULL_NAME },
    { FONT_PROPERTY::FAMILY_NAME, DWRITE_FONT_PROPERTY_ID_FAMILY_NAME },
    { FONT_PROPERTY::SUBFAMILY_NAME, DWRITE_FONT_PROPERTY_ID_FACE_NAME },
    { FONT_PROPERTY::WEIGHT, DWRITE_FONT_PROPERTY_ID_WEIGHT },
    { FONT_PROPERTY::STYLE, DWRITE_FONT_PROPERTY_ID_STYLE },
};


Microsoft::WRL::ComPtr<IDWriteFactory3> FontMatch3::factory3 = nullptr; // 静态变量初始化

bool FontMatch3::IsSupported()
{
    if (FontMatch::IsSupported())   // 检查FontMatch(DW1)是否支持，同时也会创建DW1工厂
        return factory3 || SUCCEEDED(factory.As(&factory3));    // 尝试创建DW3工厂
    else
        return false;
}

bool FontMatch3::Init()
{   // 获取系统字体集
    return SUCCEEDED(factory3->GetSystemFontSet(&this->systemFontSet));
}

const wstring FontMatch3::GetMatchingFont(unordered_map<FONT_PROPERTY, wstring>& propDict, bool strict)
{
    // 提取各种名字属性，用于严格筛选 ------
    vector<DWRITE_FONT_PROPERTY> fontProps; // 字体属性描述
    FONT_PROPERTY propNames[] = {   // 用于严格筛选的属性名
        FONT_PROPERTY::POSTSCRIPT_NAME,
        FONT_PROPERTY::FULL_NAME,
        FONT_PROPERTY::SUBFAMILY_NAME,
        FONT_PROPERTY::FAMILY_NAME
    };
    wstring* prop_value;
    for (auto& prop_name : propNames) {
        prop_value = GetFromMap(propDict, prop_name);
        if (prop_value) {    // 查询属性中包含指定名字
            fontProps.emplace_back();
            auto& prop = fontProps.back();
            prop.propertyId = FONT_PROPERTY_TO_PROPERTY_ID[prop_name];
            prop.propertyValue = prop_value->c_str();
        }
    }

    // 进行严格筛选 ------
    ComPtr<IDWriteFontSet> fontSet; // 筛选结果集合
    if (fontProps.empty()
        || FAILED(this->systemFontSet->GetMatchingFonts(fontProps.data(), (UINT32)fontProps.size(), &fontSet))
        || fontSet->GetFontCount() == 0)    // 这个重载版本的GetMatchingFonts只能按照各种名字筛选，不能筛选weight和style
        return wstring();

    // 三种字体样式信息 ------
    bool weight_exists, style_exists, stretch_exists;
    auto font_weight = GetEnumFromMap(propDict, FONT_PROPERTY::WEIGHT, DWRITE_FONT_WEIGHT_REGULAR, &weight_exists); // 字重
    auto font_style = GetEnumFromMap(propDict, FONT_PROPERTY::STYLE, DWRITE_FONT_STYLE_NORMAL, &style_exists); // 风格（斜体）
    auto font_stretch = GetEnumFromMap(propDict, FONT_PROPERTY::STRETCH, DWRITE_FONT_STRETCH_NORMAL, &stretch_exists); // 拉伸
    wstring*& family_name = prop_value;  // 因为FAMILY_NAME排在最后一个查找，所以最后一个prop_value就是家族名

    // 进行字重风格和子族的筛选，并选出一个匹配的字体 -------
    ComPtr<IDWriteFontFaceReference> matched_faceRef = nullptr; // 最终可能匹配到的字体引用
    if (strict && (weight_exists || style_exists)) {    // 严格模式且有字重风格匹配，则进行严格匹配
        int max_score = 0;  // 当前匹配上的字体的评分，取值0-3，字重、风格、拉伸每满足一项算一分
        for (UINT32 i = 0; i < fontSet->GetFontCount(); i++) {
            ComPtr<IDWriteFontFaceReference> faceRef;   // 字体引用
            ComPtr<IDWriteFontFace3> font_face;
            if (FAILED(fontSet->GetFontFaceReference(i, &faceRef)) ||
                FAILED(faceRef->CreateFontFace(&font_face)) ||
                weight_exists && font_face->GetWeight() != font_weight ||
                style_exists && font_face->GetStyle() != font_style ||
                stretch_exists && font_face->GetStretch() != font_stretch)
                continue;
            int score = this->CalculateMatchingScore(font_face, // 计算字体匹配分值
                font_weight, !weight_exists, font_style, !style_exists, font_stretch, !stretch_exists);
            if (score > max_score) {
                matched_faceRef = faceRef;
                max_score = score;
            }
        }
        if (!matched_faceRef)   // 匹配失败
            return wstring();
    }
    else if (family_name) {  // 非严格模式、或严格模式但不需要字重风格匹配，只要包含家族查询，则进行模糊匹配
        ComPtr<IDWriteFontSet> filtered;    // 筛选结果容器
        if (SUCCEEDED(fontSet->GetMatchingFonts(    // 这个重载版本会进行weigth和style的模糊查找，匹配一个最接近的返回
            family_name->c_str(), font_weight, font_stretch, font_style, &filtered))
            && filtered->GetFontCount() > 0)
            fontSet = filtered;
        else    // 匹配失败
            return wstring();
    }   // 如果非严格模式下查找条件中不包含家族名，则weight和style的筛选也无意义，因为它们是模糊匹配的，不在家族内筛了等于没筛

    ComPtr<IDWriteFontFile> file;   // 字体文件
    if ((matched_faceRef || SUCCEEDED(fontSet->GetFontFaceReference(0, &matched_faceRef)))  // 选第一个结果就可以
        && SUCCEEDED(matched_faceRef->GetFontFile(&file)))
        return GetFontPath(file);   // 获取路径字串
    else
        return wstring();
}
