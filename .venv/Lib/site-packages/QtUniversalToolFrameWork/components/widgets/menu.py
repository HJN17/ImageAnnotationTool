from enum import Enum
from typing import List, Union

from qframelesswindow import WindowEffect
from PyQt5.QtCore import (QEasingCurve, QEvent, QPropertyAnimation, QObject, QModelIndex,
                          Qt, QSize, QRectF, pyqtSignal, QPoint, QTimer, QParallelAnimationGroup, QRect)
from PyQt5.QtGui import (QIcon, QColor, QPainter, QPen, QPixmap, QRegion, QCursor, QTextCursor, QHoverEvent,
                         QFontMetrics, QKeySequence)
from PyQt5.QtWidgets import (QAction, QApplication, QMenu, QProxyStyle, QStyle,
                             QGraphicsDropShadowEffect, QListWidget, QWidget, QHBoxLayout,
                             QListWidgetItem, QLineEdit, QTextEdit, QStyledItemDelegate, QStyleOptionViewItem, QLabel)

from ...common.icon import FluentIcon as FIF,FluentIconEngine, Action, FluentIconBase, Icon
from ...common.style_sheet import FluentStyleSheet, themeColor
from ...common.screen import getCurrentScreenGeometry
from ...common.font import getFont
from ...common.config import isDarkTheme


from .scroll_bar import SmoothScrollDelegate

class CustomMenuStyle(QProxyStyle):
    """ 自定义菜单样式 """

    def __init__(self, iconSize=14):
        """
        初始化自定义菜单样式
        
        参数
        ----------
        iconSize : int
            图标的大小
        """
        super().__init__()
        self.iconSize = iconSize

    def pixelMetric(self, metric, option, widget):
        """\重写像素度量方法以自定义图标大小"""
        if metric == QStyle.PM_SmallIconSize:
            return self.iconSize

        return super().pixelMetric(metric, option, widget)


class DWMMenu(QMenu):
    """ 带有DWM阴影的菜单 """

    def __init__(self, title="", parent=None):
        """初始化带有DWM阴影的菜单"""
        super().__init__(title, parent)
        self.windowEffect = WindowEffect(self)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Popup | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyle(CustomMenuStyle())
        FluentStyleSheet.MENU.apply(self)

    def event(self, e: QEvent):
        """重写事件处理方法以在窗口ID更改时添加阴影效果"""
        if e.type() == QEvent.WinIdChange:
            self.windowEffect.addMenuShadowEffect(self.winId())
        return QMenu.event(self, e)


class MenuAnimationType(Enum):
    """ 菜单动画类型枚举 """

    NONE = 0  # 无动画
    DROP_DOWN = 1  # 下拉动画
    PULL_UP = 2  # 上拉动画
    FADE_IN_DROP_DOWN = 3  # 淡入下拉动画
    FADE_IN_PULL_UP = 4  # 淡入上拉动画



