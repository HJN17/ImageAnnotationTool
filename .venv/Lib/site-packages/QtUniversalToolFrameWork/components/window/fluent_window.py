# coding:utf-8
import sys 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel,QStackedWidget

from ...common.config import qconfig 
from ...common.router import router
from ...common.color import ThemeBackgroundColor
from ...common.icon import FluentIconBase 
from ...common.style_sheet import FluentStyleSheet
from ...common.animation import BackgroundAnimation 

from ...components.navigation import NavigationInterface, NavigationItemPosition, NavigationPushButton
from ...components.window.stacked_widget import StackedWidget 
from ...common.menu_icon_manager import mfb

from qframelesswindow import FramelessWindow,TitleBar, TitleBarBase



class FluentTitleBar(TitleBar):
    """ 自定义Fluent风格标题栏 """

    def __init__(self, parent):
        super().__init__(parent) 

        self.setFixedHeight(48)

        self.hBoxLayout.removeWidget(self.minBtn)
        self.hBoxLayout.removeWidget(self.maxBtn)
        self.hBoxLayout.removeWidget(self.closeBtn)

        self.iconLabel = QLabel(self) 
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertWidget(0, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.window().windowIconChanged.connect(self.setIcon)

        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(1, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.titleLabel.setObjectName('titleLabel')

        self.window().windowTitleChanged.connect(self.setTitle) # 连接窗口标题变化信号到setTitle方法（窗口标题更新时同步标签）

        self.vBoxLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(0) 
        self.buttonLayout.setContentsMargins(0, 0, 0, 0) 
        self.buttonLayout.setAlignment(Qt.AlignTop)
        self.buttonLayout.addWidget(self.minBtn)
        self.buttonLayout.addWidget(self.maxBtn)
        self.buttonLayout.addWidget(self.closeBtn)
        self.vBoxLayout.addLayout(self.buttonLayout)  
        self.vBoxLayout.addStretch(1) 
        self.hBoxLayout.addLayout(self.vBoxLayout, 0) 


    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize() 

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))

class FluentWindow(BackgroundAnimation, FramelessWindow):
    """ 自定义Fluent窗口 """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTitleBar(FluentTitleBar(self))

        self.navigationInterface = NavigationInterface(self) 
        self.stackedWidget = StackedWidget(self) 
        
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)

        self.titleBar.raise_() 

        self._init_ui()

        self.stackedWidget.setObjectName('stackedWidget')

    def _init_ui(self):
        FluentStyleSheet.FLUENT_WINDOW.apply(self)

        self.hBoxLayout = QHBoxLayout(self) 
        self.hBoxLayout.setSpacing(0) 
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.widgetLayout = QHBoxLayout()

        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addLayout(self.widgetLayout) 
        self.hBoxLayout.setStretchFactor(self.widgetLayout, 1) # 导航栏宽度固定，子界面宽度自适应

        self.widgetLayout.addWidget(self.stackedWidget) 
        self.widgetLayout.setContentsMargins(0, 48, 8, 8)



    def addScrollItem(self,super_interface: QWidget, interface: QWidget, icon: FluentIconBase, text: str,
                                onClick=None) -> NavigationPushButton:
        
        if not interface.objectName():
            raise ValueError("子界面objectName不能为空")
        
        super_key = super_interface.objectName()

        routeKey = interface.objectName() 

        mfb.set_menu_function_button_item(super_key, routeKey)

        return self.navigationInterface.addItemScroll(
            routeKey=routeKey,
            icon=icon,
            text=text, 
            onClick=onClick,
            tooltip=text
        )


    def addSubInterface(self, interface: QWidget, icon: FluentIconBase, text: str,
                                position=NavigationItemPosition.TOP,) -> NavigationPushButton:
        

        if not interface.objectName():
            raise ValueError("子界面objectName不能为空")
    
        routeKey = interface.objectName() 
        
        self.stackedWidget.addWidget(interface)

        router.set(routeKey, self.stackedWidget)

        self.navigationInterface.addItem(
            routeKey=routeKey,
            icon=icon,
            text=text, 
            onClick=lambda: self.switchTo(interface), 
            position=position, 
            tooltip=text
        )

        if self.stackedWidget.count() == 1:
            self.navigationInterface.setCurrentItem(routeKey)
            self.navigationInterface.setDisabledItems(mfb.get_menu_function_button_items(routeKey))


    def switchTo(self, interface: QWidget):
        self.stackedWidget.setCurrentWidget(interface)
        self.navigationInterface.setDisabledItems(mfb.get_menu_function_button_items(interface.objectName()))

    def _normalBackgroundColor(self):
        return ThemeBackgroundColor.color()


    def paintEvent(self, e):
        """ 窗口绘制事件（绘制背景色） """
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.backgroundColor)
        painter.drawRect(self.rect())


    def setTitleBar(self, titleBar):
        """ 设置自定义标题栏 """
        super().setTitleBar(titleBar)

        # 在macOS上隐藏自定义标题栏按钮（使用系统标题栏按钮）
        if sys.platform == "darwin" and self.isSystemButtonVisible() and isinstance(titleBar, TitleBarBase):
            titleBar.minBtn.hide() 
            titleBar.maxBtn.hide() 
            titleBar.closeBtn.hide()

    def resizeEvent(self, e):
        self.titleBar.move(15, 0)
        self.titleBar.resize(self.width()-15, self.titleBar.height())
