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

class LabelCardItem(QWidget):
    
    def __init__(self,label_name:str,parent=None):
        super().__init__(parent)

        self._name = label_name

        self._color = cl.get_color(label_name)

        self._view_button_bool = True

        self._viewButton = TransparentToolButton(f":/resource/images/icons/View_black.svg", self) # HIDE
        
        self._viewButton.clicked.connect(self._on_view_button_clicked)

        self._init_ui()


    def _init_ui(self):
        
        self.setFixedSize(280, 40)
        hBoxLayout = QHBoxLayout(self)
        hBoxLayout.setSpacing(0)
        hBoxLayout.setContentsMargins(20, 0, 10, 0)
        hBoxLayout.addWidget(self._viewButton,0, Qt.AlignRight | Qt.AlignVCenter)


    def _on_view_button_clicked(self):
        
        if self._name == "default":
            return

        if not self._view_button_bool:
            self._view_button_bool = True
            self._viewButton.setIcon(f":/resource/images/icons/View_black.svg")
            signalBus.caseLabelShow.emit(self._name,True)
            return
        
        self._view_button_bool = False
        self._viewButton.setIcon(f":/resource/images/icons/Hide_black.svg")
        signalBus.caseLabelShow.emit(self._name,False)
    

    def paintEvent(self, event):

        painter = QPainter(self)
        
        rect_f = QRectF(self.rect().adjusted(1, 1, -1, -1))

        painter.setRenderHint(QPainter.Antialiasing)

        b_color = QColor(self._color)

        b_color.setAlpha(200) 

        painter.setBrush(QBrush(b_color))
        painter.setPen(QPen(self._color,1))

        _radius = 6
        
        painter.drawRoundedRect(rect_f, _radius, _radius)

        painter.setPen(QPen(Qt.black, 1) )

        painter.setFont(getFont(fontSize=14))

        rect_f = self.rect().adjusted(20, 0, -10, 0) # 调整矩形框，留出10像素的边距

        painter.drawText(rect_f, Qt.AlignLeft | Qt.AlignVCenter, self._name)


class LabelCardInterface(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._items = {}

        self.scrollWidget = QWidget(self)
       
        self._init_ui()

        for label_name in cl.get_all_labels():
            self.insertItem(-1, label_name)

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

    def addItem(self,labelName: str,onClick=None):
        return self.insertItem(-1, labelName ,onClick) 

    def insertItem(self, index: int, labelName: str,onClick=None):
        if labelName in self.items:
            return

        widget = LabelCardItem(labelName, self.scrollWidget)
       
        self.insertWidget(index, labelName, widget, onClick)

        return widget

    def insertWidget(self, index: int, labelName: str, widget: LabelCardItem, onClick=None):
       
        if labelName in self.items:
            return

        widget.setProperty('labelName', labelName)
        
        self.items[labelName] = widget
        self.vBoxLayout.insertWidget(index, widget, 1)


    def removeItem(self, labelName: str):

        if labelName not in self.items:
            return
        
        widget = self.items[labelName]
        self.vBoxLayout.removeWidget(widget) # 从布局中移除部件
        widget.deleteLater() # 删除部件
        del self.items[labelName]

    def clear(self):
        for labelName in list(self.items.keys()):
            self.removeItem(labelName)



