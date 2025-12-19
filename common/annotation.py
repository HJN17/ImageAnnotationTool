# coding=utf-8
from enum import Enum
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPolygonF,QPainter,QColor,QBrush,QPen
from abc import ABC, abstractmethod


class AnnotationType(Enum):
    """ 标注类型枚举 """
    BBOX = "bbox" # 矩形框
    POLYGON = "polygon" # 多边形
    LINE = "line" # 线
    POINT = "point" # 点
    DEFAULT = "default" # 默认

class AnnotationFrameBase(ABC):

    annotation_type={}
    
    @abstractmethod
    def draw(self, painter: QPainter, scale: float, offset: QPointF,color: QColor,func: callable = None) -> list[QPointF]:
        
        painter.setPen(QPen(color, 2))

        transparent_color = QColor(color)

        transparent_color.setAlpha(128)

        painter.setBrush(QBrush(transparent_color, Qt.SolidPattern)) 

        rotated_points = [func(point) for point in self.all_points]

        new_points = [QPointF(point.x() * scale + offset.x(), 
                        point.y() * scale + offset.y()) 
                for point in rotated_points]
        
        return new_points
        
    
 


    @classmethod
    def register(cls, annotation_type: AnnotationType):
        def wrapper(annotation_cls):
            if annotation_type not in cls.annotation_type:
                cls.annotation_type[annotation_type] = annotation_cls
            return annotation_cls
        return wrapper
    

    @classmethod
    def create(cls, annotation_type: AnnotationType, parent=None, **kwargs):
        if annotation_type not in cls.annotation_type:
            raise ValueError(f"标注类型 `{annotation_type}` 未注册")
        return cls.annotation_type[annotation_type](**kwargs)




@AnnotationFrameBase.register(AnnotationType.POLYGON)
class PolygonAnnotation(AnnotationFrameBase):
    def __init__(self, points: list[QPointF] = None):
        
        self._points = points if points else []
        self._temp_points = []

    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor,func: callable = None):

            new_points = super().draw(painter, scale, offset, color,func)
            
            if len(new_points) >= 3:
                painter.drawPolygon(QPolygonF(new_points)) # 绘制多边形
            
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            for point in new_points:
                painter.drawEllipse(point, 3, 3)
        

    @property
    def points(self) -> list[QPointF]:
        return self._points
    
    @property
    def all_points(self) -> list[QPointF]:
        return self._points + self._temp_points
    
    def set_temp_point(self, point: QPointF):
        self._temp_points = [point]
    
    def add_point(self, point: QPointF):
        self._points.append(point)


@AnnotationFrameBase.register(AnnotationType.POINT)
class PointAnnotation(AnnotationFrameBase):

    def __init__(self, points: list[QPointF] = None):
        self._points = points if points else []
        self._temp_points = []


    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor,func: callable = None):
        
        new_points = super().draw(painter, scale, offset, color,func)
        
        for i in range(1, len(new_points)):
            painter.drawLine(new_points[i-1], new_points[i]) 
        
        painter.setBrush(QBrush(color, Qt.SolidPattern))
        for point in new_points:
            painter.drawEllipse(point, 3, 3) 
    
    @property
    def points(self) -> list[QPointF]:
        return self._points
    
    @property
    def all_points(self) -> list[QPointF]:
        return self._points + self._temp_points
    
    def set_temp_point(self, point: QPointF):
        self._temp_points = [point]
    
    def add_point(self, point: QPointF):
        self._points.append(point)


@AnnotationFrameBase.register(AnnotationType.BBOX)
class BboxAnnotation(AnnotationFrameBase):
    def draw(self, painter, scale, offset):
        # 绘制矩形逻辑
        pass


@AnnotationFrameBase.register(AnnotationType.DEFAULT)
class BboxAnnotation(AnnotationFrameBase):
    def draw(self, painter, scale, offset):
        # 绘制矩形逻辑
        pass


