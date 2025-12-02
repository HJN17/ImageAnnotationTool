# coding:utf-8
# 导入必要的类型提示
from typing import Dict

# 导入PyQt5相关模块
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPainter, QFont, QColor
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QHBoxLayout, QSizePolicy

# 导入自定义的配置和样式相关模块
from ...common.font import setFont
from ...common.router import router
from ...common.style_sheet import themeColor, FluentStyleSheet
from ...common.color import autoFallbackThemeColor
from ...common.animation import FluentAnimation,FluentAnimationType,FluentAnimationProperty

from ..widgets.button import PushButton



class PivotItem(PushButton):
    """ 导航枢轴项目
    
    表示导航枢轴（Pivot）中的单个项目，通常是一个可点击的按钮，
    用于在不同的内容页面之间切换。
    """

    # 定义项目点击信号，参数表示是否由用户触发
    itemClicked = pyqtSignal(bool)

    def _postInit(self):
        """ 初始化后的处理方法，由父类在构造函数后调用 """
        self.isSelected = False  # 设置初始选中状态为未选中
        self.setProperty('isSelected', False)  # 设置Qt属性，用于样式表
        # 连接点击信号到itemClicked信号
        self.clicked.connect(lambda: self.itemClicked.emit(True))
        # 设置属性，使布局使用部件的矩形区域进行计算
        self.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        FluentStyleSheet.PIVOT.apply(self)  # 应用枢轴样式
        setFont(self, 18)  # 设置字体大小为18

    def setSelected(self, isSelected: bool):
        """ 设置项目是否被选中
        
        Parameters
        ----------
        isSelected: bool
            项目是否被选中
        """
        if self.isSelected == isSelected:
            return  # 如果选中状态没有改变，直接返回

        self.isSelected = isSelected  # 更新选中状态
        self.setProperty('isSelected', isSelected)  # 更新Qt属性
        self.setStyle(QApplication.style())  # 刷新样式
        self.update()  # 更新界面显示

