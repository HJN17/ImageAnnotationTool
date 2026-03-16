import os
from natsort import natsorted
import shutil
import threading
import time
from PyQt5.QtCore import Qt,pyqtSlot,QPoint,QThread,pyqtSignal,QUrl
from PyQt5.QtGui import QFont,QPixmap,QDesktopServices
from PyQt5.QtWidgets import (QWidget, QPushButton, QFrame, QHBoxLayout, QVBoxLayout, 
                           QApplication, QFileDialog, QMessageBox,QTextBrowser,QDialog)

from QtUniversalToolFrameWork.common.font import getFont
from QtUniversalToolFrameWork.common.cache import LRUCache
from QtUniversalToolFrameWork.common.image_utils import ImageManager,get_image_paths
from QtUniversalToolFrameWork.common.icon import Action,FluentIcon as FIF
from QtUniversalToolFrameWork.common.cursor import CursorStyle,cursor
from QtUniversalToolFrameWork.components.widgets.image_canvas import ImageProgressWidget,ImageSearchFlyoutView
from QtUniversalToolFrameWork.components.widgets.label import CommandBarLabel,BodyLabel,FluentLabelBase
from QtUniversalToolFrameWork.components.widgets.command_bar import CommandBar
from QtUniversalToolFrameWork.components.widgets.flyout import Flyout,FlyoutAnimationType
from QtUniversalToolFrameWork.components.widgets.gallery_interface import TitleToolBar
from QtUniversalToolFrameWork.components.widgets.info_bar import InfoBar,InfoBarPosition
from QtUniversalToolFrameWork.components.widgets.state_tool_tip import StateToolTip
from QtUniversalToolFrameWork.components.widgets.button import PushButton
from QtUniversalToolFrameWork.components.dialog_box import CustomMessageBoxBase,MessageBox


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


class TitleLabel(FluentLabelBase):
    """ 标题文本标签 """
    def getFont(self):
        return getFont(16, QFont.DemiBold)

class KeyLabel(FluentLabelBase):
    """ 文本标签 """
    def getFont(self):
        return getFont(14, QFont.DemiBold)
    
class DescLabel(FluentLabelBase):
    """ 描述文本标签 """
    def getFont(self):
        return getFont(14)

class TitleText(QWidget):
    def __init__(self, title:str,parent=None):
        super().__init__(parent)

        self.titleLabel = TitleLabel(title,self)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 20, 0, 10)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.addWidget(self.titleLabel,0,Qt.AlignLeft | Qt.AlignVCenter)

class bodyText(QWidget):
    def __init__(self, key:str,desc:str,parent=None):
        super().__init__(parent)

        k = key+" :" if key else ""

        self.keyLabel = KeyLabel(k,self)
        self.descLabel = DescLabel(desc,self)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(50, 0, 0, 0)
        self.hBoxLayout.setSpacing(0)
        self.keyLabel.setFixedWidth(200)
        self.hBoxLayout.addWidget(self.keyLabel,0,Qt.AlignLeft | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.descLabel,1,Qt.AlignLeft | Qt.AlignVCenter)

class HelpMessageBox(CustomMessageBoxBase):
    """ 标签列表设置消息框 """
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_title_label("✨ 基础操作快捷键")
        
        self.add_body_text("ESC键","取消所有操作")
        self.add_body_text("N键开始","新建标注框")
        self.add_body_text("N键结束","完成标注框")
        self.add_body_text("SPACE键","重置布局")
        self.add_body_text("B键","删除选中的标注框")
        self.add_body_text("W健","切换多边形显示/隐藏")
        self.add_body_text("S键","分割多边形标注框")
        self.add_body_text("SHIFT键（长按）","添加标注点（标注框边缘）")
        self.add_body_text("X键","删除选中顶点（需先选中顶点）")
        self.add_body_text("A键","切换到上一张图片（自动保存）")
        self.add_body_text("D键","切换到下一张图片（自动保存）")

        self.add_title_label("✨ 鼠标操作")
        self.add_body_text("左键点击","新建多边形时 - 添加顶点")
        self.add_body_text("","选中顶点时 - 拖动调整顶点位置")
        self.add_body_text("","选中标注框内部时 - 拖动整个标注框")
        self.add_body_text("右键拖动","平移画布")
        self.add_body_text("鼠标滚轮","缩放画布")

        self.yesButton.setText('知道啦')
        self.cancelButton.hide()
        self.widget.setMinimumWidth(600)

    def add_title_label(self,title:str):
        self.viewLayout.addWidget(TitleText(title,self))

    def add_body_text(self,key:str,desc:str):
        self.viewLayout.addWidget(bodyText(key,desc,self))

