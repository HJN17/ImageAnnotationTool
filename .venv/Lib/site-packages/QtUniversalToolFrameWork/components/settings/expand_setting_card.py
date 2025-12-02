# coding:utf-8
from typing import List, Union
from PyQt5.QtCore import QEvent, Qt, QPropertyAnimation, pyqtProperty, QEasingCurve, QRectF
from PyQt5.QtGui import QColor, QPainter, QIcon, QPainterPath
from PyQt5.QtWidgets import QFrame, QWidget, QAbstractButton, QApplication, QScrollArea, QVBoxLayout

from ...common.config import isDarkTheme
from ...common.icon import FluentIcon as FIF
from ...common.style_sheet import FluentStyleSheet

from .setting_card import SettingCard


class ExpandButton(QAbstractButton):
    """ 
    展开按钮组件
    
    用于控制设置卡片的展开和折叠状态，继承自QAbstractButton。
    包含旋转动画效果，点击时会旋转180度并触发展开/折叠操作，支持悬停和按下状态的样式变化。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        
        self.__angle = 0    # 初始化旋转角度为0度（未展开状态）
        self.isHover = False
        self.isPressed = False
        self.rotateAni = QPropertyAnimation(self, b'angle', self) # 创建旋转动画对象，绑定angle属性
        self.clicked.connect(self.__onClicked)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |  QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        r = 255 if isDarkTheme() else 0
        color = Qt.transparent

        if self.isEnabled():
            if self.isPressed:
                color = QColor(r, r, r, 10)
            elif self.isHover:
                color = QColor(r, r, r, 14)
        else:
            painter.setOpacity(0.36)

        painter.setBrush(color)
        painter.drawRoundedRect(self.rect(), 4, 4)

        painter.translate(self.width()//2, self.height()//2)
        painter.rotate(self.__angle)
        FIF.ARROW_DOWN.render(painter, QRectF(-5, -5, 9.6, 9.6))

    def enterEvent(self, e):
        self.setHover(True)

    def leaveEvent(self, e):
        self.setHover(False)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.setPressed(True)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.setPressed(False)

    def setHover(self, isHover: bool):
        self.isHover = isHover
        self.update()

    def setPressed(self, isPressed: bool):
        self.isPressed = isPressed
        self.update()

    def __onClicked(self):
        self.setExpand(self.angle < 180)

    def setExpand(self, isExpand: bool):
        self.rotateAni.stop()  # 停止当前动画（若正在运行）
        self.rotateAni.setEndValue(180 if isExpand else 0)
        self.rotateAni.setDuration(200)  # 动画持续时间200毫秒
        self.rotateAni.start()  # 启动动画

    def getAngle(self):
        return self.__angle

    def setAngle(self, angle):
        self.__angle = angle
        self.update()

    angle = pyqtProperty(float, getAngle, setAngle)


class SpaceWidget(QWidget):
    """ 
    间隔占位组件
    
    用于在布局中创建固定高度的透明间隔，通常用于分隔不同区域或调整布局间距。
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(1)


