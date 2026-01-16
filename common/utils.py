import random
from typing import List, Optional
from PyQt5.QtGui import QColor, QGuiApplication
from PyQt5.QtCore import QPointF
import math
class Utils:

    @staticmethod
    def get_rectangle_points(points: list[QPointF]): # 计算矩形的四个顶点

        if len(points) != 2:
            print("矩形顶点数量不等于2")
            return []
        

        p1 = points[0]
        p2 = points[1]
    
        x1 = p1.x()
        y1 = p1.y()
        x2 = p2.x()
        y2 = p2.y()

        point_1 = QPointF(min(x1, x2), min(y1, y2))  # 左下角
        point_2 = QPointF(min(x1, x2), max(y1, y2))  # 左上角
        point_3 = QPointF(max(x1, x2), max(y1, y2))  # 右上角
        point_4 = QPointF(max(x1, x2), min(y1, y2))  # 右下角
        return [point_1, point_2, point_3, point_4]

    @staticmethod
    def get_rectangle_vertices(points: list[QPointF]): # 得到矩形的两个对角点
        if len(points) != 4:
            print("矩形顶点数量不等于4")
            return []
        
        min_x = min(point.x() for point in points)
        max_x = max(point.x() for point in points)
        min_y = min(point.y() for point in points)
        max_y = max(point.y() for point in points)
        return [QPointF(min_x, min_y), QPointF(max_x, max_y)]
        

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
    def get_intersection_point(points: list[QPointF], start_point: QPointF, end_point: QPointF) -> tuple[int, Optional[QPointF]]:
        """
        查找线段与指定图形边的交点（排除起点）
        
        Args:
            item_idx: 数据项索引
            start_point: 线段起点
            end_point: 线段终点
            
        Returns:
            元组(最近边索引+1, 交点坐标)，无有效交点返回(-1, None)
        """

       
        num_points = len(points)

        if num_points < 2:
            return (-1, None)

        def is_start_point(point: QPointF, threshold: float = 1e-6) -> bool:
            """判断点是否为起点（增加浮点精度阈值）"""
            dx = abs(point.x() - start_point.x())
            dy = abs(point.y() - start_point.y())
            return dx < threshold and dy < threshold

        best_edge_idx = -1
        intersection_point = None
        
        for j in range(num_points):
            p1 = points[j]
            p2 = points[(j + 1) % num_points]

            current_intersection = Utils.line_intersection(p1, p2, start_point, end_point)
            
            if current_intersection is not None and not is_start_point(current_intersection):
                best_edge_idx = j
                intersection_point = current_intersection
                break 

        return (best_edge_idx + 1) if best_edge_idx != -1 else -1, intersection_point

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
    def get_closest_point_index_and_edge(points: List[QPointF],point: QPointF) -> tuple[int,QPointF]:
        """ 查找点到指定图形边的最近距离点"""
       
        num_points = len(points)

        if num_points < 2:
            return points[0] if num_points == 1 else point  # 无点返回原坐标，单点返回自身


        min_dist = float("inf")
        best_edge_idx = 0 

        for j in range(num_points):
            p1 = points[j]
            p2 = points[(j + 1) % num_points]

            dist = Utils.point_to_line_distance(point, p1, p2)
            
            if dist < min_dist:
                min_dist = dist
                best_edge_idx = j  # 关键修正：直接记录边的起始索引j

        edge_p1 = points[best_edge_idx]
        edge_p2 = points[(best_edge_idx + 1) % num_points]

        
        closest_point = Utils.get_closest_point_on_line_segment(point, edge_p1, edge_p2)
        return best_edge_idx + 1,closest_point



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

    
    def compare_points_on_line(p: QPointF,q: QPointF,line_p1: QPointF, line_p2: QPointF,eps: float = 1e-8 ) -> int:
       
        dir_x = line_p2.x() - line_p1.x()
        dir_y = line_p2.y() - line_p1.y()
    
        if abs(dir_x) < eps and abs(dir_y) < eps:
            raise ValueError("基准点line_p1和line_p2不能重合！")
        
        dir_len = math.hypot(dir_x, dir_y)
        unit_dir_x = dir_x / dir_len
        unit_dir_y = dir_y / dir_len
        
        vec_p_x = p.x() - line_p1.x()
        vec_p_y = p.y() - line_p1.y()
        proj_p = vec_p_x * unit_dir_x + vec_p_y * unit_dir_y
        
        vec_q_x = q.x() - line_p1.x()
        vec_q_y = q.y() - line_p1.y()
        proj_q = vec_q_x * unit_dir_x + vec_q_y * unit_dir_y
        
        if abs(proj_p - proj_q) < eps:
            return 0  # 两点重合
        return -1 if proj_p < proj_q else 1


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

