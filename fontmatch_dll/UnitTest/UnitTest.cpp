#include "pch.h"
#include <windows.h>
#include <string>
#include <codecvt>      // C++11, C++17已废弃，但仍可用
#include "CppUnitTest.h"

using namespace std;
using namespace Microsoft::VisualStudio::CppUnitTestFramework;

extern "C" __declspec(dllimport) int FONT_PROPERTY_ID_POSTSCRIPT_NAME;  // 0
extern "C" __declspec(dllimport) int FONT_PROPERTY_ID_FULL_NAME;        // 1
extern "C" __declspec(dllimport) int FONT_PROPERTY_ID_FAMILY_NAME;      // 2
extern "C" __declspec(dllimport) int FONT_PROPERTY_ID_SUBFAMILY_NAME;   // 3
extern "C" __declspec(dllimport) int FONT_PROPERTY_WEIGHT;              // 4
extern "C" __declspec(dllimport) int FONT_PROPERTY_STYLE;               // 5

// UTF-8转换器，.from_bytes()：UTF-8转wstring，.to_bytes()：wstring转UTF-8
wstring_convert<codecvt_utf8<wchar_t>> utf8conv;


namespace UnitTest
{
	TEST_CLASS(UnitTest)
	{
	public:
        typedef const char* (*GetMatchingFontFunc)(const char* json_str);
        typedef void (*ReleaseArrayFunc)(const void* data);
        typedef bool (*InitFunc)();

        HMODULE hDll;

        // UTF8字串与wstring的比较函数
        static inline bool utf8cmp(const char* str1, const wchar_t* str2) {
            return lstrcmpiW(utf8conv.from_bytes(str1).c_str(), str2) == 0;
        }

        TEST_METHOD_INITIALIZE(MethodInit)
        {
            // 载入DLL
#ifdef _DEBUG
            hDll = LoadLibrary(L"../../x64/Debug/fontmatch.dll");
#else
            hDll = LoadLibrary(L"../../x64/Release/fontmatch.dll");
#endif
            if (!hDll) {
                Assert::Fail(L"Unable to load DLL.");
                return;
            }
        }

		TEST_METHOD(TestMethod1)
		{
            // 函数名称必须和DLL中导出的一致
            auto GetMatchingFont = (GetMatchingFontFunc)GetProcAddress(hDll, "GetMatchingFont");
            auto Init = (InitFunc)GetProcAddress(hDll, "Init");

            if (!GetMatchingFont || !Init) {
                Assert::Fail(L"Fail to load functions.");
                return;
            }

            if (!Init()) {
                Assert::Fail(L"Unable to initiate dll.");
                return;
            }

            // Test cases -------------
            const char* fontname = GetMatchingFont(R"({"0": "ArialMT", "1": "Arial", "2": "Arial", "3": "regular", "4": 100, "5": 2})");
            Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIAL.TTF"));

            fontname = GetMatchingFont(R"({"0": "ArialMT", "1": "Arial", "2": "Arial", "3": "Bold", "4": 100, "5": 2})");
            Assert::AreEqual(fontname, nullptr);

            fontname = GetMatchingFont(R"({"1": "Arial", "2": "Arial", "3": "bold", "4": 100, "5": 2})");
            Assert::AreEqual(fontname, nullptr);

            fontname = GetMatchingFont(R"({"2": "Arial", "3": "Bold", "4": 100, "5": 2})");
            Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALBD.TTF"));

            fontname = GetMatchingFont(R"({"2": "Arial", "4": 100, "5": 2})");
            Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALI.TTF"));

            fontname = GetMatchingFont(R"({"2": "Arial", "4": 700, "5": 2})");
            Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALBI.TTF"));

            fontname = GetMatchingFont(utf8conv.to_bytes(LR"({"2": "微软雅黑", "4": 700, "5": 2})").c_str());
            Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\MSYHBD.TTC"));

            fontname = GetMatchingFont(R"({"2": "Arial", "5": 2})");
            //Logger::WriteMessage(fontname);
            Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALI.TTF"));

            FreeLibrary(hDll);
		}
	};
}
