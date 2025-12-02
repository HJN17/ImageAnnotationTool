# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog


from ..common.config import qconfig,VERSION
from ..common.icon import FluentIcon as FIF
from ..common.style_sheet import FluentStyleSheet,updateStyleSheet

from ..components.settings import SettingCardGroup, OptionsSettingCard,SettingCard,CustomColorSettingCard
from ..components.layout import ExpandLayout
from ..components.widgets import InfoBar, ScrollArea

class SettingInterface(ScrollArea):
    """ 设置界面 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.settingLabel = QLabel("设置", self)

        # self.pathGroup = SettingCardGroup(
        #     "路径", self.scrollWidget)
        # self.downloadFolderCard = PushSettingCard(
        #     '选择文件夹',
        #     FIF.DOWNLOAD,
        #     "下载目录", 
        #     qconfig.get(qconfig.downloadFolder),
        #     self.pathGroup  # 父容器：音乐设置组
        # )

        self.personalGroup = SettingCardGroup(
            "个性化", self.scrollWidget)
        
        self.themeCard = OptionsSettingCard(
            qconfig.themeMode,
            FIF.BRUSH,
            "应用主题",
            "调整你的应用外观",
            texts=["浅色", "深色","跟随系统设置"],
            parent=self.personalGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            qconfig.themeColor,
            FIF.PALETTE,
            "应用主题色",
            "调整你的应用主题色",
            self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            qconfig.dpiScale,
            FIF.ZOOM,
            "界面缩放",
            "调整部件和字体大小",
            texts=["100%", "125%", "150%", "175%", "200%","跟随系统设置"],
            parent=self.personalGroup 
        )


        self.aboutGroup = SettingCardGroup("关于", self.scrollWidget)  
        self.aboutCard = SettingCard(
            FIF.INFO,
            "关于",
            "版本 " + VERSION,
            self.aboutGroup 
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        self.setViewportMargins(0, 80, 0, 20)  # 设置视口边距：上80px，下20px（顶部留空放标题）
        self.setWidget(self.scrollWidget)  # 设置滚动内容部件：将scrollWidget设为滚动区域的内容
        self.setWidgetResizable(True)  # 设置内容自适应大小：允许scrollWidget随内容调整大小
        self.setObjectName('settingInterface')

        # 初始化样式表：应用设置界面专用样式
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        FluentStyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()


    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # 将卡片添加到对应设置组
        #self.pathGroup.addSettingCard(self.downloadFolderCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard) 
        self.personalGroup.addSettingCard(self.zoomCard)

        self.aboutGroup.addSettingCard(self.aboutCard)
       
        self.expandLayout.setSpacing(28) 
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        #self.expandLayout.addWidget(self.pathGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """ 显示配置更新提示：告知用户配置需重启后生效 """
        InfoBar.success(
            '更新成功',
            '配置需重启软件后生效',
            duration=1500,
            parent=self
        )

    
    def __onDownloadFolderCardClicked(self):
        """ 下载文件夹卡片点击事件槽函数：处理文件夹选择逻辑 """
        folder = QFileDialog.getExistingDirectory(
            self, "选择文件夹", qconfig.get(qconfig.downloadFolder) or  "./" )
        if not folder or qconfig.get(qconfig.downloadFolder) == folder:
            return

        qconfig.set(qconfig.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)  # 更新卡片内容：显示新路径

    # 连接信号与槽：绑定UI事件到对应处理函数
    def __connectSignalToSlot(self):
        """ 连接信号与槽函数：建立UI交互与业务逻辑的关联 """
        qconfig.appRestartSig.connect(self.__showRestartTooltip)  # 配置重启信号连接提示函数

        # self.downloadFolderCard.clicked.connect(  
        #     self.__onDownloadFolderCardClicked)

        # 个性化设置组信号
        qconfig.themeChanged.connect(updateStyleSheet)  # 主题变更信号连接系统主题设置函数
        qconfig.themeColorChanged.connect(updateStyleSheet)

