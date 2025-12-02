# coding:utf-8
from typing import List
from PyQt5.QtCore import QSize, QPoint, Qt, QRect, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QEvent, QTimer, QObject
from PyQt5.QtWidgets import QLayout, QWidgetItem, QLayoutItem

class FlowLayout(QLayout):
    """ 流式布局 
    自动将子部件按照水平方向排列，当一行无法容纳更多部件时自动换行
    """

    def __init__(self, parent=None, needAni=False, isTight=False):
        """ 初始化流式布局 """
        
        super().__init__(parent)
        self._items = []    # 存储布局中的所有项目
        self._anis = []     # 存储所有动画对象
        self._aniGroup = QParallelAnimationGroup(self)  # 并行动画组，用于同时执行多个动画
        self._verticalSpacing = 10  # 垂直方向上的间距
        self._horizontalSpacing = 10  # 水平方向上的间距
        self.duration = 300  # 动画持续时间（毫秒）
        self.ease = QEasingCurve.Linear  # 动画缓动曲线
        self.needAni = needAni  # 是否需要动画
        self.isTight = isTight  # 是否使用紧凑布局
        self._deBounceTimer = QTimer(self)  # 防抖动定时器
        self._deBounceTimer.setSingleShot(True)  # 设置为单次触发模式
        # 定时器超时后重新布局
        self._deBounceTimer.timeout.connect(lambda: self._doLayout(self.geometry(), True))
        self._wParent = None  # 父窗口部件引用
        self._isInstalledEventFilter = False  # 事件过滤器是否已安装

    def addItem(self, item):
        # 向布局添加一个项目
        self._items.append(item)

    def insertItem(self, index, item):
        # 在指定索引位置插入项目
        self._items.insert(index, item)

    def addWidget(self, w):
        super().addWidget(w)
        self._onWidgetAdded(w)

    def insertWidget(self, index, w):
        self.insertItem(index, QWidgetItem(w))
        self.addChildWidget(w)
        self._onWidgetAdded(w, index)

    def _onWidgetAdded(self, w, index=-1):
        if not self._isInstalledEventFilter:
                    
            if w.parent():
                self._wParent = w.parent()
                w.parent().installEventFilter(self)
            else:
                w.installEventFilter(self)


        if not self.needAni:
            return

        ani = QPropertyAnimation(w, b'geometry')
        
        ani.setEndValue(QRect(QPoint(0, 0), w.size()))

        ani.setDuration(self.duration)

        ani.setEasingCurve(self.ease)
        
        w.setProperty('flowAni', ani)

        self._aniGroup.addAnimation(ani)

        if index == -1:
            self._anis.append(ani)
        else:
            self._anis.insert(index, ani)

    def setAnimation(self, duration, ease=QEasingCurve.Linear):
        """ 设置移动动画参数

        参数
        ----------
        duration: int
            动画持续时间（毫秒）

        ease: QEasingCurve
            动画缓动曲线类型
        """
        # 如果不需要动画，则直接返回
        if not self.needAni:
            return

        # 更新动画持续时间和缓动曲线
        self.duration = duration
        self.ease = ease

        # 为所有已存在的动画应用新的参数
        for ani in self._anis:
            ani.setDuration(duration)
            ani.setEasingCurve(ease)

    def count(self):
        # 返回布局中的项目数量
        return len(self._items)

    def itemAt(self, index: int):
        # 返回指定索引位置的项目，如果索引无效则返回None
        if 0 <= index < len(self._items):
            return self._items[index]

        return None

    def takeAt(self, index: int):
        # 移除并返回指定索引位置的项目
        if 0 <= index < len(self._items):
            item = self._items[index]   # type: QLayoutItem
            # 获取部件关联的动画
            ani = item.widget().property('flowAni')
            if ani:
                # 从动画列表和动画组中移除动画
                self._anis.remove(ani)
                self._aniGroup.removeAnimation(ani)
                # 安排动画对象稍后删除
                ani.deleteLater()

            # 从项目列表中移除并返回部件
            return self._items.pop(index).widget()

        return None

    def removeWidget(self, widget):
        # 移除指定的部件
        for i, item in enumerate(self._items):
            if item.widget() is widget:
                return self.takeAt(i)

    def removeAllWidgets(self):
        """ 从布局中移除所有部件，但不删除它们 """
        while self._items:
            self.takeAt(0)

    def takeAllWidgets(self):
        """ 从布局中移除所有部件并删除它们 """
        # 循环移除并删除所有部件
        while self._items:
            w = self.takeAt(0)
            if w:
                w.deleteLater()

    def expandingDirections(self):
        # 重写父类方法，返回布局可扩展的方向，返回0表示不可扩展
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        # 重写父类方法，指示布局支持根据宽度计算高度
        return True

    def heightForWidth(self, width: int):
        """ 根据给定的宽度计算所需的最小高度

        参数
        ----------
        width: int
            布局的宽度

        返回
        -------
        int: 所需的最小高度
        """
        # 调用布局计算函数，但不实际移动部件
        return self._doLayout(QRect(0, 0, width, 0), False)

    def setGeometry(self, rect: QRect):
        # 重写父类方法，设置布局的几何形状
        super().setGeometry(rect)

        # 如果需要动画，则启动防抖动定时器
        if self.needAni:
            self._deBounceTimer.start(80)
        else:
            # 否则直接进行布局
            self._doLayout(rect, True)

    def sizeHint(self):
        # 返回布局的推荐大小（这里直接返回最小大小）
        return self.minimumSize()

    def minimumSize(self):
        # 计算布局的最小大小
        size = QSize()

        # 遍历所有项目，取最大的最小大小
        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        # 添加内容边距
        m = self.contentsMargins()
        size += QSize(m.left()+m.right(), m.top()+m.bottom())

        return size

    def setVerticalSpacing(self, spacing: int):
        """ 设置部件之间的垂直间距

        参数
        ----------
        spacing: int
            垂直间距值（像素）
        """
        self._verticalSpacing = spacing

    def verticalSpacing(self):
        """ 获取部件之间的垂直间距

        返回
        -------
        int: 垂直间距值（像素）
        """
        return self._verticalSpacing

    def setHorizontalSpacing(self, spacing: int):
        """ 设置部件之间的水平间距

        参数
        ----------
        spacing: int
            水平间距值（像素）
        """
        self._horizontalSpacing = spacing

    def horizontalSpacing(self):
        """ 获取部件之间的水平间距

        返回
        -------
        int: 水平间距值（像素）
        """
        return self._horizontalSpacing

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        # 处理部件的父对象变化事件
        if obj in [w.widget() for w in self._items] and event.type() == QEvent.Type.ParentChange:
            self._wParent = obj.parent()
            obj.parent().installEventFilter(self)
            self._isInstalledEventFilter = True

        # 处理父窗口显示事件
        if obj == self._wParent and event.type() == QEvent.Type.Show:
            self._doLayout(self.geometry(), True)
            self._isInstalledEventFilter = True

        # 调用父类的事件过滤器
        return super().eventFilter(obj, event)

    def _doLayout(self, rect: QRect, move: bool):
        """ 根据窗口大小调整部件位置

        参数
        ----------
        rect: QRect
            布局的矩形区域

        move: bool
            是否实际移动部件

        返回
        -------
        int: 布局所需的高度
        """
        # 标记动画是否需要重启
        aniRestart = False
        # 获取内容边距
        margin = self.contentsMargins()
        # 计算初始X坐标（左边界+左边距）
        x = rect.x() + margin.left()
        # 计算初始Y坐标（上边界+上边距）
        y = rect.y() + margin.top()
        # 当前行的最大高度
        rowHeight = 0
        # 获取水平和垂直间距
        spaceX = self.horizontalSpacing()
        spaceY = self.verticalSpacing()

        # 遍历所有项目
        for i, item in enumerate(self._items):
            # 如果启用了紧凑布局，并且部件不可见，则跳过该部件
            if item.widget() and not item.widget().isVisible() and self.isTight:
                continue

            # 计算放置当前部件后的X坐标
            nextX = x + item.sizeHint().width() + spaceX

            # 如果下一个部件的X坐标超出右边界且当前行有部件，则换行
            if nextX - spaceX > rect.right() - margin.right() and rowHeight > 0:
                x = rect.x() + margin.left()  # 重置X坐标到左边界
                y = y + rowHeight + spaceY  # Y坐标下移一行
                nextX = x + item.sizeHint().width() + spaceX  # 重新计算下一个X坐标
                rowHeight = 0  # 重置行高

            # 如果需要移动部件
            if move:
                # 计算目标位置
                target = QRect(QPoint(x, y), item.sizeHint())
                if not self.needAni:
                    # 如果不需要动画，直接设置部件位置
                    item.setGeometry(target)
                elif target != self._anis[i].endValue():
                    # 如果目标位置与当前动画结束位置不同，更新动画
                    self._anis[i].stop()
                    self._anis[i].setEndValue(target)
                    aniRestart = True

            # 更新X坐标
            x = nextX
            # 更新当前行的最大高度
            rowHeight = max(rowHeight, item.sizeHint().height())

        # 如果需要动画且有动画需要重启
        if self.needAni and aniRestart:
            self._aniGroup.stop()
            self._aniGroup.start()

        # 返回布局所需的总高度
        return y + rowHeight + margin.bottom() - rect.y()