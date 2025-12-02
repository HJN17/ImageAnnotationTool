# 导入必要的模块
from typing import List, Union
from PyQt5.QtCore import QSize, Qt, QRectF, pyqtSignal, QPoint, QTimer, QEvent, QAbstractItemModel, pyqtProperty, QModelIndex,QSortFilterProxyModel
from PyQt5.QtGui import QPainter, QPainterPath, QIcon, QColor
from PyQt5.QtWidgets import (QApplication, QAction, QHBoxLayout, QLineEdit, QToolButton, QTextEdit,
                             QPlainTextEdit, QCompleter, QStyle, QWidget, QTextBrowser)


from ...common.style_sheet import FluentStyleSheet, themeColor
from ...common.icon import isDarkTheme, FluentIconBase, drawIcon 
from ...common.icon import FluentIcon as FIF 
from ...common.font import setFont
from ...common.color import FluentSystemColor, autoFallbackThemeColor  # 导入系统颜色和自动回退主题颜色


from .tool_tip import ToolTipFilter
from .menu import LineEditMenu, TextEditMenu, RoundMenu, MenuAnimationType, IndicatorMenuItemDelegate
from .scroll_bar import SmoothScrollDelegate


class LineEditButton(QToolButton):
    """ 行编辑按钮组件，继承自QToolButton，用于在行编辑框中显示图标按钮 
    
    该组件专门为LineEdit系列组件设计，提供了统一的按钮样式和交互行为。
    支持设置图标、动作，以及按压状态的视觉反馈。
    """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], parent=None):
        """ 初始化行编辑按钮
        
        :param icon: 按钮图标，可以是字符串路径、QIcon对象或FluentIconBase图标
        :param parent: 父部件
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self._icon = icon  # 存储图标
        self._action = None  # 存储关联的动作
        self.isPressed = False  # 按压状态标志
        self.setFixedSize(16, 16)  # 设置按钮固定大小
        self.setCursor(Qt.PointingHandCursor)  # 设置鼠标指针为手形
        self.setObjectName('lineEditButton')  # 设置对象名，用于样式表选择
        FluentStyleSheet.LINE_EDIT.apply(self)  # 应用行编辑样式表

    def setAction(self, action: QAction):
        """ 设置按钮关联的动作
        
        :param action: QAction对象，包含图标、文本、工具提示等信息
        """
        self._action = action  # 存储动作
        self._onActionChanged()  # 初始化动作相关属性

        self.clicked.connect(action.trigger)  # 连接点击信号到动作的触发槽
        action.toggled.connect(self.setChecked)  # 连接动作的切换信号到按钮的设置选中状态槽
        action.changed.connect(self._onActionChanged)  # 连接动作的变化信号到动作变化处理槽

        self.installEventFilter(ToolTipFilter(self, 700))  # 安装工具提示过滤器，延迟700毫秒显示

    def _onActionChanged(self):
        """ 动作属性变化时的处理槽函数
        
        当关联的动作属性（如图标、工具提示、启用状态等）发生变化时，更新按钮相应属性。
        """
        action = self.action()  # 获取当前关联的动作
        self.setIcon(action.icon())  # 设置按钮图标
        self.setToolTip(action.toolTip())  # 设置按钮工具提示
        self.setEnabled(action.isEnabled())  # 设置按钮启用状态
        self.setCheckable(action.isCheckable())  # 设置按钮是否可选中
        self.setChecked(action.isChecked())  # 设置按钮选中状态

    def action(self):
        """ 获取当前关联的动作
        
        :return: QAction对象，如果没有关联动作则返回None
        """
        return self._action  # 返回存储的动作

    def setIcon(self, icon: Union[str, FluentIconBase, QIcon]):
        """ 设置按钮图标
        
        :param icon: 新的图标，可以是字符串路径、FluentIconBase图标或QIcon对象
        """
        self._icon = icon  # 更新存储的图标
        self.update()  # 触发重绘

    def mousePressEvent(self, e):
        """ 鼠标按下事件处理
        
        :param e: QMouseEvent对象，包含鼠标事件信息
        """
        self.isPressed = True  # 设置按压状态标志为True
        super().mousePressEvent(e)  # 调用父类的鼠标按下事件处理

    def mouseReleaseEvent(self, e):
        """ 鼠标释放事件处理
        
        :param e: QMouseEvent对象，包含鼠标事件信息
        """
        self.isPressed = False  # 设置按压状态标志为False
        super().mouseReleaseEvent(e)  # 调用父类的鼠标释放事件处理

    def paintEvent(self, e):
        """ 绘制事件处理
        
        :param e: QPaintEvent对象，包含绘制事件信息
        """
        super().paintEvent(e)  # 调用父类的绘制事件处理
        painter = QPainter(self)  # 创建绘制器
        painter.setRenderHints(QPainter.Antialiasing |  # 设置渲染提示：抗锯齿
                               QPainter.SmoothPixmapTransform)  # 平滑像素变换

        # iw, ih = self.iconSize().width(), self.iconSize().height()  # 获取图标大小
        w, h = self.width(), self.height()  # 获取按钮大小
        rect = QRectF(4, 4, w-8, h-8)  # 计算图标绘制区域（居中）

        if self.isPressed:  # 如果按钮处于按压状态
            painter.setOpacity(0.7)  # 设置透明度为0.7

        if isDarkTheme():  # 如果当前是深色主题
            drawIcon(self._icon, painter, rect)  # 绘制图标，使用默认颜色
        else:  # 如果当前是浅色主题
            drawIcon(self._icon, painter, rect, fill='#656565')  # 绘制图标，使用指定颜色


class FuzzyProxyModel(QSortFilterProxyModel):
    """
    一个实现了模糊匹配的代理模型。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterRole(Qt.DisplayRole)

        self._filter_text = "" # 用于存储当前过滤文本的实例变量

    def setFilterFixedString(self, pattern):
        """
        重写 setFilterFixedString 方法，将过滤文本保存到我们自己的变量中。
        """
        self._filter_text = pattern.strip() # 去除首尾空格并保存

        super().setFilterFixedString(pattern)

    def filterAcceptsRow(self, source_row, source_parent):
        """
        重写此方法来实现自定义过滤逻辑。
        """
        # 直接使用我们自己存储的 _filter_text
        filter_text = self._filter_text
        
        # 如果过滤文本为空，则显示所有行
        if not filter_text:
            return True

        source_model = self.sourceModel()
        if not source_model:
            return False

        index = source_model.index(source_row, self.filterKeyColumn(), source_parent)
        if not index.isValid():
            return False
        
        item_text = source_model.data(index, self.filterRole())
        if not item_text:
            return False

        if self.filterCaseSensitivity() == Qt.CaseInsensitive:
            # 检查 filter_text 是否是 item_text 的子串
            return filter_text.lower() in item_text.lower()
        else:
            return filter_text in item_text


