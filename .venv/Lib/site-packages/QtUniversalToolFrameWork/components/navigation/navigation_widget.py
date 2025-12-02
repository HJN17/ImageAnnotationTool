# coding:utf-8
from typing import Union, List

from PyQt5.QtCore import pyqtSignal, QRect, QRectF, QPoint, QMargins,Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QIcon, QCursor, QFont, QBrush, QPixmap, QImage
from PyQt5.QtWidgets import QWidget


from ...common.config import isDarkTheme
from ...common.style_sheet import themeColor,ThemeColor
from ...common.icon import drawIcon, toQIcon
from ...common.icon import FluentIcon as FIF
from ...common.font import setFont
from ...common.animation import FluentAnimation, FluentAnimationType, FluentAnimationProperty,FluentAnimationSpeed


class NavigationWidget(QWidget):
    """ 导航组件基类
    
    这是所有导航组件的基类，提供了基本的导航项功能和交互行为。
    """

    clicked = pyqtSignal(bool) 

    EXPAND_WIDTH = 160

    def __init__(self, parent=None):
        super().__init__(parent)

        self.isCompacted = True  # 是否压缩状态
        self.isSelected = False # 是否选中状态
        self.isPressed = False
        self.isEnter = False 
    
        self.lightTextColor = QColor(0, 0, 0)  
        self.darkTextColor = QColor(255, 255, 255) 

        self.setFixedSize(40, 36)

    def enterEvent(self, e):
        # 鼠标进入事件处理
        self.isEnter = True 
        self.update()  

    def leaveEvent(self, e):
        # 鼠标离开事件处理
        self.isEnter = False 
        self.isPressed = False 
        self.update() 

    def mousePressEvent(self, e):
        super().mousePressEvent(e) 
        self.isPressed = True 
        self.update() 

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.isPressed = False  
        self.update()        
        self.clicked.emit(True) 

    def click(self):
        self.clicked.emit(True)

    def setCompacted(self, isCompacted: bool):
        if isCompacted == self.isCompacted: # 状态未改变，无需更新
            return

        self.isCompacted = isCompacted 
        
        if isCompacted:
            self.setFixedSize(40, 36) 
        else:
            self.setFixedSize(self.EXPAND_WIDTH-10, 36) 

        self.update()
    
    def setHidden(self, isHidden: bool):

        self.setVisible(isHidden) # 隐藏时，不占用空间 isHidden 为 True 时，不占用空间

    def setSelected(self, isSelected: bool):

        self.isSelected = isSelected 
        self.update()   

    # 反转文本颜色
    def textColor(self, bool : bool = False):
        if bool:
            return self.lightTextColor if isDarkTheme() else self.darkTextColor

        return self.darkTextColor if isDarkTheme() else self.lightTextColor
    
    def setTextColor(self, light, dark):
       
        self.lightTextColor = QColor(light)
        self.darkTextColor = QColor(dark)  
        self.update()

