# coding:utf-8
from PyQt5.QtCore import Qt, pyqtSignal, QEasingCurve,QPropertyAnimation,QAbstractAnimation,QPoint
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QAbstractScrollArea,QWidget,QStackedWidget

class PopUpAniInfo:
    """ 弹出动画信息数据类"""
    def __init__(self, widget: QWidget, deltaX: int, deltaY, ani: QPropertyAnimation):

        self.widget = widget  
        self.deltaX = deltaX 
        self.deltaY = deltaY 
        self.ani = ani   

class PopUpAniStackedWidget(QStackedWidget):
    """ 带有弹出动画效果的堆叠窗口部件"""

    aniFinished = pyqtSignal()
    aniStart = pyqtSignal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aniInfos = []  
        self.isAnimationEnabled = True
        self._nextIndex = None # 下一个要显示的部件索引
        self._ani = None # 当前正在运行的动画对象

    def addWidget(self, widget, deltaX=0, deltaY=30):
        
        super().addWidget(widget)

        self.aniInfos.append(PopUpAniInfo(
            widget=widget,
            deltaX=deltaX,
            deltaY=deltaY,
            ani=QPropertyAnimation(widget, b'pos'),  # 动画作用于部件的'pos'（位置）属性
        ))

    def removeWidget(self, widget: QWidget):
        index = self.indexOf(widget)
        if index == -1:
            return
        self.aniInfos.pop(index)
        super().removeWidget(widget)

    def setAnimationEnabled(self, isEnabled: bool):

        self.isAnimationEnabled = isEnabled  # 是否启用动画效果

    def setCurrentIndex(self, index: int, needPopOut: bool = False, showNextWidgetDirectly: bool = True,
                        duration: int = 250, easingCurve=QEasingCurve.OutQuad):
        
        if index < 0 or index >= self.count():
            return

        if index == self.currentIndex():
            return

        if not self.isAnimationEnabled:
            return super().setCurrentIndex(index)

        if self._ani and self._ani.state() == QAbstractAnimation.Running:
            self._ani.stop()
            self.__onAniFinished() # 停止当前动画并触发结束信号

        self._nextIndex = index

        nextAniInfo = self.aniInfos[index]

        currentAniInfo = self.aniInfos[self.currentIndex()]

        currentWidget = self.currentWidget()

        nextWidget = nextAniInfo.widget

        ani = currentAniInfo.ani if needPopOut else nextAniInfo.ani
        self._ani = ani

        if needPopOut: # 如果需要弹出当前部件
            deltaX, deltaY = currentAniInfo.deltaX, currentAniInfo.deltaY
            pos = currentWidget.pos() + QPoint(deltaX, deltaY)
            self.__setAnimation(ani, currentWidget.pos(), pos, duration, easingCurve)
            nextWidget.setVisible(showNextWidgetDirectly)
        else:
            deltaX, deltaY = nextAniInfo.deltaX, nextAniInfo.deltaY
            pos = nextWidget.pos() + QPoint(deltaX, deltaY)
            self.__setAnimation(ani, pos, QPoint(nextWidget.x(), 0), duration, easingCurve)
            super().setCurrentIndex(index)

        ani.finished.connect(self.__onAniFinished)
        ani.start()
        self.aniStart.emit()

    def setCurrentWidget(self, widget, needPopOut: bool = False, showNextWidgetDirectly: bool = True,
                         duration: int = 250, easingCurve=QEasingCurve.OutQuad):
       
        self.setCurrentIndex(
            self.indexOf(widget), needPopOut, showNextWidgetDirectly, duration, easingCurve)

    def __setAnimation(self, ani, startValue, endValue, duration, easingCurve=QEasingCurve.Linear):
        
        ani.setEasingCurve(easingCurve)
        ani.setStartValue(startValue)
        ani.setEndValue(endValue)
        ani.setDuration(duration)

    def __onAniFinished(self):
        """ 动画结束时的槽函数 """
        self._ani.disconnect() #
        super().setCurrentIndex(self._nextIndex)
        self.aniFinished.emit()



class StackedWidget(QFrame):
    """ 带动画效果的堆叠窗口部件，继承自QFrame
    用于管理多个子界面，支持平滑切换动画，通常与导航组件配合使用 """

    currentChanged = pyqtSignal(int) 

    def __init__(self, parent=None):
        super().__init__(parent=parent) 
        self.hBoxLayout = QHBoxLayout(self) 
        self.view = PopUpAniStackedWidget(self) 

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.view) 

        self.view.currentChanged.connect(self.currentChanged)
        self.setAttribute(Qt.WA_StyledBackground)

    def isAnimationEnabled(self) -> bool:
        return self.view.isAnimationEnabled  

    def setAnimationEnabled(self, isEnabled: bool):

        self.view.setAnimationEnabled(isEnabled) 

    def addWidget(self, widget):
       
        self.view.addWidget(widget)

    def removeWidget(self, widget):
       
        self.view.removeWidget(widget)

    def widget(self, index: int):
        
        return self.view.widget(index)

    def setCurrentWidget(self, widget, popOut=False):
        
        if isinstance(widget, QAbstractScrollArea):
            widget.verticalScrollBar().setValue(0)

        if not popOut: # 如果不需要弹出当前部件
            self.view.setCurrentWidget(widget, duration=200)
        else:
            self.view.setCurrentWidget(
                widget, True, False, 200, QEasingCurve.InQuad)

    def setCurrentIndex(self, index, popOut=False):
        
        self.setCurrentWidget(self.view.widget(index), popOut)

    def currentIndex(self):
       
        return self.view.currentIndex()

    def currentWidget(self):
        
        return self.view.currentWidget()

    def indexOf(self, widget):
        
        return self.view.indexOf(widget)

    def count(self):
       
        return self.view.count()
    