class HeaderSettingCard(SettingCard):
    """ 
    头部设置卡片组件
    
    作为可展开设置卡片的标题区域，继承自基础设置卡片(SettingCard)，
    包含标题、内容描述、展开按钮及自定义交互区域，支持鼠标事件过滤。
    """

    def __init__(self, icon, title, content=None, parent=None):
        # 调用父类SettingCard构造方法，传入图标、标题、内容和父部件
        super().__init__(icon, title, content, parent)
        # 创建展开按钮并设置为当前卡片的子部件
        self.expandButton = ExpandButton(self)

        # 将展开按钮添加到水平布局中，靠右对齐
        self.hBoxLayout.addWidget(self.expandButton, 0, Qt.AlignRight)
        # 添加右侧间距（8像素）
        self.hBoxLayout.addSpacing(8)

        # 为标题标签设置对象名（用于样式表选择）
        self.titleLabel.setObjectName("titleLabel")
        # 为当前卡片安装事件过滤器（监控鼠标事件）
        self.installEventFilter(self)

    def eventFilter(self, obj, e):
        # 事件过滤器：处理当前卡片的鼠标事件，同步到展开按钮
        if obj is self:
            if e.type() == QEvent.Enter:
                # 鼠标进入卡片：设置展开按钮为悬停状态
                self.expandButton.setHover(True)
            elif e.type() == QEvent.Leave:
                # 鼠标离开卡片：取消展开按钮悬停状态
                self.expandButton.setHover(False)
            elif e.type() == QEvent.MouseButtonPress and e.button() == Qt.LeftButton:
                # 鼠标左键按下：设置展开按钮为按下状态
                self.expandButton.setPressed(True)
            elif e.type() == QEvent.MouseButtonRelease and e.button() == Qt.LeftButton:
                # 鼠标左键释放：取消展开按钮按下状态并触发点击
                self.expandButton.setPressed(False)
                self.expandButton.click()

        # 调用父类事件过滤逻辑
        return super().eventFilter(obj, e)

    def addWidget(self, widget: QWidget):
        """ 
        向卡片右侧添加自定义部件
        
        将部件插入到展开按钮左侧，用于显示额外的交互元素（如开关、下拉框等）。
        
        参数:
            widget (QWidget): 要添加的自定义部件
        """
        # 获取水平布局中的部件数量
        N = self.hBoxLayout.count()
        # 移除布局中最后一个项目（原右侧间距）
        self.hBoxLayout.removeItem(self.hBoxLayout.itemAt(N - 1))
        # 添加自定义部件，靠右对齐
        self.hBoxLayout.addWidget(widget, 0, Qt.AlignRight)
        # 添加部件与展开按钮之间的间距（19像素）
        self.hBoxLayout.addSpacing(19)
        # 重新添加展开按钮，靠右对齐
        self.hBoxLayout.addWidget(self.expandButton, 0, Qt.AlignRight)
        # 添加右侧最终间距（8像素）
        self.hBoxLayout.addSpacing(8)

    def paintEvent(self, e):
        # 绘制卡片背景和边框
        painter = QPainter(self)
        # 启用抗锯齿渲染
        painter.setRenderHints(QPainter.Antialiasing)
        # 不绘制边框
        painter.setPen(Qt.NoPen)

        # 根据主题模式设置背景色（深色主题：白色半透明；浅色主题：白色更高透明度）
        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))

        # 获取父部件（应为ExpandSettingCard类型）
        p = self.parent()  # type: ExpandSettingCard
        # 创建绘制路径
        path = QPainterPath()
        # 设置填充规则为缠绕填充（确保圆角矩形正确填充）
        path.setFillRule(Qt.WindingFill)
        # 添加调整后的圆角矩形路径（向内缩进1像素，避免边缘溢出）
        path.addRoundedRect(QRectF(self.rect().adjusted(1, 1, -1, -1)), 6, 6)

        # 若父部件处于展开状态，将底部圆角设置为0（与内容区域无缝连接）
        if hasattr(p, 'isExpand') and p.isExpand:
            path.addRect(1, self.height() - 8, self.width() - 2, 8)

        # 绘制简化后的路径（合并圆角矩形和底部矩形）
        painter.drawPath(path.simplified())


