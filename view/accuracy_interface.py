import os
from natsort import natsorted
import shutil
import json
from PyQt5.QtCore import Qt, QPoint, QPointF, pyqtSlot,QRegExp
from PyQt5.QtGui import QPolygonF,QColor,QPixmap
from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, 
                           QGroupBox, QFileDialog, QMessageBox,QTextBrowser,QDialog)

from QtUniversalToolFrameWork.common.image_utils import ImageManager,get_image_paths
from QtUniversalToolFrameWork.common.icon import Action,FluentIcon as FIF
from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageProgressWidget,ImageSearchFlyoutView
from QtUniversalToolFrameWork.components.widgets.label import CommandBarLabel
from QtUniversalToolFrameWork.components.widgets.command_bar import CommandBar
from QtUniversalToolFrameWork.components.widgets.info_bar import InfoBar,InfoBarPosition
from QtUniversalToolFrameWork.components.widgets.flyout import Flyout,FlyoutAnimationType


from common.utils import Utils
from components.image_canvas import PolygonsDrawImageCanvas
from common.json_structure_data import DataInfo,DataItemInfo,load_json_data,AnnotationType,save_json_data


class AccuracyInterface(QWidget):
    """OCR精度调整工具模块，用于调整OCR识别区域的多边形标注"""


    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("accuracy_interface")

        self._progress_widget = ImageProgressWidget(self)
        self._image_manager = ImageManager(self)
        self._image_canvas = PolygonsDrawImageCanvas(self)
        self._image_name_label = CommandBarLabel(self)
        self._commandBar = self.createCommandBar()
        
        self._current_dir = ""
        self._shift_pressed = False
        self._n_pressed = False
        
        self._show_data_items = True  # 默认显示DataItem

        self.init_ui()
        self.init_vars()

    def init_vars(self):
        self._data_info = None  # 根数据对象

        self._current_data_index = -1  # 当前选中的DataItem索引

        self._creating_data_item = False # 是否正在创建DataItem
        self._current_create_data_item = []  # 当前正在创建的DataItem（QPointF列表）
        
        self._current_point_index = -1  # 当前选中的点索引

        self._dragging_vertex = False
        self._dragging_data_item = False # 是否正在拖动DataItem

        self._drag_start_pos = QPointF() # 拖动开始位置

        self._data_item_original_pos = [] # 每个DataItem的原始位置（QPointF列表）
        self._data_item_colors = []  # 每个DataItem的颜色


    def init_ui(self):
        """初始化UI"""
        vBoxLayout = QVBoxLayout(self)
        vBoxLayout.setContentsMargins(10, 10, 10, 10)
        vBoxLayout.setAlignment(Qt.AlignTop) 

        self._image_name_label.setContentsMargins(20, 0, 0, 0)

        vBoxLayout.addWidget(self._commandBar,0,Qt.AlignHCenter)
        vBoxLayout.setSpacing(10)
        vBoxLayout.addWidget(self._image_canvas,1)
        vBoxLayout.addWidget(self._image_name_label,0,Qt.AlignLeft)

    @property
    def current_data_index(self):
        return self._current_data_index
    
    @current_data_index.setter
    def current_data_index(self, index):
        
        if index < 0 or index >= len(self._data_info.items):
            return
        
        if self._current_data_index == index:
            return

        self._current_data_index = index
        self._current_point_index = -1  # 重置当前点索引
        self._update_canvas_data_items()


    def createCommandBar(self):
            bar = CommandBar(self)
            bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

            bar.addActions([
                Action(FIF.ADD, "加载", triggered=self._on_folder_path_changed),
                Action(FIF.EDIT, "标签", checkable=True),
            ])

            bar.addSeparator()
            
            bar.addActions([
                Action(FIF.LEFT_ARROW,triggered=self._image_manager.previous,shortcut="Left"),
                Action(FIF.RIGHT_ARROW,triggered=self._image_manager.next,shortcut="Right"),
            ])

            bar.addWidget(self._progress_widget)

            bar.addActions([
                Action(FIF.SEARCH,triggered=self._on_search_clicked),
            ])

            bar.addSeparator()

            bar.addActions([
                Action(FIF.ROTATE,triggered=self._image_canvas.rotate_image,shortcut="R"),
                Action(FIF.ZOOM_IN,triggered=self._image_canvas.zoom_in),
                Action(FIF.ZOOM_OUT,triggered=self._image_canvas.zoom_out),
                Action(FIF.DELETE,triggered=self._on_delete_image_and_annotations_clicked,shortcut="Delete"),
            ])
            return bar
    
    def _on_folder_path_changed(self,):

        folder = QFileDialog.getExistingDirectory(
            self, "选择图像文件夹", self._current_dir or "./",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if folder:
            self._current_dir = folder
            image_paths = get_image_paths(self._current_dir)
            self._image_manager.set_items(image_paths)
    
            
    @pyqtSlot(QPixmap)
    def _display_current_image(self, pixmap: QPixmap):
        if not pixmap:
            return

        self._image_canvas.load_pixmap(pixmap)
        self._image_name_label.setText(self._image_manager.current_item)

            
    def _load_annotations(self):
        """加载标注数据"""

        self.init_vars()

        image_name = os.path.basename(self._image_manager.current_item)
        json_path = os.path.join(os.path.dirname(self._image_manager.current_item), f"{image_name.split('.')[0]}.json")
        try:
            self._data_info = load_json_data(json_path)

        except Exception:
            self._data_info = DataInfo(file_name=image_name, items=[])

        # 更新画布显示
        self._update_canvas_data_items()

        # 自动选中第一个DataItem
        if self._data_info and self._data_info.items:
            self.selected_charset_index = 0
            self._update_data_item_property_display()
                
 
            
    def _update_canvas_data_items(self):
        """更新画布上的DataItem（只显示DataItem的points）"""
        if not self._data_info or not self._data_info.items:
            self._image_canvas.all_points = []
            self._image_canvas.update()
            return

        if self._show_data_items:

            self._image_canvas.selected_item = self.current_data_index

            # 显示所有DataItem + 当前正在创建的DataItem
            if self._creating_data_item and self._current_create_data_item:

                self._image_canvas.all_points = self._data_info.all_items_points() + [self._current_create_data_item]

                self._image_canvas.all_points_colors = self._data_item_colors + [QColor(0, 255, 255, 150)]
            else:
                self._image_canvas.all_points = self._data_info.all_items_points()
                self._image_canvas.all_points_colors = self._data_item_colors
        else:
            self._image_canvas.all_points = []

        self._image_canvas.update()

    def _update_data_item_property_display(self):
        """更新选中DataItem的属性显示"""
        if self.selected_charset_index < 0 or not self._data_info or not self._data_info.items:
            return

    def mousePressEvent(self, event): 

        if not self._data_info or not self._data_info.items:
            self._image_canvas.mousePressEvent(event)
            return

        # 转换坐标到图像坐标系
        x = (event.pos().x() - self._image_canvas.offset.x()) / self._image_canvas.scale
        y = (event.pos().y() - self._image_canvas.offset.y()) / self._image_canvas.scale
        
        click_point = QPointF(x, y)
        
        if self._creating_data_item and event.button() == Qt.LeftButton:
            self._add_create_data_item_vertex(click_point)
            return

        if self._shift_pressed and event.button() == Qt.LeftButton:
            self._add_vertex_to_data_item(click_point)
            return


        if event.button() == Qt.LeftButton:
            
            self._check_vertex_click(click_point)

            if self._dragging_vertex:
                return

           
            self._check_poly_click(click_point)

            if self._dragging_data_item:
                return

            self.current_data_index = -1
            self._current_point_index = -1

        self._image_canvas.mousePressEvent(event)


    def _add_create_data_item_vertex(self, click_point):
        """添加创建DataItem的顶点"""
 
        clamped_point = QPointF( # 限制在图片范围内
            max(0, min(click_point.x(), self._image_canvas.width())),
            max(0, min(click_point.y(), self._image_canvas.height()))
        )

        self._current_create_data_item.append(clamped_point)
        self._update_canvas_data_items()
        self._image_canvas.update()

    def _check_vertex_click(self, click_point):
        """检查是否点击了顶点"""
        items = self._data_info.items
        threshold = 10 / self._image_canvas.scale

        for i, item in enumerate(items):
            for j, point in enumerate(item.points):
                dist = ((point.x() - click_point.x())**2 + (point.y() - click_point.y())**2)**0.5 # 计算距离
                if dist < threshold:
                  
                    self.current_data_index = i
                    self._current_point_index = j
                    self._dragging_vertex = True # 拖动顶点

    def _check_poly_click(self, click_point):
        """检查是否点击了多边形内部"""
        items = self._data_info.items

        for i, item in enumerate(items):
            
            points = item.points

            if not points:
                continue

            polyf = QPolygonF(points) # 转换为QPolygonF

            if polyf.containsPoint(click_point, Qt.OddEvenFill): # 检查是否点击了多边形内部
                # 选中该DataItem
                self.current_data_index = i
                self._current_point_index = -1
                self._dragging_data_item = True
                self._drag_start_pos = click_point
                self._data_item_original_pos = points
    
    def _add_vertex_to_data_item(self, click_point):
        """在DataItem的边上添加顶点"""
    
        threshold = 2 / self._image_canvas.scale
        item_idx = -1 
        best_edge_idx = -1 
        min_dist = float("inf") # 最小距离，用于判断点击是否在边的附近

        for i, item in enumerate(self._data_info.items):
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
            item = self._data_info.items[item_idx]
            item.insert_point(best_edge_idx, click_point)
            self._current_point_index = best_edge_idx
            self._image_canvas.selected_item = item_idx

            self._update_canvas_data_items()
            self._image_canvas.update()

    def mouseMoveEvent(self, event):
        if not self._dragging_vertex and not self._dragging_data_item:
            self._image_canvas.mouseMoveEvent(event)
            return

        x = (event.pos().x() - self._image_canvas.offset.x()) / self._image_canvas.scale
        y = (event.pos().y() - self._image_canvas.offset.y()) / self._image_canvas.scale

        current_point = QPointF(x, y)

        if self._dragging_vertex:
            self._drag_vertex(current_point)
            return

        if self._dragging_data_item:
            self._drag_charset_poly(current_point)
            return

        if self._creating_data_item:

            self._preview_create_poly(current_point)



            return

        self._image_canvas.mouseMoveEvent(event)

    def _drag_vertex(self, current_point):
        """拖动顶点"""
        if self.current_data_index < 0 or self._current_point_index < 0:
            return

       
        clamped_point = QPointF( # 限制在图片范围内
            max(0, min(current_point.x(), self._image_canvas.width())),
            max(0, min(current_point.y(), self._image_canvas.height()))
        )
       
        item = self._data_info.items[self.current_data_index]
        item.points[self._current_point_index] = clamped_point

        self._update_canvas_data_items()    

    def _drag_charset_poly(self, current_point):
        """拖动整个Charset多边形"""
        if self.current_data_index < 0:
            return

       
        dx = current_point.x() - self._drag_start_pos.x()
        dy = current_point.y() - self._drag_start_pos.y()

        item = self._data_info.items[self.current_data_index]
        new_poly = []
        for point in item.points:
            new_x = point.x() + dx
            new_y = point.y() + dy
            new_x = max(0, min(new_x, self._image_canvas.width()))
            new_y = max(0, min(new_y, self._image_canvas.height()))
            new_poly.append(QPointF(new_x, new_y))

        item.points = new_poly
        self._update_canvas_data_items()

    def _preview_create_poly(self, current_point):
        
        if not self._creating_data_item:
            return
        
        original_points= self._current_create_data_item.copy()
        self._current_create_data_item.append(current_point)
        self._update_canvas_data_items()
        self._current_create_data_item = original_points

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging_vertex = False
            self._dragging_data_item = False
        self._image_canvas.mouseReleaseEvent(event)

    def _start_create_data_item(self):
        """开始创建DataItem"""
        self._creating_data_item = True
        self.setMouseTracking(True) # 开启鼠标跟踪，用于预览创建的多边形
        self.setCursor(Qt.CrossCursor)
        self._current_create_data_item = []

    def _finish_create_data_item(self):
        """完成创建DataItem（添加为新的DataItem）"""
        if len(self._current_create_data_item) < 3:
            print("DataItem至少需要3个顶点")
            return

        new_data_item = DataItemInfo(
            text="",
            language="",
            annotation_type=AnnotationType.DEFAULT,
            caseLabel="default",
            points=self._current_create_data_item.copy()
        )

        self._data_info.items.append(new_data_item)

        self._creating_data_item = False
        self._current_create_data_item = []
        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)

        self.current_data_index = len(self._data_info.items) - 1
        self._current_point_index = -1

        self._update_canvas_data_items()
        self._update_data_item_property_display()

    def _cancel_create_data_item(self):
        """取消创建DataItem"""
        self._creating_data_item = False
        self._current_create_data_item = []
        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)
        self._update_canvas_data_items()

    def _delete_selected_data_item(self):
        """删除选中的DataItem"""
        if self.current_data_index < 0 or not self._data_info.items:
            return
        
        del self._data_info.items[self.current_data_index]

        self.current_data_index = -1
        self._current_point_index = -1

        self._update_canvas_data_items()
        self._update_data_item_property_display()
        
    def _clear_all_data_items(self):
        if not self._data_info or not self._data_info.items:
            return

        self._data_info.items = []
        self.init_vars()
        self._update_canvas_data_items()

    def _save_annotations(self):

        if self.current_data_index < 0 or not self._data_info or not self._data_info.items:
            return
        
        image_name = os.path.basename(self._image_manager.current_item)
        json_path = os.path.join(os.path.dirname(self._image_manager.current_item), f"{image_name.split('.')[0]}.json")

        self._data_info.file_name = image_name
        self._data_info.label = ""
        self._data_info.issues = ""

        try:
            save_json_data(json_path, self._data_info)
        except Exception as e:
            print(f"保存标注失败: {str(e)}")
            return


    def _on_d_pressed(self):
        if self.current_data_index < 0 or self._current_point_index < 0 or not self._data_info or not self._data_info.items:
            return
        
        item = self._data_info.items[self.current_data_index]
        if len(item.points) <= 3:
            print("DataItem至少需要3个顶点")
            return

        item.remove_point(self._current_point_index)
        self.selected_vertex = -1
        self._update_canvas_data_items()


    def _on_shift_pressed(self, pressed):

        self.shift_pressed = pressed

        if pressed:
            print("Shift键已按下，点击Charset边缘添加顶点") 
            self.setCursor(Qt.PointingHandCursor)
        else:
            print("Shift键已释放")
            self.setCursor(Qt.ArrowCursor)

    def _on_n_pressed(self):
        if not self._creating_data_item:
            self._start_create_data_item()
            print("开始创建DataItem")
        else:
            self._finish_create_data_item()
            print("完成创建DataItem")

    def _on_escape_pressed(self):
        self._cancel_create_data_item()
        print("取消创建DataItem")
        

    def _toggle_polygons_visibility(self):
        """切换多边形显示/隐藏"""

        self.show_polygons = not self.show_polygons

        if self.show_polygons:
            self._update_canvas_data_items()
    

    @pyqtSlot(QPixmap)
    def _display_current_image(self, pixmap: QPixmap):
        if not pixmap:
            return

        self._image_canvas.load_pixmap(pixmap)
        self._image_name_label.setText(self._image_manager.current_item)

    @pyqtSlot(int)
    def _on_progress_changed(self, value: int):
        self._image_manager.go_to(value-1)
    

    def _on_search_clicked(self):

        if not self._image_manager.items:
            return

        searchFlyoutView = ImageSearchFlyoutView()
        searchFlyoutView.searchSignal.connect(self._on_search_signal)
        searchFlyoutView.set_stands([os.path.basename(p) for p in self._image_manager.items])
        Flyout.make(view = searchFlyoutView,
                    target = self._commandBar,
                    parent = self,
                    aniType = FlyoutAnimationType.DROP_DOWN)
        

    @pyqtSlot(str)
    def _on_search_signal(self, search_text: str):
        if search_text:
            try:
                image_index = self._image_manager.items.index(os.path.join(self._current_dir, search_text))    
            except ValueError:
                print(f"未找到图像 {search_text}")
                return
                
            self._image_manager.go_to(image_index)

        
    
    def _on_delete_image_and_annotations_clicked(self):
        if not self._image_manager.items or self._image_manager.current_index == -1:
            return
        
        image_name = os.path.basename(self._image_manager.current_item)

        dir_name = os.path.dirname(self._image_manager.current_item)

        json_path = os.path.join(dir_name, f"{image_name.split('.')[0]}.json")

        delete_path = os.path.join(dir_name, 'deleted')
        
        os.makedirs(delete_path, exist_ok=True)

        try:
            shutil.move(self._image_manager.current_item, os.path.join(delete_path, image_name))

            if os.path.exists(json_path):
                shutil.move(json_path, os.path.join(delete_path, image_name.split('.')[0] + '.json'))

            self._image_manager.delete_current()

            print(f"删除成功")
        except Exception as e:
            print(f"删除失败, 原因: {str(e)}")
            return
        
        
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._commandBar:
            self._commandBar.setFixedWidth(min(self._commandBar.suitableWidth(), self.width()-20))
            self._commandBar.updateGeometry()

  
    def _show_info_message(self, title: str, content: str):
        InfoBar.info(
            title=title, content=content, orient=Qt.Horizontal,
            isClosable=True, position=InfoBarPosition.TOP_RIGHT,
            duration=2000, parent=self
        )

    def _show_error_message(self, title: str, content: str):
        InfoBar.error(
            title=title, content=content, orient=Qt.Horizontal,
            isClosable=True, position=InfoBarPosition.TOP_RIGHT,
            duration=3000, parent=self
        )


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self._creating_data_item:
            self._cancel_create_data_item()
            return
        
        if event.key() == Qt.Key_N:
            self._on_n_pressed()
            return
        
        if event.key() == Qt.Key_Shift:
            self._on_shift_pressed(True)
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):

        if event.key() == Qt.Key_Shift:
            self._on_shift_pressed(False)
            return
        
        super().keyReleaseEvent(event)

    def show_shortcut_help(self):
        """显示快捷键说明弹窗"""
        class ShortcutDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("快捷键说明")
                self.setMinimumSize(600, 400)
                self.setModal(True)
                
                self.setStyleSheet("""
                    QDialog { background-color: #f5f5f5; font-family: 'Segoe UI', Arial, sans-serif; }
                    QTextBrowser {
                        background-color: white;
                        border: 1px solid #ddd;
                        border-radius: 6px;
                        padding: 15px;
                        font-size: 14px;
                        line-height: 1.6;
                    }
                    QPushButton {
                        background-color: #4CAF50; color: white; border: none;
                        border-radius: 4px; padding: 8px 16px; font-size: 14px; min-width: 80px;
                    }
                    QPushButton:hover { background-color: #45a049; }
                    QPushButton:pressed { background-color: #3d8b40; }
                """)
                
                layout = QVBoxLayout(self)
                text_browser = QTextBrowser()
                
                shortcut_content = """
                <style>
                    h3 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-top: 20px; margin-bottom: 15px; }
                    ul { color: #2c3e50; margin: 10px 0; padding-left: 25px; }
                    li { margin: 8px 0; }
                    b { color: #e74c3c; }
                </style>
                
                <h3>一、基础操作快捷键</h3>
                <ul>
                    <li><b>N键开始</b>：新建Charset多边形</li>
                    <li><b>N键结束</b>：完成Charset多边形</li>
                    <li><b>ESC键</b>：取消新建多边形</li>
                    <li><b>DEL键</b>：删除选中的Charset</li>
                    <li><b>CTRL+S</b>：保存当前标注</li>
                    <li><b>S键</b>：切换多边形显示/隐藏</li>
                    <li><b>SPACE键</b>：重置视图（居中显示）</li>
                    <li><b>SHIFT键（长按）</b>：添加顶点（点击Charset边缘）</li>
                    <li><b>D键</b>：删除选中顶点（需先选中顶点）</li>
                    <li><b>LEFT键</b>：切换到上一张图片（自动保存）</li>
                    <li><b>RIGHT键</b>：切换到下一张图片（自动保存）</li>
                </ul>
                
                <h3>二、鼠标操作</h3>
                <ul>
                    <li><b>左键点击</b>：
                        <ul>
                            <li>新建多边形时：添加顶点</li>
                            <li>选中顶点时：拖动调整顶点位置</li>
                            <li>选中Charset内部：拖动整个Charset</li>
                        </ul>
                    </li>
                    <li><b>右键拖动</b>：平移画布</li>
                    <li><b>鼠标滚轮</b>：缩放画布</li>
                </ul>
                """
                text_browser.setHtml(shortcut_content)
                
                close_btn = QPushButton("关闭")
                close_btn.clicked.connect(self.accept)
                
                layout.addWidget(text_browser)
                layout.addWidget(close_btn, alignment=Qt.AlignRight | Qt.AlignBottom)
        
        dialog = ShortcutDialog(self)
        dialog.exec_()




