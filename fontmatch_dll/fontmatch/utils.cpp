#include "pch.h"
#include "utils.h"

using Microsoft::WRL::ComPtr;
using namespace std;


ComPtr<IDWriteFontFile> GetFontFile(ComPtr<IDWriteFont> font)
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

bool FontHasName(ComPtr<IDWriteFont> font, DWRITE_INFORMATIONAL_STRING_ID stringId, wstring& name)
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

vector<wstring> GetFontNames(ComPtr<IDWriteFont> font, DWRITE_INFORMATIONAL_STRING_ID stringId)
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

wstring GetFontPath(ComPtr<IDWriteFontFile> file)
{
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