class ExpandBorderWidget(QWidget):
    """ 
    展开设置卡片的边框部件
    
    用于绘制可展开卡片的边框和分隔线，随父部件（ExpandSettingCard）大小变化而调整，
    忽略鼠标事件以不干扰底层交互。
    """

    def __init__(self, parent=None):
        # 调用父类QWidget构造方法
        super().__init__(parent=parent)
        # 设置鼠标事件透明（允许事件穿透到下层部件）
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        # 为父部件安装事件过滤器（监控大小变化）
        parent.installEventFilter(self)

    def eventFilter(self, obj, e):
        # 事件过滤器：当父部件大小变化时，同步调整自身大小
        if obj is self.parent() and e.type() == QEvent.Resize:
            self.resize(e.size())

        # 调用父类事件过滤逻辑
        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        # 绘制边框和分隔线
        painter = QPainter(self)
        # 启用抗锯齿渲染
        painter.setRenderHints(QPainter.Antialiasing)
        # 不填充背景
        painter.setBrush(Qt.NoBrush)

        # 根据主题模式设置边框颜色（深色主题：黑色半透明；浅色主题：黑色更低透明度）
        if isDarkTheme():
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setPen(QColor(0, 0, 0, 19))

        # 获取父部件（ExpandSettingCard类型）
        p = self.parent()  # type: ExpandSettingCard
        r, d = 6, 12  # 圆角半径和分隔线相关参数（未直接使用，保留用于扩展）
        ch, h, w = p.card.height(), self.height(), self.width()  # 卡片高度、自身高度、宽度

        # 绘制圆角矩形边框（仅在未展开状态显示完整圆角）
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)

        # 若卡片高度小于自身高度（即展开状态），绘制卡片底部的分隔线
        if ch < h:
            painter.drawLine(1, ch, w - 1, ch)

