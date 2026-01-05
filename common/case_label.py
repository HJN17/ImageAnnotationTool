#coding=utf-8
from typing import List,Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QTransform
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject

from QtUniversalToolFrameWork.common.style_sheet import themeColor
from QtUniversalToolFrameWork.common.config import qconfig

from common.utils import Utils
from common.signal_bus import signalBus

class CaseLabel(QObject):

    label_show_changed = pyqtSignal(str)

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

        self.set_label("default", themeColor())

        self.set_label("char")

        self.set_label("test")

        self.set_label("string")


        qconfig.themeColor.valueChanged.connect(lambda: self.set_label("default", themeColor()))
        signalBus.caseLabelShow.connect(self._on_case_label_show)


    def get_color(self, label_value: str) -> QColor:

        if label_value in self._label.keys():
            return self._label[label_value]["color"]
        return themeColor()
    
      
    def set_label(self, label_value: str, color: QColor= None, is_show: bool = True):

        if color is None:
            color = Utils.generate_random_color()

        if label_value in self._label.keys():
            self._label[label_value]["color"] = color
    
        else:
            self._label[label_value] = {"color": color, "show": is_show}


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
    
    def _on_case_label_show(self, caseLabel: str, show: bool):
        if caseLabel in self._label.keys():

            if self._label[caseLabel]["show"] != show:
                self._label[caseLabel]["show"] = show
                self.label_show_changed.emit(caseLabel)
        
cl = CaseLabel()