class LineEdit(QLineEdit):
    """ 行编辑组件，继承自QLineEdit，提供了增强的功能和样式
    
    该组件扩展了QLineEdit，添加了自定义按钮、清除功能、自动完成菜单等特性，
    并支持错误状态显示和自定义聚焦边框颜色。
    """

    def __init__(self, parent=None):
        """ 初始化行编辑组件
        
        :param parent: 父部件
        """
        super().__init__(parent=parent)
        self._fuzzy_proxy_model = FuzzyProxyModel(self) # 创建一个代理模型实例
        self._isClearButtonEnabled = False  # 清除按钮是否启用的标志
        self._completer = None  # 自动完成器对象
        self._completerMenu = None  # 自动完成菜单对象
        self._isError = False  # 错误状态标志
        self.lightFocusedBorderColor = QColor()  # 浅色主题下的聚焦边框颜色
        self.darkFocusedBorderColor = QColor()  # 深色主题下的聚焦边框颜色

        self.leftButtons = []   # 左侧按钮列表
        self.rightButtons = []  # 右侧按钮列表

        self.setProperty("transparent", True)  # 设置透明属性
        FluentStyleSheet.LINE_EDIT.apply(self)  # 应用行编辑样式表
        self.setFixedHeight(31)  # 设置固定高度
        self.setAttribute(Qt.WA_MacShowFocusRect, False)  # 禁用Mac系统默认聚焦矩形
        setFont(self)  # 设置字体

        self.hBoxLayout = QHBoxLayout(self)  # 创建水平布局
        self.clearButton = LineEditButton(FIF.CLOSE, self)  # 创建清除按钮，使用关闭图标

        self.clearButton.setFixedSize(27, 23)  # 设置清除按钮大小
        self.clearButton.hide()  # 初始隐藏清除按钮

        self.hBoxLayout.setSpacing(0)  # 设置布局内控件间距
        self.hBoxLayout.setContentsMargins(2, 2, 4, 2)  # 设置布局边距
        self.hBoxLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 设置布局对齐方式
        self.hBoxLayout.addWidget(self.clearButton, 0, Qt.AlignRight)  # 添加清除按钮到布局

        self.clearButton.clicked.connect(self.clear)  # 连接清除按钮的点击信号到clear槽函数
        self.textChanged.connect(self.__onTextChanged)  # 连接文本变化信号到__onTextChanged槽函数
        self.textEdited.connect(self.__onTextEdited)  # 连接文本编辑信号到__onTextEdited槽函数

    def isError(self):
        """ 获取错误状态
        
        :return: bool - True表示处于错误状态，False表示正常状态
        """
        return self._isError  # 返回错误状态标志

    def setError(self, isError: bool):
        """ 设置错误状态
        
        :param isError: bool - True表示设置为错误状态，False表示恢复正常状态
        """
        if isError == self.isError():  # 如果新状态与当前状态相同
            return  # 直接返回，不做处理

        self._isError = isError  # 更新错误状态标志
        self.update()  # 触发重绘以更新视觉效果

    def setCustomFocusedBorderColor(self, light, dark):
        """ 设置聚焦状态下的边框颜色
        
        :param light: 浅色主题下的边框颜色，可以是字符串、QColor对象或Qt全局颜色
        :param dark: 深色主题下的边框颜色，可以是字符串、QColor对象或Qt全局颜色
        """
        self.lightFocusedBorderColor = QColor(light)  # 设置浅色主题下的边框颜色
        self.darkFocusedBorderColor = QColor(dark)  # 设置深色主题下的边框颜色
        self.update()  # 触发重绘以更新视觉效果

    def focusedBorderColor(self):
        """ 获取聚焦状态下的边框颜色
        
        根据当前主题和错误状态返回相应的边框颜色。
        
        :return: QColor - 聚焦状态下的边框颜色
        """
        if self.isError():  # 如果处于错误状态
            return FluentSystemColor.CRITICAL_FOREGROUND.color()  # 返回系统错误颜色

        return autoFallbackThemeColor(self.lightFocusedBorderColor, self.darkFocusedBorderColor)  # 根据主题返回对应的边框颜色

    def setClearButtonEnabled(self, enable: bool):
        """ 设置清除按钮是否启用
        
        :param enable: bool - True表示启用清除按钮，False表示禁用
        """
        self._isClearButtonEnabled = enable  # 更新清除按钮启用标志
        self._adjustTextMargins()  # 调整文本边距以适应按钮

    def isClearButtonEnabled(self) -> bool:
        """ 获取清除按钮是否启用
        
        :return: bool - True表示清除按钮已启用，False表示禁用
        """
        return self._isClearButtonEnabled  # 返回清除按钮启用标志

    def setCompleter(self, completer: QCompleter):
        """ 设置自动完成器
        
        :param completer: QCompleter - 自动完成器对象
        """
        self._completer = completer  # 存储自动完成器

    def completer(self):
        """ 获取自动完成器
        
        :return: QCompleter - 自动完成器对象，如果没有设置则返回None
        """
        return self._completer  # 返回自动完成器

    def addAction(self, action: QAction, position=QLineEdit.ActionPosition.TrailingPosition):
        """ 添加动作按钮到行编辑框
        
        :param action: QAction - 要添加的动作对象
        :param position: 按钮位置，默认为右侧位置
        """
        QWidget.addAction(self, action)  # 调用父类方法添加动作

        button = LineEditButton(action.icon())  # 创建行编辑按钮，使用动作的图标
        button.setAction(action)  # 设置按钮关联的动作
        button.setFixedWidth(29)  # 设置按钮固定宽度

        if position == QLineEdit.ActionPosition.LeadingPosition:  # 如果是左侧位置
            self.hBoxLayout.insertWidget(len(self.leftButtons), button, 0, Qt.AlignLeading)  # 插入按钮到左侧
            if not self.leftButtons:  # 如果左侧按钮列表为空
                self.hBoxLayout.insertStretch(1, 1)  # 在位置1插入伸缩项

            self.leftButtons.append(button)  # 添加按钮到左侧按钮列表
        else:  # 如果是右侧位置
            self.rightButtons.append(button)  # 添加按钮到右侧按钮列表
            self.hBoxLayout.addWidget(button, 0, Qt.AlignRight)  # 添加按钮到布局右侧

        self._adjustTextMargins()  # 调整文本边距以适应按钮

    def addActions(self, actions, position=QLineEdit.ActionPosition.TrailingPosition):
        """ 批量添加动作按钮到行编辑框
        
        :param actions: 动作对象列表
        :param position: 按钮位置，默认为右侧位置
        """
        for action in actions:  # 遍历所有动作
            self.addAction(action, position)  # 添加每个动作

    def _adjustTextMargins(self):
        """ 调整文本边距以适应按钮
        
        根据左侧和右侧按钮的数量计算并设置适当的文本边距，确保文本不被按钮遮挡。
        """
        left = len(self.leftButtons) * 24  # 左侧边距 = 左侧按钮数量 * 30
        right = len(self.rightButtons) * 24 + 22 * self.isClearButtonEnabled()  # 右侧边距 = 右侧按钮数量 * 30 + 清除按钮宽度（如果启用）
        m = self.textMargins()  # 获取当前文本边距
        print(left, right, m.top(), m.bottom())
        self.setTextMargins(left, m.top(), right, m.bottom())  # 设置新的文本边距

    def focusOutEvent(self, e):
        """ 失去焦点事件处理
        
        :param e: QFocusEvent对象，包含焦点事件信息
        """
        super().focusOutEvent(e)  # 调用父类的失去焦点事件处理
        self.clearButton.hide()  # 隐藏清除按钮

    def focusInEvent(self, e):
        """ 获得焦点事件处理
        
        :param e: QFocusEvent对象，包含焦点事件信息
        """
        super().focusInEvent(e)  # 调用父类的获得焦点事件处理
        if self.isClearButtonEnabled():  # 如果清除按钮已启用
            self.clearButton.setVisible(bool(self.text()))  # 根据文本是否为空显示或隐藏清除按钮

    def __onTextChanged(self, text):
        """ 文本变化槽函数
        
        :param text: str - 变化后的文本
        """
        if self.isClearButtonEnabled():  # 如果清除按钮已启用
            self.clearButton.setVisible(bool(text) and self.hasFocus())  # 根据文本是否为空和是否有焦点显示或隐藏清除按钮

    def __onTextEdited(self, text):
        """ 文本编辑槽函数
        
        :param text: str - 编辑后的文本
        """
        if not self.completer():  # 如果没有设置自动完成器
            return  # 直接返回

        if self.text():  # 如果文本不为空
            QTimer.singleShot(50, self._showCompleterMenu)  # 延迟50毫秒显示自动完成菜单
        elif self._completerMenu:  # 如果文本为空且自动完成菜单存在
            self._completerMenu.close()  # 关闭自动完成菜单

    def setCompleterMenu(self, menu):
        """ 设置自动完成菜单
        
        :param menu: CompleterMenu - 自动完成菜单对象
        """

        # 在连接新菜单之前，断开与旧菜单的所有连接
        if self._completerMenu:
            # 断开所有由 self._completerMenu 发出的信号连接
            self._completerMenu.activated.disconnect()
            self._completerMenu.indexActivated.disconnect()

        # 确保有 completer 再进行连接，增加代码健壮性
        current_completer = self.completer()
        if current_completer and menu:
            # 连接菜单的 activated 信号到 completer 的 activated[str] 信号
            menu.activated.connect(current_completer.activated[str])

            # 直接指定信号的类型，避免使用 lambda 和直接访问内部 _completer
            menu.indexActivated.connect(current_completer.activated[QModelIndex])

        # 存储新的菜单
        self._completerMenu = menu

    

    def _showCompleterMenu(self):
        """ 显示自动完成菜单
        
        检查条件并显示自动完成菜单，根据自动完成器的模型和列填充菜单内容。
        """
        current_completer = self.completer()
        if not current_completer or not self.text().strip():  # 如果没有自动完成器或文本为空
            return  # 直接返回

        # 创建菜单
        if not self._completerMenu:  # 如果自动完成菜单不存在
            self.setCompleterMenu(CompleterMenu(self))  # 创建并设置自动完成菜单



        # --- 核心改动开始 ---
        
        # 1. 获取原始的完成模型
        source_model = current_completer.completionModel()
        if not source_model:
            return

        # 2. 将原始模型设置为模糊代理模型的源模型
        self._fuzzy_proxy_model.setSourceModel(source_model)
        
        # 3. 设置要过滤的列（通常是第0列）
        self._fuzzy_proxy_model.setFilterKeyColumn(current_completer.completionColumn())

        # 4. 将输入框的当前文本设置为代理模型的过滤文本
        self._fuzzy_proxy_model.setFilterFixedString(self.text())
        
        # --- 核心改动结束 ---

        # 5. 将 FILTERED MODEL (代理模型) 传递给 CompleterMenu
        changed = self._completerMenu.setCompletion(
            self._fuzzy_proxy_model,  # <-- 这里不再是 source_model
            current_completer.completionColumn()
        )


        # 添加菜单项
        # self.completer().setCompletionPrefix(self.text())  # 设置自动完成的前缀文本

        # changed = self._completerMenu.setCompletion(
        #     current_completer.completionModel(),
        #     current_completer.completionColumn()
        # )

        self._completerMenu.setMaxVisibleItems(current_completer.maxVisibleItems())

        if changed:
            # 调用 popup 时可以指定一个全局位置，这里我们让菜单自己决定最佳位置
            # QCompleter 通常会将菜单显示在输入框下方
            self._completerMenu.popup()

    def contextMenuEvent(self, e):
        """ 上下文菜单事件处理
        
        :param e: QContextMenuEvent对象，包含上下文菜单事件信息
        """
        menu = LineEditMenu(self)  # 创建行编辑菜单
        menu.exec_(e.globalPos())  # 在鼠标位置显示菜单

    def paintEvent(self, e):
        """ 绘制事件处理
        
        :param e: QPaintEvent对象，包含绘制事件信息
        """
        super().paintEvent(e)  # 调用父类的绘制事件处理
        if not self.hasFocus():  # 如果没有焦点
            return  # 直接返回

        painter = QPainter(self)  # 创建绘制器
        painter.setRenderHints(QPainter.Antialiasing)  # 设置渲染提示：抗锯齿
        painter.setPen(Qt.NoPen)  # 设置画笔为无边框

        m = self.contentsMargins()  # 获取内容边距
        path = QPainterPath()  # 创建绘制路径
        w, h = self.width()-m.left()-m.right(), self.height()  # 计算内容区域宽度和高度
        path.addRoundedRect(QRectF(m.left(), h-10, w, 10), 5, 5)  # 添加圆角矩形路径

        rectPath = QPainterPath()  # 创建矩形路径
        rectPath.addRect(m.left(), h-10, w, 8)  # 添加矩形路径
        path = path.subtracted(rectPath)  # 从圆角矩形路径中减去矩形路径，创建底部圆弧效果

        painter.fillPath(path, self.focusedBorderColor())  # 使用聚焦边框颜色填充路径

