from typing import Union

from PyQt5.QtCore import pyqtSignal, QUrl, Qt, QRectF, QSize, QPoint, pyqtProperty, QRect
from PyQt5.QtGui import QDesktopServices, QIcon, QPainter, QColor, QPainterPath
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QRadioButton, QToolButton, QApplication, QWidget, QSizePolicy

from ...common.animation import TranslateYAnimation
from ...common.icon import FluentIconBase, drawIcon, isDarkTheme, Theme, toQIcon, Icon
from ...common.icon import FluentIcon as FIF
from ...common.font import setFont, getFont
from ...common.style_sheet import FluentStyleSheet, themeColor, ThemeColor
from ...common.color import autoFallbackThemeColor
from ...common.overload import singledispatchmethod


from .menu import RoundMenu, MenuAnimationType


class PushButton(QPushButton):
    """ 基础按钮类"""

    @singledispatchmethod  # 用于支持函数重载的装饰器
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)  # 调用父类QPushButton的构造函数
        FluentStyleSheet.BUTTON.apply(self)  # 应用Fluent风格样式表
        self.isPressed = False  # 标记按钮是否被按下
        self.isHover = False  # 标记鼠标是否悬停在按钮上
        self.setIconSize(QSize(16, 16))  # 设置图标尺寸为16x16像素
        self.setIcon(None)  # 初始设置为无图标
        setFont(self)  # 设置按钮字体
        self._postInit()  # 调用子类可能重写的初始化后方法

    @__init__.register  # 注册带文本和可选图标的构造函数
    def _(self, text: str, parent: QWidget = None, icon: Union[QIcon, str, FluentIconBase] = None):
        self.__init__(parent=parent)  # 调用无参构造函数
        self.setText(text)  # 设置按钮文本
        self.setIcon(icon)  # 设置按钮图标

    @__init__.register  # 注册带图标和文本的构造函数
    def _(self, icon: QIcon, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)  # 调用带文本的构造函数

    @__init__.register  # 注册带Fluent图标和文本的构造函数
    def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)  # 调用带文本的构造函数

    def _postInit(self):
        """ 初始化后钩子方法，供子类重写 """
        pass

    def setIcon(self, icon: Union[QIcon, str, FluentIconBase]):
        """ 设置按钮图标
        icon: 可以是QIcon对象、图标路径字符串或FluentIconBase对象
        """
        self.setProperty('hasIcon', icon is not None)  # 设置hasIcon属性，用于样式表
        self.setStyle(QApplication.style())  # 重新设置样式
        self._icon = icon or QIcon()  # 存储图标，如果为None则使用空QIcon
        self.update()  # 触发重绘

    def icon(self):
        """ 获取按钮图标（转换为QIcon类型） """
        return toQIcon(self._icon)  # 将存储的图标转换为QIcon返回

    def setProperty(self, name: str, value) -> bool:
        """ 重写setProperty方法，处理icon属性的特殊情况 """
        if name != 'icon':  # 如果不是icon属性，调用父类方法
            return super().setProperty(name, value)

        self.setIcon(value)  # 是icon属性时调用自定义的setIcon方法
        return True

    def mousePressEvent(self, e):
        """ 处理鼠标按下事件，设置isPressed标记 """
        self.isPressed = True  # 标记按钮被按下
        super().mousePressEvent(e)  # 调用父类方法处理事件

    def mouseReleaseEvent(self, e):
        """ 处理鼠标释放事件，重置isPressed标记 """
        self.isPressed = False  # 标记按钮未被按下
        super().mouseReleaseEvent(e)  # 调用父类方法处理事件

    def enterEvent(self, e):
        """ 处理鼠标进入事件，设置isHover标记并触发重绘 """
        self.isHover = True  # 标记鼠标悬停
        self.update()  # 触发重绘以显示悬停效果

    def leaveEvent(self, e):
        """ 处理鼠标离开事件，重置isHover标记并触发重绘 """
        self.isHover = False  # 标记鼠标未悬停
        self.update()  # 触发重绘以恢复默认效果

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """ 绘制图标的内部方法
        icon: 要绘制的图标
        painter: QPainter绘图对象
        rect: 绘制区域
        state: 图标状态（默认为QIcon.Off）
        """
        drawIcon(icon, painter, rect, state)  # 调用通用的图标绘制函数

    def paintEvent(self, e):
        """ 处理重绘事件，绘制按钮和图标 """
        super().paintEvent(e)  # 调用父类方法处理基本绘制
        if self.icon().isNull():  # 如果没有图标，直接返回
            return

        painter = QPainter(self)  # 创建绘图对象
        painter.setRenderHints(QPainter.Antialiasing |  # 设置抗锯齿
                               QPainter.SmoothPixmapTransform)  # 设置平滑像素变换

        if not self.isEnabled():  # 如果按钮被禁用，设置透明度
            painter.setOpacity(0.3628)
        elif self.isPressed:  # 如果按钮被按下，设置不同的透明度
            painter.setOpacity(0.786)

        w, h = self.iconSize().width(), self.iconSize().height()  # 获取图标尺寸
        y = (self.height() - h) / 2  # 计算图标垂直居中位置
        mw = self.minimumSizeHint().width()  # 获取最小尺寸提示的宽度
        if mw > 0:  # 如果有最小宽度
            x = 12 + (self.width() - mw) // 2  # 计算图标水平位置
        else:
            x = 12  # 默认水平位置

        if self.isRightToLeft():  # 如果是从右到左的布局
            x = self.width() - w - x  # 调整图标水平位置

        self._drawIcon(self._icon, painter, QRectF(x, y, w, h))  # 绘制图标


class PrimaryPushButton(PushButton):
    """ 主色调按钮

    构造函数
    ------------
    * PrimaryPushButton(`parent`: QWidget = None) - 创建一个无文本无图标的主色调按钮
    * PrimaryPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None) - 创建带文本和可选图标的主色调按钮
    * PrimaryPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None) - 创建带图标和文本的主色调按钮
    """

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """ 重绘图标方法，为主色调按钮提供特殊的图标绘制逻辑
        当图标是FluentIconBase类型且按钮可用时，反转图标颜色以适应主色调背景
        """
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            # 反转图标颜色以适应主色调背景
            theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
            icon = icon.icon(theme)
        elif not self.isEnabled():
            painter.setOpacity(0.786 if isDarkTheme() else 0.9)
            if isinstance(icon, FluentIconBase):
                icon = icon.icon(Theme.DARK)

        PushButton._drawIcon(self, icon, painter, rect, state)  # 调用父类方法绘制图标


class TransparentPushButton(PushButton):
    """ 透明背景按钮

    构造函数
    ------------
    * TransparentPushButton(`parent`: QWidget = None) - 创建一个无文本无图标的透明按钮
    * TransparentPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None) - 创建带文本和可选图标的透明按钮
    * TransparentPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None) - 创建带图标和文本的透明按钮
    """


