# coding:utf-8
from enum import Enum
import sys
from typing import Union
import weakref

from PyQt5.QtCore import (Qt, QEvent, QSize, QRectF, QObject, QPropertyAnimation,
                          QEasingCurve, QTimer, pyqtSignal, QParallelAnimationGroup, QPoint)
from PyQt5.QtGui import QPainter, QIcon, QColor
from PyQt5.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QToolButton, QGraphicsOpacityEffect, QApplication)

from ...common.auto_wrap import TextWrap
from ...common.style_sheet import FluentStyleSheet, themeColor
from ...common.icon import FluentIconBase, Theme, isDarkTheme,drawIcon
from ...common.icon import FluentIcon as FIF

from ..widgets.button import TransparentToolButton


class InfoBarIcon(FluentIconBase, Enum):
    """ 信息栏图标枚举类，定义信息栏支持的图标类型 """

    INFORMATION = "Info"       # 信息类型图标
    SUCCESS = "Success"        # 成功类型图标
    WARNING = "Warning"        # 警告类型图标
    ERROR = "Error"            # 错误类型图标

    def path(self, theme=Theme.AUTO):
        """
        获取图标路径（根据主题自动切换明暗模式图标）
        
        参数:
            theme: Theme枚举，指定主题模式（AUTO/light/dark）
            
        返回:
            str: 对应主题的SVG图标文件路径
        """
        if theme == Theme.AUTO:
            # 自动模式下，根据当前系统主题判断使用深色还是浅色图标
            color = "dark" if isDarkTheme() else "light"
        else:
            # 手动指定主题时，直接使用对应主题值
            color = theme.value.lower()

        # 返回拼接后的图标路径（基于资源文件）
        return f':/resource/images/info_bar/{self.value}_{color}.svg'


class InfoBarPosition(Enum):
    """ 信息栏位置枚举类，定义信息栏在父窗口中的显示位置 """
    TOP = 0                     # 顶部居中
    BOTTOM = 1                  # 底部居中
    TOP_LEFT = 2                # 左上角
    TOP_RIGHT = 3               # 右上角
    BOTTOM_LEFT = 4             # 左下角
    BOTTOM_RIGHT = 5            # 右下角
    NONE = 6                    # 无预设位置（自定义定位）


class InfoIconWidget(QWidget):
    """ 信息栏图标部件，用于在信息栏中显示指定图标 """

    def __init__(self, icon: InfoBarIcon, parent=None):
        """
        初始化图标部件
        
        参数:
            icon: InfoBarIcon枚举，指定要显示的图标类型
            parent: QWidget，父部件
        """
        super().__init__(parent=parent)
        self.setFixedSize(36, 36)  # 设置部件固定大小为36x36像素
        self.icon = icon            # 保存图标类型

    def paintEvent(self, e):
        """
        重写绘制事件，绘制图标
        
        参数:
            e: QPaintEvent，绘制事件对象
        """
        painter = QPainter(self)    # 创建画家对象
        # 设置画家渲染提示：抗锯齿和平滑像素变换
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # 定义图标绘制区域（矩形）：x=10, y=10, 宽=15, 高=15
        rect = QRectF(10, 10, 15, 15)
        if self.icon != InfoBarIcon.INFORMATION:
            # 非信息类型图标，直接绘制
            drawIcon(self.icon, painter, rect)
        else:
            # 信息类型图标，使用主题色填充（indexes=[0]指定SVG中需要填充的路径索引）
            drawIcon(self.icon, painter, rect, indexes=[0], fill=themeColor().name())


