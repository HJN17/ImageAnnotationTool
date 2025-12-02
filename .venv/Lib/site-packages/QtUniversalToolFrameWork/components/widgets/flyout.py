from enum import Enum
import sys
from typing import Union

from PyQt5.QtCore import (Qt, QPropertyAnimation, QPoint, QParallelAnimationGroup, QEasingCurve, QMargins,
                          QRectF, QObject, QSize, pyqtSignal, QEvent)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QCursor, QIcon, QImage, QPainterPath, QBrush, QMovie, QImageReader
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect, QLabel, QHBoxLayout, QVBoxLayout, QApplication

from ...common.auto_wrap import TextWrap  # 文本自动换行工具
from ...common.style_sheet import isDarkTheme, FluentStyleSheet  # 主题检测和样式表
from ...common.icon import FluentIconBase, drawIcon, FluentIcon  # 图标基类和绘制工具
from ...common.screen import getCurrentScreenGeometry  # 获取当前屏幕几何信息

from .button import TransparentToolButton  # 透明工具按钮
from .label import ImageLabel  # 图像标签


class FlyoutAnimationType(Enum):
    """ 浮窗动画类型枚举 """
    PULL_UP = 0  # 上拉动画
    DROP_DOWN = 1  # 下拉动画
    SLIDE_LEFT = 2  # 向左滑动动画
    SLIDE_RIGHT = 3  # 向右滑动动画
    FADE_IN = 4  # 淡入动画
    NONE = 5  # 无动画


