# coding:utf-8
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

from ...common.style_sheet import FluentStyleSheet
from ...common.font import setFont

from ..layout.expand_layout import ExpandLayout


# 定义设置卡片组类：继承自QWidget，用于将多个设置卡片组织成一个逻辑组，提供统一的标题和布局管理
class SettingCardGroup(QWidget):
    """ 
    设置卡片组类，用于对功能相关的设置卡片进行分组管理。
    
    功能特点：
    - 包含一个标题标签，用于标识组的功能类别（如"个性化"、"系统设置"）
    - 使用垂直布局（QVBoxLayout）组织标题和卡片区域，使用扩展布局（ExpandLayout）排列卡片
    - 支持添加单个或多个设置卡片，并自动调整组的高度以适应内容
    - 应用预定义样式表，确保与应用整体风格统一
    
    典型应用场景：在设置界面中，将同类设置项（如主题设置、更新设置）的卡片归类到同一组，提升界面可读性。
    """

    # 构造方法：初始化设置卡片组的UI元素、布局和样式
    def __init__(self, title: str, parent=None):
        # 调用父类构造方法：初始化QWidget基类，指定父窗口（可选，用于控件层级管理）
        super().__init__(parent=parent)
        # 创建标题标签：用于显示组标题文本（如"音乐在这台电脑上"）
        self.titleLabel = QLabel(title, self)
        # 创建主垂直布局：作为卡片组的根布局，用于排列标题和卡片区域
        self.vBoxLayout = QVBoxLayout(self)
        # 创建卡片扩展布局：用于管理设置卡片的排列，继承自ExpandLayout，支持垂直动态扩展
        self.cardLayout = ExpandLayout()

        # 配置主布局内边距：设置为(0,0,0,0)，移除默认内边距以实现紧凑布局
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        # 配置主布局对齐方式：设置为顶部对齐（Qt.AlignTop），确保内容从顶部开始排列
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        # 配置主布局组件间距：设置为0，标题与卡片区域之间的间距通过addSpacing单独控制
        self.vBoxLayout.setSpacing(0)
        # 配置卡片布局内边距：设置为(0,0,0,0)，确保卡片与组边缘无额外间距
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        # 配置卡片布局组件间距：设置为2px，控制相邻卡片之间的垂直间距
        self.cardLayout.setSpacing(2)

        # 向主布局添加标题标签：作为布局的第一个元素（顶部）
        self.vBoxLayout.addWidget(self.titleLabel)
        # 向主布局添加固定间距：在标题下方添加12px间距，分隔标题与卡片区域
        self.vBoxLayout.addSpacing(12)
        # 向主布局添加卡片布局：将卡片布局添加到主布局，并设置拉伸因子为1（使其占满剩余空间）
        self.vBoxLayout.addLayout(self.cardLayout, 1)

        # 应用样式表：为卡片组应用预定义的"SETTING_CARD_GROUP"样式（定义于FluentStyleSheet）
        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        # 设置标题标签字体：调用setFont工具函数，将标题字体大小设置为20px
        setFont(self.titleLabel, 20)
        # 调整标题标签大小：根据文本内容自动调整标签尺寸（避免文本截断）
        self.titleLabel.adjustSize()

    # 添加单个设置卡片到组：将设置卡片添加到卡片布局，并调整组尺寸
    def addSettingCard(self, card: QWidget):
        """ 
        向设置卡片组添加单个设置卡片
        
        参数:
            card (QWidget): 要添加的设置卡片控件（如SwitchSettingCard、OptionsSettingCard等）
        """
        # 设置卡片父控件：将卡片的父控件设为当前卡片组，确保控件树层级正确（影响样式和事件传递）
        card.setParent(self)
        # 添加卡片到卡片布局：通过cardLayout（ExpandLayout）管理卡片的位置和大小
        self.cardLayout.addWidget(card)
        # 调整组尺寸：根据新增卡片更新卡片组的整体大小
        self.adjustSize()

    # 添加多个设置卡片到组：批量添加卡片，内部调用addSettingCard逐个处理
    def addSettingCards(self, cards: List[QWidget]):
        """ 
        向设置卡片组批量添加多个设置卡片
        
        参数:
            cards (List[QWidget]): 要添加的设置卡片控件列表（元素类型同addSettingCard的card参数）
        """
        # 遍历卡片列表：逐个调用addSettingCard添加卡片
        for card in cards:
            self.addSettingCard(card)

    # 调整卡片组尺寸：根据卡片布局高度和标题区域计算总高度，并调整自身大小
    def adjustSize(self):
        # 计算总高度：卡片布局高度（通过heightForWidth获取） + 标题区域高度（固定46px，含标题高度和间距）
        h = self.cardLayout.heightForWidth(self.width()) + 46
        # 调整自身大小：保持宽度不变，高度设为计算值h
        return self.resize(self.width(), h)