class ToggleButton(PushButton):
    """ 切换按钮（可选中状态）

    构造函数
    ------------
    * ToggleButton(`parent`: QWidget = None) - 创建一个无文本无图标的切换按钮
    * ToggleButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None) - 创建带文本和可选图标的切换按钮
    * ToggleButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None) - 创建带图标和文本的切换按钮
    """

    def _postInit(self):
        """ 初始化后设置按钮为可选中状态 """
        self.setCheckable(True)  # 设置按钮可选中
        self.setChecked(False)  # 初始设置为未选中状态

    def _drawIcon(self, icon, painter, rect):
        """ 重绘图标方法，根据按钮选中状态绘制不同样式的图标
        如果未选中，使用普通按钮样式；如果选中，使用主色调按钮样式
        """
        if not self.isChecked():
            return PushButton._drawIcon(self, icon, painter, rect)  # 未选中时使用普通样式

        PrimaryPushButton._drawIcon(self, icon, painter, rect, QIcon.On)  # 选中时使用主色调样式


TogglePushButton = ToggleButton  # 别名定义


class TransparentTogglePushButton(TogglePushButton):
    """ 透明背景切换按钮

    构造函数
    ------------
    * TransparentTogglePushButton(`parent`: QWidget = None) - 创建一个无文本无图标的透明切换按钮
    * TransparentTogglePushButton(`text`: str, `parent`: QWidget = None,
                                  `icon`: QIcon | str | FluentIconBase = None) - 创建带文本和可选图标的透明切换按钮
    * TransparentTogglePushButton(`icon`: QIcon | FluentIconBase, `text`: str, `parent`: QWidget = None) - 创建带图标和文本的透明切换按钮
    """


class HyperlinkButton(PushButton):
    """ 超链接按钮

    构造函数
    ------------
    * HyperlinkButton(`parent`: QWidget = None) - 创建一个无文本无图标的超链接按钮
    * HyperlinkButton(`url`: str, `text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None) - 创建带URL、文本和可选图标的超链接按钮
    * HyperlinkButton(`icon`: QIcon | FluentIconBase, `url`: str, `text`: str, `parent`: QWidget = None) - 创建带图标、URL和文本的超链接按钮
    """

    @singledispatchmethod  # 用于支持函数重载的装饰器
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)  # 调用父类PushButton的构造函数
        self._url = QUrl()  # 初始化URL属性
        FluentStyleSheet.BUTTON.apply(self)  # 应用Fluent风格样式表
        self.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时显示手型光标
        setFont(self)  # 设置按钮字体
        self.clicked.connect(self._onClicked)  # 连接点击信号到槽函数

    @__init__.register  # 注册带URL、文本和可选图标的构造函数
    def _(self, url: str, text: str, parent: QWidget = None, icon: Union[QIcon, FluentIconBase, str] = None):
        self.__init__(parent)  # 调用无参构造函数
        self.setText(text)  # 设置按钮文本
        self.url.setUrl(url)  # 设置按钮URL
        self.setIcon(icon)  # 设置按钮图标

    @__init__.register  # 注册带图标、URL和文本的构造函数
    def _(self, icon: QIcon, url: str, text: str, parent: QWidget = None):
        self.__init__(url, text, parent, icon)  # 调用带URL的构造函数

    @__init__.register  # 注册带Fluent图标、URL和文本的构造函数
    def _(self, icon: FluentIconBase, url: str, text: str, parent: QWidget = None):
        self.__init__(url, text, parent, icon)  # 调用带URL的构造函数

    def getUrl(self):
        """ 获取按钮的URL """
        return self._url  # 返回URL属性

    def setUrl(self, url: Union[str, QUrl]):
        """ 设置按钮的URL
        url: 可以是字符串或QUrl对象
        """
        self._url = QUrl(url)  # 将URL转换为QUrl对象并存储

    def _onClicked(self):
        """ 处理按钮点击事件，打开链接 """
        if self.getUrl().isValid():  # 检查URL是否有效
            QDesktopServices.openUrl(self.getUrl())  # 打开URL

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """ 重绘图标方法，为超链接按钮提供特殊的图标绘制逻辑
        当图标是FluentIconBase类型且按钮可用时，使用主题色绘制图标
        """
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            icon = icon.icon(color=themeColor())  # 使用主题色绘制图标
        elif not self.isEnabled():
            painter.setOpacity(0.3628 if isDarkTheme() else 0.36)  # 设置透明度

        drawIcon(icon, painter, rect, state)  # 调用通用的图标绘制函数

    url = pyqtProperty(QUrl, getUrl, setUrl)  # 定义Qt属性，允许在Qt设计器中编辑URL


