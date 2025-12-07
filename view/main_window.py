# coding: utf-8
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from enum import Enum
from QtUniversalToolFrameWork.view.main_window import MainWindow  
from QtUniversalToolFrameWork.common.icon import FluentIcon as FIF
from QtUniversalToolFrameWork.components.navigation import NavigationInterface, NavigationItemPosition
from QtUniversalToolFrameWork.common.config import qconfig, OptionsConfigItem, ConfigItem, FolderValidator
from common.icon import myIcon
from resources import resource
from .accuracy_interface import AccuracyInterface


class mWindow(MainWindow):
    
    def __init__(self):
        super().__init__()


    def initNavigation(self):
        """ 初始化导航栏，添加导航项和分隔符 """

        self.accuracy_interface = AccuracyInterface(self)


        #self.addScrollItem(self.imageViewInterface,self.imageViewInterface1,FIF.NAVIGATION, '导航')

        self.addSubInterface(self.homeInterface, FIF.HOME,'首页')
        self.addSubInterface(self.accuracy_interface, FIF.PHOTO,'图像工具')
        self.navigationInterface.addSeparator() 

        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)
    
    def initWindow(self):
        self.resize(980, 780)
        self.setMinimumWidth(860)
        
        self.setWindowIcon(QIcon(':/resource/images/logo.png'))
        self.setWindowTitle('图像标注工具')