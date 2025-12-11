# coding: utf-8
from typing import List
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QTransform
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPointF

from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageCanvas
from common.utils import Utils
from common.json_structure_data import DataItemInfo
from common.annotation import AnnotationType,AnnotationFrameBase



class PolygonsDrawImageCanvas(ImageCanvas):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.shift_pressed = False
        self.all_points_colors = [] 
        self.polygon_clipper = PolygonClipper()
        self.init_vars()

    def init_vars(self):
        
        self.data_items = []

        self.total_rotate_angle = 0

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
            self._draw_points(painter, self.annotion_frame.all_points,len(self.data_items),True)


    def _get_color(self, index : int):
        """获取指定索引的颜色"""

        if index < len(self.all_points_colors):
            color = self.all_points_colors[index]
        else:
            color = Utils.generate_random_color()
            self.all_points_colors.append(color)
        return color


    def _draw_all_points(self, painter : QPainter):
        for i, item in enumerate(self.data_items): 
            self._draw_points(painter, item.points, i)
    
    def _draw_points(self, painter : QPainter, points : list[QPointF],index : int = -1,selected_bool : bool = False):
        """绘制标注框"""

        rotated_points = [self._rotate_point(point) for point in points]

        new_points = [QPointF(point.x() * self.scale + self.offset.x(), 
                        point.y() * self.scale + self.offset.y()) 
                for point in rotated_points]
        
        #print(f"缩放+偏移后点：{[(int(p.x()),int(p.y())) for p in new_points]}")

        color = self._get_color(index)

        painter.setPen(QPen(color, 2))

        transparent_color = QColor(color)

        if selected_bool or index == self.current_item_index:
            transparent_color.setAlpha(128)
        else:
            transparent_color.setAlpha(20)

        painter.setBrush(QBrush(transparent_color, Qt.SolidPattern)) # 填充颜色
        
        if len(new_points) >= 3:
            painter.drawPolygon(QPolygonF(new_points)) # 绘制多边形
        
        painter.setBrush(QBrush(color, Qt.SolidPattern))
        for point in new_points:
            painter.drawEllipse(point, 3, 3)
        


    def _rotate_point(self, point: QPointF) -> QPointF:
        """对单个点应用旋转变换（围绕图片中心）"""

        if self.original_pixmap_w_h is None:
            return point

        if self.total_rotate_angle == 0:
            return point
        
        if self.total_rotate_angle == 90:
            new_x = self.original_pixmap_w_h.height() - point.y()
            new_y = point.x()
        elif self.total_rotate_angle == 180:
            new_x = self.original_pixmap_w_h.width() - point.x()
            new_y = self.original_pixmap_w_h.height() - point.y()
        else:  # 270°顺时针
            new_x = point.y()
            new_y = self.original_pixmap_w_h.width() - point.x()
        
        return QPointF(new_x, new_y)
    
    def _rotate_point_back(self, point: QPointF) -> QPointF:

        if self.original_pixmap_w_h is None:
            return point

        if self.total_rotate_angle == 0:
            return point
        
        if self.total_rotate_angle == 90:
            new_x = point.y()
            new_y = self.original_pixmap_w_h.height() - point.x()
        elif self.total_rotate_angle == 180:
            new_x = self.original_pixmap_w_h.width() - point.x()
            new_y = self.original_pixmap_w_h.height() - point.y()
        else: 
            new_x = self.original_pixmap_w_h.width() - point.y()
            new_y = point.x()
        
        return QPointF(new_x, new_y)
    
    def _convert_to_original_coords(self, point: QPointF) -> QPointF:

        return QPointF(
            (point.x() - self.offset.x()) / self.scale,
            (point.y() - self.offset.y()) / self.scale)

    def _is_point_in_pixmap(self, point: QPointF, offset : QPointF = QPointF(0,0), scale : float = 1.0) -> bool:
        """判断点是否在图片范围内"""

        if self.original_pixmap_w_h is None:
            return None
        
        return QPointF(
            max(0, min((point.x() - offset.x()) / scale, self.original_pixmap_w_h.width())),
            max(0, min((point.y() - offset.y()) / scale, self.original_pixmap_w_h.height())))
    


    def mousePressEvent(self, event): 
        
        if not self.original_pixmap:
            return


        self.current_item_index = -1
        self.current_point_index = -1

        current_point = event.pos()

        clamped_point = self._rotate_point_back(self._is_point_in_pixmap(current_point, self.offset, self.scale))

     
        if self.creating_data_item and event.button() == Qt.LeftButton:
            self._add_create_data_item_vertex(current_point)
            return

        if self.shift_pressed and event.button() == Qt.LeftButton:
            self._add_vertex_to_data_item(clamped_point)
            return


        if event.button() == Qt.LeftButton:

            self._check_vertex_click(clamped_point)

            if self._dragging_vertex:
                return

            self._check_poly_click(clamped_point)

            if self._dragging_data_item:
                return

        
        super().mousePressEvent(event)

    def _add_create_data_item_vertex(self, current_point):
        """添加创建DataItem的顶点"""

        clamped_point = self._convert_to_original_coords(current_point)
        clamped_point = self._rotate_point_back(clamped_point)

        self.annotion_frame.add_point(clamped_point)
                
        self.update()

    def _check_vertex_click(self, clamped_point):
        """检查是否点击了顶点"""

        items = self.data_items

        threshold = 10 / self.scale

        for i, item in enumerate(items):
            for j, point in enumerate(item.points):
                
                dist = ((point.x() - clamped_point.x())**2 + (point.y() - clamped_point.y())**2)**0.5 # 计算距离
                if dist < threshold:
                    self.current_item_index = i
                    self.current_point_index = j
                    self._dragging_vertex = True # 拖动顶点

    def _check_poly_click(self, clamped_point):
        """检查是否点击了多边形内部"""
        items = self.data_items
        
        # 从后往前检查，确保后绘制的多边形优先被选中
        for i, item in enumerate(items):
            item = items[i]

            points = item.points

            if len(points) < 3: 
                continue

            polyf = QPolygonF(points)
        
            is_inside = polyf.containsPoint(clamped_point, Qt.WindingFill)
            
            if is_inside:
                self.current_item_index = i
                self.current_point_index = -1
                self._dragging_data_item = True
                self._drag_start_pos = clamped_point
                self._data_item_original_pos = [QPointF(p.x(), p.y()) for p in item.points]
                return 
    
    def _add_vertex_to_data_item(self, clamped_point):
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
                dist = Utils.point_to_line_distance(clamped_point, p1, p2)
                if dist < threshold and dist < min_dist:
                    min_dist = dist
                    item_idx = i
                    best_edge_idx = j + 1  # 插入到边的后面
        
        if item_idx != -1:
            # 插入新顶点
            item = items[item_idx]
            item.insert_point(best_edge_idx, clamped_point)
            self.current_point_index = best_edge_idx
            self.current_item_index = item_idx
            self.update()
    
    def mouseMoveEvent(self, event):

        current_point = event.pos()
        

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
        
        clamped_point = self._rotate_point_back(self._is_point_in_pixmap(current_point , self.offset, self.scale))
        
        
        item = self.data_items[self.current_item_index]
        item.points[self.current_point_index] = clamped_point

        self.update()    

    def _drag_poly(self, current_point):
        """拖动整个多边形"""
        
        if self.current_item_index < 0 or not self.original_pixmap:
            return
        

        current_point = QPointF((current_point.x() - self.offset.x()) / self.scale,(current_point.y() - self.offset.y()) / self.scale)

        current_point = self._rotate_point_back(current_point)

        dx = current_point.x() - self._drag_start_pos.x()
        dy = current_point.y() - self._drag_start_pos.y()
    
        item = self.data_items[self.current_item_index]

        new_poly = []
        for point in self._data_item_original_pos:
            new_x = point.x() + dx
            new_y = point.y() + dy

            clamped_point = self._is_point_in_pixmap(QPointF(new_x, new_y))
            new_poly.append(clamped_point)

        item.points = new_poly
        self.update()

    def _create_poly(self, current_point):

        clamped_point = self._convert_to_original_coords(current_point)

        clamped_point = self._rotate_point_back(clamped_point)

        self.annotion_frame.set_temp_point(clamped_point) 
        self.update()

    def convert_annotion_frame_coords(self) -> list[QPointF]:
        """保存标注框"""

        points = self.annotion_frame.points

        if len(points) < 3:
            print("DataItem至少需要3个顶点")
            return None
        
        self.creating_data_item = False
        self.annotion_frame = AnnotationFrameBase.create(AnnotationType.POLYGON)
        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)

        clipped_points = self.polygon_clipper.clip_polygon_to_image(points, self.original_pixmap_w_h)
        if clipped_points is None:
            return None
        
        return clipped_points

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging_vertex = False
            self._dragging_data_item = False
        super().mouseReleaseEvent(event)


