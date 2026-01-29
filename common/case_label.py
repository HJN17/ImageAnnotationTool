#coding=utf-8
from typing import List,Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QTransform
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject

from QtUniversalToolFrameWork.common.style_sheet import themeColor
from QtUniversalToolFrameWork.common.config import qconfig

from common.utils import Utils

class CaseLabel(QObject):


    update_label_changed = pyqtSignal() # 更新标签信号，参数为标签值

    color_label_changed = pyqtSignal(str) # 标签颜色改变信号，参数为标签值

    show_label_changed = pyqtSignal(str) # 标签显示状态改变信号，参数为标签值,是否选中

    add_label_changed = pyqtSignal(str) # 添加标签信号，参数为标签值

    del_label_changed = pyqtSignal(str) # 删除标签信号，参数为标签值

    _INSTANCE = None 
    _INSTANCE_INIT = False 

    def __new__(cls, *args, **kwargs):
        if not cls._INSTANCE:
            cls._INSTANCE = super().__new__(cls)
        return cls._INSTANCE

    def __init__(self):
        if self._INSTANCE_INIT:
            return
        self._INSTANCE_INIT = True

        super().__init__()  

        self._label = {} # 标签字典，key为标签值,color为颜色,show为是否选中


        qconfig.themeColor.valueChanged.connect(lambda: self._set_color("default", themeColor()))


    def get_color(self, label_value: str) -> QColor:

        if label_value in self._label.keys():
            return self._label[label_value]["color"]
        return themeColor()
    
    def set_label(self, label_value: str, color: QColor= None, is_show: bool = True):

        if label_value in self._label.keys():
            return
        
        if label_value == "default":
            self._label[label_value] = {"color": themeColor(), "show": is_show}
            self.add_label_changed.emit(label_value)
            return
        
        if color is None:
            color = Utils.generate_random_color()

        self._label[label_value] = {"color": color, "show": is_show}
        self.add_label_changed.emit(label_value)

    def remove_label(self, label_value: str):
        if label_value in self._label.keys():
            del self._label[label_value]
            self.del_label_changed.emit(label_value)

    def get_label_name(self, label_value: str):
        if label_value in self._label.keys():
            return label_value
        return "default"
    
    def get_all_labels(self):
        return self._label.keys()

    def get_all_show_labels(self):
        return [label for label in self._label.keys() if self._label[label]["show"]]
    
    def is_show(self, label_value: str):
        if label_value in self._label.keys():
            return self._label[label_value]["show"]
        return True
    
    def set_show(self, caseLabel: str, show: bool):
        if caseLabel in self._label.keys():

            if self._label[caseLabel]["show"] != show:
                self._label[caseLabel]["show"] = show
                self.show_label_changed.emit(caseLabel)
                self.update_label_changed.emit()
        
    def _set_color(self, label_value: str, color: QColor):
        if label_value in self._label.keys():
            if self._label[label_value]["color"] != color:
                self._label[label_value]["color"] = color
                self.color_label_changed.emit(label_value)
                
cl = CaseLabel()
