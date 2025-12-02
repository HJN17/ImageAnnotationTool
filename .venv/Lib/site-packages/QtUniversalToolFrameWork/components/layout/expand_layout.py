# coding:utf-8

from PyQt5.QtCore import QSize, QPoint, Qt, QEvent, QRect
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QLayout, QWidget

class ExpandLayout(QLayout): 
    """ 
    扩展布局管理器类，继承自QLayout，用于实现垂直方向的动态布局管理。
    特点：
    - 所有组件在垂直方向依次排列，宽度一致（填满可用空间）
    - 支持组件显示/隐藏状态识别，隐藏组件不占用布局空间
    - 自动响应组件大小变化（尤其是高度变化），并调整父窗口尺寸
    - 支持布局边距（margins）和组件间距（spacing）配置
    适用于需要垂直排列且组件高度可能动态变化的场景，如可展开的设置面板、动态内容列表等。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__items = [] # 布局项列表：存储通过addItem添加的QLayoutItem对象
        self.__widgets = [] # 组件列表：存储通过addWidget添加的QWidget对象，用于布局计算和位置调整

    def addWidget(self, widget: QWidget):
        if widget in self.__widgets:
            return
        
        self.__widgets.append(widget)
        widget.installEventFilter(self)

    def addItem(self, item):
        self.__items.append(item)

    def count(self):
        return len(self.__items)

    def itemAt(self, index):
        # 索引有效性检查
        if 0 <= index < len(self.__items):
            return self.__items[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self.__items):
            # 同步移除组件列表中的对应组件
            self.__widgets.pop(index)
            return self.__items.pop(index)
        return None

    def expandingDirections(self):
        """ 返回布局可扩展方向：垂直方向 """
        return Qt.Vertical

    def hasHeightForWidth(self):
        """ 返回True：表示布局的高度计算依赖于当前宽度（如宽度变化时，高度可能需要重新计算） """
        return True 

    def heightForWidth(self, width):
        """ 根据给定宽度计算布局所需的最小高度 """
        return self.__doLayout(QRect(0, 0, width, 0), False)


    def setGeometry(self, rect):
        """ 设置布局几何区域：重写QLayout的setGeometry方法，当布局位置或大小变化时调用 """
        super().setGeometry(rect)
        self.__doLayout(rect, True) # 调用__doLayout调整组件位置：move=True表示实际移动组件到计算出的位置

    def sizeHint(self):
        """ 获取推荐尺寸：重写QLayout的sizeHint方法，返回布局的推荐大小 """
        return self.minimumSize()

    def minimumSize(self):
        """ 获取最小尺寸：重写QLayout的minimumSize方法，计算布局所需的最小尺寸 """
    
        size = QSize()

        for w in self.__widgets:
            size = size.expandedTo(w.minimumSize()) #expandedTo 方法：返回一个新的QSize对象，其宽度和高度分别是当前尺寸和组件最小尺寸的较大值

        m = self.contentsMargins() # 获取布局边距
        size += QSize(m.left() + m.right(), m.top() + m.bottom())

        return size

    def __doLayout(self, rect, move):
        """ 根据窗口尺寸调整组件位置 
        
        参数:
            rect (QRect): 布局可用的矩形区域（包含布局的位置和大小）
            move (bool): 是否实际移动组件到计算出的位置（True=移动，False=仅计算高度）
        """
        margin = self.contentsMargins()
        x = rect.x() + margin.left()
        y = rect.y() + margin.top()
        # 计算组件可用宽度：布局矩形宽度 - 左边距 - 右边距（确保组件不超出布局区域）
        width = rect.width() - margin.left() - margin.right()

        for i, w in enumerate(self.__widgets):
            # 跳过隐藏组件：隐藏的组件不占用布局空间
            if w.isHidden():
                continue

            # 添加组件间距：如果不是第一个组件（i>0），在组件上方添加spacing()指定的间距
            y += (i > 0) * self.spacing()
            # 移动组件（如果需要）：设置组件的几何区域（位置为(x,y)，宽度为可用宽度，高度为组件自身高度）
            if move:
                w.setGeometry(QRect(QPoint(x, y), QSize(width, w.height())))

            # 更新y坐标：将y移动到当前组件下方，为下一个组件预留空间
            y += w.height()

        # 返回布局总高度：布局底部相对于rect顶部的偏移量（即整个布局所需的高度）
        return y - rect.y()

    def eventFilter(self, obj, e):
       
        if obj in self.__widgets:    # 检查事件源是否为布局管理的组件：仅处理__widgets列表中的组件事件
          
            if e.type() == QEvent.Resize:
                # 构造QResizeEvent对象：获取尺寸变化信息（新尺寸和旧尺寸）
                re = QResizeEvent(e)
                # 计算尺寸变化量：新尺寸 - 旧尺寸（QSize对象，包含宽和高的变化）
                ds = re.size() - re.oldSize()  # type:QSize
                # 仅处理高度变化且宽度无变化的情况：避免水平变化触发垂直布局调整
                if ds.height() != 0 and ds.width() == 0:
                    # 获取父窗口：通过布局的父组件获取顶级窗口（假设布局的父组件是窗口）
                    w = self.parentWidget()
                    # 调整父窗口高度：窗口高度 += 组件高度变化量（保持宽度不变）
                    w.resize(w.width(), w.height() + ds.height())

        return super().eventFilter(obj, e)