class SubMenuItemWidget(QWidget):
    """ 子菜单项部件 """

    showMenuSig = pyqtSignal(QListWidgetItem)  # 显示子菜单的信号

    def __init__(self, menu, item, parent=None):
        """
        初始化子菜单项部件
        
        参数
        ----------
        menu: QMenu | RoundMenu
            子菜单

        item: QListWidgetItem
            菜单项

        parent: QWidget
            父部件
        """
        super().__init__(parent)
        self.menu = menu
        self.item = item

    def enterEvent(self, e):
        """当鼠标进入部件时，发出显示子菜单的信号"""
        super().enterEvent(e)
        self.showMenuSig.emit(self.item)

    def paintEvent(self, e):
        """绘制右侧的箭头指示器"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        # 绘制向右箭头
        FIF.CHEVRON_RIGHT.render(painter, QRectF(
            self.width()-10, self.height()/2-9/2, 9, 9))


class MenuItemDelegate(QStyledItemDelegate):
    """ 菜单项代理 """

    def __init__(self, parent=None):
        """初始化菜单项代理"""
        super().__init__(parent)
        self.tooltipDelegate = None  # 提示代理

    def _isSeparator(self, index: QModelIndex):
        """检查是否为分隔符"""
        return index.model().data(index, Qt.DecorationRole) == "seperator"

    def paint(self, painter, option, index):
        """重写绘制方法，绘制分隔符"""
        if not self._isSeparator(index):
            return super().paint(painter, option, index)

        # 绘制分隔符
        painter.save()

        c = 0 if not isDarkTheme() else 255
        pen = QPen(QColor(c, c, c, 25), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        rect = option.rect
        painter.drawLine(0, rect.y() + 4, rect.width() + 12, rect.y() + 4)

        painter.restore()



class ShortcutMenuItemDelegate(MenuItemDelegate):
    """ 快捷键菜单项代理 """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """重写绘制方法，绘制快捷键"""
        super().paint(painter, option, index)
        if self._isSeparator(index):
            return

        # 绘制快捷键
        action = index.data(Qt.UserRole)  # type: QAction
        if not isinstance(action, QAction) or action.shortcut().isEmpty():
            return

        painter.save()

        if not option.state & QStyle.State_Enabled:
            painter.setOpacity(0.5 if isDarkTheme() else 0.6)

        font = getFont(12)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 200) if isDarkTheme() else QColor(0, 0, 0, 153))

        fm = QFontMetrics(font)
        shortcut = action.shortcut().toString(QKeySequence.NativeText)

        sw = fm.width(shortcut)
        painter.translate(option.rect.width()-sw-20, 0)

        rect = QRectF(0, option.rect.y(), sw, option.rect.height())
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, shortcut)

        painter.restore()


class MenuActionListWidget(QListWidget):
    """ 菜单动作列表部件 """

    def __init__(self, parent=None):
        """初始化菜单动作列表部件"""
        super().__init__(parent)
        self._itemHeight = 28  # 项目高度
        self._maxVisibleItems = -1  # 根据屏幕大小调整可见项目数

        self.setViewportMargins(0, 6, 0, 6)
        self.setTextElideMode(Qt.ElideNone)
        self.setDragEnabled(False)
        self.setMouseTracking(True)
        self.setIconSize(QSize(14, 14))
        self.setItemDelegate(ShortcutMenuItemDelegate(self))

        self.scrollDelegate = SmoothScrollDelegate(self)
        self.setStyleSheet(
            'MenuActionListWidget{font: 14px "Segoe UI", "Microsoft YaHei", "PingFang SC"}')

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def insertItem(self, row, item):
        """ 在列表的指定位置插入菜单项 """
        super().insertItem(row, item)
        self.adjustSize()

    def addItem(self, item):
        """ 在末尾添加菜单项 """
        super().addItem(item)
        self.adjustSize()

    def takeItem(self, row):
        """ 从列表中删除项目 """
        item = super().takeItem(row)
        self.adjustSize()
        return item

    def adjustSize(self, pos=None, aniType=MenuAnimationType.NONE):
        """调整部件大小以适应所有项目"""
        size = QSize()
        for i in range(self.count()):
            s = self.item(i).sizeHint()
            size.setWidth(max(s.width(), size.width(), 1))
            size.setHeight(max(1, size.height() + s.height()))

        # 调整视口高度
        w, h = MenuAnimationManager.make(self, aniType).availableViewSize(pos)

        # 修复 https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/844
        # self.viewport().adjustSize()

        # 调整列表部件高度
        m = self.viewportMargins()
        size += QSize(m.left()+m.right()+2, m.top()+m.bottom())
        size.setHeight(min(h, size.height()+3))
        size.setWidth(max(min(w, size.width()), self.minimumWidth()))

        if self.maxVisibleItems() > 0:
            size.setHeight(min(
                size.height(), self.maxVisibleItems() * self._itemHeight + m.top()+m.bottom() + 3))

        self.setFixedSize(size)

    def setItemHeight(self, height: int):
        """ 设置项目的高度 """
        if height == self._itemHeight:
            return

        for i in range(self.count()):
            item = self.item(i)
            if not self.itemWidget(item):
                item.setSizeHint(QSize(item.sizeHint().width(), height))

        self._itemHeight = height
        self.adjustSize()

    def setMaxVisibleItems(self, num: int):
        """ 设置最大可见项目数 """
        self._maxVisibleItems = num
        self.adjustSize()

    def maxVisibleItems(self):
        """获取最大可见项目数"""
        return self._maxVisibleItems

    def heightForAnimation(self, pos: QPoint, aniType: MenuAnimationType):
        """动画的高度"""
        ih = self.itemsHeight()
        _, sh = MenuAnimationManager.make(self, aniType).availableViewSize(pos)
        return min(ih, sh)

    def itemsHeight(self):
        """ 返回所有项目的高度 """
        N = self.count() if self.maxVisibleItems() < 0 else min(self.maxVisibleItems(), self.count())
        h = sum(self.item(i).sizeHint().height() for i in range(N))
        m = self.viewportMargins()
        return h + m.top() + m.bottom()


class RoundMenu(QMenu):
    """ 圆角菜单 """

    closedSignal = pyqtSignal()  # 关闭信号

    def __init__(self, title="", parent=None):
        """初始化圆角菜单"""
        super().__init__(parent=parent)
        self.setTitle(title)
        self._icon = QIcon()
        self._actions = []  # type: List[QAction]
        self._subMenus = []

        self.isSubMenu = False
        self.parentMenu = None
        self.menuItem = None
        self.lastHoverItem = None
        self.lastHoverSubMenuItem = None
        self.isHideBySystem = True
        self.itemHeight = 28

        self.hBoxLayout = QHBoxLayout(self)
        self.view = MenuActionListWidget(self)

        self.aniManager = None
        self.timer = QTimer(self)

        self.__initWidgets()

    def __initWidgets(self):
        """初始化窗口部件"""
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                            Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.timer.setSingleShot(True)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self._onShowMenuTimeOut)

        self.setShadowEffect()
        self.hBoxLayout.addWidget(self.view, 1, Qt.AlignCenter)

        self.hBoxLayout.setContentsMargins(12, 8, 12, 20)
        FluentStyleSheet.MENU.apply(self)

        self.view.itemClicked.connect(self._onItemClicked)
        self.view.itemEntered.connect(self._onItemEntered)

    def setMaxVisibleItems(self, num: int):
        """ 设置最大可见项目数 """
        self.view.setMaxVisibleItems(num)
        self.adjustSize()

    def setItemHeight(self, height):
        """ 设置菜单项的高度 """
        if height == self.itemHeight:
            return

        self.itemHeight = height
        self.view.setItemHeight(height)

    def setShadowEffect(self, blurRadius=30, offset=(0, 8), color=QColor(0, 0, 0, 30)):
        """ 为对话框添加阴影效果 """
        self.shadowEffect = QGraphicsDropShadowEffect(self.view)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.view.setGraphicsEffect(None)
        self.view.setGraphicsEffect(self.shadowEffect)

    def _setParentMenu(self, parent, item):
        """设置父菜单"""
        self.parentMenu = parent
        self.menuItem = item
        self.isSubMenu = True if parent else False

    def adjustSize(self):
        """调整菜单大小"""
        m = self.layout().contentsMargins()
        w = self.view.width() + m.left() + m.right()
        h = self.view.height() + m.top() + m.bottom()
        self.setFixedSize(w, h)

    def icon(self):
        """获取菜单图标"""
        return self._icon

    def title(self):
        """获取菜单标题"""
        return self._title

    def clear(self):
        """ 清除所有动作 """
        while self._actions:
            self.removeAction(self._actions[-1])

        while self._subMenus:
            self.removeMenu(self._subMenus[-1])

    def setIcon(self, icon: Union[QIcon, FluentIconBase]):
        """ 设置菜单图标 """
        if isinstance(icon, FluentIconBase):
            icon = Icon(icon)

        self._icon = icon

    def setTitle(self, title: str):
        """设置菜单标题"""
        self._title = title
        super().setTitle(title)

    def addAction(self, action: Union[QAction, Action]):
        """ 向菜单添加动作

        参数
        ----------
        action: QAction
            菜单动作
        """
        item = self._createActionItem(action)
        self.view.addItem(item)
        self.adjustSize()

    def addWidget(self, widget: QWidget, selectable=True, onClick=None):
        """ 添加自定义部件

        参数
        ----------
        widget: QWidget
            自定义部件

        selectable: bool
            菜单项是否可选择

        onClick: callable
            点击回调函数
        """
        action = QAction()
        action.setProperty('selectable', selectable)

        item = self._createActionItem(action)
        item.setSizeHint(widget.size())

        self.view.addItem(item)
        self.view.setItemWidget(item, widget)

        if not selectable:
            item.setFlags(Qt.NoItemFlags)

        if onClick:
            action.triggered.connect(onClick)

        self.adjustSize()

    def _createActionItem(self, action: QAction, before=None):
        """ 创建菜单动作项  """
        if not before:
            self._actions.append(action)
            super().addAction(action)
        elif before in self._actions:
            index = self._actions.index(before)
            self._actions.insert(index, action)
            super().insertAction(before, action)
        else:
            raise ValueError('`before` 不在动作列表中')

        item = QListWidgetItem(self._createItemIcon(action), action.text())
        self._adjustItemText(item, action)

        # 如果动作不可用，则禁用项目
        if not action.isEnabled():
            item.setFlags(Qt.NoItemFlags)
        if action.text() != action.toolTip():
            item.setToolTip(action.toolTip())

        item.setData(Qt.UserRole, action)
        action.setProperty('item', item)
        action.changed.connect(self._onActionChanged)
        return item

    def _hasItemIcon(self):
        """检查是否有项目图标"""
        return any(not i.icon().isNull() for i in self._actions+self._subMenus)

    def _adjustItemText(self, item: QListWidgetItem, action: QAction):
        """ 调整项目文本 """
        # 为快捷键留出一些空间
        if isinstance(self.view.itemDelegate(), ShortcutMenuItemDelegate):
            sw = self._longestShortcutWidth()
            if sw:
                sw += 22
        else:
            sw = 0

        # 调整项目宽度
        if not self._hasItemIcon():
            item.setText(action.text())
            w = 40 + self.view.fontMetrics().width(action.text()) + sw
        else:
            # 添加一个空白字符以增加图标和文本之间的空间
            item.setText(" " + action.text())
            space = 4 - self.view.fontMetrics().width(" ")
            w = 60 + self.view.fontMetrics().width(item.text()) + sw + space

        item.setSizeHint(QSize(w, self.itemHeight))
        return w

    def _longestShortcutWidth(self):
        """最长快捷键宽度"""
        fm = QFontMetrics(getFont(12))
        return max(fm.width(a.shortcut().toString()) for a in self.menuActions())

    def _createItemIcon(self, w):
        """ 创建菜单项图标 """
        hasIcon = self._hasItemIcon()
        icon = QIcon(FluentIconEngine(w.icon()))

        if hasIcon and w.icon().isNull():
            pixmap = QPixmap(self.view.iconSize())
            pixmap.fill(Qt.transparent)
            icon = QIcon(pixmap)
        elif not hasIcon:
            icon = QIcon()

        return icon

    def insertAction(self, before: Union[QAction, Action], action: Union[QAction, Action]):
        """ 在指定动作之前插入动作 """
        if before not in self._actions:
            return

        beforeItem = before.property('item')
        if not beforeItem:
            return

        index = self.view.row(beforeItem)
        item = self._createActionItem(action, before)
        self.view.insertItem(index, item)
        self.adjustSize()

    def addActions(self, actions: List[Union[QAction, Action]]):
        """ 向菜单添加多个动作

        参数
        ----------
        actions: Iterable[QAction]
            菜单动作列表
        """
        for action in actions:
            self.addAction(action)

    def insertActions(self, before: Union[QAction, Action], actions: List[Union[QAction, Action]]):
        """ 在指定动作之前插入多个动作 """
        for action in actions:
            self.insertAction(before, action)

    def removeAction(self, action: Union[QAction, Action]):
        """ 从菜单中删除动作 """
        if action not in self._actions:
            return

        # 删除动作
        item = action.property("item")
        self._actions.remove(action)
        action.setProperty('item', None)

        if not item:
            return

        # 删除项目
        self._removeItem(item)
        super().removeAction(action)

    def removeMenu(self, menu):
        """ 删除子菜单 """
        if menu not in self._subMenus:
            return

        item = menu.menuItem
        self._subMenus.remove(menu)
        self._removeItem(item)

    def setDefaultAction(self, action: Union[QAction, Action]):
        """ 设置默认动作 """
        if action not in self._actions:
            return

        item = action.property("item")
        if item:
            self.view.setCurrentItem(item)

    def addMenu(self, menu):
        """ 添加子菜单

        参数
        ----------
        menu: RoundMenu
            子圆角菜单
        """
        if not isinstance(menu, RoundMenu):
            raise ValueError('`menu` 应该是 `RoundMenu` 的实例。')

        item, w = self._createSubMenuItem(menu)
        self.view.addItem(item)
        self.view.setItemWidget(item, w)
        self.adjustSize()

    def insertMenu(self, before: Union[QAction, Action], menu):
        """ 在指定动作之前插入菜单 """
        if not isinstance(menu, RoundMenu):
            raise ValueError('`menu` 应该是 `RoundMenu` 的实例。')

        if before not in self._actions:
            raise ValueError('`before` 应该在菜单动作列表中')

        item, w = self._createSubMenuItem(menu)
        self.view.insertItem(self.view.row(before.property('item')), item)
        self.view.setItemWidget(item, w)
        self.adjustSize()

    def _createSubMenuItem(self, menu):
        """创建子菜单项"""
        self._subMenus.append(menu)

        item = QListWidgetItem(self._createItemIcon(menu), menu.title())
        if not self._hasItemIcon():
            w = 60 + self.view.fontMetrics().width(menu.title())
        else:
            # 添加一个空白字符以增加图标和文本之间的空间
            item.setText(" " + item.text())
            w = 72 + self.view.fontMetrics().width(item.text())

        # 添加子菜单项
        menu._setParentMenu(self, item)
        item.setSizeHint(QSize(w, self.itemHeight))
        item.setData(Qt.UserRole, menu)
        w = SubMenuItemWidget(menu, item, self)
        w.resize(item.sizeHint())

        return item, w

    def _removeItem(self, item):
        """删除项目"""
        self.view.takeItem(self.view.row(item))
        item.setData(Qt.UserRole, None)

        # 删除部件
        widget = self.view.itemWidget(item)
        if widget:
            widget.deleteLater()

    def _showSubMenu(self, item):
        """ 显示子菜单 """
        self.lastHoverItem = item
        self.lastHoverSubMenuItem = item
        # 延迟400毫秒以防抖
        self.timer.stop()
        self.timer.start()

    def _onShowMenuTimeOut(self):
        """显示菜单超时处理"""
        if self.lastHoverSubMenuItem is None or not self.lastHoverItem is self.lastHoverSubMenuItem:
            return

        w = self.view.itemWidget(self.lastHoverSubMenuItem)

        if w.menu.parentMenu.isHidden():
            return

        itemRect = QRect(w.mapToGlobal(w.rect().topLeft()), w.size())
        x = itemRect.right() + 5
        y = itemRect.y() - 5

        screenRect = getCurrentScreenGeometry()
        subMenuSize = w.menu.sizeHint()
        if (x + subMenuSize.width()) > screenRect.right():
            x = max(itemRect.left() - subMenuSize.width() - 5, screenRect.left())

        if (y + subMenuSize.height()) > screenRect.bottom():
            y = screenRect.bottom() - subMenuSize.height()

        y = max(y, screenRect.top())

        w.menu.exec(QPoint(x, y))

    def addSeparator(self):
        """ 向菜单添加分隔符 """
        m = self.view.viewportMargins()
        w = self.view.width()-m.left()-m.right()

        # 向列表部件添加分隔符
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(w, 9))
        self.view.addItem(item)
        item.setData(Qt.DecorationRole, "seperator")
        self.adjustSize()

    def _onItemClicked(self, item):
        """项目点击事件处理"""
        action = item.data(Qt.UserRole)  # type: QAction
        if action not in self._actions or not action.isEnabled():
            return

        if self.view.itemWidget(item) and not action.property('selectable'):
            return

        self._hideMenu(False)

        if not self.isSubMenu:
            action.trigger()
            return

        # 关闭父菜单
        self._closeParentMenu()
        action.trigger()

    def _closeParentMenu(self):
        """关闭父菜单"""
        menu = self
        while menu:
            menu.close()
            menu = menu.parentMenu

    def _onItemEntered(self, item):
        """项目进入事件处理"""
        self.lastHoverItem = item
        if not isinstance(item.data(Qt.UserRole), RoundMenu):
            return

        self._showSubMenu(item)

    def _hideMenu(self, isHideBySystem=False):
        """隐藏菜单"""
        self.isHideBySystem = isHideBySystem
        self.view.clearSelection()
        if self.isSubMenu:
            self.hide()
        else:
            self.close()

    def hideEvent(self, e):
        """隐藏事件处理"""
        if self.isHideBySystem and self.isSubMenu:
            self._closeParentMenu()

        self.isHideBySystem = True
        e.accept()

    def closeEvent(self, e):
        """关闭事件处理"""
        e.accept()
        self.closedSignal.emit()
        self.view.clearSelection()

    def menuActions(self):
        """获取菜单动作列表"""
        return self._actions

    def mousePressEvent(self, e):
        """鼠标按下事件处理"""
        w = self.childAt(e.pos())
        if (w is not self.view) and (not self.view.isAncestorOf(w)):
            self._hideMenu(True)

    def mouseMoveEvent(self, e):
        """鼠标移动事件处理"""
        if not self.isSubMenu:
            return

        # 当鼠标移出子菜单项时隐藏子菜单
        pos = e.globalPos()
        view = self.parentMenu.view

        # 获取菜单项的矩形
        margin = view.viewportMargins()
        rect = view.visualItemRect(self.menuItem).translated(
            view.mapToGlobal(QPoint()))
        rect = rect.translated(margin.left(), margin.top()+2)
        if self.parentMenu.geometry().contains(pos) and not rect.contains(pos) and \
                not self.geometry().contains(pos):
            view.clearSelection()
            self._hideMenu(False)

    def _onActionChanged(self):
        """ 动作更改槽函数 """
        action = self.sender()  # type: QAction
        item = action.property('item')  # type: QListWidgetItem
        item.setIcon(self._createItemIcon(action))

        if action.text() != action.toolTip():
            item.setToolTip(action.toolTip())

        self._adjustItemText(item, action)

        if action.isEnabled():
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        else:
            item.setFlags(Qt.NoItemFlags)

        self.view.adjustSize()
        self.adjustSize()

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        """ 显示菜单

        参数
        ----------
        pos: QPoint
            弹出位置

        ani: bool
            是否显示弹出动画

        aniType: MenuAnimationType
            菜单动画类型
        """
        #if self.isVisible():
        #    aniType = MenuAnimationType.NONE

        self.aniManager = MenuAnimationManager.make(self, aniType)
        self.aniManager.exec(pos)

        self.show()

        if self.isSubMenu:
            self.menuItem.setSelected(True)

    def exec_(self, pos: QPoint, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        """ 显示菜单

        参数
        ----------
        pos: QPoint
            弹出位置

        ani: bool
            是否显示弹出动画

        aniType: MenuAnimationType
            菜单动画类型
        """
        self.exec(pos, ani, aniType)

    def adjustPosition(self):
        """调整菜单位置"""
        m = self.layout().contentsMargins()
        rect = getCurrentScreenGeometry()
        w, h = self.width(), self.height()

        # 计算最大X坐标
        maxX = rect.right() - w + m.left()
        if self.x() > maxX:
            self.move(maxX, self.y())

        # 计算最大Y坐标
        maxY = rect.bottom() - h + m.bottom()
        if self.y() > maxY:
            self.move(self.x(), maxY)

        # 确保菜单不会超出屏幕顶部
        self.move(self.x(), max(self.y(), rect.top()))

    def paintEvent(self, e):
        """绘制事件（空实现）"""
        pass


class MenuAnimationManager(QObject):
    """ 菜单动画管理器 """

    managers = {}  # 动画管理器注册表

    def __init__(self, menu: RoundMenu):
        """初始化菜单动画管理器"""
        super().__init__()
        self.menu = menu
        self.ani = QPropertyAnimation(menu, b'pos', menu)

        self.ani.setDuration(250)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)
        self.ani.valueChanged.connect(self._onValueChanged)
        self.ani.valueChanged.connect(self._updateMenuViewport)

    def _onValueChanged(self):
        """值变化事件处理（可由子类重写）"""
        pass

    def availableViewSize(self, pos: QPoint):
        """ 返回视图的可用大小 """
        ss = getCurrentScreenGeometry()
        w, h = ss.width() - 100, ss.height() - 100
        return w, h

    def _updateMenuViewport(self):
        """更新菜单视口"""
        self.menu.view.viewport().update()
        self.menu.view.setAttribute(Qt.WA_UnderMouse, True)
        e = QHoverEvent(QEvent.HoverEnter, QPoint(), QPoint(1, 1))
        QApplication.sendEvent(self.menu.view, e)

    def _endPosition(self, pos):
        """计算结束位置"""
        m = self.menu
        rect = getCurrentScreenGeometry()
        w, h = m.width() + 5, m.height()
        x = min(pos.x() - m.layout().contentsMargins().left(), rect.right() - w)
        y = min(pos.y() - 4, rect.bottom() - h + 10)

        return QPoint(x, y)

    def _menuSize(self):
        """获取菜单大小"""
        m = self.menu.layout().contentsMargins()
        w = self.menu.view.width() + m.left() + m.right() + 120
        h = self.menu.view.height() + m.top() + m.bottom() + 20
        return w, h

    def exec(self, pos: QPoint):
        """执行动画（由子类实现）"""
        pass

    @classmethod
    def register(cls, name):
        """ 注册菜单动画管理器

        参数
        ----------
        name: Any
            管理器名称，应该是唯一的
        """
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager

            return Manager

        return wrapper

    @classmethod
    def make(cls, menu: RoundMenu, aniType: MenuAnimationType):
        """创建指定类型的动画管理器"""
        if aniType not in cls.managers:
            raise ValueError(f'`{aniType}` 是无效的菜单动画类型。')

        return cls.managers[aniType](menu)


@MenuAnimationManager.register(MenuAnimationType.NONE)
class DummyMenuAnimationManager(MenuAnimationManager):
    """ 无动画菜单管理器 """

    def exec(self, pos: QPoint):
        """直接移动到结束位置"""
        self.menu.move(self._endPosition(pos))


@MenuAnimationManager.register(MenuAnimationType.DROP_DOWN)
class DropDownMenuAnimationManager(MenuAnimationManager):
    """ 下拉菜单动画管理器 """

    def exec(self, pos):
        """执行下拉动画"""
        pos = self._endPosition(pos)
        h = self.menu.height() + 5

        self.ani.setStartValue(pos-QPoint(0, int(h/2)))
        self.ani.setEndValue(pos)
        self.ani.start()

    def availableViewSize(self, pos: QPoint):
        """获取可用视图大小"""
        ss = getCurrentScreenGeometry()
        return ss.width() - 100, max(ss.bottom() - pos.y() - 10, 1)

    def _onValueChanged(self):
        """值变化时更新菜单遮罩"""
        w, h = self._menuSize()
        y = self.ani.endValue().y() - self.ani.currentValue().y()
        self.menu.setMask(QRegion(0, y, w, h))


@MenuAnimationManager.register(MenuAnimationType.PULL_UP)
class PullUpMenuAnimationManager(MenuAnimationManager):
    """ 上拉菜单动画管理器 """

    def _endPosition(self, pos):
        """计算结束位置"""
        m = self.menu
        rect = getCurrentScreenGeometry()
        w, h = m.width() + 5, m.height()
        x = min(pos.x() - m.layout().contentsMargins().left(), rect.right() - w)
        y = max(pos.y() - h + 13, rect.top() + 4)
        return QPoint(x, y)

    def exec(self, pos):
        """执行上拉动画"""
        pos = self._endPosition(pos)
        h = self.menu.height() + 5

        self.ani.setStartValue(pos+QPoint(0, int(h/2)))
        self.ani.setEndValue(pos)
        self.ani.start()

    def availableViewSize(self, pos: QPoint):
        """获取可用视图大小"""
        ss = getCurrentScreenGeometry()
        return ss.width() - 100, max(pos.y() - ss.top() - 28, 1)

    def _onValueChanged(self):
        """值变化时更新菜单遮罩"""
        w, h = self._menuSize()
        y = self.ani.endValue().y() - self.ani.currentValue().y()
        self.menu.setMask(QRegion(0, y, w, h - 28))


@MenuAnimationManager.register(MenuAnimationType.FADE_IN_DROP_DOWN)
class FadeInDropDownMenuAnimationManager(MenuAnimationManager):
    """ 淡入下拉菜单动画管理器 """

    def __init__(self, menu: RoundMenu):
        """初始化淡入下拉菜单动画管理器"""
        super().__init__(menu)
        self.opacityAni = QPropertyAnimation(menu, b'windowOpacity', self)
        self.aniGroup = QParallelAnimationGroup(self)
        self.aniGroup.addAnimation(self.ani)
        self.aniGroup.addAnimation(self.opacityAni)

    def exec(self, pos):
        """执行淡入下拉动画"""
        pos = self._endPosition(pos)

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)

        self.ani.setStartValue(pos-QPoint(0, 8))
        self.ani.setEndValue(pos)
        self.ani.setDuration(150)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)

        self.aniGroup.start()

    def availableViewSize(self, pos: QPoint):
        """获取可用视图大小"""
        ss = getCurrentScreenGeometry()
        return ss.width() - 100, max(ss.bottom() - pos.y() - 10, 1)


@MenuAnimationManager.register(MenuAnimationType.FADE_IN_PULL_UP)
class FadeInPullUpMenuAnimationManager(MenuAnimationManager):
    """ 淡入上拉菜单动画管理器 """

    def __init__(self, menu: RoundMenu):
        """初始化淡入上拉菜单动画管理器"""
        super().__init__(menu)
        self.opacityAni = QPropertyAnimation(menu, b'windowOpacity', self)
        self.aniGroup = QParallelAnimationGroup(self)
        self.aniGroup.addAnimation(self.ani)
        self.aniGroup.addAnimation(self.opacityAni)

    def _endPosition(self, pos):
        """计算结束位置"""
        m = self.menu
        rect = getCurrentScreenGeometry()
        w, h = m.width() + 5, m.height()
        x = min(pos.x() - m.layout().contentsMargins().left(), rect.right() - w)
        y = max(pos.y() - h + 15, rect.top() + 4)
        return QPoint(x, y)

    def exec(self, pos):
        """执行淡入上拉动画"""
        pos = self._endPosition(pos)

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)

        self.ani.setStartValue(pos+QPoint(0, 8))
        self.ani.setEndValue(pos)
        self.ani.setDuration(200)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)
        self.aniGroup.start()

    def availableViewSize(self, pos: QPoint):
        """获取可用视图大小"""
        ss = getCurrentScreenGeometry()
        return ss.width() - 100, pos.y()- ss.top() - 28


class EditMenu(RoundMenu):
    """ 编辑菜单 """

    def createActions(self):
        """创建编辑动作"""
        self.cutAct = QAction(
            FIF.CUT.icon(),
            self.tr("剪切"),
            self,
            shortcut="Ctrl+X",
            triggered=self.parent().cut,
        )
        self.copyAct = QAction(
            FIF.COPY.icon(),
            self.tr("复制"),
            self,
            shortcut="Ctrl+C",
            triggered=self.parent().copy,
        )
        self.pasteAct = QAction(
            FIF.PASTE.icon(),
            self.tr("粘贴"),
            self,
            shortcut="Ctrl+V",
            triggered=self.parent().paste,
        )
        self.cancelAct = QAction(
            FIF.CANCEL.icon(),
            self.tr("撤销"),
            self,
            shortcut="Ctrl+Z",
            triggered=self.parent().undo,
        )
        self.selectAllAct = QAction(
            self.tr("全选"),
            self,
            shortcut="Ctrl+A",
            triggered=self.parent().selectAll
        )
        self.action_list = [
            self.cutAct, self.copyAct,
            self.pasteAct, self.cancelAct, self.selectAllAct
        ]

    def _parentText(self):
        """获取父部件文本（由子类实现）"""
        raise NotImplementedError

    def _parentSelectedText(self):
        """获取父部件选中文本（由子类实现）"""
        raise NotImplementedError

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        """显示编辑菜单，根据父部件状态调整显示的动作"""
        self.clear()
        self.createActions()

        if QApplication.clipboard().mimeData().hasText():
            if self._parentText():
                if self._parentSelectedText():
                    if self.parent().isReadOnly():
                        self.addActions([self.copyAct, self.selectAllAct])
                    else:
                        self.addActions(self.action_list)
                else:
                    if self.parent().isReadOnly():
                        self.addAction(self.selectAllAct)
                    else:
                        self.addActions(self.action_list[2:])
            elif not self.parent().isReadOnly():
                self.addAction(self.pasteAct)
            else:
                return
        else:
            if not self._parentText():
                return

            if self._parentSelectedText():
                if self.parent().isReadOnly():
                    self.addActions([self.copyAct, self.selectAllAct])
                else:
                    self.addActions(
                        self.action_list[:2] + self.action_list[3:])
            else:
                if self.parent().isReadOnly():
                    self.addAction(self.selectAllAct)
                else:
                    self.addActions(self.action_list[3:])

        super().exec(pos, ani, aniType)


class LineEditMenu(EditMenu):
    """ 行编辑菜单 """

    def __init__(self, parent: QLineEdit):
        """初始化行编辑菜单"""
        super().__init__("", parent)
        self.selectionStart = parent.selectionStart()
        self.selectionLength = parent.selectionLength()

    def _onItemClicked(self, item):
        """项目点击事件处理"""
        if self.selectionStart >= 0:
            self.parent().setSelection(self.selectionStart, self.selectionLength)

        super()._onItemClicked(item)

    def _parentText(self):
        """获取父部件文本"""
        return self.parent().text()

    def _parentSelectedText(self):
        """获取父部件选中文本"""
        return self.parent().selectedText()


class TextEditMenu(EditMenu):
    """ 文本编辑菜单 """

    def __init__(self, parent: QTextEdit):
        """初始化文本编辑菜单"""
        super().__init__("", parent)
        cursor = parent.textCursor()
        self.selectionStart = cursor.selectionStart()
        self.selectionLength = cursor.selectionEnd() - self.selectionStart + 1

    def _parentText(self):
        """获取父部件文本"""
        return self.parent().toPlainText()

    def _parentSelectedText(self):
        """获取父部件选中文本"""
        return self.parent().textCursor().selectedText()

    def _onItemClicked(self, item):
        """项目点击事件处理"""
        if self.selectionStart >= 0:
            cursor = self.parent().textCursor()
            cursor.setPosition(self.selectionStart)
            cursor.movePosition(
                QTextCursor.Right, QTextCursor.KeepAnchor, self.selectionLength)

        super()._onItemClicked(item)


class IndicatorMenuItemDelegate(MenuItemDelegate):
    """ 带指示器的菜单项代理 """

    def paint(self, painter: QPainter, option, index):
        """重写绘制方法，绘制选中指示器"""
        super().paint(painter, option, index)
        if not option.state & QStyle.State_Selected:
            return

        painter.save()
        painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)

        painter.setPen(Qt.NoPen)
        painter.setBrush(themeColor())
        painter.drawRoundedRect(6, 11+option.rect.y(), 3, 15, 1.5, 1.5)

        painter.restore()


class CheckableMenuItemDelegate(ShortcutMenuItemDelegate):
    """ 可勾选菜单项代理 """

    def _drawIndicator(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """绘制勾选指示器（由子类实现）"""
        raise NotImplementedError

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """重写绘制方法，绘制勾选状态"""
        super().paint(painter, option, index)

        # 绘制指示器
        action = index.data(Qt.UserRole)  # type: QAction
        if not (isinstance(action, QAction) and action.isChecked()):
            return

        painter.save()
        self._drawIndicator(painter, option, index)
        painter.restore()


class RadioIndicatorMenuItemDelegate(CheckableMenuItemDelegate):
    """ 带单选指示器的可勾选菜单项代理 """

    def _drawIndicator(self, painter, option, index):
        """绘制单选指示器"""
        rect = option.rect
        r = 5
        x = rect.x() + 22
        y = rect.center().y() - r / 2

        painter.setRenderHints(QPainter.Antialiasing)
        if not option.state & QStyle.State_MouseOver:
            painter.setOpacity(0.75 if isDarkTheme() else 0.65)

        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white if isDarkTheme() else Qt.black)
        painter.drawEllipse(QRectF(x, y, r, r))


class CheckIndicatorMenuItemDelegate(CheckableMenuItemDelegate):
    """ 带复选指示器的可勾选菜单项代理 """

    def _drawIndicator(self, painter, option, index):
        """绘制复选指示器"""
        rect = option.rect
        s = 11
        x = rect.x() + 19
        y = rect.center().y() - s / 2

        painter.setRenderHints(QPainter.Antialiasing)
        if not option.state & QStyle.State_MouseOver:
            painter.setOpacity(0.75)

        FIF.ACCEPT.render(painter, QRectF(x, y, s, s))


class MenuIndicatorType(Enum):
    """ 菜单指示器类型 """
    CHECK = 0  # 复选框
    RADIO = 1  # 单选框


def createCheckableMenuItemDelegate(style: MenuIndicatorType):
    """ 创建可勾选菜单项代理 """
    if style == MenuIndicatorType.RADIO:
        return RadioIndicatorMenuItemDelegate()
    if style == MenuIndicatorType.CHECK:
        return CheckIndicatorMenuItemDelegate()

    raise ValueError(f'`{style}` 不是有效的菜单指示器类型。')


class CheckableMenu(RoundMenu):
    """ 可勾选菜单 """

    def __init__(self, title="", parent=None, indicatorType=MenuIndicatorType.CHECK):
        """初始化可勾选菜单"""
        super().__init__(title, parent)
        self.view.setItemDelegate(createCheckableMenuItemDelegate(indicatorType))
        self.view.setObjectName('checkableListWidget')

    def _adjustItemText(self, item: QListWidgetItem, action: QAction):
        """调整项目文本"""
        w = super()._adjustItemText(item, action)
        item.setSizeHint(QSize(w + 26, self.itemHeight))


class SystemTrayMenu(RoundMenu):
    """ 系统托盘菜单 """

    def sizeHint(self) -> QSize:
        """获取大小提示"""
        m = self.layout().contentsMargins()
        s = self.layout().sizeHint()
        return QSize(s.width() - m.right() + 5, s.height() - m.bottom())


class CheckableSystemTrayMenu(CheckableMenu):
    """ 可勾选系统托盘菜单 """

    def sizeHint(self) -> QSize:
        """获取大小提示"""
        m = self.layout().contentsMargins()
        s = self.layout().sizeHint()
        return QSize(s.width() - m.right() + 5, s.height() - m.bottom())


class LabelContextMenu(RoundMenu):
    """ 标签上下文菜单 """

    def __init__(self, parent: QLabel):
        """初始化标签上下文菜单"""
        super().__init__("", parent)
        self.selectedText = parent.selectedText()

        self.copyAct = QAction(
            FIF.COPY.icon(),
            self.tr("复制"),
            self,
            shortcut="Ctrl+C",
            triggered=self._onCopy
        )
        self.selectAllAct = QAction(
            self.tr("全选"),
            self,
            shortcut="Ctrl+A",
            triggered=self._onSelectAll
        )

    def _onCopy(self):
        """复制操作"""
        QApplication.clipboard().setText(self.selectedText)

    def _onSelectAll(self):
        """全选操作"""
        self.label().setSelection(0, len(self.label().text()))

    def label(self) -> QLabel:
        """获取标签部件"""
        return self.parent()

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        """显示菜单，根据选中状态调整显示的动作"""
        if self.label().hasSelectedText():
            self.addActions([self.copyAct, self.selectAllAct])
        else:
            self.addAction(self.selectAllAct)

        return super().exec(pos, ani, aniType)