# coding:utf-8
from typing import  Union

from PyQt5.QtCore import Qt, pyqtProperty, pyqtSignal, QSize, QRectF, QUrl
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QImage, QPainterPath,QImageReader, QMovie, QDesktopServices
from PyQt5.QtWidgets import QLabel, QWidget, QApplication, QPushButton

from ...common.overload import singledispatchmethod
from ...common.font import setFont, getFont
from ...common.style_sheet import FluentStyleSheet, setCustomStyleSheet
from ...common.config import qconfig, isDarkTheme

from .menu import LabelContextMenu

from functools import singledispatchmethod

class PixmapLabel(QLabel):
    """ 高 DPI 像素图标签 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__pixmap = QPixmap()

    def setPixmap(self, pixmap: QPixmap):
        self.__pixmap = pixmap
        self.setFixedSize(pixmap.size())
        self.update()

    def pixmap(self):
        return self.__pixmap

    def paintEvent(self, e):
        if self.__pixmap.isNull():
            return super().paintEvent(e)

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)
        painter.drawPixmap(self.rect(), self.__pixmap)




class FluentLabelBase(QLabel):
    """ Fluent 标签基类
    
    这是所有 Fluent UI 风格标签的基类，提供主题切换支持、字体设置、颜色控制等基础功能。
    
    构造函数
    ----------
    * FluentLabelBase(`parent`: QWidget = None) - 创建无文本的标签
    * FluentLabelBase(`text`: str, `parent`: QWidget = None) - 创建带文本的标签
    """

    # 使用 singledispatchmethod 实现多态构造函数
    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._init()

    # 注册第二个构造函数，支持直接传入文本
    @__init__.register
    def _(self, text: str, parent: QWidget = None):
        self.__init__(parent)
        self.setText(text)

    def _init(self):
        FluentStyleSheet.LABEL.apply(self)
        # 设置字体（由子类实现）
        self.setFont(self.getFont())
        # 设置文本颜色（默认值）
        self.setTextColor()
        # 连接主题变化信号，实现主题切换时自动更新颜色
        connect = qconfig.themeChanged.connect(lambda: self.setTextColor(self.lightColor, self.darkColor))
        # 确保在控件销毁时断开信号连接，防止内存泄漏
        self.destroyed.connect(lambda: self.disconnect(connect))

        # 连接上下文菜单请求信号
        self.customContextMenuRequested.connect(self._onContextMenuRequested)
        return self

    def getFont(self):
        raise NotImplementedError

    def setTextColor(self, light=QColor(0, 0, 0), dark=QColor(255, 255, 255)):
        """ 设置标签的文本颜色

        参数
        ----------
        light, dark: QColor | Qt.GlobalColor | str
            亮色/暗色模式下的文本颜色
        """
        # 保存颜色设置
        self._lightColor = QColor(light)
        self._darkColor = QColor(dark)

        # 设置自定义样式表，实现根据主题自动切换颜色
        setCustomStyleSheet(
            self,
            f"FluentLabelBase{{color:{self.lightColor.name(QColor.NameFormat.HexArgb)}}}",
            f"FluentLabelBase{{color:{self.darkColor.name(QColor.NameFormat.HexArgb)}}}"
        )
        

    # 定义 lightColor 属性的 getter 方法
    @pyqtProperty(QColor)
    def lightColor(self):
        return self._lightColor

    # 定义 lightColor 属性的 setter 方法
    @lightColor.setter
    def lightColor(self, color: QColor):
        self.setTextColor(color, self.darkColor)

    # 定义 darkColor 属性的 getter 方法
    @pyqtProperty(QColor)
    def darkColor(self):
        return self._darkColor

    # 定义 darkColor 属性的 setter 方法
    @darkColor.setter
    def darkColor(self, color: QColor):
        self.setTextColor(self.lightColor, color)

    # 定义 pixelFontSize 属性的 getter 方法
    @pyqtProperty(int)
    def pixelFontSize(self):
        return self.font().pixelSize()

    # 定义 pixelFontSize 属性的 setter 方法
    @pixelFontSize.setter
    def pixelFontSize(self, size: int):
        font = self.font()
        font.setPixelSize(size)
        self.setFont(font)

    # 定义 strikeOut 属性的 getter 方法（获取是否有删除线）
    @pyqtProperty(bool)
    def strikeOut(self):
        return self.font().strikeOut()

    # 定义 strikeOut 属性的 setter 方法（设置是否有删除线）
    @strikeOut.setter
    def strikeOut(self, isStrikeOut: bool):
        font = self.font()
        font.setStrikeOut(isStrikeOut)
        self.setFont(font)

    # 定义 underline 属性的 getter 方法（获取是否有下划线）
    @pyqtProperty(bool)
    def underline(self):
        return self.font().underline()

    # 定义 underline 属性的 setter 方法（设置是否有下划线）
    @underline.setter
    def underline(self, isUnderline: bool):
        font = self.font()
        font.setStyle()  # 设置字体样式
        font.setUnderline(isUnderline)  # 设置下划线
        self.setFont(font)

    # 上下文菜单请求事件处理函数
    def _onContextMenuRequested(self, pos):
        # 创建标签的上下文菜单
        menu = LabelContextMenu(parent=self)
        # 在鼠标位置显示上下文菜单（转换为全局坐标）
        menu.exec(self.mapToGlobal(pos))


class CaptionLabel(FluentLabelBase):
    """ 文字体标签 """
    def getFont(self):
        return getFont(12)


class BodyLabel(FluentLabelBase):
    """ 正文文本标签 """

    def getFont(self):
        return getFont(14)


class CommandBarLabel(FluentLabelBase):
    """ 标题文本标签 """

    def getFont(self):
        return getFont(13, QFont.DemiBold,'Arial') 



# 标题标签类
# 继承自FluentLabelBase，用于显示较大字号的标题文本
class TitleLabel(FluentLabelBase):
    """ 标题文本标签 """

    def getFont(self):
      
      return getFont(24, QFont.DemiBold,'Arial')


class ImageLabel(QLabel):
    """ 图像标签类 """

    clicked = pyqtSignal()

    # 使用 singledispatchmethod 装饰器实现多态构造函数
    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        
        self.image = QImage()
        self.setBorderRadius(0, 0, 0, 0)  # 设置默认的四个角的边框圆角为 0（无圆角）
        self._postInit()    # 调用子类可能重写的初始化后方法

    # 注册接受字符串路径作为图像的构造函数
    @__init__.register
    def _(self, image: str, parent=None):
        self.__init__(parent)
       
        self.setImage(image)

    # 注册接受 QImage 对象作为图像的构造函数
    @__init__.register
    def _(self, image: QImage, parent=None):
        self.__init__(parent)
        self.setImage(image)

    # 注册接受 QPixmap 对象作为图像的构造函数
    @__init__.register
    def _(self, image: QPixmap, parent=None):
        self.__init__(parent)
        self.setImage(image)

    # 初始化后方法，子类可以重写此方法进行额外初始化
    def _postInit(self):
        pass

    def _onFrameChanged(self, index: int):
        """ 当图像帧改变时调用，更新当前显示的图像 """
        self.image = self.movie().currentImage()
        self.update()

    def setBorderRadius(self, topLeft: int, topRight: int, bottomLeft: int, bottomRight: int):
        """ 设置图像标签的边框圆角 """
        self._topLeftRadius = topLeft
        self._topRightRadius = topRight
        self._bottomLeftRadius = bottomLeft
        self._bottomRightRadius = bottomRight
        self.update()

    def setImage(self, image: Union[str, QPixmap, QImage] = None):
        """ 设置图像标签的图像 """
        self.image = image or QImage()

        if isinstance(image, str):
            reader = QImageReader(image)
            if reader.supportsAnimation():
                self.setMovie(QMovie(image)) # 设置动画图像
            else:
                self.image = reader.read()
        elif isinstance(image, QPixmap):
            self.image = image.toImage()

        self.setFixedSize(self.image.size())
        self.update()

    def scaledToWidth(self, width: int):
        """ 按宽度缩放图像标签的图像 """
        if self.isNull():
            return

        h = int(width / self.image.width() * self.image.height())
        self.setFixedSize(width, h)

        if self.movie():
            self.movie().setScaledSize(QSize(width, h))

    def scaledToHeight(self, height: int):
        """ 按高度缩放图像标签的图像 """
        if self.isNull():
            return

        w = int(height / self.image.height() * self.image.width())
        self.setFixedSize(w, height)

        if self.movie():
            self.movie().setScaledSize(QSize(w, height))

    def setScaledSize(self, size: QSize):
        """ 设置图像标签的缩放大小 """
        if self.isNull():
            return

        self.setFixedSize(size)

        if self.movie():
            self.movie().setScaledSize(size)

    def isNull(self):
        """ 判断图像标签是否为空 """
        return self.image.isNull()

    def mouseReleaseEvent(self, e):
        """ 处理图像标签的鼠标释放事件 """
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def setPixmap(self, pixmap: QPixmap):
        """ 设置图像标签的图像为 QPixmap 对象 """
        self.setImage(pixmap)

    def pixmap(self) -> QPixmap:
        """ 获取图像标签的图像为 QPixmap 对象 """
        return QPixmap.fromImage(self.image)

    def setMovie(self, movie: QMovie):
        """ 设置图像标签的动画为 QMovie 对象 """
        super().setMovie(movie)
        self.movie().start()
        self.image = self.movie().currentImage()
        self.movie().frameChanged.connect(self._onFrameChanged)

    def paintEvent(self, e):
        """ 绘制图像标签的图像 """
        if self.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing) # 开启反锯齿渲染

        path = QPainterPath() # 创建一个路径对象
        w, h = self.width(), self.height()

        # 绘制顶部线
        path.moveTo(self.topLeftRadius, 0)
        path.lineTo(w - self.topRightRadius, 0)

        # 绘制顶部右弧
        d = self.topRightRadius * 2
        path.arcTo(w - d, 0, d, d, 90, -90)

        # 绘制右侧线
        path.lineTo(w, h - self.bottomRightRadius)

        # 绘制底部右弧
        d = self.bottomRightRadius * 2
        path.arcTo(w - d, h - d, d, d, 0, -90)

        # 绘制底部线
        path.lineTo(self.bottomLeftRadius, h)

        # 绘制底部左弧
        d = self.bottomLeftRadius * 2
        path.arcTo(0, h - d, d, d, -90, -90)

        # 绘制左侧线
        path.lineTo(0, self.topLeftRadius)

        # 绘制顶部左弧
        d = self.topLeftRadius * 2
        path.arcTo(0, 0, d, d, -180, -90)

        # 绘制图像
        image = self.image.scaled(
            self.size()*self.devicePixelRatioF(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        painter.setPen(Qt.NoPen) # 不绘制边框
        painter.setClipPath(path) # 设置裁剪路径为图像标签的圆角路径
        painter.drawImage(self.rect(), image) # 绘制图像，将其裁剪为圆角路径

    @pyqtProperty(int)
    def topLeftRadius(self):
        return self._topLeftRadius

    @topLeftRadius.setter
    def topLeftRadius(self, radius: int):
        self.setBorderRadius(radius, self.topRightRadius, self.bottomLeftRadius, self.bottomRightRadius)

    @pyqtProperty(int)
    def topRightRadius(self):
        return self._topRightRadius

    @topRightRadius.setter
    def topRightRadius(self, radius: int):
        self.setBorderRadius(self.topLeftRadius, radius, self.bottomLeftRadius, self.bottomRightRadius)

    @pyqtProperty(int)
    def bottomLeftRadius(self):
        return self._bottomLeftRadius

    @bottomLeftRadius.setter
    def bottomLeftRadius(self, radius: int):
        self.setBorderRadius(self.topLeftRadius, self.topRightRadius, radius, self.bottomRightRadius)

    @pyqtProperty(int)
    def bottomRightRadius(self):
        return self._bottomRightRadius

    @bottomRightRadius.setter
    def bottomRightRadius(self, radius: int):
        self.setBorderRadius(
            self.topLeftRadius, self.topRightRadius, self.bottomLeftRadius, radius)


class AvatarWidget(ImageLabel):
    """ 头像组件
    这是一个用于显示用户头像的组件，继承自 ImageLabel，支持显示图像或文本首字母作为头像。"""

    
    def _postInit(self):
        self.setRadius(48)  # 设置头像的默认半径为 48 像素（直径为 96 像素）
        self.lightBackgroundColor = QColor(0, 0, 0, 50) # 设置亮色主题下的背景颜色（黑色，透明度 50）
        self.darkBackgroundColor = QColor(255, 255, 255, 50)    # 设置暗色主题下的背景颜色（白色，透明度 50）

    # radius 属性的 getter 方法，获取头像半径
    def getRadius(self):
        return self._radius

    # radius 属性的 setter 方法，设置头像半径
    def setRadius(self, radius: int):
        # 存储半径值
        self._radius = radius
        # 根据半径设置字体大小
        setFont(self, radius)
        # 设置头像的固定大小为直径（2*radius）
        self.setFixedSize(2*radius, 2*radius)
        # 更新显示
        self.update()

    # 重写父类的 setImage 方法，设置头像图像
    def setImage(self, image: Union[str, QPixmap, QImage] = None):
        # 调用父类的 setImage 方法设置图像
        super().setImage(image)
        # 确保设置图像后半径保持不变
        self.setRadius(self.radius)

    # 设置头像的背景颜色
    def setBackgroundColor(self, light: QColor, dark: QColor):
        # 设置亮色主题下的背景颜色
        self.lightBackgroundColor = QColor(light)
        # 设置暗色主题下的背景颜色
        self.darkBackgroundColor = QColor(dark)
        # 更新显示
        self.update()

    # 重写 paintEvent 方法，自定义头像绘制
    def paintEvent(self, e):
        # 创建绘图对象
        painter = QPainter(self)
        # 设置抗锯齿渲染提示，使绘制更平滑
        painter.setRenderHints(QPainter.Antialiasing)

        # 判断是否有图像
        if not self.isNull():
            # 如果有图像，绘制图像头像
            self._drawImageAvatar(painter)
        else:
            # 如果没有图像，绘制文本头像
            self._drawTextAvatar(painter)

    # 绘制图像头像的内部方法
    def _drawImageAvatar(self, painter: QPainter):
        # 中心裁剪图像以适应圆形区域
        # 将图像按比例缩放，保持宽高比并扩展以填充整个头像区域
        image = self.image.scaled(
            self.size()*self.devicePixelRatioF(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)  # type: QImage

        # 获取缩放后图像的宽度和高度
        iw, ih = image.width(), image.height()
        # 计算目标直径（考虑设备像素比）
        d = self.getRadius() * 2 * self.devicePixelRatioF()
        # 计算裁剪起始坐标（居中裁剪）
        x, y = (iw - d) / 2, (ih - d) / 2
        # 裁剪图像为正方形
        image = image.copy(int(x), int(y), int(d), int(d))

        # 创建圆形裁剪路径
        path = QPainterPath()
        path.addEllipse(QRectF(self.rect()))

        # 设置无画笔，使用裁剪路径
        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)
        # 绘制裁剪后的图像
        painter.drawImage(self.rect(), image)

    # 绘制文本头像的内部方法
    def _drawTextAvatar(self, painter: QPainter):
        # 如果没有文本，直接返回
        if not self.text():
            return

        # 根据当前主题设置背景色
        painter.setBrush(self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor)
        # 设置无画笔
        painter.setPen(Qt.NoPen)
        # 绘制圆形背景
        painter.drawEllipse(QRectF(self.rect()))

        # 设置字体
        painter.setFont(self.font())
        # 根据主题设置文本颜色
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        # 在中心绘制文本的第一个字符（大写）
        painter.drawText(self.rect(), Qt.AlignCenter, self.text()[0].upper())

    # 定义 radius 属性，关联 getter 和 setter 方法
    radius = pyqtProperty(int, getRadius, setRadius)


class HyperlinkLabel(QPushButton):
    """ Hyperlink label

    Constructors
    ------------
    * HyperlinkLabel(`parent`: QWidget = None)
    * HyperlinkLabel(`text`: str, `parent`: QWidget = None)
    * HyperlinkLabel(`url`: QUrl, `parent`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._url = QUrl()

        setFont(self, 14)
        self.setUnderlineVisible(False)
        FluentStyleSheet.LABEL.apply(self)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._onClicked)

    @__init__.register
    def _(self, text: str, parent=None):
        self.__init__(parent)
        self.setText(text)

    @__init__.register
    def _(self, url: QUrl, text: str, parent=None):
        self.__init__(parent)
        self.setText(text)
        self._url = url

    def getUrl(self) -> QUrl:
        return self._url

    def setUrl(self, url: Union[QUrl, str]):
        self._url = QUrl(url)

    def isUnderlineVisible(self):
        return self._isUnderlineVisible

    def setUnderlineVisible(self, isVisible: bool):
        self._isUnderlineVisible = isVisible
        self.setProperty('underline', isVisible)
        self.setStyle(QApplication.style())

    def _onClicked(self):
        if self.getUrl().isValid():
            QDesktopServices.openUrl(self.getUrl())

    url = pyqtProperty(QUrl, getUrl, setUrl)
    underlineVisible = pyqtProperty(bool, isUnderlineVisible, setUnderlineVisible)