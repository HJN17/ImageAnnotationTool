# coding: utf-8
from enum import Enum
from PyQt5.QtGui import QColor
from .style_sheet import themeColor, Theme, isDarkTheme
from .config import isDarkThemeMode

class ThemeBackgroundColor(Enum):

    LIGHT = QColor(249, 244, 240)
    DARK = QColor(32, 32, 32)

    @classmethod
    def color(cls) -> QColor:
        return cls.DARK.value if isDarkThemeMode() else cls.LIGHT.value



class FluentSystemColor(Enum):
    """
    Fluent系统状态颜色枚举类
    定义与系统状态（成功/警告/错误）相关的颜色，每个枚举值包含浅色/深色主题双值
    通过color()方法根据当前主题自动切换颜色值
    """
    
    SUCCESS_FOREGROUND = ("#0f7b0f", "#6ccb5f") # 成功状态前景色：(浅色主题值, 深色主题值) - 用于成功提示文本
    CAUTION_FOREGROUND = ("#9d5d00", "#fce100") # 警告状态前景色：(浅色主题值, 深色主题值) - 用于警告提示文本
    CRITICAL_FOREGROUND = ("#c42b1c", "#ff99a4")    # 严重错误状态前景色：(浅色主题值, 深色主题值) - 用于错误提示文本
    SUCCESS_BACKGROUND = ("#dff6dd", "#393d1b") # 成功状态背景色：(浅色主题值, 深色主题值) - 用于成功提示背景
    CAUTION_BACKGROUND = ("#fff4ce", "#433519") # 警告状态背景色：(浅色主题值, 深色主题值) - 用于警告提示背景
    CRITICAL_BACKGROUND = ("#fde7e9", "#442726")    # 严重错误状态背景色：(浅色主题值, 深色主题值) - 用于错误提示背景

    def color(self, theme=Theme.AUTO) -> QColor:
        color = self.value[1] if isDarkThemeMode(theme) else self.value[0]
        return QColor(color)

def validColor(color: QColor, default: QColor) -> QColor:
    # 验证颜色有效性并返回安全颜色（无效时返回默认值）
    return color if color.isValid() else default

def fallbackThemeColor(color: QColor):
    # 颜色无效时回退到当前主题的默认颜色
    return color if color.isValid() else themeColor()


def autoFallbackThemeColor(light: QColor, dark: QColor):
    # 根据当前主题自动选择颜色，无效时回退到主题默认色
    color = dark if isDarkTheme() else light
    return fallbackThemeColor(color)

