import os
from .App import App


class LanguageDict:
    """多语言字典"""
    ENGLISH = 'English'

    def __init__(self, langDir: str = None):
        self.langDir = langDir if langDir else os.path.join(App.getResourcesDirectory(), 'lang')
        self.lang = {}
        self.currentLang = self.ENGLISH
        self.initLang = App.Config.get('General', 'lang', 'English')
        self.langList = []

    def __getitem__(self, key) -> str:
        return self.lang.get(key, key)

    def load(self, langName: str = None):
        if not os.path.exists(self.langDir):
            return

        if not langName:
            langName = self.initLang
        self.langList = [self.ENGLISH]
        filenames = next(os.walk(self.langDir))[2]
        for filename in filenames:
            if filename[-5:].lower() != '.json':
                return
            lang_path = os.path.join(self.langDir, filename)
            try:
                with open(lang_path, 'r', encoding='utf-8') as file:
                    file_str = file.read()
                lang_dict = eval(file_str)
                self.langList.append(lang_dict['name'])
                if lang_dict['name'] == langName:
                    self.currentLang = langName
                    self.lang = lang_dict['lang']
            except Exception as e:
                if 'file' in locals() and file:
                    file.close()
                print(f'Warning: 语言文件 {lang_path} 错误，已忽略.')

        if langName not in self.langList:   # 如果ini中设置的语言文件找不到，则将设置修改回English
            self.initLang = self.ENGLISH
            self.saveSetting(self.ENGLISH)

    def saveSetting(self, langName: str = None):
        if langName:
            self.currentLang = langName
        App.Config.set('General', 'lang', self.currentLang)


Lang = LanguageDict()
Lang.load()