class PolygonClipper:

    def clip_polygon_to_image(self, points: List[QPointF], image_size: QSize) -> List[QPointF]:

        w, h = image_size.width(), image_size.height()
        clip_functions = [
            lambda p: p.x() >= 0,
            lambda p1, p2: QPointF(0, p1.y() + (p2.y()-p1.y())*(0 - p1.x())/(p2.x()-p1.x())),
            lambda p: p.y() >= 0,
            lambda p1, p2: QPointF(p1.x() + (p2.x()-p1.x())*(0 - p1.y())/(p2.y()-p1.y()), 0),
            lambda p: p.x() <= w,
            lambda p1, p2: QPointF(w, p1.y() + (p2.y()-p1.y())*(w - p1.x())/(p2.x()-p1.x())),
            lambda p: p.y() <= h,
            lambda p1, p2: QPointF(p1.x() + (p2.x()-p1.x())*(h - p1.y())/(p2.y()-p1.y()), h)
        ]

        clipped = points.copy()
        for i in range(0, 8, 2):
            inside_func = clip_functions[i]
            intersect_func = clip_functions[i+1]
            if not clipped:
                break
            new_clipped = []
            n = len(clipped)
            for j in range(n):
                curr = clipped[j]
                prev = clipped[j-1] if j > 0 else clipped[-1]
                
                curr_in = inside_func(curr)
                prev_in = inside_func(prev)

                if curr_in:
                    if not prev_in:
                        try:
                            intersect = intersect_func(prev, curr)
                            new_clipped.append(intersect)
                        except:
                            pass
                    new_clipped.append(curr)
                elif prev_in:
                    try:
                        intersect = intersect_func(prev, curr)
                        new_clipped.append(intersect)
                    except:
                        pass
            clipped = self._clean_points(new_clipped)
        return clipped

    def _clean_points(self, points: List[QPointF]) -> List[QPointF]:
        cleaned = []
        eps = 1e-5
        for p in points:
            if not (p.x() == p.x() and p.y() == p.y()):
                continue
            if not cleaned or (abs(p.x()-cleaned[-1].x()) > eps or abs(p.y()-cleaned[-1].y()) > eps):
                cleaned.append(p)
        return cleaned