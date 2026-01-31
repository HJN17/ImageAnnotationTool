
# coding:utf-8
import sys
from natsort import natsorted
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QColor
from QtUniversalToolFrameWork.components.navigation.pivot import SegmentedWidget
from QtUniversalToolFrameWork.components.window.stacked_widget import StackedWidget


from components.info_card import InfoCardInterface
from components.label_card import LabelCardInterface
from components.issue_card import IssueCardInterface
from common.data_structure import DataItemInfo


class PivotStacked(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setFixedWidth(320)

        self.pivot = SegmentedWidget(self)
        self.stackedWidget = StackedWidget(self)

        self.annotationInterface = InfoCardInterface(self)
        self.labelInterface = LabelCardInterface(self)
        self.issueInterface = IssueCardInterface(self)

        self.addSubInterface(self.annotationInterface, 'annotationInterface', '标注')
        self.addSubInterface(self.labelInterface, 'labelInterface', '标签')
        self.addSubInterface(self.issueInterface, 'issueInterface', '批注')

        self.stackedWidget.setCurrentWidget(self.annotationInterface) # 初始化时显示标注界面

        self.pivot.setCurrentItem(self.annotationInterface.objectName())
        self.pivot.currentItemChanged.connect(
            lambda k:  self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k)))

        self._init_ui()


    def _init_ui(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self.view = QFrame(self)

        self.vBoxLayout = QVBoxLayout(self.view)
        

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(5, 5, 5, 5)
        #self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize) # 设置布局大小约束为固定大小

        mainLayout.addWidget(self.view)

        self.view.setObjectName("view")
        self.stackedWidget.setObjectName("stacked")
        
    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def show_info_card_interface(self,item:DataItemInfo):
        
        print(item.to_dict())

        self.annotationInterface.show_item(item.caseLabel,item.annotation_type)

    