class CompleterMenu(RoundMenu):
    """ 自动完成菜单，继承自RoundMenu，用于显示自动完成选项
    
    该组件提供了一个自定义的自动完成菜单，支持通过模型数据设置菜单项，
    并提供了动画效果和键盘导航功能。
    """

    activated = pyqtSignal(str)  # 激活信号，传递选中的文本
    indexActivated = pyqtSignal(QModelIndex)  # 索引激活信号，传递选中的模型索引

    def __init__(self, lineEdit: LineEdit):
        """ 初始化自动完成菜单
        
        :param lineEdit: LineEdit - 关联的行编辑组件
        """
        super().__init__()  # 调用父类构造函数
        self.items = []  # 菜单项文本列表
        self.indexes = []  # 菜单项对应的模型索引列表
        self.lineEdit = lineEdit  # 关联的行编辑组件

        self.view.setViewportMargins(0, 2, 0, 6)  # 设置视图的视口边距
        self.view.setObjectName('completerListWidget')  # 设置视图对象名，用于样式表选择
        self.view.setItemDelegate(IndicatorMenuItemDelegate())  # 设置项目代理，提供指示器样式
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 设置垂直滚动条策略为需要时显示

        self.installEventFilter(self)  # 安装事件过滤器到自身
        self.setItemHeight(33)  # 设置项目高度

    def setCompletion(self, model: QAbstractItemModel, column=0):
        """ 设置自动完成模型
        
        :param model: QAbstractItemModel - 提供自动完成数据的模型
        :param column: int - 从模型中获取数据的列索引，默认为0
        :return: bool - True表示菜单项有变化，False表示无变化
        """
        items = []  # 临时存储菜单项文本
        self.indexes.clear()  # 清空索引列表
        for i in range(model.rowCount()):  # 遍历模型的所有行
            items.append(model.data(model.index(i, column)))  # 获取指定行列的数据并添加到列表
            self.indexes.append(model.index(i, column))  # 存储对应的模型索引

        if self.items == items and self.isVisible():  # 如果新菜单项与当前菜单项相同且菜单可见
            return False  # 返回False表示无变化

        self.setItems(items)  # 设置菜单项
        return True  # 返回True表示有变化

    def setItems(self, items: List[str]):
        """ 设置自动完成菜单项
        
        :param items: List[str] - 菜单项文本列表
        """
        self.view.clear()  # 清空视图

        self.items = items  # 存储菜单项文本列表
        self.view.addItems(items)  # 向视图添加所有菜单项

        for i in range(self.view.count()):  # 遍历所有菜单项
            item = self.view.item(i)  # 获取当前菜单项
            item.setSizeHint(QSize(1, self.itemHeight))  # 设置菜单项的大小提示

    def _onItemClicked(self, item):
        """ 菜单项点击处理槽函数
        
        :param item: QListWidgetItem - 被点击的菜单项
        """
        self._hideMenu(False)  # 隐藏菜单，不触发动画
        self._onCompletionItemSelected(item.text(), self.view.row(item))  # 处理选中的完成项

    def eventFilter(self, obj, e: QEvent):
        """ 事件过滤器
        
        处理菜单的键盘事件，支持Esc键关闭菜单，Enter/Return键选择当前项。
        
        :param obj: QObject - 事件发送者
        :param e: QEvent - 事件对象
        :return: bool - True表示事件已处理，False表示未处理
        """
        if e.type() != QEvent.KeyPress:  # 如果不是键盘按下事件
            return super().eventFilter(obj, e)  # 调用父类的事件过滤器

        # 重定向输入到行编辑
        self.lineEdit.event(e)  # 让行编辑处理事件
        self.view.event(e)  # 让视图处理事件

        if e.key() == Qt.Key_Escape:  # 如果按下的是Esc键
            self.close()  # 关闭菜单
        if e.key() in [Qt.Key_Enter, Qt.Key_Return] and self.view.currentRow() >= 0:  # 如果按下的是Enter/Return键且有当前项
            self._onCompletionItemSelected(self.view.currentItem().text(), self.view.currentRow())  # 处理选中的完成项
            self.close()  # 关闭菜单

        return super().eventFilter(obj, e)  # 调用父类的事件过滤器

    def _onCompletionItemSelected(self, text, row):
        """ 完成项选中处理函数
        
        :param text: str - 选中的文本
        :param row: int - 选中项的行索引
        """
        self.lineEdit.setText(text)  # 设置行编辑的文本为选中的文本
        self.activated.emit(text)  # 发射激活信号

        if 0 <= row < len(self.indexes):  # 如果行索引在有效范围内
            self.indexActivated.emit(self.indexes[row])  # 发射索引激活信号

    def popup(self):
        """ 显示菜单
        
        计算菜单的位置和动画类型，然后显示菜单。
        """
        if not self.items:  # 如果没有菜单项
            return self.close()  # 直接关闭菜单

        # 调整菜单大小
        p = self.lineEdit  # 获取关联的行编辑组件
        if self.view.width() < p.width():  # 如果视图宽度小于行编辑宽度
            self.view.setMinimumWidth(p.width())  # 设置视图最小宽度为行编辑宽度
            self.adjustSize()  # 调整菜单大小

        # 根据视图的最大高度确定动画类型
        x = -self.width()//2 + self.layout().contentsMargins().left() + p.width()//2  # 计算x坐标
        y = p.height() - self.layout().contentsMargins().top() + 2  # 计算下拉动画的y坐标
        pd = p.mapToGlobal(QPoint(x, y))  # 转换为全局坐标
        hd = self.view.heightForAnimation(pd, MenuAnimationType.FADE_IN_DROP_DOWN)  # 计算下拉动画所需的高度

        pu = p.mapToGlobal(QPoint(x, 7))  # 计算上拉动画的全局坐标
        hu = self.view.heightForAnimation(pu, MenuAnimationType.FADE_IN_PULL_UP)  # 计算上拉动画所需的高度

        if hd >= hu:  # 如果下拉动画高度大于等于上拉动画高度
            pos = pd  # 使用下拉位置
            aniType = MenuAnimationType.FADE_IN_DROP_DOWN  # 使用下拉动画
        else:  # 如果上拉动画高度大于下拉动画高度
            pos = pu  # 使用上拉位置
            aniType = MenuAnimationType.FADE_IN_PULL_UP  # 使用上拉动画

        self.view.adjustSize(pos, aniType)  # 调整视图大小和位置

        # 更新边框样式
        self.view.setProperty('dropDown', aniType == MenuAnimationType.FADE_IN_DROP_DOWN)  # 设置下拉属性
        self.view.setStyle(QApplication.style())  # 更新样式
        self.view.update()  # 触发视图重绘

        self.adjustSize()  # 调整菜单大小
        self.exec(pos, aniType=aniType)  # 显示菜单，应用指定的动画类型

        # 移除菜单的焦点
        self.view.setFocusPolicy(Qt.NoFocus)  # 设置视图无焦点
        self.setFocusPolicy(Qt.NoFocus)  # 设置菜单无焦点
        p.setFocus()  # 让行编辑获得焦点

