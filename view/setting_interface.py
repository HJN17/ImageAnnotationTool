# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog

from QtUniversalToolFrameWork.common.config import qconfig
from QtUniversalToolFrameWork.view.setting_interface import SettingInterface, SettingCardGroup


from components.label_list_setting_card import LabelListSettingCard
from common.case_label import cl    


class SetInterface(SettingInterface):
        """ 设置界面 """
        

        def post_init(self):
            self.labelGroup = SettingCardGroup("标签", self.scrollWidget)
            
            self.labelCard = LabelListSettingCard(
                qconfig.labelMode,
                "标签列表",
                parent=self.labelGroup
            )
            

        def _initLayout(self):
            
            self.post_init()


            self.settingLabel.move(36, 30)

            # 将卡片添加到对应设置组
            self.labelGroup.addSettingCard(self.labelCard)
            self.personalGroup.addSettingCard(self.themeCard)
            self.personalGroup.addSettingCard(self.themeColorCard) 
            self.personalGroup.addSettingCard(self.zoomCard)

            self.aboutGroup.addSettingCard(self.aboutCard)
        
            self.expandLayout.setSpacing(28) 
            self.expandLayout.setContentsMargins(36, 10, 36, 0)
            #self.expandLayout.addWidget(self.pathGroup)
            self.expandLayout.addWidget(self.labelGroup)
            self.expandLayout.addWidget(self.personalGroup)
            self.expandLayout.addWidget(self.aboutGroup)        

        
        def _connectSignalToSlot(self):
            """ 连接信号与槽函数：建立UI交互与业务逻辑的关联 """
            super()._connectSignalToSlot()
            

    

