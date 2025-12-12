import random
from PyQt5.QtGui import QColor, QGuiApplication
from PyQt5.QtCore import QPointF
import math
class Utils:

    @staticmethod
    def point_to_line_distance(point: QPointF, line_p1: QPointF, line_p2: QPointF) -> float:
        """计算点到线段的垂直距离"""
        x0, y0 = point.x(), point.y()
        x1, y1 = line_p1.x(), line_p1.y()
        x2, y2 = line_p2.x(), line_p2.y()
        
        # 计算向量
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(x0 - x1, y0 - y1)
        
        # 计算垂足参数
        t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        
        # 计算垂足点
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        # 计算距离
        return math.hypot(x0 - proj_x, y0 - proj_y)


    @staticmethod
    def get_closest_point_on_line_segment(point: QPointF, line_p1: QPointF, line_p2: QPointF) -> QPointF:
        """获取点到线段的最近点（垂足）"""
        x0, y0 = point.x(), point.y()
        x1, y1 = line_p1.x(), line_p1.y()
        x2, y2 = line_p2.x(), line_p2.y()
        
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return QPointF(x1, y1)
        
        t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        
        return QPointF(x1 + t * dx, y1 + t * dy)
    

    @staticmethod
    def line_intersection(p1: QPointF, p2: QPointF, p3: QPointF, p4: QPointF) -> QPointF:
        """
        计算两条线段的交点
        :param p1, p2: 第一条线段的两个端点
        :param p3, p4: 第二条线段的两个端点
        :return: 交点（QPointF），无交点返回None
        """
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        x3, y3 = p3.x(), p3.y()
        x4, y4 = p4.x(), p4.y()
        
        # 计算分母
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return None
        
        # 计算参数t和u
        t_numer = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
        u_numer = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3))
        
        t = t_numer / denom
        u = u_numer / denom
        
        # 检查交点是否在线段上
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return QPointF(x, y)
        
        return None

    




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
    def generate_random_color()->QColor:
        """生成随机颜色，确保中等亮度和饱和度（不深不浅）"""
        hue = random.randint(0, 359)  # 随机色相（0-359，覆盖所有颜色）
        saturation = random.randint(120, 180) # 中等饱和度（120-180）- 避免颜色过于灰暗或过于鲜艳
        lightness = random.randint(140, 180) # 中等亮度（140-180）- 避免过深（<100）或过浅（>200)
        return QColor.fromHsl(hue, saturation, lightness) # 中等亮度和饱和度

