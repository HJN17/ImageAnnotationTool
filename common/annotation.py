# coding=utf-8
from enum import Enum
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPolygonF,QPainter,QColor,QBrush,QPen
from abc import ABC, abstractmethod
from common.utils import Utils

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
        self._temp_point = None

    @property
    def points(self) -> list[QPointF]:
        return self._points
    
    @property
    def all_points(self) -> list[QPointF]:
        return self._points + [self._temp_point] if self._temp_point else self._points
    
    def set_temp_point(self, point: QPointF):
        self._temp_point = point
    
    def add_point(self, point: QPointF):
        self._points.append(point)

    @abstractmethod
    def draw(self, painter: QPainter, scale: float, offset: QPointF,color: QColor,func: callable = None,selected: bool = False,item_points: list[QPointF] = None) -> list[QPointF]:
        pass    
        
    def check_click(self, points: list[QPointF], clamped_point: QPointF) -> bool:
        return False

    def verify_points(self, points: list[QPointF]=None) -> bool:
        return True
    
    # 拖动顶点
    def drag_vertex(self, item , vertex_idx: int, clamped_point: QPointF):

        item.points[vertex_idx] = clamped_point
    
    # 拖动框
    def drag_frame(self, item, clamped_point: QPointF):
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

    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor, func: callable = None,selected: bool = False,item_points: list[QPointF] = None):
            
            if not item_points:
                points = self.all_points
            else:
                points = item_points

            rotated_points = [func(point) for point in points]

            new_points = [QPointF(point.x() * scale + offset.x(), 
                            point.y() * scale + offset.y()) 
                    for point in rotated_points]
            
            transparent_color = QColor(color)

            if selected:
                transparent_color.setAlpha(128)
            else:
                transparent_color.setAlpha(20)
            

            painter.setPen(QPen(color, 2))

            if self.verify_points(new_points):
                painter.setBrush(QBrush(transparent_color, Qt.SolidPattern))
                painter.drawPolygon(QPolygonF(new_points)) # 绘制多边形
            
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            for point in new_points:
                painter.drawEllipse(point, 2, 2)
    
        
    def verify_points(self, points: list[QPointF]=None) -> bool:
        if not points:
            points = self.points
        return len(points) >= 3
    
    def check_click(self, points: list[QPointF], clamped_point: QPointF) -> bool:
        
        if not self.verify_points(points):
            return False

        polyf = QPolygonF(points)
        if polyf.containsPoint(clamped_point, Qt.WindingFill):
            return True
        return False
    
              
@AnnotationFrameBase.register(AnnotationType.LINE)
class LineAnnotation(AnnotationFrameBase):




    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor,func: callable = None,selected: bool = False,item_points: list[QPointF] = None):
        
        if not item_points:
            points = self.all_points
        else:
            points = item_points


       

        rotated_points = [func(point) for point in points]

        new_points = [QPointF(point.x() * scale + offset.x(), 
                        point.y() * scale + offset.y()) 
                for point in rotated_points]
        

        transparent_color = QColor(color)

        if selected:
            transparent_color.setAlpha(200)
       
        painter.setPen(QPen(transparent_color, 2))


        if self.verify_points(new_points):
            for i in range(1, len(new_points)):
                painter.drawLine(new_points[i-1], new_points[i]) 
        
        painter.setBrush(QBrush(color, Qt.SolidPattern))
        for point in new_points:
            painter.drawEllipse(point, 2, 2) 
        
    def verify_points(self, points: list[QPointF]=None) -> bool:
        if not points:
            points = self.points
        return len(points) >= 2

    def check_click(self, points: list[QPointF], clamped_point: QPointF) -> bool:
        
        if not self.verify_points(points):
            return False

        threshold = 8
        min_dist = 8


        for j in range(len(points)):
            p1 = points[j]
            p2 = points[(j + 1) % len(points)]
            dist = Utils.point_to_line_distance(clamped_point, p1, p2) # 计算点到线的距离
            if dist < threshold and dist < min_dist:
                min_dist = dist
               
        if min_dist < threshold:
            return True
        
        return False

@AnnotationFrameBase.register(AnnotationType.BBOX)
class BboxAnnotation(AnnotationFrameBase):
    
    def __init__(self):
        super().__init__()
        self._start_point = None

    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor,func: callable = None,selected: bool = False,item_points: list[QPointF] = None):

        if not item_points:
            points = self.all_points
        else:
            points = item_points

        rotated_points = [func(point) for point in points]

        new_points = [QPointF(point.x() * scale + offset.x(), 
                        point.y() * scale + offset.y()) 
                for point in rotated_points]
        
        transparent_color = QColor(color)

        if selected:
            transparent_color.setAlpha(128)
        else:
            transparent_color.setAlpha(20)
        
        painter.setPen(QPen(color, 2))
        
        if self.verify_points(new_points):
            painter.setBrush(QBrush(transparent_color, Qt.SolidPattern))
            painter.drawPolygon(QPolygonF(new_points)) 
        
        painter.setBrush(QBrush(color, Qt.SolidPattern))
        for point in new_points:
            painter.drawEllipse(point, 2, 2)

    def verify_points(self, points: list[QPointF]=None) -> bool:
        if not points:
            points = self.points
        return len(points) == 4


    def check_click(self, points: list[QPointF], clamped_point: QPointF) -> bool:
        
        if not self.verify_points(points):
            return False

        polyf = QPolygonF(points)
        if polyf.containsPoint(clamped_point, Qt.WindingFill): # 检查点击是否在矩形框内
            return True
        
        return False

    def drag_vertex(self, item , vertex_idx: int, clamped_point: QPointF):
        
        points = item.points  

        new_points = [clamped_point,None]

        if vertex_idx == 0: 
            new_points[1] =  points[2] 
        if vertex_idx == 1: 
            new_points[1] =  points[3]  
        if vertex_idx == 2: 
            new_points[1] =  points[0] 
        if vertex_idx == 3: 
            new_points[1] =  points[1]  

        
        item.points = Utils.get_rectangle_points(new_points)

    def add_point(self, point: QPointF):
       self._start_point = point

    def set_temp_point(self, point):

        if self._start_point is None:
            self._temp_point = point
            return
        
        self._temp_point = None

        self._points = Utils.get_rectangle_points([self._start_point, point])


@AnnotationFrameBase.register(AnnotationType.POINT)
class PointAnnotation(AnnotationFrameBase):

    def draw(self, painter: QPainter, scale: float, offset: QPointF, color: QColor,func: callable = None,selected: bool = False,item_points: list[QPointF] = None):
        

        if not item_points:
                points = self.all_points
        else:
            points = item_points


        rotated_points = [func(point) for point in points]

        new_points = [QPointF(point.x() * scale + offset.x(), 
                        point.y() * scale + offset.y()) 
                for point in rotated_points]
        

        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color, Qt.SolidPattern))

        for point in new_points:
            painter.drawEllipse(point, 2, 2) 
    
   