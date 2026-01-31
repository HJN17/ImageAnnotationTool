# coding:utf-8
from typing import List
from pathlib import Path
from copy import deepcopy
from enum import Enum
from PyQt5.QtCore import Qt, pyqtSignal, QSize,QEvent
from PyQt5.QtGui import QPainter, QColor,QPen,QFont
from PyQt5.QtWidgets import (QPushButton, QInputDialog, QWidget, QLabel,
                             QHBoxLayout, QToolButton, QSizePolicy)

from QtUniversalToolFrameWork.common.icon import FluentIcon
from QtUniversalToolFrameWork.common.style_sheet import setShadowEffect
from QtUniversalToolFrameWork.common.font import getFont
from QtUniversalToolFrameWork.common.config import ConfigItem,qconfig
from QtUniversalToolFrameWork.common.color import themeColor
from QtUniversalToolFrameWork.components.settings.expand_setting_card import ExpandSettingCard
from QtUniversalToolFrameWork.components.layout.flow_layout import FlowLayout
from QtUniversalToolFrameWork.components.dialog_box import CustomMessageBoxBase,CustomMessageBox
from QtUniversalToolFrameWork.components.widgets.button import TransparentToolButton,PushButton,TransparentPushButton
from QtUniversalToolFrameWork.components.widgets.label import BodyLabel,CaptionLabel,FluentLabelBase
from QtUniversalToolFrameWork.components.widgets.line_edit import CustomLineEdit,LineEdit
from QtUniversalToolFrameWork.components.widgets.combo_box import ComboBox
from QtUniversalToolFrameWork.components.widgets.tool_tip import ToolTipFilter
from common.case_label import cl
from common.signal_bus import signalBus
from common.case_attrbute import cattr,AttributeType
from common.message import message

class AttributeMessageBox(CustomMessageBoxBase):
    """ 属性列表设置消息框 """

    yesButtonClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel('选择标签', self)

        self._comboBox = AttributeComboBox(self)

        self._comboBox.addItems(cl.get_all_labels())
        self._comboBox.setCurrentText(self._comboBox.items[0])

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(12)
        self.viewLayout.addWidget(self._comboBox, 0, Qt.AlignVCenter)

        self.yesButton.setText('选择')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)
        self.yesButton.clicked.connect(self._onYesButtonClicked)

    def _onYesButtonClicked(self):
        label_name = self._comboBox.currentText()
        self.yesButtonClicked.emit(label_name)

    
    def showEvent(self, event):

        super().showEvent(event)

        self._comboBox.clear()
        self._comboBox.addItems(cl.get_all_labels())

        self._comboBox.setCurrentText(self._comboBox.items[0])


#选项值的消息框
class OptionValueMessageBox(CustomMessageBoxBase):
    """ 选项值设置消息框 """
    
    yesButtonClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel('添加选项值', self)
        self.inputLineEdit = LineEdit(self)
        
        self.inputLineEdit.setPlaceholderText('输入选项值')
        self.inputLineEdit.setClearButtonEnabled(True)
        self.inputLineEdit.clearButton.setFixedSize(19, 19)

        self.warningLabel = CaptionLabel("选项值不能为空")
        self.warningLabel.setTextColor("#cf1010", QColor(255, 28, 32))

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(12)
        self.viewLayout.addWidget(self.inputLineEdit, 0, Qt.AlignVCenter)
        self.viewLayout.addWidget(self.warningLabel)
        self.warningLabel.hide()

        # change the text of button
        self.yesButton.setText('添加')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)

        self.yesButton.clicked.connect(self._onYesButtonClicked)

    def _onYesButtonClicked(self):
        option_value = self.inputLineEdit.text().strip()
        if not option_value:
            self.warningLabel.show()
            return
        self.warningLabel.hide()
        self.yesButtonClicked.emit(option_value)

    def showEvent(self, e):
        self.inputLineEdit.clear()
        self.inputLineEdit.setFocus()
        
        return super().showEvent(e)


class AttributeLabel(FluentLabelBase):
    """ 文字体标签 """
    def getFont(self):
        # 加微粗字体,
        return getFont(15, weight=QFont.DemiBold)
    
class OptionLabel(FluentLabelBase):
    """ 选项类型标签 """

    
    def getFont(self):
        return getFont(14)
    
    def setTextColor(self, light=QColor(80, 80, 80), dark=QColor(200, 200, 200)):
        super().setTextColor(light=light, dark=dark)

