# coding:utf-8
from copy import deepcopy
from PyQt5.QtCore import Qt,QRect,QRectF,QPoint,pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QWidget, QHBoxLayout, QVBoxLayout,QLineEdit
from PyQt5.QtGui import QColor, QPainter, QBrush, QPainterPath,QPen


from QtUniversalToolFrameWork.common.color import ThemeBackgroundColor
from QtUniversalToolFrameWork.common.config import isDarkThemeMode
from QtUniversalToolFrameWork.common.font import getFont
from QtUniversalToolFrameWork.common.style_sheet import setShadowEffect
from QtUniversalToolFrameWork.common.icon import FluentIcon
from QtUniversalToolFrameWork.components.widgets import ScrollArea
from QtUniversalToolFrameWork.components.widgets.label import CardLabel
from QtUniversalToolFrameWork.components.widgets.combo_box import ComboBox
from QtUniversalToolFrameWork.components.widgets.button import TransparentToolButton
from QtUniversalToolFrameWork.components.widgets.line_edit import LineEdit

from common.annotation import AnnotationType
from common.style_sheet import StyleSheet
from common.case_label import cl
from common.signal_bus import signalBus
from common.case_attrbute import cattr,AttributeType
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


class CustomLineEdit(QLineEdit):

    valueChanged = pyqtSignal(object) 

    def __init__(self, parent=None):
        super().__init__(parent) 

        self.textChanged.connect(self._onTextChanged)
        self.setAlignment(Qt.AlignLeft)  # 居中对齐
        self.setFocusPolicy(Qt.NoFocus)  # 设置无焦点策略
        self.setFixedHeight(25)  # 设置固定高度
        self.setFont(getFont(14))  # 设置字体

        StyleSheet.INFO_CARD.apply(self)

    def setValue(self, value: str):
        self.setText(value) 

    def value(self) -> str:
        return self.text() 

    def _onTextChanged(self, text):

        value = self.value()
        if value is not None:
            self.valueChanged.emit(value)  # 发射值变化信号

    def mousePressEvent(self, event):
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        super().mousePressEvent(event)

    def focusOutEvent(self, event):
        self.setFocusPolicy(Qt.NoFocus)
        super().focusOutEvent(event)



