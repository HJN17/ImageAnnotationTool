# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal

from common.annotation import AnnotationType

class SignalBus(QObject):
    """ Signal bus """

    annotationTypeChanged = pyqtSignal(AnnotationType)

    splitPolygonFunction = pyqtSignal(bool)


    itemCaseLabelChanged = pyqtSignal(str, str) # item中标签改变信号，参数为itemKey, caseLabel
    
    deleteItem = pyqtSignal(str)
    selectItem = pyqtSignal(str)
    addItem = pyqtSignal(str, str, AnnotationType)
    caseLabelShow = pyqtSignal(str, bool)

signalBus = SignalBus()