class RadioButton(QRadioButton):
    """ 单选按钮

    构造函数
    ------------
    * RadioButton(`parent`: QWidget = None) - 创建一个无文本的单选按钮
    * RadioButton(`url`: text, `text`: str, `parent`: QWidget = None,
                  `icon`: QIcon | str | FluentIconBase = None) - 创建带文本的单选按钮
    """

    @singledispatchmethod  # 用于支持函数重载的装饰器
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)  # 调用父类QRadioButton的构造函数
        self._lightTextColor = QColor(0, 0, 0)  # 浅色主题下的文本颜色
        self._darkTextColor = QColor(255, 255, 255)  # 深色主题下的文本颜色
        self.lightIndicatorColor = QColor()  # 浅色主题下的指示器颜色
        self.darkIndicatorColor = QColor()  # 深色主题下的指示器颜色
        self.indicatorPos = QPoint(11, 12)  # 指示器位置
        self.isHover = False  # 标记鼠标是否悬停

        FluentStyleSheet.BUTTON.apply(self)  # 应用Fluent风格样式表
        self.setAttribute(Qt.WA_MacShowFocusRect, False)  # 禁用Mac焦点矩形
        self._postInit()  # 调用子类可能重写的初始化后方法

    @__init__.register  # 注册带文本的构造函数
    def _(self, text: str, parent: QWidget = None):
        self.__init__(parent)  # 调用无参构造函数
        self.setText(text)  # 设置按钮文本

    def _postInit(self):
        """ 初始化后钩子方法，供子类重写 """
        pass

    def enterEvent(self, e):
        """ 处理鼠标进入事件，设置isHover标记并触发重绘 """
        self.isHover = True  # 标记鼠标悬停
        self.update()  # 触发重绘以显示悬停效果

    def leaveEvent(self, e):
        """ 处理鼠标离开事件，重置isHover标记并触发重绘 """
        self.isHover = False  # 标记鼠标未悬停
        self.update()  # 触发重绘以恢复默认效果

    def paintEvent(self, e):
        """ 处理重绘事件，绘制单选按钮指示器和文本 """
        painter = QPainter(self)  # 创建绘图对象
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)  # 设置抗锯齿
        self._drawIndicator(painter)  # 绘制指示器
        self._drawText(painter)  # 绘制文本

    def _drawText(self, painter: QPainter):
        """ 绘制按钮文本
        painter: QPainter绘图对象
        """
        if not self.isEnabled():  # 如果按钮被禁用，设置透明度
            painter.setOpacity(0.36)

        painter.setFont(self.font())  # 设置字体
        painter.setPen(self.textColor())  # 设置文本颜色
        # 绘制文本，左对齐，垂直居中
        painter.drawText(QRect(29, 0, self.width(), self.height()), Qt.AlignVCenter, self.text())

    def _drawIndicator(self, painter: QPainter):
        """ 绘制单选按钮指示器（圆形部分）
        painter: QPainter绘图对象
        根据按钮状态（选中/未选中、悬停/未悬停、按下/未按下、启用/禁用）绘制不同样式的指示器
        """
        if self.isChecked():  # 如果按钮被选中
            if self.isEnabled():  # 如果按钮可用
                # 获取指示器边框颜色，自动适应主题
                borderColor = autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor)
            else:  # 如果按钮不可用
                # 设置不可用状态下的边框颜色
                borderColor = QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 55)

            # 设置填充颜色
            filledColor = Qt.black if isDarkTheme() else Qt.white

            # 根据是否悬停和按下状态绘制不同大小的指示器
            if self.isHover and not self.isDown():
                self._drawCircle(painter, self.indicatorPos, 10, 4, borderColor, filledColor)
            else:
                self._drawCircle(painter, self.indicatorPos, 10, 5, borderColor, filledColor)

        else:  # 如果按钮未被选中
            if self.isEnabled():  # 如果按钮可用
                if not self.isDown():  # 如果按钮未被按下
                    # 设置未按下状态的边框颜色
                    borderColor = QColor(255, 255, 255, 153) if isDarkTheme() else QColor(0, 0, 0, 153)
                else:  # 如果按钮被按下
                    # 设置按下状态的边框颜色
                    borderColor = QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 55)

                if self.isDown():  # 如果按钮被按下
                    # 设置按下状态的填充颜色
                    filledColor = Qt.black if isDarkTheme() else Qt.white
                elif self.isHover:  # 如果鼠标悬停
                    # 设置悬停状态的填充颜色
                    filledColor = QColor(255, 255, 255, 11) if isDarkTheme() else QColor(0, 0, 0, 15)
                else:  # 默认状态
                    # 设置默认状态的填充颜色
                    filledColor = QColor(0, 0, 0, 26) if isDarkTheme() else QColor(0, 0, 0, 6)
            else:  # 如果按钮不可用
                # 设置不可用状态的颜色
                filledColor = Qt.transparent
                borderColor = QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 55)

            # 绘制未选中状态的圆形指示器
            self._drawCircle(painter, self.indicatorPos, 10, 1, borderColor, filledColor)

            # 如果按钮可用且被按下，额外绘制一个内环
            if self.isEnabled() and self.isDown():
                borderColor = QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 24)
                self._drawCircle(painter, self.indicatorPos, 9, 4, borderColor, Qt.transparent)

    def _drawCircle(self, painter: QPainter, center: QPoint, radius, thickness, borderColor, filledColor):
        """ 绘制圆形的辅助方法
        painter: QPainter绘图对象
        center: 圆心坐标
        radius: 圆的半径
        thickness: 边框厚度
        borderColor: 边框颜色
        filledColor: 填充颜色
        """
        path = QPainterPath()  # 创建绘制路径
        path.setFillRule(Qt.FillRule.WindingFill)  # 设置填充规则

        # 绘制外圆（边框）
        outerRect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        path.addEllipse(outerRect)  # 添加椭圆到路径

        # 绘制内部中心（填充区域）
        ir = radius - thickness  # 内圆半径
        innerRect = QRectF(center.x() - ir, center.y() - ir, 2 * ir, 2 * ir)  # 内圆矩形
        innerPath = QPainterPath()  # 创建内圆路径
        innerPath.addEllipse(innerRect)  # 添加内圆到路径

        path = path.subtracted(innerPath)  # 从外圆路径中减去内圆路径，得到环形区域

        # 绘制外圆环
        painter.setPen(Qt.NoPen)  # 不使用边框
        painter.fillPath(path, borderColor)  # 填充环形区域

        # 填充内部圆
        painter.fillPath(innerPath, filledColor)  # 填充内部圆形区域

    def textColor(self):
        """ 根据当前主题返回文本颜色 """
        return self.darkTextColor if isDarkTheme() else self.lightTextColor

    def getLightTextColor(self) -> QColor:
        """ 获取浅色主题下的文本颜色 """
        return self._lightTextColor

    def getDarkTextColor(self) -> QColor:
        """ 获取深色主题下的文本颜色 """
        return self._darkTextColor

    def setLightTextColor(self, color: QColor):
        """ 设置浅色主题下的文本颜色
        color: QColor对象
        """
        self._lightTextColor = QColor(color)  # 设置浅色主题文本颜色
        self.update()  # 触发重绘

    def setDarkTextColor(self, color: QColor):
        """ 设置深色主题下的文本颜色
        color: QColor对象
        """
        self._darkTextColor = QColor(color)  # 设置深色主题文本颜色
        self.update()  # 触发重绘

    def setIndicatorColor(self, light, dark):
        """ 设置指示器颜色
        light: 浅色主题下的颜色
        dark: 深色主题下的颜色
        """
        self.lightIndicatorColor = QColor(light)  # 设置浅色主题指示器颜色
        self.darkIndicatorColor = QColor(dark)  # 设置深色主题指示器颜色
        self.update()  # 触发重绘

    def setTextColor(self, light, dark):
        """ 设置文本颜色（同时设置浅色和深色主题）
        light: 浅色主题下的颜色
        dark: 深色主题下的颜色
        """
        self.setLightTextColor(light)  # 设置浅色主题文本颜色
        self.setDarkTextColor(dark)  # 设置深色主题文本颜色

    # 定义Qt属性，允许在Qt设计器中编辑文本颜色
    lightTextColor = pyqtProperty(QColor, getLightTextColor, setLightTextColor)
    darkTextColor = pyqtProperty(QColor, getDarkTextColor, setDarkTextColor)


