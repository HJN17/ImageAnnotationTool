from PyQt5.QtCore import QRect
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication 


def getCurrentScreen():
    """获取当前光标所在的屏幕对象"""
    cursorPos = QCursor.pos() 
    
   
    for s in QApplication.screens():
    
        if s.geometry().contains(cursorPos):
            return s 

    return None 

def getCurrentScreenGeometry(avaliable=True):
    """ 获取当前屏幕的几何区域（支持获取可用区域或完整区域）"""
    screen = getCurrentScreen() or QApplication.primaryScreen()

    if not screen:
        return QRect(0, 0, 1920, 1080)

    return screen.availableGeometry() if avaliable else screen.geometry()