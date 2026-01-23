# coding:utf-8
from enum import Enum
from QtUniversalToolFrameWork.common.icon import FluentIconBase, getIconColor
from QtUniversalToolFrameWork.common.config import Theme

class icon(FluentIconBase, Enum):
    """ Fluent图标枚举（定义所有可用的Fluent风格图标） """

    UNDO = "undo"
    REDO = "redo"


    BBOX = "bbox"
    LINE = "line"
    MOUSE = "mouse"
    POINT = "point"
    POLYGON = "polygon" 
    SPLIT = "split"
    VERTEX = "vertex"
    ADD_POINT = "add_point"
    HELP = "help"



    def path(self, theme=Theme.AUTO) -> str:

        color = getIconColor(theme)

        return f':/app/images/{color}/{self.value}.svg'
