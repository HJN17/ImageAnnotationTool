#coding=utf-8

from typing import List
from PyQt5.QtGui import QColor
from QtUniversalToolFrameWork.common.config import qconfig,ConfigItem,ConfigValidator,ConfigSerializer
from QtUniversalToolFrameWork.common.color import themeColor
from common.utils import Utils

class LabelListValidator(ConfigValidator):
    """ 标签列表验证器：验证列表中的所有路径是否存在，并过滤无效路径 """

    def validate(self, value):
        return value != []
    
    def correct(self, value):
        items = []
        for item in value:
            if item not in items:
                items.append(item)
        return items
    

class LabelColorListValidator(ConfigValidator):

    def validate(self, value):
        return value != []

    def correct(self, value):
        items = []
        for item in value:
            if item not in items:
                color = item if QColor(item).isValid() else Utils.generate_random_color()
                items.append(color)
        return items

class  LabelColorListSerializer(ConfigSerializer):

    def serialize(self, value):
        items = []
        for item in value:
            items.append(item.name(QColor.HexArgb))
        return items

    def deserialize(self, value):

        items = []
        for item in value:
            items.append(QColor(item))
        return items


class AttributeListValidator(ConfigValidator):
    """ 属性列表验证器：验证列表中的所有路径是否存在，并过滤无效路径 """

    def validate(self, value): # 验证属性列表是否为空
        return value != []

    def correct(self, value):
        items = []
        for item in value:
            if isinstance(item, dict):
                items.append(item)
        return items


labelConfigItem = ConfigItem(
        "Labels", "LabelList", ["default"], LabelListValidator())
setattr(qconfig, "labelMode", labelConfigItem)

labelConfigItem = ConfigItem("Labels", "LabelColorList", [themeColor()], LabelColorListValidator(), LabelColorListSerializer())
setattr(qconfig, "labelColorMode", labelConfigItem)

attrConfigItem = ConfigItem(
        "Attributes", "", [], AttributeListValidator())
setattr(qconfig, "attrMode", attrConfigItem)