class ToolButton(QToolButton):
    """ 工具按钮

    构造函数
    ------------
    * ToolButton(`parent`: QWidget = None) - 创建一个无图标的工具按钮
    * ToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None) - 创建带图标的工具按钮
    """

    @singledispatchmethod  # 用于支持函数重载的装饰器
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        FluentStyleSheet.BUTTON.apply(self)
        self.isPressed = False  # 标记按钮是否被按下
        self.isHover = False  # 标记鼠标是否悬停在按钮上
        self.setIconSize(QSize(16, 16))  # 设置图标尺寸为16x16像素
        self.setIcon(QIcon())  # 初始设置为无图标
        setFont(self)  # 设置按钮字体
        self._postInit()  # 调用子类可能重写的初始化后方法

    @__init__.register 
    def _(self, icon: FluentIconBase, parent: QWidget = None):
        self.__init__(parent) 
        self.setIcon(icon) # 设置按钮图标

    @__init__.register 
    def _(self, icon: QIcon, parent: QWidget = None):
        self.__init__(parent) 
        self.setIcon(icon)

    @__init__.register 
    def _(self, icon: str, parent: QWidget = None):
        self.__init__(parent) 
        self.setIcon(icon)

    def _postInit(self):
        """ 初始化后钩子方法，供子类重写 """
        pass

    def setIcon(self, icon: Union[QIcon, str, FluentIconBase]):
        """ 设置按钮图标 """
        self._icon = icon
        self.update()

    def icon(self):
        """ 获取按钮图标（转换为QIcon类型） """
        return toQIcon(self._icon)

    def setProperty(self, name: str, value) -> bool:
        """ 重写setProperty方法，处理icon属性的特殊情况 """
        if name != 'icon':  # 如果不是icon属性，调用父类方法
            return super().setProperty(name, value)

        self.setIcon(value)  # 是icon属性时调用自定义的setIcon方法
        return True

    def mousePressEvent(self, e):
        """ 处理鼠标按下事件，设置isPressed标记 """
        self.isPressed = True  # 标记按钮被按下
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """ 处理鼠标释放事件，重置isPressed标记 """
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        """ 处理鼠标进入事件，设置isHover标记并触发重绘 """
        self.isHover = True 
        self.update()

    def leaveEvent(self, e):
        """ 处理鼠标离开事件，重置isHover标记并触发重绘 """
        self.isHover = False 
        self.update() 

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
        """ 绘制图标的内部方法
        icon: 要绘制的图标
        painter: QPainter绘图对象
        rect: 绘制区域
        state: 图标状态（默认为QIcon.Off）
        """
        drawIcon(icon, painter, rect, state)

    def paintEvent(self, e):
        """ 处理重绘事件，绘制按钮和图标 """
        super().paintEvent(e) 
        if self._icon is None:  # 如果没有图标，直接返回
            return

        painter = QPainter(self)  # 创建绘图对象
        painter.setRenderHints(QPainter.Antialiasing |  # 设置抗锯齿
                               QPainter.SmoothPixmapTransform)  # 设置平滑像素变换

        if not self.isEnabled():  # 如果按钮被禁用，设置透明度
            painter.setOpacity(0.43)
        elif self.isPressed:  # 如果按钮被按下，设置不同的透明度
            painter.setOpacity(0.63)

        w, h = self.iconSize().width(), self.iconSize().height()  # 获取图标尺寸
        y = (self.height() - h) / 2  # 计算图标垂直居中位置
        x = (self.width() - w) / 2  # 计算图标水平居中位置
        self._drawIcon(self._icon, painter, QRectF(x, y, w, h))  # 绘制图标


class TransparentToolButton(ToolButton):
    """ 透明背景工具按钮 """
    def _drawIcon(self, icon, painter, rect):
        return super()._drawIcon(icon, painter, rect)  # 直接调用父类方法


class PrimaryToolButton(ToolButton):
    """ 主色调工具按钮

    构造函数
    ------------
    * PrimaryToolButton(`parent`: QWidget = None) - 创建一个无图标的主色调工具按钮
    * PrimaryToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None) - 创建带图标的主色调工具按钮
    """

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
        """ 重绘图标方法，为主色调工具按钮提供特殊的图标绘制逻辑
        当图标是FluentIconBase或Icon类型且按钮可用时，反转图标颜色以适应主色调背景
        """
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            # 反转图标颜色以适应主色调背景
            theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
            icon = icon.icon(theme)
        elif isinstance(icon, Icon) and self.isEnabled():
            # 对Icon类型处理相同的反转逻辑
            theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
            icon = icon.fluentIcon.icon(theme)
        elif not self.isEnabled():
            # 设置禁用状态的透明度和图标主题
            painter.setOpacity(0.786 if isDarkTheme() else 0.9)
            if isinstance(icon, FluentIconBase):
                icon = icon.icon(Theme.DARK)

        return drawIcon(icon, painter, rect, state)  # 调用通用的图标绘制函数


class ToggleToolButton(ToolButton):
    """ 切换工具按钮

    构造函数
    ------------
    * ToggleToolButton(`parent`: QWidget = None) - 创建一个无图标的切换工具按钮
    * ToggleToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None) - 创建带图标的切换工具按钮
    """

    def _postInit(self):
        """ 初始化后设置按钮为可选中状态 """
        self.setCheckable(True) 
        self.setChecked(False)

    def _drawIcon(self, icon, painter, rect):
        """ 重绘图标方法，根据按钮选中状态绘制不同样式的图标
        如果未选中，使用普通工具按钮样式；如果选中，使用主色调工具按钮样式
        """
        if not self.isChecked():
            return ToolButton._drawIcon(self, icon, painter, rect)  # 未选中时使用普通样式

        PrimaryToolButton._drawIcon(self, icon, painter, rect, QIcon.On)  # 选中时使用主色调样式



class TransparentToggleToolButton(ToggleToolButton):
    """ 透明背景切换工具按钮

    构造函数
    ------------
    * TransparentToggleToolButton(`parent`: QWidget = None) - 创建一个无图标的透明切换工具按钮
    * TransparentToggleToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None) - 创建带图标的透明切换工具按钮
    """


