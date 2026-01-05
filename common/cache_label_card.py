# coding:utf-8
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import pyqtSignal,QObject,QThread,pyqtSlot
from PyQt5.QtWidgets import QWidget


import threading
from natsort import natsorted

from QtUniversalToolFrameWork.common.cache import LRUCache


from common.data_structure import jsonFileManager
from components.info_card import InfoCardInterface
from common.case_label import cl


class LabelCardManager(QObject):
   
    def __init__(self, batch_size=20):

        self._cache = LRUCache(capacity=batch_size*2)
        self._batch_size = batch_size
    
    def get(self, key):
        return self._cache.get(key)
    
    def put(self, key, value):
        self._cache.put(key, value)

    def _stop_preload(self):
        if self._load_worker and self._load_worker.isRunning():
            self._load_worker.stop()
            self._load_worker.wait()

    def _preload_next_batch(self,json_paths:list,current_index:int):
        
        next_batch_start = current_index+1

        next_batch_end = min(next_batch_start + self._batch_size, len(json_paths))

        current_batch_paths = json_paths[next_batch_start:next_batch_end]

        paths_to_preload = [p for p in current_batch_paths if p not in self._cache.cache.keys()]

        if paths_to_preload:
    
            self._stop_preload()
            
            self._load_worker = LabelCardPreloadWorker(paths_to_preload)
            self._load_worker.progress.connect(self._on_widget_preloaded)
    
            self._load_worker.start()

    @pyqtSlot(str, QWidget)
    def _on_widget_preloaded(self, path: str, widget: QWidget):
        """ 预加载线程完成信号槽函数：处理预加载完成后的缓存更新 """
        if widget:
            self._cache.put(path, widget)


class LabelCardPreloadWorker(QThread):
    """
    预加载线程，用于异步加载图片文件。
    """

    progress = pyqtSignal(str, QWidget)
    finished = pyqtSignal()
    
    def __init__(self, json_paths: list):

        super().__init__()

        self._json_paths = json_paths
        self.is_running = True
        self._stop_event = threading.Event()

    def run(self):
        for path in self._json_paths:

            if self._stop_event.is_set():
                break
            
            infoCard = self._load_widget(path)
    
            if infoCard:
                self.progress.emit(path, infoCard)

        self.finished.emit()

    def _load_widget(self, json_path) -> QWidget:
        try:
      
            data_info = jsonFileManager.load_json(json_path)

            infoCard = InfoCardInterface()

            items = data_info.items

            sorted_items = natsorted(items, key=lambda x: (cl.get_label_name(x.caseLabel)=="default", x.caseLabel)) # 先排序默认标签，再排序其他标签

            for item in sorted_items: 
                infoCard.addItem(item.id,item.caseLabel,item.annotation_type)   

        except Exception:
            infoCard = None

        return infoCard

    def stop(self):
        self._stop_event.set()




    