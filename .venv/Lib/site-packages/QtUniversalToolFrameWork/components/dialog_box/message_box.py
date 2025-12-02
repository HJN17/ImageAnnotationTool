# coding:utf-8
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from ...common.style_sheet import FluentStyleSheet, setShadowEffect  # 导入样式表
from ...common.auto_wrap import TextWrap  # 导入文本自动换行工具
from ..widgets.button import PrimaryPushButton  # 导入主要按钮组件
from ..widgets.label import BodyLabel,CaptionLabel  # 导入标签组件
from .mask_dialog_base import MaskDialogBase  # 导入带遮罩的对话框基类

from ..widgets.line_edit import LineEdit  # 导入行编辑组件

 

class CustomMessageBoxBase(MaskDialogBase):
    """ 消息框基础类 """

    def __init__(self, parent=None):
        """
            初始化消息框基础类
            
            参数:
                parent: QWidget，父部件，默认为None
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self.buttonGroup = QFrame(self.widget)  # 创建按钮组框架
        self.yesButton = PrimaryPushButton('确定', self.buttonGroup)  # 创建确认按钮
        self.cancelButton = QPushButton('取消', self.buttonGroup)  # 创建取消按钮

        self.vBoxLayout = QVBoxLayout(self.widget)
        self.viewLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout(self.buttonGroup)

        self.__initWidget()  # 初始化小部件

    def __initWidget(self):
        """ 初始化界面部件 """
        self.__setQss()  # 设置样式
        self.__initLayout()  # 初始化布局

        # 设置阴影效果：半径60，偏移(0, 10)，颜色(0, 0, 0, 50)
        setShadowEffect(self.widget, 60, (0, 10), QColor(0, 0, 0, 50))
        # 设置遮罩颜色为半透明黑色
        self.setMaskColor(QColor(0, 0, 0, 120))


        self.yesButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)  # 确认按钮使用小部件矩形布局
        self.cancelButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)  # 取消按钮使用小部件矩形布局
        
         # 在Mac系统上不显示焦点矩形
        self.yesButton.setAttribute(Qt.WA_MacShowFocusRect, False)

        # 设置确认按钮为焦点
        self.yesButton.setFocus()
        # 设置按钮组固定高度
        self.buttonGroup.setFixedHeight(81)

        # 连接信号和槽
        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)

    def __initLayout(self):
        """ 初始化布局 """
        # 重新添加中心部件到布局，使其居中显示
        self._hBoxLayout.removeWidget(self.widget)
        self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignCenter)

        # 设置主垂直布局的间距和边距
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        # 添加视图布局和按钮组到主布局
        self.vBoxLayout.addLayout(self.viewLayout, 1)
        self.vBoxLayout.addWidget(self.buttonGroup, 0, Qt.AlignBottom)

        # 设置视图布局的间距和边距
        self.viewLayout.setSpacing(12)
        self.viewLayout.setContentsMargins(24, 24, 24, 24)

        # 设置按钮布局的间距和边距
        self.buttonLayout.setSpacing(12)
        self.buttonLayout.setContentsMargins(24, 24, 24, 24)
        # 添加确认按钮和取消按钮到按钮布局
        self.buttonLayout.addWidget(self.yesButton, 1, Qt.AlignVCenter)
        self.buttonLayout.addWidget(self.cancelButton, 1, Qt.AlignVCenter)

    def validate(self) -> bool:
        """ 验证表单数据是否合法
        
        Returns
        -------
        isValid: bool
            是否表单数据合法
        """
        return True

    def __onCancelButtonClicked(self):
        """ 取消按钮点击事件处理 """
        self.reject()

    def __onYesButtonClicked(self):
        """ 确认按钮点击事件处理 """
        if self.validate():
            # 如果数据验证通过，接受对话框
            self.accept()

    def __setQss(self):
        """ 设置样式表 """
        # 设置对象名称，用于QSS选择器
        self.buttonGroup.setObjectName('buttonGroup')
        self.cancelButton.setObjectName('cancelButton')
        # 应用样式表
        FluentStyleSheet.DIALOG.apply(self)

    def hideYesButton(self):
        """ 隐藏确认按钮 """
        self.yesButton.hide()  # 隐藏确认按钮
        self.buttonLayout.insertStretch(0, 1)  # 在按钮布局中添加伸缩项

    def hideCancelButton(self):
        """ 隐藏取消按钮 """
        self.cancelButton.hide()  # 隐藏取消按钮
        self.buttonLayout.insertStretch(0, 1)  # 在按钮布局中添加伸缩项



"""
Displayable Components  """

class CustomMessageBox(CustomMessageBoxBase):
    """ 自定义消息框 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel('打开 URL', self)
        self.urlLineEdit = LineEdit(self)

        self.urlLineEdit.setPlaceholderText('输入文件、流或者播放列表的 URL')
        self.urlLineEdit.setClearButtonEnabled(True)

        self.warningLabel = CaptionLabel("The url is invalid")
        self.warningLabel.setTextColor("#cf1010", QColor(255, 28, 32))

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.urlLineEdit)
        self.viewLayout.addWidget(self.warningLabel)
        self.warningLabel.hide()

        # change the text of button
        self.yesButton.setText('打开')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)

        # self.hideYesButton()

    def validate(self):
        """ 验证表单数据是否合法
        
        Returns
        -------
        isValid: bool
            是否表单数据合法
        """
        isValid = self.urlLineEdit.text().lower().startswith("http://")
        self.warningLabel.setHidden(isValid)
        self.urlLineEdit.setError(not isValid)
        return isValid