class SearchLineEdit(LineEdit):
    """ 搜索行编辑组件，继承自LineEdit，专门用于搜索功能
    
    该组件集成了搜索按钮和清除按钮，并提供了搜索信号和清除信号，
    方便实现搜索功能。
    """

    searchSignal = pyqtSignal(str)  # 搜索信号，传递搜索文本
    clearSignal = pyqtSignal()  # 清除信号，当清除搜索或搜索空文本时发射
    def __init__(self, parent=None):
        """ 初始化搜索行编辑组件
        
        :param parent: 父部件
        """
        super().__init__(parent) 
        self.searchButton = LineEditButton(FIF.SEARCH, self)  # 创建搜索按钮，使用搜索图标
        
        self.hBoxLayout.addWidget(self.searchButton, 0, Qt.AlignRight)  # 添加搜索按钮到布局右侧
        self.setClearButtonEnabled(True)  # 启用清除按钮
        
        self.searchButton.clicked.connect(self.search)  # 连接搜索按钮的点击信号到search槽函数
        self.clearButton.clicked.connect(self.clearSignal)  # 连接清除按钮的点击信号到clearSignal信号

    def search(self):
        """ 执行搜索操作
        
        获取文本并发射搜索信号，如果文本为空则发射清除信号。
        """
        text = self.text().strip()  # 获取文本并去除首尾空格
        if text:  # 如果文本不为空
            self.searchSignal.emit(text)  # 发射搜索信号
        else:  # 如果文本为空
            self.clearSignal.emit()  # 发射清除信号


    def setSearchButtonSize(self, size: int):
        """ 设置搜索按钮的大小
        
        :param size: int - 搜索按钮的大小，单位为像素
        """
        self.searchButton.setFixedSize(size, size)  # 设置搜索按钮的固定大小


    def setClearButtonSize(self, size: int):
        """ 设置清除按钮的大小
        
        :param size: int - 清除按钮的大小，单位为像素
        """
        self.clearButton.setFixedSize(size, size)  # 设置清除按钮的固定大小


    def setClearButtonEnabled(self, enable: bool):
        """ 设置清除按钮是否启用
        
        重写父类方法，以适应搜索按钮的存在。
        
        :param enable: bool - True表示启用清除按钮，False表示禁用
        """
        self._isClearButtonEnabled = enable  # 更新清除按钮启用标志
        self.setTextMargins(0, 0, self.searchButton.width()*enable+self.clearButton.width(), 0)  # 调整文本边距，为清除按钮和搜索按钮留出空间




