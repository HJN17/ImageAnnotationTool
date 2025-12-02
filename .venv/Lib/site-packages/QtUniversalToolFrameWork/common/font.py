# coding: utf-8
from PyQt5.QtGui import QFont 
from PyQt5.QtWidgets import QWidget

def setFont(widget: QWidget, fontSize=14, weight=QFont.Normal):
    widget.setFont(getFont(fontSize, weight))

def getFont(fontSize=14, weight=QFont.Normal,fontType : str = 'Microsoft YaHei'):
    font = QFont()
    font.setFamilies(['Segoe UI', fontType, 'PingFang SC'])
    font.setPixelSize(fontSize)
    font.setWeight(weight)
    return font