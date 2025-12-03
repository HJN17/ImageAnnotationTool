import numpy as np
from PyQt5.QtWidgets import QWidget
from .utils import Utils  
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QPixmap

from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPointF


class ImageCanvas(QWidget):
    """
    图像显示与交互画布组件，提供缩放、平移等基础功能，优化焦点与快捷键处理。
    """

    # 定义快捷键信号，用于与父组件通信
    key_Shift_pressed = pyqtSignal(bool)  # 传递Shift键按下状态
    key_D_pressed = pyqtSignal()  # D键按下信号
    Key_Left_pressed = pyqtSignal()  # 左键 按下信号
    Key_Right_pressed = pyqtSignal()  # 右键 按下信号
    Key_N_pressed = pyqtSignal()  # N键按下信号
    Key_ESCAPE_pressed = pyqtSignal()  # ESC键按下信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.image = None  # 存储原始图像数据（QPixmap）
        self.scaled_image = None  # 存储缩放后的图像数据
        self.scale = 1.0  # 当前图像的缩放比例
        self.offset = QPoint(0, 0)  # 图像显示的偏移量（整数坐标）
        self.dragging = False  # 标记是否正在拖动图像
        self.last_pos = QPoint()  # 记录鼠标拖动的上一个位置
    
        self.markers = {}  # 存储标记点信息
        self.polygons = []  # 存储多边形的顶点信息（原始坐标，未缩放）
        self.poly_colors = []  # 存储每个多边形的颜色
        self.selected_item = -1  # 当前选中的多边形索引，-1 表示未选中
        self.setMinimumSize(400, 300)  # 设置画布的最小尺寸
        
        # 焦点相关设置
        self.setFocusPolicy(Qt.ClickFocus)  # 允许画布通过鼠标点击获取焦点
        self.has_focus = False  # 焦点状态标记

    def init_load_image(self):
        # 计算合适的初始缩放比例，确保图片完全显示在画布中
        if self.image is not None and self.width() > 0 and self.height() > 0 and not self.image.isNull():
            scale_width = self.width() / self.image.width()
            scale_height = self.height() / self.image.height()
            self.scale = min(scale_width, scale_height)
            scaled_width = self.image.width() * self.scale
            scaled_height = self.image.height() * self.scale
            self.offset = QPoint(
                self.width() // 2 - int(scaled_width) // 2,
                self.height() // 2 - int(scaled_height) // 2
            )
        else:
            self.scale = 1.0
            self.offset = QPoint(0, 0)

    def load_image(self, image_path):
        """加载指定路径的图像并更新画布显示"""
        self.image = QPixmap(image_path)
        if self.image.isNull():
            return False
        
        self.init_load_image()
        self.update_scaled_image()
        self.update()
        return True

    def update_scaled_image(self):
        """根据当前缩放比例更新缩放后的图像"""
        if self.image is not None:
            w, h = self.image.width(), self.image.height()
            scaled_h = int(h * self.scale)
            scaled_w = int(w * self.scale)
            self.scaled_image = self.image.scaled(scaled_w, scaled_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        if self.scaled_image is not None:
            painter.drawPixmap(self.offset, self.scaled_image)
        
        self.draw_markers(painter)
        self.draw_polygons(painter)

    def draw_markers(self, painter):
        """绘制标记点"""
        painter.setPen(QPen(Qt.red, 5))
        painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
        for i, marker in self.markers.items():
            if marker is not None:
                x = marker.x() * self.scale + self.offset.x()
                y = marker.y() * self.scale + self.offset.y()
                painter.drawEllipse(QPoint(int(x), int(y)), 5, 5)
                painter.drawText(int(x) + 10, int(y) - 10, str(i + 1))
    
    def draw_polygons(self, painter):
        """绘制多边形（使用你的原始实现）"""
        for i, polygon in enumerate(self.polygons):
            if i < len(self.poly_colors):
                color = self.poly_colors[i]
            else:
                color = self.generate_random_color()
                self.poly_colors.append(color)
            
            # 原始坐标 → 画布坐标
            polygon_points = [
                QPointF(point.x() * self.scale + self.offset.x(), 
                        point.y() * self.scale + self.offset.y()) 
                for point in polygon
            ]
            
            painter.setPen(QPen(color, 2))
            transparent_color = QColor(color)
            if i == self.selected_item:
                transparent_color.setAlpha(128)
            else:
                transparent_color.setAlpha(20)
            painter.setBrush(QBrush(transparent_color, Qt.SolidPattern))
            
            if len(polygon_points) >= 3:
                painter.drawPolygon(QPolygonF(polygon_points))
            
            # 绘制顶点
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            for point in polygon_points:
                painter.drawEllipse(point, 3, 3)

    def generate_random_color(self):
        """生成随机颜色（适配你的Utils）"""
        import random
        return QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 150)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.dragging = True
            self.last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        self.setFocus()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and self.image is not None:
            delta = event.pos() - self.last_pos
            self.offset += delta
            self.last_pos = event.pos()
            self.update()
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton and self.dragging:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if self.image is None:
            return
        if not self.has_focus:
            super().wheelEvent(event)
            return

        scale_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        old_scale = self.scale
        self.scale *= scale_factor
        self.scale = max(0.1, min(self.scale, 5.0))

        mouse_pos = event.pos()
        img_x = (mouse_pos.x() - self.offset.x()) / old_scale
        img_y = (mouse_pos.y() - self.offset.y()) / old_scale

        self.offset.setX(int(mouse_pos.x() - img_x * self.scale))
        self.offset.setY(int(mouse_pos.y() - img_y * self.scale))
        self.update_scaled_image()
        self.update()

    def resizeEvent(self, event):
        self.reset_view()

    def reset_view(self):
        self.init_load_image()
        self.update_scaled_image()
        self.update()

    def focusInEvent(self, event):
        self.has_focus = True
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.has_focus = False
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if not self.has_focus:
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key_Shift:
            self.setCursor(Qt.PointingHandCursor)
            self.key_Shift_pressed.emit(True)
            event.accept()
        elif event.key() == Qt.Key_D:
            self.key_D_pressed.emit()
            event.accept()
        elif event.key() == Qt.Key_Left:
            self.Key_Left_pressed.emit()
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.Key_Right_pressed.emit()
            event.accept()
        elif event.key() == Qt.Key_N:
            self.Key_N_pressed.emit()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            self.Key_ESCAPE_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not self.has_focus:
            super().keyReleaseEvent(event)
            return

        if event.key() == Qt.Key_Shift:
            self.key_Shift_pressed.emit(False)
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().keyReleaseEvent(event)
