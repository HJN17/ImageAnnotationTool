# coding:utf-8
import sys

from PyQt5.QtCore import Qt,pyqtSignal,QRectF,QEvent
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QFont


from QtUniversalToolFrameWork.common.config import isDarkTheme

from QtUniversalToolFrameWork.common.font import getFont
from QtUniversalToolFrameWork.common.icon import FluentIcon
from QtUniversalToolFrameWork.common.color import ThemeBackgroundColor
from QtUniversalToolFrameWork.components.widgets import ScrollArea
from QtUniversalToolFrameWork.components.layout import ExpandLayout
from QtUniversalToolFrameWork.components.widgets.label import CardLabel
from QtUniversalToolFrameWork.components.widgets.combo_box import ComboBox
from QtUniversalToolFrameWork.components.widgets.button import TransparentToolButton,PushButton

from common.annotation import AnnotationType
from common.style_sheet import StyleSheet
from common.case_label import cl
from common.signal_bus import signalBus


class IssueCardInterface(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._items = {}

        self.scrollWidget = QWidget(self)
       
        self._init_ui()


     
    def _init_ui(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        
        self.setViewportMargins(0, 0, 10, 0)
        self.setWidgetResizable(True)
        self.setWidget(self.scrollWidget)

        self.scrollWidget.setObjectName('scrollWidget')

        StyleSheet.ACCURACY_INTERFACE.apply(self)
    
    @property
    def items(self):
        return self._items

    


