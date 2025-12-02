# coding:utf-8

from typing import Iterable, List, Callable
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRectF, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter,QRegion
from PyQt5.QtWidgets import (QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                             QSizePolicy, QPushButton, QListWidgetItem)

from ...common.style_sheet import FluentStyleSheet,isDarkTheme,setShadowEffect,themeColor
from ...common.icon import FluentIcon
from ...common.screen import getCurrentScreenGeometry

from ..widgets import CycleListWidget,TransparentToolButton


class SeparatorWidget(QWidget):
    """ 分隔线部件
    用于在界面中创建水平或垂直分隔线，起到分隔不同UI元素的作用
    """

    def __init__(self, orient: Qt.Orientation, parent=None):
        super().__init__(parent=parent)
        if orient == Qt.Horizontal:  
            self.setFixedHeight(1)
        else:  
            self.setFixedWidth(1)

        self.setAttribute(Qt.WA_StyledBackground)   # 设置部件支持样式化背景
        # 应用时间选择器样式
        FluentStyleSheet.TIME_PICKER.apply(self)

class ItemMaskWidget(QWidget):
    """ 项目遮罩部件
    用于在选择器中显示和高亮当前选中的项目
    """

    def __init__(self, listWidgets: List[CycleListWidget], parent=None):
        super().__init__(parent=parent)
        
        self.listWidgets = listWidgets  # 保存列表部件引用

        self.setFixedHeight(37)
        
        FluentStyleSheet.TIME_PICKER.apply(self)

    def paintEvent(self, e):
        """ 绘制事件处理函数，负责绘制遮罩背景和文本"""
        
        painter = QPainter(self)
        # 设置渲染提示，启用抗锯齿和文本抗锯齿
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.TextAntialiasing)

        painter.setPen(Qt.NoPen)  # 不使用边框
        # 根据当前主题获取背景色
        painter.setBrush(themeColor())
        # 绘制圆角矩形背景
        painter.drawRoundedRect(self.rect().adjusted(5, 0, -5, 0), 5, 5)

        # 绘制文本
        # 根据当前主题设置文本颜色（深色主题用黑色，浅色主题用白色）
        painter.setPen(Qt.black if isDarkTheme() else Qt.white)
        
        painter.setFont(self.font())
        
        w, h = 0, self.height()
        
        # 遍历所有列表部件
        for i, p in enumerate(self.listWidgets):
            
            painter.save()  # 保存当前绘图状态

            # 绘制第一个项目的文本
            x = p.itemSize.width()//2 + self.x()
            item1 = p.itemAt(QPoint(x, self.y()+6)) # 获取指定位置的项目
            
            if not item1:   # 如果没有项目，恢复绘图状态并继续下一个循环
                painter.restore()
                continue

            iw = item1.sizeHint().width()
            
            y = p.visualItemRect(item1).y() # 获取项目的可视化矩形位置

            #print(f"{y}-{self.y()}: {y - self.y()}")

            painter.translate(w, 0) # 平移坐标系，将文本绘制到正确位置
            # 绘制文本
            self._drawText(item1, painter, 0)

            # 绘制第二个项目的文本
            # 获取第二个项目
            item2 = p.itemAt(self.pos() + QPoint(x, h - 6))
            # 绘制第二个项目的文本
            self._drawText(item2, painter, h)

            # 恢复绘图状态
            painter.restore()
            # 累加宽度（项目宽度+边距）
            w += iw+1

    def _drawText(self, item: QListWidgetItem, painter: QPainter, y: int):
        """ 绘制项目文本
        item: 列表项目对象
        painter: 绘图对象
        y: 文本y坐标
        """
        # 获取文本对齐方式
        align = item.textAlignment()
        # 获取项目大小
        w, h = item.sizeHint().width(), item.sizeHint().height()
        # 根据对齐方式设置文本矩形
        if align & Qt.AlignLeft:  # 左对齐
            rect = QRectF(15, y, w, h)      # padding-left: 11px
        elif align & Qt.AlignRight:  # 右对齐
            rect = QRectF(1, y, w-15, h)    # padding-right: 11px
        elif align & Qt.AlignCenter:  # 居中对齐
            rect = QRectF(1, y, w, h)

        # 绘制文本
        painter.drawText(rect, align, item.text())

