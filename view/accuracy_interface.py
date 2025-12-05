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
from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageProgressWidget
from QtUniversalToolFrameWork.components.widgets.label import CommandBarLabel
from QtUniversalToolFrameWork.components.widgets.command_bar import CommandBar

from common.utils import Utils
from components.image_canvas import PolygonsDrawImageCanvas
from common.json_structure_data import DataInfo,DataItemInfo,load_json_data
class OCRAccuracyInterface(QWidget):
    """OCR精度调整工具模块，用于调整OCR识别区域的多边形标注"""


    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ocr_accuracy_interface")

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
        self._drag_start_pos = QPointF()

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
                Action(FIF.DELETE,triggered=self._on_delete_image_clicked,shortcut="Delete"),
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

            
    def _load_annotations(self, json_path):
        """加载标注数据"""

        self.init_vars()

        self._data_info = load_json_data(json_path)
        

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
        
        if self.creating_poly and event.button() == Qt.LeftButton:
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
 
        w = self._image_canvas.width()
        h = self._image_canvas.height()

        clamped_point = QPointF( # 限制在图片范围内
            max(0, min(click_point.x(), w)),
            max(0, min(click_point.y(), h))
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
                self._data_item_original_pos = [QPointF(p.x(), p.y()) for p in points]
    
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
            self.drag_vertex(current_point)
            return

        if self._dragging_data_item:
            self.drag_charset_poly(current_point)
            return

        if self.creating_poly:
            self.preview_create_poly(current_point)
            return

        self._image_canvas.mouseMoveEvent(event)

    def drag_vertex(self, current_point):
        """拖动顶点"""
        if self.selected_charset_index < 0 or self.selected_vertex < 0:
            return

        # 限制在图片范围内
        if self.canvas.image:
            img_width = self.canvas.image.width()
            img_height = self.canvas.image.height()
            clamped_x = max(0, min(current_point.x(), img_width))
            clamped_y = max(0, min(current_point.y(), img_height))
        else:
            clamped_x = current_point.x()
            clamped_y = current_point.y()

        # 更新顶点位置
        charset = self.JsonDataList.all_charsets[self.selected_charset_index]
        charset.poly[self.selected_vertex] = QPointF(clamped_x, clamped_y)

        # 更新UI
        self.vertex_x.setText(f"{clamped_x:.1f}")
        self.vertex_y.setText(f"{clamped_y:.1f}")
        self.update_canvas_polygons()
        self.canvas.update()

    def drag_charset_poly(self, current_point):
        """拖动整个Charset多边形"""
        if self.selected_charset_index < 0:
            return

        # 计算偏移量
        dx = current_point.x() - self.drag_start_pos.x()
        dy = current_point.y() - self.drag_start_pos.y()

        # 限制在图片范围内
        if self.canvas.image:
            img_width = self.canvas.image.width()
            img_height = self.canvas.image.height()
        else:
            img_width = float('inf')
            img_height = float('inf')

        # 更新所有顶点
        charset = self.JsonDataList.all_charsets[self.selected_charset_index]
        new_poly = []
        for i, (orig_p, curr_p) in enumerate(zip(self.poly_original_pos, charset.poly)):
            new_x = orig_p.x() + dx
            new_y = orig_p.y() + dy
            # 限制范围
            new_x = max(0, min(new_x, img_width))
            new_y = max(0, min(new_y, img_height))
            new_poly.append(QPointF(new_x, new_y))

        charset.poly = new_poly
        self.update_canvas_polygons()
        self.canvas.update()

    def preview_create_poly(self, current_point):
        """预览正在创建的多边形"""
        if not self.current_poly:
            return
        original_poly = self.current_poly.copy()
        self.current_poly.append(current_point)
        self.update_canvas_polygons()
        self.canvas.update()
        self.current_poly = original_poly

    def on_canvas_release(self, event):
        """画布释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging_vertex = False
            self.dragging_poly = False
        self.original_mouseReleaseEvent(event)

    def start_create_poly(self):
        """开始创建多边形"""
        self.creating_poly = True
        self.canvas.setMouseTracking(True)
        self.canvas.setCursor(Qt.CrossCursor)
        self.current_poly = []
        self.status_updated.emit("请在图像上点击添加多边形顶点，完成后点击'完成多边形'", "white")

    def finish_create_poly(self):
        """完成创建多边形（添加为新的Charset）"""
        if len(self.current_poly) < 3:
            QMessageBox.warning(self, "警告", "多边形至少需要3个顶点")
            return

        # 创建新的Charset
        new_charset = JsonCharsetInfo(
            poly=self.current_poly.copy(),
            text="",
            confidence=0.0
        )

        # 如果没有DataListInfo，创建一个默认的
        if not self.JsonDataList.data_list:
            default_data_info = JsonDataListInfo(
                id=f"Data_{len(self.JsonDataList.data_list)}",
                text="",
                language="",
                poly=[],
                charsets=[new_charset]
            )
            self.JsonDataList.add_data_list_info(default_data_info)
        else:
            # 添加到最后一个DataListInfo中
            last_data_info = self.JsonDataList.data_list[-1]
            last_data_info.add_charset(new_charset)

        # 更新状态
        self.poly_colors.append(Utils.generate_random_color())
        self.creating_poly = False
        self.current_poly = []
        self.canvas.setMouseTracking(False)
        self.canvas.setCursor(Qt.ArrowCursor)

        # 选中新创建的Charset
        self.selected_charset_index = len(self.JsonDataList.all_charsets) - 1
        self.selected_vertex = -1
        self.canvas.selected_item = self.selected_charset_index

        # 更新画布
        self.update_canvas_polygons()
        self.canvas.poly_colors = self.poly_colors
        self.canvas.update()
        self.update_charset_property_display()
        self.status_updated.emit(f"已创建Charset，共 {len(self.JsonDataList.all_charsets)} 个", "white")

    def cancel_create_poly(self):
        """取消创建多边形"""
        self.creating_poly = False
        self.current_poly = []
        self.canvas.setCursor(Qt.ArrowCursor)
        self.canvas.setMouseTracking(False)
        self.update_canvas_polygons()
        self.canvas.update()
        self.status_updated.emit("已取消新建多边形", "white")

    def delete_selected(self):
        """删除选中的Charset"""
        if self.selected_charset_index < 0 or not self.JsonDataList:
            return

        # 获取选中的Charset及其所属的DataListInfo
        data_info, data_index, charset_subindex = self.JsonDataList.get_charset_by_index(self.selected_charset_index)
        if not data_info:
            return

        # 删除Charset
        data_info.remove_charset(charset_subindex)

        # 如果DataListInfo没有Charset了，删除该DataListInfo
        if not data_info.charsets:
            self.JsonDataList.remove_data_list_info(data_index)

        # 更新颜色列表
        del self.poly_colors[self.selected_charset_index]

        # 更新选中状态
        self.selected_charset_index = -1
        self.selected_vertex = -1
        self.canvas.selected_item = -1

        # 更新画布
        self.update_canvas_polygons()
        self.canvas.poly_colors = self.poly_colors
        self.canvas.update()
        self.update_charset_property_display()
        self.status_updated.emit(f"已删除选中Charset，剩余 {len(self.JsonDataList.all_charsets)} 个", "white")

    def clear_all(self):
        """清空所有Charset和DataListInfo"""
        if not self.JsonDataList or not self.JsonDataList.all_charsets:
            return

        reply = QMessageBox.question(self, "确认", "确定要清空所有标注吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.JsonDataList = JsonDataList(FilePath="", Source="", data_list=[])
            self.init_vars()
            self.update_canvas_polygons()
            self.canvas.update()
            self.status_updated.emit("已清空所有标注", "white")

    def save_annotations(self):

        """保存标注（适配新的JSON层级结构）"""
        if self.current_index < 0 or not self.file_pairs or not self.JsonDataList:
            return
        
        json_path = self.file_pairs[self.current_index]['json']
        image_path = self.file_pairs[self.current_index]['image']

        # 构建JSON数据
        json_data = {
            "FilePath": os.path.basename(image_path),
            "Source": self.JsonDataList._Source,
            "DataList": []
        }

        # 遍历每个DataListInfo
        for data_info in self.JsonDataList.data_list:
            data_item = {
                "id": data_info.id,
                "text": data_info.text,
                "language": data_info.language,
                "poly": [[p.x(), p.y()] for p in data_info.poly],
                "charsets": []
            }

            # 遍历每个Charset
            for charset in data_info.charsets:
                data_item["charsets"].append({
                    "poly": [[[p.x(), p.y()] for p in charset.poly]],
                    "text": charset.text,
                    "confidence": charset.confidence
                })

            json_data["DataList"].append(data_item)

        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            self.status_updated.emit("标注已保存", "green")
        except Exception as e:
            self.status_updated.emit(f"保存标注失败: {str(e)}", "red")


    def update_poly_text(self):
        """更新选中Charset的文本"""
        if self.selected_charset_index < 0 or not self.JsonDataList:
            return

        charset = self.JsonDataList.all_charsets[self.selected_charset_index]
        charset.text = self.poly_text.text()
        self.status_updated.emit("Charset文本已更新", "white")

    def update_poly_language(self):
        """更新选中Charset所属DataListInfo的语言"""
        if self.selected_charset_index < 0 or not self.JsonDataList:
            return

        data_info, _, _ = self.JsonDataList.get_charset_by_index(self.selected_charset_index)
        if data_info:
            data_info.language = self.poly_lang.text()
            self.status_updated.emit("语言已更新", "white")

    
    def apply_vertex_coords(self):
        """应用顶点坐标修改"""
        if self.selected_charset_index < 0 or self.selected_vertex < 0 or not self.JsonDataList:
            return

        try:
            x = float(self.vertex_x.text())
            y = float(self.vertex_y.text())

            # 限制在图片范围内
            if self.canvas.image:
                x = max(0, min(x, self.canvas.image.width()))
                y = max(0, min(y, self.canvas.image.height()))

            # 更新顶点
            charset = self.JsonDataList.all_charsets[self.selected_charset_index]
            charset.poly[self.selected_vertex] = QPointF(x, y)

            # 更新画布
            self.update_canvas_polygons()
            self.canvas.update()
            self.status_updated.emit("顶点坐标已更新", "white")
        except ValueError:
            self.status_updated.emit("顶点坐标必须是数字", "red")

    
    def on_d_pressed(self):
        """删除选中的顶点"""
        if self.selected_charset_index < 0 or self.selected_vertex < 0 or not self.JsonDataList:
            return

        charset = self.JsonDataList.all_charsets[self.selected_charset_index]
        if len(charset.poly) <= 3:
            QMessageBox.warning(self, "警告", "多边形至少需要3个顶点")
            return

        # 删除顶点
        charset.remove_poly(self.selected_vertex)
        self.selected_vertex = -1
        self.vertex_idx.clear()
        self.vertex_x.clear()
        self.vertex_y.clear()

        # 更新画布
        self.update_canvas_polygons()
        self.canvas.update()
        self.status_updated.emit("已删除顶点", "white")

    def on_shift_pressed(self, pressed):
        self.shift_pressed = pressed
        if pressed:
            self.status_updated.emit("Shift键已按下，点击Charset边缘添加顶点", "white")
        else:
            self.status_updated.emit("Shift键已释放", "white")

    def on_Key_N_pressed(self):
        if not self.creating_poly:
            self.start_create_poly()
        else:
            self.finish_create_poly()

    def on_Key_ESCAPE_pressed(self):
        self.cancel_create_poly()
    
    def on_Key_Left_pressed(self):
        if self.file_pairs and self.current_index > 0:
            self.save_annotations()
            self.current_index -= 1
            self.load_current_file()

    def on_Key_Right_pressed(self):
        if self.file_pairs and self.current_index < len(self.file_pairs) - 1:
            self.save_annotations()
            self.current_index += 1
            self.load_current_file()
    
    def toggle_polygons_visibility(self):
        """切换多边形显示/隐藏"""
        self.show_polygons = not self.show_polygons
        self.update_canvas_polygons()
        self.canvas.update()
        status = "已显示" if self.show_polygons else "已隐藏"
        self.status_updated.emit(f"{status}多边形", "white")
            
    
    


    def delete_annotations(self):
        """删除当前图片和JSON文件"""
        if self.current_index < 0 or not self.file_pairs:
            return

        reply = QMessageBox.question(self, "确认", "确定要删除当前图片和JSON文件吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            file_pair = self.file_pairs[self.current_index]
            delete_path = os.path.join(os.path.dirname(file_pair['image']), 'deleted')
            os.makedirs(delete_path, exist_ok=True)

            # 移动文件
            shutil.move(file_pair['json'], os.path.join(delete_path, os.path.basename(file_pair['json'])))
            shutil.move(file_pair['image'], os.path.join(delete_path, os.path.basename(file_pair['image'])))
            
            # 更新文件列表
            self.file_pairs.pop(self.current_index)
            self.init_vars()

            # 加载下一个文件
            self.current_index = max(0, self.current_index - 1)
            if self.file_pairs:
                self.load_current_file()
            else:
                self.canvas.clear()

            self.status_updated.emit("已删除当前图像的标注", "white")



    def go_to_image(self):
        """跳转图片"""
        try:
            index = int(self.go_text.text()) - 1
            if 0 <= index < len(self.file_pairs):
                self.current_index = index
                self.load_current_file()
                self.status_updated.emit(f"跳转至第 {index + 1} 张图片", "white")
            else:
                self.status_updated.emit("图片索引无效", "red")
        except ValueError:
            self.status_updated.emit("请输入有效的数字", "red")

    def reset_labels(self):
        """重置数据"""
        if self.current_index >= 0 and self.file_pairs:
            self.load_annotations(self.file_pairs[self.current_index]['json'])

    def reset_view(self):
        """重置视图"""
        self.canvas.reset_view()


    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_C and self.creating_poly:
            self.cancel_create_poly()
        elif event.key() == Qt.Key_S:
            self.toggle_polygons_visibility()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        """滚轮缩放"""
        self.canvas.wheelEvent(event)
        self.scale_updated.emit(self.canvas.scale)


 
    
    
        
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


    def closeEvent(self, event):
        """关闭事件"""
        self.settings.setValue("ocr_accuracy_tool_images_dir", self.images_dir.text())
        self.settings.setValue("ocr_accuracy_tool_jsons_dir", self.jsons_dir.text())
        super().closeEvent(event)




