#coding=utf-8

from typing import List

from QtUniversalToolFrameWork.common.config import qconfig,ConfigItem,ConfigValidator



class LabelListValidator(ConfigValidator):
    """ 标签列表验证器：验证列表中的所有路径是否存在，并过滤无效路径 """

    def validate(self, value):
        return value != []

    def correct(self, value):
        items = ["default"]
        for item in value:
            if item.strip() != "":
                if item not in items:
                    items.append(item.strip())
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
        "Labels", "LabelList", [], LabelListValidator())
setattr(qconfig, "labelMode", labelConfigItem)


attrConfigItem = ConfigItem(
        "Attributes", "", [], AttributeListValidator())
setattr(qconfig, "attrMode", attrConfigItem)



