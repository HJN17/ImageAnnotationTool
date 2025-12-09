# coding:utf-8
import sys
import os
import json
import shutil
from typing import List
from enum import Enum
from PyQt5.QtCore import QPointF
from common.annotation import AnnotationType



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




def save_json_data(json_path : str, data_info : DataInfo):
    """保存标注数据"""
    if not data_info or not data_info.items:
        raise ValueError("DataInfo 为空或没有标注项")
    
    try:

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_info.to_dict(), f, ensure_ascii=False, indent=4)
        
    except Exception as e:
        raise e # 抛出异常，由调用者处理

    

def load_json_data(json_path) -> DataInfo:
    """加载标注数据"""
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"文件不存在: {json_path}")
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        
        return _load_data(data)

    except Exception as e:
        raise e



def _load_data(data: dict) -> DataInfo:
    
    items: List[DataItemInfo] = []

    for item_dict in data.get("items", []):
        points = [QPointF(float(p[0]), float(p[1])) for p in item_dict.get("points", [])]
        anno_type_value = item_dict.get("annotation_type", AnnotationType.DEFAULT.value)
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
    print("load_json_data",data_info)
    return data_info


def _goolge_load_data(data: dict) -> DataInfo:
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





