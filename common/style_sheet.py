# coding: utf-8
from enum import Enum

from QtUniversalToolFrameWork.common.config import Theme, qconfig
from QtUniversalToolFrameWork.common.style_sheet import StyleSheetBase


class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """


    ACCURACY_INTERFACE = "accuracy_interface"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.themeMode.value if theme == Theme.AUTO else theme
        return f":/app/qss/{theme.value.lower()}/{self.value}.qss"
