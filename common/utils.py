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

