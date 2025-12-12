# coding: utf-8
from typing import List
from PyQt5.QtCore import QPointF, QSize


class PolygonClipper:

    def clip_polygon_to_image(self, points: List[QPointF], image_size: QSize) -> List[QPointF]:

        
        def _clean_points(points: List[QPointF]) -> List[QPointF]: # 清理多边形中的无效点
            cleaned = []
            eps = 1e-5
            for p in points:
                if not (p.x() == p.x() and p.y() == p.y()):
                    continue
                if not cleaned or (abs(p.x()-cleaned[-1].x()) > eps or abs(p.y()-cleaned[-1].y()) > eps):
                    cleaned.append(p)
            return cleaned


        w, h = image_size.width(), image_size.height()
        clip_functions = [
            lambda p: p.x() >= 0,
            lambda p1, p2: QPointF(0, p1.y() + (p2.y()-p1.y())*(0 - p1.x())/(p2.x()-p1.x())),
            lambda p: p.y() >= 0,
            lambda p1, p2: QPointF(p1.x() + (p2.x()-p1.x())*(0 - p1.y())/(p2.y()-p1.y()), 0),
            lambda p: p.x() <= w,
            lambda p1, p2: QPointF(w, p1.y() + (p2.y()-p1.y())*(w - p1.x())/(p2.x()-p1.x())),
            lambda p: p.y() <= h,
            lambda p1, p2: QPointF(p1.x() + (p2.x()-p1.x())*(h - p1.y())/(p2.y()-p1.y()), h)
        ]

        clipped = points.copy()
        for i in range(0, 8, 2):
            inside_func = clip_functions[i]
            intersect_func = clip_functions[i+1]
            if not clipped:
                break
            new_clipped = []
            n = len(clipped)
            for j in range(n):
                curr = clipped[j]
                prev = clipped[j-1] if j > 0 else clipped[-1]
                
                curr_in = inside_func(curr)
                prev_in = inside_func(prev)

                if curr_in:
                    if not prev_in:
                        try:
                            intersect = intersect_func(prev, curr)
                            new_clipped.append(intersect)
                        except:
                            pass
                    new_clipped.append(curr)
                elif prev_in:
                    try:
                        intersect = intersect_func(prev, curr)
                        new_clipped.append(intersect)
                    except:
                        pass
            clipped = _clean_points(new_clipped)
        return clipped

    
    
polygon_clipper = PolygonClipper()