class PickerPanel(QWidget):
    """ 选择器面板
    弹出式选择面板，包含多个选择列表和操作按钮
    """
    confirmed = pyqtSignal(list)

    ITEM_HEIGHT = 37

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.listWidgets = [] # 初始化列表部件列表

        # 创建UI组件
        self.view = QFrame(self)
        self.itemMaskWidget = ItemMaskWidget(self.listWidgets, self) # 创建项目遮罩部件
        self.hSeparatorWidget = SeparatorWidget(Qt.Horizontal, self.view) # 创建水平分隔线部件
        self.yesButton = TransparentToolButton(FluentIcon.ACCEPT, self.view) # 创建确认按钮
        self.cancelButton = TransparentToolButton(FluentIcon.CLOSE, self.view) # 创建取消按钮

        # 创建布局
        self.hBoxLayout = QHBoxLayout(self)
        self.listLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout(self.view)

        # 初始化部件
        self.__initWidget()

    def __initWidget(self):
        """ 初始化界面部件 """

        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)  # 设置窗口标志：弹出窗口、无边框、无阴影
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景透明

        setShadowEffect(self.view)  # 设置阴影效果
    
        self.yesButton.setIconSize(QSize(16, 16))
        self.cancelButton.setIconSize(QSize(13, 13))
        # 设置按钮固定高度
        self.yesButton.setFixedHeight(33)
        self.cancelButton.setFixedHeight(33)

        # 设置布局间距和边距
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        #加入内边距
        self.hBoxLayout.addWidget(self.view, 1, Qt.AlignCenter)
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize) # 设置布局大小约束为固定大小

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.listLayout, 1)
        self.vBoxLayout.addWidget(self.hSeparatorWidget)
        self.vBoxLayout.addLayout(self.buttonLayout, 1)
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.buttonLayout.setSpacing(6)
        self.buttonLayout.setContentsMargins(3, 3, 3, 3)
        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addWidget(self.cancelButton)
        # 设置按钮大小策略为扩展
        self.yesButton.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cancelButton.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 连接信号和槽
        self.yesButton.clicked.connect(self._fadeOut)
        self.yesButton.clicked.connect(
            lambda: self.confirmed.emit(self.value()))
        self.cancelButton.clicked.connect(self._fadeOut)

        self.view.setObjectName('view')
        FluentStyleSheet.TIME_PICKER.apply(self)



    def addColumn(self, items: Iterable, width: int, align=Qt.AlignCenter):
        """ 向视图添加一列
        items: 要添加的项目
        width: 项目宽度
        align: 项目文本对齐方式
        """
        # 如果已有列表部件，添加垂直分隔线
        if self.listWidgets:
            self.listLayout.addWidget(SeparatorWidget(Qt.Vertical))


        w = CycleListWidget(items, QSize(width, self.ITEM_HEIGHT), align, self)

        # 连接滚动条值变化信号到遮罩更新
        w.vScrollBar.valueChanged.connect(self.itemMaskWidget.update)

        self.listWidgets.append(w)
        self.listLayout.addWidget(w)

    def resizeEvent(self, e):
        """ 窗口大小变化事件
        e: 事件对象
        """
        self.itemMaskWidget.resize(self.view.width(), self.ITEM_HEIGHT) # 调整遮罩部件大小
        m = self.hBoxLayout.contentsMargins() 
        self.itemMaskWidget.move(m.left(), m.top() + 150)

    def value(self):
        """ 返回所有列的值
        返回: 值列表
        """
        return [i.currentItem().text() for i in self.listWidgets]

    def setValue(self, value: list):
        """ 设置所有列的值
        value: 值列表
        """
        # 检查值列表长度是否与列数量匹配
        if len(value) != len(self.listWidgets):
            return
        
        # 为每个列设置对应的值
        for v, w in zip(value, self.listWidgets):
            w.setSelectedItem(v)

    def exec(self, pos, ani=True):
        """ 显示面板
        pos: 弹出位置
        ani: 是否显示弹出动画
        """
        # 如果已经可见，直接返回
        if self.isVisible():
            return

        self.show()

        
        rect = getCurrentScreenGeometry()   # 获取当前屏幕几何信息
        w, h = self.width() + 5, self.height()
        # 调整位置，确保面板不会超出屏幕
        pos.setX(
            min(pos.x() - self.layout().contentsMargins().left(), rect.right() - w))
        pos.setY(max(rect.top(), min(pos.y() - 4, rect.bottom() - h + 5)))
        # 移动面板到指定位置
        self.move(pos)

        # 如果不需要动画，直接返回
        if not ani:
            return

        # 设置展开状态标志
        self.isExpanded = False
        # 创建属性动画（窗口不透明度）
        self.ani = QPropertyAnimation(self.view, b'windowOpacity', self)
        # 连接动画值变化信号到槽函数
        self.ani.valueChanged.connect(self._onAniValueChanged)
        # 设置动画参数
        self.ani.setStartValue(0)  # 开始不透明度
        self.ani.setEndValue(1)    # 结束不透明度
        self.ani.setDuration(400)  # 动画持续时间（毫秒）
        self.ani.setEasingCurve(QEasingCurve.OutQuad)  # 缓动曲线
        # 开始动画
        self.ani.start()

    def _onAniValueChanged(self, opacity):
        """ 动画值变化处理函数
        opacity: 当前不透明度值
        """
        # 获取布局边距
        m = self.layout().contentsMargins()
        # 计算遮罩区域大小
        w = self.view.width() + m.left() + m.right() + 120
        h = self.view.height() + m.top() + m.bottom() + 12
        # 根据展开状态设置不同的遮罩区域
        if not self.isExpanded:  # 展开动画
            y = int(h / 2 * (1 - opacity))
            self.setMask(QRegion(0, y, w, h-y*2))
        else:  # 收起动画
            y = int(h / 3 * (1 - opacity))
            self.setMask(QRegion(0, y, w, h-y*2))

    def _fadeOut(self):
        """ 淡出动画，关闭面板
        """
        # 设置展开状态标志为True（表示正在收起）
        self.isExpanded = True
        # 创建淡出动画
        self.ani = QPropertyAnimation(self, b'windowOpacity', self)
        # 连接动画信号
        self.ani.valueChanged.connect(self._onAniValueChanged)
        self.ani.finished.connect(self.deleteLater)
        # 设置动画参数
        self.ani.setStartValue(1)  # 开始不透明度
        self.ani.setEndValue(0)    # 结束不透明度
        self.ani.setDuration(150)  # 动画持续时间（毫秒）
        self.ani.setEasingCurve(QEasingCurve.OutQuad)  # 缓动曲线
        # 开始动画
        self.ani.start()