class ExpandSettingCard(QScrollArea):

    """ 
    可展开的设置卡片组件
    
    继承自QScrollArea，支持展开/折叠内容区域，包含头部卡片（HeaderSettingCard）、
    内容视图区域和展开动画效果，用于展示需要分类或隐藏的复杂设置项。

    """

    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str = None, parent=None):
        # 调用父类QScrollArea构造方法
        super().__init__(parent=parent)
        # 初始化展开状态为False（折叠）
        self.isExpand = False

        # 创建内部部件和布局
        self.scrollWidget = QFrame(self)  # 滚动区域的容器部件
        self.view = QFrame(self.scrollWidget)  # 内容视图部件（存放展开内容）
        self.card = HeaderSettingCard(icon, title, content, self)  # 头部卡片

        self.scrollLayout = QVBoxLayout(self.scrollWidget)  # 滚动容器的垂直布局
        self.viewLayout = QVBoxLayout(self.view)  # 内容视图的垂直布局
        self.spaceWidget = SpaceWidget(self.scrollWidget)  # 间隔占位部件（控制展开高度）
        self.borderWidget = ExpandBorderWidget(self)  # 边框绘制部件

        # 创建展开动画（控制滚动条位置实现平滑展开/折叠）
        self.expandAni = QPropertyAnimation(self.verticalScrollBar(), b'value', self)

        # 初始化部件
        self.__initWidget()

    def __initWidget(self):
        """ 初始化所有部件和布局的属性、样式及信号连接 """
        # 设置滚动区域的widget为scrollWidget
        self.setWidget(self.scrollWidget)
        # 设置widget大小可调整
        self.setWidgetResizable(True)
        # 设置初始固定高度为头部卡片高度（折叠状态）
        self.setFixedHeight(self.card.height())
        # 设置视口边距：顶部为头部卡片高度（使头部固定在顶部），其他方向为0
        self.setViewportMargins(0, self.card.height(), 0, 0)
        # 禁用垂直和水平滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 初始化滚动布局：无边距、无间距
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(0)
        # 添加内容视图和间隔部件到滚动布局
        self.scrollLayout.addWidget(self.view)
        self.scrollLayout.addWidget(self.spaceWidget)

        # 初始化展开动画：设置缓动曲线（OutQuad：先快后慢）和持续时间（200毫秒）
        self.expandAni.setEasingCurve(QEasingCurve.OutQuad)
        self.expandAni.setDuration(200)

        # 设置对象名（用于样式表选择）
        self.view.setObjectName('view')
        self.scrollWidget.setObjectName('scrollWidget')
        # 设置展开状态属性（用于样式表动态调整）
        self.setProperty('isExpand', False)
        # 应用样式表
        FluentStyleSheet.EXPAND_SETTING_CARD.apply(self.card)
        FluentStyleSheet.EXPAND_SETTING_CARD.apply(self)

        # 安装事件过滤器和信号连接
        self.card.installEventFilter(self)
        # 动画值变化时调整卡片高度
        self.expandAni.valueChanged.connect(self._onExpandValueChanged)
        # 头部展开按钮点击时切换展开状态
        self.card.expandButton.clicked.connect(self.toggleExpand)

    def addWidget(self, widget: QWidget):
        """ 
        向头部卡片添加自定义部件
        
        将部件添加到头部卡片的右侧（展开按钮左侧），用于显示与标题相关的快捷控件。
        
        参数:
            widget (QWidget): 要添加的自定义部件
        """
        self.card.addWidget(widget)
        # 调整内容视图大小
        self._adjustViewSize()

    def wheelEvent(self, e):
        # 重写滚轮事件：禁止滚动（内容区域通过展开/折叠控制，无需滚轮）
        pass

    def setExpand(self, isExpand: bool):
        """ 
        设置卡片的展开状态
        
        根据目标状态切换展开/折叠，并启动相应的动画效果，更新样式和布局。
        
        参数:
            isExpand (bool): True表示展开，False表示折叠
        """
        # 若当前状态与目标状态一致，直接返回
        if self.isExpand == isExpand:
            return

        # 调整内容视图大小
        self._adjustViewSize()

        # 更新展开状态和样式属性
        self.isExpand = isExpand
        self.setProperty('isExpand', isExpand)
        self.setStyle(QApplication.style())  # 刷新样式

        # 启动展开/折叠动画
        if isExpand:
            # 展开：获取内容视图的高度，设置动画从最大滚动值到0（滚动到顶部）
            h = self.viewLayout.sizeHint().height()
            self.verticalScrollBar().setValue(h)
            self.expandAni.setStartValue(h)
            self.expandAni.setEndValue(0)
        else:
            # 折叠：动画从0滚动到最大滚动值（隐藏内容）
            self.expandAni.setStartValue(0)
            self.expandAni.setEndValue(self.verticalScrollBar().maximum())

        # 启动动画并更新展开按钮状态
        self.expandAni.start()
        self.card.expandButton.setExpand(isExpand)

    def toggleExpand(self):
        """ 切换卡片的展开/折叠状态 """
        self.setExpand(not self.isExpand)

    def resizeEvent(self, e):
        # 大小变化事件：调整头部卡片和滚动容器的宽度为当前卡片宽度
        self.card.resize(self.width(), self.card.height())
        self.scrollWidget.resize(self.width(), self.scrollWidget.height())

    def _onExpandValueChanged(self):
        """ 展开动画值变化时的回调：调整卡片的固定高度 """
        # 获取内容视图的高度
        vh = self.viewLayout.sizeHint().height()
        # 获取视口顶部边距（头部卡片高度）
        h = self.viewportMargins().top()
        # 设置卡片高度为：头部高度 + 内容高度 - 当前滚动值（实现平滑过渡）
        self.setFixedHeight(max(h + vh - self.verticalScrollBar().value(), h))

    def _adjustViewSize(self):
        """ 调整内容视图和间隔部件的高度，以适应内容大小 """
        # 设置间隔部件高度为内容视图的建议高度（控制展开后的总高度）
        h = self.viewLayout.sizeHint().height()
        self.spaceWidget.setFixedHeight(h)

        # 若处于展开状态，直接设置卡片高度为头部高度+内容高度
        if self.isExpand:
            self.setFixedHeight(self.card.height()+h)


class GroupSeparator(QWidget):
    """ 
    组分隔线部件
    
    用于在展开内容区域中分隔不同组别的设置项，显示为一条水平细线。
    """

    def __init__(self, parent=None):
        # 调用父类QWidget构造方法
        super().__init__(parent=parent)
        # 设置固定高度为3像素（分隔线高度）
        self.setFixedHeight(3)

    def paintEvent(self, e):
        # 绘制分隔线
        painter = QPainter(self)
        # 启用抗锯齿渲染
        painter.setRenderHints(QPainter.Antialiasing)

        # 根据主题模式设置分隔线颜色（深色主题：黑色半透明；浅色主题：黑色更低透明度）
        if isDarkTheme():
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setPen(QColor(0, 0, 0, 19))

        # 绘制水平线（从左到右，y坐标为1像素）
        painter.drawLine(0, 1, self.width(), 1)