class AttributeComboBox(ComboBox):

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


class AttributeItem(QWidget):

    removed = pyqtSignal(QWidget)

    def __init__(self, label_name: str,attr_name:str="", attr_type: str = AttributeType.INPUT.value,attr_value:List[str] = [], parent=None):
        super().__init__(parent=parent)
        
        self.label_name = label_name
        self._color = cl.get_color(label_name)

        self.attr_name = attr_name
        self.attr_type = attr_type
        self.attr_value = deepcopy(attr_value)
        
        #在应用的中间展示
    
        self._label = AttributeLabel(self.label_name, self)
        self._label.setTextColor(self._color, self._color)

        self.inputLineEdit = CustomLineEdit(self)

        if self.attr_name:
            self.inputLineEdit.setText(self.attr_name)
        
        self.inputLineEdit.setPlaceholderText('输入属性名称')
    

        self._type_name = OptionLabel("选项类型:", self)

        self._typeComboBox = AttributeComboBox(self)
        self._typeComboBox.addItems([item.value for item in AttributeType])
        self._typeComboBox.setCurrentText(AttributeType.INPUT.value)


        self._value_name = OptionLabel("选项值:", self)
        self._valueComboBox = AttributeComboBox(self)

        if self.attr_value:
            self._valueComboBox.addItems(self.attr_value)
        
            

        self._addValueButton = TransparentToolButton(FluentIcon.ADD,self)
        self._addValueButton.setToolTip("添加选项值")
        self._addValueButton.installEventFilter(ToolTipFilter(self._addValueButton, 1000))# 安装工具提示事件过滤器，延迟1000ms显示工具提示
        
        self._delValueButton = TransparentToolButton(FluentIcon.REMOVE,self)
        self._delValueButton.setToolTip("删除当前选项值")
        self._delValueButton.installEventFilter(ToolTipFilter(self._delValueButton, 1000))# 安装工具提示事件过滤器，延迟1000ms显示工具提示

        self._closeButton = TransparentToolButton(FluentIcon.CLOSE, self)
        self._closeButton.setIconSize(QSize(12, 12))

        self._msgBox = OptionValueMessageBox(self.window())
        self._msgBox.yesButtonClicked.connect(self._add_value_comboBox)
        self._msgBox.hide()
    
        self.inputLineEdit.textChanged.connect(self._set_attr_name)

        self._typeComboBox.currentTextChanged.connect(self._set_attr_type)

        self._addValueButton.clicked.connect(self._msgBox.show)
        self._delValueButton.clicked.connect(self._remove_value_comboBox)
        
        self._closeButton.clicked.connect(lambda: self.removed.emit(self))

        self._show_by_type(self.attr_type)

        self._init_ui()

    def _init_ui(self):
            
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed) # QSizePolicy.Ignored 忽略父布局的宽度策略

        hBoxLayout = QHBoxLayout(self)
        hBoxLayout.setContentsMargins(0, 0, 30, 0)
        self._label.setFixedSize(60, 29)
        hBoxLayout.addWidget(self._label, 0, Qt.AlignLeft)
        hBoxLayout.addSpacing(20)
        self.inputLineEdit.setFixedSize(150, 29)
        hBoxLayout.addWidget(self.inputLineEdit, 0, Qt.AlignLeft)
        hBoxLayout.addSpacing(30)

        hBoxLayout.addWidget(self._type_name, 0, Qt.AlignLeft)
        hBoxLayout.addSpacing(10)
        self._typeComboBox.setFixedSize(90, 29)
        hBoxLayout.addWidget(self._typeComboBox, 0, Qt.AlignLeft)
        hBoxLayout.addSpacing(30)


        hBoxLayout.addWidget(self._value_name, 0, Qt.AlignLeft)
        hBoxLayout.addSpacing(10)
        self._valueComboBox.setFixedSize(130, 29)
        hBoxLayout.addWidget(self._valueComboBox, 0, Qt.AlignLeft)
        hBoxLayout.addSpacing(5)
        hBoxLayout.addWidget(self._addValueButton, 0, Qt.AlignLeft)
        hBoxLayout.addWidget(self._delValueButton, 0, Qt.AlignLeft)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(self._closeButton, 0, Qt.AlignRight)
        hBoxLayout.setAlignment(Qt.AlignVCenter)

    def _set_attr_name(self,attr_name: str):
        self.attr_name = attr_name

    def _set_attr_type(self,attr_type: str):
        self.attr_type = attr_type
        self._show_by_type(attr_type)

    def _show_by_type(self,attr_type: str = AttributeType.INPUT.value):

        if attr_type == AttributeType.INPUT.value:
            self._value_name.hide()
            self._valueComboBox.hide()
            self._addValueButton.hide()
            self._delValueButton.hide()

        else:
            self._value_name.show()
            self._valueComboBox.show()
            self._addValueButton.show()
            self._delValueButton.show() if self._valueComboBox.count() > 0 else self._delValueButton.hide()
    
    def _add_value_comboBox(self, value: str):
        self.attr_value.append(value)
        self._valueComboBox.addItem(value)
        self._delValueButton.show()
        
    def _remove_value_comboBox(self):

        if self._valueComboBox.currentIndex() == -1:
            return
        
        self.attr_value.remove(self._valueComboBox.currentText())
        self._valueComboBox.removeItem(self._valueComboBox.currentIndex())

        self._valueComboBox.setCurrentIndex(self._valueComboBox.count() - 1) if self._valueComboBox.count() > 0 else self._valueComboBox.setCurrentText("")

        self._delValueButton.hide() if self._valueComboBox.count() == 0 else self._delValueButton.show()

