# coding:utf-8
from typing import List
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QSize,QRectF
from PyQt5.QtGui import QPainter, QColor,QPen
from PyQt5.QtWidgets import (QPushButton, QInputDialog, QWidget, QLabel,
                             QHBoxLayout, QToolButton, QSizePolicy)

from QtUniversalToolFrameWork.common.icon import FluentIcon
from QtUniversalToolFrameWork.common.style_sheet import setShadowEffect

from QtUniversalToolFrameWork.common.config import ConfigItem,qconfig
from QtUniversalToolFrameWork.common.color import themeColor
from QtUniversalToolFrameWork.components.settings.expand_setting_card import ExpandSettingCard
from QtUniversalToolFrameWork.components.layout.flow_layout import FlowLayout
from QtUniversalToolFrameWork.components.dialog_box import CustomMessageBoxBase,CustomMessageBox
from QtUniversalToolFrameWork.components.widgets.button import TransparentToolButton,PushButton,ColorButton
from QtUniversalToolFrameWork.components.widgets.label import BodyLabel,CaptionLabel
from QtUniversalToolFrameWork.components.widgets.line_edit import LineEdit

from common.case_label import cl



class AddLabelMessageBox(CustomMessageBoxBase):
    """ 标签列表设置消息框 """
    
    yesButtonClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel('添加标签', self)
        self.inputLineEdit = LineEdit(self)
        
        self.inputLineEdit.setPlaceholderText('输入标签名称')
        self.inputLineEdit.setClearButtonEnabled(True)
        self.inputLineEdit.clearButton.setFixedSize(19, 19)

        self.warningLabel = CaptionLabel("标签名称不能为空")
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
        label_name = self.inputLineEdit.text().strip()
        if not label_name:
            self.warningLabel.show()
            return
        self.warningLabel.hide()
        self.yesButtonClicked.emit(label_name)

    def showEvent(self, e):
        self.inputLineEdit.clear()
        self.inputLineEdit.setFocus()
        
        return super().showEvent(e)


class LabelItem(QWidget):

    removed = pyqtSignal(QWidget)

    def __init__(self, label_name: str,color:QColor, parent=None):
        super().__init__(parent=parent)
        
        self._label_name = label_name
        self._color = color

        self._colorButton = ColorButton(label_name,color,self)

        self._closeButton = TransparentToolButton(FluentIcon.CLOSE, self)
        # self._closeButton.setFixedSize(39, 29)
        self._closeButton.setIconSize(QSize(12, 12))

        self._closeButton.clicked.connect(
            lambda: self.removed.emit(self))

        #setShadowEffect(self,blurRadius=10, offset=(0, 1), color=QColor(0, 0, 0, 60))
        if label_name == "default":
            self._closeButton.hide()

        cl.color_label_changed.connect(self._update_color)

        self._init_ui()

    def _init_ui(self):
            
        self.setFixedHeight(30)
        self._colorButton.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed) # QSizePolicy.Ignored 忽略父布局的宽度策略

        hBoxLayout = QHBoxLayout(self)
        hBoxLayout.setContentsMargins(0, 0, 30, 0)
        
        #self._labelLabel.setFixedWidth(120)

        hBoxLayout.addWidget(self._colorButton, 0, Qt.AlignLeft)
        hBoxLayout.addSpacing(16)
        hBoxLayout.addStretch(1)
        hBoxLayout.addWidget(self._closeButton, 0, Qt.AlignRight)
        hBoxLayout.setAlignment(Qt.AlignVCenter)

    @property
    def label_name(self):
        return self._label_name
    
    def _update_color(self, label: str):
        if label == self._label_name:
            self._color = cl.get_color(label)
            self._colorButton.setColor(self._color)


class LabelListSettingCard(ExpandSettingCard):
    """ 标签列表设置卡片    """

    def __init__(self, configItem: ConfigItem, title: str, content: str = None, parent=None):
        
        super().__init__(FluentIcon.LABEL, title, content, parent)
        self.configItem = configItem
        self.addFolderButton = PushButton("添加标签", self, FluentIcon.ADD)

        #在应用的中间展示
        self._msgBox = AddLabelMessageBox(self.window())
        self._msgBox.yesButtonClicked.connect(self._onAddLabel)
        self._msgBox.hide()
        self._init_ui()

    def _init_ui(self):

        self.addWidget(self.addFolderButton)

        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setSpacing(19) 
        self.viewLayout.setContentsMargins(48, 18, 0, 18)
        
        labels = qconfig.get(self.configItem).copy()

        for label in labels:
            self._addLabelItem(label)

        self.addFolderButton.clicked.connect(self._msgBox.show)

        
    def _addLabelItem(self, label: str):
        
        cl.set_label(label)

        color = cl.get_color(label)
        
        item = LabelItem(label, color, self.view)
        item.removed.connect(self._removeLabel)
        self.viewLayout.addWidget(item)
        item.show()
        self._adjustViewSize()

    def _onAddLabel(self, label_name: str):

        if label_name in cl.get_all_labels():
            return

        self._addLabelItem(label_name)
        qconfig.set(self.configItem, cl.get_all_labels())

    def _removeLabel(self, item: LabelItem):

        if item.label_name not in cl.get_all_labels():
            return
        
        cl.remove_label(item.label_name)
        self.viewLayout.removeWidget(item)
        item.deleteLater()
        self._adjustViewSize()
        qconfig.set(self.configItem, cl.get_all_labels())
