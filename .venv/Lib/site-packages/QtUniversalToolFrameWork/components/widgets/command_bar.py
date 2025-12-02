from typing import Iterable, List, Tuple, Union

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRectF, QRect, QPoint, QEvent
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QHoverEvent, QPainterPath
from PyQt5.QtWidgets import QAction, QLayoutItem, QWidget, QFrame, QHBoxLayout, QApplication

from ...common.font import setFont
from ...common.icon import FluentIcon, Icon, Action
from ...common.style_sheet import isDarkTheme,setStyleSheet

from .menu import RoundMenu, MenuAnimationType
from .button import TransparentToggleToolButton, CustomStandardButton
from .tool_tip import ToolTipFilter
from .flyout import FlyoutViewBase, Flyout


class CommandButton(CustomStandardButton):
    """
    命令按钮组件
    
    构造函数:
    ------------
    * CommandButton(`parent`: QWidget = None) - 创建无图标命令按钮
    * CommandButton(`icon`: QIcon | str | FluentIconBase = None, `parent`: QWidget = None) - 创建带图标的命令按钮
    """

    def _postInit(self):
        super()._postInit()
        self.setCheckable(False) # 设置按钮不可选中
        self.setToolButtonStyle(Qt.ToolButtonIconOnly) # 设置工具按钮样式为仅显示图标
        setFont(self)
        self._text = '' # 初始化文本内容为空
        self._action = None # 初始化动作对象为空
        
        self._isTight = False   # 初始化紧凑模式标志为False

    def setTight(self, isTight: bool):
        self._isTight = isTight
        self.update()

    def isTight(self):
        return self._isTight

    def sizeHint(self) -> QSize:
        """ 
        如果按钮仅显示图标，则根据是否为紧凑模式返回不同大小
        """
        if self.isIconOnly():   # 如果按钮仅显示图标
            return QSize(36, 32) if self.isTight() else QSize(48, 32)

        # 获取文本宽度
        tw = self.fontMetrics().width(self.text())

        # 根据工具按钮样式返回不同大小
        style = self.toolButtonStyle()
        if style == Qt.ToolButtonTextBesideIcon: # 如果工具按钮样式为文本BesideIcon
            return QSize(tw + 47, 32)
        if style == Qt.ToolButtonTextOnly: # 如果工具按钮样式为文本Only
            return QSize(tw + 32, 32)

        return QSize(tw + 32, 50)

    def isIconOnly(self):
        if not self.text():
            return True

        return self.toolButtonStyle() in [Qt.ToolButtonIconOnly, Qt.ToolButtonFollowStyle]

    def _drawIcon(self, icon, painter, rect):
        pass

    def text(self):
        # 获取按钮文本
        return self._text

    def setText(self, text: str):
        # 设置按钮文本
        self._text = text
        # 触发重绘
        self.update()

    def setAction(self, action: QAction):
        # 设置按钮关联的动作
        self._action = action
        
        self._onActionChanged()

        self.clicked.connect(action.trigger)    # 连接按钮点击信号到动作的触发槽
        
        action.toggled.connect(self.setChecked) # 连接动作的选中状态变化到按钮的选中状态
        
        action.changed.connect(self._onActionChanged)   # 连接动作的属性变化到按钮的更新方法

        # 安装自定义的工具提示过滤器，延迟700毫秒显示
        self.installEventFilter(CommandToolTipFilter(self, 700))

    def _onActionChanged(self):
        action = self.action()  # 获取关联的动作
        self.setIcon(action.icon())  # 同步动作的图标到按钮
        self.setText(action.text()) # 同步动作的文本到按钮
        self.setToolTip(action.toolTip())   # 同步动作的工具提示到按钮
        self.setEnabled(action.isEnabled()) # 同步动作的启用状态到按钮
        self.setCheckable(action.isCheckable()) # 同步动作的可选中状态到按钮
        self.setChecked(action.isChecked()) # 同步动作的选中状态到按钮

    def action(self):
        return self._action

    def paintEvent(self, e):
        # 调用父类的绘制事件处理
        super().paintEvent(e)

        # 创建绘制器
        painter = QPainter(self)
        # 设置渲染提示：抗锯齿和平滑像素变换
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        # 根据按钮状态设置画笔颜色
        if not self.isChecked():
            # 未选中时，根据当前主题设置文本颜色
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        else:
            # 选中时，根据当前主题设置相反的文本颜色
            painter.setPen(Qt.black if isDarkTheme() else Qt.white)

        # 根据按钮状态设置透明度
        if not self.isEnabled():
            # 禁用状态下透明度为0.43
            painter.setOpacity(0.43)
        elif self.isPressed:
            # 按下状态下透明度为0.63
            painter.setOpacity(0.63)

        # 绘制图标和文本
        style = self.toolButtonStyle()
        iw, ih = self.iconSize().width(), self.iconSize().height()

        if self.isIconOnly():
            # 仅显示图标的情况
            y = (self.height() - ih) / 2
            x = (self.width() - iw) / 2
            super()._drawIcon(self._icon, painter, QRectF(x, y, iw, ih))
        elif style == Qt.ToolButtonTextOnly:
            # 仅显示文本的情况
            painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        elif style == Qt.ToolButtonTextBesideIcon:
            # 文本在图标旁边的情况
            y = (self.height() - ih) / 2
            super()._drawIcon(self._icon, painter, QRectF(9, y, iw, ih))

            rect = QRectF(24, 0, self.width() - 26, self.height())
            painter.drawText(rect, Qt.AlignCenter, self.text())
        elif style == Qt.ToolButtonTextUnderIcon:
            # 文本在图标下方的情况
            x = (self.width() - iw) / 2
            super()._drawIcon(self._icon, painter, QRectF(x, 9, iw, ih))

            rect = QRectF(0, ih + 13, self.width(), self.height() - ih - 13)
            painter.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, self.text())


