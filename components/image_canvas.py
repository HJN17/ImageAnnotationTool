# coding: utf-8
from typing import List
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QTransform
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPointF

from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageCanvas
from common.utils import Utils
from common.json_structure_data import DataItemInfo
from common.annotation import AnnotationType,AnnotationFrameBase
from common.polygon_clip import polygon_clipper



class PolygonsDrawImageCanvas(ImageCanvas):

    # 分割点创建完成信号
    split_vertex_created = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.shift_pressed = False

        self.all_points_colors = [] 
       
        self.init_vars()

    def init_vars(self):
        
        self.data_items = []

        self.total_rotate_angle = 0

        self.current_item_index = -1 

        self.creating_data_item = False 
        self.creating_split_vertex = False
        self.annotion_frame = AnnotationFrameBase.create(AnnotationType.POLYGON)

        self.current_point_index = -1  # 当前选中的点索引

        self._dragging_vertex = False



        self.split_item_index = -1 # 分割项索引

        self.split_point_index_start = -1 # 分割点索引开始
        self.split_point_index_end = -1 # 分割点索引结束
        


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
            self.annotion_frame.draw(painter, self.scale, self.offset, self._get_color(len(self.data_items)), self._rotate_point)
            return
        
        if self.creating_split_vertex:
            self.annotion_frame.draw(painter, self.scale, self.offset, self._get_color(self.split_item_index), self._rotate_point)
            return

    def _get_color(self, index : int):
        """获取指定索引的颜色"""

        if index < len(self.all_points_colors):
            color = self.all_points_colors[index]
        else:
            color = Utils.generate_random_color()
            self.all_points_colors.append(color)
        return color

    def _draw_all_points(self, painter : QPainter):

        items = self.data_items

        for i, item in enumerate(items): 

            rotated_points = [self._rotate_point(point) for point in item.points]


            # for index, point in enumerate(rotated_points):
            #     print("---"*30)
            #     print(index, point)
            #     print("---"*30)

            new_points = [QPointF(point.x() * self.scale + self.offset.x(), 
                            point.y() * self.scale + self.offset.y()) 
                    for point in rotated_points]
            
            #print(f"缩放+偏移后点：{[(int(p.x()),int(p.y())) for p in new_points]}")

            color = self._get_color(i)

            painter.setPen(QPen(color, 2))

            transparent_color = QColor(color)

            if i == self.current_item_index and not self.creating_data_item and not self.creating_split_vertex:
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
            self._add_create_data_item_point(current_point)
            return

        if self.shift_pressed and event.button() == Qt.LeftButton:
            self._add_vertex_to_data_item(clamped_point)
            return

        if self.creating_split_vertex and event.button() == Qt.LeftButton:
            self._add_split_vertex_to_data_item(clamped_point)
            return

        if event.button() == Qt.LeftButton:

            item_idx, vertex_idx = self._check_vertex_click(clamped_point)
            if item_idx != -1 and vertex_idx != -1:
                self.current_item_index = item_idx
                self.current_point_index = vertex_idx
                self._dragging_vertex = True # 拖动顶点
                return

            item_idx = self._check_poly_click(clamped_point)
            if item_idx != -1:
                self.current_item_index = item_idx
                self._dragging_data_item = True
                self._drag_start_pos = clamped_point
                self._data_item_original_pos = [QPointF(p.x(), p.y()) for p in self.data_items[item_idx].points]
                return

        super().mousePressEvent(event)

    def _check_poly_edge_click(self,clamped_point) -> tuple:
        """检查是否点击了多边形边"""
        items = self.data_items
        threshold = 3 / self.scale
        min_dist = float("inf") 
        item_idx = -1 
        best_edge_idx = -1 

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

        if item_idx != -1 and best_edge_idx != -1:
            return(item_idx,best_edge_idx)
        else:
            return (-1,-1)



    def _get_intersection_point(self, item_idx: int, start_point: QPointF, end_point: QPointF) -> tuple:
        
        if item_idx < 0 or item_idx >= len(self.data_items):
            raise IndexError(f"item_idx {item_idx} 超出数据范围")

        item = self.data_items[item_idx]
        points = item.points
        num_points = len(points)

        if num_points < 2:
            return (0,end_point)

        best_edge_idx = 0

        # 遍历所有边，找到距离最近的边
        for j in range(num_points):
            p1 = points[j]
            p2 = points[(j + 1) % num_points]

            
            intersection_point = Utils.line_intersection(p1, p2,start_point, end_point)
            if intersection_point is not None:
                best_edge_idx = j
                break


        return best_edge_idx,intersection_point



    def _get_closest_point_index_and_edge(self, item_idx: int,point: QPointF) -> QPointF:

        if item_idx < 0 or item_idx >= len(self.data_items):
            raise IndexError(f"item_idx {item_idx} 超出数据范围")

        item = self.data_items[item_idx]
        points = item.points
        num_points = len(points)

        if num_points < 2:
            return points[0] if num_points == 1 else point  # 无点返回原坐标，单点返回自身


        min_dist = float("inf")
        best_edge_idx = 0 

        for j in range(num_points):
            p1 = points[j]
            p2 = points[(j + 1) % num_points]

            dist = Utils.point_to_line_distance(point, p1, p2)
            
            if dist < min_dist:
                min_dist = dist
                best_edge_idx = j  # 关键修正：直接记录边的起始索引j

        edge_p1 = points[best_edge_idx]
        edge_p2 = points[(best_edge_idx + 1) % num_points]

        
        closest_point = Utils.get_closest_point_on_line_segment(point, edge_p1, edge_p2)
        return best_edge_idx + 1,closest_point
    


    def _check_vertex_click(self, clamped_point) -> tuple:
        """检查是否点击了顶点"""

        items = self.data_items

        threshold = 10 / self.scale

        for i, item in enumerate(items):
            for j, point in enumerate(item.points):
                
                dist = ((point.x() - clamped_point.x())**2 + (point.y() - clamped_point.y())**2)**0.5 # 计算距离
                if dist < threshold:
                    return (i, j)
        
        return (-1,-1)

    def _check_poly_click(self, clamped_point) -> int:
        items = self.data_items
        
        # 从后往前检查，确保后绘制的多边形优先被选中
        for i, item in enumerate(items):
            item = items[i]

            points = item.points

            if len(points) < 3: 
                continue

            polyf = QPolygonF(points)

            if polyf.containsPoint(clamped_point, Qt.WindingFill):
                return i
            
        return -1
            
    def _add_create_data_item_point(self, current_point):
        """添加创建DataItem的顶点"""

        clamped_point = self._convert_to_original_coords(current_point)
        clamped_point = self._rotate_point_back(clamped_point)

        self.annotion_frame.add_point(clamped_point)
                
        self.update()

    def _add_vertex_to_data_item(self, clamped_point):
        """在DataItem的边上添加顶点"""

        item_idx, best_edge_idx = self._check_poly_edge_click(clamped_point)
        
        if item_idx != -1 and best_edge_idx != -1:
            item = self.data_items[item_idx]
            item.insert_point(best_edge_idx, clamped_point)
            self.current_point_index = best_edge_idx
            self.current_item_index = item_idx
            self.update()
    
    def _add_split_vertex_to_data_item(self, clamped_point):


        def reset_split_state():
            self.annotion_frame = AnnotationFrameBase.create(AnnotationType.POINT)
            self.split_point_index_start = -1
            self.split_point_index_end = -1

            self.split_item_index = -1

        if self.split_item_index == -1:

            item_idx, best_edge_idx = self._check_poly_edge_click(clamped_point)
            
            if item_idx != -1 and best_edge_idx != -1:
                reset_split_state() 
                self.setCursor(Qt.BlankCursor)

                best_edge_idx,closest_point = self._get_closest_point_index_and_edge(item_idx, clamped_point)

                self.split_point_index_start = best_edge_idx
                self.split_item_index = item_idx
                self.annotion_frame.add_point(closest_point)
        
        else:
            item_idx = self._check_poly_click(clamped_point)
            if item_idx == -1:
                print("没有点击到多边形")
                best_edge_idx,closest_point = self._get_intersection_point(self.split_item_index,self.annotion_frame.points[-1], clamped_point)
                self.split_point_index_end = best_edge_idx
                self.annotion_frame.add_point(closest_point)
                self.split_vertex_created.emit()
            else:
                self.annotion_frame.add_point(clamped_point)
        
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
            self._build_annotation_frame(current_point)
            return
        
        if self.creating_split_vertex and self.split_item_index != -1:
            self._build_annotation_frame(current_point)
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

    def _build_annotation_frame(self, current_point):

        clamped_point = self._convert_to_original_coords(current_point)

        clamped_point = self._rotate_point_back(clamped_point)

        self.annotion_frame.set_temp_point(clamped_point) 

        self.update()

    def convert_annotion_frame_coords(self) -> list[QPointF]:

        points = self.annotion_frame.points

        if len(points) < 3:
            print("DataItem至少需要3个顶点")
            return None
        
        self.creating_data_item = False
        self.annotion_frame = AnnotationFrameBase.create(AnnotationType.POLYGON)
        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)

        clipped_points = polygon_clipper.clip_polygon_to_image(points, self.original_pixmap_w_h)
        if clipped_points is None:
            return None
        
        return clipped_points
    
    def finish_create_split_vertex(self):

        item_data_1 = []
        for idx, point in enumerate(self.data_items[self.split_item_index].points):

            if idx < self.split_point_index_start:
                item_data_1.append(point)

            if idx == self.split_point_index_start:
                item_data_1 += self.annotion_frame.points
            
            if idx >= self.split_point_index_end:
                item_data_1.append(point)

        item_data_2 = []
        for idx, point in enumerate(self.data_items[self.split_item_index].points):

            if idx == self.split_point_index_start:
                item_data_2 += self.annotion_frame.points[::-1]
            
            if self.split_point_index_end > idx >= self.split_point_index_start:
                item_data_2.append(point)

 
        del self.data_items[self.split_item_index]
        del self.all_points_colors[self.split_item_index]
        self.creating_split_vertex = False
        self.annotion_frame = AnnotationFrameBase.create(AnnotationType.POLYGON)
        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)

        return (item_data_1, item_data_2)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging_vertex = False
            self._dragging_data_item = False
        super().mouseReleaseEvent(event)


