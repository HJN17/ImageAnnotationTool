# coding:utf-8
from typing import List  # 导入List类型用于类型注解
from PyQt5.QtCore import Qt  # 导入Qt核心模块，包含对齐常量等
from PyQt5.QtWidgets import QVBoxLayout, QWidget  # 导入QVBoxLayout和QWidget类


class VBoxLayout(QVBoxLayout):
    """ 垂直盒子布局类 - 扩展QVBoxLayout，提供更便捷的控件管理方法 """

    def __init__(self, parent):
        """
        初始化垂直布局
        
        参数:
            parent: QWidget - 父窗口部件，布局将应用于此部件
        """
        super().__init__(parent)  # 调用父类QVBoxLayout的构造函数
        self.widgets = []  # 初始化一个列表，用于存储添加到布局中的所有控件

    def addWidgets(self, widgets: List[QWidget], stretch=0, alignment=Qt.AlignTop):
        """
        一次性添加多个控件到布局中
        
        参数:
            widgets: List[QWidget] - 要添加的控件列表
            stretch: int - 控件的伸缩因子，决定空间分配比例，默认为0
            alignment: Qt.AlignmentFlag - 控件在布局中的对齐方式，默认为顶部对齐
        """
        for widget in widgets:  # 遍历控件列表
            self.addWidget(widget, stretch, alignment)  # 调用自身的addWidget方法添加单个控件

    def addWidget(self, widget: QWidget, stretch=0, alignment=Qt.AlignTop):
        """
        添加单个控件到布局中
        
        参数:
            widget: QWidget - 要添加的控件对象
            stretch: int - 控件的伸缩因子，默认为0
            alignment: Qt.AlignmentFlag - 控件在布局中的对齐方式，默认为顶部对齐
        """
        super().addWidget(widget, stretch, alignment)  # 调用父类的addWidget方法添加控件到布局
        self.widgets.append(widget)  # 将控件添加到内部存储的控件列表中
        widget.show()  # 显示控件

    def removeWidget(self, widget: QWidget):
        """
        从布局中移除控件，但不删除控件对象
        
        参数:
            widget: QWidget - 要移除的控件对象
        """
        super().removeWidget(widget)  # 调用父类的removeWidget方法从布局中移除控件
        self.widgets.remove(widget)  # 从内部存储的控件列表中移除控件

    def deleteWidget(self, widget: QWidget):
        """
        从布局中移除控件并删除控件对象
        
        参数:
            widget: QWidget - 要删除的控件对象
        """
        self.removeWidget(widget)  # 调用自身的removeWidget方法从布局中移除控件
        widget.hide()  # 隐藏控件
        widget.deleteLater()  # 安排控件在适当的时候被删除

    def removeAllWidget(self):
        """
        从布局中移除所有控件，但不删除控件对象
        """
        for widget in self.widgets:  # 遍历所有存储的控件
            super().removeWidget(widget)  # 调用父类的removeWidget方法从布局中移除控件

        self.widgets.clear()  # 清空内部存储的控件列表