class CommandToolTipFilter(ToolTipFilter):
    """
    命令按钮的工具提示过滤器
    仅在按钮仅显示图标的情况下才显示工具提示
    """

    def _canShowToolTip(self) -> bool:
        # 调用父类的方法并检查按钮是否仅显示图标
        return super()._canShowToolTip() and self.parent().isIconOnly()


class MoreActionsButton(CommandButton):
    """
    更多操作按钮
    用于显示隐藏的操作菜单
    """

    def _postInit(self):
        super()._postInit()
        self.setIcon(FluentIcon.MORE)

    def sizeHint(self):
        return QSize(40, 28)


class CommandSeparator(QWidget):
    """
    命令栏分隔符
    在命令按钮之间显示分隔线
    """

    def __init__(self, parent=None):
        # 初始化父类
        super().__init__(parent)
        # 设置固定大小
        self.setFixedSize(9, 28)

    def paintEvent(self, e):
        # 创建绘制器
        painter = QPainter(self)
        # 根据当前主题设置分隔线颜色
        painter.setPen(QColor(255, 255, 255, 21)
                       if isDarkTheme() else QColor(0, 0, 0, 15))
        # 绘制垂直线
        painter.drawLine(5, 2, 5, self.height() - 4)


class CommandMenu(RoundMenu):
    """
    命令菜单
    用于显示命令栏中的更多操作
    """

    def __init__(self, parent=None):
        # 初始化父类，标题为空字符串
        super().__init__("", parent)
        # 设置菜单项高度
        self.setItemHeight(32)
        # 设置菜单项图标大小
        self.view.setIconSize(QSize(16, 16))