class InfoBar(QFrame):
    """ 信息提示栏部件，用于显示通知、警告、错误等提示信息 """

    closedSignal = pyqtSignal()  # 信息栏关闭时发出的信号
    _desktopView = None          # 桌面级信息栏容器（静态变量）

    def __init__(self, icon: Union[InfoBarIcon, FluentIconBase, QIcon, str], title: str, content: str,
                 orient=Qt.Horizontal, isClosable=True, duration=1000, position=InfoBarPosition.TOP_RIGHT,
                 parent=None):
        """
        初始化信息栏
        
        参数:
            icon: 图标类型，支持InfoBarIcon枚举、FluentIconBase枚举、QIcon对象或字符串路径
            title: 标题文本，信息栏的简短标题
            content: 内容文本，信息栏的详细描述
            orient: 布局方向，Qt.Horizontal（水平）或Qt.Vertical（垂直），短内容建议水平布局
            isClosable: 是否可关闭，True显示关闭按钮，False隐藏
            duration: 显示时长（毫秒），小于0时永久显示，否则到时自动关闭
            position: 显示位置，InfoBarPosition枚举指定
            parent: 父部件，信息栏将显示在该部件内
        """
        super().__init__(parent=parent)
        self.title = title                # 保存标题文本
        self.content = content            # 保存内容文本
        self.orient = orient              # 保存布局方向
        self.icon = icon                  # 保存图标
        self.duration = duration          # 保存显示时长
        self.isClosable = isClosable      # 保存是否可关闭状态
        self.position = position          # 保存显示位置

        self.titleLabel = QLabel(self)    # 标题标签部件
        self.contentLabel = QLabel(self)  # 内容标签部件
        # 关闭按钮（使用透明工具按钮，图标为关闭图标）
        self.closeButton = TransparentToolButton(FIF.CLOSE, self)
        self.iconWidget = InfoIconWidget(icon)  # 图标部件（使用自定义InfoIconWidget）

        self.hBoxLayout = QHBoxLayout(self)          # 主水平布局
        # 文本布局：水平布局（水平方向时）或垂直布局（垂直方向时）
        self.textLayout = QHBoxLayout() if self.orient == Qt.Horizontal else QVBoxLayout()
        # 部件布局：水平布局（水平方向时）或垂直布局（垂直方向时）
        self.widgetLayout = QHBoxLayout() if self.orient == Qt.Horizontal else QVBoxLayout()

        self.opacityEffect = QGraphicsOpacityEffect(self)  # 透明度效果对象
        # 透明度动画：控制透明度效果的opacity属性
        self.opacityAni = QPropertyAnimation(self.opacityEffect, b'opacity', self)

        self.lightBackgroundColor = None  # 浅色主题背景色（自定义时使用）
        self.darkBackgroundColor = None   # 深色主题背景色（自定义时使用）

        self.__initWidget()  # 初始化界面部件

    def __initWidget(self):
        """ 初始化界面部件（设置透明度、按钮样式、布局等） """
        self.opacityEffect.setOpacity(1)  # 设置初始透明度为1（完全不透明）
        self.setGraphicsEffect(self.opacityEffect)  # 为部件应用透明度效果

        self.closeButton.setFixedSize(36, 36)       # 设置关闭按钮大小为36x36像素
        self.closeButton.setIconSize(QSize(12, 12))  # 设置关闭按钮图标大小为12x12像素
        self.closeButton.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停为手型光标
        self.closeButton.setVisible(self.isClosable)  # 根据isClosable显示/隐藏关闭按钮

        self.__setQss()    # 设置样式表
        self.__initLayout()  # 初始化布局

        self.closeButton.clicked.connect(self.close)  # 关闭按钮点击信号连接到close方法

    def __initLayout(self):
        """ 初始化布局（设置边距、间距、添加部件到布局） """
        self.hBoxLayout.setContentsMargins(6, 6, 6, 6)  # 设置主布局外边距（上、右、下、左）
        self.hBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)  # 主布局大小约束：最小尺寸
        self.textLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)  # 文本布局大小约束：最小尺寸
        self.textLayout.setAlignment(Qt.AlignTop)  # 文本布局内控件顶部对齐
        self.textLayout.setContentsMargins(1, 8, 0, 8)  # 文本布局内边距

        self.hBoxLayout.setSpacing(0)  # 主布局控件间距为0
        self.textLayout.setSpacing(5)  # 文本布局控件间距为5

        # 添加图标部件到主布局（顶部左对齐）
        self.hBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignTop | Qt.AlignLeft)

        # 添加标题标签到文本布局（顶部对齐，占1份空间）
        self.textLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.titleLabel.setVisible(bool(self.title))  # 标题为空时隐藏标签

        # 水平布局时，标题和内容间添加7像素间距
        if self.orient == Qt.Horizontal:
            self.textLayout.addSpacing(7)

        # 添加内容标签到文本布局（顶部对齐，占1份空间）
        self.textLayout.addWidget(self.contentLabel, 1, Qt.AlignTop)
        self.contentLabel.setVisible(bool(self.content))  # 内容为空时隐藏标签
        self.hBoxLayout.addLayout(self.textLayout)  # 将文本布局添加到主布局

        # 添加部件布局（用于添加自定义控件）
        if self.orient == Qt.Horizontal:
            self.hBoxLayout.addLayout(self.widgetLayout)  # 水平布局时添加到主布局
            self.widgetLayout.setSpacing(10)  # 部件布局间距为10
        else:
            self.textLayout.addLayout(self.widgetLayout)  # 垂直布局时添加到文本布局

        self.hBoxLayout.addSpacing(12)  # 主布局添加12像素间距
        # 添加关闭按钮到主布局（顶部左对齐）
        self.hBoxLayout.addWidget(self.closeButton, 0, Qt.AlignTop | Qt.AlignLeft)

        self._adjustText()  # 调整文本显示（自动换行）

    def __setQss(self):
        """ 设置样式表（通过对象名和属性让样式表生效） """
        self.titleLabel.setObjectName('titleLabel')    # 设置标题标签对象名（用于QSS选择）
        self.contentLabel.setObjectName('contentLabel')  # 设置内容标签对象名
        if isinstance(self.icon, Enum):
            # 如果图标是枚举类型，设置type属性为枚举值（用于QSS根据类型设置不同样式）
            self.setProperty('type', self.icon.value)

        FluentStyleSheet.INFO_BAR.apply(self)  # 应用信息栏样式表

    def __fadeOut(self):
        """ 淡出动画（信息栏关闭前的渐隐效果） """
        self.opacityAni.setDuration(200)  # 动画时长200毫秒
        self.opacityAni.setStartValue(1)  # 起始透明度1（不透明）
        self.opacityAni.setEndValue(0)    # 结束透明度0（完全透明）
        self.opacityAni.finished.connect(self.close)  # 动画结束后关闭部件
        self.opacityAni.start()  # 启动动画

    def _adjustText(self):
        """ 调整文本显示（自动换行，限制最大宽度） """
        # 计算最大宽度：父部件存在时为父部件宽度-50，否则为900像素
        w = 900 if not self.parent() else (self.parent().width() - 50)

        # 调整标题文本：根据宽度计算最大字符数（10像素/字符，限制30-120字符）
        chars = max(min(w / 10, 120), 30)
        # 使用TextWrap工具换行，取第一行（超出部分省略）
        self.titleLabel.setText(TextWrap.wrap(self.title, chars, False)[0])

        # 调整内容文本：根据宽度计算最大字符数（9像素/字符，限制30-120字符）
        chars = max(min(w / 9, 120), 30)
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])
        self.adjustSize()  # 调整部件大小以适应文本

    def addWidget(self, widget: QWidget, stretch=0):
        """
        向信息栏添加自定义部件
        
        参数:
            widget: 要添加的部件
            stretch: 拉伸因子，控制部件在布局中所占空间比例
        """
        self.widgetLayout.addSpacing(6)  # 添加6像素间距
        # 对齐方式：垂直布局时顶部对齐，水平布局时垂直居中
        align = Qt.AlignTop if self.orient == Qt.Vertical else Qt.AlignVCenter
        # 添加部件到部件布局（左对齐+指定对齐方式，拉伸因子为stretch）
        self.widgetLayout.addWidget(widget, stretch, Qt.AlignLeft | align)

    def setCustomBackgroundColor(self, light, dark):
        """
        设置自定义背景色（支持浅色/深色主题分别设置）
        
        参数:
            light: 浅色主题背景色（QColor/颜色字符串/Qt全局颜色）
            dark: 深色主题背景色（QColor/颜色字符串/Qt全局颜色）
        """
        self.lightBackgroundColor = QColor(light)  # 转换为QColor并保存
        self.darkBackgroundColor = QColor(dark)
        self.update()  # 触发重绘以应用新背景色

    def eventFilter(self, obj, e: QEvent):
        """
        事件过滤器（监听父部件事件，如调整大小时重新计算文本）
        
        参数:
            obj: 事件源对象
            e: 事件对象
            
        返回:
            bool: 是否拦截事件
        """
        if obj is self.parent():
            # 父部件调整大小或窗口状态变化时，重新调整文本
            if e.type() in [QEvent.Resize, QEvent.WindowStateChange]:
                self._adjustText()

        return super().eventFilter(obj, e)  # 调用父类实现

    def closeEvent(self, e):
        """
        关闭事件（信息栏关闭时触发）
        
        参数:
            e: 关闭事件对象
        """
        self.closedSignal.emit()  # 发出关闭信号
        self.deleteLater()  # 安排部件延迟删除（释放资源）
        e.ignore()  # 忽略事件（由deleteLater处理）

    def showEvent(self, e):
        """
        显示事件（信息栏显示时触发）
        
        参数:
            e: 显示事件对象
        """
        self._adjustText()  # 显示前调整文本
        super().showEvent(e)  # 调用父类显示事件

        # 显示时长>=0时，启动定时器，到时后执行淡出动画
        if self.duration >= 0:
            QTimer.singleShot(self.duration, self.__fadeOut)

        # 非NONE位置时，通过InfoBarManager管理位置和动画
        if self.position != InfoBarPosition.NONE:
            manager = InfoBarManager.make(self.position)
            manager.add(self)

        # 父部件存在时，安装事件过滤器（监听父部件大小变化）
        if self.parent():
            self.parent().installEventFilter(self)

    def paintEvent(self, e):
        """
        绘制事件（自定义背景色时绘制背景）
        
        参数:
            e: 绘制事件对象
        """
        super().paintEvent(e)  # 调用父类绘制（绘制框架等）
        if self.lightBackgroundColor is None:
            return  # 未设置自定义背景色时不绘制

        painter = QPainter(self)  # 创建画家对象
        painter.setRenderHints(QPainter.Antialiasing)  # 启用抗锯齿
        painter.setPen(Qt.NoPen)  # 不绘制边框

        # 根据当前主题选择背景色
        if isDarkTheme():
            painter.setBrush(self.darkBackgroundColor)
        else:
            painter.setBrush(self.lightBackgroundColor)

        # 绘制圆角矩形背景（调整矩形大小，留出1像素边框空间）
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 6, 6)  # 圆角半径6像素

    @classmethod
    def new(cls, icon, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
            position=InfoBarPosition.TOP_RIGHT, parent=None):
        """
        创建信息栏实例并显示（工厂方法）
        
        参数:
            同__init__方法
            
        返回:
            InfoBar: 创建的信息栏实例
        """
        w = InfoBar(icon, title, content, orient, isClosable, duration, position, parent)
        w.show()  # 显示信息栏
        return w

    @classmethod
    def info(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
             position=InfoBarPosition.TOP_RIGHT, parent=None):
        """创建信息类型信息栏（快捷方法）"""
        return cls.new(InfoBarIcon.INFORMATION, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def success(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
                position=InfoBarPosition.TOP_RIGHT, parent=None):
        """创建成功类型信息栏（快捷方法）"""
        return cls.new(InfoBarIcon.SUCCESS, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def warning(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
                position=InfoBarPosition.TOP_RIGHT, parent=None):
        """创建警告类型信息栏（快捷方法）"""
        return cls.new(InfoBarIcon.WARNING, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def error(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
              position=InfoBarPosition.TOP_RIGHT, parent=None):
        """创建错误类型信息栏（快捷方法）"""
        return cls.new(InfoBarIcon.ERROR, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def desktopView(cls):
        """
        获取桌面级信息栏容器（静态方法）
        
        返回:
            DesktopInfoBarView: 桌面级容器实例（用于在桌面显示信息栏）
        """
        if not cls._desktopView:
            cls._desktopView = DesktopInfoBarView()
            cls._desktopView.show()  # 首次调用时创建并显示容器

        return cls._desktopView


class InfoBarManager(QObject):
    """ 信息栏管理器，负责管理信息栏的位置、动画和布局 """

    _instance = None  # 单例实例
    managers = {}     # 位置管理器注册表（键：InfoBarPosition，值：管理器类）

    def __new__(cls, *args, **kwargs):
        """ 单例模式实现（确保每个管理器类型只有一个实例） """
        if cls._instance is None:
            cls._instance = super(InfoBarManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.__initialized = False  # 初始化标记

        return cls._instance

    def __init__(self):
        super().__init__()
        if self.__initialized:
            return  # 已初始化过则返回

        self.spacing = 16  # 信息栏之间的间距
        self.margin = 24   # 信息栏与父部件边缘的边距
        # 弱引用字典：键为父部件，值为该父部件下的信息栏列表（避免内存泄漏）
        self.infoBars = weakref.WeakKeyDictionary() 
        # 弱引用字典：键为父部件，值为该父部件的动画组（并行动画）
        self.aniGroups = weakref.WeakKeyDictionary()
        self.slideAnis = []  # 滑动动画列表
        self.dropAnis = []   # 下落动画列表
        self.__initialized = True  # 标记为已初始化

    def add(self, infoBar: InfoBar):
        """
        添加信息栏到管理器（设置动画和位置）
        
        参数:
            infoBar: 要添加的信息栏实例
        """
        p = infoBar.parent()  # 获取父部件
        if not p:
            return  # 无父部件时不处理

        if p not in self.infoBars:
            # 父部件首次添加信息栏：安装事件过滤器，初始化信息栏列表和动画组
            p.installEventFilter(self)
            self.infoBars[p] = []
            self.aniGroups[p] = QParallelAnimationGroup(self)

        if infoBar in self.infoBars[p]:
            return  # 信息栏已添加过则返回

        # 已有信息栏时，为新信息栏添加下落动画（其他信息栏下移腾出空间）
        if self.infoBars[p]:
            dropAni = QPropertyAnimation(infoBar, b'pos')  # 位置属性动画
            dropAni.setDuration(200)  # 动画时长200毫秒

            self.aniGroups[p].addAnimation(dropAni)  # 添加到动画组
            self.dropAnis.append(dropAni)

            infoBar.setProperty('dropAni', dropAni)  # 信息栏关联下落动画

        # 添加滑动动画（信息栏滑入显示）
        self.infoBars[p].append(infoBar)
        slideAni = self._createSlideAni(infoBar)  # 创建滑动动画
        self.slideAnis.append(slideAni)

        infoBar.setProperty('slideAni', slideAni)  # 信息栏关联滑动动画
        # 信息栏关闭信号连接到remove方法（移除自身）
        infoBar.closedSignal.connect(lambda: self.remove(infoBar))

        slideAni.start()  # 启动滑动动画

    def remove(self, infoBar: InfoBar):
        """
        从管理器中移除信息栏（调整其他信息栏位置）
        
        参数:
            infoBar: 要移除的信息栏实例
        """
        p = infoBar.parent()
        if p not in self.infoBars:
            return

        if infoBar not in self.infoBars[p]:
            return

        self.infoBars[p].remove(infoBar)  # 从列表中移除

        # 移除下落动画
        dropAni = infoBar.property('dropAni')  # 获取信息栏的下落动画
        if dropAni:
            self.aniGroups[p].removeAnimation(dropAni)  # 从动画组移除
            self.dropAnis.remove(dropAni)

        # 移除滑动动画
        slideAni = infoBar.property('slideAni')
        if slideAni:
            self.slideAnis.remove(slideAni)

        # 更新剩余信息栏的位置（通过下落动画调整）
        self._updateDropAni(p)
        self.aniGroups[p].start()  # 启动动画组

    def _createSlideAni(self, infoBar: InfoBar):
        """
        创建滑动动画（信息栏从屏幕外滑入）
        
        参数:
            infoBar: 信息栏实例
            
        返回:
            QPropertyAnimation: 滑动动画对象
        """
        slideAni = QPropertyAnimation(infoBar, b'pos')  # 位置属性动画
        slideAni.setEasingCurve(QEasingCurve.OutQuad)  # 缓动曲线：先快后慢
        slideAni.setDuration(200)  # 动画时长200毫秒

        slideAni.setStartValue(self._slideStartPos(infoBar))  # 起始位置（屏幕外）
        slideAni.setEndValue(self._pos(infoBar))  # 结束位置（目标位置）

        return slideAni

    def _updateDropAni(self, parent):
        """
        更新下落动画（信息栏移除后，其他信息栏上移填补空位）
        
        参数:
            parent: 父部件
        """
        for bar in self.infoBars[parent]:
            ani = bar.property('dropAni')  # 获取信息栏的下落动画
            if not ani:
                continue

            ani.setStartValue(bar.pos())  # 起始位置为当前位置
            ani.setEndValue(self._pos(bar))  # 结束位置为新计算的目标位置

    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:
        """
        计算信息栏的目标位置（由子类实现具体位置逻辑）
        
        参数:
            infoBar: 信息栏实例
            parentSize: 父部件大小（可选，用于优化计算）
            
        返回:
            QPoint: 目标位置坐标
        """
        raise NotImplementedError  # 抽象方法，子类必须实现

    def _slideStartPos(self, infoBar: InfoBar) -> QPoint:
        """
        计算滑动动画的起始位置（由子类实现具体逻辑）
        
        参数:
            infoBar: 信息栏实例
            
        返回:
            QPoint: 起始位置坐标（屏幕外）
        """
        raise NotImplementedError  # 抽象方法，子类必须实现

    def eventFilter(self, obj, e: QEvent):
        """
        事件过滤器（监听父部件事件，如调整大小时重新计算信息栏位置）
        
        参数:
            obj: 事件源对象
            e: 事件对象
            
        返回:
            bool: 是否拦截事件
        """
        if obj not in self.infoBars:
            return False  # 非管理的父部件不处理

        # 父部件调整大小或窗口状态变化时，更新所有信息栏位置
        if e.type() in [QEvent.Resize, QEvent.WindowStateChange]:
            size = e.size() if e.type() == QEvent.Resize else None
            for bar in self.infoBars[obj]:
                bar.move(self._pos(bar, size))  # 移动信息栏到新位置

        return super().eventFilter(obj, e)  # 调用父类实现

    @classmethod # 类方法，用于注册位置管理器
    def register(cls, name):
        """
        注册位置管理器（装饰器，用于将子类注册到managers字典）
        
        参数:
            name: 注册名称（InfoBarPosition枚举值）
            
        返回:
            装饰器函数，用于注册管理器类
        """
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager  # 注册管理器类
            return Manager

        return wrapper

    @classmethod # 类方法，用于创建指定位置的管理器实例
    def make(cls, position: InfoBarPosition):
        """
        根据位置创建对应的管理器实例
        
        参数:
            position: InfoBarPosition枚举，指定位置
            
        返回:
            InfoBarManager: 对应位置的管理器实例
            
        异常:
            ValueError: 位置未注册时抛出
        """
        if position not in cls.managers:
            raise ValueError(f'`{position}` 是无效的位置类型。')

        return cls.managers[position]()  # 创建并返回管理器实例


@InfoBarManager.register(InfoBarPosition.TOP) 
class TopInfoBarManager(InfoBarManager):
    """ 顶部位置信息栏管理器（信息栏顶部居中堆叠） """

    def _pos(self, infoBar: InfoBar, parentSize=None):
        """计算顶部居中位置：水平居中，垂直方向按添加顺序堆叠"""
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        # 水平居中：(父部件宽度 - 信息栏宽度) // 2
        x = (infoBar.parent().width() - infoBar.width()) // 2
        y = self.margin  # 初始Y坐标为边距
        index = self.infoBars[p].index(infoBar)  # 获取信息栏索引
        # 累加前面信息栏的高度和间距（每个信息栏占：高度 + 间距）
        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)
        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        """滑动起始位置：目标位置上方16像素（从上往下滑入）"""
        pos = self._pos(infoBar)
        return QPoint(pos.x(), pos.y() - 16)


@InfoBarManager.register(InfoBarPosition.TOP_RIGHT)
class TopRightInfoBarManager(InfoBarManager):
    """ 右上角位置信息栏管理器（信息栏右上角垂直堆叠） """

    def _pos(self, infoBar: InfoBar, parentSize=None):
        """计算右上角位置：右对齐，上对齐，垂直方向堆叠"""
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        # 右对齐：父部件宽度 - 信息栏宽度 - 边距
        x = parentSize.width() - infoBar.width() - self.margin
        y = self.margin  # 初始Y坐标为边距
        index = self.infoBars[p].index(infoBar)
        # 累加前面信息栏的高度和间距
        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        """滑动起始位置：父部件右侧（从右往左滑入）"""
        return QPoint(infoBar.parent().width(), self._pos(infoBar).y())


@InfoBarManager.register(InfoBarPosition.BOTTOM_RIGHT)
class BottomRightInfoBarManager(InfoBarManager):
    """ 右下角位置信息栏管理器（信息栏右下角垂直堆叠） """

    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:
        """计算右下角位置：右对齐，下对齐，垂直方向堆叠（从下往上）"""
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        # 右对齐：父部件宽度 - 信息栏宽度 - 边距
        x = parentSize.width() - infoBar.width() - self.margin
        # 下对齐：父部件高度 - 信息栏高度 - 边距
        y = parentSize.height() - infoBar.height() - self.margin

        index = self.infoBars[p].index(infoBar)
        # 累加前面信息栏的高度和间距（从下往上堆叠，Y坐标减小）
        for bar in self.infoBars[p][0:index]:
            y -= (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        """滑动起始位置：父部件右侧（从右往左滑入）"""
        return QPoint(infoBar.parent().width(), self._pos(infoBar).y())


@InfoBarManager.register(InfoBarPosition.TOP_LEFT)
class TopLeftInfoBarManager(InfoBarManager):
    """ 左上角位置信息栏管理器（信息栏左上角垂直堆叠） """

    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:
        """计算左上角位置：左对齐，上对齐，垂直方向堆叠"""
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        y = self.margin  # 初始Y坐标为边距
        index = self.infoBars[p].index(infoBar)
        # 累加前面信息栏的高度和间距
        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)

        return QPoint(self.margin, y)  # X坐标为边距（左对齐）

    def _slideStartPos(self, infoBar: InfoBar):
        """滑动起始位置：父部件左侧（从左往右滑入）"""
        return QPoint(-infoBar.width(), self._pos(infoBar).y())


@InfoBarManager.register(InfoBarPosition.BOTTOM_LEFT)
class BottomLeftInfoBarManager(InfoBarManager):
    """ 左下角位置信息栏管理器（信息栏左下角垂直堆叠） """

    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:
        """计算左下角位置：左对齐，下对齐，垂直方向堆叠（从下往上）"""
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        # 下对齐：父部件高度 - 信息栏高度 - 边距
        y = parentSize.height() - infoBar.height() - self.margin
        index = self.infoBars[p].index(infoBar)
        # 累加前面信息栏的高度和间距（从下往上堆叠，Y坐标减小）
        for bar in self.infoBars[p][0:index]:
            y -= (bar.height() + self.spacing)

        return QPoint(self.margin, y)  # X坐标为边距（左对齐）

    def _slideStartPos(self, infoBar: InfoBar):
        """滑动起始位置：父部件左侧（从左往右滑入）"""
        return QPoint(-infoBar.width(), self._pos(infoBar).y())


@InfoBarManager.register(InfoBarPosition.BOTTOM)
class BottomInfoBarManager(InfoBarManager):
    """ 底部位置信息栏管理器（信息栏底部居中堆叠） """

    def _pos(self, infoBar: InfoBar, parentSize: QSize = None) -> QPoint:
        """计算底部居中位置：水平居中，垂直方向从下往上堆叠"""
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        # 水平居中：(父部件宽度 - 信息栏宽度) // 2
        x = (parentSize.width() - infoBar.width()) // 2
        # 初始Y坐标：父部件高度 - 信息栏高度 - 边距
        y = parentSize.height() - infoBar.height() - self.margin
        index = self.infoBars[p].index(infoBar)
        # 累加前面信息栏的高度和间距（从下往上堆叠，Y坐标减小）
        for bar in self.infoBars[p][0:index]:
            y -= (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        """滑动起始位置：目标位置下方16像素（从下往上滑入）"""
        pos = self._pos(infoBar)
        return QPoint(pos.x(), pos.y() + 16)


class DesktopInfoBarView(QWidget):
    """ 桌面级信息栏容器（用于在桌面显示信息栏，不受应用窗口限制） """

    def __init__(self, parent=None):
        super().__init__(parent)

        if sys.platform == "win32":
            # Windows系统：无边框、置顶、子窗口（避免任务栏显示）
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        else:
            # 其他系统：无边框、置顶、工具窗口、鼠标穿透
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 鼠标事件穿透（点击穿透到桌面）
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明
        # 设置窗口大小为屏幕可用区域（覆盖整个桌面）
        self.setGeometry(QApplication.primaryScreen().availableGeometry())
