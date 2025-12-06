
# coding: utf-8
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QPixmap
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPointF

from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageCanvas
from common.utils import Utils

class PolygonsDrawImageCanvas(ImageCanvas):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self._points = {}
        self.all_points = []
        self.all_points_colors = []  
        self.selected_item = -1 
   
    def paintEvent(self, event):

        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        self._draw_all_points(painter)

    
    def _draw_all_points(self, painter : QPainter):
        """绘制多边形（使用你的原始实现）"""
        for i, points in enumerate(self.all_points):
            
            if i < len(self.all_points_colors):
                color = self.all_points_colors[i]
            else:
                color = Utils.generate_random_color()
                self.all_points_colors.append(color)
            # 原始坐标 → 画布坐标
            new_points = [
                QPointF(point.x() * self.scale + self.offset.x(), 
                        point.y() * self.scale + self.offset.y()) 
                for point in points
            ]
            
            painter.setPen(QPen(color, 2))

            transparent_color = QColor(color)

            if i == self.selected_item:
                transparent_color.setAlpha(128)
            else:
                transparent_color.setAlpha(20)

            painter.setBrush(QBrush(transparent_color, Qt.SolidPattern)) # 填充颜色
            
            if len(new_points) >= 3:
                painter.drawPolygon(QPolygonF(new_points)) # 绘制多边形
            
            # 绘制顶点
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            for point in new_points:
                painter.drawEllipse(point, 3, 3)


