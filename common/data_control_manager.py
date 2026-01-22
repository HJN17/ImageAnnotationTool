# coding: utf-8

from copy import deepcopy
import uuid
from PyQt5.QtCore import pyqtSignal, QObject,QPointF,Qt,QSize
from PyQt5.QtGui import QPainter,QColor,QBrush
from QtUniversalToolFrameWork.common.style_sheet import themeColor


from common.data_structure import DataItemInfo
from common.signal_bus import signalBus
from common.case_label import cl
from common.polygon_clip import polygon_clipper
from common.key_manager import keyManager

from common.annotation import AnnotationFrameBase,AnnotationType
from common.utils import Utils
from common.message import message



class DataManager(QObject):
    
    update_data_item = pyqtSignal() # 更新DataItem信号

    _INSTANCE = None 
    _INSTANCE_INIT = False 

    def __new__(cls, *args, **kwargs):
        if not cls._INSTANCE:
            cls._INSTANCE = super().__new__(cls)
        return cls._INSTANCE

    def __init__(self):
        if self._INSTANCE_INIT:
            return
        self._INSTANCE_INIT = True

        super().__init__()
        self.data_info = None
        self.shift_pressed = False

        self.scale = 1.0    

        signalBus.selectItem.connect(self._on_select_item) # 选择DataItem信号
        signalBus.labelComboBoxChanged.connect(self._on_item_label_changed) # 标签ComboBox改变信号
        signalBus.deleteItem.connect(self.delete_item_by_key) # 删除DataItem信号

        self.init_vars()

    def init_vars(self):
        
        self.data_items = []

        self._current_item_index = -1  # 当前选中的DataItem索引
        
        self.current_point_index = -1  # 当前选中的点索引
        self.split_item_index = -1 # 分割项索引

        self.split_point_index_start = -1 # 分割点索引开始
        self.split_point_index_end = -1 # 分割点索引结束

        self.creating_data_item = False  # 是否正在创建DataItem
        self.creating_split_vertex = False # 是否正在创建分割点

        self.annotion_frame = None # 当前正在编辑的AnnotationFrame

        self.update_data_item.emit()


    def init_data_items(self):
        self.data_items = self.data_info.items
        self.current_item_index = -1

        self.update_data_item.emit()

    @property
    def current_item_index(self) -> int:
        return self._current_item_index
    
    @current_item_index.setter
    def current_item_index(self, index: int):

        if index < 0 or index >= len(self.data_items):
            return
        
        if self.current_item_index == index:
            return
        
        self._current_item_index = index
        signalBus.selectItem.emit(self.data_items[index].id)
    
    @property
    def current_data_item(self) -> DataItemInfo:
        if not self.is_current_item_valid():
            return None
        
        return self.data_items[self.current_item_index]


    def _on_select_item(self, routeKey: str):

        if not self.data_items:
            return
        
        for i, item in enumerate(self.data_items):
            if item.id == routeKey:
                index = i
                break
        else:
            return
        
        if index == self.current_item_index:
            return
        
        self.current_item_index = index

        self.update_data_item.emit()

    def _on_item_label_changed(self, routeKey: str, caseLabel: str):

        if not self.is_current_item_valid():
            return
        
        if self.current_data_item.id != routeKey:
            return
        
        self.current_data_item.caseLabel = caseLabel

        self.update_data_item.emit()


    def get_item_points(self, index: int) -> list[QPointF]:
        if index < 0 or index >= len(self.data_items):
            return []
        
        return self.data_items[index].points

    def get_item_by_key(self, routeKey: str) -> DataItemInfo:
        if not self.data_items:
            return None
        
        for item in self.data_items:
            if item.id == routeKey:
                return item
        return None

    def get_current_item_label(self):    
        if not self.is_current_item_valid():
            return None
        
        return self.data_items[self.current_item_index].caseLabel
        

    def is_current_item_valid(self):
        return self.data_items and self.current_item_index >= 0 and self.current_item_index < len(self.data_items)


    def delete_item_by_key(self, routeKey: str):

        if not self.data_items:
            return
        
        item = self.get_item_by_key(routeKey)

        if not item:
            return
        
        self.data_items.remove(item)

        self.current_item_index = -1
        self.current_point_index = -1

        message.show_info_message("提示", "删除了标注框！")

        self.update_data_item.emit()

    
    
    def delete_item(self, index: int):
        if index < 0 or index >= len(self.data_items):
            return
    
        routeKey = self.data_items[index].id        
        signalBus.deleteItem.emit(routeKey)

    def add_item(self, data_item: DataItemInfo):

        self.data_items.append(data_item)
        signalBus.addItem.emit(data_item.id, data_item.caseLabel, data_item.annotation_type)
        self.current_item_index = len(self.data_items) - 1
        self.current_point_index = -1
        self.update_data_item.emit()
        message.show_success_message("提示", "添加标注框成功！")

    def delete_current_point(self):

        if not self.is_current_item_valid():
            return 
        
        if self.current_point_index < 0 or self.current_point_index >= len(item.points):
            return 
        
        item = self.current_data_item

        if not item.annotation.verify_points(len(item.points)-1):
            message.show_error_message("错误", "删除点失败，点数量不符合要求！")
            return 
        
        item.remove_point(self.current_point_index)
        self.current_point_index = -1
        self.update_data_item.emit()
    

    def draw(self, painter: QPainter, offset: QPointF,func: callable = None):

        for i, item in enumerate(self.data_items): 
            
            if not cl.is_show(item.caseLabel):
                continue

            selected = False

            if i == self.current_item_index and not self.creating_data_item and not self.creating_split_vertex:
                selected=True

            item.annotation.draw(painter, self.scale, offset,cl.get_color(item.caseLabel),func,selected,item.points)

    def temp_frame_draw(self, painter: QPainter, offset: QPointF,func: callable = None):

        if self.creating_data_item:
            self.annotion_frame.draw(painter, self.scale, offset, themeColor(), func,True)
            return
        
        if self.creating_split_vertex:
            label = self.get_current_item_label()
            self.annotion_frame.draw(painter, self.scale, offset, cl.get_color(label), func,True)
            return

    def check_edge_click(self,clamped_point:QPointF) -> tuple[bool,int,int]:
        """检查是否点击了多边形边"""
        for i, item in enumerate(self.data_items):

            if not cl.is_show(item.caseLabel):
                continue

            best_edge_idx = item.annotation.check_edge_click(item.points,clamped_point,self.scale)
            if best_edge_idx != -1:
                return True,i,best_edge_idx

        return False,-1,-1
    
    def check_vertex_click(self,clamped_point:QPointF) -> tuple[bool,int,int]:
        """检查是否点击了多边形顶点"""
        threshold = max(6, 6/self.scale)

        for i, item in enumerate(self.data_items):

            if not cl.is_show(item.caseLabel):
                continue

            for j, point in enumerate(item.points):

                dist = ((point.x() - clamped_point.x())**2 + (point.y() - clamped_point.y())**2)**0.5 # 计算距离
                if dist < threshold:
                    return True,i, j
        
        return False,-1,-1


    def check_frame_click(self, clamped_point:QPointF) -> tuple[bool,int]:
        """检查是否点击了多边形"""

        # 从后往前检查，确保后绘制的多边形优先被选中
        for i, item in enumerate(self.data_items):
            
            if not cl.is_show(item.caseLabel):
                continue
            
            is_click = item.annotation.check_click(item.points, clamped_point,self.scale)
            if is_click:
                return True,i
            
        return False,-1


    def add_vertex(self, clamped_point):
        """在DataItem的边上添加顶点"""
       
        is_click,item_idx, best_edge_idx = self.check_edge_click(clamped_point)
        
        if is_click:
            item = self.data_items[item_idx]
            item.insert_point(best_edge_idx, clamped_point)
            self.current_point_index = best_edge_idx
            self.current_item_index = item_idx
            self.update_data_item.emit()

    def add_create_vertex(self, point: QPointF):
        """添加创建DataItem的顶点"""
        self.annotion_frame.set_point(point)
        self.update_data_item.emit()

    def add_split_vertex(self, clamped_point):

        def reset_split_state():
            self.annotion_frame = AnnotationFrameBase.create(AnnotationType.LINE)
            self.split_point_index_start = -1
            self.split_point_index_end = -1
            self.split_item_index = -1

        if self.split_item_index == -1:
 
            is_click,item_idx, _ = self.check_edge_click(clamped_point) # 检查是否点击了多边形的边
            
            item = self.data_items[item_idx]

            item_type = item.annotation.annotation_type

            if not (item_type == AnnotationType.POLYGON or item_type == AnnotationType.DEFAULT):
                return

            if is_click:

                reset_split_state() 

                best_edge_idx,closest_point = Utils.get_closest_point_index_and_edge(self.get_item_points(item_idx), clamped_point)

                self.split_point_index_start = best_edge_idx
                self.split_item_index = item_idx
                self.current_item_index = item_idx
                self.annotion_frame.set_point(closest_point)
        
        else:
            is_click,_ = self.check_frame_click(clamped_point)

            if not is_click:
                best_edge_idx,closest_point = Utils.get_intersection_point(self.get_item_points(self.split_item_index), self.annotion_frame.points[-1], clamped_point)
                if closest_point is None:
                    message.show_error_message("错误", "未找到与分割线相交的点！")
                    keyManager.release_all_keys()
                    return
                else:
                    self.split_point_index_end = best_edge_idx
                    self.annotion_frame.set_point(closest_point)

                self.finish_split()

            else:
                self.annotion_frame.set_point(clamped_point)
        
        self.update_data_item.emit()


    def add_temp_frame_point(self, clamped_point):
        """添加临时多边形顶点"""
        self.annotion_frame.set_temp_point(clamped_point) 
        self.update_data_item.emit()


    def finish_split(self):

        if self.split_item_index == -1:
            return

        points = self.get_item_points(self.split_item_index)

        item_data_1 = []
        item_data_2 = []

        # 分割点在多边形外部
        if self.split_point_index_start > self.split_point_index_end:

            item_data_1.extend(points[0:self.split_point_index_end])
            item_data_1.extend(self.annotion_frame.points[::-1])
            item_data_1.extend(points[self.split_point_index_start:])

        elif self.split_point_index_start == self.split_point_index_end:
            
            item_data_1.extend(points[0:self.split_point_index_end])


            if Utils.compare_points_on_line(self.annotion_frame.points[0],self.annotion_frame.points[-1],
                                            points[self.split_point_index_end-1],points[self.split_point_index_end if self.split_point_index_end < len(points)-1 else 0])==-1:

                item_data_1.extend(self.annotion_frame.points)
            else:
                item_data_1.extend(self.annotion_frame.points[::-1])

            item_data_1.extend(points[self.split_point_index_end:])
        else :
             item_data_1.extend(points[0:self.split_point_index_start])
             item_data_1.extend(self.annotion_frame.points)
             item_data_1.extend(points[self.split_point_index_end:])

        
        # 分割点在多边形内部
        if self.split_point_index_start > self.split_point_index_end:
            item_data_2.extend(self.annotion_frame.points)
            item_data_2.extend(points[self.split_point_index_end:self.split_point_index_start])
        elif self.split_point_index_start == self.split_point_index_end:
            item_data_2 = self.annotion_frame.points
        else:
            item_data_2.extend(self.annotion_frame.points[::-1])
            item_data_2.extend(points[self.split_point_index_start:self.split_point_index_end])


        self.creating_split_vertex = False
        self.annotion_frame = None 

        if not item_data_1 or not item_data_2:
            message.show_error_message("错误", "分割点在多边形内部或外部异常！")
            self.update_data_item.emit()
            return 

        self.delete_item(self.split_item_index)
           
        new_data_item_1 = DataItemInfo(
                id=str(uuid.uuid4()),
                annotation_type=AnnotationType.DEFAULT,
                caseLabel="default",
                points=item_data_1
            )
            
        new_data_item_2 = DataItemInfo(
            id=str(uuid.uuid4()),
            annotation_type=AnnotationType.DEFAULT,
            caseLabel="default",
            points=item_data_2
        )

        self.add_item(new_data_item_1)
        self.add_item(new_data_item_2)


    def finish_create(self,image_size: QSize):

        if not self.annotion_frame:
            return
        
        points = self.annotion_frame.points

        self.creating_data_item = False
        
        clipped_points = polygon_clipper.clip_polygon_to_image(points, image_size)
        
        if clipped_points is None:
            return


        if self.annotion_frame.annotation_type == AnnotationType.BBOX:
            points = Utils.get_rectangle_vertices(points)
            if not points:
                message.show_error_message("错误", "无法计算矩形顶点！")
                return

        data_item = DataItemInfo(
            id=str(uuid.uuid4()),
            annotation_type=self.annotion_frame.annotation_type,
            caseLabel="default",
            points=points
        )
        
        self.add_item(data_item)


dm = DataManager()