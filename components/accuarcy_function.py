# codint=utf-8

from abc import ABC, abstractmethod

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
from QtUniversalToolFrameWork.common.icon import FluentIconBase 

from common.icon import icon
from common.signal_bus import signalBus
from common.annotation import AnnotationType


class AccuracyFunctionBase(QWidget):
    def __init__(self,icon: FluentIconBase,text:str,tip :str,checkable:bool=False, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._text = text
        self._tip = tip
        self._checkable = checkable

    @property
    def icon(self):
        return self._icon
    @property
    def text(self):
        return self._text
    
    @property
    def tip(self):
        return self._tip
    
    @property
    def checkable(self):
        return self._checkable

    def on_click(self, event):
        pass


class DefaultMouseFunction(AccuracyFunctionBase):

    def __init__(self,parent=None):
        super().__init__(icon.MOUSE,"鼠标功能","鼠标功能",True,parent=parent)
        self.setObjectName("defaultMouseFunction")
    
    def on_click(self, event):
        signalBus.annotationTypeChanged.emit(AnnotationType.DEFAULT)


class PolygonFunction(AccuracyFunctionBase):

    def __init__(self,parent=None):
        super().__init__(icon.POLYGON,"绘制多边形","多边形",True,parent=parent)
        self.setObjectName("polygonFunction")
    
    def on_click(self, event):
        signalBus.annotationTypeChanged.emit(AnnotationType.POLYGON)

class BboxFunction(AccuracyFunctionBase):

    def __init__(self,parent=None):
        super().__init__(icon.BBOX,"绘制矩形框","矩形框",True,parent=parent)
        self.setObjectName("bboxFunction")
    
    def on_click(self, event):
        signalBus.annotationTypeChanged.emit(AnnotationType.BBOX)

class LineFunction(AccuracyFunctionBase):

    def __init__(self,parent=None):
        super().__init__(icon.LINE,"绘制折线","折线",True,parent=parent)
        self.setObjectName("lineFunction")
    
    def on_click(self, event):
        signalBus.annotationTypeChanged.emit(AnnotationType.LINE)

class PointFunction(AccuracyFunctionBase):

    def __init__(self,parent=None):
        super().__init__(icon.POINT,"绘制点","点",True,parent=parent)
        self.setObjectName("pointFunction")
    
    def on_click(self, event):
        signalBus.annotationTypeChanged.emit(AnnotationType.POINT)


class SplitPolygonFunction(AccuracyFunctionBase):
    def __init__(self,parent=None):
        super().__init__(icon.SPLIT,"分割多边形","分割多边形",False,parent=parent)
        self.setObjectName("splitPolygonFunction")
    
    def on_click(self, event):
        signalBus.splitPolygonFunction.emit(True)