class DropDownButtonBase:
    """ 下拉按钮基类 """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # 调用父类构造函数
        self._menu = None  # 下拉菜单对象
        self.arrowAni = TranslateYAnimation(self)  # 箭头动画对象

    def setMenu(self, menu: RoundMenu):
        """ 设置下拉菜单
        menu: RoundMenu对象
        """
        self._menu = menu  # 存储菜单对象

    def menu(self) -> RoundMenu:
        """ 获取下拉菜单 """
        return self._menu  # 返回菜单对象

    def _showMenu(self):
        """ 显示下拉菜单
        自动选择最佳的动画方向（下拉或上拉）
        """
        if not self.menu():  # 如果没有菜单，直接返回
            return

        menu = self.menu()  # 获取菜单对象
        menu.view.setMinimumWidth(self.width())  # 设置菜单最小宽度
        menu.view.adjustSize()  # 调整视图大小
        menu.adjustSize()  # 调整菜单大小

        # 计算下拉方向的动画高度
        x = -menu.width()//2 + menu.layout().contentsMargins().left() + self.width()//2  # 计算水平位置
        pd = self.mapToGlobal(QPoint(x, self.height()))  # 下拉位置
        hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)  # 下拉动画高度

        # 计算上拉方向的动画高度
        pu = self.mapToGlobal(QPoint(x, 0))  # 上拉位置
        hu = menu.view.heightForAnimation(pu, MenuAnimationType.PULL_UP)  # 上拉动画高度

        # 选择动画方向并显示菜单
        if hd >= hu:  # 如果下拉方向有更多空间
            menu.view.adjustSize(pd, MenuAnimationType.DROP_DOWN)  # 调整视图大小
            menu.exec(pd, aniType=MenuAnimationType.DROP_DOWN)  # 以下拉动画显示菜单
        else:  # 如果上拉方向有更多空间
            menu.view.adjustSize(pu, MenuAnimationType.PULL_UP)  # 调整视图大小
            menu.exec(pu, aniType=MenuAnimationType.PULL_UP)  # 以上拉动画显示菜单

    def _hideMenu(self):
        """ 隐藏下拉菜单 """
        if self.menu():  # 如果有菜单
            self.menu().hide()  # 隐藏菜单

    def _drawDropDownIcon(self, painter, rect):
        """ 绘制下拉箭头图标
        painter: QPainter绘图对象
        rect: 绘制区域
        根据主题绘制不同颜色的箭头图标
        """
        if isDarkTheme():  # 如果是深色主题
            FIF.ARROW_DOWN.render(painter, rect)  # 使用默认颜色绘制箭头
        else:  # 如果是浅色主题
            FIF.ARROW_DOWN.render(painter, rect, fill="#646464")  # 使用灰色绘制箭头

    def paintEvent(self, e):
        """ 处理重绘事件，绘制下拉箭头图标
        根据按钮状态（悬停/按下）设置不同的透明度
        """
        painter = QPainter(self)  # 创建绘图对象
        painter.setRenderHints(QPainter.Antialiasing)  # 设置抗锯齿
        if self.isHover:  # 如果鼠标悬停
            painter.setOpacity(0.8)  # 设置透明度
        elif self.isPressed:  # 如果按钮被按下
            painter.setOpacity(0.7)  # 设置透明度

        # 计算箭头位置并绘制
        rect = QRectF(self.width()-22, self.height() /
                      2-5+self.arrowAni.y, 10, 10)
        self._drawDropDownIcon(painter, rect)  # 绘制下拉箭头


class DropDownPushButton(DropDownButtonBase, PushButton):
    """ 下拉推式按钮

    构造函数
    ------------
    * DropDownPushButton(`parent`: QWidget = None) - 创建一个无文本无图标的下拉推式按钮
    * DropDownPushButton(`text`: str, `parent`: QWidget = None,
                         `icon`: QIcon | str | FluentIconBase = None) - 创建带文本和可选图标的下拉推式按钮
    * DropDownPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None) - 创建带图标和文本的下拉推式按钮
    """

    def mouseReleaseEvent(self, e):
        """ 处理鼠标释放事件，调用父类方法后显示菜单 """
        PushButton.mouseReleaseEvent(self, e)  # 调用PushButton的鼠标释放事件处理
        self._showMenu()  # 显示下拉菜单

    def paintEvent(self, e):
        """ 处理重绘事件，先调用PushButton的绘制方法，再调用DropDownButtonBase的绘制方法 """
        PushButton.paintEvent(self, e)  # 调用PushButton的绘制方法
        DropDownButtonBase.paintEvent(self, e)  # 调用DropDownButtonBase的绘制方法（绘制下拉箭头）


class TransparentDropDownPushButton(DropDownPushButton):
    """ 透明背景下拉推式按钮

    构造函数
    ------------
    * TransparentDropDownPushButton(`parent`: QWidget = None) - 创建一个无文本无图标的透明下拉推式按钮
    * TransparentDropDownPushButton(`text`: str, `parent`: QWidget = None,
                                    `icon`: QIcon | str | FluentIconBase = None) - 创建带文本和可选图标的透明下拉推式按钮
    * TransparentDropDownPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None) - 创建带图标和文本的透明下拉推式按钮
    """


class DropDownToolButton(DropDownButtonBase, ToolButton):
    """ 下拉工具按钮

    构造函数
    ------------
    * DropDownToolButton(`parent`: QWidget = None) - 创建一个无图标的下拉工具按钮
    * DropDownToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None) - 创建带图标的下拉工具按钮
    """

    def mouseReleaseEvent(self, e):
        """ 处理鼠标释放事件，调用父类方法后显示菜单 """
        ToolButton.mouseReleaseEvent(self, e)  # 调用ToolButton的鼠标释放事件处理
        self._showMenu()  # 显示下拉菜单

    def _drawIcon(self, icon, painter, rect: QRectF):
        """ 重绘图标方法，调整图标位置使其不与下拉箭头重叠 """
        rect.moveLeft(12)  # 调整图标位置到左侧
        return super()._drawIcon(icon, painter, rect)  # 调用父类方法绘制图标

    def paintEvent(self, e):
        """ 处理重绘事件，先调用ToolButton的绘制方法，再调用DropDownButtonBase的绘制方法 """
        ToolButton.paintEvent(self, e)  # 调用ToolButton的绘制方法
        DropDownButtonBase.paintEvent(self, e)  # 调用DropDownButtonBase的绘制方法（绘制下拉箭头）


class TransparentDropDownToolButton(DropDownToolButton):
    """ 透明背景下拉工具按钮

    构造函数
    ------------
    * TransparentDropDownToolButton(`parent`: QWidget = None) - 创建一个无图标的透明下拉工具按钮
    * TransparentDropDownToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None) - 创建带图标的透明下拉工具按钮
    """


class PrimaryDropDownButtonBase(DropDownButtonBase):
    """ 主色调下拉按钮基类 """

    def _drawDropDownIcon(self, painter, rect):
        """ 重绘下拉箭头图标方法，为主色调按钮提供特殊的箭头颜色
        根据当前主题自动反转箭头颜色以适应主色调背景
        """
        theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT  # 反转主题
        FIF.ARROW_DOWN.render(painter, rect, theme)  # 使用反转后的主题绘制箭头


class PrimaryDropDownPushButton(PrimaryDropDownButtonBase, PrimaryPushButton):
    """ 主色调下拉推式按钮

    构造函数
    ------------
    * PrimaryDropDownPushButton(`parent`: QWidget = None) - 创建一个无文本无图标的主色调下拉推式按钮
    * PrimaryDropDownPushButton(`text`: str, `parent`: QWidget = None,
                                `icon`: QIcon | str | FluentIconBase = None) - 创建带文本和可选图标的主色调下拉推式按钮
    * PrimaryDropDownPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None) - 创建带图标和文本的主色调下拉推式按钮
    """

    def mouseReleaseEvent(self, e):
        """ 处理鼠标释放事件，调用父类方法后显示菜单 """
        PrimaryPushButton.mouseReleaseEvent(self, e)  # 调用PrimaryPushButton的鼠标释放事件处理
        self._showMenu()  # 显示下拉菜单

    def paintEvent(self, e):
        """ 处理重绘事件，先调用PrimaryPushButton的绘制方法，再调用PrimaryDropDownButtonBase的绘制方法 """
        PrimaryPushButton.paintEvent(self, e)  # 调用PrimaryPushButton的绘制方法
        PrimaryDropDownButtonBase.paintEvent(self, e)  # 调用PrimaryDropDownButtonBase的绘制方法（绘制下拉箭头）


