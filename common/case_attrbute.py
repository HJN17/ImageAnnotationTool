#coding=utf-8
from typing import List
from enum import Enum
from copy import deepcopy

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QColor, QTransform
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject

from QtUniversalToolFrameWork.common.style_sheet import themeColor
from QtUniversalToolFrameWork.common.config import qconfig
from common.message import message
from common.utils import Utils


class AttributeType(Enum):
    
    OPTION = "选项框"
    INPUT = "输入框"


class CaseAttribute(QObject):


    update_attr_changed = pyqtSignal()

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

        self._items = []

    @property
    def items(self) -> List[dict]:
        return self._items


    def get_items(self, label_name: str) -> List[dict]:
        items = []

        for item in self._items:
            if item["label_name"] == "default" or item["label_name"] == label_name:
                items.append(item)


        return items

    def set_attr(self, items:list,show_msg:bool=True):
        
        self._items.clear()

        temp_items = []
        name_list= {}
        for item in items:
            
            if item.get("attr_name") is None:
                message.show_message_dialog("异常",f"{item.get('label_name')}属性名称不能为空！")
                return

            try:
                type = AttributeType(item.get("attr_type"))
            except ValueError:
                message.show_message_dialog("异常",f"{item.get('label_name')}_{item.get('attr_name')}属性类型错误！")
                return

            if type == AttributeType.OPTION and len(item.get("attr_value")) == 0:
                message.show_message_dialog("异常",f"{item.get('label_name')}_{item.get('attr_name')}选项属性值不能为空！")
                return
            
            temp_dict = {
                "label_name": item.get("label_name"),
                "attr_name": item.get("attr_name"),
                "attr_type": item.get("attr_type"),
            }

            if type == AttributeType.OPTION:
                temp_dict["attr_value"] = item.get("attr_value")

            if show_msg:
                if item.get("label_name") in name_list.keys():
                    if name_list[item.get("label_name")] == item.get("attr_name"):
                        message.show_message_dialog("异常",f"{item.get('label_name')}的{item.get('attr_name')}属性名称重复！")
                        return
                
                name_list[item.get("label_name")] = item.get("attr_name")

            temp_items.append(temp_dict)
            

        


        if show_msg:
            message.show_success_message("提示",f"属性设置成功😄")
        
        
        qconfig.set(qconfig.attrMode,temp_items)
        self._items = deepcopy(temp_items)

        self.update_attr_changed.emit()

    def get_attr_name(self, label_name: str) -> List[str]:
        name = []
        for item in self._items:
            if item["label_name"] == label_name:
                if "attr_name" in item.keys():
                    name.append(item["attr_name"])
        return name
    
    def get_attr_type(self, label_name: str,attr_name: str):
        for item in self._items:
            if item["label_name"] == label_name:
                if attr_name in item.keys():
                    return item["attr_type"]
        return AttributeType.OPTION
    
    def get_attr_value(self, label_name: str,attr_name: str):
        
        type = self.get_attr_type(label_name,attr_name)
        if type == AttributeType.INPUT:
            return [] # 输入框默认值为空

        for item in self._items:
            if item["label_name"] == label_name:
                if attr_name in item.keys():
                    return item[attr_name]
        return []


cattr = CaseAttribute()
