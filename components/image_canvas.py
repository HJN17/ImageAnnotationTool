# coding: utf-8
from typing import List,Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QTransform
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPointF

from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageCanvas
from QtUniversalToolFrameWork.common.style_sheet import themeColor

from common.utils import Utils
from common.data_structure import DataItemInfo
from common.annotation import AnnotationType,AnnotationFrameBase
from common.polygon_clip import polygon_clipper
from common.case_label import cl
from common.data_control_manager import dm

class PolygonsDrawImageCanvas(ImageCanvas):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self._dragging_vertex = False
        self._dragging_data_item = False # 是否正在拖动DataItem
        self._drag_start_pos = QPointF() # 拖动开始位置
        self._data_item_original_pos = [] # 每个DataItem的原始位置（QPointF列表）

        dm.update_data_item.connect(self.update)

        cl.label_show_changed.connect(lambda label: self.update())

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
        
        if dm.creating_data_item:

            transparent_color = QColor(themeColor())
            transparent_color.setAlpha(128)
            painter.setBrush(QBrush(transparent_color, Qt.SolidPattern)) # 填充颜色

            dm.annotion_frame.draw(painter, self.scale, self.offset, themeColor(), self._rotate_point)
            return
        
        if dm.creating_split_vertex:
            label = dm.get_current_data_item_label()

            dm.annotion_frame.draw(painter, self.scale, self.offset, cl.get_color(label), self._rotate_point)
        
            return


    def _draw_all_points(self, painter : QPainter):

        items = dm.data_items

        
        for i, item in enumerate(items): 
            
            if not cl.is_show(item.caseLabel):
                continue

            selected = False

            color = cl.get_color(item.caseLabel)

            if i == dm.current_item_index and not dm.creating_data_item and not dm.creating_split_vertex:
                selected=True

            annotation_frame = AnnotationFrameBase.create(item.annotation_type)
            annotation_frame.draw(painter, self.scale, self.offset, color,self._rotate_point,selected,item.points)

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

    def _is_point_in_pixmap(self, point: QPointF) -> bool:
        """判断点是否在图片范围内"""

        if self.original_pixmap_w_h is None:
            return None
        
        return QPointF(
            max(0, min(point.x(), self.original_pixmap_w_h.width())),
            max(0, min(point.y(), self.original_pixmap_w_h.height())))
    
    def mousePressEvent(self, event): 
        
        if not self.original_pixmap:
            return

        dm.current_item_index = -1
        dm.current_point_index = -1

        current_point = event.pos()

        clamped_point = self._convert_to_original_coords(current_point)

        clamped_point = self._rotate_point_back(clamped_point)

        clamped_point = self._is_point_in_pixmap(clamped_point)
     
        if dm.creating_data_item and event.button() == Qt.LeftButton:
            self._add_create_data_item_point(current_point)
            return

        if dm.shift_pressed and event.button() == Qt.LeftButton:
            self._add_vertex_to_data_item(clamped_point)
            return

        if dm.creating_split_vertex and event.button() == Qt.LeftButton:
            self._add_split_vertex_to_data_item(clamped_point)
            return

        if event.button() == Qt.LeftButton:

            item_idx, vertex_idx = self._check_vertex_click(clamped_point)
            if item_idx != -1 and vertex_idx != -1:
                dm.current_item_index = item_idx
                dm.current_point_index = vertex_idx
                self._dragging_vertex = True 
                self.update()
                return

            item_idx = self._check_item_click(clamped_point)
            if item_idx != -1:
                dm.current_item_index = item_idx
                self._dragging_data_item = True
                self._drag_start_pos = clamped_point
                self._data_item_original_pos = [QPointF(p.x(), p.y()) for p in dm.data_items[item_idx].points]
                self.update()
                return

        super().mousePressEvent(event)

    def _check_poly_edge_click(self,clamped_point) -> tuple:
        """检查是否点击了多边形边"""
        items = dm.data_items
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

    def _check_vertex_click(self, clamped_point:QPointF) -> tuple:
        """检查是否点击了顶点"""

        items = dm.data_items

        threshold = 10 / self.scale

        for i, item in enumerate(items):
            for j, point in enumerate(item.points):

                dist = ((point.x() - clamped_point.x())**2 + (point.y() - clamped_point.y())**2)**0.5 # 计算距离
                if dist < threshold:
                    return (i, j)
        
        return (-1,-1)

    def _check_item_click(self, clamped_point) -> int:

        items = dm.data_items
        
        # 从后往前检查，确保后绘制的多边形优先被选中
        for i, item in enumerate(items):

            item = items[i]
            annotation_frame = AnnotationFrameBase.create(item.annotation_type)
            if annotation_frame.check_click(item.points, clamped_point):
                return i
            
        return -1
            
    def _add_create_data_item_point(self, current_point):
        """添加创建DataItem的顶点"""

        clamped_point = self._convert_to_original_coords(current_point)
        clamped_point = self._rotate_point_back(clamped_point)

        dm.annotion_frame.add_point(clamped_point)
                
        self.update()

    def _add_vertex_to_data_item(self, clamped_point):
        """在DataItem的边上添加顶点"""

        item_idx, best_edge_idx = self._check_poly_edge_click(clamped_point)
        
        if item_idx != -1 and best_edge_idx != -1:
            item = dm.data_items[item_idx]
            item.insert_point(best_edge_idx, clamped_point)
            dm.current_point_index = best_edge_idx
            dm.current_item_index = item_idx
            self.update()
    
    def _add_split_vertex_to_data_item(self, clamped_point):

        def reset_split_state():
            dm.annotion_frame = AnnotationFrameBase.create(AnnotationType.LINE)
            dm.split_point_index_start = -1
            dm.split_point_index_end = -1

            dm.split_item_index = -1

        if dm.split_item_index == -1:
 
            item_idx, _ = self._check_poly_edge_click(clamped_point) # 检查是否点击了多边形的边
            
            if item_idx != -1:
                reset_split_state() 
                self.setCursor(Qt.BlankCursor)

                best_edge_idx,closest_point = Utils.get_closest_point_index_and_edge(dm.data_items[item_idx].points, clamped_point)

                dm.split_point_index_start = best_edge_idx
                dm.split_item_index = item_idx
                dm.annotion_frame.add_point(closest_point)
        
        else:
            item_idx = self._check_item_click(clamped_point)
            if item_idx == -1:
                print("没有点击到多边形")
                best_edge_idx,closest_point = Utils.get_intersection_point(dm.data_items[dm.split_item_index].points, dm.annotion_frame.points[-1], clamped_point)
                if closest_point is None:
                    raise ValueError("未找到与分割线相交的点")
                else:
                    dm.split_point_index_end = best_edge_idx
                    dm.annotion_frame.add_point(closest_point)

                dm.split_vertex_created.emit()
            else:
                dm.annotion_frame.add_point(clamped_point)
        
        self.update()

    def mouseMoveEvent(self, event):

        current_point = event.pos()
        
        if self._dragging_vertex:
            self._drag_vertex(current_point)
            return

        if self._dragging_data_item:
            self._drag_poly(current_point)
            return

        if dm.creating_data_item:
            self._build_annotation_frame(current_point)
            return
        
        if dm.creating_split_vertex and dm.split_item_index != -1:
            self._build_annotation_frame(current_point)
            return

        super().mouseMoveEvent(event)

    def _drag_vertex(self, current_point):
        """拖动顶点"""
        if dm.current_item_index < 0 or dm.current_point_index < 0:
            return
        

        clamped_point = self._convert_to_original_coords(current_point) # 转换为原始坐标

        clamped_point = self._rotate_point_back(clamped_point) # 转换为旋转前的坐标

        clamped_point = self._is_point_in_pixmap(clamped_point) # 限制在图片范围内
        
        
        annotation_frame = AnnotationFrameBase.create(dm.current_data_item.annotation_type)
        annotation_frame.drag_vertex(dm.current_data_item, dm.current_point_index, clamped_point)
        self.update()    

    def _drag_poly(self, current_point):
        """拖动整个多边形"""
        
        if not dm.is_current_data_item_valid():
            return
        

        current_point = self._convert_to_original_coords(current_point) # 转换为原始坐标

        current_point = self._rotate_point_back(current_point)

        dx = current_point.x() - self._drag_start_pos.x()
        dy = current_point.y() - self._drag_start_pos.y()
    
        item = dm.current_data_item

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

        dm.annotion_frame.set_temp_point(clamped_point) 

        self.update()

    def finish_create_frame_coords(self) -> list[QPointF]:

        if not dm.annotion_frame:
            return None
        
        points = dm.annotion_frame.points

        if not dm.annotion_frame.verify_points(points):
            print("多边形坐标数量异常")
            return None
        
        dm.creating_data_item = False
        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)

        #points = Utils.get_rectangle_points(points[0], points[1])

        clipped_points = polygon_clipper.clip_polygon_to_image(points, self.original_pixmap_w_h)
        if clipped_points is None:
            return None
        
        return clipped_points
    

    def finish_split_frame_coords(self) -> list[QPointF]:

        if dm.split_item_index == -1:
            return

        points = dm.data_items[dm.split_item_index].points

        item_data_1 = []

        if dm.split_point_index_start > dm.split_point_index_end:

            item_data_1.extend(points[0:dm.split_point_index_end])
            item_data_1.extend(dm.annotion_frame.points[::-1])
            item_data_1.extend(points[dm.split_point_index_start:])

        elif dm.split_point_index_start == dm.split_point_index_end:
            
            item_data_1.extend(points[0:dm.split_point_index_end])


            if Utils.compare_points_on_line(dm.annotion_frame.points[0],dm.annotion_frame.points[-1],
                                            points[dm.split_point_index_end-1],points[dm.split_point_index_end if dm.split_point_index_end < len(points)-1 else 0])==-1:

                item_data_1.extend(dm.annotion_frame.points)
            else:
                item_data_1.extend(dm.annotion_frame.points[::-1])

            item_data_1.extend(points[dm.split_point_index_end:])
        else :
             item_data_1.extend(points[0:dm.split_point_index_start])
             item_data_1.extend(dm.annotion_frame.points)
             item_data_1.extend(points[dm.split_point_index_end:])

        item_data_2 = []

        if dm.split_point_index_start > dm.split_point_index_end:
            item_data_2.extend(dm.annotion_frame.points)
            item_data_2.extend(points[dm.split_point_index_end:dm.split_point_index_start])
        elif dm.split_point_index_start == dm.split_point_index_end:
            item_data_2 = dm.annotion_frame.points
        else:
            item_data_2.extend(dm.annotion_frame.points[::-1])
            item_data_2.extend(points[dm.split_point_index_start:dm.split_point_index_end])



        dm.delete_data_item_by_index(dm.split_item_index)
        dm.creating_split_vertex = False
        dm.annotion_frame = None    
        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)
        
        return item_data_1,item_data_2

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging_vertex = False
            self._dragging_data_item = False
        super().mouseReleaseEvent(event)


