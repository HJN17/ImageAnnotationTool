from PyQt5.QtCore import pyqtSignal,QObject
from PyQt5.QtCore import pyqtSignal


class AbstractViewer(QObject):
    """
    抽象的“查看器”模型。负责管理一个列表和当前索引，并提供浏览接口。
    当状态变化时，通过信号通知视图。
    
    """

    current_item_changed = pyqtSignal()
    item_deleted = pyqtSignal(int)   
    item_inserted = pyqtSignal(int)  
    model_reset = pyqtSignal()  

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._current_index = -1

    @property
    def items(self):
        return self._items.copy()

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def current_item(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return None

    @property
    def count(self) -> int:
        return len(self._items)

    def set_items(self, items):
        if not isinstance(items, (list, tuple)):
            raise TypeError("items 必须是一个列表或元组。")

        self._items = list(items)
        self._current_index = 0 if self._items else -1
        self.model_reset.emit()
        if self._items:
            self.current_item_changed.emit()

    def insert_item(self, index: int, item):

        if not (0 <= index <= self.count):
            index = self.count

        self._items.insert(index, item)

        if index <= self._current_index:
            self._current_index += 1
            self.current_item_changed.emit()

        self.item_inserted.emit(index)

    def clear(self):
        if self._items:
            self._items.clear()
            self._current_index = -1
            self.model_reset.emit()
    
    def next(self):
        if self._current_index < len(self._items) - 1:
            self.go_to(self._current_index + 1)

    def previous(self):
        if self._current_index > 0:
            self.go_to(self._current_index - 1)

    def go_to(self, index: int):

        if not isinstance(index, int):
            raise TypeError("index 必须是整数。")

        if 0 <= index < self.count and index != self._current_index:
            self._current_index = index
            self.current_item_changed.emit()

    def delete_current(self):
        if self._current_index == -1:
            return

        deleted_index = self._current_index

        del self._items[deleted_index]

        if deleted_index < len(self._items):
            new_index = deleted_index
        else:
            new_index = len(self._items) - 1 

        self._current_index = new_index
        self.current_item_changed.emit()

        self.item_deleted.emit(deleted_index)