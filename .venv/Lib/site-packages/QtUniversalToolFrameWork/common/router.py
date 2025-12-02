# coding:utf-8

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QStackedWidget 


class StackedRouter(QObject):
    """ 路由管理器 - 管理多个堆栈窗口部件的路由历史，提供页面跳转功能 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._stackedWidgets = {}

    def get(self, routeKey: str) -> QStackedWidget:
        """ 获取指定路由键对应的堆栈窗口部件 """
        return self._stackedWidgets.get(routeKey, None)

    def set(self, routeKey: str, stacked: QStackedWidget):
        
        self._stackedWidgets[routeKey] = stacked

    def pop(self):

        if not self._stackedWidgets: 
            return

        self._stackedWidgets.popitem() 

    def remove(self, routeKey: str):
      
        if routeKey in self._stackedWidgets:
            del self._stackedWidgets[routeKey]

       

router = StackedRouter()