class AttributeListSettingCard(ExpandSettingCard):
    """ 标签列表设置卡片    """

    def __init__(self, configItem: ConfigItem, title: str, content: str = None, parent=None):
        
        super().__init__(FluentIcon.BOOK_SHELF, title, content, parent)
        self.configItem = configItem
        self.selectButton = PushButton("选择标签", self, FluentIcon.LABEL)
        self.saveButton = PushButton("保存属性", self, FluentIcon.SAVE)

        self._items = []

        attrs = qconfig.get(self.configItem).copy()
        for item in attrs:
            self._addAttrlItem(item.get("label_name"),item.get("attr_name"),item.get("attr_type"),item.get("attr_value") if item.get("attr_value") else [])

        self.save_all_attributes(False)

        #在应用的中间展示
        self._msgBox = AttributeMessageBox(self.window())
        self._msgBox.yesButtonClicked.connect(self._onAddLabel)
        self._msgBox.hide()

        self.selectButton.clicked.connect(self._msgBox.show)
        self.saveButton.clicked.connect(lambda: self.save_all_attributes(True))
        
        self._init_ui()

    def _init_ui(self):

        self.addWidget(self.selectButton)
        self.addWidget(self.saveButton)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setSpacing(19) 
        self.viewLayout.setContentsMargins(48, 18, 0, 18)

    def _addAttrlItem(self,label_name:str,attr_name:str="", attr_type: str = AttributeType.INPUT.value,attr_value:List[str]=[]):

        item = AttributeItem(label_name,attr_name,attr_type,attr_value,self.view)  
        item.setObjectName(label_name)
        item.removed.connect(self._removeAttr)

        self._items.append(item)
        
        index = -1
        for i in range(self.viewLayout.count()):
            if self.viewLayout.itemAt(i).widget().objectName() == label_name:
                index = i
                break
    
        self.viewLayout.insertWidget(index, item)
        item.show()
        self._adjustViewSize()

    def _onAddLabel(self, label_name: str):
        self._addAttrlItem(label_name)

    def _removeAttr(self, item: AttributeItem):
        
        if item in self._items:
            self._items.remove(item)

        self.viewLayout.removeWidget(item)
        item.deleteLater()
        self._adjustViewSize()

    def save_all_attributes(self,show_msg:bool=True):
        all_attributes = []

        #优先保存default属性
        for item in self._items :
            if item.label_name == "default":
                attr_data = {
                    "label_name": item.label_name,
                    "attr_name": item.attr_name,
                    "attr_type": item.attr_type,
                    "attr_value": deepcopy(item.attr_value),
                }
                all_attributes.append(attr_data)


        for item in self._items:
            if item.label_name != "default":
                attr_data = {
                    "label_name": item.label_name,
                    "attr_name": item.attr_name,
                    "attr_type": item.attr_type,
                    "attr_value": deepcopy(item.attr_value),
                }
                all_attributes.append(attr_data)
        
        cattr.set_attr(all_attributes,show_msg)
