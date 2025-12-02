# coding:utf-8
from typing import Union

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QPainter
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QToolButton,
                             QVBoxLayout, QPushButton)


from ...common.style_sheet import FluentStyleSheet
from ...common.config import qconfig, isDarkTheme, ConfigItem, OptionsConfigItem
from ...common.icon import FluentIconBase, drawIcon


from ..dialog_box.color_dialog import ColorDialog
from ..widgets.switch_button import SwitchButton, IndicatorPosition
from ..widgets.slider import Slider
from ..widgets.icon_widget import IconWidget
from ..widgets.button import HyperlinkButton



class SettingIconWidget(IconWidget):
    """ 设置项图标部件，继承自自定义图标部件IconWidget，用于在设置卡片中显示图标 """

    def paintEvent(self, e):
        """ 重写绘制事件，自定义图标绘制逻辑
        :param e: 绘制事件对象，包含事件相关信息
        """
        painter = QPainter(self)  # 创建QPainter对象，用于在当前部件(self)上绘制

        if not self.isEnabled():  # 判断部件是否禁用
            painter.setOpacity(0.36)  # 禁用时设置透明度为0.36（半透明效果）

        # 设置绘制提示：启用抗锯齿和平滑 pixmap 变换，提升绘制质量
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        drawIcon(self._icon, painter, self.rect())  # 调用自定义drawIcon函数绘制图标，参数为图标对象、画家对象、绘制区域（当前部件矩形区域）



