# coding:utf-8
from enum import Enum

from PyQt5.QtCore import QEvent, QObject, QPoint, QTimer, Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame,QHBoxLayout, QLabel, QWidget, QAbstractItemView,QTableView

from ...common.style_sheet import FluentStyleSheet
from ...common.screen import getCurrentScreenGeometry
from ...common.style_sheet import setShadowEffect

class ToolTipPosition(Enum):
    """ 提示框位置枚举类，定义提示框相对于父窗口的显示位置 """

    TOP = 0              # 上方
    BOTTOM = 1           # 下方
    LEFT = 2             # 左侧
    RIGHT = 3            # 右侧
    TOP_LEFT = 4         # 左上角
    TOP_RIGHT = 5        # 右上角
    BOTTOM_LEFT = 6      # 左下角
    BOTTOM_RIGHT = 7     # 右下角


class ItemViewToolTipType(Enum):
    """ 项目视图提示框类型枚举类，定义在不同项目视图中的显示类型 """

    LIST = 0             # 列表视图类型
    TABLE = 1            # 表格视图类型


class ToolTip(QFrame):
    """ 自定义提示框类，实现带样式和动画效果的提示框 """

    def __init__(self, text='', parent=None):
        super().__init__(parent=parent) 
        self.__text = text              # 存储提示文本内容
        self.__duration = 1000          # 设置默认显示持续时间为1000毫秒

        self.container = self._createContainer()  # 创建提示框容器
        self.timer = QTimer(self)                 # 创建定时器，用于控制提示框自动隐藏

        self.setLayout(QHBoxLayout())             # 设置提示框的布局管理器为水平布局
        self.containerLayout = QHBoxLayout(self.container)  # 设置容器的布局管理器
        self.label = QLabel(text, self)           # 创建用于显示文本的标签

        # 设置布局边距
        self.layout().setContentsMargins(12, 8, 12, 12)  # 设置提示框的外边距
        self.layout().addWidget(self.container)           # 将容器添加到提示框布局中
        self.containerLayout.addWidget(self.label)        # 将标签添加到容器布局中
        self.containerLayout.setContentsMargins(8, 6, 8, 6)  # 设置容器的内边距

        # 添加透明度动画效果
        self.opacityAni = QPropertyAnimation(self, b'windowOpacity', self)  # 创建透明度动画
        self.opacityAni.setDuration(150)  # 设置动画持续时间为150毫秒


        # 添加阴影效果
        setShadowEffect(self.container, blurRadius=25, offset=(0, 5), color=QColor(0, 0, 0, 50))
        
        self.timer.setSingleShot(True)  # 设置定时器为单次触发模式
        self.timer.timeout.connect(self.hide)  # 连接定时器超时信号到隐藏方法

        # 设置窗口属性
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 设置鼠标事件透明
        self.setAttribute(Qt.WA_TranslucentBackground)      # 设置背景透明
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)  # 设置为工具窗口和无边框
        self.__setQss()  # 应用样式表

    def text(self):
        """ 获取提示框的文本内容 """
        return self.__text

    def setText(self, text):
        """ 设置提示框的文本内容 """
        self.__text = text 
        self.label.setText(text)  # 更新标签显示的文本
        self.container.adjustSize() # 调整容器大小以适应新文本
        self.adjustSize() # 调整提示框大小以适应新文本

    def duration(self):
        """ 获取提示框的显示持续时间 """
        return self.__duration 

    def setDuration(self, duration: int):
        """ 设置提示框的显示持续时间（毫秒）"""
        self.__duration = duration 

    def __setQss(self):
        """ 设置样式表，应用自定义外观 """
        self.container.setObjectName("container")  # 设置容器对象名称，用于样式表选择器
        self.label.setObjectName("contentLabel")   # 设置标签对象名称，用于样式表选择器
        FluentStyleSheet.TOOL_TIP.apply(self)      # 应用工具提示样式表
        self.label.adjustSize()  # 调整标签大小以适应文本
        self.adjustSize()        # 调整提示框大小以适应内容

    def _createContainer(self):
        """ 创建提示框的内容容器 """
        return QFrame(self)

    def showEvent(self, e):
        """ 当提示框显示时触发的事件处理器 """
        self.opacityAni.setStartValue(0)  # 设置透明度动画的起始值为0（完全透明）
        self.opacityAni.setEndValue(1)    # 设置透明度动画的结束值为1（完全不透明）
        self.opacityAni.start()           # 启动透明度动画

        self.timer.stop()  # 停止之前可能正在运行的定时器
        if self.duration() > 0:  # 如果设置了自动消失时间
            # 启动定时器，在指定时间后隐藏提示框
            self.timer.start(self.__duration + self.opacityAni.duration())

        super().showEvent(e)

    def hideEvent(self, e):
        """ 当提示框隐藏时触发的事件处理器 """
        self.timer.stop()  # 停止定时器
        super().hideEvent(e)

    def adjustPos(self, widget, position: ToolTipPosition):
        """ 调整提示框相对于指定窗口部件的位置

        参数:
        ----------
        widget: QWidget
            参考的窗口部件
        position: ToolTipPosition
            提示框相对于窗口部件的位置
        """
        manager = ToolTipPositionManager.make(position)  # 创建位置管理器实例
        self.move(manager.position(self, widget))  # 移动提示框到计算的位置


