# coding:utf-8
# 导入PyQt5相关模块
from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt, QEvent, QPoint
from PyQt5.QtGui import QColor, QResizeEvent
from PyQt5.QtWidgets import (QDialog,QGraphicsOpacityEffect, QHBoxLayout, QWidget, QFrame)

from ...common.config import isDarkTheme
from ...common.style_sheet import setShadowEffect

class MaskDialogBase(QDialog):
    """ 对话框基础类，包含窗口遮罩 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._isClosableOnMaskClicked = False # 是否可通过点击遮罩关闭对话框
        self._isDraggable = False # 是否可拖动
        self._dragPos = QPoint()    # 拖动位置
        self._hBoxLayout = QHBoxLayout(self)    # 创建水平布局管理器
        self.windowMask = QWidget(self) # 创建窗口遮罩部件
        self.widget = QFrame(self, objectName='centerWidget')   # 创建对话框中心部件，所有子部件都以它为父部件
        
        self.setWindowFlags(Qt.FramelessWindowHint) # 设置窗口无边框
        self.setAttribute(Qt.WA_TranslucentBackground) # 设置窗口背景透明
        self.setGeometry(0, 0, parent.width(), parent.height()) # 设置对话框大小与父窗口相同

        # 根据当前主题设置遮罩颜色（深色主题为黑色，浅色主题为白色）
        c = 0 if isDarkTheme() else 255
        # 调整遮罩大小与对话框一致
        self.windowMask.resize(self.size())
        # 设置遮罩样式表，带有透明度
        self.windowMask.setStyleSheet(f'background:rgba({c}, {c}, {c}, 0.6)')
        # 将中心部件添加到布局中
        self._hBoxLayout.addWidget(self.widget)
        # 为对话框添加阴影效果
        setShadowEffect(self.widget, 60, (0, 10), QColor(0, 0, 0, 80))

        self.setMaskColor(QColor(0, 0, 0, 120))
        
        # 为窗口、遮罩和中心部件安装事件过滤器
        self.window().installEventFilter(self)
        self.windowMask.installEventFilter(self)
        self.widget.installEventFilter(self)

    def setMaskColor(self, color: QColor):
        """设置对话框遮罩颜色
            :param color: 遮罩颜色
        """
        self.windowMask.setStyleSheet(f"""
            background: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})
        """)

    def showEvent(self, e):
        """ 对话框显示事件，实现淡入效果 """
        opacityEffect = QGraphicsOpacityEffect(self)    # 创建透明度效果
        self.setGraphicsEffect(opacityEffect)   # 应用透明度效果
        opacityAni = QPropertyAnimation(opacityEffect, b'opacity', self)    # 创建透明度动画
        opacityAni.setStartValue(0) # 设置动画起始透明度
        opacityAni.setEndValue(1)   # 设置动画结束透明度
        opacityAni.setDuration(500) # 设置动画持续时间
        opacityAni.setEasingCurve(QEasingCurve.InSine)  # 设置动画缓动曲线
        opacityAni.finished.connect(lambda: self.setGraphicsEffect(None))   # 动画完成后移除图形效果
        opacityAni.start()  # 开始动画
       
        super().showEvent(e)

    def done(self, code):
        """ 对话框关闭事件，实现淡出效果 """
        self.widget.setGraphicsEffect(None) # 清除中心部件的图形效果
        
        opacityEffect = QGraphicsOpacityEffect(self) # 创建透明度效果
        self.setGraphicsEffect(opacityEffect) # 应用透明度效果
        
        opacityAni = QPropertyAnimation(opacityEffect, b'opacity', self) # 创建透明度动画
        
        opacityAni.setStartValue(1) # 设置动画起始透明度
        opacityAni.setEndValue(0) # 设置动画结束透明度
        opacityAni.setDuration(500) # 设置动画持续时间
        opacityAni.finished.connect(lambda: self._onDone(code)) # 动画完成后调用_onDone方法
        opacityAni.start()

    def _onDone(self, code):
        self.setGraphicsEffect(None)    # 清除图形效果
        QDialog.done(self, code)

    def isClosableOnMaskClicked(self) -> bool:
        return self._isClosableOnMaskClicked # 返回是否可通过点击遮罩关闭对话框的状态

    def setClosableOnMaskClicked(self, isClosable: bool):
        self._isClosableOnMaskClicked = isClosable # 设置是否可通过点击遮罩关闭对话框

    def setDraggable(self, draggable: bool):
  
        self._isDraggable = draggable   # 设置对话框是否可拖动

    def isDraggable(self) -> bool:
        return self._isDraggable    # 返回对话框是否可拖动的状态

    def resizeEvent(self, e):
        self.windowMask.resize(self.size()) # 调整遮罩大小与对话框一致

    def eventFilter(self, obj, e: QEvent):
        # 处理窗口事件
        if obj is self.window():
            if e.type() == QEvent.Resize:
                re = QResizeEvent(e)
                self.resize(re.size())
        # 处理遮罩事件
        elif obj is self.windowMask:
            
            if e.type() == QEvent.MouseButtonRelease and e.button() == Qt.LeftButton \
                    and self.isClosableOnMaskClicked(): # 如果是鼠标左键释放事件且允许通过点击遮罩关闭
                self.reject() # 拒绝对话框
        # 处理中心部件事件且对话框可拖动
        elif obj is self.widget and self.isDraggable():
            # 如果是鼠标左键按下事件
            if e.type() == QEvent.MouseButtonPress and e.button() == Qt.LeftButton:
                # 如果点击位置不在子部件上
                if not self.widget.childrenRegion().contains(e.pos()):
                    # 记录拖动起始位置
                    self._dragPos = e.pos()
                    return True
            # 如果是鼠标移动事件且拖动位置有效
            elif e.type() == QEvent.MouseMove and not self._dragPos.isNull():
                # 计算新位置
                pos = self.widget.pos() + e.pos() - self._dragPos
                # 限制位置在对话框内
                pos.setX(max(0, min(pos.x(), self.width() - self.widget.width())))
                pos.setY(max(0, min(pos.y(), self.height() - self.widget.height())))

                # 移动中心部件
                self.widget.move(pos)
                return True
            # 如果是鼠标按钮释放事件
            elif e.type() == QEvent.MouseButtonRelease:
                # 重置拖动位置
                self._dragPos = QPoint()

        return super().eventFilter(obj, e)