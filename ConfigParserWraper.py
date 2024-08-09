import os
import configparser


class ConfigParserWraper:
    """用来方便读写ini文件的类"""
    def __init__(self, path: str = None):
        self.path = path
        self.parser = configparser.ConfigParser()
        if os.path.isfile(path) and os.access(path, os.R_OK):
            with open(self.path, 'r', encoding='utf-8') as f:
                self.parser.read_file(f)
            # self.parser.read(self.path)

    def get(self, section: str, key: str = None, default=None, saveDefault: bool = True) -> (str, iter):
        """
        读取ini配置值
        :param section: section
        :param key: key，如果为空则取回该section下的所有(key,value)对
        :param default: 如果指定的section或key找不到，则返回default
        :param saveDefault: 当指定的值找不到，需返回default时，是否将default保存到section和key的位置
        :return:
        """
        if section in self.parser:
            if key is None:
                return self.parser[section].items()
            elif key in self.parser[section]:
                return self.parser[section][key]
        if saveDefault:
            self.set(section, key, default)
        return default

    def set(self, section: str, key: str, value=None) -> None:
        """设置ini配置值"""
        if key is None:
            key = ''
        if value is None:
            value = ''
        if section not in self.parser:
            self.parser.add_section(section)
        self.parser.set(section, key, str(value))

    def save(self, path: str = None) -> bool:
        """保存配置到path指定的文件，path缺省则保存到源文件"""
        if not path:
            path = self.path
        dir = os.path.dirname(path)
        try:
            if not os.path.exists(dir):
                os.makedirs(dir, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as file:
                self.parser.write(file)
            return True
        except Exception as e:
            if 'file' in locals() and file:
                file.close()
            print('配置文件写入错误:', path)
            return False
