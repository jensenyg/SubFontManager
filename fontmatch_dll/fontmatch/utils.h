#pragma once
#include <unordered_map>
#include <string>
#include <wrl/client.h> // ComPtr智能指针
#include <dwrite_3.h>   // DirectWrite3 API


// 获取字体文件
Microsoft::WRL::ComPtr<IDWriteFontFile> GetFontFile(Microsoft::WRL::ComPtr<IDWriteFont> font);

// 从字体中取出各个名字
std::vector<std::wstring> GetFontNames(Microsoft::WRL::ComPtr<IDWriteFont> font, DWRITE_INFORMATIONAL_STRING_ID stringId);

// 字体的指定名字类型中是否包含指定的名字
bool FontHasName(Microsoft::WRL::ComPtr<IDWriteFont> font, DWRITE_INFORMATIONAL_STRING_ID stringId, const std::wstring& name);

// 获取文件路径
std::wstring GetFontPath(Microsoft::WRL::ComPtr<IDWriteFontFile> file);

// 从map中获取指向值的指针，如果key不存在，则返回nullptr
template<template<typename, typename, typename...> typename T, typename T1, typename T2, typename... Rest>
T2* GetFromMap(T<T1, T2, Rest...>& _map, T1 key) {
    auto it = _map.find(key);
    // 这里不能用&，因为有些类型会重载&操作符，例如ComPtr
    return it == _map.end() ? nullptr : std::addressof(it->second);
}

// 从map中获取指向值的指针，如果key不存在，则返回nullptr。（const版本）
template<template<typename, typename, typename...> typename T, typename T1, typename T2, typename... Rest>
const T2* GetFromMap(const T<T1, T2, Rest...>& _map, T1 key) {
    auto it = _map.find(key);
    return it == _map.end() ? nullptr : std::addressof(it->second);
}

// 从map中获取enum类型的值，当key不存在时返回_default，exists用于接收key是否存在的布尔值
template<template<typename, typename, typename...> typename T, typename T1, typename T2, typename T3, typename... Rest>
T3 GetEnumFromMap(const T<T1, T2, Rest...>& _map, T1 key, T3 _default, bool* exists = nullptr) {
    auto it = _map.find(key);
    if (exists)
        *exists = it != _map.end();
    return it == _map.end() ? _default : static_cast<T3>(stoi(it->second));
}

// 分析非嵌套JSON字串，返回键值字典，格式不合法则抛出异常
std::unordered_map<std::string, std::string> ParseJson(const char* str);