class CustomLineEdit(QLineEdit):
    """ 自定义行编辑组件，继承自QLineEdit
    
    该组件提供了自定义的行编辑功能，包括文本边距调整和清除按钮。
    """
    valueChanged = pyqtSignal(float)  # 值变化信号，当数字值改变时发射

    def __init__(self, parent=None):
        super().__init__(parent) 

        self.lightFocusedBorderColor = QColor()  # 浅色主题下的聚焦边框颜色
        self.darkFocusedBorderColor = QColor()  # 深色主题下的聚焦边框颜色


        self.textChanged.connect(self._onTextChanged)

        self.setAlignment(Qt.AlignCenter)  # 居中对齐
        FluentStyleSheet.LINE_EDIT.apply(self)  # 应用行编辑样式表
        setFont(self,fontSize=12)  # 设置字体


    def setCustomFocusedBorderColor(self, light, dark):
        """ 设置聚焦状态下的边框颜色
        
        :param light: 浅色主题下的边框颜色，可以是字符串、QColor对象或Qt全局颜色
        :param dark: 深色主题下的边框颜色，可以是字符串、QColor对象或Qt全局颜色
        """
        self.lightFocusedBorderColor = QColor(light)  # 设置浅色主题下的边框颜色
        self.darkFocusedBorderColor = QColor(dark)  # 设置深色主题下的边框颜色
        self.update()  # 触发重绘以更新视觉效果

    def focusedBorderColor(self):
        """ 获取聚焦状态下的边框颜色 """
        
        return autoFallbackThemeColor(self.lightFocusedBorderColor, self.darkFocusedBorderColor)  # 根据主题返回对应的边框颜色

    def setValue(self, value: str):
        """ 设置行编辑的文本值
        
        :param value: str - 要设置的文本值
        """
        self.setText(value)  # 设置文本值

    def value(self) -> str:
        """ 获取行编辑的文本值
        
        :return: str - 当前文本值
        """
        return self.text()  # 返回当前文本值

    def _onTextChanged(self, text):
        """ 文本变化槽函数，覆盖父类方法以处理数字值变化
        
        :param text: str - 变化后的文本
        """

        value = self.value()
        if value is not None:
            self.valueChanged.emit(value)  # 发射值变化信号

    def paintEvent(self, e):
        """ 绘制事件处理
        
        :param e: QPaintEvent对象，包含绘制事件信息
        """
        super().paintEvent(e)  # 调用父类的绘制事件处理
        if not self.hasFocus():  # 如果没有焦点
            return  # 直接返回

        painter = QPainter(self)  # 创建绘制器
        painter.setRenderHints(QPainter.Antialiasing)  # 设置渲染提示：抗锯齿
        painter.setPen(Qt.NoPen)  # 设置画笔为无边框

        m = self.contentsMargins()  # 获取内容边距
        path = QPainterPath()  # 创建绘制路径
        w, h = self.width()-m.left()-m.right(), self.height()  # 计算内容区域宽度和高度
        path.addRoundedRect(QRectF(m.left(), h-10, w, 10), 5, 5)  # 添加圆角矩形路径

        rectPath = QPainterPath()  # 创建矩形路径
        rectPath.addRect(m.left(), h-10, w, 8)  # 添加矩形路径
        path = path.subtracted(rectPath)  # 从圆角矩形路径中减去矩形路径，创建底部圆弧效果

        painter.fillPath(path, self.focusedBorderColor())  # 使用聚焦边框颜色填充路径