class ClearAllItemsMessageBox(MessageBox):
    """ 清除所有标注项消息框 """
    
    def __init__(self, parent=None):
        super().__init__("确认清除所有标注项吗？","清除所有标注项后，无法恢复，请确认操作。",parent)
        self.yesButton.setText('确认清除')
        self.cancelButton.setText('取消')
        self.widget.setMinimumWidth(400)


class DataLoadThread(QThread):
   
    load_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event() # 用于停止线程的事件

    def run(self):
        """子线程中执行耗时的数据加载"""
        try:
            
            total_steps = 10 # 模拟加载步骤数
            for i in range(total_steps):

                if self._stop_event.is_set(): # 检查是否需要停止线程
                    break
                time.sleep(0.3) # 模拟耗时操作
               
            # 加载完成，发送数据
            self.load_finished.emit()
        except Exception as e:
            message.show_error_message("错误", str(e))
    
    def stop(self):
        self._stop_event.set()

class AccuracyInterface(QWidget):
    """OCR精度调整工具模块，用于调整OCR识别区域的多边形标注"""

    CACHE_CAPACITY = 5
    EXAMPLE_URL = "https://github.com/HJN17/ImageAnnotationTool"
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("accuracy_interface")
        self._title_toolbar = TitleToolBar(":app/images/image.svg",'图像标注工具')
        self._progress_widget = ImageProgressWidget(self)

        self._image_manager = ImageManager(self,self.CACHE_CAPACITY)
        
        self._image_canvas = PolygonsDrawImageCanvas(self)
        self._image_name_label = CommandBarLabel(self)

        self._pivot_stacked = PivotStacked(self)
        self._annotation_type = AnnotationType.DEFAULT

        

        self.sourceButton = PushButton("源代码", self, FIF.GITHUB)
        self.helpButton = PushButton("帮助", self, icon.HELP)

        self._help_message_box = HelpMessageBox(self.window())
        self._help_message_box.hide()

        self._clear_all_items_message_box = ClearAllItemsMessageBox(self.window())
        self._clear_all_items_message_box.hide()


        self._commandBar1, self._commandBar2 = self.createCommandBar()

        self._current_dir = ""
        self._load_thread = None

        self.helpButton.clicked.connect(self._help_message_box.show)
        self.sourceButton.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.EXAMPLE_URL)))

        self._progress_widget.progress.connect(self._on_progress_changed)

        self._image_manager.image_loaded.connect(self._display_current_image)
        self._image_manager.image_loaded.connect(self._set_progress_value)
        self._image_manager.skip_previous_item.connect(self._save_annotations)
        self._image_manager.item_deleted.connect(self._set_progress_range)
        self._image_manager.item_inserted.connect(self._set_progress_range)
        self._image_manager.model_reset.connect(self._set_progress_range)

        dm.update_data_item.connect(self._save_annotations)

        keyManager.N.connect(self._on_n_pressed)
        keyManager.S.connect(self._on_s_pressed)
        keyManager.X.connect(self._on_x_pressed)
        keyManager.B.connect(self._on_b_pressed)
        keyManager.SHIFT.connect(self._on_shift_pressed)
        keyManager.SPACE.connect(self._on_space_pressed)

        signalBus.annotationTypeChanged.connect(self._annotation_type_changed)
        signalBus.splitPolygonFunction.connect(self._on_s_pressed)
        
        self._clear_all_items_message_box.yesSignal.connect(self._clear_all_items)

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

        #self._progress_widget.set_slider_width(200)
        self._image_name_label.setContentsMargins(20, 0, 0, 0)

        w = QWidget(self)
        w.setFixedWidth(310)

        toolBarLayout.addWidget(self._commandBar1,0,Qt.AlignLeft)
        toolBarLayout.addWidget(self._commandBar2,1,Qt.AlignHCenter|Qt.AlignLeft)
        toolBarLayout.addWidget(self.helpButton,0,Qt.AlignRight)
        toolBarLayout.addWidget(self.sourceButton,0,Qt.AlignRight)
    
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
            self._show_annotations_action = Action(FIF.TAG, "标注", checkable=True,triggered=self._on_show_annotations_toggled,shortcut="W")
           

            bar1.addActions([
                Action(FIF.ADD, "加载", triggered=self._on_folder_path_changed),
                self._show_annotations_action, 
            ])

            bar1.addSeparator()

            bar2 = CommandBar(self)

            bar2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            
            bar2.addActions([
                Action(FIF.LEFT_ARROW,triggered=self._image_manager.previous,shortcut="A"),
                Action(FIF.RIGHT_ARROW,triggered=self._image_manager.next,shortcut="D"),
            ])

            bar2.addWidget(self._progress_widget)


            bar2.addActions([
                Action(FIF.SEARCH,triggered=self._on_search_clicked)

            ])

            bar2.addSeparator()

            bar2.addActions([
                Action(FIF.ROTATE,triggered=self._image_canvas.rotate_image,shortcut="R"),
                Action(FIF.ZOOM_IN,triggered=self._image_canvas.zoom_in),
                Action(FIF.ZOOM_OUT,triggered=self._image_canvas.zoom_out),
                Action(FIF.DELETE,triggered=self._on_delete_image_clicked),
                Action(FIF.ERASE_TOOL,triggered=self._clear_all_items_message_box.show),
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

            self._load_thread = DataLoadThread()
            self._load_thread.load_finished.connect(self._on_load_label_finished)

            self._load_thread.start()

    def _on_load_label_finished(self):
        if self.stateTooltip:
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
            return
        
    def _load_annotations(self):
        """加载标注数据"""


        json_path = self.json_path(self._image_manager.current_item)

        try:
            di = jsonFileManager.load_json(json_path)
            if di is None:
                message.show_error_message("错误", "未找到标注文件!")
                return
            
        except Exception as e:
            message.show_error_message("错误", f"加载标注文件失败：{e}")
            return
        
        dm.data_info = di

        self._on_show_annotations_toggled()

    def _save_annotations(self):
        
        if dm.data_items is None or len(dm.data_items) == 0:
            return
        
        name = self._image_manager.current_item
        dm.data_info.file_name = os.path.basename(name)
        dm.data_info.label = ""
        dm.data_info.issues = []

        try:
            jsonFileManager.save_json(self.json_path(name), dm.data_info)
        except Exception as e:
            message.show_error_message("错误","标签文件保存失败！")
            return

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
        image_name = os.path.basename(self._image_manager.current_item)
        dm.data_info = DataInfo(file_name=image_name, items=[])
        dm.init_vars()


    def _on_space_pressed(self, pressed):
        if pressed:
            #重置画布位置
            self._image_canvas.center_image()

    
        
    def _on_shift_pressed(self, pressed):

        dm.creating_vertex_pressed = pressed

        if pressed:
            self._image_canvas.setCursor(Qt.PointingHandCursor)
        else:
            self._image_canvas.setCursor(Qt.ArrowCursor)

    def _on_x_pressed(self, pressed):
        if pressed:
            dm.delete_current_point()
    
    def _on_b_pressed(self, pressed):
        if pressed:
            dm.delete_current_item()

    def _on_n_pressed(self, pressed):

        if pressed:
            if dm.creating_data_item:

                self._image_canvas.setMouseTracking(False)
                self._image_canvas.setCursor(Qt.ArrowCursor)
                dm.finish_create(self._image_canvas.get_origin_image_size())
            else:
                dm.creating_data_item = True
                dm.annotation_frame = AnnotationFrameBase.create(self._annotation_type)
                self._image_canvas.setMouseTracking(True)
                self._image_canvas.setCursor(Qt.BlankCursor) # 隐藏鼠标光标
                
        elif dm.creating_data_item:
            dm.creating_data_item = False
            dm.annotation_frame = None
            self._image_canvas.setMouseTracking(False)
            self._image_canvas.setCursor(Qt.ArrowCursor)
            self._image_canvas.update()
            
    def _on_s_pressed(self, pressed):

        if pressed:
            dm.creating_split_vertex = True
            dm.split_item_index = -1
            dm.annotation_frame = AnnotationFrameBase.create(AnnotationType.LINE)


            self._image_canvas.setMouseTracking(True)
            self._image_canvas.setCursor(Qt.PointingHandCursor)

        elif dm.creating_split_vertex:
            dm.creating_split_vertex = False
            dm.split_item_index = -1
            dm.annotation_frame = None
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
    
    def json_path(self,key:str):
        image_name = os.path.basename(key).split(".")[0]
        return os.path.join(os.path.dirname(key), f"{image_name}.json")



