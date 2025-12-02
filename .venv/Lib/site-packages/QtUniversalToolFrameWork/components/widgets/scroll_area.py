# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QScrollArea

from ...common.smooth_scroll import SmoothScroll, SmoothMode

from .scroll_bar import SmoothScrollBar, SmoothScrollDelegate

class ScrollArea(QScrollArea):
    """ 平滑滚动区域控件 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scrollDelagate = SmoothScrollDelegate(self) # 创建平滑滚动委托实例，用于管理平滑滚动行为

    def setSmoothMode(self, mode: SmoothMode, orientation: Qt.Orientation):
        """ 设置平滑滚动模式
        
        参数
        ----------
        mode: SmoothMode
            平滑滚动模式
        
        orientation: Qt.Orientation
            滚动方向（水平或垂直）
        """
        # 判断滚动方向是否为垂直方向
        if orientation == Qt.Orientation.Vertical:
            # 如果是垂直方向，设置垂直平滑滚动的模式
            self.scrollDelagate.verticalSmoothScroll.setSmoothMode(mode)
        else:
            # 如果是水平方向，设置水平平滑滚动的模式
            self.scrollDelagate.horizonSmoothScroll.setSmoothMode(mode)

    def enableTransparentBackground(self):
        # 设置滚动区域的样式表，去除边框并设置背景透明
        self.setStyleSheet("QScrollArea{border: none; background: transparent}")

        # 检查是否存在滚动内容部件
        if self.widget(): 
            # 如果存在，设置内容部件的背景为透明
            self.widget().setStyleSheet("QWidget{background: transparent}")


class SingleDirectionScrollArea(QScrollArea):
    """ 单方向滚动区域控件 """

    def __init__(self, parent=None, orient=Qt.Vertical):
        """
        参数
        ----------
        parent: QWidget
            父部件
        
        orient: Orientation
            滚动方向（默认为垂直方向）
        """
    
        super().__init__(parent)
        self.orient = orient
        self.smoothScroll = SmoothScroll(self, orient)  # 创建平滑滚动实例，指定当前控件和滚动方向
        self.vScrollBar = SmoothScrollBar(Qt.Vertical, self)    # 创建垂直平滑滚动条实例  
        self.hScrollBar = SmoothScrollBar(Qt.Horizontal, self)  # 创建水平平滑滚动条实例

    def setVerticalScrollBarPolicy(self, policy):
        # 调用父类方法，强制设置垂直滚动条为始终隐藏
        super().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 根据传入的策略设置垂直滚动条是否强制隐藏
        self.vScrollBar.setForceHidden(policy == Qt.ScrollBarAlwaysOff)

    def setHorizontalScrollBarPolicy(self, policy):
        # 调用父类方法，强制设置水平滚动条为始终隐藏
        super().setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 根据传入的策略设置水平滚动条是否强制隐藏
        self.hScrollBar.setForceHidden(policy == Qt.ScrollBarAlwaysOff)

    def setSmoothMode(self, mode):
        """ 设置平滑滚动模式
        
        参数
        ----------
        mode: SmoothMode
            平滑滚动模式
        """
        # 设置平滑滚动的模式
        self.smoothScroll.setSmoothMode(mode)

    def keyPressEvent(self, e):
        # 判断按下的键是否为左右方向键
        if e.key() in [Qt.Key_Left, Qt.Key_Right]:
            # 如果是左右方向键，不处理该事件
            return
        return super().keyPressEvent(e)

    def wheelEvent(self, e: QWheelEvent):
        # 判断滚轮事件的水平滚动分量是否不为零
        if e.angleDelta().x() != 0:
            # 如果有水平滚动分量，不处理该事件
            return

        # 将滚轮事件交给平滑滚动处理
        self.smoothScroll.wheelEvent(e)
        # 标记事件已被处理
        e.setAccepted(True)

    def enableTransparentBackground(self):
        # 设置滚动区域的样式表，去除边框并设置背景透明
        self.setStyleSheet("QScrollArea{border: none; background: transparent}")

        # 检查是否存在滚动内容部件
        if self.widget():
            # 如果存在，设置内容部件的背景为透明
            self.widget().setStyleSheet("QWidget{background: transparent}")