class PrimaryDropDownToolButton(PrimaryDropDownButtonBase, PrimaryToolButton):
    """ 主色调下拉工具按钮

    构造函数
    ------------
    * PrimaryDropDownToolButton(`parent`: QWidget = None) - 创建一个无图标的主色调下拉工具按钮
    * PrimaryDropDownToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None) - 创建带图标的主色调下拉工具按钮
    """

    def mouseReleaseEvent(self, e):
        """ 处理鼠标释放事件，调用父类方法后显示菜单 """
        PrimaryToolButton.mouseReleaseEvent(self, e)  # 调用PrimaryToolButton的鼠标释放事件处理
        self._showMenu()  # 显示下拉菜单

    def _drawIcon(self, icon, painter, rect: QRectF):
        """ 重绘图标方法，调整图标位置使其不与下拉箭头重叠 """
        rect.moveLeft(12)  # 调整图标位置到左侧
        return super()._drawIcon(icon, painter, rect)  # 调用父类方法绘制图标

    def paintEvent(self, e):
        """ 处理重绘事件，先调用PrimaryToolButton的绘制方法，再调用PrimaryDropDownButtonBase的绘制方法 """
        PrimaryToolButton.paintEvent(self, e)  # 调用PrimaryToolButton的绘制方法
        PrimaryDropDownButtonBase.paintEvent(self, e)  # 调用PrimaryDropDownButtonBase的绘制方法（绘制下拉箭头）


class SplitDropButton(ToolButton):
    """ 分割按钮的下拉部分 """

    def _postInit(self):
        """ 初始化后设置下拉按钮的特殊属性 """
        self.arrowAni = TranslateYAnimation(self)  # 创建箭头动画对象
        self.setIcon(FIF.ARROW_DOWN)  # 设置箭头图标
        self.setIconSize(QSize(10, 10))  # 设置图标尺寸
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)  # 设置尺寸策略

    def _drawIcon(self, icon, painter, rect):
        """ 重绘图标方法，应用动画效果并根据按钮状态设置不同透明度 """
        rect.translate(0, self.arrowAni.y)  # 应用动画位移

        if self.isPressed:  # 如果按钮被按下
            painter.setOpacity(0.5)  # 设置透明度
        elif self.isHover:  # 如果鼠标悬停
            painter.setOpacity(1)  # 设置透明度
        else:  # 默认状态
            painter.setOpacity(0.63)  # 设置透明度

        super()._drawIcon(icon, painter, rect)  # 调用父类方法绘制图标


class PrimarySplitDropButton(PrimaryToolButton):
    """ 主色调分割按钮的下拉部分 """

    def _postInit(self):
        """ 初始化后设置主色调下拉按钮的特殊属性 """
        self.arrowAni = TranslateYAnimation(self)  # 创建箭头动画对象
        self.setIcon(FIF.ARROW_DOWN)  # 设置箭头图标
        self.setIconSize(QSize(10, 10))  # 设置图标尺寸
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)  # 设置尺寸策略

    def _drawIcon(self, icon, painter, rect):
        """ 重绘图标方法，应用动画效果、设置透明度并根据主题反转图标颜色 """
        rect.translate(0, self.arrowAni.y)  # 应用动画位移

        if self.isPressed:  # 如果按钮被按下
            painter.setOpacity(0.7)  # 设置透明度
        elif self.isHover:  # 如果鼠标悬停
            painter.setOpacity(0.9)  # 设置透明度
        else:  # 默认状态
            painter.setOpacity(1)  # 设置透明度

        if isinstance(icon, FluentIconBase):  # 如果是Fluent图标
            # 根据主题反转图标颜色以适应主色调背景
            icon = icon.icon(Theme.DARK if not isDarkTheme() else Theme.LIGHT)

        super()._drawIcon(icon, painter, rect)  # 调用父类方法绘制图标


class SplitWidgetBase(QWidget):
    """ 分割按钮基类部件 """

    dropDownClicked = pyqtSignal()  # 下拉按钮点击信号

    def __init__(self, parent=None):
        super().__init__(parent=parent)  # 调用父类QWidget的构造函数
        self.flyout = None  # 弹出窗口部件
        self.dropButton = SplitDropButton(self)  # 创建下拉按钮

        self.hBoxLayout = QHBoxLayout(self)  # 创建水平布局
        self.hBoxLayout.setSpacing(0)  # 设置间距为0
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)  # 设置边距为0
        self.hBoxLayout.addWidget(self.dropButton)  # 添加下拉按钮到布局

        # 连接下拉按钮的点击信号
        self.dropButton.clicked.connect(self.dropDownClicked)
        self.dropButton.clicked.connect(self.showFlyout)

        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置尺寸策略

    def setWidget(self, widget: QWidget):
        """ 设置左侧的主要部件
        widget: 要添加的QWidget对象
        """
        self.hBoxLayout.insertWidget(0, widget, 1, Qt.AlignLeft)  # 在布局左侧插入部件

    def setDropButton(self, button):
        """ 设置下拉按钮
        button: 新的下拉按钮对象
        """
        self.hBoxLayout.removeWidget(self.dropButton)  # 从布局中移除旧的下拉按钮
        self.dropButton.deleteLater()  # 删除旧的下拉按钮

        self.dropButton = button  # 设置新的下拉按钮
        # 连接新下拉按钮的点击信号
        self.dropButton.clicked.connect(self.dropDownClicked)
        self.dropButton.clicked.connect(self.showFlyout)
        self.hBoxLayout.addWidget(button)  # 将新下拉按钮添加到布局

    def setDropIcon(self, icon: Union[str, QIcon, FluentIconBase]):
        """ 设置下拉按钮的图标
        icon: 可以是字符串、QIcon对象或FluentIconBase对象
        """
        self.dropButton.setIcon(icon)  # 设置下拉按钮图标
        self.dropButton.removeEventFilter(self.dropButton.arrowAni)  # 移除动画事件过滤器

    def setDropIconSize(self, size: QSize):
        """ 设置下拉按钮的图标尺寸
        size: QSize对象
        """
        self.dropButton.setIconSize(size)  # 设置下拉按钮图标尺寸

    def setFlyout(self, flyout):
        """ 设置点击下拉按钮时弹出的窗口部件

        参数
        ----------
        flyout: QWidget
            点击下拉按钮时弹出的窗口部件，需要包含`exec(pos: QPoint)`方法
        """
        self.flyout = flyout  # 设置弹出窗口部件

    def showFlyout(self):
        """ 显示弹出窗口
        计算弹出位置并执行显示
        """
        if not self.flyout:  # 如果没有弹出窗口，直接返回
            return

        w = self.flyout  # 获取弹出窗口

        if isinstance(w, RoundMenu):  # 如果是RoundMenu类型
            w.view.setMinimumWidth(self.width())  # 设置视图最小宽度
            w.view.adjustSize()  # 调整视图大小
            w.adjustSize()  # 调整菜单大小

        # 计算水平偏移量
        dx = w.layout().contentsMargins().left() if isinstance(w, RoundMenu) else 0
        x = -w.width()//2 + dx + self.width()//2  # 计算水平位置使其居中
        y = self.height()  # 垂直位置在按钮下方
        w.exec(self.mapToGlobal(QPoint(x, y)))  # 在全局坐标位置显示弹出窗口


