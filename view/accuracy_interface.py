import os
from natsort import natsorted
import shutil
import threading
import time
from PyQt5.QtCore import Qt,pyqtSlot,QPoint,QThread,pyqtSignal
from PyQt5.QtGui import QColor,QPixmap
from PyQt5.QtWidgets import (QWidget, QPushButton, QFrame, QHBoxLayout, QVBoxLayout, 
                           QApplication, QFileDialog, QMessageBox,QTextBrowser,QDialog)

from QtUniversalToolFrameWork.common.cache import LRUCache
from QtUniversalToolFrameWork.common.image_utils import ImageManager,get_image_paths
from QtUniversalToolFrameWork.common.icon import Action,FluentIcon as FIF
from QtUniversalToolFrameWork.common.cursor import CursorStyle,cursor
from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageProgressWidget,ImageSearchFlyoutView
from QtUniversalToolFrameWork.components.widgets.label import CommandBarLabel
from QtUniversalToolFrameWork.components.widgets.command_bar import CommandBar
from QtUniversalToolFrameWork.components.widgets.flyout import Flyout,FlyoutAnimationType
from QtUniversalToolFrameWork.components.widgets.gallery_interface import TitleToolBar
from QtUniversalToolFrameWork.components.widgets.info_bar import InfoBar,InfoBarPosition
from QtUniversalToolFrameWork.components.widgets.state_tool_tip import StateToolTip

from common.signal_bus import signalBus
from common.style_sheet import StyleSheet
from common.utils import Utils
from components.image_canvas import PolygonsDrawImageCanvas
from common.data_structure import DataInfo,DataItemInfo,jsonFileManager
from common.annotation import AnnotationType,AnnotationFrameBase
from common.key_manager import keyManager
from common.data_control_manager import dm
from common.case_label import cl
from common.message import message
from common.icon import icon
from components.pivot_stacked import PivotStacked
from components.info_card import InfoCardInterface


class Data_cache(QWidget):

    data_size_changed = pyqtSignal(int)

    def __init__(self,parent=None,capacity=50):
        super().__init__(parent)
        self._cache = LRUCache(capacity=capacity*2)

    def size(self):
        return self._cache.size()

    def json_path(self,key:str):
        image_name = os.path.basename(key).split(".")[0]
        return os.path.join(os.path.dirname(key), f"{image_name}.json")

    def put(self,key:str):

        json_path = self.json_path(key)

        try:
            data_info = jsonFileManager.load_json(json_path)
            if data_info is None:
                message.show_error_message("错误", "未找到标注文件!")
                return
            
        except Exception as e:
            message.show_error_message("错误", f"加载标注文件失败：{e}")
            return

        infoCard = InfoCardInterface(self)
  
        sorted_items = natsorted(data_info.items, key=lambda x: (cl.get_label_name(x.caseLabel)=="default", x.caseLabel)) # 先排序默认标签，再排序其他标签

        infoCard.setUpdatesEnabled(False)

        for item in sorted_items: 
            infoCard.addItem(item.id,item.caseLabel,item.annotation_type)
        
        infoCard.setUpdatesEnabled(True)
        
        self._cache.put(key,(data_info,infoCard))
        
        self.data_size_changed.emit(self.size())
                    
    def get_data_info(self,key:str) -> DataInfo:
        
        if key not in self._cache.keys():
            self.put(key)

        return self._cache.get(key)[0]
        
    def get_info_card(self,key:str) -> InfoCardInterface:

        if key not in self._cache.keys():
            self.put(key)
            
        return self._cache.get(key)[1]
    
    def save_json(self,key:str):

        data_info = self.get_data_info(key)

        data_info.file_name = os.path.basename(key)
        data_info.label = ""
        data_info.issues = []

        try:
            jsonFileManager.save_json(self.json_path(key), data_info)
        except Exception as e:
            message.show_error_message("错误","标签文件保存失败！")
            return


