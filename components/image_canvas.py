
# coding: utf-8
from tkinter import N
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QPixmap
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPointF

from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageCanvas
from common.utils import Utils
from common.json_structure_data import DataItemInfo
from common.annotation import AnnotationType,AnnotationFrameBase



class PolygonsDrawImageCanvas(ImageCanvas):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.shift_pressed = False
        self._all_points_colors = [] 

        self.init_vars()

    def init_vars(self):
        
        self.data_items = []

        self.current_item_index = -1 

        self.creating_data_item = False 

        self.annotion_frame = AnnotationFrameBase.create(AnnotationType.POLYGON)
       
        self.current_point_index = -1  # 当前选中的点索引

        self._dragging_vertex = False

        self._dragging_data_item = False # 是否正在拖动DataItem
        self._drag_start_pos = QPointF() # 拖动开始位置
        self._data_item_original_pos = [] # 每个DataItem的原始位置（QPointF列表）

        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event):


        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        self._draw_all_points(painter)
        
        if self.creating_data_item:
            self.annotion_frame.draw(painter, self.scale, self.offset,self._get_color(len(self.data_items)))


    def _get_color(self, index : int):
        """获取指定索引的颜色"""

        if index < len(self._all_points_colors):
            color = self._all_points_colors[index]
        else:
            color = Utils.generate_random_color()
            self._all_points_colors.append(color)
        return color

    def _draw_all_points(self, painter : QPainter):
        
        for i, item in enumerate(self.data_items):

            new_points = [QPointF(point.x() * self.scale + self.offset.x(), 
                            point.y() * self.scale + self.offset.y()) 
                    for point in item.points]

            color = self._get_color(i)

            painter.setPen(QPen(color, 2))

            transparent_color = QColor(color)

            if i == self.current_item_index:
                transparent_color.setAlpha(128)
            else:
                transparent_color.setAlpha(20)

            painter.setBrush(QBrush(transparent_color, Qt.SolidPattern)) # 填充颜色
            
            if len(new_points) >= 3:
                painter.drawPolygon(QPolygonF(new_points)) # 绘制多边形
            
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            for point in new_points:
                painter.drawEllipse(point, 3, 3)
    
    def mousePressEvent(self, event): 
        
        if self._original_pixmap.isNull():
            return

        click_point = QPointF( # 限制在图片范围内
            max(0, min((event.pos().x() - self.offset.x()) / self.scale, self._original_pixmap.width())),
            max(0, min((event.pos().y() - self.offset.y()) / self.scale, self._original_pixmap.height()))
        )

     
        if self.creating_data_item and event.button() == Qt.LeftButton:
            self._add_create_data_item_vertex(click_point)
            return

        if self.shift_pressed and event.button() == Qt.LeftButton:
            self._add_vertex_to_data_item(click_point)
            return


        if event.button() == Qt.LeftButton:

            self._check_vertex_click(click_point)

            if self._dragging_vertex:
                return

            self._check_poly_click(click_point)

            if self._dragging_data_item:
                return

            self.current_item_index = -1
            self.current_point_index = -1
        
        super().mousePressEvent(event)

    def _add_create_data_item_vertex(self, click_point):
        """添加创建DataItem的顶点"""

        self.annotion_frame.add_point(click_point)
        self.update()

    def _check_vertex_click(self, click_point):
        """检查是否点击了顶点"""

        items = self.data_items

        threshold = 10 / self.scale

        for i, item in enumerate(items):
            for j, point in enumerate(item.points):
                
                dist = ((point.x() - click_point.x())**2 + (point.y() - click_point.y())**2)**0.5 # 计算距离
                
                if dist < threshold:
                    self.current_item_index = i
                    self.current_point_index = j
                    self._dragging_vertex = True # 拖动顶点

    def _check_poly_click(self, click_point):
        """检查是否点击了多边形内部"""
        items = self.data_items
        
        # 从后往前检查，确保后绘制的多边形优先被选中
        for i, item in enumerate(items):
            item = items[i]

            points = item.points

            if len(points) < 3: 
                continue

            polyf = QPolygonF(points)
        
            is_inside = polyf.containsPoint(click_point, Qt.WindingFill)
            
            if is_inside:
                self.current_item_index = i
                self.current_point_index = -1
                self._dragging_data_item = True
                self._drag_start_pos = click_point
                self._data_item_original_pos = [QPointF(p.x(), p.y()) for p in item.points]
                return 
    
    def _add_vertex_to_data_item(self, click_point):
        """在DataItem的边上添加顶点"""

        items = self.data_items

        threshold = 2 / self.scale
        item_idx = -1 
        best_edge_idx = -1 
        min_dist = float("inf") # 最小距离，用于判断点击是否在边的附近

        for i, item in enumerate(items):
            points = item.points

            if len(points) < 2:
                continue
            
            for j in range(len(points)):
                p1 = points[j]
                p2 = points[(j + 1) % len(points)]
                dist = Utils.point_to_line_distance(click_point, p1, p2)
                if dist < threshold and dist < min_dist:
                    min_dist = dist
                    item_idx = i
                    best_edge_idx = j + 1  # 插入到边的后面
        
        if item_idx != -1:
            # 插入新顶点
            item = items[item_idx]
            item.insert_point(best_edge_idx, click_point)
            self.current_point_index = best_edge_idx
            self.current_item_index = item_idx
            self.update()
    
    def mouseMoveEvent(self, event):


        current_point = QPointF((event.pos().x() - self.offset.x()) / self.scale,(event.pos().y() - self.offset.y()) / self.scale)


        if self._dragging_vertex:
            
            self._drag_vertex(current_point)
            return

        if self._dragging_data_item:
            self._drag_poly(current_point)
            return

        if self.creating_data_item:
            self._create_poly(current_point)

            return

        super().mouseMoveEvent(event)

    def _drag_vertex(self, current_point):
        """拖动顶点"""
        if self.current_item_index < 0 or self.current_point_index < 0:
            return
        
        clamped_point = QPointF( # 限制在图片范围内
            max(0, min(current_point.x(), self._original_pixmap.width())),
            max(0, min(current_point.y(), self._original_pixmap.height()))
        )
        
        
        item = self.data_items[self.current_item_index]
        item.points[self.current_point_index] = clamped_point

        self.update()    

    def _drag_poly(self, current_point):
        """拖动整个多边形"""
        if self.current_item_index < 0 or self._original_pixmap.isNull():
            return

        dx = current_point.x() - self._drag_start_pos.x()
        dy = current_point.y() - self._drag_start_pos.y()

    
        item = self.data_items[self.current_item_index]
        
        img_width = self._original_pixmap.width()
        img_height = self._original_pixmap.height()


        new_poly = []
        for point in self._data_item_original_pos:
            new_x = point.x() + dx
            new_y = point.y() + dy
            new_x = max(0, min(new_x, img_width))
            new_y = max(0, min(new_y, img_height))
            new_poly.append(QPointF(new_x, new_y))

        item.points = new_poly
        self.update()

    def _create_poly(self, current_point):

        clamped_point = QPointF( # 限制在图片范围内
            max(0, min(current_point.x(), self._original_pixmap.width())),
            max(0, min(current_point.y(), self._original_pixmap.height()))
        )

        self.annotion_frame.set_temp_point(clamped_point) 
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging_vertex = False
            self._dragging_data_item = False
        super().mouseReleaseEvent(event)