class CommandBar(QFrame):
    """
    命令栏组件
    用于显示一系列命令按钮，支持自动隐藏溢出的按钮到"更多"菜单中
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        self._widgets = []  # 存储所有添加到命令栏的控件
        self._hiddenWidgets = []  # 存储当前隐藏的控件
        self._hiddenActions = []  # 存储始终隐藏的动作

        self._menuAnimation = MenuAnimationType.DROP_DOWN    # 设置菜单动画类型为下拉 
        self._toolButtonStyle = Qt.ToolButtonIconOnly   # 设置工具按钮样式为仅显示图标
        self._iconSize = QSize(16, 16)  # 设置图标大小   
        self._isButtonTight = False # 设置按钮是否为紧凑模式
        self._spacing = 2   # 设置控件间距
        self.moreButton = MoreActionsButton(self)   # 创建"更多"按钮
        self.moreButton.clicked.connect(self._showMoreActionsMenu)  # 连接"更多"按钮的点击信号到显示菜单的槽
        self.moreButton.hide()  # 初始隐藏"更多"按钮
        setFont(self, 12)   # 设置字体大小为12
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置透明背景

    def setSpacing(self, spacing: int):
        """设置控件间距"""
        # 如果间距值未变化则直接返回
        if spacing == self._spacing:
            return

        self._spacing = spacing
        # 更新几何布局
        self.updateGeometry()

    def spacing(self):
        """返回当前间距值"""
        return self._spacing

    def addAction(self, action: QAction):
        """
        添加动作到命令栏
        
        参数:
        ----------
        action: QAction
            要添加的动作对象
        """
        # 如果动作已存在则直接返回
        if action in self.actions():
            return

        # 创建按钮并关联动作
        button = self._createButton(action)
        self._insertWidgetToLayout(-1, button)
        super().addAction(action)
        return button

    def addActions(self, actions: Iterable[QAction]):
        # 批量添加多个动作
        for action in actions:
            self.addAction(action)

    def addHiddenAction(self, action: QAction):
        """
        添加隐藏的动作（仅在"更多"菜单中显示）
        """
        # 如果动作已存在则直接返回
        if action in self.actions():
            return

        # 将动作添加到隐藏动作列表
        self._hiddenActions.append(action)
        # 更新几何布局
        self.updateGeometry()
        # 调用父类方法添加动作
        super().addAction(action)

    def addHiddenActions(self, actions: List[QAction]):
        """
        批量添加隐藏的动作
        """
        for action in actions:
            self.addHiddenAction(action)

    def insertAction(self, before: QAction, action: QAction):

        if before not in self.actions():
            return

        # 获取参考动作的索引
        index = self.actions().index(before)
        # 创建按钮并关联动作
        button = self._createButton(action)
        # 在参考动作位置插入新按钮
        self._insertWidgetToLayout(index, button)
        # 调用父类方法插入动作
        super().insertAction(before, action)
        # 返回创建的按钮
        return button

    def addSeparator(self):
        # 在末尾添加分隔符
        self.insertSeparator(-1)

    def insertSeparator(self, index: int):
        # 在指定位置插入分隔符
        self._insertWidgetToLayout(index, CommandSeparator(self))

    def addWidget(self, widget: QWidget):
        """
        向命令栏添加自定义控件
        """
        # 将控件添加到布局末尾
        self._insertWidgetToLayout(-1, widget)

    def removeAction(self, action: QAction):
        # 如果动作不存在则直接返回
        if action not in self.actions():
            return

        # 遍历所有命令按钮
        for w in self.commandButtons:
            # 查找关联了该动作的按钮
            if w.action() is action:
                # 从控件列表中移除
                self._widgets.remove(w)
                # 隐藏按钮
                w.hide()
                # 安排按钮稍后删除
                w.deleteLater()
                break

        # 更新几何布局
        self.updateGeometry()

    def removeWidget(self, widget: QWidget):
        # 如果控件不在列表中则直接返回
        if widget not in self._widgets:
            return

        # 从控件列表中移除
        self._widgets.remove(widget)
        # 更新几何布局
        self.updateGeometry()

    def removeHiddenAction(self, action: QAction):
        # 如果动作在隐藏列表中则移除
        if action in self._hiddenActions:
            self._hiddenActions.remove(action)

    def setToolButtonStyle(self, style: Qt.ToolButtonStyle):
        """
        设置工具按钮的显示样式
        """
        # 如果样式未变化则直接返回
        if self.toolButtonStyle() == style:
            return

        # 更新样式
        self._toolButtonStyle = style
        # 为所有命令按钮应用新样式
        for w in self.commandButtons:
            w.setToolButtonStyle(style)

    def toolButtonStyle(self):
        # 返回当前工具按钮样式
        return self._toolButtonStyle

    def setButtonTight(self, isTight: bool):
        # 如果紧凑模式状态未变化则直接返回
        if self.isButtonTight() == isTight:
            return

        # 更新紧凑模式状态
        self._isButtonTight = isTight

        # 为所有命令按钮应用紧凑模式
        for w in self.commandButtons:
            w.setTight(isTight)

        # 更新几何布局
        self.updateGeometry()

    def isButtonTight(self):
        # 返回当前是否为紧凑模式
        return self._isButtonTight

    def setIconSize(self, size: QSize):
        # 如果图标大小未变化则直接返回
        if size == self._iconSize:
            return

        # 更新图标大小
        self._iconSize = size
        # 为所有命令按钮应用新图标大小
        for w in self.commandButtons:
            w.setIconSize(size)

    def iconSize(self):
        # 返回当前图标大小
        return self._iconSize

    def resizeEvent(self, e):
        # 当控件大小变化时更新几何布局
        self.updateGeometry()

    def _createButton(self, action: QAction):
        """
        创建命令按钮
        """
        # 创建命令按钮
        button = CommandButton(self)
        
        button.setAction(action)
        button.setToolButtonStyle(self.toolButtonStyle())
        button.setTight(self.isButtonTight())
        button.setIconSize(self.iconSize())
        button.setFont(self.font())
        return button

    def _insertWidgetToLayout(self, index: int, widget: QWidget):
        """
        向布局添加控件
        """
        # 设置控件的父对象
        widget.setParent(self)
        # 显示控件
        widget.show()

        # 根据索引添加控件到列表
        if index < 0:
            # 索引为负表示添加到末尾
            self._widgets.append(widget)
        else:
            # 在指定索引位置插入控件
            self._widgets.insert(index, widget)

        # 设置命令栏的高度为所有控件中的最大高度
        self.setFixedHeight(max(w.height() for w in self._widgets))
        # 更新几何布局
        self.updateGeometry()

    def minimumSizeHint(self) -> QSize:
        # 返回最小大小提示（仅包含"更多"按钮的大小）
        return self.moreButton.size()

    def updateGeometry(self):
        """更新几何布局"""
        self._hiddenWidgets.clear() # 清空隐藏控件列表
        self.moreButton.hide()  # 隐藏"更多"按钮
        visibles = self._visibleWidgets()   # 获取可见控件列表
        x = self.contentsMargins().left()   # 初始化X坐标为内容边距的左边距
        h = self.height()   # 获取命令栏高度

        # 布局可见控件
        for widget in visibles:
            widget.show()
            widget.move(x, (h - widget.height()) // 2)  # 计算Y坐标使控件垂直居中
            x += (widget.width() + self.spacing())  # 更新X坐标，为下一个控件留出空间

        # 如果有隐藏动作或控件未全部显示，则显示"更多"按钮
        if self._hiddenActions or len(visibles) < len(self._widgets):
            self.moreButton.show()  # 显示"更多"按钮
            self.moreButton.move(x, (h - self.moreButton.height()) // 2)  # 计算"更多"按钮的位置使其垂直居中

        # 隐藏超出空间的控件
        for widget in self._widgets[len(visibles):]:
            widget.hide()
            self._hiddenWidgets.append(widget)  # 将隐藏的控件添加到隐藏列表

    def _visibleWidgets(self) -> List[QWidget]:
        """
        返回布局中可见的控件列表
        """
        # 如果有足够空间显示所有控件
        if self.suitableWidth() <= self.width():
            return self._widgets

        # 计算可显示的控件数量
        w = self.moreButton.width() # 初始化宽度为"更多"按钮宽度
        for index, widget in enumerate(self._widgets):
            w += widget.width()
            if index > 0:
                w += self.spacing()

            if w > self.width():     # 如果超出宽度限制则停止
                break

        # 返回可显示的控件
        return self._widgets[:index]

    def suitableWidth(self):
        """计算显示所有控件所需的宽度"""
        
        widths = [w.width() for w in self._widgets] # 计算所有控件的宽度
        if self._hiddenActions:
            widths.append(self.moreButton.width())

        # 返回总宽度，包括所有控件宽度和间距
        return sum(widths) + self.spacing() * max(len(widths) - 1, 0)

    def resizeToSuitableWidth(self):
        """将命令栏调整为适合的宽度"""
        self.setFixedWidth(self.suitableWidth())

    def setFont(self, font: QFont):
        """设置命令栏字体"""
        super().setFont(font)
        # 为所有命令按钮应用相同的字体
        for button in self.commandButtons:
            button.setFont(font)

    @property
    def commandButtons(self):
        """返回所有命令按钮控件"""
        return [w for w in self._widgets if isinstance(w, CommandButton)]

    def setMenuDropDown(self, down: bool):
        """
        设置"更多"菜单的动画方向
        """
        if down:
            # 设置为下拉动画
            self._menuAnimation = MenuAnimationType.DROP_DOWN
        else:
            # 设置为上拉动画
            self._menuAnimation = MenuAnimationType.PULL_UP

    def isMenuDropDown(self):
        # 返回菜单是否为下拉方向
        return self._menuAnimation == MenuAnimationType.DROP_DOWN

    def _showMoreActionsMenu(self):
        """
        显示"更多"动作菜单
        """
        # 清除"更多"按钮的状态
        #self.moreButton.clearState()

        # 复制隐藏动作列表
        actions = self._hiddenActions.copy()

        # 将隐藏控件中的动作添加到菜单（逆序添加以保持顺序）
        for w in reversed(self._hiddenWidgets):
            if isinstance(w, CommandButton):
                actions.insert(0, w.action())

        # 创建命令菜单
        menu = CommandMenu(self)
        # 添加所有要显示的动作
        menu.addActions(actions)

        # 计算菜单位置
        x = -menu.width() + menu.layout().contentsMargins().right() + \
            self.moreButton.width() + 18
        if self._menuAnimation == MenuAnimationType.DROP_DOWN:
            y = self.moreButton.height()
        else:
            y = -5

        # 将位置转换为全局坐标并显示菜单
        pos = self.moreButton.mapToGlobal(QPoint(x, y))
        menu.exec(pos, aniType=self._menuAnimation)


class CommandViewMenu(CommandMenu):
    """
    命令视图菜单
    具有特殊样式的命令菜单
    """

    def __init__(self, parent=None):
        # 初始化父类
        super().__init__(parent)
        # 设置视图对象名称
        self.view.setObjectName('commandListWidget')

    def setDropDown(self, down: bool, long=False):
        # 设置下拉属性
        self.view.setProperty('dropDown', down)
        # 设置长菜单属性
        self.view.setProperty('long', long)
        # 强制更新样式
        self.view.setStyle(QApplication.style())
        self.view.update()


class CommandViewBar(CommandBar):
    """
    命令视图栏
    在CommandBar基础上增加了淡入淡出动画效果
    """

    def __init__(self, parent=None):
        # 初始化父类
        super().__init__(parent)
        # 默认设置为下拉菜单
        self.setMenuDropDown(True)

    def setMenuDropDown(self, down: bool):
        """
        设置"更多"菜单的动画方向
        """
        if down:
            # 设置为淡入下拉动画
            self._menuAnimation = MenuAnimationType.FADE_IN_DROP_DOWN
        else:
            # 设置为淡入上拉动画
            self._menuAnimation = MenuAnimationType.FADE_IN_PULL_UP

    def isMenuDropDown(self):
        # 返回菜单是否为淡入下拉方向
        return self._menuAnimation == MenuAnimationType.FADE_IN_DROP_DOWN

    def _showMoreActionsMenu(self):
      

        # 复制隐藏动作列表
        actions = self._hiddenActions.copy()

        # 将隐藏控件中的动作添加到菜单（逆序添加以保持顺序）
        for w in reversed(self._hiddenWidgets):
            if isinstance(w, CommandButton):
                actions.insert(0, w.action())

        # 创建命令视图菜单
        menu = CommandViewMenu(self)
        # 添加所有要显示的动作
        menu.addActions(actions)

        # 调整视图形状
        view = self.parent()  # type: CommandBarView
        view.setMenuVisible(True)

        # 调整菜单形状
        menu.closedSignal.connect(lambda: view.setMenuVisible(False))
        menu.setDropDown(self.isMenuDropDown(), menu.view.width() > view.width()+5)

        # 调整菜单大小
        if menu.view.width() < view.width():
            menu.view.setFixedWidth(view.width())
            menu.adjustSize()

        # 计算菜单位置
        x = -menu.width() + menu.layout().contentsMargins().right() + \
            self.moreButton.width() + 18
        if self.isMenuDropDown():
            y = self.moreButton.height()
        else:
            y = -13
            # 上拉菜单不显示阴影
            menu.setShadowEffect(0, (0, 0), QColor(0, 0, 0, 0))
            # 调整内边距
            menu.layout().setContentsMargins(12, 20, 12, 8)

        # 将位置转换为全局坐标并显示菜单
        pos = self.moreButton.mapToGlobal(QPoint(x, y))
        menu.exec(pos, aniType=self._menuAnimation)


class CommandBarView(FlyoutViewBase):
    """
    命令栏视图
    将CommandViewBar包装在一个带有圆角和背景的视图中
    """

    def __init__(self, parent=None):
        # 初始化父类
        super().__init__(parent=parent)
        # 创建命令视图栏
        self.bar = CommandViewBar(self)
        # 创建水平布局
        self.hBoxLayout = QHBoxLayout(self)

        # 设置布局内边距
        self.hBoxLayout.setContentsMargins(6, 6, 6, 6)
        # 将命令栏添加到布局
        self.hBoxLayout.addWidget(self.bar)
        # 设置布局大小约束为最小和最大大小
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMinAndMaxSize)

        # 设置按钮为紧凑模式
        self.setButtonTight(True)
        # 设置图标大小
        self.setIconSize(QSize(14, 14))

        # 初始化菜单可见标志
        self._isMenuVisible = False

    def setMenuVisible(self, isVisible):
        # 设置菜单可见状态
        self._isMenuVisible = isVisible
        # 触发重绘
        self.update()

    # 以下方法是对CommandBar对应方法的包装
    def addWidget(self, widget: QWidget):
        self.bar.addWidget(widget)

    def setSpacing(self, spacing: int):
        self.bar.setSpacing(spacing)

    def spacing(self):
        return self.bar.spacing()

    def addAction(self, action: QAction):
        return self.bar.addAction(action)

    def addActions(self, actions: Iterable[QAction]):
        self.bar.addActions(actions)

    def addHiddenAction(self, action: QAction):
        self.bar.addHiddenAction(action)

    def addHiddenActions(self, actions: List[QAction]):
        self.bar.addHiddenActions(actions)

    def insertAction(self, before: QAction, action: QAction):
        return self.bar.insertAction(before, action)

    def addSeparator(self):
        self.bar.addSeparator()

    def insertSeparator(self, index: int):
        self.bar.insertSeparator(index)

    def removeAction(self, action: QAction):
        self.bar.removeAction(action)

    def removeWidget(self, widget: QWidget):
        self.bar.removeWidget(widget)

    def removeHiddenAction(self, action: QAction):
        self.bar.removeAction(action)

    def setToolButtonStyle(self, style: Qt.ToolButtonStyle):
        self.bar.setToolButtonStyle(style)

    def toolButtonStyle(self):
        return self.bar.toolButtonStyle()

    def setButtonTight(self, isTight: bool):
        self.bar.setButtonTight(isTight)

    def isButtonTight(self):
        return self.bar.isButtonTight()

    def setIconSize(self, size: QSize):
        self.bar.setIconSize(size)

    def iconSize(self):
        return self.bar.iconSize()

    def setFont(self, font: QFont):
        self.bar.setFont(font)

    def setMenuDropDown(self, down: bool):
        self.bar.setMenuDropDown(down)

    def suitableWidth(self):
        # 计算适合的宽度，包括内边距
        m = self.contentsMargins()
        return m.left() + m.right() + self.bar.suitableWidth()

    def resizeToSuitableWidth(self):
        # 调整命令栏宽度并设置自身宽度
        self.bar.resizeToSuitableWidth()
        self.setFixedWidth(self.suitableWidth())

    def actions(self):
        # 返回所有动作
        return self.bar.actions()

    def paintEvent(self, e):
        # 创建绘制器
        painter = QPainter(self)
        # 设置抗锯齿渲染
        painter.setRenderHints(QPainter.Antialiasing)

        # 创建路径用于绘制圆角矩形
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        # 添加圆角矩形路径
        path.addRoundedRect(QRectF(self.rect().adjusted(1, 1, -1, -1)), 8, 8)

        # 如果菜单可见，添加连接菜单的矩形路径
        if self._isMenuVisible:
            y = self.height() - 10 if self.bar.isMenuDropDown() else 1
            path.addRect(1, y, self.width() - 2, 9)

        # 根据当前主题设置填充颜色和边框颜色
        painter.setBrush(
            QColor(40, 40, 40) if isDarkTheme() else QColor(248, 248, 248))
        painter.setPen(
            QColor(56, 56, 56) if isDarkTheme() else QColor(233, 233, 233))
        # 绘制简化后的路径
        painter.drawPath(path.simplified())