class NumberEdit(CustomLineEdit):

    """ 数字行编辑组件，继承自LineEdit，专门用于数字输入和搜索
    
    该组件限制只能输入数字，并集成了搜索按钮，方便进行数值搜索操作。
    支持整数和小数输入，并提供范围限制功能。
    """

    def __init__(self, parent=None, min_value=None, max_value=None):
        """ 初始化数字行编辑组件
        
        :param parent: 父部件
        :param min_value: 允许输入的最小值，None表示无下限
        :param max_value: 允许输入的最大值，None表示无上限
        """
        super().__init__(parent) 

        self._minValue = min_value  # 最小值限制
        self._maxValue = max_value  # 最大值限制
        
        # 连接文本变化信号到_onTextChanged槽函数
        # 验证器设置
        self.setValidator(None)  # 先清除可能的验证器
        self._updateValidator()  # 更新验证器
        self.installEventFilter(self)
    def _updateValidator(self):
        """ 更新输入验证器，限制只能输入整数 """
        from PyQt5.QtGui import QIntValidator
        validator = QIntValidator(self)  # 创建整数验证器
        # 设置范围
        if self._minValue is not None:
            validator.setBottom(self._minValue)  # 设置最小值
        if self._maxValue is not None:
            validator.setTop(self._maxValue)  # 设置最大值
        
        self.setValidator(validator)  # 应用验证器

    def setRange(self, min_value=None, max_value=None):
        """ 设置输入数值的范围
        
        :param min_value: 允许输入的最小值，None表示无下限
        :param max_value: 允许输入的最大值，None表示无上限
        """
        self._minValue = min_value  # 更新最小值
        self._maxValue = max_value  # 更新最大值
        self._updateValidator()  # 更新验证器
        
        # 检查当前值是否在新范围内
        value = self.value()
        if value is not None:
            if (self._minValue is not None and value < self._minValue) or (self._maxValue is not None and value > self._maxValue):
                # 如果当前值超出新范围，则清空
                    self.clear()

    def setValue(self, value):
        """ 设置数字值
        
        :param value: 要设置的数字值
        """
        # 检查值是否在范围内
        if (self._minValue is not None and value < self._minValue) or (self._maxValue is not None and value > self._maxValue):
            return  # 如果超出范围，则不设置
        
        self.setText(str(value))  # 设置文本为数字的字符串表示

    def value(self):
        """ 获取当前输入的数字值
        
        :return: float - 当前输入的数字值，如果无法转换则返回None
        """
        try:
            text = self.text().strip()
            if not text:
                return None
            return int(text)  # 尝试转换为整数
        except ValueError:
            return None  # 转换失败返回None

