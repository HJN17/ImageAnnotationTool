# coding: utf-8
from PyQt5.QtCore import Qt, QObject, pyqtSlot,pyqtSignal

class KeyManager(QObject):

    ESC= pyqtSignal()
    SHIFT= pyqtSignal(bool)
    N= pyqtSignal(bool)
    S= pyqtSignal(bool)
    X= pyqtSignal(bool)
    B= pyqtSignal(bool)

    _INSTANCE = None 
    _INSTANCE_INIT = False 

    def __new__(cls, *args, **kwargs):
        if not cls._INSTANCE:
            cls._INSTANCE = super().__new__(cls)
        return cls._INSTANCE

    def __init__(self):
        if self._INSTANCE_INIT:
            return self._INSTANCE
        
        self._INSTANCE_INIT = True

        super().__init__()

        self.key_states = {
            Qt.Key_Shift: self.SHIFT,
            Qt.Key_N: self.N,
            Qt.Key_S: self.S,
            Qt.Key_X: self.X,
            Qt.Key_B: self.B,
        }

    def release_all_keys(self):
        for key in self.key_states.keys():
            self.key_states[key].emit(False)

    def press_key(self, qkey: Qt.Key) -> bool:
        
        key_set = self.key_states.keys()
        
        if qkey == Qt.Key_Escape:
            for key in key_set: 
                self.key_states[key].emit(False)
            return True

        if qkey in key_set:
            for key in key_set: 
                if key != qkey:
                    self.key_states[key].emit(False)

            self.key_states[qkey].emit(True)
            return True
        
        return False
    

    def release_key(self, qkey: Qt.Key) -> bool:
        
        if qkey == Qt.Key_Shift:
            self.key_states[qkey].emit(False)
            return True
        
        return False

keyManager = KeyManager()