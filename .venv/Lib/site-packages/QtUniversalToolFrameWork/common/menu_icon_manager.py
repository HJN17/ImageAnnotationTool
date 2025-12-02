# coding:utf-8
from PyQt5.QtCore import Qt, QObject

class MenuFunctionButtonManager(QObject):
    _instance = None 
    _initialized = False # 是否初始化

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not MenuFunctionButtonManager._initialized:
            super().__init__()
            MenuFunctionButtonManager._initialized = True
            self._menuFunctionButtonItems = {}

    def __str__(self):
        return f"MenuFunctionButtonManager({self._menuFunctionButtonItems})"

    def remove_menu_function_button_item(self, ui_key : str, button_item):

        if ui_key in self._menuFunctionButtonItems:
            self._menuFunctionButtonItems[ui_key].remove(button_item)

    def set_menu_function_button_item(self, ui_key : str, button_item):

        if ui_key in self._menuFunctionButtonItems:
            self._menuFunctionButtonItems[ui_key].append(button_item)
        else:
            self._menuFunctionButtonItems[ui_key] = [button_item]

    def get_menu_function_button_items(self, ui_key : str):
        return self._menuFunctionButtonItems.get(ui_key, [])


mfb = MenuFunctionButtonManager()