class NavigationPushButton(NavigationWidget):
    """ 导航推送按钮 """

    def __init__(self, icon: FIF, text: str, parent=None):
       
        super().__init__(parent=parent)

        self._icon = icon  
        self._text = text 
        self.lightIndicatorColor = QColor() 
        self.darkIndicatorColor = QColor()

        setFont(self) 

    def text(self):
        return self._text

    def setText(self, text: str):
       
        self._text = text 
        self.update()

    def icon(self):
        return toQIcon(self._icon)

    def setIcon(self, icon: FIF): 
        self._icon = icon  
        self.update()
    
    def _margins(self):
        return QMargins(0, 0, 0, 0)

    def _canDrawIndicator(self):
        return self.isSelected

    def paintEvent(self, e):
        """ 绘制按钮界面 """
        painter = QPainter(self) 
        painter.setRenderHints(QPainter.Antialiasing |  QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7) 
        if not self.isEnabled():
            painter.setOpacity(0.4)

        c = 255 if isDarkTheme() else 0 
        m = self._margins()  
        pl, pr = m.left(), m.right() 

        globalRect = QRect(self.mapToGlobal(QPoint()), self.size())  # 按钮全局矩形区域

        if self._canDrawIndicator():


            painter.setBrush(QColor(c, c, c, 6 if self.isEnter else 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

            painter.setBrush(themeColor()) 
            painter.drawRoundedRect(pl, 10, 3, 16, 1.5, 1.5) 

        elif self.isEnter and self.isEnabled() and globalRect.contains(QCursor.pos()):
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        drawIcon(self._icon, painter, QRectF(11.5+pl, 10, 16, 16))

        if self.isCompacted:
            return 

        painter.setFont(self.font())  
        painter.setPen(self.textColor()) 

        left = 44 + pl if not self.icon().isNull() else pl + 16
        painter.drawText(QRectF(left, 0, self.width()-13-left-pr, self.height()), Qt.AlignVCenter, self.text())

class NavigationIconButton(NavigationPushButton):
    """ 导航图标按钮"""

    def __init__(self, icon: FIF, text: str, parent=None):

        super().__init__(icon, text, parent=parent)

        self._fadeAni = FluentAnimation.create(FluentAnimationType.FADE_IN_OUT, FluentAnimationProperty.OPACITY,speed=FluentAnimationSpeed.SLOW, value=0, parent=self)
        
        self._reverseIcon = None

        self.setHidden(True)   

    def setHidden(self, isHidden: bool):
        super().setHidden(isHidden)
        
        if isHidden:
            self._fadeAni.startAnimation(1,0)

    def setSelected(self, isSelected: bool):
        if isSelected:
            self._reverseIcon = self._icon.qicon(True)
        else:
            self._reverseIcon = self._icon

        super().setSelected(isSelected)
        

    def paintEvent(self, e):
        """ 绘制按钮界面 """
        painter = QPainter(self) 
        painter.setRenderHints(QPainter.Antialiasing |  QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        painter.setOpacity(self._fadeAni.value())
   
        c = 255 if isDarkTheme() else 0 
        m = self._margins()  
        pl, pr = m.left(), m.right() 

        globalRect = QRect(self.mapToGlobal(QPoint()), self.size())  # 按钮全局矩形区域

        if self._canDrawIndicator():
            painter.setBrush(themeColor()) 
            painter.drawRoundedRect(self.rect(), 5, 5) 

        elif self.isEnter and self.isEnabled() and globalRect.contains(QCursor.pos()): # 鼠标悬停在按钮上
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        drawIcon(self._reverseIcon, painter, QRectF(11.5+pl, 10, 16, 16))

        if self.isCompacted:
            return 
        
        if self._canDrawIndicator():
            painter.setPen(self.textColor(True)) 
        else:
            painter.setPen(self.textColor()) 
        
        painter.setFont(self.font())  
        left = 44 + pl if not self.icon().isNull() else pl + 16
        painter.drawText(QRectF(left, 0, self.width()-13-left-pr, self.height()), Qt.AlignVCenter, self.text())


class NavigationToolButton(NavigationPushButton):
    """ 导航工具按钮"""

    def __init__(self, icon: Union[str, QIcon, FIF], parent=None):
        super().__init__(icon, '', parent)

    def setCompacted(self, isCompacted: bool): # 重写设置紧凑模式方法
        
        self.setFixedSize(40, 36)

class NavigationSeparator(NavigationWidget):
    """ 导航分隔符
    
    用于在导航栏中分隔不同组的项目。
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent) 

        self.setCompacted(True)

    def setCompacted(self, isCompacted: bool):
        if isCompacted:
            self.setFixedSize(40, 3)  # 紧凑模式下的大小
        else:
            self.setFixedSize(self.EXPAND_WIDTH-10, 3)  # 展开模式下的大小

        self.update()

    def paintEvent(self, e):
        """ 绘制分隔符 """
        painter = QPainter(self)
        c = 255 if isDarkTheme() else 0 
        pen = QPen(QColor(c, c, c, 15))
        pen.setCosmetic(True) 
        painter.setPen(pen)
        painter.drawLine(1, 1, self.width()-2, 1)  # 绘制分隔线
