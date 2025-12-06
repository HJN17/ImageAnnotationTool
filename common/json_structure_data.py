# coding:utf-8

import os
import json
from enum import Enum
from PyQt5.QtCore import QPointF



class AnnotationType(Enum):
    """ 标注类型枚举 """
    BBOX = "bbox" # 矩形框
    POLYGON = "polygon" # 多边形
    DEFAULT = "default" # 默认



class DataItemInfo:
    def __init__(self,  text : str, language : str, points : list[QPointF], annotation_type : AnnotationType = AnnotationType.DEFAULT, caseLabel : str = "default"):
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

        def insert_point(self, index : int, point : QPointF):
            self._points.insert(index, point)
        
        def remove_point(self, index : int):
            self._points.pop(index)

class  DataInfo:
    def __init__(self, file_name : str,items : list[DataItemInfo],label : str = "default",issues : list[str] = []):
        self._file_name = file_name
        self._items = items
        self._label = label
        self._issues = issues
    
    def __str__(self):
        return f"DataInfo(file_name={self.file_name}, items={self.items})"

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

    def all_items_points(self) -> list[QPointF]:
        """返回所有标注点"""
        points = []
        for item in self.items:
            points.extend(item.points)
        return points


def save_json_data(json_path : str, data_info : DataInfo):
    """保存标注数据"""
    if not data_info or not data_info.items:
        raise ValueError("DataInfo 为空或没有标注项")
    
    try:

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_info.__dict__, f, ensure_ascii=False, indent=4)
        
    except Exception as e:
        raise e # 抛出异常，由调用者处理


def load_json_data(json_path) -> DataInfo:
    """加载标注数据"""
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"文件不存在: {json_path}")
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items  = []

        for item in data.get('DataList',[]):

            for charset_dict in item.get('charsets', []):

                poly = charset_dict.get('points', [])
                if not poly:
                    continue
                
                points = [QPointF(p[0], p[1]) for p in poly[0]]
                text = charset_dict.get("text", "")
                language = item.get('language', '')
                items.append(DataItemInfo(text, language, points, AnnotationType.DEFAULT,"character"))
                
            text = item.get("text", "")
            points = [QPointF(p[0], p[1]) for p in item.get('poly', [])]
            language = item.get('language', '')
            items.append(DataItemInfo(text, language, points, AnnotationType.DEFAULT,"string"))

        return DataInfo(file_name=os.path.basename(json_path),items=items)

    except Exception as e:
        raise e


