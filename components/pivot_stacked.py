
# coding:utf-8
import sys
from natsort import natsorted
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QColor
from QtUniversalToolFrameWork.components.navigation.pivot import SegmentedWidget
from QtUniversalToolFrameWork.components.window.stacked_widget import StackedWidget

from common.utils import Utils
from common.annotation import AnnotationType
from common.style_sheet import StyleSheet
from components.info_card import InfoCardInterface
from components.label_card import LabelCardInterface
from components.issue_card import IssueCardInterface
from common.data_structure import DataItemInfo
from common.data_structure import jsonFileManager
class PivotStacked(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setFixedWidth(310)

        self.pivot = SegmentedWidget(self)
        self.stackedWidget = StackedWidget(self)


        self.annotationInterface = StackedInfoCardInterface(self)
        self.labelInterface = LabelCardInterface(self)
        self.issueInterface = IssueCardInterface(self)

        self.addSubInterface(self.annotationInterface, 'annotationInterface', '标注')
        self.addSubInterface(self.labelInterface, 'labelInterface', '标签')
        self.addSubInterface(self.issueInterface, 'issueInterface', '批注')

        self.stackedWidget.setCurrentWidget(self.annotationInterface)
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

    def show_info_card_interface(self,widget:InfoCardInterface):
        self.annotationInterface.replace_temp_widget(widget)

    def hide_info_card_interface(self):
        self.annotationInterface.hide_info_card_interface()


class StackedInfoCardInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._default_widget = InfoCardInterface()

        self._temp_widget = InfoCardInterface()
        

        self.main_layout = QVBoxLayout(self) 
        
        self.main_layout.setContentsMargins(0, 0, 0, 0) 
        self.main_layout.setSpacing(0)
        
        self.main_layout.addWidget(self._temp_widget)
        
        self.setLayout(self.main_layout)

        StyleSheet.ACCURACY_INTERFACE.apply(self)

    

    def hide_info_card_interface(self):
        self.replace_temp_widget(self._default_widget)

    def replace_temp_widget(self,widget:InfoCardInterface):
        
        widget.setStyleSheet("background-color: transparent;")
        
        self.main_layout.replaceWidget(self._temp_widget,widget) # 替换临时widget为infoCard
        self._temp_widget.hide() # 隐藏临时widget
        widget.show()
        self._temp_widget = widget