class SettingCard(QFrame):
    """ 基础设置卡片部件，继承自QFrame，用于展示设置项的标题、内容和图标 """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """ 初始化设置卡片
        :param icon: 图标，可以是字符串（路径）、QIcon对象或FluentIconBase子类实例
        :param title: 卡片标题文本
        :param content: 卡片内容文本（可选，默认为None）
        :param parent: 父部件（可选，默认为None）
        """
        super().__init__(parent=parent)  # 调用父类QFrame的初始化方法
        self.iconLabel = SettingIconWidget(icon, self)  # 创建图标标签部件，使用自定义的SettingIconWidget
        self.titleLabel = QLabel(title, self)  # 创建标题标签，显示标题文本
        self.contentLabel = QLabel(content or '', self)  # 创建内容标签，显示内容文本（无内容时为空字符串）
        self.hBoxLayout = QHBoxLayout(self)  # 创建水平布局管理器，用于管理卡片内水平方向的部件排列
        self.vBoxLayout = QVBoxLayout()  # 创建垂直布局管理器，用于管理标题和内容标签的垂直排列

        if not content:  # 如果内容为空
            self.contentLabel.hide()  # 隐藏内容标签

        # 设置卡片固定高度：有内容时70px，无内容时50px
        self.setFixedHeight(70 if content else 50)
        self.iconLabel.setFixedSize(16, 16)  # 设置图标标签固定大小为16x16像素

        # 初始化水平布局
        self.hBoxLayout.setSpacing(0)  # 设置布局内部件间距为0px
        self.hBoxLayout.setContentsMargins(16, 0, 0, 0)  # 设置布局外边距：左16px，上、右、下0px
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)  # 设置布局内部件垂直居中对齐
        # 初始化垂直布局
        self.vBoxLayout.setSpacing(0)  # 设置布局内部件间距为0px
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)  # 设置布局外边距为0px
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)  # 设置布局内部件垂直居中对齐

        # 将图标标签添加到水平布局，对齐方式为左对齐
        self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)  # 在图标标签后添加16px间距

        self.hBoxLayout.addLayout(self.vBoxLayout)  # 将垂直布局添加到水平布局
        # 将标题标签添加到垂直布局，对齐方式为左对齐
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        # 将内容标签添加到垂直布局，对齐方式为左对齐
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignLeft)

        self.hBoxLayout.addSpacing(16)  # 在垂直布局后添加16px间距
        self.hBoxLayout.addStretch(1)  # 添加伸缩项，将右侧部件推到最右

        self.contentLabel.setObjectName('contentLabel')  # 设置内容标签的对象名称（用于样式表选择）
        FluentStyleSheet.SETTING_CARD.apply(self)  # 应用设置卡片的Fluent样式表

    def setTitle(self, title: str):
        """ 设置卡片标题文本
        :param title: 新的标题文本
        """
        self.titleLabel.setText(title)  # 设置标题标签的文本内容

    def setContent(self, content: str):
        """ 设置卡片内容文本
        :param content: 新的内容文本（为空时隐藏内容标签）
        """
        self.contentLabel.setText(content)  # 设置内容标签的文本内容
        self.contentLabel.setVisible(bool(content))  # 根据内容是否为空设置内容标签可见性

    def setValue(self, value):
        """ 设置配置项的值（基础卡片无实际功能，子类可重写）
        :param value: 配置项的值
        """
        pass  # 空实现，供子类重写

    def setIconSize(self, width: int, height: int):
        """ 设置图标标签的固定大小
        :param width: 图标宽度
        :param height: 图标高度
        """
        self.iconLabel.setFixedSize(width, height)  # 设置图标标签的固定宽高

    def paintEvent(self, e):
        """ 重写绘制事件，自定义卡片背景绘制
        :param e: 绘制事件对象
        """
        painter = QPainter(self)  # 创建QPainter对象，用于绘制卡片背景
        painter.setRenderHints(QPainter.Antialiasing)  # 启用抗锯齿，使圆角更平滑

        if isDarkTheme():  # 判断当前是否为深色主题（通过isDarkTheme函数获取）
            painter.setBrush(QColor(255, 255, 255, 13))  # 深色主题：背景色为白色（透明度13/255）
            painter.setPen(QColor(0, 0, 0, 50))  # 深色主题：边框色为黑色（透明度50/255）
        else:  # 浅色主题
            painter.setBrush(QColor(255, 255, 255, 170))  # 浅色主题：背景色为白色（透明度170/255）
            painter.setPen(QColor(0, 0, 0, 19))  # 浅色主题：边框色为黑色（透明度19/255）

        # 绘制带圆角的矩形作为背景：调整矩形区域（向内缩1px），圆角半径6px
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class SwitchSettingCard(SettingCard):
    """ 带开关按钮的设置卡片，继承自SettingCard，用于通过开关控制配置项 """

    checkedChanged = pyqtSignal(bool)  # 开关状态变化信号，发射新的选中状态（True/False）

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None,
                 configItem: ConfigItem = None, parent=None):
        """ 初始化带开关的设置卡片
        :param icon: 图标（字符串路径/QIcon/FluentIconBase）
        :param title: 卡片标题
        :param content: 卡片内容（可选）
        :param configItem: 关联的配置项对象（ConfigItem类型，用于读写配置值）
        :param parent: 父部件（可选）
        """
        super().__init__(icon, title, content, parent)  # 调用父类SettingCard的初始化方法
        self.configItem = configItem  # 保存关联的配置项
        # 创建开关按钮：显示文本"Off"，父部件为当前卡片，指示器位置在右侧
        self.switchButton = SwitchButton('关', self, IndicatorPosition.RIGHT)

        if configItem:  # 如果关联了配置项
            self.setValue(qconfig.get(configItem))  # 从配置中获取初始值并设置
            configItem.valueChanged.connect(self.setValue)  # 配置项值变化时，同步更新开关状态

        # 将开关按钮添加到水平布局，对齐方式为右对齐
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)  # 在开关按钮后添加16px间距

        # 连接开关按钮的状态变化信号到内部处理函数
        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def __onCheckedChanged(self, isChecked: bool):
        """ 开关按钮状态变化的槽函数
        :param isChecked: 开关新的选中状态（True为开，False为关）
        """
        self.setValue(isChecked)  # 更新配置项值
        self.checkedChanged.emit(isChecked)  # 发射开关状态变化信号

    def setValue(self, isChecked: bool):
        """ 设置开关状态和配置项值
        :param isChecked: 开关选中状态（True为开，False为关）
        """
        if self.configItem:  # 如果关联了配置项
            qconfig.set(self.configItem, isChecked)  # 将配置项值设为isChecked

        self.switchButton.setChecked(isChecked)  # 设置开关按钮的选中状态
        # 根据选中状态更新开关按钮文本（"On"或"Off"，支持翻译）
        self.switchButton.setText('关' if isChecked else '开')

    def setChecked(self, isChecked: bool):
        """ 设置开关选中状态（封装方法，便于外部调用）
        :param isChecked: 选中状态（True为开，False为关）
        """
        self.setValue(isChecked)  # 调用setValue方法设置状态

    def isChecked(self):
        """ 获取开关当前选中状态
        :return: 开关选中状态（True为开，False为关）
        """
        return self.switchButton.isChecked()  # 返回开关按钮的选中状态


