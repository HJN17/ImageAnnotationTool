# coding: utf-8
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from ..common.config import qconfig
from ..common.icon import FluentIcon as FIF,Icon
from ..common.theme_listener import SystemThemeListener

from ..components.window import FluentWindow, SplashScreen
from ..components.navigation import NavigationInterface, NavigationItemPosition
from ..resources import resource

from .home_interface import HomeInterface
from .setting_interface import SettingInterface

class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__() 

        self.initWindow()

    
        self.themeListener = SystemThemeListener(self)

        self.homeInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)

        self.initNavigation()

        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(128, 128))
        self.splashScreen.raise_()

        desktop = QApplication.desktop().availableGeometry() # 获取桌面可用区域尺寸
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()



        QTimer.singleShot(100, self.splashScreen.finish) 
        self.themeListener.start()

    def initNavigation(self):
        """ 初始化导航栏，添加导航项和分隔符 """

       #self.addScrollItem(self.imageViewInterface,self.imageViewInterface1,FIF.NAVIGATION, '导航')

        self.addSubInterface(self.homeInterface, FIF.HOME,'首页')
        #self.addSubInterface(self.imageViewInterface, FIF.PHOTO,'图像工具')
        self.navigationInterface.addSeparator() 

        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)

    

    def initWindow(self):
        self.resize(980, 780)
        self.setMinimumWidth(860)
        
        self.setWindowIcon(QIcon(':/resource/images/logo.png'))
        self.setWindowTitle('FrameCoreTool')
    

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size()) 

    def closeEvent(self, e):
        self.themeListener.terminate()  # 终止主题监听器线程
        self.themeListener.deleteLater()  # 安排主题监听器对象稍后删除(释放资源)
        super().closeEvent(e)
