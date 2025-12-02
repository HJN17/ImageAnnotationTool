# coding:utf-8
from typing import Iterable 
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent, QRectF
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QToolButton


from ...common.icon import FluentIcon, isDarkTheme 

from .scroll_area import SmoothScrollBar


class ScrollButton(QToolButton):
    """ 滚动按钮类 - 用于CycleListWidget中的上下滚动按钮 """

    def __init__(self, icon: FluentIcon, parent=None):
        """

        初始化滚动按钮
        
        参数:
            icon: FluentIcon - 按钮上显示的图标
            parent: QWidget - 父窗口部件
        """
        super().__init__(parent=parent) 
        self._icon = icon
        self.isPressed = False
        
        self.installEventFilter(self)

    def eventFilter(self, obj, e: QEvent):
        """
        事件过滤器 - 监控鼠标按下和释放事件以更新按钮状态
        
        参数:
            obj: QObject - 事件源对象
            e: QEvent - 事件对象
        
        返回:
            bool - 是否处理了事件
        """
        if obj is self:  # 如果事件源是自身
            if e.type() == QEvent.MouseButtonPress:  # 鼠标按下事件
                self.isPressed = True
                self.update()
            elif e.type() == QEvent.MouseButtonRelease:  # 鼠标释放事件
                self.isPressed = False
                self.update()
        
        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        """
        绘制事件 - 自定义按钮的外观绘制
        
        参数:
            e: QPaintEvent - 绘制事件对象
        """
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)  # 设置抗锯齿渲染

        if not self.isPressed: # 如果按钮未被按下
            w, h = 10, 10 
        else:
            w, h = 8, 8 

        x = (self.width() - w) / 2  # 计算图标X坐标（水平居中）
        y = (self.height() - h) / 2  # 计算图标Y坐标（垂直居中）

        if not isDarkTheme():  # 如果当前不是深色主题
            self._icon.render(painter, QRectF(x, y, w, h), fill="#5e5e5e")  # 渲染图标并设置填充色
        else:
            self._icon.render(painter, QRectF(x, y, w, h))  # 使用默认颜色渲染图标


