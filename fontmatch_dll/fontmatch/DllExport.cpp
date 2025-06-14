﻿#include "pch.h"
#include <unordered_map>
#include <string>
#include <codecvt>  // C++11, C++17已废弃，但仍可用
#include "utils.h"
#include "FontMatch3.h"
#include "DllExport.h"

using namespace std;

FontMatch  fontMatcher1;    // 基于DirectWrite1的字体匹配器
FontMatch3 fontMatcher3;    // 基于DirectWrite3的字体匹配器
FontMatch* fontMatcher;     // 实际使用的字体匹配器指针，指向fontMatcher1或fontMatcher3

int resultCode; // 匹配操作的结果码


bool Init(const int version) {   // 初始化
    // 根据系统支持情况选择DW1（Win7）或DW3（Win10）的接口，DW1的接口需要缓存，DW3不需要
    if (FontMatch::IsSupported()) {
        if ((version == 0 || version > 1) && FontMatch3::IsSupported()) {    // 支持DW3，初始化FontMatch3
            if (fontMatcher3.Init())
                fontMatcher = &fontMatcher3;
            else
                return false;
        }
        else {  // 要求使用DW1或仅支持DW1，初始化FontMatch
            if (fontMatcher1.Init())
                fontMatcher = &fontMatcher1;
            else
                return false;
        }
        return true;
    }
    return false;
}

const char* GetMatchingFont(const char* json_str, bool strict) {
    // 解析JSON串 ------
    unordered_map<string, string> json;
    try {
        json = ParseJson(json_str);
        if (!json.size()) {
            resultCode = 1;
            return nullptr;
        }
    }
    catch (...) {
        resultCode = 1;
        return nullptr;
    }

    resultCode = 0; // 结果码置为正常

    // UTF-8转换器，.from_bytes()：UTF-8转wstring，.to_bytes()：wstring转UTF-8
    static wstring_convert<codecvt_utf8<wchar_t>> utf8conv;

    // 将JSON <string, string>字典转换为<FONT_PROPERTY, wstring>字典
    unordered_map<FONT_PROPERTY, wstring> prop_dict;
    for (auto& pair : json)
        prop_dict[static_cast<FONT_PROPERTY>(stoi(pair.first))] =
            utf8conv.from_bytes(pair.second.c_str());

    static string path_str; // 用static变量来返回，这样内存在DLL内管理，外部不用回收
    // 查找匹配字体并返回路径再转换为UTF-8 string
    path_str = utf8conv.to_bytes(fontMatcher->GetMatchingFont(prop_dict, strict));
    return path_str.size() == 0 ? nullptr : path_str.c_str();   // 空字串直接返回空指针
}

int GetLastResultCode()
{
    return resultCode;
}