class InfoCardItem(QWidget):

    def __init__(self,data_item:DataItemInfo, parent=None):
        super().__init__(parent)

        self._data = deepcopy(data_item)

        self._color = cl.get_color(self._data.caseLabel)
        self._case_label = self._data.caseLabel if self._data.caseLabel in cl.get_all_labels() else "default"

        self._annotation_type = CardLabel(self._data.annotation_type.value.upper(), self)
        self._label_comboBox = InfoCardComboBox(self)

        self._personButton = TransparentToolButton(FluentIcon.ROBOT, self) 
        self._viewButton = TransparentToolButton(FluentIcon.VIEW, self) # HIDE
        self._pinButton = TransparentToolButton(FluentIcon.PIN, self) # UNPIN
        self._delButton = TransparentToolButton(FluentIcon.DELETE, self)
        self._delButton.setToolTip("删除标注框 [B]")

        self._label_comboBox.addItems(cl.get_all_labels())
        self._label_comboBox.setCurrentText(self._case_label)

        cl.add_label_changed.connect(self._add_comboBox_item)
        cl.del_label_changed.connect(self._del_comboBox_item)
        cl.color_label_changed.connect(self._update_color)
        cl.show_label_changed.connect(self._update_show)

        self._label_comboBox.currentTextChanged.connect(lambda text: self._set_case_label(text))
        self._label_comboBox.currentTextChanged.connect(self.update)

        self._delButton.clicked.connect(dm.delete_current_item)

        self._init_ui()
    
    def _init_ui(self):
        StyleSheet.INFO_CARD.apply(self)
        self.setFixedWidth(290)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(10, 20, 10, 20)

        self._annotation_type.setFixedSize(60, 31)
        self._label_comboBox.setFixedSize(170, 31)
        
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)
        type_layout.setContentsMargins(20, 0, 20, 0)
        type_layout.addWidget(self._annotation_type, 0, Qt.AlignLeft)
        type_layout.addWidget(self._label_comboBox, 0, Qt.AlignLeft)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(20, 0, 0, 0)
        button_layout.addWidget(self._personButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._viewButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._pinButton, 0, Qt.AlignLeft)
        button_layout.addWidget(self._delButton, 0, Qt.AlignLeft)

        self.vBoxLayout.addLayout(type_layout)
        self.vBoxLayout.addLayout(button_layout)
        
        self.vBoxLayout.setSpacing(20)

        attr_items = cattr.get_items(self._case_label)

        if attr_items:
            self.attr_group = QGroupBox("属性选项", self)
            self.attr_group.setFont(getFont(13))
            attr_group_vBoxLayout = QVBoxLayout(self.attr_group)
            attr_group_vBoxLayout.setSpacing(10)
            attr_group_vBoxLayout.setContentsMargins(20, 20, 20, 10)
            attr_group_vBoxLayout.setAlignment(Qt.AlignTop)
            
            for attr in attr_items:
                attr_layout = QHBoxLayout()
                attr_layout.setSpacing(20)
                attr_layout.setContentsMargins(0, 0, 0, 0)
                temp_attr_name = CardLabel(attr["attr_name"], self)

                if attr["attr_type"] == AttributeType.OPTION.value:
                    temp_attr_value = InfoCardComboBox(self)
                    attr_name = attr["attr_name"]
                    temp_attr_value.addItems(attr["attr_value"])

                    if self._data.is_attribute_exist(attr_name):
                        temp_attr_value.setCurrentText(self._data.get_attribute_value(attr_name))
                    else:
                        dm.set_current_attribute(attr_name, temp_attr_value.currentText())

                    temp_attr_value.currentTextChanged.connect(
                        lambda text, name=attr_name: dm.set_current_attribute(name, text)
                    )
                else:
                    temp_attr_value = CustomLineEdit(self)
                    attr_name = attr["attr_name"]
                    if self._data.is_attribute_exist(attr_name):
                        temp_attr_value.setText(self._data.get_attribute_value(attr_name))

                    temp_attr_value.textChanged.connect(
                        lambda text, name=attr_name: dm.set_current_attribute(name, text)
                    )

                temp_attr_name.setFixedSize(50, 27)
                temp_attr_value.setFixedSize(160, 27)

                attr_layout.addWidget(temp_attr_name, 0, Qt.AlignLeft)
                attr_layout.addWidget(temp_attr_value, 0, Qt.AlignLeft)
                attr_group_vBoxLayout.addLayout(attr_layout)

            self.vBoxLayout.addWidget(self.attr_group)

        self._adjustViewSize()
        setShadowEffect(self,blurRadius=10, offset=(0, 2), color=QColor(0, 0, 0, 50))

        
    def _update_color(self, label: str):
        if label == self._case_label:
            self._color = cl.get_color(label)
            self.update()

    def _add_comboBox_item(self, label: str):
        
        self._label_comboBox.addItem(label)

        if self._data.caseLabel == label:
            self._set_case_label(label)
            self._label_comboBox.setCurrentText(label)
        
    def _del_comboBox_item(self, label: str):

        index = self._label_comboBox.findText(label)
        if index != -1:
            
            if self._case_label == label:
                self._set_case_label("default")
                self._label_comboBox._set_temp_text("default")

            self._label_comboBox.removeItem(index)


    def _set_case_label(self, case_label: str):

        self._case_label = case_label if case_label in cl.get_all_labels() else "default"

        if self._case_label != "default":
            self._data.caseLabel = case_label

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
    
    def _adjustViewSize(self):
        h = self.vBoxLayout.sizeHint().height()
        self.setFixedHeight(h)

class InfoCardInterface(ScrollArea):
   
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scrollWidget = QWidget(self)

        dm.select_data_item.connect(self.show_item)

    

        cattr.update_attr_changed.connect(lambda:self.show_item(dm.current_data_item))

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

        self.all_hide()

        if data_item is None:
            return
        
        if not cl.is_show(data_item.caseLabel):
            return

        widget = InfoCardItem(data_item, self.scrollWidget)

        self.vBoxLayout.addWidget(widget)
    
   
    def all_hide(self):
    
        for i in reversed(range(self.vBoxLayout.count())): 
            w = self.vBoxLayout.itemAt(i).widget()
            
            if isinstance(w, InfoCardItem):
                w.hide() # 移除部件
                w.deleteLater()
            

 