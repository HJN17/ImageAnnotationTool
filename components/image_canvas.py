# coding: utf-8

from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPointF,pyqtSlot

from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageCanvas

from common.case_label import cl
from common.data_control_manager import dm

class PolygonsDrawImageCanvas(ImageCanvas):


    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._scale = 1.0
        self._dragging_vertex = False
        self._dragging_data_item = False # 是否正在拖动DataItem
        self._drag_start_pos = QPointF() # 拖动开始位置
        self._data_item_original_pos = [] # 每个DataItem的原始位置（QPointF列表）
        dm.update_data_item.connect(self.update)
        cl.update_label_changed.connect(self.update)

        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)

        self.scaleSignal.connect(self._update_scale)


    def _update_scale(self, scale: float):
        dm.scale = scale

    def paintEvent(self, event):

        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        dm.draw(painter, self.offset,self._rotate_point)
        
        dm.temp_frame_draw(painter, self.offset,self._rotate_point)
        


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

        original_point = self._convert_to_original_coords(current_point)

        rotated_point = self._rotate_point_back(original_point)

        clamped_point = self._is_point_in_pixmap(rotated_point)
     
        if dm.creating_data_item and event.button() == Qt.LeftButton:
            dm.add_create_vertex(rotated_point)
            return

        if dm.shift_pressed and event.button() == Qt.LeftButton:
            dm.add_vertex(clamped_point)
            return

        if dm.creating_split_vertex and event.button() == Qt.LeftButton:
            dm.add_split_vertex(clamped_point)
            return

        if event.button() == Qt.LeftButton:

            is_click,item_idx, vertex_idx = dm.check_vertex_click(clamped_point)
            if is_click:
                dm.current_item_index = item_idx
                dm.current_point_index = vertex_idx
                self._dragging_vertex = True 
                self.update()
                return

            is_click,item_idx = dm.check_frame_click(clamped_point)
            if is_click:
                dm.current_item_index = item_idx
                self._dragging_data_item = True
                self._drag_start_pos = clamped_point
                self._data_item_original_pos = [QPointF(p.x(), p.y()) for p in dm.data_items[item_idx].points]
                self.update()
                return

        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):

        current_point = event.pos()

        original_point = self._convert_to_original_coords(current_point)

        rotated_point = self._rotate_point_back(original_point)

        clamped_point = self._is_point_in_pixmap(rotated_point)


        if self._dragging_vertex:
            self._drag_vertex(clamped_point)
            return

        if self._dragging_data_item:
            self._drag_frame(rotated_point)
            return

        if dm.creating_data_item:
            dm.add_temp_frame_point(rotated_point)
            return
        
        if dm.creating_split_vertex and dm.split_item_index != -1:
            dm.add_temp_frame_point(rotated_point)
            return

        super().mouseMoveEvent(event)

    def _drag_vertex(self, clamped_point):
   
        dm.current_data_item.annotation.drag_vertex(dm.current_data_item, dm.current_point_index, clamped_point)
        
        self.update()    


    def _drag_frame(self, clamped_point):
        """拖动整个多边形"""

        item = dm.current_data_item
        
        dx = clamped_point.x() - self._drag_start_pos.x()
        dy = clamped_point.y() - self._drag_start_pos.y()
    
        new_points = []
        for point in self._data_item_original_pos:
            new_x = point.x() + dx
            new_y = point.y() + dy

            clamped_point = self._is_point_in_pixmap(QPointF(new_x, new_y))
            new_points.append(clamped_point)

        item.points = new_points
        self.update()

    def get_origin_image_size(self) -> QSize:
        return self.original_pixmap_w_h

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging_vertex = False
            self._dragging_data_item = False
        super().mouseReleaseEvent(event)


