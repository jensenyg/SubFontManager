import os
from .App import App


class LanguageDict:
    """多语言字典"""
    ENGLISH = 'English'

    def __init__(self, langDir: str = None):
        self.name: str = '' # 语言名，如English，简体中文
        self.dict: dict[str, str] = {}  # 语言翻译字典
        self.allLangs: dict[str, str] = {self.ENGLISH: ''}  # 语言目录下所有的语言名和文件名映射

        lang_dir: str = langDir if langDir else os.path.join(App.getResourcesDirectory(), 'lang')   # 语言文件目录
        lang_file: str = App.Config.get('General', 'lang', App.lang).lower()    # 语言文件名，缺省使用系统界面语言

        if os.path.exists(lang_dir):
            for filename_ext in next(os.walk(lang_dir))[2]: # 遍历目录内所有文件
                filename, ext = os.path.splitext(filename_ext)
                if ext.lower() != '.json':  # 跳过非json文件
                    continue
                lang_path = os.path.join(lang_dir, filename_ext)
                try:
                    with open(lang_path, 'r', encoding='utf-8') as file:
                        file_str = file.read()
                    lang_dict = eval(file_str)  # 对简单的文本键值json，直接用eval执行
                    lang_name = lang_dict.get('name')   # 语言名
                    if lang_name is None:   # 不包含语言名，不是合法的语言文件
                        continue
                    self.allLangs[lang_name] = filename
                    if filename.lower() == lang_file:   # 找到当前配置的语言文件
                        self.name = lang_name
                        self.dict = lang_dict.get('dict', {})
                except Exception:
                    print(f'Warning: 语言文件 {lang_path} 错误，已忽略.')

        if not self.name:   # 如果没找到当前配置的语言文件，则退回到英语
            self.name = self.ENGLISH
            App.Config.set('General', 'lang', '')

        self.nameInConfig = self.name   # 配置文件中已经保存的语言，此值为语言名，但其实ini里存的是文件名

    def __getitem__(self, key) -> str:
        return self.dict.get(key, key)

    def Switch(self, name: str):
        """切换语言，仅保存配置，新语言重启后生效"""
        self.nameInConfig = name
        App.Config.set('General', 'lang', self.allLangs[name])


Lang = LanguageDict()
