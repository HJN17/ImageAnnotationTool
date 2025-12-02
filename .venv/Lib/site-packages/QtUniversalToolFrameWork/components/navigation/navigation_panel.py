# coding:utf-8
from enum import Enum
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QSize, QEvent, QEasingCurve, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QApplication


from ...common.style_sheet import FluentStyleSheet
from ...common.icon import FluentIconBase
from ...common.icon import FluentIcon as FIF

from ..widgets.scroll_area import ScrollArea
from ..widgets.tool_tip import ToolTipFilter
from ..widgets.scroll_bar import ScrollBarHandleDisplayMode

from .navigation_widget import NavigationToolButton, NavigationWidget, NavigationSeparator,NavigationPushButton,NavigationIconButton



class NavigationDisplayMode(Enum):
    """ 导航栏显示模式枚举 """
    COMPACT = 1
    EXPAND = 2
    MENU = 3 

class NavigationItemPosition(Enum):
    """ 导航项位置枚举 """
    TOP = 0    
    SCROLL = 1  
    BOTTOM = 2 

class NavigationToolTipFilter(ToolTipFilter):
    """ 导航工具提示过滤器（继承自基础工具提示过滤器） """

    def _canShowToolTip(self) -> bool:
        
        isVisible = super()._canShowToolTip()

        parent = self.parent() 
        
        return isVisible and parent.isCompacted

