# coding:utf-8
from typing import Iterable
from PyQt5.QtCore import Qt, pyqtSignal,QPoint
from PyQt5.QtWidgets import (QApplication , QHBoxLayout, QPushButton)

from ...common.style_sheet import FluentStyleSheet

#导入PickerPanel
from .picker_base import PickerPanel, PickerColumnButton


class PickerBase(QPushButton):
    """ 选择器基类
    提供选择器的基本功能，如添加列、设置值等
    """
    valueChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        self.columnValues = []   # 初始化列值列表

        self.columns = []   # 初始化列列表

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetFixedSize) # 设置布局大小约束为固定大小
        FluentStyleSheet.TIME_PICKER.apply(self)

        self.clicked.connect(self._showPanel) # 连接点击信号到显示面板槽函数

    
    def addColumn(self, name: str, items: Iterable, width: int, align=Qt.AlignCenter,columnFormatter = lambda c: c):
        """ 添加列
        name: 列名称
        items: 列中的项目列表
        width: 列宽度
        align: 文本对齐方式
        columnFormatter: 列格式化函数，用于格式化列中的项目
        """
        button = PickerColumnButton(name, items, width,columnFormatter, align,self)
        
        self.columns.append(button)

        self.hBoxLayout.addWidget(button, 0, Qt.AlignLeft)

        for btn in self.columns[:-1]:
            btn.setProperty('hasBorder', True)
            btn.setStyle(QApplication.style())


    def listValue(self):
        """ 获取所有列的值 """
        return [c.value for c in self.columns]

    def enterEvent(self, e):
        """ 鼠标进入事件 """
       
        self._setButtonProperty('enter', True) # 设置按钮属性为鼠标进入状态

    def leaveEvent(self, e):
        """ 鼠标离开事件 """
       
        self._setButtonProperty('enter', False)

    def mousePressEvent(self, e):
        """ 鼠标按下事件 """
       
        self._setButtonProperty('pressed', True)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """ 鼠标释放事件 """
       
        self._setButtonProperty('pressed', False)
        super().mouseReleaseEvent(e)

    def _setButtonProperty(self, name, value):
        """ 向所有选择器按钮发送事件 """
    
        for button in self.columns:
            button.setProperty(name, value)
            button.setStyle(QApplication.style())

    def _showPanel(self):
        """ 显示选择面板
        """
        panel = PickerPanel(self)

        _ = [panel.addColumn(column.items, column.width(),column.align) for column in self.columns] # 添加所有列到面板

        panel.setValue(self.listValue()) # 设置面板初始值

        panel.confirmed.connect(self._onConfirmed)

        w = panel.vBoxLayout.sizeHint().width() - self.width() # 计算面板宽度，减去选择器宽度
        ITEM_HEIGHT = 37
        panel.exec(self.mapToGlobal(QPoint(-w//2, -ITEM_HEIGHT * 4+2))) # 显示面板并执行动画

    def _onConfirmed(self, value: list):
        """ 确认选择后的处理 """
        for i, v in enumerate(value):
            self.columns[i].setValue(v)

        if self.columnValues != value:
            self.columnValues = value
            self.valueChanged.emit(value)

    

"""
Displayable Components  """

class TimePicker(PickerBase):
    """ 24小时制时间选择器，提供小时、分钟、秒的选择功能 """

    WIDTH = 80

    def __init__(self, parent=None):
        super().__init__(parent)


        self.addColumn("小时", range(0, 24),self.WIDTH,columnFormatter=self.defaultColumnFormatter)
        self.addColumn("分钟", range(0, 60),self.WIDTH,columnFormatter=self.defaultColumnFormatter)
        self.addColumn("秒", range(0, 60),self.WIDTH,columnFormatter=self.zfillColumnFormatter)

    def zfillColumnFormatter(self, value):
        return str(value).zfill(2)
    
    def defaultColumnFormatter(self,value):
        return str(value)
    