class PickerColumnButton(QPushButton):
    """ 选择器列按钮
    表示选择器中的一个列，包含名称、项目和格式化等信息
    """
    DEFAULT_HEIGHT = 37

    def __init__(self, name: str, items: Iterable, width: int,columnFormatter:Callable, align=Qt.AlignLeft, parent=None):
       
        super().__init__(text=name, parent=parent)
        
        self._name = name   # 保存列名称
        
        self._value = None  
        
        self._columnFormatter = columnFormatter # 保存列格式化函数

        self.setItems(items) # 设置项目列表
        
        self.setAlignment(align)   # 设置文本对齐方式
        
        self.setFixedSize(width, self.DEFAULT_HEIGHT)    # 设置固定大小
       
        self.setObjectName('pickerButton')   # 设置对象名称，用于样式选择器
        
        self.setProperty('hasBorder', False)    # 设置属性，表示没有边框
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 设置属性，表示鼠标事件透明

    @property
    def align(self):
        return self._align
    
    def setAlignment(self, align=Qt.AlignCenter):
        """ 设置文本对齐方式 """
        
        if align == Qt.AlignLeft:
            self.setProperty('align', 'left')
        elif align == Qt.AlignRight:
            self.setProperty('align', 'right')
        else:
            self.setProperty('align', 'center')

        self._align = align
        self.setStyle(QApplication.style())

    @property
    def value(self) -> str:
        """ 获取当前值 """

        return self._columnFormatter(self._value)
    
    def setValue(self, v):
        """ 设置当前值 """
        self._value = v
        
        if v is None:
            self.setText(self.name)
            self.setProperty('hasValue', False)
        else:
            self.setText(self.value + ' ' + self.name)
            self.setProperty('hasValue', True)

        self.setStyle(QApplication.style())

    @property
    def items(self):
        """ 获取所有项目 """
        return self._items

    def setItems(self, items: Iterable):
        """ 设置项目列表 """

        self._items = []

        for item in items:
            if item is None:
                continue
            self._items.append(self._columnFormatter(item))

    @property
    def name(self):
        """ 获取列名称
        返回: 列名称字符串
        """
        return self._name

    def setName(self, name: str):
        """ 设置列名称
        name: 新的列名称
        """
        if self.text() == self.name():
            self.setText(name)

        self._name = name
