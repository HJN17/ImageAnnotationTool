# coding:utf-8
from typing import Union, List

from PyQt5.QtCore import Qt, QEvent, pyqtSignal
from PyQt5.QtGui import QResizeEvent, QIcon
from PyQt5.QtWidgets import QWidget

from .navigation_panel import NavigationPanel, NavigationItemPosition, NavigationDisplayMode
from .navigation_widget import NavigationPushButton
from ...common.icon import FluentIconBase


class NavigationInterface(QWidget):
    """ 导航界面组件，继承自QWidget，用于管理应用程序的导航菜单"""

    displayModeChanged = pyqtSignal(NavigationDisplayMode) 

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.panel = NavigationPanel(self)
        self.panel.installEventFilter(self)
        self.panel.displayModeChanged.connect(self.displayModeChanged)  # 连接面板的显示模式变化信号到当前界面的同名信号（转发信号）

        self.resize(50, self.height())
        self.setMinimumWidth(50)  
        self.setAttribute(Qt.WA_TranslucentBackground) 

    def addItem(self, routeKey: str, icon: FluentIconBase, text: str, onClick=None,
                 position=NavigationItemPosition.TOP, tooltip: str = None) -> NavigationPushButton:
        
        return self.panel.insertItem(-1,routeKey, icon, text, onClick,position, tooltip)

    def addItemScroll(self, routeKey: str, icon: FluentIconBase, text: str, onClick=None,
                 tooltip: str = None) -> NavigationPushButton:
        return self.panel.insertItem(-1,routeKey, icon, text, onClick,NavigationItemPosition.SCROLL, tooltip)

    def setDisabledItems(self, routeKeys:list[str]):
        self.panel.setDisabledItems(routeKeys)
    
    def setCurrentItem(self, routeKey: str):
        self.panel.setCurrentItem(routeKey)

    def addSeparator(self, position: NavigationItemPosition = NavigationItemPosition.TOP):

        self.panel.insertSeparator(-1,position)

    def eventFilter(self, obj, e: QEvent):
        """ 事件过滤器：处理导航面板的事件（如尺寸变化）"""

        if obj is not self.panel or e.type() != QEvent.Resize:
            return super().eventFilter(obj, e)

        if self.panel.displayMode != NavigationDisplayMode.MENU:
            event = QResizeEvent(e)
            
            if event.oldSize().width() != event.size().width(): # 宽度变化时更新固定宽度
                self.setFixedWidth(event.size().width()) 

        return super().eventFilter(obj, e) 

    def resizeEvent(self, e: QResizeEvent):

        if e.oldSize().height() != self.height():
            self.panel.setFixedHeight(self.height())
