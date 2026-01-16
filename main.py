# coding:utf-8
import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from enum import Enum
from QtUniversalToolFrameWork.common.config import qconfig
from view.main_window import mWindow

import os


qconfig.load(qconfig.filePath())

os.environ["QT_LOGGING_RULES"] = "qt.gui.icc=false"

if qconfig.get(qconfig.dpiScale) == "Auto":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
else:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0" 
    os.environ["QT_SCALE_FACTOR"] = str(qconfig.get(qconfig.dpiScale))  # 设置QT缩放因子为配置值（将配置中的数值转为字符串）
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)  # 设置应用程序使用高DPI位图（确保图标等资源在高分辨率下清晰）

app = QApplication(sys.argv)                
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)  # 设置属性：不创建原生窗口部件的兄弟节点（避免某些平台下的渲染问题）

w = mWindow()
w.show()
app.exec_()


