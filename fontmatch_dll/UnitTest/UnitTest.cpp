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
extern "C" __declspec(dllimport) int FONT_PROPERTY_STRETCH;             // 6

// UTF-8转换器，.from_bytes()：UTF-8转wstring，.to_bytes()：wstring转UTF-8
wstring_convert<codecvt_utf8<wchar_t>> utf8conv;


namespace UnitTest
{
	TEST_CLASS(UnitTest)
	{
	public:
        typedef const char* (*GetMatchingFontFunc)(const char* json_str, bool strict);
        typedef bool (*InitFunc)(const int version);

        HMODULE hDll;

        // UTF8字串与wstring的比较函数
        static inline bool utf8cmp(const char* str1, const wchar_t* str2) {
            return str1 && lstrcmpiW(utf8conv.from_bytes(str1).c_str(), str2) == 0;
        }

        //TEST_METHOD_INITIALIZE(MethodInit) {}

		TEST_METHOD(TestMethod1)
		{
            int versions[] = { 0, 1, 3 };
            for (int& version : versions) { // 两种DW版本和自动判断各执行一遍
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

                // 函数名称必须和DLL中导出的一致
                auto GetMatchingFont = (GetMatchingFontFunc)GetProcAddress(hDll, "GetMatchingFont");
                auto Init = (InitFunc)GetProcAddress(hDll, "Init");

                if (!GetMatchingFont || !Init) {
                    Assert::Fail(L"Fail to load functions.");
                    return;
                }

                if (!Init(version)) {
                    Assert::Fail(L"Unable to initiate dll.");
                    return;
                }

                // Test cases -------------
                const char* fontname = GetMatchingFont(R"({"0": "ArialMT", "1": "Arial", "2": "Arial", "3": "regular", "4": 100, "5": 2})", false);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIAL.TTF"));

                fontname = GetMatchingFont(R"({"0": "ArialMT", "1": "Arial", "2": "Arial", "3": "regular", "4": 100, "5": 2})", true);
                Assert::AreEqual(fontname, nullptr);

                fontname = GetMatchingFont(R"({"0": "ArialMT", "1": "Arial", "2": "Arial", "3": "regular", "4": 400, "5": 0})", true);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIAL.TTF"));

                fontname = GetMatchingFont(R"({"0": "ArialMT", "1": "Arial", "2": "Arial", "3": "Bold", "4": 100, "5": 2})", false);
                Assert::AreEqual(fontname, nullptr);

                fontname = GetMatchingFont(R"({"1": "Arial", "2": "Arial", "3": "bold", "4": 100, "5": 2})", false);
                Assert::AreEqual(fontname, nullptr);

                fontname = GetMatchingFont(R"({"2": "Arial", "3": "Bold", "4": 100, "5": 2})", false);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALBD.TTF"));

                fontname = GetMatchingFont(R"({"2": "Arial", "3": "Bold", "4": 100, "5": 2})", true);
                Assert::AreEqual(fontname, nullptr);

                fontname = GetMatchingFont(R"({"2": "Arial", "4": 100, "5": 2})", false);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALI.TTF"));

                fontname = GetMatchingFont(R"({"2": "Arial", "4": 400, "5": 2})", true);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALI.TTF"));   // 注意不能返回ARIALNI等

                fontname = GetMatchingFont(R"({"2": "Arial", "4": 700, "5": 2})", false);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALBI.TTF"));

                fontname = GetMatchingFont(R"({"2": "Arial", "4": 700, "5": 2, "6": 3})", false);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALNBI.TTF"));

                fontname = GetMatchingFont(R"({"2": "Arial", "4": 700, "5": 2})", true);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALBI.TTF"));  // 注意不能返回ARIALNBI等

                fontname = GetMatchingFont(utf8conv.to_bytes(LR"({"1": "Arial Bold", "3": "Bold", "5": 0})").c_str(), false);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\ARIALBD.TTF"));

                fontname = GetMatchingFont(utf8conv.to_bytes(LR"({"2": "微软雅黑", "4": 700, "5": 2})").c_str(), false);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\MSYHBD.TTC"));

                fontname = GetMatchingFont(utf8conv.to_bytes(LR"({"2": "微软雅黑", "4": 700, "5": 0})").c_str(), true);
                Assert::IsTrue(utf8cmp(fontname, L"C:\\WINDOWS\\FONTS\\MSYHBD.TTC"));
                Logger::WriteMessage(fontname);

                FreeLibrary(hDll);
            }
		}
	};
}
