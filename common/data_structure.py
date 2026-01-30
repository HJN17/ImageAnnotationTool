# coding:utf-8
import os
import json
import time
import threading
from collections import defaultdict 
from copy import deepcopy
from typing import List
from PyQt5.QtCore import QPointF, QTimer

from common.annotation import AnnotationType,AnnotationFrameBase
from common.utils import Utils
from common.case_label import cl
from common.message import message


class DataItemInfo:

    def __init__(self,id : str, annotation_type : str = "default", caseLabel : str = "",points : list[QPointF] = [],attributes : List[dict[str,object]] = []):

        self._id = id
        self._annotation_type = self.verify_annotation_type(annotation_type)
        self._annotation = AnnotationFrameBase.create(self._annotation_type)
        self._caseLabel = caseLabel
        self._attributes = attributes
        self._points = self.validate_points(points)
       
    @property
    def id(self) -> str:
        return self._id

    @property
    def annotation_type(self) -> AnnotationType:
        return self._annotation_type
    
    @property
    def caseLabel(self) -> str:
        return self._caseLabel
        
    @property
    def attributes(self) -> dict[str,str]:
        return self._attributes
    
    @property
    def points(self) -> list[QPointF]:

        if self._annotation_type == AnnotationType.BBOX:
            return Utils.get_rectangle_points(self._points)

        return self._points
    
    @property
    def origin_points(self) -> list[QPointF]:
        return self._points
    
    @property
    def annotation(self) -> AnnotationFrameBase:
        return self._annotation

    def validate_points(self, points : list[QPointF]):

        length = len(points)

        if not self._annotation.verify_points(length):

            message.show_message_dialog("错误!", "点的数量不符合要求")

            raise Exception("The number of points does not meet the requirements.")
        
        return points

    @id.setter
    def id(self, value : str):
        self._id = value
    
    @annotation_type.setter
    def annotation_type(self, value : AnnotationType):
        self._annotation_type = value
    
    @caseLabel.setter
    def caseLabel(self, value : str):
        self._caseLabel = value
        
    @attributes.setter
    def attributes(self, value : dict[str,str]):
        self._attributes = value
        
    @points.setter
    def points(self, value : list[QPointF]):
        
        if self._annotation_type == AnnotationType.BBOX:
            self._points =  Utils.get_rectangle_vertices(value)
            return
        
        self._points = value

    def insert_point(self, index : int, point : QPointF = QPointF()):
        self._points.insert(index, point)
    
    def remove_point(self, index : int):
        self._points.pop(index)

    def get_attribute_name(self, index : int):
        return self._attributes[index].get("attr_name")
    
    def get_attribute_type(self, index : int):
        return self._attributes[index].get("attr_type")

    def get_attribute_value(self, index : int):
        return self._attributes[index].get("attr_value")

    # 验证annotation_type是否合法
    def verify_annotation_type(self, value : str):
        try:
            return AnnotationType(value)
        
        except ValueError:
            
            return AnnotationType.DEFAULT
    

    def to_dict(self):
        return {
            "annotation_type": self._annotation_type.value,
            "caseLabel": self._caseLabel,
            "attributes": self._attributes,
            "points": [[p.x(),p.y()] for p in self._points]
        }




class  DataInfo:
    def __init__(self, file_name : str,items : list[DataItemInfo],label : str = "default",issues : list[str] = []):
        self._file_name = file_name
        self._label = label
        self._issues = issues
        self._items = items

    @property
    def file_name(self) -> str:
        return self._file_name
    
    @property
    def items(self) -> list[DataItemInfo]:
        return self._items
    
    @property
    def label(self) -> str:
        return self._label
    
    @property
    def issues(self) -> list[str]:
        return self._issues
    
    @label.setter
    def label(self, value : str):
        self._label = value
    
    @issues.setter
    def issues(self, value : list[str]):
        self._issues = value

    @file_name.setter
    def file_name(self, value : str):
        self._file_name = value

    def add_items(self, item: DataItemInfo):
        self._items.append(item)
    
    def remove_item(self, index: int):
        if 0 <= index < len(self._items):
            del self._items[index]
    
    @property
    def all_items_points(self) -> list[QPointF]:
        """返回所有标注点"""
        points = []
        for item in self.items:
            points.extend(item.points)
        return points
    
    def to_dict(self):
        return {
            "file_name": self.file_name,
            "label": self.label,
            "issues": self.issues,
            "items": [item.to_dict() for item in self.items],
        }

