"""提供全局工具"""

from . import version as Version
from .App import App
from .ConfigParserWraper import ConfigParserWraper
from .Lang import Lang

__all__ = ['App', 'ConfigParserWraper', 'Lang', 'Version']
