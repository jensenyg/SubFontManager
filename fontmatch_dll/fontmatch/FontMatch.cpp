#include "pch.h"
#include <vector>
#include "FontMatch.h"

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

bool FontMatch::IsSupported() {
    return factory || SUCCEEDED(DWriteCreateFactory(DWRITE_FACTORY_TYPE_SHARED, __uuidof(IDWriteFactory), &factory));
}

bool FontMatch::Init() {    // 创建系统字体信息缓存
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
                set<ComPtr<IDWriteFont>>* p_fonts;  // 同名字体集合，为合并重复，使用set
                if (TryGetFromMap(this->fullNameDict, name, p_fonts)) {
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

const wstring FontMatch::GetMatchingFont(unordered_map<FONT_PROPERTY, wstring>& propDict)
{
    FONT_PROPERTY tmp;
    // Postscript名匹配 -------
    ComPtr<IDWriteFont>* p_psname_font = nullptr;   // Postscript名匹配结果
    wstring* ps_name;
    if (TryGetFromMap(propDict, tmp = FONT_PROPERTY::POSTSCRIPT_NAME, ps_name)  // 查询属性中包含指定名字
        && !TryGetFromMap(this->postScriptDict, *ps_name, p_psname_font))   // 从缓存中取出字体对象
        return wstring();   // 系统中不存在，匹配失败

    // 全名匹配 -------
    set<ComPtr<IDWriteFont>>* p_fullname_fonts = nullptr;   // 全名匹配结果列表
    wstring* full_name;
    if (TryGetFromMap(propDict, tmp = FONT_PROPERTY::FULL_NAME, full_name)  // 查询属性中包含指定名字
        && !TryGetFromMap(this->fullNameDict, *full_name, p_fullname_fonts))    // 从缓存中取出字体对象
        return wstring();   // 系统中不存在，匹配失败

    // 合并p_psname_font和p_fullname_fonts -------
    set<ComPtr<IDWriteFont>> matching_fonts;    // 合并后PS名和全名的联合筛选结果，通常最多就一个了
    if (p_psname_font) {
        if (p_fullname_fonts && p_fullname_fonts->find(*p_psname_font) == p_fullname_fonts->end())
            return wstring();
        matching_fonts.emplace(*p_psname_font);
    }
    else if (p_fullname_fonts)
        matching_fonts = *p_fullname_fonts;

    // 从matching_fonts中筛选子族 -------
    wstring* subfamily_name = nullptr; // 子族名（"Bold", "Italic"等）
    if (TryGetFromMap(propDict, tmp = FONT_PROPERTY::SUBFAMILY_NAME, subfamily_name) && !matching_fonts.empty()) {
        set<ComPtr<IDWriteFont>> matching_fonts2;
        for (auto& font : matching_fonts) { // 遍历每个字体，检查是否包含指定的子族名
            if (this->FontHasName(font, DWRITE_INFORMATIONAL_STRING_WIN32_SUBFAMILY_NAMES, *subfamily_name))
                matching_fonts2.emplace(font);
        }
        if (matching_fonts2.empty())    // 没有找到子族名，匹配失败
            return wstring();
        matching_fonts = move(matching_fonts2);
    }

    // 家族名匹配 -------
    ComPtr<IDWriteFontFamily> matched_family = nullptr;   // 目标家族
    wstring* family_name;
    if (TryGetFromMap(propDict, tmp = FONT_PROPERTY::FAMILY_NAME, family_name)) { // 查询属性中包含家族名
        BOOL exists = FALSE;
        UINT32 family_index;    // 家族在系统家族表中的序号
        if (FAILED(this->systemFontCollection->FindFamilyName(family_name->c_str(), &family_index, &exists)) || !exists
            || FAILED(this->systemFontCollection->GetFontFamily(family_index, &matched_family))) // 系统中找到该家族名并获取家族对象
            return wstring();   // 系统中不存在家族名，那匹配失败
    }

    // 合并matched_family和matching_fonts -------
    ComPtr<IDWriteFont> matched_font = nullptr; // 最终匹配上的字体
    if (matched_family) {   // 有家族筛选
        if (matching_fonts.empty()) {   // 无PS名和全名筛选
            auto font_weight = this->GetWeightFromFontProperty(propDict);   // 字重
            auto font_style = this->GetStyleFromFontProperty(propDict);     // 风格（斜体）
            ComPtr<IDWriteFont> font;

            // 有子族筛选，从家族选出按匹配程度排序的列表，从中选出第一个符合子族筛选的字体
            if (subfamily_name != nullptr) {
                ComPtr<IDWriteFontList> ordered_family_fonts;   // 按属性匹配程度排序的列表
                if (FAILED(matched_family->GetMatchingFonts(
                    font_weight, DWRITE_FONT_STRETCH_NORMAL, font_style, &ordered_family_fonts)))
                    return wstring();
                for (UINT32 i = 0; i < ordered_family_fonts->GetFontCount(); i++) {
                    if (SUCCEEDED(ordered_family_fonts->GetFont(i, &font))
                        && this->FontHasName(font, DWRITE_INFORMATIONAL_STRING_WIN32_SUBFAMILY_NAMES, *subfamily_name)) {
                        matched_font = font;    // 选出第一个符合子族筛选条件的字体
                        break;  // 有家族筛选和子族筛选时，忽略weight和style筛选，因为它们是模糊筛选，怎么都能匹配上
                    }
                }
            }
            // 没有子族筛选，直接返回家族中最符合的一个
            else if (SUCCEEDED(matched_family->GetFirstMatchingFont(
                font_weight, DWRITE_FONT_STRETCH_NORMAL, font_style, &font)))
                matched_font = font;
        }
        else {  // 有PS名和全名筛选，从家族中找出符合PS名和全名筛选的第一个字体
            // 构建matching_font的FontFace集合，因为只有FontFace之间的比较才能正确判断字体是否相等
            set<ComPtr<IDWriteFontFace>> matching_font_faces;
            for (auto& font : matching_fonts) {
                ComPtr<IDWriteFontFace> face;
                font->CreateFontFace(&face);    // 构建FontFace
                matching_font_faces.emplace(face);
            }
            // 遍历家族中的每个字体，检查是否有和matching_font重合的
            for (UINT32 i = 0; i < matched_family->GetFontCount(); i++) {
                ComPtr<IDWriteFont> family_font;
                ComPtr<IDWriteFontFace> family_font_face;
                if (SUCCEEDED(matched_family->GetFont(i, &family_font)) // 获取字体对象
                    && SUCCEEDED(family_font->CreateFontFace(&family_font_face))    // 构造FontFace
                    && matching_font_faces.find(family_font_face) != matching_font_faces.end()) // 在集合中查找家族字体
                {   // 绝大多数情况下，一个家族内不会出现重复的PS名和全名，所以匹配到第一个就成功
                    matched_font = family_font;
                    break;  // 有家族筛选和PS名/全名筛选时，同样忽略weight和style筛选，因为它们是模糊筛选
                }
            }
        }
    }
    else if (!matching_fonts.empty())   // 没有家族筛选
        matched_font = *matching_fonts.begin();

    return matched_font == nullptr ? wstring() : GetFontPath(GetFontFile(matched_font));
}

Microsoft::WRL::ComPtr<IDWriteFontFile> FontMatch::GetFontFile(Microsoft::WRL::ComPtr<IDWriteFont> font)
{
    ComPtr<IDWriteFontFace> fontFace;
    if (FAILED(font->CreateFontFace(&fontFace)))    // 构建FontFace
        return nullptr;

    UINT32 fileCount = 0;
    if (FAILED(fontFace->GetFiles(&fileCount, nullptr)) || fileCount == 0)  // 获取该Face的文件数量
        return nullptr;

    vector<IDWriteFontFile*> fontFiles(fileCount);
    if (FAILED(fontFace->GetFiles(&fileCount, fontFiles.data())))   // 获取该Face的所有文件
        return nullptr;

    // 采用第一个字体文件，交给ComPtr指针管理。一般而言，如果文件数超过一个，那也不是本程序应该处理的情况
    ComPtr<IDWriteFontFile> font_file;  // 实际采用的字体文件对象
    font_file.Attach(fontFiles[0]); // 交给ComPtr指针，它会负责资源的释放
    for (UINT32 j = 1; j < fileCount; j++)  // 注意跳过第一个
        fontFiles[j]->Release();    // 将其他的所有字体文件对象都释放了
    return font_file;
}

bool FontMatch::FontHasName(ComPtr<IDWriteFont> font, DWRITE_INFORMATIONAL_STRING_ID stringId, wstring& name)
{
    BOOL exists = FALSE;
    ComPtr<IDWriteLocalizedStrings> names;
    if (FAILED(font->GetInformationalStrings(stringId, &names, &exists)) || !exists)
        return false;

    auto count = names->GetCount();
    for (UINT32 i = 0; i < count; i++) {    // 遍历字体中每个该类型名字
        UINT32 length = 0;
        if (FAILED(names->GetStringLength(i, &length)))
            continue;
        wstring font_name(length + 1, L'\0');
        if (FAILED(names->GetString(i, &font_name[0], length + 1)))  // 获取名字
            continue;
        font_name.resize(length);
        if (lstrcmpiW(font_name.c_str(), name.c_str()) == 0)    // 不区分大小写比较
            return true;
    }
    return false;
}

vector<wstring> FontMatch::GetFontNames(ComPtr<IDWriteFont> font, DWRITE_INFORMATIONAL_STRING_ID stringId)
{   // 获取字体中指定类别名字的各种版本，例如："Bold", "粗体", "Negreta"（西语）
    vector<wstring> vecNames;
    BOOL exists = FALSE;
    ComPtr<IDWriteLocalizedStrings> names;  // 字体中该类名字的各种本地化版本
    if (SUCCEEDED(font->GetInformationalStrings(stringId, &names, &exists)) || !exists) {   // 获取所有名字
        UINT32 count = names->GetCount();
        vecNames.reserve(count);
        for (UINT32 i = 0; i < count; i++) {    // 遍历字体中每个该类型名字
            UINT32 length = 0;
            if (SUCCEEDED(names->GetStringLength(i, &length))) {
                vecNames.emplace_back(length + 1, L'\0');
                auto& name = vecNames.back();
                if (SUCCEEDED(names->GetString(i, &name[0], length + 1)))  // 获取名字
                    name.resize(length);
            }
        }
    }
    return vecNames;
}

wstring FontMatch::GetFontPath(ComPtr<IDWriteFontFile> file) {
    const void* refKey = nullptr;    // 字体文件访问key
    UINT32 keySize = 0;
    if (FAILED(file->GetReferenceKey(&refKey, &keySize)))
        return wstring();

    ComPtr<IDWriteFontFileLoader> loader;   // 字体文件载入器
    if (FAILED(file->GetLoader(&loader)))
        return wstring();

    ComPtr<IDWriteLocalFontFileLoader> localLoader; // 字体文件本地载入器
    if (FAILED(loader.As(&localLoader)))
        return wstring();

    UINT32 length = 0; // 字体文件路径长度
    if (FAILED(localLoader->GetFilePathLengthFromKey(refKey, keySize, &length)))
        return wstring();

    wstring path(length + 1, L'\0');
    // GetFilePathFromKey不会给字串尾部加\0，不过这里用string::resize来切长度，所以没关系
    if (FAILED(localLoader->GetFilePathFromKey(refKey, keySize, &path[0], length + 1)))
        return wstring();
    path.resize(length);
    return path;
}

DWRITE_FONT_WEIGHT FontMatch::GetWeightFromFontProperty(unordered_map<FONT_PROPERTY, wstring>& propDict)
{   // 获取字重
    auto prop_it = propDict.find(FONT_PROPERTY::WEIGHT);
    return prop_it == propDict.end() ?
        DWRITE_FONT_WEIGHT_REGULAR : static_cast<DWRITE_FONT_WEIGHT>(stoi(prop_it->second));
}

DWRITE_FONT_STYLE FontMatch::GetStyleFromFontProperty(unordered_map<FONT_PROPERTY, wstring>& propDict)
{   // 获取风格（斜体）
    auto prop_it = propDict.find(FONT_PROPERTY::STYLE);
    return prop_it == propDict.end() ?
        DWRITE_FONT_STYLE_NORMAL : static_cast<DWRITE_FONT_STYLE>(stoi(prop_it->second));
}

template<typename MAP, typename T1, typename T2>
static bool FontMatch::TryGetFromMap(MAP& _map, T1& key, T2*& p_value) {
    auto it = _map.find(key);
    if (it == _map.end())
        return false;
    else {
        p_value = addressof(it->second); // 这里不用&，因为it->second可能重载了&，如ComPtr
        return true;
    }
}
