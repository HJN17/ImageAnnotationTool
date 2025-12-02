# coding:utf-8
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QPoint, QRectF, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QColor, QMouseEvent, QPainter, QPainterPath
from PyQt5.QtWidgets import QProxyStyle, QSlider, QStyle, QStyleOptionSlider,QWidget

from ...common.style_sheet import isDarkTheme
from ...common.color import autoFallbackThemeColor
from ...common.overload import singledispatchmethod



class SliderHandle(QWidget):
    """ 滑块手柄类，用于显示和控制滑块的可拖动部分 """

    pressed = pyqtSignal()  # 滑块按下信号
    released = pyqtSignal()  # 滑块释放信号

    def __init__(self, parent: QSlider):
        """ 初始化滑块手柄

        参数:
            parent: 父滑块控件
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self.setFixedSize(16, 16)  # 设置手柄固定大小
        self._radius = 4  # 内部圆的初始半径
        # 亮暗主题下的手柄颜色
        self.lightHandleColor = QColor()
        self.darkHandleColor = QColor()
        # 创建半径动画，用于手柄状态变化时的动画效果
        self.radiusAni = QPropertyAnimation(self, b'radius', self)
        self.radiusAni.setDuration(100)  # 设置动画持续时间为100毫秒

    @pyqtProperty(float)
    def radius(self):
        """ 获取手柄内部圆的半径 (属性装饰器) """
        return self._radius

    @radius.setter
    def radius(self, r):
        """ 设置手柄内部圆的半径 (属性装饰器设置方法)

        参数:
            r: 新的半径值
        """
        self._radius = r  # 更新半径值
        self.update()  # 触发重绘

    def setHandleColor(self, light, dark):
        """ 设置手柄颜色

        参数:
            light: 亮主题下的颜色
            dark: 暗主题下的颜色
        """
        self.lightHandleColor = QColor(light)  # 设置亮主题颜色
        self.darkHandleColor = QColor(dark)  # 设置暗主题颜色
        self.update()  # 触发重绘

    def enterEvent(self, e):
        """ 鼠标进入事件处理

        参数:
            e: 鼠标事件对象
        """
        self._startAni(5)  # 鼠标进入时放大半径到6.5

    def leaveEvent(self, e):
        """ 鼠标离开事件处理

        参数:
            e: 鼠标事件对象
        """
        self._startAni(4)  # 鼠标离开时恢复半径到5

    def mousePressEvent(self, e):
        """ 鼠标按下事件处理

        参数:
            e: 鼠标事件对象
        """
        self._startAni(3)  # 按下时缩小半径到4
        self.pressed.emit()  # 发射按下信号

    def mouseReleaseEvent(self, e):
        """ 鼠标释放事件处理

        参数:
            e: 鼠标事件对象
        """
        self._startAni(5)  # 释放时放大半径到6.5
        self.released.emit()  # 发射释放信号

    def _startAni(self, radius):
        """ 启动半径动画

        参数:
            radius: 目标半径值
        """
        self.radiusAni.stop()  # 停止当前动画
        self.radiusAni.setStartValue(self.radius)  # 设置起始值
        self.radiusAni.setEndValue(radius)  # 设置结束值
        self.radiusAni.start()  # 启动动画

    def paintEvent(self, e):
        """ 绘制事件处理，自定义手柄外观

        参数:
            e: 绘制事件对象
        """
        painter = QPainter(self)  # 创建画家对象
        # 设置渲染提示，启用抗锯齿
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)  # 初始不设置画笔

        # 绘制外圈
        isDark = isDarkTheme()  # 检查是否为暗主题
        # 根据主题设置外圈边框颜色
        painter.setPen(QColor(0, 0, 0, 90 if isDark else 25))
        # 根据主题设置外圈填充颜色
        painter.setBrush(QColor(69, 69, 69) if isDark else Qt.GlobalColor.white)
        # 绘制外圈椭圆
        painter.drawEllipse(self.rect().adjusted(1, 1, -1, -1))

        # 绘制内圈
        # 使用自动回退的主题颜色
        painter.setBrush(autoFallbackThemeColor(self.lightHandleColor, self.darkHandleColor))
        # 绘制内圈椭圆，使用当前半径
        painter.drawEllipse(QPoint(8, 8), self.radius, self.radius)


class Slider(QSlider):
    """ 可点击的滑块控件类

    构造函数
    ------------
    * Slider(`parent`: QWidget = None) - 创建默认水平滑块
    * Slider(`orient`: Qt.Orientation, `parent`: QWidget = None) - 创建指定方向的滑块
    """

    clicked = pyqtSignal(int)  # 滑块点击信号，传递当前值

    @singledispatchmethod # 单分派方法装饰器，根据参数类型选择不同的实现
    def __init__(self, parent: QWidget = None):
        """ 初始化水平滑块

        参数:
            parent: 父部件
        """
        super().__init__(parent)
        self._postInit()  # 执行后初始化

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent: QWidget = None):
        """ 初始化指定方向的滑块

        参数:
            orientation: 滑块方向（水平或垂直）
            parent: 父部件
        """
        super().__init__(orientation, parent=parent)
        self._postInit()  # 执行后初始化

    def _postInit(self):
        """ 后初始化方法，设置滑块的通用属性和信号连接 """
        self.handle = SliderHandle(self)  # 创建滑块手柄
        self._pressedPos = QPoint()  # 存储鼠标按下位置
        # 存储亮暗主题下的轨道颜色
        self.lightGrooveColor = QColor()
        self.darkGrooveColor = QColor()
        self.setOrientation(self.orientation())  # 设置方向

        # 连接信号到槽函数
        self.handle.pressed.connect(self.sliderPressed) # 连接手柄按下信号到槽函数
        self.handle.released.connect(self.sliderReleased) # 连接手柄释放信号到槽函数
        self.valueChanged.connect(self._adjustHandlePos) # 连接值改变信号到槽函数

    def setThemeColor(self, light, dark):
        """ 设置滑块的主题颜色

        参数:
            light: 亮主题下的颜色
            dark: 暗主题下的颜色
        """
        self.lightGrooveColor = QColor(light)  # 设置亮主题轨道颜色
        self.darkGrooveColor = QColor(dark)  # 设置暗主题轨道颜色
        self.handle.setHandleColor(light, dark)  # 设置手柄颜色
        self.update()  # 触发重绘

    def setOrientation(self, orientation: Qt.Orientation) -> None:
        """ 设置滑块方向

        参数:
            orientation: 滑块方向（水平或垂直）
        """
        super().setOrientation(orientation)  # 调用父类方法
        # 根据方向设置最小尺寸
        if orientation == Qt.Orientation.Horizontal:
            self.setMinimumHeight(16)  # 水平滑块设置最小高度
        else:
            self.setMinimumWidth(16)  # 垂直滑块设置最小宽度

    def mousePressEvent(self, e: QMouseEvent):
        """ 鼠标按下事件处理

        参数:
            e: 鼠标事件对象
        """
        self._pressedPos = e.pos()  # 记录按下位置
        self.setValue(self._posToValue(e.pos()))  # 将位置转换为值并设置
        self.clicked.emit(self.value())  # 发射点击信号

    def mouseMoveEvent(self, e: QMouseEvent):
        """ 鼠标移动事件处理

        参数:
            e: 鼠标事件对象
        """
        self.setValue(self._posToValue(e.pos()))  # 将位置转换为值并设置
        self._pressedPos = e.pos()  # 更新按下位置
        self.sliderMoved.emit(self.value())  # 发射滑块移动信号

    @property
    def grooveLength(self):
        """ 获取轨道长度属性

        返回:
            int: 轨道长度（减去手柄宽度）
        """
        # 根据方向获取长度（宽度或高度）
        l = self.width() if self.orientation() == Qt.Orientation.Horizontal else self.height()
        return l - self.handle.width()  # 减去手柄宽度

    def _adjustHandlePos(self):
        """ 根据当前值调整手柄位置 """
        total = max(self.maximum() - self.minimum(), 1)  # 计算最大值与最小值的差值
        # 计算手柄位置的偏移量
        delta = int((self.value() - self.minimum()) / total * self.grooveLength)

        # 根据方向设置手柄位置
        if self.orientation() == Qt.Orientation.Vertical:
            self.handle.move(0, delta)  # 垂直方向设置Y坐标
        else:
            self.handle.move(delta, 0)  # 水平方向设置X坐标

    def _posToValue(self, pos: QPoint):
        """ 将鼠标位置转换为滑块值

        参数:
            pos: 鼠标位置

        返回:
            int: 对应的滑块值
        """
        pd = self.handle.width() / 2  # 手柄半径
        gs = max(self.grooveLength, 1)  # 轨道长度（至少为1）
        # 获取位置的X或Y坐标
        v = pos.x() if self.orientation() == Qt.Orientation.Horizontal else pos.y()
        # 计算对应的滑块值
        return int((v - pd) / gs * (self.maximum() - self.minimum()) + self.minimum())

    def paintEvent(self, e):
        """ 绘制事件处理

        参数:
            e: 绘制事件对象
        """
        painter = QPainter(self)  # 创建画家对象
        # 设置渲染提示，启用抗锯齿
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)  # 不设置画笔
        # 根据主题设置背景填充颜色
        painter.setBrush(QColor(255, 255, 255, 115) if isDarkTheme() else QColor(0, 0, 0, 100))

        # 根据方向调用不同的绘制方法
        if self.orientation() == Qt.Orientation.Horizontal:
            self._drawHorizonGroove(painter)  # 绘制水平轨道
            self._drawHorizonTick(painter)  # 绘制水平刻度（未实现）
        else:
            self._drawVerticalGroove(painter)  # 绘制垂直轨道
            self._drawVerticalTick(painter)  # 绘制垂直刻度（未实现）

    def _drawHorizonTick(self, painter: QPainter):
        """ 绘制水平滑块刻度（空实现）

        参数:
            painter: 画家对象
        """
        pass

    def _drawVerticalTick(self, painter: QPainter):
        """ 绘制垂直滑块刻度（空实现）

        参数:
            painter: 画家对象
        """
        pass

    def _drawHorizonGroove(self, painter: QPainter):
        """ 绘制水平轨道

        参数:
            painter: 画家对象
        """
        w, r = self.width(), self.handle.width() / 2  # 获取宽度和手柄半径
        # 绘制背景轨道
        painter.drawRoundedRect(QRectF(r, r-2, w-r*2, 4), 2, 2)

        # 检查是否有有效范围
        if self.maximum() - self.minimum() == 0:
            return

        # 设置已选择部分的颜色
        painter.setBrush(autoFallbackThemeColor(self.lightGrooveColor, self.darkGrooveColor))
        # 计算已选择部分的宽度
        aw = (self.value() - self.minimum()) / (self.maximum() - self.minimum()) * (w - r*2)
        # 绘制已选择部分的轨道
        painter.drawRoundedRect(QRectF(r, r-2, aw, 4), 2, 2)

    def _drawVerticalGroove(self, painter: QPainter):
        """ 绘制垂直轨道

        参数:
            painter: 画家对象
        """
        h, r = self.height(), self.handle.width() / 2  # 获取高度和手柄半径
        # 绘制背景轨道
        painter.drawRoundedRect(QRectF(r-2, r, 4, h-2*r), 2, 2)

        # 检查是否有有效范围
        if self.maximum() - self.minimum() == 0:
            return

        # 设置已选择部分的颜色
        painter.setBrush(autoFallbackThemeColor(self.lightGrooveColor, self.darkGrooveColor))
        # 计算已选择部分的高度
        ah = (self.value() - self.minimum()) / (self.maximum() - self.minimum()) * (h - r*2)
        # 绘制已选择部分的轨道
        painter.drawRoundedRect(QRectF(r-2, r, 4, ah), 2, 2)

    def resizeEvent(self, e):
        """ 尺寸变化事件处理

        参数:
            e: 尺寸事件对象
        """
        self._adjustHandlePos()  # 调整手柄位置


class ClickableSlider(QSlider):
    """ 可点击的滑块控件类，支持点击轨道直接跳转 """

    clicked = pyqtSignal(int)  # 点击信号，传递当前值

    def mousePressEvent(self, e: QMouseEvent):
        """ 鼠标按下事件处理

        参数:
            e: 鼠标事件对象
        """
        super().mousePressEvent(e)  # 调用父类方法

        # 根据滑块方向计算点击位置对应的值
        if self.orientation() == Qt.Horizontal:
            # 水平滑块：根据X坐标计算值
            value = int(e.pos().x() / self.width() * self.maximum())
        else:
            # 垂直滑块：根据Y坐标计算值（注意方向相反）
            value = int((self.height()-e.pos().y()) /
                        self.height() * self.maximum())

        self.setValue(value)  # 设置滑块值
        self.clicked.emit(self.value())  # 发射点击信号


class HollowHandleStyle(QProxyStyle):
    """ 空心手柄样式类，为滑块提供自定义的空心手柄外观 """

    def __init__(self, config: dict = None):
        """ 初始化空心手柄样式

        参数:
            config: 样式配置字典，可自定义各种样式参数
        """
        super().__init__()  # 调用父类构造函数
        # 初始化默认配置
        self.config = {
            "groove.height": 3,  # 轨道高度
            "sub-page.color": QColor(255, 255, 255),  # 已选择部分颜色
            "add-page.color": QColor(255, 255, 255, 64),  # 未选择部分颜色
            "handle.color": QColor(255, 255, 255),  # 手柄颜色
            "handle.ring-width": 4,  # 手柄环宽度
            "handle.hollow-radius": 6,  # 手柄内空心半径
            "handle.margin": 4  # 手柄边距
        }
        config = config if config else {}  # 确保配置不为None
        self.config.update(config)  # 更新配置

        # 计算手柄大小
        w = self.config["handle.margin"]+self.config["handle.ring-width"] + \
            self.config["handle.hollow-radius"]
        self.config["handle.size"] = QSize(2*w, 2*w)  # 设置手柄尺寸

    def subControlRect(self, cc: QStyle.ComplexControl, opt: QStyleOptionSlider, sc: QStyle.SubControl, widget: QWidget):
        """ 获取子控件占用的矩形区域

        参数:
            cc: 复杂控件类型
            opt: 样式选项
            sc: 子控件类型
            widget: 控件实例

        返回:
            QRect: 子控件的矩形区域
        """
        # 仅处理滑块控件且为水平方向且不是刻度标记的情况
        if cc != self.CC_Slider or opt.orientation != Qt.Horizontal or sc == self.SC_SliderTickmarks:
            return super().subControlRect(cc, opt, sc, widget)  # 其他情况调用父类方法

        rect = opt.rect  # 获取控件矩形

        if sc == self.SC_SliderGroove:
            # 计算轨道矩形
            h = self.config["groove.height"]  # 轨道高度
            # 居中显示轨道
            grooveRect = QRectF(0, (rect.height()-h)//2, rect.width(), h)
            return grooveRect.toRect()  # 返回矩形区域

        elif sc == self.SC_SliderHandle:
            # 计算手柄矩形
            size = self.config["handle.size"]  # 手柄大小
            # 计算手柄位置
            x = self.sliderPositionFromValue(
                opt.minimum, opt.maximum, opt.sliderPosition, rect.width())

            # 处理手柄超出滑块范围的情况
            x *= (rect.width()-size.width())/rect.width()
            # 创建手柄矩形
            sliderRect = QRectF(x, 0, size.width(), size.height())
            return sliderRect.toRect()  # 返回矩形区域

    def drawComplexControl(self, cc: QStyle.ComplexControl, opt: QStyleOptionSlider, painter: QPainter, widget: QWidget):
        """ 绘制复杂控件

        参数:
            cc: 复杂控件类型
            opt: 样式选项
            painter: 画家对象
            widget: 控件实例
        """
        # 仅处理滑块控件且为水平方向的情况
        if cc != self.CC_Slider or opt.orientation != Qt.Horizontal:
            return super().drawComplexControl(cc, opt, painter, widget)  # 其他情况调用父类方法

        # 获取轨道和手柄的矩形区域
        grooveRect = self.subControlRect(cc, opt, self.SC_SliderGroove, widget)
        handleRect = self.subControlRect(cc, opt, self.SC_SliderHandle, widget)
        # 设置渲染属性
        painter.setRenderHints(QPainter.Antialiasing)  # 启用抗锯齿
        painter.setPen(Qt.NoPen)  # 不使用画笔

        # 绘制轨道
        painter.save()  # 保存当前状态
        painter.translate(grooveRect.topLeft())  # 移动坐标系到轨道左上角

        # 绘制已选择部分
        w = handleRect.x()-grooveRect.x()  # 计算已选择宽度
        h = self.config['groove.height']  # 获取轨道高度
        painter.setBrush(self.config["sub-page.color"])  # 设置已选择部分颜色
        painter.drawRect(0, 0, w, h)  # 绘制已选择部分

        # 绘制未选择部分
        x = w+self.config['handle.size'].width()  # 计算未选择部分起始位置
        painter.setBrush(self.config["add-page.color"])  # 设置未选择部分颜色
        painter.drawRect(x, 0, grooveRect.width()-w, h)  # 绘制未选择部分
        painter.restore()  # 恢复之前的状态

        # 绘制手柄
        ringWidth = self.config["handle.ring-width"]  # 环宽度
        hollowRadius = self.config["handle.hollow-radius"]  # 空心半径
        radius = ringWidth + hollowRadius  # 外环半径

        path = QPainterPath()  # 创建路径
        path.moveTo(0, 0)  # 移动到起点
        center = handleRect.center() + QPoint(1, 1)  # 计算中心位置（微调）
        path.addEllipse(center, radius, radius)  # 添加外环
        path.addEllipse(center, hollowRadius, hollowRadius)  # 添加内环（用于创建空心效果）

        # 设置手柄颜色
        handleColor = self.config["handle.color"]  # 获取手柄颜色
        # 根据是否激活调整透明度
        handleColor.setAlpha(255 if opt.activeSubControls !=
                             self.SC_SliderHandle else 153)
        painter.setBrush(handleColor)  # 设置画笔颜色
        painter.drawPath(path)  # 绘制路径（空心效果）

        # 绘制按下状态的手柄
        if widget.isSliderDown():
            handleColor.setAlpha(255)  # 不透明
            painter.setBrush(handleColor)  # 设置画笔颜色
            painter.drawEllipse(handleRect)  # 绘制实心椭圆