class IconWidget(QWidget):
    """ 图标显示部件 """

    def __init__(self, icon, parent=None):
        """初始化图标显示部件
        
        参数:
            icon: 要显示的图标
            parent: 父窗口部件
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self.setFixedSize(36, 54)  # 设置固定大小
        self.icon = icon  # 保存图标

    def paintEvent(self, e):
        """绘制事件处理
        
        参数:
            e: 绘制事件对象
        """
        if not self.icon:  # 如果没有图标则直接返回
            return

        painter = QPainter(self)  # 创建绘图对象
        # 设置渲染提示：抗锯齿和平滑像素变换
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        # 计算图标绘制区域
        rect = QRectF(8, (self.height()-20)/2, 20, 20)
        # 绘制图标
        drawIcon(self.icon, painter, rect)


class FlyoutViewBase(QWidget):
    """ 浮窗视图基类 """

    def __init__(self, parent=None):
        """初始化浮窗视图基类
        
        参数:
            parent: 父窗口部件
        """
        super().__init__(parent=parent)

    def addWidget(self, widget: QWidget, stretch=0, align=Qt.AlignLeft):
        """添加部件到视图中（由子类实现）
        
        参数:
            widget: 要添加的窗口部件
            stretch: 拉伸因子
            align: 对齐方式
        """
        raise NotImplementedError  # 抛出未实现异常

    def backgroundColor(self):
        """获取背景颜色
        
        返回:
            根据当前主题返回对应的背景颜色
        """
        # 根据当前是否为暗色主题返回不同的背景颜色
        return QColor(32, 32, 32) if isDarkTheme() else QColor(249, 244, 240)

    def borderColor(self):
        """获取边框颜色
        
        返回:
            根据当前主题返回对应的边框颜色
        """
        # 根据当前是否为暗色主题返回不同的边框颜色
        return QColor(0, 0, 0, 45) if isDarkTheme() else QColor(0, 0, 0, 17)

    def paintEvent(self, e):
        """绘制事件处理
        
        参数:
            e: 绘制事件对象
        """
        painter = QPainter(self)  # 创建绘图对象
        painter.setRenderHints(QPainter.Antialiasing)  # 设置抗锯齿

        painter.setBrush(self.backgroundColor())  # 设置背景色
        painter.setPen(self.borderColor())  # 设置边框颜色

        # 调整绘制区域
        rect = self.rect().adjusted(1, 1, -1, -1)
        # 绘制圆角矩形
        painter.drawRoundedRect(rect, 8, 8)


class FlyoutView(FlyoutViewBase):
    """ 浮窗视图 """

    closed = pyqtSignal()  # 关闭信号

    def __init__(self, title: str, content: str, icon: Union[FluentIconBase, QIcon, str] = None,
                 image: Union[str, QPixmap, QImage] = None, isClosable=False, parent=None):
        """初始化浮窗视图
        
        参数:
            title: 浮窗标题
            content: 浮窗内容
            icon: 浮窗图标
            image: 浮窗图像
            isClosable: 是否显示关闭按钮
            parent: 父窗口部件
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self.icon = icon  # 保存图标
        self.title = title  # 保存标题
        self.image = image  # 保存图像
        self.content = content  # 保存内容
        self.isClosable = isClosable  # 保存是否可关闭

        self.vBoxLayout = QVBoxLayout(self)  # 垂直布局
        self.viewLayout = QHBoxLayout()  # 水平视图布局
        self.widgetLayout = QVBoxLayout()  # 部件垂直布局

        self.titleLabel = QLabel(title, self)  # 标题标签
        self.contentLabel = QLabel(content, self)  # 内容标签
        self.iconWidget = IconWidget(icon, self)  # 图标部件
        self.imageLabel = ImageLabel(self)  # 图像标签
        self.closeButton = TransparentToolButton(FluentIcon.CLOSE, self)  # 关闭按钮

        self.__initWidgets()  # 初始化部件

    def __initWidgets(self):
        """初始化窗口部件"""
        self.imageLabel.setImage(self.image)  # 设置图像

        self.closeButton.setFixedSize(32, 32)  # 设置关闭按钮大小
        self.closeButton.setIconSize(QSize(12, 12))  # 设置关闭按钮图标大小
        self.closeButton.setVisible(self.isClosable)  # 根据是否可关闭设置按钮可见性
        self.titleLabel.setVisible(bool(self.title))  # 根据是否有标题设置标签可见性
        self.contentLabel.setVisible(bool(self.content))  # 根据是否有内容设置标签可见性
        self.iconWidget.setHidden(self.icon is None)  # 根据是否有图标设置图标部件可见性

        self.closeButton.clicked.connect(self.closed)  # 连接关闭信号

        self.titleLabel.setObjectName('titleLabel')  # 设置对象名称
        self.contentLabel.setObjectName('contentLabel')  # 设置对象名称
        FluentStyleSheet.TEACHING_TIP.apply(self)  # 应用样式表

        self.__initLayout()  # 初始化布局

    def __initLayout(self):
        """初始化布局"""
        self.vBoxLayout.setContentsMargins(1, 1, 1, 1)  # 设置主布局外边距
        self.widgetLayout.setContentsMargins(0, 8, 0, 8)  # 设置部件布局外边距
        self.viewLayout.setSpacing(4)  # 设置视图布局内边距
        self.widgetLayout.setSpacing(0)  # 设置部件布局内边距
        self.vBoxLayout.setSpacing(0)  # 设置主布局内边距

        # 添加图标部件
        if not self.title or not self.content:  # 如果没有标题或内容
            self.iconWidget.setFixedHeight(36)  # 设置图标部件固定高度

        self.vBoxLayout.addLayout(self.viewLayout)  # 将视图布局添加到主布局
        self.viewLayout.addWidget(self.iconWidget, 0, Qt.AlignTop)  # 将图标部件添加到视图布局

        # 添加文本
        self._adjustText()  # 调整文本
        self.widgetLayout.addWidget(self.titleLabel)  # 添加标题标签到部件布局
        self.widgetLayout.addWidget(self.contentLabel)  # 添加内容标签到部件布局
        self.viewLayout.addLayout(self.widgetLayout)  # 将部件布局添加到视图布局

        # 添加关闭按钮
        self.closeButton.setVisible(self.isClosable)  # 设置关闭按钮可见性
        self.viewLayout.addWidget(
            self.closeButton, 0, Qt.AlignRight | Qt.AlignTop)  # 添加关闭按钮到视图布局

        # 调整内容边距
        margins = QMargins(6, 5, 6, 5)  # 基本边距
        margins.setLeft(20 if not self.icon else 5)  # 根据是否有图标调整左边距
        margins.setRight(20 if not self.isClosable else 6)  # 根据是否可关闭调整右边距
        self.viewLayout.setContentsMargins(margins)  # 设置视图布局外边距

        # 添加图像
        self._adjustImage()  # 调整图像
        self._addImageToLayout()  # 将图像添加到布局

    def addWidget(self, widget: QWidget, stretch=0, align=Qt.AlignLeft):
        """向视图添加部件
        
        参数:
            widget: 要添加的窗口部件
            stretch: 拉伸因子
            align: 对齐方式
        """
        self.widgetLayout.addSpacing(8)  # 添加间距
        self.widgetLayout.addWidget(widget, stretch, align)  # 添加部件到布局

    def _addImageToLayout(self):
        """将图像添加到布局"""
        self.imageLabel.setBorderRadius(8, 8, 0, 0)  # 设置图像标签圆角
        self.imageLabel.setHidden(self.imageLabel.isNull())  # 如果图像为空则隐藏
        self.vBoxLayout.insertWidget(0, self.imageLabel)  # 将图像标签插入到布局顶部

    def _adjustText(self):
        """调整文本显示"""
        # 计算最大宽度
        w = min(900, QApplication.screenAt(
            QCursor.pos()).geometry().width() - 200)

        # 调整标题
        chars = max(min(w / 10, 120), 30)  # 计算标题最大字符数
        self.titleLabel.setText(TextWrap.wrap(self.title, chars, False)[0])  # 自动换行标题

        # 调整内容
        chars = max(min(w / 9, 120), 30)  # 计算内容最大字符数
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])  # 自动换行内容

    def _adjustImage(self):
        """调整图像大小"""
        w = self.vBoxLayout.sizeHint().width() - 2  # 计算图像宽度
        self.imageLabel.scaledToWidth(w)  # 缩放图像到指定宽度

    def showEvent(self, e):
        """显示事件处理
        
        参数:
            e: 显示事件对象
        """
        super().showEvent(e)  # 调用父类显示事件
        self._adjustImage()  # 调整图像
        self.adjustSize()  # 调整大小