# 导入所需模块（假设已导入，此处省略）

class SplitPushButton(SplitWidgetBase):
    """ 分割按钮

    构造方法
    ------------
    * SplitPushButton(`parent`: QWidget = None)
        - 仅指定父窗口控件的构造方法
    * SplitPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
        - 指定文本、父窗口控件和图标的构造方法，图标支持QIcon对象、图片路径字符串或FluentIconBase图标
    """

    # 定义按钮点击信号，当主按钮被点击时发射
    clicked = pyqtSignal()

    # 使用 singledispatchmethod 装饰器实现构造方法的重载，处理仅传入父控件的情况
    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        # 调用父类 SplitWidgetBase 的构造方法
        super().__init__(parent=parent)
        # 创建一个普通按钮作为主按钮
        self.button = PushButton(self)
        # 设置主按钮的对象名称，用于样式表识别
        self.button.setObjectName('splitPushButton')
        # 将主按钮的点击信号连接到当前类的 clicked 信号
        self.button.clicked.connect(self.clicked)
        # 将主按钮设置为分割控件的主部件
        self.setWidget(self.button)
        # 调用初始化后处理方法
        self._postInit()

    # 注册另一个构造方法，处理传入文本、父控件和图标的情况
    @__init__.register
    def _(self, text: str, parent: QWidget = None, icon: Union[QIcon, str, FluentIconBase] = None):
        # 先调用仅含父控件的构造方法进行基础初始化
        self.__init__(parent)
        # 设置按钮文本
        self.setText(text)
        # 设置按钮图标
        self.setIcon(icon)

    # 注册构造方法，处理传入QIcon图标、文本和父控件的情况（图标在前，文本在后）
    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QWidget = None):
        # 调用文本在前的构造方法，调整参数顺序
        self.__init__(text, parent, icon)

    # 注册构造方法，处理传入FluentIconBase图标、文本和父控件的情况（图标在前，文本在后）
    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        # 调用文本在前的构造方法，调整参数顺序
        self.__init__(text, parent, icon)

    def _postInit(self):
        """ 初始化后处理方法，子类可重写以实现特定逻辑 """
        pass

    def text(self):
        """ 获取按钮文本 """
        return self.button.text()

    def setText(self, text: str):
        """ 设置按钮文本并调整控件大小
        
        参数:
            text: 要设置的文本字符串
        """
        self.button.setText(text)
        self.adjustSize()

    def icon(self):
        """ 获取按钮图标 """
        return self.button.icon()

    def setIcon(self, icon: Union[QIcon, FluentIconBase, str]):
        """ 设置按钮图标
        
        参数:
            icon: 支持QIcon对象、FluentIconBase图标或图片路径字符串
        """
        self.button.setIcon(icon)

    def setIconSize(self, size: QSize):
        """ 设置图标大小
        
        参数:
            size: QSize对象，表示图标尺寸
        """
        self.button.setIconSize(size)

    # 定义文本属性，可用于QSS样式表和属性绑定
    text_ = pyqtProperty(str, text, setText)
    # 定义图标属性，可用于QSS样式表和属性绑定
    icon_ = pyqtProperty(QIcon, icon, setIcon)


class PrimarySplitPushButton(SplitPushButton):
    """ 主要分割按钮（强调样式的分割按钮）

    构造方法
    ------------
    * PrimarySplitPushButton(`parent`: QWidget = None)
        - 仅指定父窗口控件的构造方法
    * PrimarySplitPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
        - 指定文本、父窗口控件和图标的构造方法
    * PrimarySplitPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
        - 指定图标（在前）、文本和父窗口控件的构造方法
    """

    def _postInit(self):
        """ 重写初始化后处理方法，替换为主要样式的按钮和下拉按钮 """
        # 设置主要样式的下拉按钮
        self.setDropButton(PrimarySplitDropButton(self))

        # 移除原主按钮并删除
        self.hBoxLayout.removeWidget(self.button)
        self.button.deleteLater()

        # 创建主要样式的主按钮
        self.button = PrimaryPushButton(self)
        # 设置主要主按钮的对象名称，用于样式表识别
        self.button.setObjectName('primarySplitPushButton')
        # 将主要主按钮的点击信号连接到当前类的 clicked 信号
        self.button.clicked.connect(self.clicked)
        # 将主要主按钮设置为分割控件的主部件
        self.setWidget(self.button)


class SplitToolButton(SplitWidgetBase):
    """ 分割工具按钮（无文本，仅图标）

    构造方法
    ------------
    * SplitToolButton(`parent`: QWidget = None)
        - 仅指定父窗口控件的构造方法
    * SplitToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
        - 指定图标和父窗口控件的构造方法，图标支持QIcon对象、图片路径字符串或FluentIconBase图标
    """

    # 定义按钮点击信号，当主按钮被点击时发射
    clicked = pyqtSignal()

    # 使用 singledispatchmethod 装饰器实现构造方法的重载，处理仅传入父控件的情况
    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        # 调用父类 SplitWidgetBase 的构造方法
        super().__init__(parent=parent)
        # 创建一个工具按钮作为主按钮
        self.button = ToolButton(self)
        # 设置主按钮的对象名称，用于样式表识别
        self.button.setObjectName('splitToolButton')
        # 将主按钮的点击信号连接到当前类的 clicked 信号
        self.button.clicked.connect(self.clicked)
        # 将主按钮设置为分割控件的主部件
        self.setWidget(self.button)
        # 调用初始化后处理方法
        self._postInit()

    # 注册构造方法，处理传入FluentIconBase图标和父控件的情况
    @__init__.register
    def _(self, icon: FluentIconBase, parent: QWidget = None):
        # 先调用仅含父控件的构造方法进行基础初始化
        self.__init__(parent)
        # 设置按钮图标
        self.setIcon(icon)

    # 注册构造方法，处理传入QIcon图标和父控件的情况
    @__init__.register
    def _(self, icon: QIcon, parent: QWidget = None):
        # 先调用仅含父控件的构造方法进行基础初始化
        self.__init__(parent)
        # 设置按钮图标
        self.setIcon(icon)

    # 注册构造方法，处理传入图片路径字符串（图标）和父控件的情况
    @__init__.register
    def _(self, icon: str, parent: QWidget = None):
        # 先调用仅含父控件的构造方法进行基础初始化
        self.__init__(parent)
        # 设置按钮图标
        self.setIcon(icon)

    def _postInit(self):
        """ 初始化后处理方法，子类可重写以实现特定逻辑 """
        pass

    def icon(self):
        """ 获取按钮图标 """
        return self.button.icon()

    def setIcon(self, icon: Union[QIcon, FluentIconBase, str]):
        """ 设置按钮图标
        
        参数:
            icon: 支持QIcon对象、FluentIconBase图标或图片路径字符串
        """
        self.button.setIcon(icon)

    def setIconSize(self, size: QSize):
        """ 设置图标大小
        
        参数:
            size: QSize对象，表示图标尺寸
        """
        self.button.setIconSize(size)

    # 定义图标属性，可用于QSS样式表和属性绑定
    icon_ = pyqtProperty(QIcon, icon, setIcon)


