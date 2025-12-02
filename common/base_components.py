import numpy as np
from PyQt5.QtWidgets import QWidget
from .utils import Utils  
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QPixmap

from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPointF


class ImageCanvas(QWidget):
    """
    图像显示与交互画布组件，提供缩放、平移等基础功能，优化焦点与快捷键处理。

    该类继承自 QWidget，用于创建一个可显示图像并支持用户交互操作的画布，
    包括图像的缩放、平移，以及多边形标注、顶点操作等功能，同时处理焦点和快捷键事件。
    """

    # 定义快捷键信号，用于与父组件通信
    key_Shift_pressed = pyqtSignal(bool)  # 传递Q键按下状态
    key_D_pressed = pyqtSignal()  # D键按下信号
    Key_Left_pressed = pyqtSignal()  # 左键 按下信号
    Key_Right_pressed = pyqtSignal()  # 右键 按下信号
    Key_N_pressed = pyqtSignal()  # N键按下信号
    Key_ESCAPE_pressed = pyqtSignal()  # ESC键按下信号

    def __init__(self, parent=None):
        """
        初始化 ImageCanvas 类的实例。

        :param parent: 父组件，默认为 None。
        """
        super().__init__(parent)
        self.parent = parent
        self.image = None  # 存储原始图像数据
        self.scaled_image = None  # 存储缩放后的图像数据
        self.scale = 1.0  # 当前图像的缩放比例
        self.offset = QPoint(0, 0)  # 图像显示的偏移量
        self.dragging = False  # 标记是否正在拖动图像
        self.last_pos = QPoint()  # 记录鼠标拖动的上一个位置
    
        self.markers = {}  # 存储标记点信息
        self.polygons = []  # 存储多边形的顶点信息
        self.poly_colors = []  # 存储每个多边形的颜色
        self.scale_changed = pyqtSignal(float)  # 缩放比例改变时发出的信号
        self.selected_item = -1  # 当前选中的多边形索引，-1 表示未选中
        self.setMinimumSize(400, 300)  # 设置画布的最小尺寸
        
        # 焦点相关设置
        self.setFocusPolicy(Qt.ClickFocus)  # 允许画布通过鼠标点击和键盘快捷键获取焦点
        self.has_focus = False  # 焦点状态标记


    def init_load_image(self):
        # 计算合适的初始缩放比例，确保图片完全显示在画布中
        if self.image is not None and self.width() > 0 and self.height() > 0 and not self.image.isNull():

            # 计算宽度和高度方向的缩放比例
            scale_width = self.width() / self.image.width()
            scale_height = self.height() / self.image.height()
            # 取较小的缩放比例，确保图片完全显示
            self.scale = min(scale_width, scale_height)
            # 计算图像显示的初始偏移量（居中显示）
            scaled_width = self.image.width() * self.scale
            scaled_height = self.image.height() * self.scale
            self.offset = QPoint(
                self.width() // 2 - int(scaled_width) // 2,
                self.height() // 2 - int(scaled_height) // 2
            )
        else:
            # 画布尺寸无效时使用默认值
            self.scale = 1.0
            self.offset = QPoint(0, 0)

    def load_image(self, image_path):
        """
        加载指定路径的图像并更新画布显示，确保图片默认完整显示。

        :param image_path: 图像文件的路径。
        :return: 若图像加载成功返回 True，否则返回 False。
        """
        self.image = QPixmap(image_path)
        if self.image.isNull():  # 检查图像是否加载成功
            return False
        
        self.init_load_image()
        
        self.update_scaled_image()  # 更新缩放后的图像
        self.update()  # 重绘画布
        return True

    def update_scaled_image(self):
        """
        根据当前缩放比例更新缩放后的图像。
        """
        if self.image is not None:
            w, h = self.image.width(), self.image.height()
            scaled_h = int(h * self.scale)
            scaled_w = int(w * self.scale)
            self.scaled_image = self.image.scaled(scaled_w, scaled_h, Qt.KeepAspectRatio,Qt.SmoothTransformation)

    def paintEvent(self, event):
        painter = QPainter(self)

        # 开启抗锯齿和图像平滑渲染
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True) 
        

        if self.scaled_image is not None:
            #w ,h= self.scaled_image.width(), self.scaled_image.height()
            #q_image = QImage(self.scaled_image.data, w, h, w * 3, QImage.Format_RGB888)
            
            painter.drawPixmap(
            QPointF(self.offset.x(), self.offset.y()),  # 浮点坐标
            self.scaled_image
        )
        
        self.draw_markers(painter)  # 绘制标记点
        self.draw_polygons(painter)  # 绘制多边形

    def draw_markers(self, painter):
        """
        在画布上绘制标记点。

        :param painter: 绘图对象。
        """
        painter.setPen(QPen(Qt.red, 5))
        painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))# 标记点颜色


        for i, marker in self.markers.items():
            if marker is not None:
                x = marker.x() * self.scale + self.offset.x()
                y = marker.y() * self.scale + self.offset.y()
                painter.drawEllipse(QPoint(x, y), 5, 5)
                painter.drawText(x + 10, y - 10, str(i + 1))
    
    def draw_polygons(self, painter):
        """
        在画布上绘制多边形。

        :param painter: 绘图对象。
        """
       

        for i, polygon in enumerate(self.polygons):
           
            if i < len(self.poly_colors):
                color = self.poly_colors[i]
            else:
                color = Utils.generate_random_color()
                self.poly_colors.append(color)
            
            # 计算多边形顶点在画布上的实际位置（使用浮点坐标提高精度）
            polygon_points = [
                QPointF(point.x() * self.scale + self.offset.x(), 
                        point.y() * self.scale + self.offset.y()) 
                for point in polygon
            ]
            
            painter.setPen(QPen(color, 2))
            
            # 处理填充透明度
            transparent_color = QColor(color)
            if i == self.selected_item:
                transparent_color.setAlpha(128)  # 选中的多边形
            else:
                transparent_color.setAlpha(20)   # 未选中的多边形

            painter.setBrush(QBrush(transparent_color, Qt.SolidPattern))
            
            # 绘制多边形（使用QPolygonF提高精度）
            if len(polygon_points) >= 1:  # 确保至少3个顶点
                painter.drawPolygon(QPolygonF(polygon_points))
            
            # 绘制顶点
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            for point in polygon_points:
                painter.drawEllipse(point, 3, 3)

    def mousePressEvent(self, event):
        """
        处理鼠标按下事件。

        :param event: 鼠标事件对象。
        """
        if event.button() == Qt.RightButton:
            self.dragging = True
            self.last_pos = event.pos() 
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

        self.setFocus()# 鼠标点击画布时获取焦点
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        """
        处理鼠标移动事件。

        :param event: 鼠标事件对象。
        """
        if self.dragging and self.image is not None:
            delta = event.pos() - self.last_pos 
            self.offset += delta  # 更新图像显示的偏移量
            self.last_pos = event.pos()  # 记录当前鼠标位置
            self.update()
            event.accept()
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        处理鼠标释放事件。

        :param event: 鼠标事件对象。
        """
        if event.button() == Qt.RightButton and self.dragging :

            self.dragging = False 
            self.setCursor(Qt.ArrowCursor)
            event.accept()
           
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件，实现图像的缩放功能。

        :param event: 鼠标滚轮事件对象。
        """
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
        self.offset.setY(int(mouse_pos.y() - img_y * self.scale))  # 计算缩放后的图像偏移量
        self.update_scaled_image()
        self.update()
    
    def resizeEvent(self, event):
        """
        处理窗口大小变化事件，更新画布大小。

        :param event: 窗口大小事件对象。
        """
        self.reset_view()

    def reset_view(self):
        """
        重置图像视图，恢复到初始缩放比例和位置。
        """
        self.init_load_image()

        self.update_scaled_image() 
        self.update()

    def focusInEvent(self, event):
        """
        获得焦点时触发，更新焦点状态并重绘画布显示焦点边框。

        :param event: 焦点事件对象。
        """
        self.has_focus = True
        
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """
        失去焦点时触发，更新焦点状态并重绘画布隐藏焦点边框。

        :param event: 焦点事件对象。
        """
        self.has_focus = False
        super().focusOutEvent(event)

   
    def keyPressEvent(self, event):
        """
        处理键盘按键按下事件。

        :param event: 键盘事件对象。
        """
        if not self.has_focus:
            super().keyPressEvent(event)
            return

        # 处理Q键（添加顶点）
        if event.key() == Qt.Key_Shift:
            self.setCursor(Qt.PointingHandCursor)  
            self.key_Shift_pressed.emit(True)
            event.accept()
        # 处理D键（删除顶点）
        elif event.key() == Qt.Key_D:
            self.key_D_pressed.emit() 
            event.accept()

        elif event.key() == Qt.Key_Left:
            self.Key_Left_pressed.emit()
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.Key_Right_pressed.emit() 
            event.accept()
        # 处理N键（多边形）
        elif event.key() == Qt.Key_N:
            self.Key_N_pressed.emit() 
            event.accept()
        # 处理ESC键（取消多边形）
        elif event.key() == Qt.Key_Escape:
            self.Key_ESCAPE_pressed.emit() 
            event.accept()
      

        
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """
        处理键盘按键释放事件。

        :param event: 键盘事件对象。
        """
        if not self.has_focus:
            super().keyReleaseEvent(event)
            return

        # 处理Q键释放
        if event.key() == Qt.Key_Shift:
            self.key_Shift_pressed.emit(False) 

            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().keyReleaseEvent(event)
