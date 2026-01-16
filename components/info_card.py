# coding:utf-8

from PyQt5.QtCore import Qt,QRect,QRectF,QPoint
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen

from QtUniversalToolFrameWork.common.icon import FluentIcon
from QtUniversalToolFrameWork.components.widgets import ScrollArea
from QtUniversalToolFrameWork.components.widgets.label import CardLabel
from QtUniversalToolFrameWork.components.widgets.combo_box import ComboBox
from QtUniversalToolFrameWork.components.widgets.button import TransparentToolButton

from common.annotation import AnnotationType
from common.style_sheet import StyleSheet
from common.case_label import cl
from common.signal_bus import signalBus


class InfoCardComboBox(ComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""

    def _set_temp_text(self, text: str):
        self._text = text

    def removeItem(self, index: int):
        if not 0 <= index < len(self.items):
            return

        self.items.pop(index)

        self.setCurrentText(self._text)
        
        if self.count() == 0:
            self.clear()



class InfoCardItem(QWidget):

    def __init__(self,routeKey:str,caseLabel : str, annotation_type:AnnotationType, parent=None):
        super().__init__(parent)

        self._id = routeKey
        self._color = cl.get_color(caseLabel)
        self._original_case_label = caseLabel
        self._case_label = caseLabel if caseLabel in cl.get_all_labels() else "default"
        self.is_selected = False

        self._annotation_type = CardLabel(annotation_type.value.upper(), self)
        self._comboBox = InfoCardComboBox(self)

        self._is_show = True

        self._personButton = TransparentToolButton(FluentIcon.ROBOT, self) 
        self._viewButton = TransparentToolButton(FluentIcon.VIEW, self) # HIDE
        self._pinButton = TransparentToolButton(FluentIcon.PIN, self) # UNPIN
        self._delButton = TransparentToolButton(FluentIcon.DELETE, self)

        self._comboBox.addItems(cl.get_all_labels())

        self._comboBox.setCurrentText(self._case_label)


        cl.add_label_changed.connect(self._add_comboBox_item)
        cl.del_label_changed.connect(self._del_comboBox_item)
        cl.color_label_changed.connect(self._update_color)

        self._comboBox.currentTextChanged.connect(lambda text: self._set_case_label(text))
        self._comboBox.currentTextChanged.connect(self.update)

        self._comboBox.clicked.connect(lambda: signalBus.selectItem.emit(self._id))
        self._delButton.clicked.connect(lambda: signalBus.deleteItem.emit(self._id))
        
        cl.show_label_changed.connect(self._update_show)

    
        self._update_show(self._case_label)

        self.setAttribute(Qt.WA_StaticContents) # 静态内容：仅内容变化时才重绘
        self.setAttribute(Qt.WA_NoSystemBackground)


        self._init_ui()
    
    def _init_ui(self):
        
        self.setFixedSize(280, 100)
        vBoxLayout = QVBoxLayout(self)
        vBoxLayout.setSpacing(0)
        vBoxLayout.setContentsMargins(20, 0, 20, 0)

        self._annotation_type.setFixedSize(70, 32)
        self._comboBox.setFixedSize(170, 32)
        
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.addWidget(self._annotation_type, 0, Qt.AlignLeft)
        type_layout.addWidget(self._comboBox, 0, Qt.AlignLeft)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 0, 0, 0)
        button_layout.addWidget(self._personButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._viewButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._pinButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._delButton, 0, Qt.AlignLeft)

        vBoxLayout.addLayout(type_layout)
        vBoxLayout.addLayout(button_layout)


    def _update_color(self, label: str):
        if label == self._case_label:
            self._color = cl.get_color(label)
            self.update()

    def _add_comboBox_item(self, label: str):
        
        self._comboBox.addItem(label)

        if self._original_case_label == label:
            self._set_case_label(label)
            self._comboBox.setCurrentText(label)
        

    def _del_comboBox_item(self, label: str):

        index = self._comboBox.findText(label)
        if index != -1:
            
            if self._case_label == label:
                self._set_case_label("default")
                self._comboBox._set_temp_text("default")

            self._comboBox.removeItem(index)


    def _set_case_label(self, case_label: str):

        self._case_label = case_label if case_label in cl.get_all_labels() else "default"

        if self._case_label != "default":
            self._original_case_label = case_label

        self._color = cl.get_color(case_label)
        self._update_show(self._case_label)
        signalBus.labelComboBoxChanged.emit(self._id, self._case_label)
    

    def is_show(self) -> bool:
        return self._is_show

    def _update_show(self, label: str): 
        if label == self._case_label:
            self._is_show = cl.is_show(label)
            self.setVisible(self._is_show)

    def setSelected(self, is_selected: bool):
        if self.is_selected == is_selected:
            return
        self.is_selected = is_selected
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        
        rect_f = QRectF(self.rect().adjusted(1, 1, -1, -1))

        painter.setRenderHint(QPainter.Antialiasing)

        if self.is_selected:
            
            selected_color = QColor(self._color)
            selected_color.setAlpha(60) 
        
            painter.setBrush(QBrush(selected_color))
            painter.setPen(QPen(self._color,1)) 
        
        else:
            painter.setBrush(self._color)
            painter.setPen(Qt.NoPen)

        _radius = 6
        
        painter.drawRoundedRect(rect_f, _radius, _radius)

        super().paintEvent(event)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            signalBus.selectItem.emit(self._id)
            return
        
        super().mousePressEvent(event)
    