class MessageBox(MaskDialogBase):
    """ 消息框类 """

    yesSignal = pyqtSignal()  # 确认按钮点击信号
    cancelSignal = pyqtSignal()  # 取消按钮点击信号

    def __init__(self, title: str, content: str, parent=None):
        """
        初始化消息框
        
        参数:
            title: str，对话框标题
            content: str，对话框内容
            parent: QWidget，父部件，默认为None
        """
        super().__init__(parent=parent)  # 调用父类构造函数
        self._setUpUi(title, content, self.widget)  # 设置UI界面


        # 重新添加中心部件到布局，使其居中显示
        self._hBoxLayout.removeWidget(self.widget)
        self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignCenter)

        # 设置按钮组最小宽度
        self.buttonGroup.setMinimumWidth(280)
        # 设置中心部件固定大小
        self.widget.setFixedSize(
            # 宽度为内容标签和标题标签宽度的较大值加48
            max(self.contentLabel.width(), self.titleLabel.width()) + 48,
            # 高度为内容标签的y坐标加内容标签高度加105
            self.contentLabel.y() + self.contentLabel.height() + 105
        )


    def _setUpUi(self, title, content, parent):
        """
            设置UI界面
            
            参数:
                title: str，对话框标题
                content: str，对话框内容
                parent: QWidget，父部件
        """
        self.content = content  # 保存内容文本
        self.titleLabel = QLabel(title, parent)  # 创建标题标签
        self.contentLabel = BodyLabel(content, parent)  # 创建内容标签

        self.buttonGroup = QFrame(parent)  # 创建按钮组框架
        self.yesButton = PrimaryPushButton("确定", self.buttonGroup)  # 创建确认按钮
        self.cancelButton = QPushButton("取消", self.buttonGroup)  # 创建取消按钮

        self.vBoxLayout = QVBoxLayout(parent)  # 创建垂直布局管理器
        self.textLayout = QVBoxLayout()  # 创建文本区域的垂直布局
        self.buttonLayout = QHBoxLayout(self.buttonGroup)  # 创建按钮区域的水平布局

        self.__initWidget()

    def __initWidget(self):
        """ 初始化界面部件 """
        self.__setQss()  # 设置样式
        self.__initLayout()  # 初始化布局

        # 设置按钮属性，使其正确响应布局管理器
        self.yesButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)
        self.cancelButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        # 设置确认按钮为焦点
        self.yesButton.setFocus()
        # 设置按钮组固定高度
        self.buttonGroup.setFixedHeight(81)

        # 设置内容标签的右键菜单策略为自定义
        self.contentLabel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # 调整文本显示
        self._adjustText()

        # 连接信号和槽
        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)

    def _adjustText(self):
        """ 根据窗口大小调整文本显示格式 """
        if self.isWindow(): # 如果是顶级窗口
            if self.parent():
                # 计算可用宽度为标题标签宽度和父窗口宽度的较大值
                w = max(self.titleLabel.width(), self.parent().width())
                # 根据宽度计算每行显示的字符数，限制在30-140之间
                chars = max(min(w / 9, 140), 30)
            else:
                chars = 100 # 没有父窗口时默认显示100个字符
        else:
            # 不是顶级窗口时，使用窗口宽度
            w = max(self.titleLabel.width(), self.window().width())
            # 根据宽度计算每行显示的字符数，限制在30-100之间
            chars = max(min(w / 9, 100), 30)

        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0]) # 自动换行处理文本

    def __initLayout(self):
        """ 初始化布局 """
        # 设置主垂直布局的间距和边距
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        # 添加文本布局和按钮组到主布局
        self.vBoxLayout.addLayout(self.textLayout, 1)
        self.vBoxLayout.addWidget(self.buttonGroup, 0, Qt.AlignBottom)
        # 设置布局大小约束为最小大小
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

         # 设置文本布局的间距和边距
        self.textLayout.setSpacing(12)
        self.textLayout.setContentsMargins(24, 24, 24, 24)
        # 添加标题标签和内容标签到文本布局
        self.textLayout.addWidget(self.titleLabel, 0, Qt.AlignTop)
        self.textLayout.addWidget(self.contentLabel, 0, Qt.AlignTop)

        
        # 设置按钮布局的间距和边距
        self.buttonLayout.setSpacing(12)
        self.buttonLayout.setContentsMargins(24, 24, 24, 24)
        # 添加确认按钮和取消按钮到按钮布局
        self.buttonLayout.addWidget(self.yesButton, 1, Qt.AlignVCenter)
        self.buttonLayout.addWidget(self.cancelButton, 1, Qt.AlignVCenter)

    def __onCancelButtonClicked(self):
        """ 取消按钮点击事件处理 """
        self.reject()  # 拒绝对话框
        self.cancelSignal.emit()  # 发送取消信号

    def __onYesButtonClicked(self):
        """ 确认按钮点击事件处理 """
        self.accept()  # 接受对话框
        self.yesSignal.emit()  # 发送确认信号

    def __setQss(self):
        """ 设置样式表 """
        # 设置对象名称，用于QSS选择器
        self.titleLabel.setObjectName("titleLabel")
        self.contentLabel.setObjectName("contentLabel")
        self.buttonGroup.setObjectName('buttonGroup')
        self.cancelButton.setObjectName('cancelButton')

        # 应用样式表
        FluentStyleSheet.DIALOG.apply(self)
        FluentStyleSheet.DIALOG.apply(self.contentLabel)

        # 调整按钮大小以适应文本
        self.yesButton.adjustSize()
        self.cancelButton.adjustSize()

    def setContentCopyable(self, isCopyable: bool):
        """ 设置内容是否可复制
        
        参数:
            isCopyable: bool，内容是否可复制
        """
        if isCopyable:
            # 设置内容标签可被鼠标选择
            self.contentLabel.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse)
        else:
            # 设置内容标签不可交互
            self.contentLabel.setTextInteractionFlags(
                Qt.TextInteractionFlag.NoTextInteraction)





    def eventFilter(self, obj, e: QEvent):
        if obj is self.window():  # 当事件发生在对话框窗口时
            if e.type() == QEvent.Resize:
                self._adjustText()  # 调整文本大小以适应窗口变化

        return super().eventFilter(obj, e)  # 调用父类事件过滤器处理其他事件

