# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal

from common.annotation import AnnotationType

class SignalBus(QObject):
    """ Signal bus """

    annotationTypeChanged = pyqtSignal(AnnotationType)
    splitPolygonFunction = pyqtSignal(bool)
    addPointFunction = pyqtSignal(bool)

signalBus = SignalBus()