class Pivot(QWidget):
    """ 导航枢轴
    
    一种水平导航控件，包含多个PivotItem，用于在不同的内容页面之间进行切换。
    """

    # 定义当前项目改变信号，参数为新的路由键
    currentItemChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        """ 初始化导航枢轴
        
        Parameters
        ----------
        parent: QWidget, optional
            父部件
        """
        super().__init__(parent)  # 调用父类初始化方法
        self.items = {}  # type: Dict[str, PivotItem]  # 存储所有项目的字典，键为路由键，值为PivotItem
        self._currentRouteKey = None  # 当前选中项目的路由键

        self.lightIndicatorColor = QColor()  # 亮色主题下的指示器颜色
        self.darkIndicatorColor = QColor()   # 暗色主题下的指示器颜色

        self.hBoxLayout = QHBoxLayout(self)  # 创建水平布局
        # 创建滑动动画，用于指示器移动效果
        self.slideAni = FluentAnimation.create(FluentAnimationType.POINT_TO_POINT, FluentAnimationProperty.SCALE, value=0, parent=self)

        FluentStyleSheet.PIVOT.apply(self)  # 应用枢轴样式

        self.hBoxLayout.setSpacing(0)  # 设置布局间距为0
        self.hBoxLayout.setAlignment(Qt.AlignLeft)  # 设置布局左对齐
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)  # 设置布局边距为0
        # 设置布局大小约束为最小大小
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        # 设置部件大小策略为最小大小
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    def addItem(self, routeKey: str, text: str, onClick=None, icon=None):
        """ 添加导航项目
        
        Parameters
        ----------
        routeKey: str
            项目的唯一标识符
        
        text: str
            导航项目的文本
        
        onClick: callable, optional
            连接到项目点击信号的槽函数
        
        icon: str, optional
            导航项目的图标
        
        Returns
        -------
        PivotItem
            创建的导航项目
        """
        # 调用insertItem方法，索引为-1表示添加到末尾
        return self.insertItem(-1, routeKey, text, onClick, icon)

    def addWidget(self, routeKey: str, widget: PivotItem, onClick=None):
        """ 添加自定义导航部件
        
        Parameters
        ----------
        routeKey: str
            项目的唯一标识符
        
        widget: PivotItem
            要添加的导航部件
        
        onClick: callable, optional
            连接到项目点击信号的槽函数
        """
        # 调用insertWidget方法，索引为-1表示添加到末尾
        self.insertWidget(-1, routeKey, widget, onClick)

    def insertItem(self, index: int, routeKey: str, text: str, onClick=None, icon=None):
        """ 在指定位置插入导航项目
        
        Parameters
        ----------
        index: int
            插入位置的索引
        
        routeKey: str
            项目的唯一标识符
        
        text: str
            导航项目的文本
        
        onClick: callable, optional
            连接到项目点击信号的槽函数
        
        icon: str, optional
            导航项目的图标
        
        Returns
        -------
        PivotItem
            创建的导航项目
        """
        if routeKey in self.items:
            return  # 如果路由键已存在，直接返回

        item = PivotItem(text, self)  # 创建新的PivotItem
        if icon:
            item.setIcon(icon)  # 如果提供了图标，设置图标

        # 插入部件
        self.insertWidget(index, routeKey, item, onClick)
        return item

    def insertWidget(self, index: int, routeKey: str, widget: PivotItem, onClick=None):
        """ 在指定位置插入自定义导航部件
        
        Parameters
        ----------
        index: int
            插入位置的索引
        
        routeKey: str
            项目的唯一标识符
        
        widget: PivotItem
            要插入的导航部件
        
        onClick: callable, optional
            连接到项目点击信号的槽函数
        """
        if routeKey in self.items:
            return  # 如果路由键已存在，直接返回

        widget.setProperty('routeKey', routeKey)  # 设置路由键属性
        widget.itemClicked.connect(self._onItemClicked)  # 连接点击信号到内部处理函数
        if onClick:
            widget.itemClicked.connect(onClick)  # 连接点击信号到用户提供的槽函数

        self.items[routeKey] = widget  # 存储部件
        # 插入到布局，拉伸因子为1
        self.hBoxLayout.insertWidget(index, widget, 1)

    def removeWidget(self, routeKey: str):
        """ 移除导航部件
        
        Parameters
        ----------
        routeKey: str
            要移除项目的唯一标识符
        """
        if routeKey not in self.items:
            return  # 如果路由键不存在，直接返回

        item = self.items.pop(routeKey)  # 从字典中移除并获取部件
        self.hBoxLayout.removeWidget(item)  # 从布局中移除
        qrouter.remove(routeKey)  # 从路由器中移除路由
        item.deleteLater()  # 安排部件稍后删除

        if not self.items:
            self._currentRouteKey = None  # 如果没有项目了，重置当前路由键

    def clear(self):
        """ 清除所有导航项目 """
        for k, w in self.items.items():
            self.hBoxLayout.removeWidget(w)  # 从布局中移除
            qrouter.remove(k)  # 从路由器中移除路由
            w.deleteLater()  # 安排部件稍后删除

        self.items.clear()  # 清空项目字典
        self._currentRouteKey = None  # 重置当前路由键

    def currentItem(self):
        """ 获取当前选中的项目
        
        Returns
        -------
        PivotItem or None
            当前选中的项目，如果没有选中项目则返回None
        """
        if self._currentRouteKey is None:
            return None

        return self.widget(self._currentRouteKey)

    def currentRouteKey(self):
        """ 获取当前选中项目的路由键
        
        Returns
        -------
        str or None
            当前选中项目的路由键，如果没有选中项目则返回None
        """
        return self._currentRouteKey

    def setCurrentItem(self, routeKey: str):
        """ 设置当前选中的项目
        
        Parameters
        ----------
        routeKey: str
            要选中项目的唯一标识符
        """
        if routeKey not in self.items or routeKey == self.currentRouteKey():
            return  # 如果路由键不存在或已选中，直接返回

        self._currentRouteKey = routeKey  # 更新当前路由键
        # 启动滑动动画到新选中项目的x坐标
        self.slideAni.startAnimation(self.widget(routeKey).x())

        # 更新所有项目的选中状态
        for k, item in self.items.items():
            item.setSelected(k == routeKey)

        # 发出当前项目改变信号
        self.currentItemChanged.emit(routeKey)

    def showEvent(self, e):
        """ 部件显示事件处理
        
        Parameters
        ----------
        e: QShowEvent
            显示事件对象
        """
        super().showEvent(e)  # 调用父类方法
        self._adjustIndicatorPos()  # 调整指示器位置

    def setItemFontSize(self, size: int):
        """ 设置项目的字体像素大小
        
        Parameters
        ----------
        size: int
            要设置的字体像素大小
        """
        for item in self.items.values():
            font = item.font()  # 获取当前字体
            font.setPixelSize(size)  # 设置字体像素大小
            item.setFont(font)  # 应用新字体
            item.adjustSize()  # 调整部件大小以适应新字体

    def setItemText(self, routeKey: str, text: str):
        """ 设置项目的文本
        
        Parameters
        ----------
        routeKey: str
            项目的唯一标识符
        
        text: str
            新的项目文本
        """
        item = self.widget(routeKey)  # 获取项目
        item.setText(text)  # 设置文本

    def setIndicatorColor(self, light, dark):
        """ 设置指示器在亮色/暗色主题下的颜色
        
        Parameters
        ----------
        light: QColor or str
            亮色主题下的指示器颜色
        
        dark: QColor or str
            暗色主题下的指示器颜色
        """
        self.lightIndicatorColor = QColor(light)  # 更新亮色主题指示器颜色
        self.darkIndicatorColor = QColor(dark)    # 更新暗色主题指示器颜色
        self.update()  # 更新界面显示

    def _onItemClicked(self):
        """ 处理项目点击事件，内部方法 """
        item = self.sender()  # 获取发出信号的部件
        # 设置当前项目为点击的项目
        self.setCurrentItem(item.property('routeKey'))

    def widget(self, routeKey: str):
        """ 根据路由键获取导航部件
        
        Parameters
        ----------
        routeKey: str
            项目的唯一标识符
        
        Returns
        -------
        PivotItem
            对应的导航部件
        
        Raises
        ------
        RouteKeyError
            如果路由键不存在
        """
        if routeKey not in self.items:
            raise RouteKeyError(f"`{routeKey}` is illegal.")  # 抛出路由键错误

        return self.items[routeKey]  # 返回对应的部件

    def resizeEvent(self, e) -> None:
        """ 部件大小改变事件处理
        
        Parameters
        ----------
        e: QResizeEvent
            大小改变事件对象
        """
        super().resizeEvent(e)  # 调用父类方法
        self._adjustIndicatorPos()  # 调整指示器位置

    def _adjustIndicatorPos(self):
        """ 调整指示器位置，内部方法 """
        item = self.currentItem()  # 获取当前选中的项目
        if item:
            self.slideAni.stop()  # 停止当前动画
            self.slideAni.setValue(item.x())  # 设置动画值为当前项目的x坐标

    def paintEvent(self, e):
        """ 绘制部件
        
        Parameters
        ----------
        e: QPaintEvent
            绘制事件对象
        """
        super().paintEvent(e)  # 调用父类方法

        if not self.currentItem():
            return  # 如果没有选中项目，直接返回

        painter = QPainter(self)  # 创建画家对象
        painter.setRenderHints(QPainter.Antialiasing)  # 设置抗锯齿渲染
        painter.setPen(Qt.NoPen)  # 设置无 pen
        # 设置画刷颜色为当前主题对应的指示器颜色
        painter.setBrush(autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor))

        # 计算指示器的x坐标
        x = int(self.currentItem().width() / 2 - 8 + self.slideAni.value())
        # 绘制圆角矩形指示器
        painter.drawRoundedRect(x, self.height() - 3, 16, 3, 1.5, 1.5)