class NavigationPanel(QFrame):
    """ 导航面板主类（继承自QFrame，实现可折叠、多模式显示的导航栏） """

    displayModeChanged = pyqtSignal(NavigationDisplayMode)

    EXPAND_WIDTH = 160
    MIN_EXPAND_WIDTH = 1000
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._parent = parent

        self.items = {} 
        
        self._selectedPushKey = None # 当前选中项的键值

        self.scrollArea = ScrollArea(self) 
        self.scrollWidget = QWidget() 
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.scrollArea.horizontalScrollBar().setEnabled(False)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True) # 使滚动区域的内容部件可调整大小（根据内容自动调整滚动区域大小）
        self.scrollArea.scrollDelagate.vScrollBar.setHandleDisplayMode(ScrollBarHandleDisplayMode.ON_HOVER) # 垂直滚动条仅在悬停时显示句柄

        self.menuButton = NavigationToolButton(FIF.MENU, self)
        self.menuButton.installEventFilter(ToolTipFilter(self.menuButton, 500))
        self.menuButton.setToolTip("打开导航")


        
       

        self.expandAni = QPropertyAnimation(self, b'geometry', self) 
        self.expandAni.setEasingCurve(QEasingCurve.OutQuad) 
        self.expandAni.setDuration(150)
    
        self.displayMode = NavigationDisplayMode.COMPACT 

        self.window().installEventFilter(self) 

        self.menuButton.clicked.connect(self.toggle)
        self.expandAni.finished.connect(self._onExpandAniFinished)

        self.setProperty('menu', False)
        
        self.scrollWidget.setObjectName('scrollWidget')

        self._init_ui() 

    def _init_ui(self):

        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self.scrollWidget)

        self.vBoxLayout = QVBoxLayout(self)
        self.topLayout = QVBoxLayout()
        self.bottomLayout = QVBoxLayout()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        
        self.vBoxLayout.setContentsMargins(0, 5, 0, 5) 
        self.topLayout.setContentsMargins(4, 48, 4, 0)
        self.bottomLayout.setContentsMargins(4, 0, 4, 0)
        self.scrollLayout.setContentsMargins(4, 0, 4, 0)
        self.vBoxLayout.setSpacing(4)
        self.topLayout.setSpacing(4)
        self.bottomLayout.setSpacing(4)
        self.scrollLayout.setSpacing(4)

        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.topLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.bottomLayout.setAlignment(Qt.AlignBottom)

        self.topLayout.addWidget(self.menuButton, 0, Qt.AlignTop)

        self.vBoxLayout.addLayout(self.topLayout, 0)
        self.vBoxLayout.addWidget(self.scrollArea, 1)
        self.vBoxLayout.addLayout(self.bottomLayout, 0) 


    def widget(self, routeKey: str):
        """ 根据路由键获取导航项部件"""
        if routeKey not in self.items:
            raise Exception(f"`{routeKey}` 是非法路由键（不存在）")

        return self.items[routeKey]


    def insertItem(self, index: int, routeKey: str, icon:FluentIconBase, text: str, onClick=None,
                                position=NavigationItemPosition.TOP, tooltip: str = None) -> NavigationPushButton:
        """ 插入导航树项（创建标准树形导航项并插入到指定位置）"""

        if routeKey in self.items.keys():
            return 
        if position in [NavigationItemPosition.TOP, NavigationItemPosition.BOTTOM]:

            w = NavigationPushButton(icon, text, self)
        else:
            w = NavigationIconButton(icon, text, self)

        self._registerWidget(routeKey, w, onClick, tooltip)

        self._insertWidgetToLayout(index, w, position)

        return w

    def insertSeparator(self, index: int, position=NavigationItemPosition.TOP):

        separator = NavigationSeparator(self) 

        self._insertWidgetToLayout(index, separator, position)

    def _registerWidget(self, routeKey: str, widget: NavigationWidget, onClick, tooltip: str):
        """ 注册导航部件（内部方法，绑定事件、属性和工具提示）"""
        
        if isinstance(widget, NavigationIconButton):
            widget.clicked.connect(lambda: self.setCurrentItem(routeKey, isScrollItem=True))
        else:
            widget.clicked.connect(lambda: self.setCurrentItem(routeKey))
        
        if onClick is not None:
            widget.clicked.connect(onClick)

        self.items[routeKey] = widget

        if self.displayMode in [NavigationDisplayMode.EXPAND, NavigationDisplayMode.MENU]:
            widget.setCompacted(False) # 展开模式下，所有导航项部件都不紧凑显示

        if tooltip:
            widget.setToolTip(tooltip)
            widget.installEventFilter(NavigationToolTipFilter(widget, 1000))

    def _insertWidgetToLayout(self, index: int, widget: NavigationWidget, position: NavigationItemPosition):
        """ 将部件插入到指定位置的布局（内部方法，处理布局添加逻辑）"""

        if position == NavigationItemPosition.TOP:
            widget.setParent(self)
            self.topLayout.insertWidget(index, widget, 0, Qt.AlignTop)
        elif position == NavigationItemPosition.SCROLL:
            widget.setParent(self.scrollWidget)
            self.scrollLayout.insertWidget(index, widget, 0, Qt.AlignTop)
        else:
            widget.setParent(self)
            self.bottomLayout.insertWidget(index, widget, 0, Qt.AlignBottom)

        widget.show()

    def setExpandWidth(self, width: int):
        """ 设置展开模式下的宽度（最小42px，避免过窄无法显示内容）"""

        if width <= 50:
            return 

        self.expandWidth = width
        NavigationWidget.EXPAND_WIDTH = width - 10

    def expand(self, useAni=True):
        """ 展开导航栏（从紧凑/最小化模式切换到展开/菜单模式）"""

        self._setWidgetCompacted(False) # 展开模式下，所有导航项部件都不紧凑显示
        self.expandAni.setProperty('expand', True) # 标记动画为"展开"状态
        self.menuButton.setToolTip('关闭导航')
       
        if (self.window().width() >= self.MIN_EXPAND_WIDTH): 
            self.displayMode = NavigationDisplayMode.EXPAND 
        else:
            self.setProperty('menu', True)
            self.setStyle(QApplication.style())
            self.displayMode = NavigationDisplayMode.MENU 
            
            if not self._parent.isWindow():
                pos = self.parent().pos()
                self.setParent(self.window()) 
                self.move(pos)

            self.show()

        if useAni:
            self.displayModeChanged.emit(self.displayMode)
            self.expandAni.setStartValue(QRect(self.pos(), QSize(50, self.height())))
            self.expandAni.setEndValue(QRect(self.pos(), QSize(self.EXPAND_WIDTH, self.height())))
            self.expandAni.start()

        else:
            self.resize(self.expandWidth, self.height())
            self._onExpandAniFinished()

    def collapse(self):
        """ 折叠导航栏（从展开/菜单模式切换到紧凑/最小化模式） """
        if self.expandAni.state() == QPropertyAnimation.Running:
            return

        self.expandAni.setStartValue(
            QRect(self.pos(), QSize(self.width(), self.height())))
        self.expandAni.setEndValue(
            QRect(self.pos(), QSize(50, self.height())))
        self.expandAni.setProperty('expand', False) 
        self.expandAni.start()

        self.menuButton.setToolTip('打开导航')

    def toggle(self):
        """ 切换导航栏显示状态（展开↔折叠） """
        if self.displayMode in [NavigationDisplayMode.COMPACT]:
            self.expand() 
        else:
            self.collapse() 


    def setDisabledItems(self, routeKeys:list[str]):
        """ 设置指定路由键的导航项为禁用状态（批量操作）"""
        
        for k, item in self.items.items():
            if isinstance(item, NavigationIconButton):
                item.setHidden(k in routeKeys)
                    

    #区分滚动区和非滚动区的导航项
    def setCurrentItem(self, routeKey: str, isScrollItem=False): 
        """ 设置当前选中的导航项（高亮显示）"""

        if self._selectedPushKey == routeKey:
            return
    
        if routeKey not in self.items.keys():
            return 
        
        for k, item in self.items.items():
            
            if isScrollItem:
                if isinstance(item, NavigationIconButton):
                    item.setSelected(k == routeKey)
            else:
                self._selectedPushKey = routeKey
                item.setSelected(k == routeKey)
    
    

    def isCollapsed(self):
        return self.displayMode == NavigationDisplayMode.COMPACT

    def eventFilter(self, obj, e: QEvent):
       
        if e.type() == QEvent.MouseButtonRelease: 
            if not self.geometry().contains(e.pos()) and self.displayMode == NavigationDisplayMode.MENU: #
                self.collapse()
        elif e.type() == QEvent.Resize:
            self.collapse()

        return super().eventFilter(obj, e)

    def _onExpandAniFinished(self):
        """ 展开/折叠动画结束回调 """
        if not self.expandAni.property('expand'):
            self.displayMode = NavigationDisplayMode.COMPACT
            self.displayModeChanged.emit(self.displayMode)

        if self.displayMode == NavigationDisplayMode.COMPACT:

            self.setProperty('menu', False)

            self.setStyle(QApplication.style())

            self._setWidgetCompacted(True)

            if not self._parent.isWindow():
                self.setParent(self._parent)
                self.move(0, 0)
                self.show()

    def _setWidgetCompacted(self, isCompacted: bool):
        """ 设置所有导航部件的紧凑模式状态（显示/隐藏文本）"""
        for item in self.findChildren(NavigationWidget): # 遍历所有导航项部件
            item.setCompacted(isCompacted)

