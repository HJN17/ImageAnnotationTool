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
    
    def __init__(self):
        self._points = []
        self._temp_points = []

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


    @abstractmethod
    def draw(self, painter: QPainter, scale: float, offset: QPointF,color: QColor,func: callable = None,item_points: list[QPointF] = None) -> list[QPointF]:
        pass    
    
    @abstractmethod
    def verify_points(self) -> bool:
        pass
    
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
@AnnotationFrameBase.register(AnnotationType.DEFAULT)
class PolygonAnnotation(AnnotationFrameBase):

    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor, func: callable = None,item_points: list[QPointF] = None):
            
            if not item_points:
                points = self.all_points
            else:
                points = item_points

            painter.setPen(QPen(color, 2))

            rotated_points = [func(point) for point in points]

            new_points = [QPointF(point.x() * scale + offset.x(), 
                            point.y() * scale + offset.y()) 
                    for point in rotated_points]
            
            if len(new_points) >= 3:
                painter.drawPolygon(QPolygonF(new_points)) # 绘制多边形
            
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            for point in new_points:
                painter.drawEllipse(point, 2, 2)
    
        
    def verify_points(self) -> bool:
        return len(self.points) >= 3
        
@AnnotationFrameBase.register(AnnotationType.LINE)
class LineAnnotation(AnnotationFrameBase):
    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor,func: callable = None,item_points: list[QPointF] = None):
        
        if not item_points:
                points = self.all_points
        else:
            points = item_points

        painter.setPen(QPen(color, 2))

        rotated_points = [func(point) for point in points]

        new_points = [QPointF(point.x() * scale + offset.x(), 
                        point.y() * scale + offset.y()) 
                for point in rotated_points]
        
        for i in range(1, len(new_points)):
            painter.drawLine(new_points[i-1], new_points[i]) 
        
        painter.setBrush(QBrush(color, Qt.SolidPattern))
        for point in new_points:
            painter.drawEllipse(point, 3, 3) 
        
    def verify_points(self) -> bool:
        return len(self._points) >= 2


@AnnotationFrameBase.register(AnnotationType.BBOX)
class BboxAnnotation(AnnotationFrameBase):

    def __init__(self):

        self._points = [QPointF(0, 0), QPointF(0, 0), QPointF(0, 0), QPointF(0, 0)]

        self._temp_points = []
        
    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor,func: callable = None,item_points: list[QPointF] = None):

        if not item_points:
            points = self.all_points
            
        else:
            points = item_points

        painter.setPen(QPen(color, 2))

        rotated_points = [func(point) for point in points if point != QPointF(0, 0)]

        new_points = [QPointF(point.x() * scale + offset.x(), 
                        point.y() * scale + offset.y()) 
                for point in rotated_points]
        
        if len(new_points) == 4:
            painter.drawPolygon(QPolygonF(new_points)) # 绘制多边形
        
        painter.setBrush(QBrush(color, Qt.SolidPattern))
        for point in new_points:
            painter.drawEllipse(point, 2, 2)


    def verify_points(self) -> bool:
        return len(self._points) == 4
    
    def add_point(self, point: QPointF):

        self._points[0] = point
        self._points[1] = QPointF(0, 0)
        self._points[2] = QPointF(0, 0)
        self._points[3] = QPointF(0, 0)


    # 临时点设置，用于绘制矩形框
    def set_temp_point(self, point):
        if self._points[0] == QPointF(0, 0):
            self._temp_points = [point]
            return

        self._temp_points = [QPointF(0, 0)]

        self._points[1] = QPointF(point.x(), self._points[0].y())
        
        self._points[2] = QPointF(point.x(), point.y())

        self._points[3] = QPointF(self._points[0].x(), point.y())