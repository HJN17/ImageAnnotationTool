# coding:utf-8
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import pyqtSignal,QObject,QThread,pyqtSlot
from PyQt5.QtWidgets import QWidget

import os
import threading
from natsort import natsorted

from QtUniversalToolFrameWork.common.cache import LRUCache


from common.data_structure import jsonFileManager,DataInfo
from components.info_card import InfoCardInterface
from common.case_label import cl
from common.message import message


class LabelCardManager(QObject):
   
    data_info_signal = pyqtSignal(str, list)

    def __init__(self, parent=None, batch_size=20):
        super().__init__(parent)
        self._cache = LRUCache(capacity=batch_size*2)
        self._batch_size = batch_size
        self._load_worker = None

    def get(self, key):
  
        data_info = self._cache.get(key)
        if data_info:
            return data_info
        image_name = os.path.basename(key).split(".")[0]
        json_path = os.path.join(os.path.dirname(key), f"{image_name}.json")

        try:
            data_info = jsonFileManager.load_json(json_path)
            
            self._on_widget_preloaded(key,data_info)

        except Exception as e:
            message.show_error_message("异常", f"加载 {image_name} 失败！")

            data_info = None
        
        return data_info
    
    
    def _stop_preload(self):
        if self._load_worker and self._load_worker.isRunning():
            self._load_worker.stop()
            self._load_worker.wait()

    def _preload_next_batch(self,image_items:list,current_index:int):
        
        next_batch_start = current_index+1

        next_batch_end = min(next_batch_start + self._batch_size, len(image_items))

        current_batch_paths = image_items[next_batch_start:next_batch_end]

        paths_to_preload = [p for p in current_batch_paths if p not in self._cache.cache.keys()]

        if paths_to_preload:
    
            self._stop_preload()
            
            self._load_worker = LabelCardPreloadWorker(paths_to_preload)
            self._load_worker.progress.connect(self._on_widget_preloaded)
    
            self._load_worker.start()

    @pyqtSlot(str, DataInfo)
    def _on_widget_preloaded(self, path: str, data_info:DataInfo):
        if data_info:
            self._cache.put(path, data_info)
            self.data_info_signal.emit(path,data_info.items)
    


class LabelCardPreloadWorker(QThread):
    """
    预加载线程，用于异步加载图片文件。
    """

    progress = pyqtSignal(str,DataInfo)
    finished = pyqtSignal()
    
    def __init__(self, paths: list):

        super().__init__()

        self._paths = paths
        self._stop_event = threading.Event()

    def run(self):

        for path in self._paths:
            
            if self._stop_event.is_set():
                break
            
            image_name = os.path.basename(path).split(".")[0]
            json_path = os.path.join(os.path.dirname(path), f"{image_name}.json")

            try:
                data_info = jsonFileManager.load_json(json_path)
            except:
                data_info = None

            if data_info:
                self.progress.emit(path, data_info)

        self.finished.emit()


    def stop(self):
        self._stop_event.set()




    