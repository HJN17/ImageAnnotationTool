
# coding:utf-8
import sys

from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy

from QtUniversalToolFrameWork.components.navigation.pivot import Pivot
from QtUniversalToolFrameWork.components.window.stacked_widget import StackedWidget

from common.annotation import AnnotationType
from common.style_sheet import StyleSheet
from components.info_card import InfoCardInterface, InfoCardItem

class PivotStacked(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedWidth(300)

        self.pivot = Pivot(self)
        self.stackedWidget = StackedWidget(self)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self.view = QFrame(self)

        self.vBoxLayout = QVBoxLayout(self.view)

        self.annotationInterface = InfoCardInterface(self)
        self.labelInterface = InfoCardInterface(self)
        self.issueInterface = InfoCardInterface(self)

        self.addSubInterface(self.annotationInterface, 'annotationInterface', '标注')
        self.addSubInterface(self.labelInterface, 'labelInterface', '标签')
        self.addSubInterface(self.issueInterface, 'issueInterface', '批注')

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(5, 5, 5, 5)
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize) # 设置布局大小约束为固定大小

        self.stackedWidget.setCurrentWidget(self.annotationInterface)
        
        self.pivot.setCurrentItem(self.annotationInterface.objectName())

        self.pivot.currentItemChanged.connect(lambda k:  self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k)))

        mainLayout.addWidget(self.view)

        self.view.setObjectName("view")
        self.stackedWidget.setObjectName("stacked")

        self.add_card_annotation_interface(['标注1', '标注2'], AnnotationType.POLYGON)
        self.add_card_annotation_interface(['标签1', '标签2'], AnnotationType.BBOX)
        self.add_card_annotation_interface(['批注1', '批注2'], AnnotationType.POINT)

    def addSubInterface(self, widget: QLabel, objectName, text):
        widget.setObjectName(objectName)
        widget.setAlignment(Qt.AlignCenter)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    
    def add_card_annotation_interface(self,label_text : list[str], annotation_type:AnnotationType):
        self.annotationInterface.addItem(label_text, annotation_type)
        