class DataLoadThread(QThread):
   
    load_finished = pyqtSignal()

    def __init__(self,capacity:int):
        super().__init__()
        self._capacity = capacity
        self._size = 0
        self._stop_event = threading.Event() # 用于停止线程的事件

    def set_capacity(self,capacity:int):
        self._capacity = capacity

    def _on_progress_changed(self,size:int):
        self._size = size

    def run(self):
        """子线程中执行耗时的数据加载"""
        try:
            
            total_steps = 100  # 模拟加载步骤数
            for i in range(total_steps):

                if self._stop_event.is_set(): # 检查是否需要停止线程
                    break
                time.sleep(0.5)
                if self._size  >= self._capacity:
                    break
            
            # 加载完成，发送数据
            self.load_finished.emit()
        except Exception as e:
            message.show_error_message("错误", str(e))

    
    def stop(self):
        self._stop_event.set()

class AccuracyInterface(QWidget):
    """OCR精度调整工具模块，用于调整OCR识别区域的多边形标注"""

    CACHE_CAPACITY = 50

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("accuracy_interface")
        self._title_toolbar = TitleToolBar(":app/images/image.svg",'图像标注工具')
        self._progress_widget = ImageProgressWidget(self)

        self._image_manager = ImageManager(self,self.CACHE_CAPACITY)
        self._data_cache = Data_cache(self,self.CACHE_CAPACITY)
        
        self._image_canvas = PolygonsDrawImageCanvas(self)
        self._image_name_label = CommandBarLabel(self)
        self._pivot_stacked = PivotStacked(self)
        self._annotation_type = AnnotationType.DEFAULT

        self._commandBar1, self._commandBar2 = self.createCommandBar()

        self._current_dir = ""
        self._load_thread = None

        
        
        self._progress_widget.progress.connect(self._on_progress_changed)

        self._image_manager.image_loaded.connect(self._display_current_image)
        self._image_manager.image_loaded.connect(self._set_progress_value)
        self._image_manager.skip_previous_item.connect(self._save_annotations)
        self._image_manager.item_deleted.connect(self._set_progress_range)
        self._image_manager.item_inserted.connect(self._set_progress_range)
        self._image_manager.model_reset.connect(self._set_progress_range)


        self._image_manager.key_progress.connect(self._data_cache.put)


        keyManager.N.connect(self._on_n_pressed)
        keyManager.M.connect(self._on_m_pressed)
        keyManager.D.connect(self._on_d_pressed)
        keyManager.SHIFT.connect(self._on_shift_pressed)

        signalBus.annotationTypeChanged.connect(self._annotation_type_changed)
        signalBus.splitPolygonFunction.connect(self._on_m_pressed)

        self.init_ui()

    def init_ui(self):
        """初始化UI"""

        StyleSheet.ACCURACY_INTERFACE.apply(self)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)


        view = QFrame(self)
        vBoxLayout = QVBoxLayout(view)
        vBoxLayout.setContentsMargins(10, 10, 10, 0)
        vBoxLayout.setAlignment(Qt.AlignTop) 

        hBoxLayout = QHBoxLayout()
        hBoxLayout.setSpacing(1)
        hBoxLayout.setContentsMargins(0, 0, 0, 0)

        toolBarLayout = QHBoxLayout()
        toolBarLayout.setContentsMargins(5, 10, 0, 10)

        self._progress_widget.set_slider_width(200)
        self._image_name_label.setContentsMargins(20, 0, 0, 0)


        w = QWidget(self)
        w.setFixedWidth(310)

        toolBarLayout.addWidget(self._commandBar1,0,Qt.AlignLeft)
        toolBarLayout.addWidget(self._commandBar2,1,Qt.AlignHCenter)
        toolBarLayout.addWidget(w,0,Qt.AlignRight)
    
        hBoxLayout.addWidget(self._image_canvas,1)
        hBoxLayout.addWidget(self._pivot_stacked,0)


        vBoxLayout.addWidget(self._title_toolbar,0,Qt.AlignLeft)
        vBoxLayout.addLayout(toolBarLayout)

        vBoxLayout.addLayout(hBoxLayout)

        vBoxLayout.addWidget(self._image_name_label,0,Qt.AlignLeft)

        view.setObjectName("view")
        mainLayout.addWidget(view)
  
    def _annotation_type_changed(self, annotation_type:AnnotationType):
        self._annotation_type = annotation_type
        keyManager.release_all_keys()
        self._image_canvas.setFocus()

    def _set_progress_range(self):
        self._progress_widget.set_slider_range(1, self._image_manager.count)
        
    def _set_progress_value(self):
        self._progress_widget.set_slider_value(self._image_manager.current_index+1)

    def createCommandBar(self):
            
            bar1 = CommandBar(self)
            bar1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self._show_annotations_action = Action(FIF.TAG, "标注", checkable=True,triggered=self._on_show_annotations_toggled,shortcut="S")
           

            bar1.addActions([
                Action(FIF.ADD, "加载", triggered=self._on_folder_path_changed),
                self._show_annotations_action, 
            ])

            bar1.addSeparator()

            bar2 = CommandBar(self)

            bar2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            
            bar2.addActions([
                Action(FIF.LEFT_ARROW,triggered=self._image_manager.previous,shortcut="Left"),
                Action(FIF.RIGHT_ARROW,triggered=self._image_manager.next,shortcut="Right"),
            ])

            bar2.addWidget(self._progress_widget)


            bar2.addActions([
                Action(FIF.SEARCH,triggered=self._on_search_clicked)
,
            ])

            bar2.addSeparator()

            bar2.addActions([
                Action(FIF.ROTATE,triggered=self._image_canvas.rotate_image,shortcut="R"),
                Action(FIF.ZOOM_IN,triggered=self._image_canvas.zoom_in),
                Action(FIF.ZOOM_OUT,triggered=self._image_canvas.zoom_out),
                Action(FIF.DELETE,triggered=self._on_delete_image_clicked,shortcut="Delete"),
            ])

            return bar1,bar2
    
    def _on_folder_path_changed(self,):

        folder = QFileDialog.getExistingDirectory(
            self, "选择图像文件夹", self._current_dir or "./",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if folder:
            self.stateTooltip = None
            self._current_dir = folder
            image_paths = get_image_paths(self._current_dir)
            self._image_manager.set_items(image_paths)

            self.stateTooltip = StateToolTip("标注数据加载", "请耐心等待...", self.window())
            self.stateTooltip.move(self.stateTooltip.getSuitablePos())
            self.stateTooltip.show()

            
            if self._load_thread and self._load_thread.isRunning():
                self._load_thread.stop()
                self._load_thread.wait()

            self._load_thread = DataLoadThread(min(self._image_manager.count,self.CACHE_CAPACITY))
            self._data_cache.data_size_changed.connect(self._load_thread._on_progress_changed)
            self._load_thread.load_finished.connect(self._on_load_label_finished)


            self._load_thread.start()


    def _on_load_label_finished(self):
        if self.stateTooltip:
            print("标注数据已加载完成！")
            self.stateTooltip.setContent("标注数据已加载完成！" + ' 😆')
            self.stateTooltip.setState(True)
            self.stateTooltip = None

          
    @pyqtSlot(QPixmap)
    def _display_current_image(self, pixmap: QPixmap):
        if not pixmap:
            return

        self._image_canvas.load_pixmap(pixmap)
        self._image_name_label.setText(self._image_manager.current_item)
        self._load_annotations()

    def _on_show_annotations_toggled(self):

        if not self._image_manager or self._image_manager.is_empty():
            return

        dm.init_vars()

        
        if self._show_annotations_action.isChecked(): # 显示标注
            dm.init_data_items()
            self._pivot_stacked.show_info_card_interface(self._data_cache.get_info_card(self._image_manager.current_item))
            return
        
        self._pivot_stacked.hide_info_card_interface()
        
    def _load_annotations(self):
        """加载标注数据"""

        dm.data_info = self._data_cache.get_data_info(self._image_manager.current_item)

        self._on_show_annotations_toggled()

    def _save_annotations(self):

        self._data_cache.save_json(self._image_manager.current_item)


    @pyqtSlot(str)
    def _on_search_signal(self, search_text: str):
        if search_text:
            try:
                image_index = self._image_manager.items.index(os.path.join(self._current_dir, search_text))    
            except ValueError:
                message.show_error_message("错误", f"未找到图像 {search_text}")
                return
                
            self._image_manager.go_to(image_index)

    def _on_delete_image_clicked(self):
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

            message.show_success_message("提示",f"图像 {image_name} 删除成功！")
        except Exception as e:
            message.show_error_message("错误",f"图像删除失败！")
            return

    
    def _clear_all_items(self):
        if not dm.is_current_item_valid():
            return
        
        dm.data_info = DataInfo(file_name=dm.data_info.file_name, items=[])
        dm.init_vars()
        
    def _on_shift_pressed(self, pressed):

        dm.shift_pressed = pressed

        if pressed:
            self._image_canvas.setCursor(Qt.PointingHandCursor)
        else:
            self._image_canvas.setCursor(Qt.ArrowCursor)

    def _on_d_pressed(self, pressed):

        if pressed:
            dm.delete_current_point()
             
    def _on_n_pressed(self, pressed):

        if pressed:
            if dm.creating_data_item:

                self._image_canvas.setMouseTracking(False)
                self._image_canvas.setCursor(Qt.ArrowCursor)

                dm.finish_create(self._image_canvas.get_origin_image_size())
            else:
                dm.creating_data_item = True
                dm.annotion_frame = AnnotationFrameBase.create(self._annotation_type)
                self._image_canvas.setMouseTracking(True)
                self._image_canvas.setCursor(Qt.BlankCursor) # 隐藏鼠标光标
                
        elif dm.creating_data_item:
            dm.creating_data_item = False
            dm.annotion_frame = None
            self._image_canvas.setMouseTracking(False)
            self._image_canvas.setCursor(Qt.ArrowCursor)
            self._image_canvas.update()
            
    def _on_m_pressed(self, pressed):

        if pressed:
            dm.creating_split_vertex = True
            dm.split_item_index = -1
            dm.annotion_frame = AnnotationFrameBase.create(AnnotationType.LINE)


            self._image_canvas.setMouseTracking(True)
            self._image_canvas.setCursor(Qt.PointingHandCursor)

        elif dm.creating_split_vertex:
            dm.creating_split_vertex = False
            dm.split_item_index = -1
            dm.annotion_frame = None
            self._image_canvas.setMouseTracking(False)
            self._image_canvas.setCursor(Qt.ArrowCursor)
            self._image_canvas.update()

    def keyPressEvent(self, event):

        if self._current_dir == "" or not self._show_annotations_action.isChecked():
            super().keyPressEvent(event)
            return

        if keyManager.press_key(event.key()):
            return
        
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        
        if keyManager.release_key(event.key()):
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
                    target=self.mapToGlobal(QPoint(self.width()//2-searchFlyoutView.width()//2,self.height()//2-searchFlyoutView.height()//2)),
                    parent = self,
                    aniType = FlyoutAnimationType.DROP_DOWN)
        
    def resizeEvent(self, e):
        super().resizeEvent(e)

        width = 325

        self._commandBar1.setFixedWidth(self._commandBar1.suitableWidth())
        width += self._commandBar1.width()
        self._commandBar1.updateGeometry()

        self._commandBar2.setFixedWidth(min(self._commandBar2.suitableWidth(), self.width()-20-width))
        width += self._commandBar2.width()
        self._commandBar2.updateGeometry()


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

    