class EditLayer(QWidget):
    """ 编辑层组件，用于在编辑组件上显示自定义的视觉效果
    
    该组件主要用于在行编辑、文本编辑等组件获得焦点时显示自定义的边框效果，
    增强用户体验。
    """

    def __init__(self, parent):
        """ 初始化编辑层组件
        
        :param parent: QWidget - 父部件，通常是编辑组件
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 设置属性：鼠标事件透明
        parent.installEventFilter(self)  # 为父部件安装事件过滤器

    def eventFilter(self, obj, e):
        """ 事件过滤器
        
        监听父部件的大小变化事件，确保编辑层与父部件大小一致。
        
        :param obj: QObject - 事件发送者
        :param e: QEvent - 事件对象
        :return: bool - True表示事件已处理，False表示未处理
        """
        if obj is self.parent() and e.type() == QEvent.Resize:  # 如果是父部件的大小变化事件
            self.resize(e.size())  # 调整编辑层大小以匹配父部件

        return super().eventFilter(obj, e)  # 调用父类的事件过滤器

    def paintEvent(self, e):
        """ 绘制事件处理
        
        当父部件获得焦点时，绘制自定义的边框效果。
        
        :param e: QPaintEvent对象，包含绘制事件信息
        """
        if not self.parent().hasFocus():  # 如果父部件没有焦点
            return  # 直接返回

        painter = QPainter(self)  # 创建绘制器
        painter.setRenderHints(QPainter.Antialiasing)  # 设置渲染提示：抗锯齿
        painter.setPen(Qt.NoPen)  # 设置画笔为无边框

        m = self.contentsMargins()  # 获取内容边距
        path = QPainterPath()  # 创建绘制路径
        w, h = self.width()-m.left()-m.right(), self.height()  # 计算内容区域宽度和高度
        path.addRoundedRect(QRectF(m.left(), h-10, w, 10), 5, 5)  # 添加圆角矩形路径

        rectPath = QPainterPath()  # 创建矩形路径
        rectPath.addRect(m.left(), h-10, w, 7.5)  # 添加矩形路径
        path = path.subtracted(rectPath)  # 从圆角矩形路径中减去矩形路径，创建底部圆弧效果

        painter.fillPath(path, themeColor())  # 使用主题颜色填充路径


class TextEdit(QTextEdit):
    """ 文本编辑组件，继承自QTextEdit，提供了增强的功能和样式
    
    该组件扩展了QTextEdit，添加了自定义的编辑层和滚动代理，
    并应用了统一的Fluent样式。
    """

    def __init__(self, parent=None):
        """ 初始化文本编辑组件
        
        :param parent: 父部件
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self.layer = EditLayer(self)  # 创建编辑层组件
        self.scrollDelegate = SmoothScrollDelegate(self)  # 创建平滑滚动代理
        FluentStyleSheet.LINE_EDIT.apply(self)  # 应用行编辑样式表
        setFont(self)  # 设置字体

    def contextMenuEvent(self, e):
        """ 上下文菜单事件处理
        
        :param e: QContextMenuEvent对象，包含上下文菜单事件信息
        """
        menu = TextEditMenu(self)  # 创建文本编辑菜单
        menu.exec_(e.globalPos())  # 在鼠标位置显示菜单




    








