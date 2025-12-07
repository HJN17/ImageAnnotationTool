# coding=utf-8
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPolygonF,QPainter

from abc import ABC, abstractmethod

class BaseAnnotation(ABC):
    @abstractmethod
    def draw(self, painter: QPainter, scale: float, offset: QPointF):
        """绘制标注"""
        pass
    
    @abstractmethod
    def contains_point(self, point: QPointF) -> bool:
        """判断点是否在标注内"""
        pass

class PolygonAnnotation(BaseAnnotation):
    def draw(self, painter, scale, offset):
        
        pass
    def contains_point(self, point: QPointF) -> bool:

        pass

class RectAnnotation(BaseAnnotation):
    def draw(self, painter, scale, offset):
        # 绘制矩形逻辑
        pass