class ToolTipPositionManager:
    """ 提示框位置管理器基类，负责计算提示框的显示位置 """

    def position(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 计算提示框的显示位置，确保不会超出屏幕边界

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = self._pos(tooltip, parent)  # 获取子类实现的位置计算结果
        x, y = pos.x(), pos.y()  # 提取坐标

        rect = getCurrentScreenGeometry()  # 获取当前屏幕的几何信息
        # 确保提示框不会超出屏幕右边界和下边界，也不会小于屏幕左边界和上边界
        x = max(rect.left(), min(pos.x(), rect.right() - tooltip.width() - 4))
        y = max(rect.top(), min(pos.y(), rect.bottom() - tooltip.height() - 4))

        return QPoint(x, y)  # 返回调整后的位置

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 子类需要实现的抽象方法，计算提示框的基本位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        raise NotImplementedError  # 未实现异常，子类必须重写此方法

    @staticmethod
    def make(position: ToolTipPosition):
        """ 根据指定的位置类型创建对应的位置管理器

        参数:
        ----------
        position: ToolTipPosition
            提示框的位置枚举值

        返回值:
        ----------
        ToolTipPositionManager: 对应的位置管理器实例

        异常:
        ----------
        ValueError: 当位置类型无效时抛出
        """
        # 位置类型到管理器类的映射字典
        managers = {
            ToolTipPosition.TOP: TopToolTipManager,                  # 上方位置管理器
            ToolTipPosition.BOTTOM: BottomToolTipManager,            # 下方位置管理器
            ToolTipPosition.LEFT: LeftToolTipManager,                # 左侧位置管理器
            ToolTipPosition.RIGHT: RightToolTipManager,              # 右侧位置管理器
            ToolTipPosition.TOP_RIGHT: TopRightToolTipManager,       # 右上角位置管理器
            ToolTipPosition.BOTTOM_RIGHT: BottomRightToolTipManager, # 右下角位置管理器
            ToolTipPosition.TOP_LEFT: TopLeftToolTipManager,         # 左上角位置管理器
            ToolTipPosition.BOTTOM_LEFT: BottomLeftToolTipManager,   # 左下角位置管理器
        }

        if position not in managers:  # 如果位置类型无效
            raise ValueError(f'`{position}` 是无效的提示框位置。')  # 抛出值错误异常

        return managers[position]()  # 创建并返回对应的位置管理器实例


class TopToolTipManager(ToolTipPositionManager):
    """ 上方提示框位置管理器，将提示框显示在父窗口部件的上方中央 """

    def _pos(self, tooltip: ToolTip, parent: QWidget):
        """ 计算提示框在父窗口部件上方中央的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = parent.mapToGlobal(QPoint())  # 将父窗口部件的局部坐标转换为全局坐标
        # 计算水平居中的x坐标
        x = pos.x() + parent.width()//2 - tooltip.width()//2
        # 计算在父窗口部件上方的y坐标
        y = pos.y() - tooltip.height()
        return QPoint(x, y)  # 返回计算的位置


class BottomToolTipManager(ToolTipPositionManager):
    """ 下方提示框位置管理器，将提示框显示在父窗口部件的下方中央 """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 计算提示框在父窗口部件下方中央的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = parent.mapToGlobal(QPoint())  # 将父窗口部件的局部坐标转换为全局坐标
        # 计算水平居中的x坐标
        x = pos.x() + parent.width()//2 - tooltip.width()//2
        # 计算在父窗口部件下方的y坐标
        y = pos.y() + parent.height()
        return QPoint(x, y)  # 返回计算的位置


class LeftToolTipManager(ToolTipPositionManager):
    """ 左侧提示框位置管理器，将提示框显示在父窗口部件的左侧中央 """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 计算提示框在父窗口部件左侧中央的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = parent.mapToGlobal(QPoint())  # 将父窗口部件的局部坐标转换为全局坐标
        # 计算在父窗口部件左侧的x坐标
        x = pos.x() - tooltip.width()
        # 计算垂直居中的y坐标
        y = pos.y() + (parent.height() - tooltip.height()) // 2
        return QPoint(x, y)  # 返回计算的位置


class RightToolTipManager(ToolTipPositionManager):
    """ 右侧提示框位置管理器，将提示框显示在父窗口部件的右侧中央 """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 计算提示框在父窗口部件右侧中央的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = parent.mapToGlobal(QPoint())  # 将父窗口部件的局部坐标转换为全局坐标
        # 计算在父窗口部件右侧的x坐标
        x = pos.x() + parent.width()
        # 计算垂直居中的y坐标
        y = pos.y() + (parent.height() - tooltip.height()) // 2
        return QPoint(x, y)  # 返回计算的位置


class TopRightToolTipManager(ToolTipPositionManager):
    """ 右上角提示框位置管理器，将提示框显示在父窗口部件的右上角 """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 计算提示框在父窗口部件右上角的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = parent.mapToGlobal(QPoint())  # 将父窗口部件的局部坐标转换为全局坐标
        # 计算在父窗口部件右上角的x坐标，考虑提示框的右外边距
        x = pos.x() + parent.width() - tooltip.width() + tooltip.layout().contentsMargins().right()
        # 计算在父窗口部件上方的y坐标
        y = pos.y() - tooltip.height()
        return QPoint(x, y)  # 返回计算的位置


class TopLeftToolTipManager(ToolTipPositionManager):
    """ 左上角提示框位置管理器，将提示框显示在父窗口部件的左上角 """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 计算提示框在父窗口部件左上角的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = parent.mapToGlobal(QPoint())  # 将父窗口部件的局部坐标转换为全局坐标
        # 计算在父窗口部件左上角的x坐标，考虑提示框的左外边距
        x = pos.x() - tooltip.layout().contentsMargins().left()
        # 计算在父窗口部件上方的y坐标
        y = pos.y() - tooltip.height()
        return QPoint(x, y)  # 返回计算的位置


class BottomRightToolTipManager(ToolTipPositionManager):
    """ 右下角提示框位置管理器，将提示框显示在父窗口部件的右下角 """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 计算提示框在父窗口部件右下角的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = parent.mapToGlobal(QPoint())  # 将父窗口部件的局部坐标转换为全局坐标
        # 计算在父窗口部件右下角的x坐标，考虑提示框的右外边距
        x = pos.x() + parent.width() - tooltip.width() + tooltip.layout().contentsMargins().right()
        # 计算在父窗口部件下方的y坐标
        y = pos.y() + parent.height()
        return QPoint(x, y)  # 返回计算的位置


class BottomLeftToolTipManager(ToolTipPositionManager):
    """ 左下角提示框位置管理器，将提示框显示在父窗口部件的左下角 """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        """ 计算提示框在父窗口部件左下角的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        parent: QWidget
            参考的父窗口部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        pos = parent.mapToGlobal(QPoint())  # 将父窗口部件的局部坐标转换为全局坐标
        # 计算在父窗口部件左下角的x坐标，考虑提示框的左外边距
        x = pos.x() - tooltip.layout().contentsMargins().left()
        # 计算在父窗口部件下方的y坐标
        y = pos.y() + parent.height()
        return QPoint(x, y)  # 返回计算的位置


class ItemViewToolTipManager(ToolTipPositionManager):
    """ 项目视图提示框位置管理器，用于在项目视图（如列表、表格）中显示提示框 """

    def __init__(self, itemRect=QRect()):
        """ 初始化项目视图提示框位置管理器

        参数:
        ----------
        itemRect: QRect
            项目的矩形区域，提示框将相对于这个区域定位
        """
        super().__init__()  # 调用父类的初始化方法
        self.itemRect = itemRect  # 存储项目的矩形区域

    def _pos(self, tooltip: ToolTip, view: QAbstractItemView) -> QPoint:
        """ 计算提示框在项目视图中项目上方的位置

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        view: QAbstractItemView
            项目视图部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        # 将项目的局部坐标转换为全局坐标
        pos = view.mapToGlobal(self.itemRect.topLeft())
        x = pos.x()  # 使用项目的x坐标
        # 计算在项目上方的y坐标，添加10像素的偏移
        y = pos.y() - tooltip.height() + 10
        return QPoint(x, y)  # 返回计算的位置

    @staticmethod
    def make(tipType: ItemViewToolTipType, itemRect: QRect):
        """ 根据提示框类型创建对应的项目视图提示框位置管理器

        参数:
        ----------
        tipType: ItemViewToolTipType
            提示框类型枚举值
        itemRect: QRect
            项目的矩形区域

        返回值:
        ----------
        ItemViewToolTipManager: 对应的项目视图提示框位置管理器实例

        异常:
        ----------
        ValueError: 当提示框类型无效时抛出
        """
        # 提示框类型到管理器类的映射字典
        managers = {
            ItemViewToolTipType.LIST: ItemViewToolTipManager,    # 列表视图提示框管理器
            ItemViewToolTipType.TABLE: TableItemToolTipManager,  # 表格视图提示框管理器
        }

        if tipType not in managers:  # 如果提示框类型无效
            raise ValueError(f'`{tipType}` 是无效的提示框类型。')  # 抛出值错误异常

        return managers[tipType](itemRect)  # 创建并返回对应的位置管理器实例


class TableItemToolTipManager(ItemViewToolTipManager):
    """ 表格项目提示框位置管理器，专门用于在表格视图中显示提示框 """

    def _pos(self, tooltip: ToolTip, view: QTableView) -> QPoint:
        """ 计算提示框在表格视图中项目上方的位置，考虑表头的可见性

        参数:
        ----------
        tooltip: ToolTip
            要显示的提示框实例
        view: QTableView
            表格视图部件

        返回值:
        ----------
        QPoint: 计算出的提示框左上角坐标
        """
        # 将项目的局部坐标转换为全局坐标
        pos = view.mapToGlobal(self.itemRect.topLeft())
        # 计算x坐标，如果垂直表头可见，则加上表头宽度
        x = pos.x() + view.verticalHeader().isVisible() * view.verticalHeader().width()
        # 计算y坐标，考虑水平表头的可见性和高度
        y = pos.y() - tooltip.height() + view.horizontalHeader().isVisible() * view.horizontalHeader().height() + 10
        return QPoint(x, y)  # 返回计算的位置


class ToolTipFilter(QObject):
    """ 提示框事件过滤器类，用于拦截和处理窗口部件的事件以显示或隐藏提示框 """

    def __init__(self, parent: QWidget, showDelay=300, position=ToolTipPosition.TOP):
        """ 初始化提示框事件过滤器

        参数:
        ----------
        parent: QWidget
            要安装提示框的窗口部件
        showDelay: int
            鼠标悬停多长时间后显示提示框（毫秒）
        position: TooltipPosition
            提示框显示的位置
        """
        super().__init__(parent=parent) 
        self.isEnter = False           # 标记鼠标是否进入窗口部件
        self._tooltip = None           # 存储提示框实例
        self._tooltipDelay = showDelay # 多久会显示提示框（毫秒）
        self.position = position       # 存储提示框显示位置
        self.timer = QTimer(self)      # 创建定时器，用于控制提示框显示延迟
        self.timer.setSingleShot(True) # 设置定时器为单次触发模式
        self.timer.timeout.connect(self.showToolTip)  # 连接定时器超时信号到显示方法

    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        """ 事件过滤器，拦截和处理窗口部件的事件

        参数:
        ----------
        obj: QObject
            事件源对象
        e: QEvent
            事件对象

        返回值:
        ----------
        bool: True 表示事件已被处理，False 表示事件未被处理
        """
        if e.type() == QEvent.ToolTip:  # 如果是提示框事件
            return True  # 拦截默认的提示框处理
        
        elif e.type() in [QEvent.Hide, QEvent.Leave]:  # 如果是隐藏或离开事件
            self.hideToolTip()  # 隐藏提示框

        elif e.type() == QEvent.Enter:  # 如果是进入事件
            self.isEnter = True  # 标记鼠标已进入
            parent = self.parent()  # 获取父窗口部件
            if self._canShowToolTip():  # 检查是否可以显示提示框
                if self._tooltip is None:  # 如果提示框实例不存在
                    self._tooltip = self._createToolTip()  # 创建提示框实例

                # 获取父窗口部件的提示框显示持续时间，如果没有设置则为-1（不自动消失）
                t = parent.toolTipDuration() if parent.toolTipDuration() > 0 else -1
                self._tooltip.setDuration(t)  # 设置提示框持续时间

                # 启动定时器，延迟显示提示框
                self.timer.start(self._tooltipDelay)
        elif e.type() == QEvent.MouseButtonPress:  # 如果是鼠标按键按下事件
            self.hideToolTip()  # 隐藏提示框

        return super().eventFilter(obj, e)  # 调用父类的事件过滤器，处理未拦截的事件

    def _createToolTip(self):
        """ 创建提示框实例，子类可以重写此方法以创建自定义提示框

        返回值:
        ----------
        ToolTip: 提示框实例
        """
        # 创建默认的提示框实例，使用父窗口部件的提示文本和顶级窗口作为父窗口
        return ToolTip(self.parent().toolTip(), self.parent().window())

    def hideToolTip(self):
        """ 隐藏提示框 """
        self.isEnter = False  # 标记鼠标已离开
        self.timer.stop()     # 停止定时器
        if self._tooltip:     # 如果提示框实例存在
            self._tooltip.hide()  # 隐藏提示框

    def showToolTip(self):
        """ 显示提示框 """
        if not self.isEnter:  # 如果鼠标已经离开窗口部件
            return  # 不显示提示框

        parent = self.parent()  # 获取父窗口部件
        self._tooltip.setText(parent.toolTip())  # 设置提示框的文本
        self._tooltip.adjustPos(parent, self.position)  # 调整提示框位置
        self._tooltip.show()  # 显示提示框

    def setToolTipDelay(self, delay: int):
        """ 设置提示框显示的延迟时间

        参数:
        ----------
        delay: int
            延迟时间（毫秒）
        """
        self._tooltipDelay = delay  # 更新延迟时间

    def _canShowToolTip(self) -> bool:
        """ 检查是否可以显示提示框，子类可以重写此方法以自定义显示条件

        返回值:
        ----------
        bool: True 表示可以显示提示框，False 表示不可以
        """
        parent = self.parent() # 获取父窗口部件
        # 检查父窗口部件是否是有效的窗口部件、是否有提示文本、是否已启用
        return parent.isWidgetType() and parent.toolTip() and parent.isEnabled()

