# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class HomeInterface(QWidget):
    """ 首页界面类：继承自ScrollArea，用于显示应用的主要功能示例卡片 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        self.__initWidget()

    def __initWidget(self):
        """ 初始化界面基础配置：设置样式、滚动属性和布局参数 """
        self.view.setObjectName('view')
        self.setObjectName('homeInterface')
       
        self.vBoxLayout.setContentsMargins(0, 0, 0, 30)
        self.vBoxLayout.setSpacing(30)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