class RangeSettingCard(SettingCard):
    """ 带滑块的设置卡片，继承自SettingCard，用于通过滑块调整数值型配置项 """

    valueChanged = pyqtSignal(int)  # 滑块值变化信号，发射新的数值

    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """ 初始化带滑块的设置卡片
        :param configItem: 关联的范围配置项（需支持range属性和value属性）
        :param icon: 图标（字符串路径/QIcon/FluentIconBase）
        :param title: 卡片标题
        :param content: 卡片内容（可选）
        :param parent: 父部件（可选）
        """
        super().__init__(icon, title, content, parent)  # 调用父类SettingCard的初始化方法
        self.configItem = configItem  # 保存关联的配置项
        self.slider = Slider(Qt.Horizontal, self)  # 创建水平滑块部件
        self.valueLabel = QLabel(self)  # 创建显示当前值的标签
        self.slider.setMinimumWidth(268)  # 设置滑块最小宽度为268px

        self.slider.setSingleStep(1)  # 设置滑块单步值为1
        self.slider.setRange(*configItem.range)  # 设置滑块范围（从配置项的range属性获取，如(100, 200)）
        self.slider.setValue(configItem.value)  # 设置滑块初始值（从配置项的value属性获取）
        self.valueLabel.setNum(configItem.value)  # 设置值标签显示初始值

        self.hBoxLayout.addStretch(1)  # 添加伸缩项，将滑块和值标签推到右侧
        # 将值标签添加到水平布局，对齐方式为右对齐
        self.hBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(6)  # 在值标签和滑块间添加6px间距
        # 将滑块添加到水平布局，对齐方式为右对齐
        self.hBoxLayout.addWidget(self.slider, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)  # 在滑块后添加16px间距

        self.valueLabel.setObjectName('valueLabel')  # 设置值标签的对象名称（用于样式表）
        configItem.valueChanged.connect(self.setValue)  # 配置项值变化时，同步更新滑块
        # 滑块值变化时，同步更新配置项和值标签
        self.slider.valueChanged.connect(self.__onValueChanged)

    def __onValueChanged(self, value: int):
        """ 滑块值变化的槽函数
        :param value: 滑块新的数值
        """
        self.setValue(value)  # 更新配置项值
        self.valueChanged.emit(value)  # 发射值变化信号

    def setValue(self, value):
        """ 设置滑块值和配置项值
        :param value: 新的数值
        """
        qconfig.set(self.configItem, value)  # 将配置项值设为value
        self.valueLabel.setNum(value)  # 更新值标签显示的数值
        self.valueLabel.adjustSize()  # 调整值标签大小以适应文本
        self.slider.setValue(value)  # 设置滑块位置为value


class PushSettingCard(SettingCard):
    """ 带按钮的设置卡片，继承自SettingCard，用于触发操作（如打开对话框） """

    clicked = pyqtSignal()  # 按钮点击信号

    def __init__(self, text, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """ 初始化带按钮的设置卡片
        :param text: 按钮显示文本
        :param icon: 卡片图标
        :param title: 卡片标题
        :param content: 卡片内容（可选）
        :param parent: 父部件（可选）
        """
        super().__init__(icon, title, content, parent)  # 调用父类初始化方法
        self.button = QPushButton(text, self)  # 创建按钮部件，显示文本为text
        # 将按钮添加到水平布局，对齐方式为右对齐
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)  # 按钮后添加16px间距
        self.button.clicked.connect(self.clicked)  # 按钮点击信号连接到卡片的clicked信号