class CycleListWidget(QListWidget):
    """ 循环列表部件类 - 实现可循环滚动的列表功能 """

    currentItemChanged = pyqtSignal(QListWidgetItem)  # 当前选中项变更的信号

    def __init__(self, items: Iterable, itemSize: QSize, align=Qt.AlignCenter, parent=None):
        """
        初始化循环列表部件
        
        参数:
            items: Iterable[Any] - 要添加的项目集合
            itemSize: QSize - 项目的尺寸
            align: Qt.AlignmentFlag - 项目文本的对齐方式
            parent: QWidget - 父窗口部件
        """
        super().__init__(parent=parent) 

        self.itemSize = itemSize
        self.align = align

        self.upButton = ScrollButton(FluentIcon.CARE_UP_SOLID, self)
        self.downButton = ScrollButton(FluentIcon.CARE_DOWN_SOLID, self)
        self.scrollDuration = 250
        self.originItems = list(items)

        self.vScrollBar = SmoothScrollBar(Qt.Vertical, self) 
        self.visibleNumber = 9

        # 重复添加项目以实现循环滚动效果
        self.setItems(items)  # 设置列表项目

        self.setVerticalScrollMode(self.ScrollPerPixel)  # 设置垂直滚动模式为逐像素滚动
        self.vScrollBar.setScrollAnimation(self.scrollDuration)  # 设置滚动动画持续时间
        self.vScrollBar.setForceHidden(True)  # 强制隐藏滚动条

        self.setViewportMargins(0, 0, 0, 0)  # 设置视口边距为0
        self.setFixedSize(itemSize.width(),  # 设置固定宽度
                          itemSize.height()*self.visibleNumber)  # 设置固定高度（可见项目总高度）

        # 隐藏滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 水平滚动条始终关闭
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 垂直滚动条始终关闭
        self.upButton.hide()
        self.downButton.hide()

        self.upButton.clicked.connect(self.scrollUp)
        self.downButton.clicked.connect(self.scrollDown)
        self.itemClicked.connect(self._onItemClicked)  # 连接项目点击信号到_onItemClicked方法

        self.installEventFilter(self)  # 安装事件过滤器监控自身事件

    def setItems(self, items: list):
        """ 设置列表中的项目 """
        self.clear()
        self._createItems(items)

    def _createItems(self, items: list):
        """
        内部方法：创建列表项目
        
        参数:
            items: list - 要创建的项目列表
        """
        N = len(items)
        self.isCycle = N > self.visibleNumber  # 判断是否需要循环滚动（项目数大于可见数）

        if self.isCycle:
            for _ in range(2):
                self._addColumnItems(items) 

            self._currentIndex = len(items)  # 设置当前索引为第一组的末尾
            super().scrollToItem(self.item(self.currentIndex()-self.visibleNumber//2), QListWidget.PositionAtTop)  # 从顶部位置开始显示
        else:
            n = self.visibleNumber // 2 

            self._addColumnItems(['']*n, True) 
            self._addColumnItems(items)  # 添加实际项目
            self._addColumnItems(['']*n, True)  # 添加n个禁用的空项目

            self._currentIndex = n  # 设置当前索引为第一个实际项目的位置

    def _addColumnItems(self, items, disabled=False):
        """
        内部方法：添加一列项目到列表中
        
        参数:
            items: list - 要添加的项目列表
            disabled: bool - 是否禁用项目
        """
        for i in items:
            item = QListWidgetItem(str(i), self)  # 创建列表项目
            item.setSizeHint(self.itemSize)
            item.setTextAlignment(self.align | Qt.AlignVCenter)
            if disabled:  # 如果设置为禁用
                item.setFlags(Qt.NoItemFlags)  # 移除所有项目标志（禁用交互）

            self.addItem(item)  # 添加项目到列表

    def _onItemClicked(self, item):
        """
        内部方法：处理项目点击事件
        
        参数:
            item: QListWidgetItem - 被点击的项目
        """
        self.setCurrentIndex(self.row(item))  # 设置当前索引为被点击项目的行号
        self.scrollToItem(self.currentItem())  # 滚动到当前项目

    def setSelectedItem(self, text: str):
        """
        设置选中的项目
        
        参数:
            text: str - 要选中的项目文本
        """
        if text is None:  # 如果文本为None
            return  # 直接返回

        items = self.findItems(str(text), Qt.MatchExactly)  # 精确查找匹配的项目
        if not items:  # 如果没有找到匹配项目
            return  # 直接返回

        if len(items) >= 2:  # 如果找到多个匹配项目（循环模式下）
            self.setCurrentIndex(self.row(items[1]))  # 选择第二个匹配项（通常是中间一组的项目）
        else:  # 如果只找到一个匹配项
            self.setCurrentIndex(self.row(items[0]))  # 选择第一个匹配项

        super().scrollToItem(self.currentItem(), QListWidget.PositionAtCenter)  # 滚动到项目中心位置

    def scrollToItem(self, item: QListWidgetItem, hint=QListWidget.PositionAtCenter):
        """
        滚动到指定项目
        
        参数:
            item: QListWidgetItem - 要滚动到的项目
            hint: QListWidget.ScrollHint - 滚动提示（默认居中）
        """
        # 滚动到中心位置
        index = self.row(item)  # 获取项目的行号
        y = item.sizeHint().height() * (index - self.visibleNumber // 2)  # 计算滚动位置
        self.vScrollBar.scrollTo(y)  # 使用平滑滚动条滚动到指定位置

        # 清除选择
        self.clearSelection()  # 清除所有选择
        item.setSelected(False)  # 取消当前项目的选中状态

        self.currentItemChanged.emit(item)  # 发射当前项目变更信号

    def wheelEvent(self, e):
        """
        处理鼠标滚轮事件
        
        参数:
            e: QWheelEvent - 鼠标滚轮事件对象
        """
        if e.angleDelta().y() < 0:  # 滚轮向下滚动
            self.scrollDown()  # 向下滚动一个项目
        else:  # 滚轮向上滚动
            self.scrollUp()  # 向上滚动一个项目

    def scrollDown(self):
        """ 向下滚动一个项目 """
        self.setCurrentIndex(self.currentIndex() + 1)  # 当前索引加1
        self.scrollToItem(self.currentItem())  # 滚动到新的当前项目

    def scrollUp(self):
        """ 向上滚动一个项目 """
        self.setCurrentIndex(self.currentIndex() - 1)  # 当前索引减1
        self.scrollToItem(self.currentItem())  # 滚动到新的当前项目

    def enterEvent(self, e):
        """
        鼠标进入事件 - 显示滚动按钮
        
        参数:
            e: QEvent - 事件对象
        """
        self.upButton.show()  # 显示向上按钮
        self.downButton.show()  # 显示向下按钮
        self.setStyleSheet("")
    def leaveEvent(self, e):
        """
        鼠标离开事件 - 隐藏滚动按钮
        
        参数:
            e: QEvent - 事件对象
        """
        self.upButton.hide()  # 隐藏向上按钮
        self.downButton.hide()  # 隐藏向下按钮

        self.setStyleSheet("""
            QListView::item:hover {
                background: transparent;
                border: none;
            }
        """)
    def resizeEvent(self, e):
        """
        窗口大小调整事件 - 重新定位滚动按钮
        
        参数:
            e: QResizeEvent - 尺寸调整事件对象
        """
        self.upButton.resize(self.width(), 34)  # 设置向上按钮尺寸（宽度与列表相同，高度34像素）
        self.downButton.resize(self.width(), 34)  # 设置向下按钮尺寸（宽度与列表相同，高度34像素）
        self.downButton.move(0, self.height() - 34)  # 将向下按钮移动到底部位置

    def eventFilter(self, obj, e: QEvent):
        """
        事件过滤器 - 处理键盘按键事件
        
        参数:
            obj: QObject - 事件源对象
            e: QEvent - 事件对象
        
        返回:
            bool - 是否处理了事件
        """
        if obj is not self or e.type() != QEvent.KeyPress:  # 如果事件源不是自身或不是按键事件
            return super().eventFilter(obj, e)  # 调用父类的事件过滤器

        if e.key() == Qt.Key_Down:  # 如果按下向下箭头键
            self.scrollDown()  # 向下滚动
            return True  # 已处理事件
        elif e.key() == Qt.Key_Up:  # 如果按下向上箭头键
            self.scrollUp()  # 向上滚动
            return True  # 已处理事件

        return super().eventFilter(obj, e)  # 调用父类的事件过滤器处理其他事件

    def currentItem(self):
        """ 获取当前项目 """
        return self.item(self.currentIndex())  # 返回当前索引对应的项目

    def currentIndex(self):
        """ 获取当前索引 """
        return self._currentIndex  # 返回当前索引值

    def setCurrentIndex(self, index: int):
        """
        设置当前索引
        
        参数:
            index: int - 要设置的索引
        """
        if not self.isCycle:  # 如果不是循环模式
            n = self.visibleNumber // 2  # 计算可见区域的中间位置
            self._currentIndex = max(  # 限制索引范围在有效项目区间内
                n, min(n + len(self.originItems) - 1, index))
        else:  # 如果是循环模式
            N = self.count() // 2  # 获取一半项目数量（因为列表中项目被重复添加了两次）
            m = (self.visibleNumber + 1) // 2  # 计算中间位置
            self._currentIndex = index  # 设置当前索引

            # 滚动到中心位置以实现循环滚动效果
            if index >= self.count() - m:  # 如果索引接近列表末尾
                self._currentIndex = N + index - self.count()  # 重置索引到开头区域
                super().scrollToItem(self.item(self.currentIndex() - 1), self.PositionAtCenter)  # 滚动到新位置
            elif index <= m - 1:  # 如果索引接近列表开头
                self._currentIndex = N + index  # 重置索引到末尾区域
                super().scrollToItem(self.item(N + index + 1), self.PositionAtCenter)  # 滚动到新位置