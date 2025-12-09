# coding:utf-8
import sys
import os
import json
import shutil
from typing import List
from PyQt5.QtCore import QPointF
from common.annotation import AnnotationType
import time
import threading
from collections import defaultdict 
from copy import deepcopy

class DataItemInfo:
    def __init__(self,  text : str = "", language : str = "", points : list[QPointF] = [], annotation_type : AnnotationType = AnnotationType.DEFAULT, caseLabel : str = "default"):
        self._text = text
        self._language = language
        self._annotation_type = annotation_type
        self._caseLabel = caseLabel
        self._points = points

    @property
    def text(self) -> str:
        return self._text
    
    @property
    def language(self) -> str:
        return self._language
    
    @property
    def annotation_type(self) -> AnnotationType:
        return self._annotation_type
    
    @property
    def caseLabel(self) -> str:
        return self._caseLabel
    
    @property
    def points(self) -> list[QPointF]:
        return self._points
    
    @text.setter
    def text(self, value : str):
        self._text = value
            
    @language.setter
    def language(self, value : str):
        self._language = value
            
    @annotation_type.setter
    def annotation_type(self, value : AnnotationType):
        self._annotation_type = value
    
    @caseLabel.setter
    def caseLabel(self, value : str):
        self._caseLabel = value
    
    @points.setter
    def points(self, value : list[QPointF]):
        self._points = value

    def insert_point(self, index : int, point : QPointF = QPointF()):
        self._points.insert(index, point)
    
    def remove_point(self, index : int):
        self._points.pop(index)

    
    def to_dict(self):
        return {
            "text": self.text,
            "language": self.language,
            "annotation_type": self.annotation_type.value,
            "caseLabel": self.caseLabel,
            "points": [[p.x(),p.y()] for p in self.points]
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
    MAX_RETRY = 5  
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
        
        self._json_cache = defaultdict(lambda: ({}, 0.0, 0.0))  # 新增：(数据, 最后修改时间, 最后访问时间)
        self._write_timers = {} # 写入定时器: {文件路径: 定时器对象}
        self._write_locks = defaultdict(threading.Lock)   # 写入锁: {文件路径: 互斥锁}
        self._cache_lock = threading.Lock()   # 缓存锁（保护缓存和定时器操作）

        self._cleanup_thread = threading.Thread(target=self._cache_cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _atomic_save_json(self, json_path : str, data_info : DataInfo): # 原子写入JSON（内部方法，加锁+临时文件替换）
        
        lock = self._write_locks[json_path] # 获取文件的写入锁
        lock.acquire() # 其他线程会阻塞在 acquire() 处，直到第一个线程释放锁，才会依次执行。
        try:
            temp_json_path = f"{json_path}.tmp"

            with open(temp_json_path, 'w', encoding='utf-8') as f:
                json.dump(data_info.to_dict(), f, ensure_ascii=False, indent=4) # 写入JSON文件（确保中文正常显示）

            print(f"_atomic_save_json: {json_path}")

            os.replace(temp_json_path, json_path)
        finally:
            lock.release() # 释放锁，允许其他线程写入


    def _safe_load_json(self, json_path : str): # 检查临时文件（写入中断时优先读临时文件）
        
        read_path = json_path if not os.path.exists(f"{json_path}.tmp") else f"{json_path}.tmp"

        if not os.path.exists(read_path):
            return {}
        
        # 重试读取（避免写入未完成）
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
        """清理过期/超量的缓存"""
        with self._cache_lock:
            now = time.time()
            
            expired_paths = [
                path for path, (_, _, last_access) in self._json_cache.items()
                if now - last_access > self.CACHE_EXPIRE_SEC
            ]

            if len(self._json_cache) > self.MAX_CACHE_SIZE:

                sorted_items = sorted(self._json_cache.items(),key=lambda x: x[1][2]) # 按最后访问时间升序

                overflow_count = len(self._json_cache) - self.MAX_CACHE_SIZE # 计算需要清理的数量
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
        """定时清理缓存的循环（守护线程）"""
        while True:
            time.sleep(60)  # 每1分钟执行一次清理
            self._cache_cleanup()


    def save_json(self, json_path : str, data_info : DataInfo): # 更新JSON（先更缓存，延迟写磁盘）

        with self._cache_lock:
            

            if self._get_data_size(data_info) > self.MAX_CACHE_SIZE_BYTES:

                self._atomic_save_json(json_path, data_info)
                return


            self._json_cache[json_path] = (deepcopy(data_info), time.time(), time.time())
           
            if json_path in self._write_timers: # 存在旧定时器，取消
                self._write_timers[json_path].cancel() # 取消旧定时器

            timer = threading.Timer(self.DELAY_WRITE_MS / 1000, self._atomic_save_json, args=(json_path, data_info)) # 延迟写入磁盘
            self._write_timers[json_path] = timer
            timer.start()
        
    def load_json(self, json_path : str):
        
        with self._cache_lock:
            if json_path in self._json_cache:
                data_info, modify_time, _ = self._json_cache[json_path]
                # 更新最后访问时间

                print(f"json_cache: {self._json_cache[json_path]}")

                self._json_cache[json_path] = (data_info, modify_time, time.time())

                return deepcopy(data_info)
        
        data = self._safe_load_json(json_path)

        data_info = self._load_data_info(data)

        with self._cache_lock:
            self._json_cache[json_path] = (deepcopy(data_info), time.time(), time.time())

        print(f"data_info: {data_info}")
        return data_info


    def exit_handler(self):
        print("程序退出，开始写入所有缓存到磁盘...")
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

        for item_dict in data.get("items", []):
            points = [QPointF(float(p[0]), float(p[1])) for p in item_dict.get("points", [])]
            anno_type_value = item_dict.get("annotation_type", AnnotationType.DEFAULT)
            try:
                annotation_type = AnnotationType(anno_type_value)
            except ValueError:
                annotation_type = AnnotationType.DEFAULT
            
            data_item = DataItemInfo(
                text=item_dict.get("text", ""),
                language=item_dict.get("language", ""),
                annotation_type=annotation_type,
                caseLabel=item_dict.get("caseLabel", "default"),
                points=points
            )
            items.append(data_item)


        data_info = DataInfo(
                file_name=data.get("file_name", ""),
                label=data.get("label", "default"),
                issues=data.get("issues", []),
                items=items
            ) 
        
        return data_info


    def _goolge_load_data_info(self, data: dict) -> DataInfo:
        """加载标注数据"""
        items  = []

        for item in data.get('DataList',[]):

            for charset_dict in item.get('charsets', []):

                poly = charset_dict.get('poly', [])

                if not poly:
                    continue
                
                points = [QPointF(p[0], p[1]) for p in poly[0]]
                text = charset_dict.get("text", "")
                language = item.get('language', '')
                items.append(DataItemInfo(text, language, points, AnnotationType.DEFAULT,"character"))
            
            file_name = data.get("FilePath", "")
            text = item.get("text", "")
            points = [QPointF(p[0], p[1]) for p in item.get('poly', [])]
            language = item.get('language', '')
            items.append(DataItemInfo(text, language, points, AnnotationType.DEFAULT,"string"))
            return DataInfo(file_name=file_name,items=items)



jsonFileManager = JsonFileManager()



# import atexit
# atexit.register(exit_handler)