class JsonFileManager:

    DELAY_WRITE_MS = 500
    MAX_RETRY = 5   # 最大重试次数
    RETRY_INTERVAL = 0.01

    CACHE_EXPIRE_SEC = 300
    MAX_CACHE_SIZE = 1000 

    MAX_CACHE_SIZE_BYTES = 1024 * 1024 * 10 

    _INSTANCE = None 
    _INSTANCE_INIT = False 
    _INSTANCE_LOCK = threading.Lock() 
    
    def __new__(cls, *args, **kwargs):
        with cls._INSTANCE_LOCK:
            if not cls._INSTANCE:
                cls._INSTANCE = super().__new__(cls)
        return cls._INSTANCE

    def __init__(self):

        if self._INSTANCE_INIT:
            return
        self._INSTANCE_INIT = True
        
        self._json_cache = defaultdict(lambda: ({}, 0.0, 0.0)) 
        self._write_timers = {} # 写入定时器: {文件路径: 定时器对象}

        self._write_locks = defaultdict(threading.Lock)   # 写入锁: {文件路径: 互斥锁}
        self._cache_lock = threading.Lock() # 缓存锁: 保护缓存数据结构的并发访问

        self._cleanup_thread = threading.Thread(target=self._cache_cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _atomic_save_json(self, json_path : str, data_info : DataInfo): # 原子写入JSON（内部方法，加锁+临时文件替换）
        
        lock = self._write_locks[json_path] 

        lock.acquire() 
        try:
            temp_json_path = f"{json_path}.tmp"

            with open(temp_json_path, 'w', encoding='utf-8') as f:
                json.dump(data_info.to_dict(), f, ensure_ascii=False, indent=4) 

            os.replace(temp_json_path, json_path)
        finally:
            lock.release()


    def _safe_load_json(self, json_path : str): 
        
        read_path = json_path if not os.path.exists(f"{json_path}.tmp") else f"{json_path}.tmp"

        if not os.path.exists(read_path):
            return {}
        
        retry_count = 0
        while retry_count < self.MAX_RETRY:
            try:
                with open(read_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                retry_count += 1
                time.sleep(self.RETRY_INTERVAL)
        return {} 

    def _get_data_size(self, data_info : DataInfo):

        return len(json.dumps(data_info.to_dict()))

    def _cache_cleanup(self):
        with self._cache_lock:

            now = time.time()
            
            expired_paths = [
                path for path, (_, _, last_access) in self._json_cache.items()
                if now - last_access > self.CACHE_EXPIRE_SEC
            ]

            if len(self._json_cache) > self.MAX_CACHE_SIZE:

                sorted_items = sorted(self._json_cache.items(),key=lambda x: x[1][2]) # 按最后访问时间升序

                overflow_count = len(self._json_cache) - self.MAX_CACHE_SIZE 
                overflow_paths = [path for path, _ in sorted_items[:overflow_count]]
            else:
                overflow_paths = []

            # 执行清理
            for path in expired_paths + overflow_paths:
                del self._json_cache[path]

                # 同时清理无效的定时器（如果有）
                if path in self._write_timers:
                    self._write_timers[path].cancel()
                    del self._write_timers[path]

            if expired_paths or overflow_paths:
                print(f"清理缓存：过期{len(expired_paths)}个，超量{len(overflow_paths)}个，剩余{len(self._json_cache)}个")
    
    def _cache_cleanup_loop(self):
        while True:
            time.sleep(60) 
            self._cache_cleanup()
            
    def save_json(self, json_path : str, data_info : DataInfo): 

        with self._cache_lock:
            

            if self._get_data_size(data_info) > self.MAX_CACHE_SIZE_BYTES:

                self._atomic_save_json(json_path, data_info)
                return


            self._json_cache[json_path] = (deepcopy(data_info), time.time(), time.time())
           
            if json_path in self._write_timers: 
                self._write_timers[json_path].cancel() 

            timer = threading.Timer(self.DELAY_WRITE_MS / 1000, self._atomic_save_json, args=(json_path, data_info))
            self._write_timers[json_path] = timer
            timer.start()
        
    def load_json(self, json_path : str):
        
        with self._cache_lock:

            if json_path in self._json_cache:

                data_info, modify_time, _ = self._json_cache[json_path]
                # 更新最后访问时间

                self._json_cache[json_path] = (data_info, modify_time, time.time())

                return deepcopy(data_info) 
        

        data = self._safe_load_json(json_path) # 安全加载JSON

        
        data_info = self._load_data_info(data)


        with self._cache_lock:
            self._json_cache[json_path] = (deepcopy(data_info), time.time(), time.time())

        return data_info


    def exit_handler(self):
        with self._cache_lock:
            for path, timer in self._write_timers.items():
                if timer.is_alive():
                    timer.cancel()
            self._write_timers.clear()
            for path, (data, _, _) in self._json_cache.items():
                if data:
                    self._atomic_save_json(path, data)
            self._json_cache.clear()

    def _load_data_info(self, data) -> DataInfo:

        items: List[DataItemInfo] = []

        id = 0

        for item_dict in data.get("items", []):
            
            points = [QPointF(float(p[0]), float(p[1])) for p in item_dict.get("points", [])]

    
            data_item = DataItemInfo(
                id=str(id),
                annotation_type=item_dict.get("annotation_type", "default"),
                caseLabel=item_dict.get("caseLabel", "default"),
                attributes=item_dict.get("attributes", [{}]),
                points=points
            )

            items.append(data_item)
            
            id += 1

        data_info = DataInfo(
                file_name=data.get("file_name", ""),
                label=data.get("label", "default"),
                issues=data.get("issues", []),
                items=items
            ) 
        
        return data_info

jsonFileManager = JsonFileManager()







