# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal

from common.annotation import AnnotationType

class SignalBus(QObject):
    """ Signal bus """

    annotationTypeChanged = pyqtSignal(AnnotationType)
    splitPolygonFunction = pyqtSignal(bool)
    addPointFunction = pyqtSignal(bool)



    labelComboBoxChanged = pyqtSignal(str, str) # 标签下拉框改变信号，参数为itemKey, caseLabel
    

    deleteItem = pyqtSignal(str) # 删除DataItem信号
    selectItem = pyqtSignal(str) # 选择DataItem信号
    addItem = pyqtSignal(str, str, AnnotationType) # 添加DataItem信号


signalBus = SignalBus()
signalBus.selectItem.connect(lambda index: print("选择了标注框:", index))