class InfoCardInterface(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._items = {}
        self._currentRouteKey = None

        self.scrollWidget = QWidget(self)
        signalBus.deleteItem.connect(self.removeItem)
        signalBus.selectItem.connect(self._set_current_item)
        signalBus.addItem.connect(self.addItem)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条

        self._init_ui()

    def _init_ui(self):
        
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        
        self.setViewportMargins(0, 0, 10, 0)
        self.setWidgetResizable(True)
        self.setWidget(self.scrollWidget)

        self.scrollWidget.setObjectName('scrollWidget')

        StyleSheet.ACCURACY_INTERFACE.apply(self)
    
    @property
    def items(self):
        return self._items

    def addItem(self,routeKey,caseLabel : str, annotation_type:AnnotationType,onClick=None):
        return self.insertItem(-1, routeKey,caseLabel, annotation_type,onClick) 

    def insertItem(self, index: int, routeKey: str,caseLabel : str, annotation_type:AnnotationType,onClick=None):
        if routeKey in self.items:
            return
        widget = InfoCardItem(routeKey,caseLabel, annotation_type, self.scrollWidget)
       
        self.insertWidget(index, routeKey, widget, onClick)
        return widget

    def insertWidget(self, index: int, routeKey: str, widget: InfoCardItem, onClick=None):
       
        if routeKey in self.items:
            return

        widget.setProperty('routeKey', routeKey)
        
        self.items[routeKey] = widget
        self.vBoxLayout.insertWidget(index, widget, 1)


    def removeItem(self, routeKey: str):

        if routeKey not in self.items:
            return

        widget = self.items[routeKey]
        self.vBoxLayout.removeWidget(widget) # 从布局中移除部件
        widget.deleteLater() # 删除部件
        del self.items[routeKey]

    def clear(self):
        for routeKey in list(self.items.keys()):
            self.removeItem(routeKey)
    
    def currentRouteKey(self):
        return self._currentRouteKey


    def _set_current_item(self, routeKey: str):

        if routeKey not in self._items or routeKey == self._currentRouteKey:
            return

        self._currentRouteKey = routeKey

        target_widget = self.items[routeKey]

        for k, item in self._items.items():
            item.setSelected(k == routeKey)

        self.scrollToWidget(target_widget)


    def currentItem(self):
        if self._currentRouteKey is None:
            return None

        return self.widget(self._currentRouteKey)
    
    def widget(self, routeKey: str):

        print(routeKey)

        if routeKey not in self.items:
            raise Exception(f"`{routeKey}` is illegal.")
        
        return self.items[routeKey]
    
 
    def scrollToWidget(self, widget: InfoCardItem, scroll_align=Qt.AlignTop):
        """
        滚动到指定部件，并支持自定义对齐方式（精准生效版）
        :param widget: 目标部件
        :param scroll_align: 对齐方式（Qt.AlignTop/Qt.AlignCenter/Qt.AlignBottom）
        """
        # 边界判断：控件为空 或 不在当前列表中，直接返回
        if not widget or widget not in self.items.values():
            return

        scroll_bar = self.verticalScrollBar() # 获取垂直滚动条
        viewport = self.viewport() # 获取滚动区域视口
        

        widget_viewport_pos = widget.mapTo(viewport, QPoint(0, 0)) # 获取控件在视口坐标系中的左上角点
        widget_size = widget.size() # 获取控件的实际尺寸（宽高）

        widget_viewport_rect = QRect(widget_viewport_pos, widget_size)

        if viewport.rect().contains(widget_viewport_rect):
            return

        viewport_height = viewport.height()
        widget_height = widget_size.height()
        current_scroll_y = scroll_bar.value()
        
        if scroll_align == Qt.AlignCenter:
            target_y = current_scroll_y + widget_viewport_pos.y() - (viewport_height - widget_height) / 2
        elif scroll_align == Qt.AlignBottom:
            target_y = current_scroll_y + widget_viewport_pos.y() - (viewport_height - widget_height)
        else:
            target_y = current_scroll_y + widget_viewport_pos.y()

        min_y = 0
        max_y = scroll_bar.maximum()
        target_y = max(min_y, min(int(target_y), max_y))
        
        scroll_bar.setValue(target_y)
        
    
 