class Flyout(QWidget):
    """ 浮窗主类 """

    closed = pyqtSignal()  # 关闭信号

    def __init__(self, view: FlyoutViewBase, parent=None, isDeleteOnClose=True, isMacInputMethodEnabled=False):
        """初始化浮窗
        
        参数:
            view: 浮窗视图
            parent: 父窗口部件
            isDeleteOnClose: 关闭时是否自动删除
            isMacInputMethodEnabled: 是否启用Mac输入法支持
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self.view = view  # 保存视图
        self.hBoxLayout = QHBoxLayout(self)  # 水平布局
        self.aniManager = None  # 动画管理器（类型: FlyoutAnimationManager）
        self.isDeleteOnClose = isDeleteOnClose  # 关闭时是否自动删除
        self.isMacInputMethodEnabled = isMacInputMethodEnabled  # 是否启用Mac输入法支持

        self.hBoxLayout.setContentsMargins(15, 8, 15, 20)  # 设置布局外边距
        self.hBoxLayout.addWidget(self.view)  # 添加视图到布局
        self.setShadowEffect()  # 设置阴影效果

        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明

        # 根据平台和设置选择窗口标志
        if sys.platform != "darwin" or not isMacInputMethodEnabled:
            # 非Mac平台或未启用Mac输入法支持时，使用Popup窗口标志
            self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                                Qt.NoDropShadowWindowHint)
        else:
            # Mac平台且启用了Mac输入法支持时，使用Dialog窗口标志并安装事件过滤器
            self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event):
        """事件过滤器，用于处理特殊事件
        
        参数:
            watched: 被监视的对象
            event: 事件对象
        
        返回:
            bool: 事件是否被处理
        """
        # 在Mac平台且启用了输入法支持时，处理鼠标按下事件
        if sys.platform == "darwin" and self.isMacInputMethodEnabled:
            # 当浮窗可见且有鼠标按下事件时
            if self.isVisible() and event.type() == QEvent.MouseButtonPress:
                # 检查点击是否在浮窗外部
                if not self.rect().contains(self.mapFromGlobal(event.globalPos())):
                    self.close()  # 关闭浮窗

        return super().eventFilter(watched, event)  # 调用父类事件过滤器

    def setShadowEffect(self, blurRadius=35, offset=(0, 8)):
        """为浮窗添加阴影效果
        
        参数:
            blurRadius: 模糊半径
            offset: 阴影偏移量
        """
        # 根据当前主题选择阴影颜色
        color = QColor(0, 0, 0, 80 if isDarkTheme() else 30)
        self.shadowEffect = QGraphicsDropShadowEffect(self.view)  # 创建阴影效果
        self.shadowEffect.setBlurRadius(blurRadius)  # 设置模糊半径
        self.shadowEffect.setOffset(*offset)  # 设置阴影偏移
        self.shadowEffect.setColor(color)  # 设置阴影颜色
        self.view.setGraphicsEffect(None)  # 清除现有效果
        self.view.setGraphicsEffect(self.shadowEffect)  # 应用阴影效果

    def closeEvent(self, e):
        """关闭事件处理
        
        参数:
            e: 关闭事件对象
        """
        if self.isDeleteOnClose:  # 如果设置了关闭时自动删除
            self.deleteLater()  # 延迟删除对象

        super().closeEvent(e)  # 调用父类关闭事件
        self.closed.emit()  # 发出关闭信号

    def showEvent(self, e):
        """显示事件处理
        
        参数:
            e: 显示事件对象
        """
        # 修复 #780 问题
        self.activateWindow()  # 激活窗口
        super().showEvent(e)  # 调用父类显示事件

    def exec(self, pos: QPoint, aniType=FlyoutAnimationType.PULL_UP):
        """显示浮窗视图
        
        参数:
            pos: 显示位置
            aniType: 动画类型
        """
        # 创建动画管理器
        self.aniManager = FlyoutAnimationManager.make(aniType, self)
        self.show()  # 显示浮窗
        self.aniManager.exec(pos)  # 执行动画

    @classmethod
    def make(cls, view: FlyoutViewBase, target: Union[QWidget, QPoint] = None, parent=None,
             aniType=FlyoutAnimationType.PULL_UP, isDeleteOnClose=True, isMacInputMethodEnabled=False):
        """创建并显示浮窗
        
        参数:
            view: 浮窗视图
            target: 目标部件或位置
            parent: 父窗口
            aniType: 浮窗动画类型
            isDeleteOnClose: 关闭时是否自动删除
            isMacInputMethodEnabled: 是否启用Mac输入法支持
        
        返回:
            Flyout: 创建的浮窗对象
        """
        w = cls(view, parent, isDeleteOnClose, isMacInputMethodEnabled)  # 创建浮窗

        if target is None:  # 如果没有目标位置
            return w  # 直接返回浮窗对象

        # 先显示浮窗以获取正确的尺寸
        w.show()

        # 将浮窗移动到目标上方
        if isinstance(target, QWidget):
            # 计算相对于目标的位置
            target = FlyoutAnimationManager.make(aniType, w).position(target)

        w.exec(target, aniType)  # 执行显示动画
        return w  # 返回浮窗对象

    @classmethod
    def create(cls, title: str, content: str, icon: Union[FluentIconBase, QIcon, str] = None,
               image: Union[str, QPixmap, QImage] = None, isClosable=False, target: Union[QWidget, QPoint] = None,
               parent=None, aniType=FlyoutAnimationType.PULL_UP, isDeleteOnClose=True, isMacInputMethodEnabled=False):
        """使用默认视图创建并显示浮窗
        
        参数:
            title: 浮窗标题
            content: 浮窗内容
            icon: 浮窗图标
            image: 浮窗图像
            isClosable: 是否显示关闭按钮
            target: 目标部件或位置
            parent: 父窗口
            aniType: 浮窗动画类型
            isDeleteOnClose: 关闭时是否自动删除
            isMacInputMethodEnabled: 是否启用Mac输入法支持
        
        返回:
            Flyout: 创建的浮窗对象
        """
        # 创建浮窗视图
        view = FlyoutView(title, content, icon, image, isClosable)
        # 创建浮窗并设置关闭连接
        w = cls.make(view, target, parent, aniType, isDeleteOnClose, isMacInputMethodEnabled)
        view.closed.connect(w.close)  # 连接视图关闭信号到浮窗关闭方法
        return w  # 返回浮窗对象

    def fadeOut(self):
        """淡出动画关闭浮窗"""
        # 创建淡出动画
        self.fadeOutAni = QPropertyAnimation(self, b'windowOpacity', self)
        self.fadeOutAni.finished.connect(self.close)  # 动画结束后关闭浮窗
        self.fadeOutAni.setStartValue(1)  # 开始透明度
        self.fadeOutAni.setEndValue(0)  # 结束透明度
        self.fadeOutAni.setDuration(120)  # 动画持续时间
        self.fadeOutAni.start()  # 开始动画


class FlyoutAnimationManager(QObject):
    """ 浮窗动画管理器基类 """

    managers = {}  # 动画管理器注册表

    def __init__(self, flyout: Flyout):
        """初始化动画管理器
        
        参数:
            flyout: 要管理的浮窗对象
        """
        super().__init__()  # 调用父类构造函数
        self.flyout = flyout  # 保存浮窗对象
        self.aniGroup = QParallelAnimationGroup(self)  # 并行动画组
        self.slideAni = QPropertyAnimation(flyout, b'pos', self)  # 滑动动画
        self.opacityAni = QPropertyAnimation(flyout, b'windowOpacity', self)  # 透明度动画

        self.slideAni.setDuration(187)  # 设置滑动动画持续时间
        self.opacityAni.setDuration(187)  # 设置透明度动画持续时间

        self.opacityAni.setStartValue(0)  # 设置透明度动画起始值
        self.opacityAni.setEndValue(1)  # 设置透明度动画结束值

        # 设置动画曲线
        self.slideAni.setEasingCurve(QEasingCurve.OutQuad)  # 滑动动画曲线
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)  # 透明度动画曲线
        self.aniGroup.addAnimation(self.slideAni)  # 添加滑动动画到动画组
        self.aniGroup.addAnimation(self.opacityAni)  # 添加透明度动画到动画组

    @classmethod
    def register(cls, name):
        """注册菜单动画管理器
        
        参数:
            name: 管理器名称，应该是唯一的
        
        返回:
            装饰器函数
        """
        def wrapper(Manager):
            if name not in cls.managers:  # 如果名称不存在于注册表中
                cls.managers[name] = Manager  # 注册管理器

            return Manager

        return wrapper

    def exec(self, pos: QPoint):
        """开始动画（由子类实现）
        
        参数:
            pos: 目标位置
        """
        raise NotImplementedError  # 抛出未实现异常

    def _adjustPosition(self, pos):
        """调整浮窗位置以确保其在屏幕内
        
        参数:
            pos: 原始位置
        
        返回:
            QPoint: 调整后的位置
        """
        rect = getCurrentScreenGeometry()  # 获取当前屏幕几何信息
        # 计算浮窗大小（包含边距）
        w, h = self.flyout.sizeHint().width() + 5, self.flyout.sizeHint().height()
        # 确保浮窗不会超出屏幕左右边界
        x = max(rect.left(), min(pos.x(), rect.right() - w))
        # 确保浮窗不会超出屏幕上下边界
        y = max(rect.top(), min(pos.y() - 4, rect.bottom() - h + 5))
        return QPoint(x, y)  # 返回调整后的位置

    def position(self, target: QWidget):
        """计算相对于目标部件的左上角位置（由子类实现）
        
        参数:
            target: 目标部件
        
        返回:
            QPoint: 计算的位置
        """
        raise NotImplementedError  # 抛出未实现异常

    @classmethod
    def make(cls, aniType: FlyoutAnimationType, flyout: Flyout) -> "FlyoutAnimationManager":
        """创建指定类型的动画管理器
        
        参数:
            aniType: 动画类型
            flyout: 浮窗对象
        
        返回:
            FlyoutAnimationManager: 动画管理器实例
        """
        if aniType not in cls.managers:  # 如果动画类型不存在于注册表中
            raise ValueError(f'`{aniType}` 是无效的动画类型。')  # 抛出值错误

        return cls.managers[aniType](flyout)  # 创建并返回动画管理器实例


@FlyoutAnimationManager.register(FlyoutAnimationType.PULL_UP)
class PullUpFlyoutAnimationManager(FlyoutAnimationManager):
    """ 上拉浮窗动画管理器 """

    def position(self, target: QWidget):
        """计算上拉动画的起始位置
        
        参数:
            target: 目标部件
        
        返回:
            QPoint: 计算的位置
        """
        w = self.flyout  # 获取浮窗
        pos = target.mapToGlobal(QPoint())  # 将目标部件原点转换为全局坐标
        # 计算水平居中位置
        x = pos.x() + target.width()//2 - w.sizeHint().width()//2
        # 计算目标上方位置
        y = pos.y() - w.sizeHint().height() + w.layout().contentsMargins().bottom()
        return QPoint(x, y)  # 返回计算的位置

    def exec(self, pos: QPoint):
        """执行上拉动画
        
        参数:
            pos: 目标位置
        """
        pos = self._adjustPosition(pos)  # 调整位置确保在屏幕内
        self.slideAni.setStartValue(pos+QPoint(0, 8))  # 设置起始位置（目标下方8像素）
        self.slideAni.setEndValue(pos)  # 设置结束位置（目标位置）
        self.aniGroup.start()  # 开始动画


@FlyoutAnimationManager.register(FlyoutAnimationType.DROP_DOWN)
class DropDownFlyoutAnimationManager(FlyoutAnimationManager):
    """ 下拉浮窗动画管理器 """

    def position(self, target: QWidget):
        """计算下拉动画的起始位置
        
        参数:
            target: 目标部件
        
        返回:
            QPoint: 计算的位置
        """
        w = self.flyout  # 获取浮窗
        pos = target.mapToGlobal(QPoint(0, target.height()))  # 将目标部件底部转换为全局坐标
        # 计算水平居中位置
        x = pos.x() + target.width()//2 - w.sizeHint().width()//2
        # 计算目标下方位置
        y = pos.y() - w.layout().contentsMargins().top() + 8
        return QPoint(x, y)  # 返回计算的位置

    def exec(self, pos: QPoint):
        """执行下拉动画
        
        参数:
            pos: 目标位置
        """
        pos = self._adjustPosition(pos)  # 调整位置确保在屏幕内
        self.slideAni.setStartValue(pos-QPoint(0, 8))  # 设置起始位置（目标上方8像素）
        self.slideAni.setEndValue(pos)  # 设置结束位置（目标位置）
        self.aniGroup.start()  # 开始动画


@FlyoutAnimationManager.register(FlyoutAnimationType.SLIDE_LEFT)
class SlideLeftFlyoutAnimationManager(FlyoutAnimationManager):
    """ 向左滑动浮窗动画管理器 """

    def position(self, target: QWidget):
        """计算向左滑动动画的起始位置
        
        参数:
            target: 目标部件
        
        返回:
            QPoint: 计算的位置
        """
        w = self.flyout  # 获取浮窗
        pos = target.mapToGlobal(QPoint(0, 0))  # 将目标部件原点转换为全局坐标
        # 计算目标左侧位置
        x = pos.x() - w.sizeHint().width() + 8
        # 计算垂直居中位置
        y = pos.y() - w.sizeHint().height()//2 + target.height()//2 + w.layout().contentsMargins().top()
        return QPoint(x, y)  # 返回计算的位置

    def exec(self, pos: QPoint):
        """执行向左滑动动画
        
        参数:
            pos: 目标位置
        """
        pos = self._adjustPosition(pos)  # 调整位置确保在屏幕内
        self.slideAni.setStartValue(pos+QPoint(8, 0))  # 设置起始位置（目标右侧8像素）
        self.slideAni.setEndValue(pos)  # 设置结束位置（目标位置）
        self.aniGroup.start()  # 开始动画


@FlyoutAnimationManager.register(FlyoutAnimationType.SLIDE_RIGHT)
class SlideRightFlyoutAnimationManager(FlyoutAnimationManager):
    """ 向右滑动浮窗动画管理器 """

    def position(self, target: QWidget):
        """计算向右滑动动画的起始位置
        
        参数:
            target: 目标部件
        
        返回:
            QPoint: 计算的位置
        """
        w = self.flyout  # 获取浮窗
        pos = target.mapToGlobal(QPoint(0, 0))  # 将目标部件原点转换为全局坐标
        # 计算目标右侧位置
        x = pos.x() + target.width() - 8
        # 计算垂直居中位置
        y = pos.y() - w.sizeHint().height()//2 + target.height()//2 + w.layout().contentsMargins().top()
        return QPoint(x, y)  # 返回计算的位置

    def exec(self, pos: QPoint):
        """执行向右滑动动画
        
        参数:
            pos: 目标位置
        """
        pos = self._adjustPosition(pos)  # 调整位置确保在屏幕内
        self.slideAni.setStartValue(pos-QPoint(8, 0))  # 设置起始位置（目标左侧8像素）
        self.slideAni.setEndValue(pos)  # 设置结束位置（目标位置）
        self.aniGroup.start()  # 开始动画


@FlyoutAnimationManager.register(FlyoutAnimationType.FADE_IN)
class FadeInFlyoutAnimationManager(FlyoutAnimationManager):
    """ 淡入浮窗动画管理器 """

    def position(self, target: QWidget):
        """计算淡入动画的起始位置
        
        参数:
            target: 目标部件
        
        返回:
            QPoint: 计算的位置
        """
        w = self.flyout  # 获取浮窗
        pos = target.mapToGlobal(QPoint())  # 将目标部件原点转换为全局坐标
        # 计算水平居中位置
        x = pos.x() + target.width()//2 - w.sizeHint().width()//2
        # 计算目标上方位置
        y = pos.y() - w.sizeHint().height() + w.layout().contentsMargins().bottom()
        return QPoint(x, y)  # 返回计算的位置

    def exec(self, pos: QPoint):
        """执行淡入动画
        
        参数:
            pos: 目标位置
        """
        self.flyout.move(self._adjustPosition(pos))  # 移动浮窗到目标位置
        self.aniGroup.removeAnimation(self.slideAni)  # 移除滑动动画（只使用淡入）
        self.aniGroup.start()  # 开始动画


@FlyoutAnimationManager.register(FlyoutAnimationType.NONE)
class DummyFlyoutAnimationManager(FlyoutAnimationManager):
    """ 无动画浮窗动画管理器 """

    def exec(self, pos: QPoint):
        """直接显示浮窗（无动画）
        
        参数:
            pos: 目标位置
        """
        self.flyout.move(self._adjustPosition(pos))  # 移动浮窗到目标位置

    def position(self, target: QWidget):
        """计算浮窗位置
        
        参数:
            target: 目标部件
        
        返回:
            QPoint: 计算的位置
        """
        m = self.flyout.hBoxLayout.contentsMargins()  # 获取浮窗布局边距
        # 计算目标上方位置
        return target.mapToGlobal(QPoint(-m.left(), -self.flyout.sizeHint().height()+m.bottom()-8))