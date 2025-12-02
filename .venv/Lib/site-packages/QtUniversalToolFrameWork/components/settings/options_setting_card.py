# coding:utf-8

from typing import Union
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QButtonGroup, QLabel

from ...common.config import OptionsConfigItem, qconfig
from ...common.icon import FluentIconBase

from ..widgets.button import RadioButton
from .expand_setting_card import ExpandSettingCard



class OptionsSettingCard(ExpandSettingCard):

    optionChanged = pyqtSignal(OptionsConfigItem)
    
    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, texts=None, parent=None):
        
        super().__init__(icon, title, content, parent)
    
        self.texts = texts or []
      
        self.configItem = configItem
      
        self.configName = configItem.name
      
        self.choiceLabel = QLabel(self)
       
        self.buttonGroup = QButtonGroup(self)
       
        self.choiceLabel.setObjectName("titleLabel")
    
        self.addWidget(self.choiceLabel)

        self.viewLayout.setSpacing(19) 
        self.viewLayout.setContentsMargins(48, 18, 0, 18)
        
        for text, option in zip(texts, configItem.options):
            button = RadioButton(text, self.view)
            self.buttonGroup.addButton(button)
            self.viewLayout.addWidget(button)
            button.setProperty(self.configName, option)

        self._adjustViewSize()
        self.setValue(qconfig.get(self.configItem)) 
        configItem.valueChanged.connect(self.setValue)
        self.buttonGroup.buttonClicked.connect(self.__onButtonClicked)

    def __onButtonClicked(self, button: RadioButton):
        """ 单选按钮点击事件的槽函数，用于处理选项变更逻辑 """
        
        if button.text() == self.choiceLabel.text():
            return

        value = button.property(self.configName)

        qconfig.set(self.configItem, value)

        self.choiceLabel.setText(button.text())
       
        self.choiceLabel.adjustSize()
        
        self.optionChanged.emit(self.configItem)

  
    def setValue(self, value):
        """ 根据配置值选择对应的单选按钮，并更新当前选择标签显示 """
     
        #qconfig.set(self.configItem, value)

        for button in self.buttonGroup.buttons():
            isChecked = button.property(self.configName) == value
            button.setChecked(isChecked)

            if isChecked:
                self.choiceLabel.setText(button.text())
                self.choiceLabel.adjustSize()