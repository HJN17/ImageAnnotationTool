import os
from natsort import natsorted
import shutil
import copy 
import time
from PyQt5.QtCore import Qt, QPoint, QPointF, pyqtSlot,pyqtSignal
from PyQt5.QtGui import QPolygonF,QColor,QPixmap
from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, 
                           QGroupBox, QFileDialog, QMessageBox,QTextBrowser,QDialog)

from QtUniversalToolFrameWork.common.image_utils import ImageManager,get_image_paths
from QtUniversalToolFrameWork.common.icon import Action,FluentIcon as FIF
from QtUniversalToolFrameWork.common.cursor import CursorStyle,cursor
from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageProgressWidget,ImageSearchFlyoutView
from QtUniversalToolFrameWork.components.widgets.label import CommandBarLabel
from QtUniversalToolFrameWork.components.widgets.command_bar import CommandBar
from QtUniversalToolFrameWork.components.widgets.info_bar import InfoBar,InfoBarPosition
from QtUniversalToolFrameWork.components.widgets.flyout import Flyout,FlyoutAnimationType


from common.utils import Utils
from components.image_canvas import PolygonsDrawImageCanvas
from common.json_structure_data import DataInfo,DataItemInfo,jsonFileManager
from common.annotation import AnnotationType,AnnotationFrameBase



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
        
        self._data_info = None
        self._current_dir = ""


        self._progress_widget.progress.connect(self._on_progress_changed)
        self._image_manager.image_loaded.connect(self._display_current_image)
        self._image_manager.current_item_changed.connect(self._set_progress_value)
        self._image_manager.skip_previous_item.connect(self._save_annotations)
        self._image_manager.item_deleted.connect(self._set_progress_range)
        self._image_manager.item_inserted.connect(self._set_progress_range)
        self._image_manager.model_reset.connect(self._set_progress_range)




        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        vBoxLayout = QVBoxLayout(self)
        vBoxLayout.setContentsMargins(10, 30, 10, 10)
        vBoxLayout.setAlignment(Qt.AlignTop) 

        self._progress_widget.set_slider_width(200)

        self._image_name_label.setContentsMargins(20, 0, 0, 0)

        vBoxLayout.addWidget(self._commandBar,0,Qt.AlignHCenter)
        vBoxLayout.setSpacing(20)
        vBoxLayout.addWidget(self._image_canvas,1)
        vBoxLayout.setSpacing(20)
        vBoxLayout.addWidget(self._image_name_label,0,Qt.AlignLeft)

    def _set_progress_range(self):
        self._progress_widget.set_slider_range(1, self._image_manager.count)
        
    def _set_progress_value(self):
        self._progress_widget.set_slider_value(self._image_manager.current_index+1)

    def createCommandBar(self):
            bar = CommandBar(self)
            bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            
            self._show_annotations_action = Action(FIF.TAG, "标注", checkable=True,triggered=self._on_show_annotations_toggled,shortcut="S")

            bar.addActions([
                Action(FIF.ADD, "加载", triggered=self._on_folder_path_changed),
                self._show_annotations_action,
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
                Action(FIF.ZOOM_OUT,triggered=self._delete_selected_data_item),
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
        self._load_annotations()
        self._image_name_label.setText(self._image_manager.current_item)

    def _on_show_annotations_toggled(self):

        if not self._image_manager or self._image_manager.is_empty():
            return

        self._image_canvas.init_vars()

        if self._show_annotations_action.isChecked():
            #self._image_canvas.data_items = copy.deepcopy(self._data_info.items) # 复制数据项，避免直接操作原数据x
            self._image_canvas.data_items = self._data_info.items
            self._image_canvas.current_item_index = 0

        self._image_canvas.update()
        self._update_data_item_property_display()

    def _load_annotations(self):
        """加载标注数据"""

        image_name = os.path.basename(self._image_manager.current_item)
        json_path = os.path.join(os.path.dirname(self._image_manager.current_item), f"{image_name.split('.')[0]}.json")
        try:
      
            self._data_info = jsonFileManager.load_json(json_path)
        except Exception:
            self._data_info = DataInfo(file_name=image_name, items=[])

        self._on_show_annotations_toggled()
                     

    def _update_data_item_property_display(self):
        """更新选中DataItem的属性显示"""
        if self._image_canvas.current_item_index < 0 or not self._data_info or not self._data_info.items:
            return

    def _start_create_data_item(self):
        """开始创建DataItem"""

        self._image_canvas.creating_data_item = True
        self._image_canvas.annotion_frame = AnnotationFrameBase.create(AnnotationType.POLYGON)
        self._image_canvas.setMouseTracking(True)
        self._image_canvas.setCursor(Qt.BlankCursor) # 隐藏鼠标光标
        #cursor.set_widget_cursor(self._image_canvas, CursorStyle.CROSS)
        
    def _finish_create_data_item(self):

        points = self._image_canvas.convert_annotion_frame_coords()

        if not points:
            return

        new_data_item = DataItemInfo(
            text="",
            language="",
            annotation_type=AnnotationType.DEFAULT,
            caseLabel="default",
            points=points
        )

        self._image_canvas.data_items.append(new_data_item)
        self._image_canvas.current_item_index = len(self._data_info.items) - 1
        self._image_canvas.update()
        self._update_data_item_property_display()

    def _cancel_create_data_item(self):
        """取消创建DataItem"""
        self._image_canvas.init_vars()
        self.update()
        
    def _delete_selected_data_item(self):
        """删除选中的DataItem"""
        if self._image_canvas.current_item_index < 0 or not self._data_info.items or not self._image_canvas.data_items:
            return
        
    
        del self._image_canvas.data_items[self._image_canvas.current_item_index]

        del self._image_canvas.all_points_colors[self._image_canvas.current_item_index]
        

        self._image_canvas.current_item_index = -1
        self._image_canvas.current_point_index = -1

        self._image_canvas.update()
        
        self._update_data_item_property_display()
        
    def _clear_all_data_items(self):
        if not self._data_info or not self._data_info.items:
            return

        self._data_info.items = []
        self._image_canvas.init_vars()
        self._image_canvas.update()

    def _save_annotations(self):

        if not self._data_info or not self._data_info.items:
            return
        image_name = os.path.basename(self._image_manager.current_item)
        json_path = os.path.join(os.path.dirname(self._image_manager.current_item), f"{image_name.split('.')[0]}.json")

        self._data_info.file_name = image_name
        self._data_info.label = ""
        self._data_info.issues = []

        try:
            jsonFileManager.save_json(json_path, self._data_info)
        except Exception as e:
            print(f"保存标注失败: {str(e)}")
            return


    def _on_d_pressed(self):
        if self._image_canvas.current_item_index < 0 or self._image_canvas.current_point_index < 0 or not self._data_info or not self._data_info.items:
            return
        
        item = self._image_canvas.data_items[self._image_canvas.current_item_index]
        
        if len(item.points) <= 3:
            print("DataItem至少需要3个顶点")
            return

        item.remove_point(self._image_canvas.current_point_index)
        self._image_canvas.current_point_index = -1
        self._image_canvas.update()

    def _on_shift_pressed(self, pressed):

        self._image_canvas.shift_pressed = pressed

        if pressed:
            print("Shift键已按下，点击Charset边缘添加顶点") 
            self._image_canvas.setCursor(Qt.PointingHandCursor)
        else:
            print("Shift键已释放")
            self._image_canvas.setCursor(Qt.ArrowCursor)

    def _on_n_pressed(self):
        if not self._image_canvas.creating_data_item:
            self._start_create_data_item()
            print("开始创建DataItem")
        else:
            self._finish_create_data_item()
            print("完成创建DataItem")


    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Escape and self._image_canvas.creating_data_item:
            self._cancel_create_data_item()
            print("取消创建DataItem")
            return
        
        if event.key() == Qt.Key_N:
            self._on_n_pressed()
            return
        
        if event.key() == Qt.Key_D:
            self._on_d_pressed()
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




