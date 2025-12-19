# coding:utf-8
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy


from QtUniversalToolFrameWork.common.font import getFont
from QtUniversalToolFrameWork.common.icon import FluentIcon

from QtUniversalToolFrameWork.components.widgets import ScrollArea
from QtUniversalToolFrameWork.components.layout import ExpandLayout
from QtUniversalToolFrameWork.components.widgets.label import CardLabel
from QtUniversalToolFrameWork.components.widgets.combo_box import ComboBox
from QtUniversalToolFrameWork.components.widgets.button import TransparentToolButton



from common.annotation import AnnotationType
from common.style_sheet import StyleSheet


class InfoCardItem(QWidget):

    def __init__(self,label_text : list[str], annotation_type:AnnotationType, parent=None):
        super().__init__(parent=parent)
       
        self._annotation_type = CardLabel(annotation_type.value.upper(), self)
        self._comboBox = ComboBox(self)

        self._personButton = TransparentToolButton(FluentIcon.ROBOT, self) 
        self._viewButton = TransparentToolButton(FluentIcon.VIEW, self) # HIDE
        self._pinButton = TransparentToolButton(FluentIcon.PIN, self) # UNPIN
        self._delButton = TransparentToolButton(FluentIcon.DELETE, self)

        self._comboBox.addItems(label_text)
        self._comboBox.setCurrentIndex(0)

        self._init_ui()

    def _init_ui(self):
        
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        view = QWidget(self)
        view.setFixedSize(280, 100)


        vBoxLayout = QVBoxLayout(view)
        vBoxLayout.setSpacing(0)
        vBoxLayout.setContentsMargins(20, 0, 20, 0)

        self._annotation_type.setFixedSize(70, 28)
        self._comboBox.setFixedSize(170, 28)
        
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.addWidget(self._annotation_type, 0, Qt.AlignLeft)
        type_layout.addWidget(self._comboBox, 0, Qt.AlignLeft)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 0, 0, 0)
        button_layout.addWidget(self._personButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._viewButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._pinButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._delButton, 0, Qt.AlignLeft)

        vBoxLayout.addLayout(type_layout)
        vBoxLayout.addLayout(button_layout)

        self.mainLayout.addWidget(view)
        
        view.setObjectName('view')

        
class InfoCardInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._item = []
        self._init_ui()

    def _init_ui(self):
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(0,0,0,0)

        view = QFrame(self)
        self.vBoxLayout = QVBoxLayout(view)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        view.setObjectName('view')

       
        mainLayout.addWidget(view)
        StyleSheet.ACCURACY_INTERFACE.apply(self)
    
    @property
    def item(self):
        return self._item

    def addItem(self,label_text : list[str], annotation_type:AnnotationType):
        self._item.append(InfoCardItem(label_text, annotation_type, self))
        self.addWidget(self._item[-1])


    def addWidget(self, widget:InfoCardItem):
        self.vBoxLayout.addWidget(widget)