class PlainTextEdit(QPlainTextEdit):
    """ 纯文本编辑组件，继承自QPlainTextEdit，提供了增强的功能和样式
    
    该组件扩展了QPlainTextEdit，添加了自定义的编辑层和滚动代理，
    并应用了统一的Fluent样式。
    """

    def __init__(self, parent=None):
        """ 初始化纯文本编辑组件
        
        :param parent: 父部件
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self.layer = EditLayer(self)  # 创建编辑层组件
        self.scrollDelegate = SmoothScrollDelegate(self)  # 创建平滑滚动代理
        FluentStyleSheet.LINE_EDIT.apply(self)  # 应用行编辑样式表
        setFont(self)  # 设置字体

    def contextMenuEvent(self, e):
        """ 上下文菜单事件处理
        
        :param e: QContextMenuEvent对象，包含上下文菜单事件信息
        """
        menu = TextEditMenu(self)  # 创建文本编辑菜单
        menu.exec_(e.globalPos())  # 在鼠标位置显示菜单


class TextBrowser(QTextBrowser):
    """ 文本浏览组件，继承自QTextBrowser，提供了增强的功能和样式
    
    该组件扩展了QTextBrowser，添加了自定义的编辑层和滚动代理，
    并应用了统一的Fluent样式。
    """

    def __init__(self, parent=None):
        """ 初始化文本浏览组件
        
        :param parent: 父部件
        """
        super().__init__(parent)  # 调用父类构造函数
        self.layer = EditLayer(self)  # 创建编辑层组件
        self.scrollDelegate = SmoothScrollDelegate(self)  # 创建平滑滚动代理
        FluentStyleSheet.LINE_EDIT.apply(self)  # 应用行编辑样式表
        setFont(self)  # 设置字体

    def contextMenuEvent(self, e):
        """ 上下文菜单事件处理
        
        :param e: QContextMenuEvent对象，包含上下文菜单事件信息
        """
        menu = TextEditMenu(self)  # 创建文本编辑菜单
        menu.exec_(e.globalPos())  # 在鼠标位置显示菜单





class PasswordLineEdit(LineEdit):
    """ 密码行编辑组件，继承自LineEdit，专门用于密码输入
    
    该组件扩展了LineEdit，添加了密码可见性切换功能，
    并默认隐藏上下文菜单以增强安全性。
    """

    def __init__(self, parent=None):
        """ 初始化密码行编辑组件
        
        :param parent: 父部件
        """
        super().__init__(parent)  # 调用父类构造函数
        self.viewButton = LineEditButton(FIF.VIEW, self)  # 创建查看按钮，使用查看图标

        self.setEchoMode(QLineEdit.Password)  # 设置回显模式为密码模式
        self.setContextMenuPolicy(Qt.NoContextMenu)  # 禁用上下文菜单，增强安全性
        self.hBoxLayout.addWidget(self.viewButton, 0, Qt.AlignRight)  # 添加查看按钮到布局右侧
        self.setClearButtonEnabled(False)  # 初始禁用清除按钮

        self.viewButton.installEventFilter(self)  # 为查看按钮安装事件过滤器
        self.viewButton.setIconSize(QSize(13, 13))  # 设置查看按钮的图标大小
        self.viewButton.setFixedSize(29, 25)  # 设置查看按钮的固定大小

    def setPasswordVisible(self, isVisible: bool):
        """ 设置密码是否可见
        
        :param isVisible: bool - True表示密码可见，False表示密码隐藏
        """
        if isVisible:  # 如果密码可见
            self.setEchoMode(QLineEdit.Normal)  # 设置回显模式为普通模式
        else:  # 如果密码隐藏
            self.setEchoMode(QLineEdit.Password)  # 设置回显模式为密码模式

    def isPasswordVisible(self):
        """ 获取密码是否可见
        
        :return: bool - True表示密码可见，False表示密码隐藏
        """
        return self.echoMode() == QLineEdit.Normal  # 返回密码是否为普通回显模式

    def setClearButtonEnabled(self, enable: bool):
        """ 设置清除按钮是否启用
        
        重写父类方法，以适应查看按钮的存在。
        
        :param enable: bool - True表示启用清除按钮，False表示禁用
        """
        self._isClearButtonEnabled = enable  # 更新清除按钮启用标志

        if self.viewButton.isHidden():  # 如果查看按钮隐藏
            self.setTextMargins(0, 0, 28*enable, 0)  # 调整文本边距，为清除按钮留出空间
        else:  # 如果查看按钮可见
            self.setTextMargins(0, 0, 28*enable + 30, 0)  # 调整文本边距，为清除按钮和查看按钮留出空间

    def setViewPasswordButtonVisible(self, isVisible: bool):
        """ 设置查看密码按钮是否可见
        
        :param isVisible: bool - True表示查看按钮可见，False表示隐藏
        """
        self.viewButton.setVisible(isVisible)  # 设置查看按钮的可见性

    def eventFilter(self, obj, e):
        """ 事件过滤器
        
        监听查看按钮的鼠标按下和释放事件，控制密码的可见性。
        
        :param obj: QObject - 事件发送者
        :param e: QEvent - 事件对象
        :return: bool - True表示事件已处理，False表示未处理
        """
        if obj is not self.viewButton or not self.isEnabled():  # 如果不是查看按钮的事件或组件被禁用
            return super().eventFilter(obj, e)  # 调用父类的事件过滤器

        if e.type() == QEvent.MouseButtonPress:  # 如果是鼠标按下事件
            self.setPasswordVisible(True)  # 设置密码可见
        elif e.type() == QEvent.MouseButtonRelease:  # 如果是鼠标释放事件
            self.setPasswordVisible(False)  # 设置密码隐藏

        return super().eventFilter(obj, e)  # 调用父类的事件过滤器

    def inputMethodQuery(self, query: Qt.InputMethodQuery):
        """ 输入法查询
        
        重写父类方法，禁用输入法，增强密码输入的安全性。
        
        :param query: Qt.InputMethodQuery - 查询类型
        :return: 查询结果
        """
        # 为密码行编辑禁用输入法
        if query == Qt.InputMethodQuery.ImEnabled:  # 如果查询是否启用输入法
            return False  # 返回False，表示禁用输入法
        else:  # 其他查询
            return super().inputMethodQuery(query)  # 调用父类的输入法查询

    passwordVisible = pyqtProperty(bool, isPasswordVisible, setPasswordVisible)  # 定义密码可见性属性