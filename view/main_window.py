# coding: utf-8
import traceback
from PyQt5.QtCore import QSize, QEvent,Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from enum import Enum
from QtUniversalToolFrameWork.view.main_window import MainWindow  
from QtUniversalToolFrameWork.common.icon import FluentIcon as FIF
from QtUniversalToolFrameWork.components.navigation import NavigationInterface, NavigationItemPosition
from QtUniversalToolFrameWork.common.config import qconfig, OptionsConfigItem, ConfigItem, FolderValidator

from common.data_structure import jsonFileManager
from common import config
from resources import resource
from view.accuracy_interface import AccuracyInterface
from view.setting_interface import SetInterface
from components.accuarcy_function import DefaultMouseFunction,PolygonFunction,BboxFunction,LineFunction,PointFunction,SplitPolygonFunction

class mWindow(MainWindow):

    window_paint_count = 0
    def __init__(self):
        super().__init__()
        
    def initNavigation(self):
        """ 初始化导航栏，添加导航项和分隔符 """

        self.accuracy_interface = AccuracyInterface(self)
        self.settingInterface = SetInterface(self)

        self.defaultMouseFunction = DefaultMouseFunction(self)
        self.polygonFunction = PolygonFunction(self)
        self.bboxFunction = BboxFunction(self)
        self.lineFunction = LineFunction(self)
        self.pointFunction = PointFunction(self)
        self.splitPolygonFunction = SplitPolygonFunction(self)
        
        self.addScrollItem(self.accuracy_interface,self.defaultMouseFunction)
        self.addScrollItem(self.accuracy_interface,self.polygonFunction)
        self.addScrollItem(self.accuracy_interface,self.bboxFunction)
        self.addScrollItem(self.accuracy_interface,self.lineFunction)
        self.addScrollItem(self.accuracy_interface,self.pointFunction)
        self.addScrollItem(self.accuracy_interface,self.splitPolygonFunction)


        self.addSubInterface(self.accuracy_interface, FIF.PHOTO,'图像首页')
        self.navigationInterface.addSeparator() 

        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)

        self.accuracy_interface.installEventFilter(self.navigationInterface)
    
    def initWindow(self):
        self.resize(1100, 780)
        self.setMinimumWidth(860)
        
        self.setWindowIcon(QIcon(':/resource/images/logo.png'))
        self.setWindowTitle('图像标注工具')

    
    def closeEvent(self, e):
        jsonFileManager.exit_handler()
        super().closeEvent(e)


    def mousePressEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass
    
    def mouseMoveEvent(self, event):
        pass


    


