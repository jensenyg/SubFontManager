#include "pch.h"
#include "FontMatch3.h"

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

bool FontMatch3::IsSupported() {
    // 检查FontMatch(DW1)是否支持，同时会创建DirectWrite工厂
    if (FontMatch::IsSupported())
        return factory3 || SUCCEEDED(factory.As(&factory3));    // 尝试创建DW3工厂
    else
        return false;
}

bool FontMatch3::Init() {   // 获取系统字体集
    return SUCCEEDED(factory3->GetSystemFontSet(&this->systemFontSet));
}

const wstring FontMatch3::GetMatchingFont(unordered_map<FONT_PROPERTY, wstring>& propDict)
{
    // 提取Postscript名、全名和子族名筛选条件 ------
    vector<DWRITE_FONT_PROPERTY> fontProps; // 字体属性描述
    FONT_PROPERTY propNames[] = {   // 用于筛选的属性名
        FONT_PROPERTY::POSTSCRIPT_NAME,
        FONT_PROPERTY::FULL_NAME,
        FONT_PROPERTY::SUBFAMILY_NAME
    };
    for (auto& prop_name : propNames) {
        wstring* value;
        if (TryGetFromMap(propDict, prop_name, value)) {    // 查询属性中包含指定名字
            fontProps.emplace_back();
            auto& prop = fontProps.back();
            prop.propertyId = FONT_PROPERTY_TO_PROPERTY_ID[prop_name];
            prop.propertyValue = value->c_str();
        }
    }

    // 按Postscript名、全名和子族名筛选 ------
    ComPtr<IDWriteFontSet> fontSet = this->systemFontSet; // 用于不断被筛选的字体集合，从系统总字体库开始
    if (!fontProps.empty()) {
        ComPtr<IDWriteFontSet> filtered;    // 筛选结果容器
        if (SUCCEEDED(fontSet->GetMatchingFonts(fontProps.data(), fontProps.size(), &filtered))
            && filtered->GetFontCount() > 0)    // 这个重载版本的GetMatchingFonts只能按照各种名字筛选，不能筛选weight和style
            fontSet = filtered;
        else
            return wstring();
    }

    // 按家族名和粗斜体筛选 ------
    wstring* family_name;
    FONT_PROPERTY tmp;
    if (TryGetFromMap(propDict, tmp = FONT_PROPERTY::FAMILY_NAME, family_name)) { // 查询属性中包含家族名
        auto font_weight = this->GetWeightFromFontProperty(propDict);   // 字重
        auto font_style = this->GetStyleFromFontProperty(propDict);     // 风格（斜体）

        ComPtr<IDWriteFontSet> filtered;    // 筛选结果容器
        if (SUCCEEDED(fontSet->GetMatchingFonts(    // 这个重载版本会进行weigth和style的模糊查找，匹配一个最接近的返回
            family_name->c_str(), font_weight, DWRITE_FONT_STRETCH_NORMAL, font_style, &filtered))
            && filtered->GetFontCount() > 0)
            fontSet = filtered;
        else
            return wstring();
    }   // 如果查找条件中不包含家族名，则weight和style的筛选也无意义，因为它们本来就是模糊匹配的，不在家族内筛了等于没筛

    if (fontSet->GetFontCount() == 0)
        return wstring();

    ComPtr<IDWriteFontFaceReference> faceRef;   // 字体引用
    if (FAILED(fontSet->GetFontFaceReference(0, &faceRef)))    // 取第一个字体就可以
        return wstring();

    ComPtr<IDWriteFontFile> file; // 字体文件
    if (FAILED(faceRef->GetFontFile(&file)))
        return wstring();

    return GetFontPath(file);  // 获取路径字串
}
