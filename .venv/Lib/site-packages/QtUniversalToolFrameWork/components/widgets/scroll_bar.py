# coding:utf-8

from enum import Enum
from PyQt5.QtCore import (QEvent, QEasingCurve, Qt, pyqtSignal, QPropertyAnimation, 
                          pyqtProperty, QRectF, QTimer, QPoint, QObject)
from PyQt5.QtGui import QPainter, QColor, QMouseEvent
from PyQt5.QtWidgets import QWidget, QToolButton, QAbstractScrollArea,QHBoxLayout, QVBoxLayout, QApplication, QAbstractItemView, QListView

from ...common.icon import FluentIcon
from ...common.style_sheet import isDarkTheme
from ...common.smooth_scroll import SmoothScroll


class ArrowButton(QToolButton):
    """ 
    箭头按钮组件
    用于滚动条的上下/左右箭头按钮，支持透明度动画和主题颜色适配
    可通过设置不同图标实现向上/向下/向左/向右功能
    """

    def __init__(self, icon: FluentIcon, parent=None):
        # 调用父类构造方法初始化组件
        super().__init__(parent=parent)
        # 设置按钮固定大小为10x10像素
        self.setFixedSize(10, 10)
        # 浅色主题下箭头颜色（黑色，透明度114/255）
        self.lightColor = QColor(0, 0, 0, 114)
        # 深色主题下箭头颜色（白色，透明度139/255）
        self.darkColor = QColor(255, 255, 255, 139)
        # 存储当前显示的图标（FluentIcon枚举类型）
        self._icon = icon
        # 初始透明度（0-1，1为完全不透明）
        self.opacity = 1

    def setOpacity(self, opacity):
        """设置按钮透明度"""
        self.opacity = opacity
        # 触发重绘事件，更新按钮显示
        self.update()

    def setLightColor(self, color):
        """设置浅色主题下的箭头颜色"""
        self.lightColor = QColor(color)
        self.update()

    def setDarkColor(self, color):
        """设置深色主题下的箭头颜色"""
        self.darkColor = QColor(color)
        self.update()

    def paintEvent(self, e):
        """重写绘图事件，自定义绘制箭头按钮"""
        # 创建绘图工具
        painter = QPainter(self)
        # 设置绘图提示：启用抗锯齿，使边缘更平滑
        painter.setRenderHints(QPainter.Antialiasing)

        # 根据当前主题选择箭头颜色
        color = self.darkColor if isDarkTheme() else self.lightColor
        # 设置透明度（综合按钮透明度和颜色自身透明度）
        painter.setOpacity(self.opacity * color.alpha() / 255)

        # 根据按钮状态调整图标大小：按下时7px，默认8px
        s = 7 if self.isDown() else 8
        # 计算图标绘制位置（居中显示）
        x = (self.width() - s) / 2
        # 渲染图标：使用指定颜色填充，绘制在(x, x)位置，大小sxs
        self._icon.render(painter, QRectF(x, x, s, s), fill=color.name())


