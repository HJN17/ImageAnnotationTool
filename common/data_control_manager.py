# coding: utf-8

from copy import deepcopy

from PyQt5.QtCore import pyqtSignal, QObject
from common.data_structure import DataItemInfo
from common.signal_bus import signalBus

class DataManager(QObject):
    
    update_data_item = pyqtSignal() # 更新DataItem信号

    split_vertex_created = pyqtSignal() # 分割点创建信号

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

        
        signalBus.selectItem.connect(self._on_select_item)
        signalBus.itemCaseLabelChanged.connect(self._on_item_case_label_changed)
        signalBus.deleteItem.connect(self.delete_data_item_by_key)


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
        if not self.is_current_data_item_valid():
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

    def _on_item_case_label_changed(self, routeKey: str, caseLabel: str):

        if not self.is_current_data_item_valid():
            return
        
        if self.current_data_item.id != routeKey:
            return
        
        self.current_data_item.caseLabel = caseLabel

        self.update_data_item.emit()


    def get_data_item_by_key(self, routeKey: str) -> DataItemInfo:
        if not self.data_items:
            return None
        
        for item in self.data_items:
            if item.id == routeKey:
                return item
        return None

    def get_current_data_item_label(self):    
        if not self.is_current_data_item_valid():
            return None
        
        return self.data_items[self.current_item_index].caseLabel
        

    def is_current_data_item_valid(self):
        return self.data_items and self.current_item_index >= 0 and self.current_item_index < len(self.data_items)


    def delete_data_item_by_key(self, routeKey: str):

        if not self.data_items:
            return
        
        item = self.get_data_item_by_key(routeKey)

        if not item:
            return
        
        self.data_items.remove(item)

        self.current_item_index = -1
        self.current_point_index = -1

        print("删除了多边形")

        self.update_data_item.emit()
        
    
    def delete_data_item_by_index(self, index: int):
        if index < 0 or index >= len(self.data_items):
            return
    
        routeKey = self.data_items[index].id        
        signalBus.deleteItem.emit(routeKey)

    def add_data_item(self, data_item: DataItemInfo):

        self.data_items.append(data_item)
        signalBus.addItem.emit(data_item.id, data_item.caseLabel, data_item.annotation_type)
        self.current_item_index = len(self.data_items) - 1
        self.current_point_index = -1
        self.update_data_item.emit()
        print("添加了多边形")

    def delete_current_point(self):

        if not self.is_current_data_item_valid():
            return 1
        
        if self.current_point_index < 0 or self.current_point_index >= len(self.current_data_item.points):
            return 1
        
        item = self.current_data_item

        if len(item.points) <= 3:
            return 2

        item.remove_point(self.current_point_index)
        dm.current_point_index = -1

        self.update_data_item.emit()
    


dm = DataManager()