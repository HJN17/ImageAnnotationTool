# coding:utf-8
from typing import Union
from PyQt5.QtCore import Qt,pyqtSignal,QRect,QObject,QEvent
from PyQt5.QtGui import QPainter, QPen, QColor,QIcon,QFontMetrics,QKeySequence
from PyQt5.QtWidgets import QWidget,QVBoxLayout, QHBoxLayout, QFrame,QLabel,QFileDialog,QCompleter,QApplication,QSizePolicy,QSpacerItem


from ...common.icon import FluentIcon as FIF,FluentIconBase,drawIcon
from ...common.config import qconfig, isDarkTheme

from ..widgets import IconWidget,TitleLabel,CaptionLabel

class TitleToolBar(QWidget):
    """ 标题工具条 """
    
    def __init__(self,icon: Union[FluentIconBase, QIcon, str],title: str, content: str, parent=None):
        super().__init__(parent=parent)

        self.iconLabel = IconLabel(icon, self)
        self.titleLabel = TitleLabel(title, self) 
        self.contentLabel = CaptionLabel(content, self)
        self._content = content 
        self.hBoxLayout = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout(self)
        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(70)
        self.contentLabel.setWordWrap(False)
        self.contentLabel.setTextColor(QColor(118, 118, 118), QColor(208, 208, 208))

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSpacing(10)
        self.hBoxLayout.addWidget(self.iconLabel, 0,Qt.AlignLeft)
        self.hBoxLayout.addWidget(self.titleLabel, 0,Qt.AlignLeft)
        self.hBoxLayout.addStretch(1)

        self.vBoxLayout.setContentsMargins(25, 10, 0, 0)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        self.vBoxLayout.addSpacing(2)
        self.vBoxLayout.addWidget(self.contentLabel)
        self.vBoxLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    

    def elide_text(self):

        left, _, right, _ = self.vBoxLayout.getContentsMargins()
        layout_margins = left + right
        max_available_width = self.parent().width() - layout_margins - 50  # 预留50px缓冲
        max_available_width = max(max_available_width, 100)  # 最小宽度限制，避免负数

        # 计算截断文本
        metrics = QFontMetrics(self.contentLabel.font())
        elided_text = metrics.elidedText(self._content, Qt.ElideRight, max_available_width)
        self.contentLabel.setText(elided_text)

    def resizeEvent(self, e):
        """ 重写QWidget的尺寸改变事件：更新文本截断显示 """
        super().resizeEvent(e)
        self.elide_text()

class SeparatorWidget(QWidget):
    """ 分隔符部件 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(6, 16)

    def paintEvent(self, e):
        painter = QPainter(self)
        pen = QPen(1)
        pen.setCosmetic(True)   # 设置画笔为装饰性（不随缩放变化粗细）

        c = QColor(255, 255, 255, 21) if isDarkTheme() else QColor(0, 0, 0, 15)
        pen.setColor(c) 
        painter.setPen(pen)
      
        x = self.width() // 2
     
        painter.drawLine(x, 0, x, self.height())

class IconLabel(IconWidget):
    """ 图标标签类 """

    def __init__(self, icon: Union[FluentIconBase, QIcon, str], parent=None):
        super().__init__(parent=parent)
        self.setIcon(icon)
        self.setFixedSize(25, 25)

    def paintEvent(self, e):
        """ 重写QWidget的绘制事件：实现图标在部件内的渲染 """
       
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        
        x,y,w,h = self.rect().getRect()

        drawIcon(self._icon, painter, QRect(x+2, y+2, w-2, h-2))

    