class ScrollBarGroove(QWidget):
    """ 
    滚动条轨道组件
    作为滚动条的背景轨道，包含上下/左右箭头按钮，支持淡入淡出动画
    根据主题自动切换背景颜色，是滚动条的基础容器
    """

    def __init__(self, orient: Qt.Orientation, parent):
        super().__init__(parent=parent)
        # 轨道透明度（0-1，0为完全透明）
        self._opacity = 1
        # 浅色主题下轨道背景色（RGB:252,252,252，透明度217/255）
        self.lightBackgroundColor = QColor(252, 252, 252, 217)
        # 深色主题下轨道背景色（RGB:44,44,44，透明度245/255）
        self.darkBackgroundColor = QColor(44, 44, 44, 245)

        if orient == Qt.Vertical:
            # 垂直滚动条：固定宽度12px
            self.setFixedWidth(12)
            # 创建上下箭头按钮（上箭头用CARE_UP_SOLID图标）
            self.upButton = ArrowButton(FluentIcon.CARE_UP_SOLID, self)
            # 下箭头用CARE_DOWN_SOLID图标
            self.downButton = ArrowButton(FluentIcon.CARE_DOWN_SOLID, self)
            # 使用垂直布局排列按钮
            self.setLayout(QVBoxLayout(self))
            # 添加上箭头按钮，水平居中对齐
            self.layout().addWidget(self.upButton, 0, Qt.AlignHCenter)
            # 添加伸缩项，使上下按钮分别位于轨道两端
            self.layout().addStretch(1)
            # 添加下箭头按钮，水平居中对齐
            self.layout().addWidget(self.downButton, 0, Qt.AlignHCenter)
            # 设置布局内边距：上下3px，左右0px
            self.layout().setContentsMargins(0, 3, 0, 3)
        else:
            # 水平滚动条：固定高度12px
            self.setFixedHeight(12)
            # 创建左右箭头按钮（左箭头用CARE_LEFT_SOLID图标）
            self.upButton = ArrowButton(FluentIcon.CARE_LEFT_SOLID, self)
            # 右箭头用CARE_RIGHT_SOLID图标
            self.downButton = ArrowButton(FluentIcon.CARE_RIGHT_SOLID, self)
            # 使用水平布局排列按钮
            self.setLayout(QHBoxLayout(self))
            # 添加左箭头按钮，垂直居中对齐
            self.layout().addWidget(self.upButton, 0, Qt.AlignVCenter)
            # 添加伸缩项，使左右按钮分别位于轨道两端
            self.layout().addStretch(1)
            # 添加右箭头按钮，垂直居中对齐
            self.layout().addWidget(self.downButton, 0, Qt.AlignVCenter)
            # 设置布局内边距：左右3px，上下0px
            self.layout().setContentsMargins(3, 0, 3, 0)

        # 创建透明度动画对象（作用于opacity属性）
        self.opacityAni = QPropertyAnimation(self, b'opacity', self)
        # 初始设置透明度为0（隐藏状态）
        self.setOpacity(0)

    def setLightBackgroundColor(self, color):
        """设置浅色主题下的轨道背景色"""
        self.lightBackgroundColor = QColor(color)
        self.update()

    def setDarkBackgroundColor(self, color):
        """设置深色主题下的轨道背景色"""
        self.darkBackgroundColor = QColor(color)
        self.update()

    def fadeIn(self):
        """淡入动画：从当前透明度过渡到完全不透明（1），持续150ms"""
        self.opacityAni.stop()
        self.opacityAni.setStartValue(self.opacity)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.start()

    def fadeOut(self):
        """淡出动画：从当前透明度过渡到完全透明（0），持续150ms"""
        self.opacityAni.stop()
        self.opacityAni.setStartValue(self.opacity)
        self.opacityAni.setEndValue(0)
        self.opacityAni.setDuration(150)
        self.opacityAni.start()

    def paintEvent(self, e):
        """重写绘图事件，绘制轨道背景"""
        painter = QPainter(self)
        # 启用抗锯齿，使圆角边缘平滑
        painter.setRenderHints(QPainter.Antialiasing)
        # 设置轨道透明度
        painter.setOpacity(self.opacity)
        # 取消边框绘制
        painter.setPen(Qt.NoPen)

        # 根据主题选择背景色并绘制圆角矩形轨道
        painter.setBrush(self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor)
        painter.drawRoundedRect(self.rect(), 6, 6)  # 圆角半径6px

    def setOpacity(self, opacity: float):
        """设置轨道透明度，并同步更新箭头按钮透明度"""
        self._opacity = opacity
        self.upButton.setOpacity(opacity)
        self.downButton.setOpacity(opacity)
        self.update()

    def getOpacity(self) -> float:
        """获取当前轨道透明度"""
        return self._opacity

    # 将opacity定义为Qt属性，支持动画控制（通过pyqtProperty暴露get/set方法）
    opacity = pyqtProperty(float, getOpacity, setOpacity)


