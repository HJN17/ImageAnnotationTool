# coding:utf-8
import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from .common.config import qconfig  # 从应用公共配置模块导入cfg（配置管理对象）
from .view.main_window import MainWindow

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

w = MainWindow()
w.show()
app.exec_()

#python -m src.QtUniversalToolFrameWork.__main__