class ExpandGroupSettingCard(ExpandSettingCard):
    """ 
    带分组的可展开设置卡片
    
    继承自ExpandSettingCard，支持向内容区域添加带分隔线的分组部件，
    自动管理组间分隔线的显示和布局。
    """

    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str = None, parent=None):
        # 调用父类ExpandSettingCard构造方法
        super().__init__(icon, title, content, parent=parent)
        # 存储添加的组部件列表
        self.widgets = []   # type: List[QWidget]

        # 初始化内容视图布局：无边距、无间距
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

    def addGroupWidget(self, widget: QWidget):
        """ 
        向内容区域添加带分隔线的组部件
        
        在内容视图中添加部件，并在非首个部件前自动插入分隔线（GroupSeparator）。
        
        参数:
            widget (QWidget): 要添加的组部件
        """
        # 若布局中已有部件，先添加分隔线
        if self.viewLayout.count() >= 1:
            self.viewLayout.addWidget(GroupSeparator(self.view))

        # 设置部件的父部件为内容视图
        widget.setParent(self.view)
        # 添加部件到列表和布局
        self.widgets.append(widget)
        self.viewLayout.addWidget(widget)
        # 调整视图大小
        self._adjustViewSize()

    def removeGroupWidget(self, widget: QWidget):
        """ 
        从内容区域移除组部件及关联的分隔线
        
        移除指定部件，并删除其前后的分隔线（若存在），调整布局和视图大小。
        
        参数:
            widget (QWidget): 要移除的组部件
        """
        # 若部件不在列表中，直接返回
        if widget not in self.widgets:
            return

        # 获取部件在布局中的索引和在列表中的索引
        layoutIndex = self.viewLayout.indexOf(widget)
        index = self.widgets.index(widget)

        # 从布局和列表中移除部件
        self.viewLayout.removeWidget(widget)
        self.widgets.remove(widget)

        # 若列表为空，调整视图大小后返回
        if not self.widgets:
            return self._adjustViewSize()

        # 移除分隔线：若部件前有分隔线（布局索引>0），移除前一个分隔线
        if layoutIndex >= 1:
            separator = self.viewLayout.itemAt(layoutIndex - 1).widget()
            separator.deleteLater()  # 删除分隔线部件
            self.viewLayout.removeWidget(separator)
        # 若部件是列表首个且布局中仍有分隔线，移除首个分隔线
        elif index == 0:
            separator = self.viewLayout.itemAt(0).widget()
            separator.deleteLater()
            self.viewLayout.removeWidget(separator)

        # 调整视图大小
        self._adjustViewSize()

    def _adjustViewSize(self):
        """ 调整内容视图和间隔部件的高度（基于所有组部件的高度总和） """
        # 计算所有组部件的高度总和（每个部件高度+3像素分隔线高度）
        h = sum(w.sizeHint().height() + 3 for w in self.widgets)
        # 设置间隔部件高度为总和（控制展开高度）
        self.spaceWidget.setFixedHeight(h)

        # 若处于展开状态，更新卡片高度
        if self.isExpand:
            self.setFixedHeight(self.card.height()+h)


class SimpleExpandGroupSettingCard(ExpandGroupSettingCard):
    """ 
    简化的带分组可展开设置卡片
    
    继承自ExpandGroupSettingCard，重写了调整视图大小的逻辑，
    直接使用布局的建议高度而非手动计算组部件总和。
    """

    def _adjustViewSize(self):
        """ 调整视图大小（使用布局的建议高度） """
        # 获取内容视图布局的建议高度
        h = self.viewLayout.sizeHint().height()
        # 设置间隔部件高度为布局建议高度
        self.spaceWidget.setFixedHeight(h)

        # 若处于展开状态，更新卡片高度
        if self.isExpand:
            self.setFixedHeight(self.card.height()+h)