class ScrollBarHandle(QWidget):
    """ 
    滚动条滑块组件
    滚动条的可拖动滑块，支持透明度动画和主题颜色适配，根据滚动方向调整尺寸
    """

    def __init__(self, orient: Qt.Orientation, parent=None):
        super().__init__(parent)
        # 滑块透明度（0-1）
        self._opacity = 1
        # 创建透明度动画对象
        self.opacityAni = QPropertyAnimation(self, b'opacity', self)
        # 浅色主题下滑块颜色（黑色，透明度114/255）
        self.lightColor = QColor(0, 0, 0, 114)
        # 深色主题下滑块颜色（白色，透明度139/255）
        self.darkColor = QColor(255, 255, 255, 139)
        # 存储滚动方向（垂直/水平）
        self.orient = orient
        if orient == Qt.Vertical:
            # 垂直滑块：固定宽度3px
            self.setFixedWidth(3)
        else:
            # 水平滑块：固定高度3px
            self.setFixedHeight(3)

    def setLightColor(self, color):
        """设置浅色主题下的滑块颜色"""
        self.lightColor = QColor(color)
        self.update()

    def setDarkColor(self, color):
        """设置深色主题下的滑块颜色"""
        self.darkColor = QColor(color)
        self.update()

    def paintEvent(self, e):
        """重写绘图事件，绘制滑块"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)  # 取消边框

        # 根据滚动方向计算圆角半径（垂直滑块取宽度的一半，水平滑块取高度的一半）
        r = self.width() / 2 if self.orient == Qt.Vertical else self.height() / 2
        # 设置透明度和颜色
        painter.setOpacity(self.opacity)
        painter.setBrush(self.darkColor if isDarkTheme() else self.lightColor)
        # 绘制圆角矩形滑块
        painter.drawRoundedRect(self.rect(), r, r)

    def fadeIn(self):
        """淡入动画：从当前透明度过渡到1，持续150ms"""
        self.opacityAni.stop()
        self.opacityAni.setStartValue(self.opacity)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.start()

    def fadeOut(self):
        """淡出动画：从当前透明度过渡到0，持续150ms"""
        self.opacityAni.stop()
        self.opacityAni.setStartValue(self.opacity)
        self.opacityAni.setEndValue(0)
        self.opacityAni.setDuration(150)
        self.opacityAni.start()

    def setOpacity(self, opacity: float):
        """设置滑块透明度"""
        self._opacity = opacity
        self.update()

    def getOpacity(self) -> float:
        """获取当前滑块透明度"""
        return self._opacity

    # 将opacity定义为Qt属性，支持动画控制
    opacity = pyqtProperty(float, getOpacity, setOpacity)


class ScrollBarHandleDisplayMode(Enum):
    """
    滚动条滑块显示模式枚举
    
    枚举成员：
    - ALWAYS: 始终显示滑块
    - ON_HOVER: 仅当鼠标悬停在滚动条上时显示滑块
    """
    ALWAYS = 0
    ON_HOVER = 1


class ScrollBar(QWidget):
    """ 
    流畅滚动条组件（Fluent风格）
    自定义滚动条实现，支持垂直/水平方向，包含轨道、滑块和箭头按钮，
    提供丰富的动画效果和主题适配，可与QAbstractScrollArea组件集成
    
    信号：
    - rangeChanged: 滚动范围变化时触发，传递新范围元组(min, max)
    - valueChanged: 滚动值变化时触发，传递新值
    - sliderPressed: 滑块被按下时触发
    - sliderReleased: 滑块被释放时触发
    - sliderMoved: 滑块被拖动时触发
    """

    # 定义自定义信号（信号用于组件间通信）
    rangeChanged = pyqtSignal(tuple)  # 滚动范围变化信号
    valueChanged = pyqtSignal(int)    # 滚动值变化信号
    sliderPressed = pyqtSignal()      # 滑块按下信号
    sliderReleased = pyqtSignal()     # 滑块释放信号
    sliderMoved = pyqtSignal()        # 滑块拖动信号

    def __init__(self, orient: Qt.Orientation, parent: QAbstractScrollArea):
        super().__init__(parent)
        # 创建滚动条轨道组件（包含箭头按钮）
        self.groove = ScrollBarGroove(orient, self)
        # 创建滚动条滑块组件
        self.handle = ScrollBarHandle(orient, self)

        # 存储滚动方向（垂直/水平）
        self._orientation = orient
        # 单步滚动值（默认1）
        self._singleStep = 1
        # 页滚动值（默认50）
        self._pageStep = 50
        # 滑块与轨道边缘的内边距（默认14px）
        self._padding = 14

        # 滚动范围最小值（默认0）
        self._minimum = 0
        # 滚动范围最大值（默认0）
        self._maximum = 0
        # 当前滚动值（默认0）
        self._value = 0

        # 滑块按下状态（默认未按下）
        self._isPressed = False
        # 鼠标进入状态（默认未进入）
        self._isEnter = False
        # 轨道展开状态（默认未展开）
        self._isExpanded = False
        # 鼠标按下时的位置
        self._pressedPos = QPoint()
        # 是否强制隐藏（默认不隐藏）
        self._isForceHidden = False
        # 滑块显示模式（默认始终显示）
        self.handleDisplayMode = ScrollBarHandleDisplayMode.ALWAYS

        if orient == Qt.Vertical:
            # 垂直滚动条：关联父组件的垂直滚动条
            self.partnerBar = parent.verticalScrollBar()
            # 隐藏父组件默认的垂直滚动条
            QAbstractScrollArea.setVerticalScrollBarPolicy(parent, Qt.ScrollBarAlwaysOff)
        else:
            # 水平滚动条：关联父组件的水平滚动条
            self.partnerBar = parent.horizontalScrollBar()
            # 隐藏父组件默认的水平滚动条
            QAbstractScrollArea.setHorizontalScrollBarPolicy(parent, Qt.ScrollBarAlwaysOff)

        # 初始化组件
        self.__initWidget(parent)

    def __initWidget(self, parent):
        """初始化滚动条组件（内部辅助方法）"""
        # 绑定箭头按钮点击事件：上箭头->向上翻页，下箭头->向下翻页
        self.groove.upButton.clicked.connect(self._onPageUp)
        self.groove.downButton.clicked.connect(self._onPageDown)
        # 绑定轨道透明度动画值变化事件
        self.groove.opacityAni.valueChanged.connect(self._onOpacityAniValueChanged)

        # 绑定关联滚动条的信号：范围变化->更新当前滚动条范围，值变化->同步当前滚动值
        self.partnerBar.rangeChanged.connect(self.setRange)
        self.partnerBar.valueChanged.connect(self._onValueChanged)
        # 当前滚动条值变化时，同步到关联滚动条
        self.valueChanged.connect(self.partnerBar.setValue)

        # 为父组件安装事件过滤器（用于监听父组件大小变化等事件）
        parent.installEventFilter(self)

        # 初始化滚动范围（同步关联滚动条的范围）
        self.setRange(self.partnerBar.minimum(), self.partnerBar.maximum())
        # 根据最大范围和是否强制隐藏决定是否显示滚动条
        self.setVisible(self.maximum() > 0 and not self._isForceHidden)
        # 调整滚动条位置（根据父组件大小）
        self._adjustPos(self.parent().size())

    def _onPageUp(self):
        """向上翻页：滚动值 = 当前值 - 页滚动值"""
        self.setValue(self.value() - self.pageStep())

    def _onPageDown(self):
        """向下翻页：滚动值 = 当前值 + 页滚动值"""
        self.setValue(self.value() + self.pageStep())

    def _onValueChanged(self, value):
        """当关联滚动条值变化时，同步更新当前滚动条值"""
        self.val = value

    def value(self):
        """获取当前滚动值"""
        return self._value

    # 将val定义为Qt属性，支持通过属性访问滚动值，并在变化时触发valueChanged信号
    @pyqtProperty(int, notify=valueChanged)
    def val(self):
        return self._value

    @val.setter
    def val(self, value: int):
        """设置滚动值（带范围校验）"""
        if value == self.value():
            return  # 值未变化则不处理

        # 确保值在[min, max]范围内
        value = max(self.minimum(), min(value, self.maximum()))
        self._value = value
        # 发送值变化信号
        self.valueChanged.emit(value)

        # 调整滑块位置
        self._adjustHandlePos()

    def minimum(self):
        """获取滚动范围最小值"""
        return self._minimum

    def maximum(self):
        """获取滚动范围最大值"""
        return self._maximum

    def orientation(self):
        """获取滚动方向"""
        return self._orientation

    def pageStep(self):
        """获取页滚动值"""
        return self._pageStep

    def singleStep(self):
        """获取单步滚动值"""
        return self._singleStep

    def isSliderDown(self):
        """判断滑块是否处于按下状态"""
        return self._isPressed

    def setValue(self, value: int):
        """设置滚动值（对外接口）"""
        self.val = value

    def setMinimum(self, min: int):
        """设置滚动范围最小值"""
        if min == self.minimum():
            return  # 值未变化则不处理

        self._minimum = min
        # 发送范围变化信号
        self.rangeChanged.emit((min, self.maximum()))

    def setMaximum(self, max: int):
        """设置滚动范围最大值"""
        if max == self.maximum():
            return  # 值未变化则不处理

        self._maximum = max
        # 发送范围变化信号
        self.rangeChanged.emit((self.minimum(), max))

    def setRange(self, min: int, max: int):
        """设置滚动范围（最小值和最大值）"""
        if min > max or (min == self.minimum() and max == self.maximum()):
            return  # 无效范围或范围未变化则不处理

        self.setMinimum(min)
        self.setMaximum(max)

        # 调整滑块大小和位置
        self._adjustHandleSize()
        self._adjustHandlePos()
        # 根据最大范围和是否强制隐藏决定是否显示滚动条
        self.setVisible(max > 0 and not self._isForceHidden)

        # 发送范围变化信号
        self.rangeChanged.emit((min, max))

    def setPageStep(self, step: int):
        """设置页滚动值（step >= 1才生效）"""
        if step >= 1:
            self._pageStep = step

    def setSingleStep(self, step: int):
        """设置单步滚动值（step >= 1才生效）"""
        if step >= 1:
            self._singleStep = step

    def setSliderDown(self, isDown: bool):
        """设置滑块按下状态"""
        self._isPressed = True
        if isDown:
            self.sliderPressed.emit()  # 发送滑块按下信号
        else:
            self.sliderReleased.emit()  # 发送滑块释放信号

    def setHandleColor(self, light, dark):
        """
        设置滑块颜色
        
        参数：
            light: 浅色主题下的颜色（QColor/str/Qt.GlobalColor）
            dark: 深色主题下的颜色（QColor/str/Qt.GlobalColor）
        """
        self.handle.setLightColor(light)
        self.handle.setDarkColor(dark)

    def setArrowColor(self, light, dark):
        """
        设置箭头按钮颜色
        
        参数：
            light: 浅色主题下的颜色
            dark: 深色主题下的颜色
        """
        self.groove.upButton.setLightColor(light)
        self.groove.upButton.setDarkColor(dark)
        self.groove.downButton.setLightColor(light)
        self.groove.downButton.setDarkColor(dark)

    def setGrooveColor(self, light, dark):
        """
        设置轨道颜色
        
        参数：
            light: 浅色主题下的颜色
            dark: 深色主题下的颜色
        """
        self.groove.setLightBackgroundColor(light)
        self.groove.setDarkBackgroundColor(dark)

    def setHandleDisplayMode(self, mode: ScrollBarHandleDisplayMode):
        """
        设置滑块显示模式
        
        参数：
            mode: ScrollBarHandleDisplayMode枚举值（ALWAYS/ON_HOVER）
        """
        if mode == self.handleDisplayMode:
            return  # 模式未变化则不处理

        self.handleDisplayMode = mode
        # 若模式为ON_HOVER且鼠标未进入，则隐藏滑块
        if mode == ScrollBarHandleDisplayMode.ON_HOVER and not self._isEnter:
            self.handle.fadeOut()
        # 若模式为ALWAYS，则显示滑块
        elif mode == ScrollBarHandleDisplayMode.ALWAYS:
            self.handle.fadeIn()

    def expand(self):
        """展开轨道：显示轨道和滑块（淡入动画）"""
        if self._isExpanded or not self._isEnter:
            return  # 已展开或鼠标未进入则不处理

        self._isExpanded = True
        self.groove.fadeIn()
        self.handle.fadeIn()

    def collapse(self):
        """折叠轨道：隐藏轨道和滑块（淡出动画）"""
        if not self._isExpanded or self._isEnter:
            return  # 未展开或鼠标已进入则不处理

        self._isExpanded = False
        self.groove.fadeOut()

        # 若滑块显示模式为ON_HOVER，则隐藏滑块
        if self.handleDisplayMode == ScrollBarHandleDisplayMode.ON_HOVER:
            self.handle.fadeOut()

    def enterEvent(self, e):
        """鼠标进入事件：标记进入状态，并延迟200ms展开轨道"""
        self._isEnter = True
        QTimer.singleShot(200, self.expand)

    def leaveEvent(self, e):
        """鼠标离开事件：标记离开状态，并延迟200ms折叠轨道"""
        self._isEnter = False
        QTimer.singleShot(200, self.collapse)

    def eventFilter(self, obj, e: QEvent):
        """事件过滤器：监听父组件事件"""
        if obj is not self.parent():
            return super().eventFilter(obj, e)

        # 当父组件大小变化时，调整滚动条位置
        if e.type() == QEvent.Resize:
            self._adjustPos(e.size())

        return super().eventFilter(obj, e)

    def resizeEvent(self, e):
        """滚动条大小变化事件：调整轨道大小与滚动条一致"""
        self.groove.resize(self.size())

    def mousePressEvent(self, e: QMouseEvent):
        """鼠标按下事件：处理滑块拖动和轨道点击"""
        super().mousePressEvent(e)
        self._isPressed = True
        self._pressedPos = e.pos()

        # 若点击位置是滑块或不在轨道区域，则不处理轨道点击逻辑
        if self.childAt(e.pos()) is self.handle or not self._isSlideResion(e.pos()):
            return

        if self.orientation() == Qt.Vertical:
            # 垂直滚动条：根据点击位置计算滚动值
            if e.pos().y() > self.handle.geometry().bottom():
                # 点击位置在滑块下方：值 = 点击y坐标 - 滑块高度 - 内边距
                value = e.pos().y() - self.handle.height() - self._padding
            else:
                # 点击位置在滑块上方：值 = 点击y坐标 - 内边距
                value = e.pos().y() - self._padding
        else:
            # 水平滚动条：根据点击位置计算滚动值
            if e.pos().x() > self.handle.geometry().right():
                # 点击位置在滑块右侧：值 = 点击x坐标 - 滑块宽度 - 内边距
                value = e.pos().x() - self.handle.width() - self._padding
            else:
                # 点击位置在滑块左侧：值 = 点击x坐标 - 内边距
                value = e.pos().x() - self._padding

        # 根据点击位置比例计算滚动值（值 = 点击位置比例 * 最大范围）
        self.setValue(int(value / max(self._slideLength(), 1) * self.maximum()))
        # 发送滑块按下信号
        self.sliderPressed.emit()

    def mouseReleaseEvent(self, e):
        """鼠标释放事件：标记滑块释放状态，并发送释放信号"""
        super().mouseReleaseEvent(e)
        self._isPressed = False
        self.sliderReleased.emit()

    def mouseMoveEvent(self, e: QMouseEvent):
        """鼠标移动事件：处理滑块拖动"""
        if self.orientation() == Qt.Vertical:
            # 垂直方向：计算y方向移动距离
            dv = e.pos().y() - self._pressedPos.y()
        else:
            # 水平方向：计算x方向移动距离
            dv = e.pos().x() - self._pressedPos.x()

        # 根据移动距离和轨道长度计算滚动值变化量（dv = 移动距离比例 * 滚动范围）
        dv = int(dv / max(self._slideLength(), 1) * (self.maximum() - self.minimum()))
        # 更新滚动值（直接调用ScrollBar.setValue避免子类重写影响）
        ScrollBar.setValue(self, self.value() + dv)

        # 更新按下位置为当前位置
        self._pressedPos = e.pos()
        # 发送滑块拖动信号
        self.sliderMoved.emit()

    def _adjustPos(self, size):
        """调整滚动条在父组件中的位置"""
        if self.orientation() == Qt.Vertical:
            # 垂直滚动条：宽度12px，高度=父组件高度-2px，位置=父组件右侧-13px，顶部1px
            self.resize(12, size.height() - 2)
            self.move(size.width() - 13, 1)
        else:
            # 水平滚动条：高度12px，宽度=父组件宽度-2px，位置=父组件底部-13px，左侧1px
            self.resize(size.width() - 2, 12)
            self.move(1, size.height() - 13)

    def _adjustHandleSize(self):
        """调整滑块大小（根据父组件内容区域大小和滚动范围）"""
        p = self.parent()
        if self.orientation() == Qt.Vertical:
            # 垂直滑块：总长度 = 滚动范围 + 父组件高度（可视区域）
            total = self.maximum() - self.minimum() + p.height()
            # 滑块高度 = 轨道长度 * 父组件高度 / 总长度（最小30px）
            s = int(self._grooveLength() * p.height() / max(total, 1))
            self.handle.setFixedHeight(max(30, s))
        else:
            # 水平滑块：总长度 = 滚动范围 + 父组件宽度（可视区域）
            total = self.maximum() - self.minimum() + p.width()
            # 滑块宽度 = 轨道长度 * 父组件宽度 / 总长度（最小30px）
            s = int(self._grooveLength() * p.width() / max(total, 1))
            self.handle.setFixedWidth(max(30, s))

    def _adjustHandlePos(self):
        """调整滑块位置（根据当前滚动值）"""
        total = max(self.maximum() - self.minimum(), 1)  # 滚动范围（避免除零）
        # 滑块偏移量 = 滚动值比例 * 轨道可用长度（轨道长度 - 滑块长度）
        delta = int(self.value() / total * self._slideLength())

        if self.orientation() == Qt.Vertical:
            # 垂直滑块：x = 滚动条宽度 - 滑块宽度 - 3px（居中），y = 内边距 + 偏移量
            x = self.width() - self.handle.width() - 3
            self.handle.move(x, self._padding + delta)
        else:
            # 水平滑块：y = 滚动条高度 - 滑块高度 - 3px（居中），x = 内边距 + 偏移量
            y = self.height() - self.handle.height() - 3
            self.handle.move(self._padding + delta, y)

    def _grooveLength(self):
        """计算轨道可用长度（轨道总长度 - 2 * 内边距）"""
        if self.orientation() == Qt.Vertical:
            return self.height() - 2 * self._padding
        return self.width() - 2 * self._padding

    def _slideLength(self):
        """计算滑块可滑动长度（轨道可用长度 - 滑块长度）"""
        if self.orientation() == Qt.Vertical:
            return self._grooveLength() - self.handle.height()
        return self._grooveLength() - self.handle.width()

    def _isSlideResion(self, pos: QPoint):
        """判断坐标是否在滑块可滑动区域内（轨道内边距之间的区域）"""
        if self.orientation() == Qt.Vertical:
            return self._padding <= pos.y() <= self.height() - self._padding
        return self._padding <= pos.x() <= self.width() - self._padding

    def _onOpacityAniValueChanged(self):
        """轨道透明度动画值变化事件：同步调整滑块尺寸（随透明度增加而变宽/高）"""
        opacity = self.groove.opacity
        if self.orientation() == Qt.Vertical:
            # 垂直滑块：宽度 = 3px + 透明度 * 3px（最大6px）
            self.handle.setFixedWidth(int(3 + opacity * 3))
        else:
            # 水平滑块：高度 = 3px + 透明度 * 3px（最大6px）
            self.handle.setFixedHeight(int(3 + opacity * 3))

        # 调整滑块位置（因尺寸变化）
        self._adjustHandlePos()

    def setForceHidden(self, isHidden: bool):
        """设置是否强制隐藏滚动条"""
        self._isForceHidden = isHidden
        # 根据最大范围和强制隐藏状态决定可见性
        self.setVisible(self.maximum() > 0 and not isHidden)

    def wheelEvent(self, e):
        """鼠标滚轮事件：将滚轮事件转发给父组件视口（由父组件处理滚动）"""
        QApplication.sendEvent(self.parent().viewport(), e)


class SmoothScrollBar(ScrollBar):
    """ 
    平滑滚动条组件
    继承自ScrollBar，增加平滑滚动动画效果，支持通过属性动画实现滚动值的平滑过渡
    """

    def __init__(self, orient: Qt.Orientation, parent):
        super().__init__(orient, parent)
        # 平滑滚动动画持续时间（默认500ms）
        self.duration = 500
        # 创建属性动画对象（作用于val属性）
        self.ani = QPropertyAnimation()
        self.ani.setTargetObject(self)
        self.ani.setPropertyName(b"val")
        # 设置动画缓动曲线（OutCubic：先快后慢）
        self.ani.setEasingCurve(QEasingCurve.OutCubic)
        self.ani.setDuration(self.duration)

        # 存储平滑滚动的目标值
        self.__value = self.value()

    def setValue(self, value, useAni=True):
        """设置滚动值（支持平滑动画）"""
        if value == self.value():
            return  # 值未变化则不处理

        # 停止当前动画
        self.ani.stop()

        if not useAni:
            # 不使用动画：直接设置值
            self.val = value
            return

        # 根据滚动距离调整动画持续时间（距离越小，时间越短）
        dv = abs(value - self.value())
        if dv < 50:
            self.ani.setDuration(int(self.duration * dv / 70))
        else:
            self.ani.setDuration(self.duration)

        # 设置动画起始值和结束值并启动
        self.ani.setStartValue(self.value())
        self.ani.setEndValue(value)
        self.ani.start()

    def scrollValue(self, value, useAni=True):
        """滚动指定距离（相对值）"""
        self.__value += value
        # 限制在滚动范围内
        self.__value = max(self.minimum(), self.__value)
        self.__value = min(self.maximum(), self.__value)
        self.setValue(self.__value, useAni)

    def scrollTo(self, value, useAni=True):
        """滚动到指定位置（绝对值）"""
        self.__value = value
        # 限制在滚动范围内
        self.__value = max(self.minimum(), self.__value)
        self.__value = min(self.maximum(), self.__value)
        self.setValue(self.__value, useAni)

    def resetValue(self, value):
        """重置滚动目标值（不触发动画）"""
        self.__value = value

    def mousePressEvent(self, e):
        """鼠标按下事件：停止动画并记录当前值"""
        self.ani.stop()
        super().mousePressEvent(e)
        self.__value = self.value()

    def mouseMoveEvent(self, e):
        """鼠标拖动事件：停止动画并记录当前值"""
        self.ani.stop()
        super().mouseMoveEvent(e)
        self.__value = self.value()

    def setScrollAnimation(self, duration, easing=QEasingCurve.OutCubic):
        """
        设置平滑滚动动画参数
        
        参数：
            duration: int - 动画持续时间（毫秒）
            easing: QEasingCurve - 动画缓动曲线类型
        """
        self.duration = duration
        self.ani.setDuration(duration)
        self.ani.setEasingCurve(easing)


class SmoothScrollDelegate(QObject):
    """ 
    平滑滚动代理组件
    为QAbstractScrollArea及其子类（如QListWidget、QTableWidget）提供平滑滚动功能，
    集成垂直和水平平滑滚动条，并处理鼠标滚轮事件
    """

    def __init__(self, parent: QAbstractScrollArea, useAni=False):
        """
        构造方法
        
        参数：
            parent: QAbstractScrollArea - 被代理的滚动区域组件
            useAni: bool - 是否使用属性动画实现平滑滚动（默认不使用）
        """
        super().__init__(parent)
        self.useAni = useAni
        # 创建垂直平滑滚动条
        self.vScrollBar = SmoothScrollBar(Qt.Vertical, parent)
        # 创建水平平滑滚动条
        self.hScrollBar = SmoothScrollBar(Qt.Horizontal, parent)
        # 创建垂直平滑滚动工具（非动画方式）
        self.verticalSmoothScroll = SmoothScroll(parent, Qt.Vertical)
        # 创建水平平滑滚动工具（非动画方式）
        self.horizonSmoothScroll = SmoothScroll(parent, Qt.Horizontal)

        # 若父组件是项视图（如QListView、QTableView），设置为像素级滚动
        if isinstance(parent, QAbstractItemView):
            parent.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            parent.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        # 若父组件是QListView，强制显示水平滚动条并隐藏原生样式
        if isinstance(parent, QListView):
            parent.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            parent.horizontalScrollBar().setStyleSheet("QScrollBar:horizontal{height: 0px}")

        # 为父组件视口安装事件过滤器（处理滚轮事件）
        parent.viewport().installEventFilter(self)
        # 重写父组件的滚动条策略设置方法（确保原生滚动条始终隐藏）
        parent.setVerticalScrollBarPolicy = self.setVerticalScrollBarPolicy
        parent.setHorizontalScrollBarPolicy = self.setHorizontalScrollBarPolicy

    def eventFilter(self, obj, e: QEvent):
        """事件过滤器：处理鼠标滚轮事件"""
        if e.type() == QEvent.Type.Wheel:
            # 判断垂直滚动是否到达边界
            verticalAtEnd = (e.angleDelta().y() < 0 and self.vScrollBar.value() == self.vScrollBar.maximum()) or \
                            (e.angleDelta().y() > 0 and self.vScrollBar.value() == self.vScrollBar.minimum())

            # 判断水平滚动是否到达边界
            horizontalAtEnd = (e.angleDelta().x() < 0 and self.hScrollBar.value() == self.hScrollBar.maximum()) or \
                              (e.angleDelta().x() > 0 and self.hScrollBar.value() == self.hScrollBar.minimum())

            # 若任一方向到达边界，则不拦截事件（允许父组件处理）
            if verticalAtEnd or horizontalAtEnd:
                return False

            if e.angleDelta().y() != 0:
                # 垂直滚轮事件
                if not self.useAni:
                    # 非动画方式：使用平滑滚动工具
                    self.verticalSmoothScroll.wheelEvent(e)
                else:
                    # 动画方式：调用平滑滚动条的scrollValue方法
                    self.vScrollBar.scrollValue(-e.angleDelta().y())
            else:
                # 水平滚轮事件
                if not self.useAni:
                    # 非动画方式：使用平滑滚动工具
                    self.horizonSmoothScroll.wheelEvent(e)
                else:
                    # 动画方式：调用平滑滚动条的scrollValue方法
                    self.hScrollBar.scrollValue(-e.angleDelta().x())

            # 标记事件已处理
            e.setAccepted(True)
            return True

        return super().eventFilter(obj, e)

    def setVerticalScrollBarPolicy(self, policy):
        """重写垂直滚动条策略设置：始终隐藏原生滚动条"""
        QAbstractScrollArea.setVerticalScrollBarPolicy(self.parent(), Qt.ScrollBarAlwaysOff)
        # 根据策略决定是否强制隐藏自定义滚动条
        self.vScrollBar.setForceHidden(policy == Qt.ScrollBarAlwaysOff)

    def setHorizontalScrollBarPolicy(self, policy):
        """重写水平滚动条策略设置：始终隐藏原生滚动条"""
        QAbstractScrollArea.setHorizontalScrollBarPolicy(self.parent(), Qt.ScrollBarAlwaysOff)
        # 根据策略决定是否强制隐藏自定义滚动条
        self.hScrollBar.setForceHidden(policy == Qt.ScrollBarAlwaysOff)