class PrimarySplitToolButton(SplitToolButton):
    """ 主要分割工具按钮（强调样式的分割工具按钮）

    构造方法
    ------------
    * PrimarySplitToolButton(`parent`: QWidget = None)
        - 仅指定父窗口控件的构造方法
    * PrimarySplitToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
        - 指定图标和父窗口控件的构造方法
    """

    def _postInit(self):
        """ 重写初始化后处理方法，替换为主要样式的工具按钮和下拉按钮 """
        # 设置主要样式的下拉按钮
        self.setDropButton(PrimarySplitDropButton(self))

        # 移除原主按钮并删除
        self.hBoxLayout.removeWidget(self.button)
        self.button.deleteLater()

        # 创建主要样式的工具按钮作为主按钮
        self.button = PrimaryToolButton(self)
        # 设置主要工具按钮的对象名称，用于样式表识别
        self.button.setObjectName('primarySplitToolButton')
        # 将主要工具按钮的点击信号连接到当前类的 clicked 信号
        self.button.clicked.connect(self.clicked)
        # 将主要工具按钮设置为分割控件的主部件
        self.setWidget(self.button)


class PillButtonBase:
    """ 药丸形状按钮的基类（提供药丸形状的绘制逻辑） """

    def __init__(self, *args, **kwargs):
        # 调用父类的构造方法，兼容不同父类的初始化参数
        super().__init__(*args, **kwargs)

    def paintEvent(self, e):
        """ 重写绘制事件，实现药丸形状的外观
        
        参数:
            e: 绘制事件对象
        """
        # 创建画家对象，用于绘制按钮
        painter = QPainter(self)
        # 设置渲染提示，启用抗锯齿，使边缘更平滑
        painter.setRenderHints(QPainter.Antialiasing)
        # 判断当前是否为深色主题
        isDark = isDarkTheme()

        # 如果按钮未被选中
        if not self.isChecked():
            # 调整绘制区域（向内缩进1像素）
            rect = self.rect().adjusted(1, 1, -1, -1)
            # 根据主题设置边框颜色
            borderColor = QColor(255, 255, 255, 18) if isDark else QColor(0, 0, 0, 15)

            # 根据按钮状态设置背景颜色
            if not self.isEnabled():  # 按钮禁用状态
                bgColor = QColor(255, 255, 255, 11) if isDark else QColor(249, 249, 249, 75)
            elif self.isPressed or self.isHover:  # 按钮被按下或悬停状态
                bgColor = QColor(255, 255, 255, 21) if isDark else QColor(249, 249, 249, 128)
            else:  # 按钮正常状态
                bgColor = QColor(255, 255, 255, 15) if isDark else QColor(243, 243, 243, 194)

        # 如果按钮被选中
        else:
            # 根据按钮状态设置背景颜色
            if not self.isEnabled():  # 选中且禁用状态
                bgColor = QColor(255, 255, 255, 40) if isDark else QColor(0, 0, 0, 55)
            elif self.isPressed:  # 选中且被按下状态
                bgColor = ThemeColor.DARK_2.color() if isDark else ThemeColor.LIGHT_3.color()
            elif self.isHover:  # 选中且悬停状态
                bgColor = ThemeColor.DARK_1.color() if isDark else ThemeColor.LIGHT_1.color()
            else:  # 选中且正常状态
                bgColor = themeColor()

            # 选中状态下无边框
            borderColor = Qt.transparent
            # 绘制区域为整个按钮区域
            rect = self.rect()

        # 设置画笔（边框）颜色
        painter.setPen(borderColor)
        # 设置画刷（背景）颜色
        painter.setBrush(bgColor)

        # 计算圆角半径（高度的一半，实现药丸形状）
        r = rect.height() / 2
        # 绘制圆角矩形（药丸形状）
        painter.drawRoundedRect(rect, r, r)


class PillPushButton(TogglePushButton, PillButtonBase):
    """ 药丸形状的切换按钮（可选中/取消选中的按钮，带文本）

    构造方法
    ------------
    * PillPushButton(`parent`: QWidget = None)
        - 仅指定父窗口控件的构造方法
    * PillPushButton(`text`: str, `parent`: QWidget = None, `icon`: QIcon | str | FluentIconBase = None)
        - 指定文本、父窗口控件和图标的构造方法
    * PillPushButton(`icon`: QIcon | FluentIcon, `text`: str, `parent`: QWidget = None)
        - 指定图标（在前）、文本和父窗口控件的构造方法
    """

    def paintEvent(self, e):
        """ 重写绘制事件，先绘制药丸形状背景，再绘制按钮内容（文本/图标）
        
        参数:
            e: 绘制事件对象
        """
        # 调用药丸形状基类的绘制方法，绘制背景
        PillButtonBase.paintEvent(self, e)
        # 调用切换按钮的绘制方法，绘制文本和图标
        TogglePushButton.paintEvent(self, e)


class PillToolButton(ToggleToolButton, PillButtonBase):
    """ 药丸形状的切换工具按钮（可选中/取消选中的工具按钮，仅图标）

    构造方法
    ------------
    * PillToolButton(`parent`: QWidget = None)
        - 仅指定父窗口控件的构造方法
    * PillToolButton(`icon`: QIcon | str | FluentIconBase, `parent`: QWidget = None)
        - 指定图标和父窗口控件的构造方法
    """

    def paintEvent(self, e):
        """ 重写绘制事件，先绘制药丸形状背景，再绘制工具按钮内容（图标）
        
        参数:
            e: 绘制事件对象
        """
        # 调用药丸形状基类的绘制方法，绘制背景
        PillButtonBase.paintEvent(self, e)
        # 调用切换工具按钮的绘制方法，绘制图标
        ToggleToolButton.paintEvent(self, e)


class CustomStandardButton(ToggleToolButton):
    """ 自定义按钮类 """
   
        
        