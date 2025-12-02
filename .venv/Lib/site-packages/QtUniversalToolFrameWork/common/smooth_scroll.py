# coding:utf-8
from collections import deque 
from enum import Enum 
from math import cos, pi 

from PyQt5.QtCore import QDateTime, Qt, QTimer, QPoint
from PyQt5.QtGui import QWheelEvent 
from PyQt5.QtWidgets import QApplication, QScrollArea, QAbstractScrollArea 


class SmoothScroll:
    """ 
    平滑滚动功能实现类
    
    为QScrollArea组件提供平滑滚动效果，支持多种滚动插值模式，
    可根据滚动频率动态调整加速度，提升用户滚动体验。

    """

    def __init__(self, widget: QScrollArea, orient=Qt.Vertical):

        self.widget = widget  # 目标滚动区域组件
        self.orient = orient  # 滚动方向
        self.fps = 60  # 平滑滚动帧率（每秒60帧）
        self.duration = 400  # 单次滚动动画持续时间（毫秒）
        self.stepsTotal = 0  # 单次滚动总步数（=帧率*持续时间/1000）
        self.stepRatio = 1.5  # 步长放大比例（增强滚动距离）
        self.acceleration = 1  # 加速度系数（基础加速度）
        self.lastWheelEvent = None  # 最后一次滚轮事件（用于构造模拟事件）
        self.scrollStamps = deque()  # 滚动事件时间戳队列（记录最近500ms内的滚动事件）
        self.stepsLeftQueue = deque()  # 待处理滚动步骤队列（存储[总距离, 剩余步数]）
        self.smoothMoveTimer = QTimer(widget)  # 平滑滚动定时器（控制每帧滚动距离）
        self.smoothMode = SmoothMode(SmoothMode.LINEAR)  # 默认平滑模式（线性插值）
        self.smoothMoveTimer.timeout.connect(self.__smoothMove)  # 绑定定时器超时回调

    def setSmoothMode(self, smoothMode):
        self.smoothMode = smoothMode

    def wheelEvent(self, e):
        delta = e.angleDelta().y() if e.angleDelta().y() != 0 else e.angleDelta().x()
         
        if self.smoothMode == SmoothMode.NO_SMOOTH or abs(delta) % 120 != 0:
            QAbstractScrollArea.wheelEvent(self.widget, e)
            return

        now = QDateTime.currentDateTime().toMSecsSinceEpoch() # 当前时间戳（毫秒）
        self.scrollStamps.append(now) 
     
        while now - self.scrollStamps[0] > 500:
            self.scrollStamps.popleft()

        accerationRatio = min(len(self.scrollStamps) / 15, 1)
        
        if not self.lastWheelEvent:
            self.lastWheelEvent = QWheelEvent(e) 
        else:
            self.lastWheelEvent = e  # 更新最后事件

        self.stepsTotal = self.fps * self.duration / 1000

        delta = delta * self.stepRatio 
        if self.acceleration > 0:
            delta += delta * self.acceleration * accerationRatio  # 叠加加速度

        self.stepsLeftQueue.append([delta, self.stepsTotal])

        self.smoothMoveTimer.start(int(1000 / self.fps))

    def __smoothMove(self):
        """ 定时器超时回调：处理平滑滚动的每一步 """
        totalDelta = 0 

        for i in self.stepsLeftQueue:
            totalDelta += self.__subDelta(i[0], i[1]) 
            i[1] -= 1 

        while self.stepsLeftQueue and self.stepsLeftQueue[0][1] == 0:
            self.stepsLeftQueue.popleft()

        if self.orient == Qt.Vertical:
            p = QPoint(0, round(totalDelta)) 
            bar = self.widget.verticalScrollBar() 
        else:
            p = QPoint(round(totalDelta), 0)
            bar = self.widget.horizontalScrollBar()

        e = QWheelEvent(
            self.lastWheelEvent.pos(), 
            self.lastWheelEvent.globalPos(), 
            QPoint(),
            p, 
            round(totalDelta),  
            self.orient, 
            self.lastWheelEvent.buttons(), 
            Qt.NoModifier 
        )

        QApplication.sendEvent(bar, e)

        if not self.stepsLeftQueue:
            self.smoothMoveTimer.stop()

    def __subDelta(self, delta, stepsLeft):
        """ 计算单步滚动距离（根据平滑模式进行插值）"""
        m = self.stepsTotal / 2 
        x = abs(self.stepsTotal - stepsLeft - m) 

        res = 0
        if self.smoothMode == SmoothMode.NO_SMOOTH:
            res = 0 
        elif self.smoothMode == SmoothMode.CONSTANT:
            res = delta / self.stepsTotal 
        elif self.smoothMode == SmoothMode.LINEAR:
            res = 2 * delta / self.stepsTotal * (m - x) / m
        elif self.smoothMode == SmoothMode.QUADRATI:
            res = 3 / 4 / m * (1 - x * x / m / m) * delta
        elif self.smoothMode == SmoothMode.COSINE:
            res = (cos(x * pi / m) + 1) / (2 * m) * delta

        return res


class SmoothMode(Enum):
    
    NO_SMOOTH = 0  # 无平滑滚动（使用原生滚动）
    CONSTANT = 1   # 恒定速度（匀速滚动）
    LINEAR = 2     # 线性插值（速度先增后减，线性变化）
    QUADRATI = 3   # 二次插值（速度按二次曲线变化，更柔和）
    COSINE = 4     # 余弦插值（速度按余弦曲线变化，最平滑）
