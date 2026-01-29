# coding:utf-8

from PyQt5.QtCore import Qt,QRect,QRectF,QPoint
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen

from QtUniversalToolFrameWork.common.style_sheet import setShadowEffect
from QtUniversalToolFrameWork.common.icon import FluentIcon
from QtUniversalToolFrameWork.components.widgets import ScrollArea
from QtUniversalToolFrameWork.components.widgets.label import CardLabel
from QtUniversalToolFrameWork.components.widgets.combo_box import ComboBox
from QtUniversalToolFrameWork.components.widgets.button import TransparentToolButton

from common.annotation import AnnotationType
from common.style_sheet import StyleSheet
from common.case_label import cl
from common.signal_bus import signalBus
from common.data_control_manager import dm,DataItemInfo

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

    def __init__(self,caseLabel : str, annotation_type:AnnotationType, parent=None):
        super().__init__(parent)

        self._color = cl.get_color(caseLabel)
        self._original_case_label = caseLabel
        self._case_label = caseLabel if caseLabel in cl.get_all_labels() else "default"

        self._annotation_type = CardLabel(annotation_type.value.upper(), self)
        self._comboBox = InfoCardComboBox(self)

        self._personButton = TransparentToolButton(FluentIcon.ROBOT, self) 
        self._viewButton = TransparentToolButton(FluentIcon.VIEW, self) # HIDE
        self._pinButton = TransparentToolButton(FluentIcon.PIN, self) # UNPIN
        self._delButton = TransparentToolButton(FluentIcon.DELETE, self)
        self._delButton.setToolTip("删除标注框 [B]")


        self._comboBox.addItems(cl.get_all_labels())
        self._comboBox.setCurrentText(self._case_label)

        cl.add_label_changed.connect(self._add_comboBox_item)
        cl.del_label_changed.connect(self._del_comboBox_item)
        cl.color_label_changed.connect(self._update_color)
        cl.show_label_changed.connect(self._update_show)

        self._comboBox.currentTextChanged.connect(lambda text: self._set_case_label(text))
        self._comboBox.currentTextChanged.connect(self.update)

        self._init_ui()
    
    def _init_ui(self):
        
        self.setFixedSize(290, 110)
        vBoxLayout = QVBoxLayout(self)
        vBoxLayout.setSpacing(0)
        vBoxLayout.setContentsMargins(20, 0, 20, 0)

        self._annotation_type.setFixedSize(60, 31)
        self._comboBox.setFixedSize(170, 31)
        
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.addWidget(self._annotation_type, 0, Qt.AlignLeft)
        type_layout.addWidget(self._comboBox, 0, Qt.AlignLeft)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(10, 0, 0, 0)
        button_layout.addWidget(self._personButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._viewButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._pinButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._delButton, 0, Qt.AlignLeft)

        vBoxLayout.addLayout(type_layout)
        vBoxLayout.addLayout(button_layout)


        setShadowEffect(self,blurRadius=10, offset=(0, 2), color=QColor(0, 0, 0, 50))

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
        dm.item_label_changed(self._case_label)
    

    def is_show(self) -> bool:
        return self._is_show

    def _update_show(self, label: str): 
        if label == self._case_label:
            self._is_show = cl.is_show(label)
            self.setVisible(self._is_show)


    def paintEvent(self, event):

        painter = QPainter(self)
        
        rect_f = QRectF(self.rect().adjusted(1, 1, -1, -1))

        painter.setRenderHint(QPainter.Antialiasing) # 开启反锯齿

        painter.setBrush(self._color)
        painter.setPen(Qt.NoPen)

        _radius = 6
        
        painter.drawRoundedRect(rect_f, _radius, _radius)

        super().paintEvent(event)
    

class InfoCardInterface(ScrollArea):
   
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scrollWidget = QWidget(self)

        self._temp_widget = QWidget()

        dm.select_data_item.connect(self.show_item)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条

        self._init_ui()

    def _init_ui(self):
        
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        
        self.setViewportMargins(5, 0, 5, 0)
        self.setWidgetResizable(True)
        self.setWidget(self.scrollWidget)

        self.scrollWidget.setObjectName('scrollWidget')

        StyleSheet.ACCURACY_INTERFACE.apply(self)
    

    def show_item(self, data_item:DataItemInfo):

        if data_item is None:
            self._temp_widget.hide()
            return

        widget = InfoCardItem(data_item.caseLabel, data_item.annotation_type, self.scrollWidget)

        self.replace_temp_widget(widget)
    
        
    def replace_temp_widget(self,widget:InfoCardItem):
        self.vBoxLayout.replaceWidget(self._temp_widget,widget) # 替换临时widget为infoCard
        self._temp_widget.hide()# 隐藏临时widget
        widget.show()
        self._temp_widget = widget
 