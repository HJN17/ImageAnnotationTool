
# coding:utf-8
import sys
from natsort import natsorted
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QColor
from QtUniversalToolFrameWork.components.navigation.pivot import SegmentedWidget
from QtUniversalToolFrameWork.components.window.stacked_widget import StackedWidget
from QtUniversalToolFrameWork.common.cache import LRUCache

from common.utils import Utils
from common.annotation import AnnotationType
from common.style_sheet import StyleSheet
from components.info_card import InfoCardInterface
from components.label_card import LabelCardInterface
from common.data_structure import DataItemInfo
from common.cache_label_card import cl

class PivotStacked(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setFixedWidth(310)

        self.pivot = SegmentedWidget(self)
        self.stackedWidget = StackedWidget(self)


        self.annotationInterface = StackedInfoCardInterface(self)
        self.labelInterface = LabelCardInterface(self)
        self.issueInterface = InfoCardInterface(self)


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

    def show_info_card_interface(self,key:str,data_items:list):
        self.annotationInterface.show_info_card_interface(key,data_items)

    def create_info_card_interface(self,key:str,data_items:list):
        return self.annotationInterface.create_info_card_interface(key,data_items)


class StackedInfoCardInterface(QWidget):

    def __init__(self, parent=None, batch_size=20):
        super().__init__(parent)
        
        self._temp_widget = InfoCardInterface()
        
        self._cache = LRUCache(capacity=batch_size*2)

        self.main_layout = QVBoxLayout(self) 
        
        self.main_layout.setContentsMargins(0, 0, 0, 0) 
        self.main_layout.setSpacing(0)
        
       
        self.main_layout.addWidget(self._temp_widget)
        
        self.setLayout(self.main_layout)


    def create_info_card_interface(self,key:str,data_items:list):

        infoCard = self._cache.get(key)

        if infoCard is not None:
            return infoCard

        infoCard = InfoCardInterface(self)
        sorted_items = natsorted(data_items, key=lambda x: (cl.get_label_name(x.caseLabel)=="default", x.caseLabel)) # 先排序默认标签，再排序其他标签

        for item in sorted_items: 
            infoCard.addItem(item.id,item.caseLabel,item.annotation_type)
        
        self._cache.put(key,infoCard)

        return infoCard

    
    def show_info_card_interface(self,key:str,data_items:list):

        infoCard = self.create_info_card_interface(key,data_items)
        
        self.replace_temp_widget(infoCard)


    def replace_temp_widget(self,widget:InfoCardInterface):
        self.main_layout.replaceWidget(self._temp_widget,widget) # 替换临时widget为infoCard
        self._temp_widget.hide() # 隐藏临时widget
        widget.show()
        self._temp_widget = widget
