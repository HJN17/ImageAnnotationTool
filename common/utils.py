import random
from PyQt5.QtGui import QColor, QGuiApplication
        
class Utils:

    @staticmethod
    def count_non_empty_values(dic):
        # 同样排除常见空值，返回符合条件的数量
        return sum(1 for value in dic.values() if value not in (None, "", [], {}, ()))


    @staticmethod
    def get_empty_value_keys(dic):
        """
        返回字典中值为空的所有键（key）
        
        :param dic: 要检查的字典
        :return: 空值对应的键组成的列表
        """
        
        for key, value in dic.items():
            # 定义空值：None、空字符串、空列表、空字典、空元组
            if value in (None, "", [], {}, ()):
                return key
        return None
    
    @staticmethod
    def generate_random_color():
        """生成随机颜色，确保中等亮度和饱和度（不深不浅）"""
        hue = random.randint(0, 359)  # 随机色相（0-359，覆盖所有颜色）
        saturation = random.randint(120, 180) # 中等饱和度（120-180）- 避免颜色过于灰暗或过于鲜艳
        lightness = random.randint(140, 180) # 中等亮度（140-180）- 避免过深（<100）或过浅（>200)
        return QColor.fromHsl(hue, saturation, lightness)
    
    @staticmethod
    def pt_to_px(pt_value):
        """
        将pt单位转换为当前屏幕的px单位
        :param pt_value: 目标pt值（如30）
        :return: 对应的px值（整数，便于图像缩放）
        """
        # 获取当前屏幕的DPI（若多屏幕，取主窗口所在屏幕的DPI）
        # QGuiApplication.primaryScreen() 获取主屏幕，也可根据主窗口位置获取对应屏幕
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return int(pt_value)  # 异常情况默认返回原pt值（降级处理）
        
        # 获取屏幕的水平DPI（通常与垂直DPI一致，取一个即可）
        dpi = screen.logicalDotsPerInch()  # logicalDotsPerInch() 对应系统设置的DPI
        
        # 计算px值并转为整数（图像像素需整数）
        px_value = pt_value * (dpi / 72.0)
        return int(px_value)
    
