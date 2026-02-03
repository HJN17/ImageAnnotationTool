# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal

from common.annotation import AnnotationType

class SignalBus(QObject):
    """ Signal bus """

    annotationTypeChanged = pyqtSignal(AnnotationType)
    splitPolygonFunction = pyqtSignal(bool)
    addPointFunction = pyqtSignal(bool)


    setting_label_color_changed = pyqtSignal()

signalBus = SignalBus()
