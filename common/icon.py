# coding:utf-8
from enum import Enum
from QtUniversalToolFrameWork.common.icon import FluentIconBase, getIconColor
from QtUniversalToolFrameWork.common.config import Theme

class myIcon(FluentIconBase, Enum):
    """ Fluent图标枚举（定义所有可用的Fluent风格图标） """

    OCR = "ocr"

    def path(self, theme=Theme.AUTO) -> str:

        color = getIconColor(theme)

        return f':/app/images/{self.value}_{color}.svg'
