# coding:utf-8
from enum import Enum
from string import Template
from typing import List, Union
import weakref  # 导入weakref模块，用于创建弱引用，避免因强引用导致的内存泄漏（如管理组件生命周期）
from PyQt5.QtCore import QFile, QObject, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget,QGraphicsDropShadowEffect
from .config import qconfig, Theme, isDarkTheme


class StyleSheetManager(QObject):
    """ 样式表管理器，用于注册、管理和自动更新界面组件的样式表 """

    def __init__(self):
        super().__init__()
        self.widgets = weakref.WeakKeyDictionary()  # 弱引用字典，存储组件与样式表的映射

    def register(self, source, widget: QWidget, reset=True):
        """ 向管理器注册组件，使其样式表可被自动管理    """
        
        if isinstance(source, str):
            source = StyleSheetFile(source)
        
        if widget not in self.widgets:
            widget.destroyed.connect(lambda: self.deregister(widget))
            widget.installEventFilter(CustomStyleSheetWatcher(widget)) # 安装自定义样式表监听器
            widget.installEventFilter(DirtyStyleSheetWatcher(widget))  # 安装事件过滤器，监听样式表变化
            self.widgets[widget] = StyleSheetCompose([source, CustomStyleSheet(widget)]) # 组合基础样式源和自定义样式源

        if not reset:
            self.source(widget).add(source)
        else:
            self.widgets[widget] = StyleSheetCompose([source, CustomStyleSheet(widget)])

    def deregister(self, widget: QWidget):   
        if widget not in self.widgets:
            return

        self.widgets.pop(widget)

    def items(self):
        return self.widgets.items()

    def source(self, widget: QWidget):
        return self.widgets.get(widget, StyleSheetCompose([]))

styleSheetManager = StyleSheetManager() 


class StyleSheetBase:
    """ 样式表基类，定义样式源的通用接口（文件型、自定义型样式源均继承此类） """

    def path(self, theme=Theme.AUTO):
        raise NotImplementedError

    def content(self, theme=Theme.AUTO):
        return getStyleSheetFromFile(self.path(theme))

    def apply(self, widget: QWidget, theme=Theme.AUTO):
        setStyleSheet(widget, self, theme)

class StyleSheetCompose(StyleSheetBase):
    """ 样式表组合类，继承自StyleSheetBase，用于组合多个样式源（如基础样式+自定义样式） """

    def __init__(self, sources: List[StyleSheetBase]):
        self.sources = sources

    def content(self, theme=Theme.AUTO):
    
        return '\n'.join([i.content(theme) for i in self.sources])

    def add(self, source: StyleSheetBase):
        """ 向组合中添加新的样式源"""

        if source is self or source in self.sources:
            return

        self.sources.append(source)

    def remove(self, source: StyleSheetBase):
        """ 从组合中移除指定的样式源 """
       
        if source not in self.sources:
            return

        self.sources.remove(source)

class FluentStyleSheet(StyleSheetBase, Enum):
    """ Fluent风格内置样式表枚举，定义各组件的预设样式（如按钮、对话框等） """

    MENU = "menu"   # 菜单组件样式
    LABEL = "label" # 标签组件样式
    PIVOT = "pivot" # 选项卡组件样式
    BUTTON = "button" # 按钮组件样式
    DIALOG = "dialog" # 对话框组件样式
    SLIDER = "slider" # 滑块组件样式
    INFO_BAR = "info_bar" # 信息提示条组件样式
    SPIN_BOX = "spin_box" # 数字输入框组件样式
    TAB_VIEW = "tab_view" # 标签页组件样式
    TOOL_TIP = "tool_tip" # 工具提示组件样式    
    CHECK_BOX = "check_box" # 复选框组件样式
    COMBO_BOX = "combo_box" # 下拉框组件样式
    FLIP_VIEW = "flip_view" # 翻转视图组件样式  
    LINE_EDIT = "line_edit" # 单行输入框组件样式
    LIST_VIEW = "list_view" # 列表视图组件样式
    TREE_VIEW = "tree_view" # 树视图组件样式
    INFO_BADGE = "info_badge" # 信息标记组件样式
    PIPS_PAGER = "pips_pager" # 页码导航组件样式
    TABLE_VIEW = "table_view" # 表格视图组件样式
    CARD_WIDGET = "card_widget" # 卡片组件样式
    TIME_PICKER = "time_picker" # 时间选择器组件样式
    COLOR_DIALOG = "color_dialog"   # 颜色选择对话框组件样式
    MEDIA_PLAYER = "media_player"   # 媒体播放器组件样式
    SETTING_CARD = "setting_card"   # 设置卡片组件样式
    TEACHING_TIP = "teaching_tip"   # 教学提示组件样式
    FLUENT_WINDOW = "fluent_window" # fluent风格窗口组件样式
    SWITCH_BUTTON = "switch_button" # 开关按钮组件样式
    MESSAGE_DIALOG = "message_dialog"   # 消息对话框组件样式
    STATE_TOOL_TIP = "state_tool_tip"   # 状态工具提示组件样式
    CALENDAR_PICKER = "calendar_picker" # 日历选择器组件样式
    FOLDER_LIST_DIALOG = "folder_list_dialog"   # 文件夹列表对话框组件样式
    SETTING_CARD_GROUP = "setting_card_group"   # 设置卡片组组件样式
    EXPAND_SETTING_CARD = "expand_setting_card"   # 可展开设置卡片组件样式
    NAVIGATION_INTERFACE = "navigation_interface"   # 导航界面组件样式


    SAMPLE_CARD = "sample_card"
    HOME_INTERFACE = "home_interface"
    SETTING_INTERFACE = "setting_interface"


    def path(self, theme=Theme.AUTO):
        
        theme = qconfig.themeMode.value if theme == Theme.AUTO else theme
        
        return f":/resource/qss/{theme.value.lower()}/{self.value}.qss"

class StyleSheetFile(StyleSheetBase):
    """ 文件型样式源类，继承自StyleSheetBase，用于从本地文件加载样式表 """

    def __init__(self, path: str):
        super().__init__()
        self.filePath = path

    def path(self, theme=Theme.AUTO):
        
        return self.filePath

class CustomStyleSheet(StyleSheetBase):
    """ 自定义样式源类，继承自StyleSheetBase，用于存储组件的自定义样式（支持浅色/深色主题区分） """

    DARK_QSS_KEY = 'darkCustomQss'
    LIGHT_QSS_KEY = 'lightCustomQss'
    
    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self._widget = weakref.ref(widget) # 把 widget 对象的弱引用保存到 self._widget，用于后续访问组件属性

    def path(self, theme=Theme.AUTO):
        return ''

    @property
    def widget(self):
        """ 获取弱引用指向的组件（可能为None，若组件已销毁） """
        return self._widget()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CustomStyleSheet): 
            return False 

        return other.widget is self.widget 

    def setCustomStyleSheet(self, lightQss: str, darkQss: str):
        """ 为组件设置自定义样式表（同时指定浅色和深色主题）"""

        if self.widget:
            self.widget.setProperty(self.LIGHT_QSS_KEY, lightQss)
            self.widget.setProperty(self.DARK_QSS_KEY, darkQss)
        return self

    def content(self, theme=Theme.AUTO) -> str:
        """ 获取当前主题对应的自定义样式表内容（重写StyleSheetBase.content方法）"""
        
        theme = qconfig.themeMode.value if theme == Theme.AUTO else theme

        if not self.widget:
            return ''

        if theme == Theme.LIGHT:
            return self.widget.property(self.LIGHT_QSS_KEY) or ''
        return self.widget.property(self.DARK_QSS_KEY) or ''



class CustomStyleSheetWatcher(QObject):
    """ 自定义样式表监听器，继承自QObject，用于监听组件的自定义样式表变化 """

    def eventFilter(self, obj: QWidget, e: QEvent):
        if e.type() != QEvent.DynamicPropertyChange:# 动态属性变化事件
            return super().eventFilter(obj, e)

        name = e.propertyName().data().decode() # 动态属性名称
        if name in [CustomStyleSheet.LIGHT_QSS_KEY, CustomStyleSheet.DARK_QSS_KEY]:
            addStyleSheet(obj, CustomStyleSheet(obj)) # 添加自定义样式表

        return super().eventFilter(obj, e)


class DirtyStyleSheetWatcher(QObject):
    """ 脏样式表监听器，继承自QObject，用于延迟更新组件样式表（优化主题切换性能） """

    def eventFilter(self, obj: QWidget, e: QEvent):
        """ 事件过滤器：监听组件的绘制事件，延迟更新脏样式表  """
        if e.type() != QEvent.Type.Paint or not obj.property('dirty-qss'):
            return super().eventFilter(obj, e)
        
        obj.setProperty('dirty-qss', False)
     
        if obj in styleSheetManager.widgets:
            obj.setStyleSheet(getStyleSheet(styleSheetManager.source(obj)))

        return super().eventFilter(obj, e)

class QssTemplate(Template):

    delimiter = '--'

def applyThemeColor(qss: str):
    """ 将主题色变量替换为实际颜色值，应用到QSS样式表中 """
    template = QssTemplate(qss)
    mappings = {c.value: c.name() for c in ThemeColor._member_map_.values()}
    return template.safe_substitute(mappings)

def getStyleSheetFromFile(file: Union[str, QFile]):
    """ 从文件读取QSS样式表内容（支持路径字符串或QFile对象）"""
    f = QFile(file)
    f.open(QFile.ReadOnly)
    qss = str(f.readAll(), encoding='utf-8')
    f.close()
    return qss

def getStyleSheet(source: Union[str, StyleSheetBase], theme=Theme.AUTO):
    """ 获取组件当前的样式表内容（根据主题模式应用主题色替换）"""
    if isinstance(source, str):
        source = StyleSheetFile(source)

    return applyThemeColor(source.content(theme))


def addStyleSheet(widget: QWidget, source: Union[str, StyleSheetBase], theme=Theme.AUTO, register=True):
    """ 添加样式表到组件（支持注册和非注册模式）"""
    if register:
        styleSheetManager.register(source, widget, reset=False)
        qss = getStyleSheet(styleSheetManager.source(widget), theme)
    else:
        qss = widget.styleSheet() + '\n' + getStyleSheet(source, theme)

    if qss.rstrip() != widget.styleSheet().rstrip():
        widget.setStyleSheet(qss)

def setStyleSheet(widget: QWidget, source: Union[str, StyleSheetBase], theme=Theme.AUTO, register=True):

    if register:
        styleSheetManager.register(source, widget)

    widget.setStyleSheet(getStyleSheet(source, theme))

def setCustomStyleSheet(widget: QWidget, lightQss: str, darkQss: str):
    """ 为组件设置自定义样式表（分别指定浅色和深色主题）"""
    CustomStyleSheet(widget).setCustomStyleSheet(lightQss, darkQss)
    
def updateStyleSheet(lazy=False):
    """ 更新所有已注册组件的样式表（通常在主题切换时调用）"""
    
    removes = []

    for widget, file in styleSheetManager.items():
        try:
            if not (lazy and widget.visibleRegion().isNull()):
                setStyleSheet(widget, file, qconfig.themeMode.value)
            else:
                styleSheetManager.register(file, widget)
                widget.setProperty('dirty-qss', True)
        except RuntimeError:
            removes.append(widget)
            
    for widget in removes:
        styleSheetManager.deregister(widget)



class ThemeColor(Enum):
    """ 主题颜色枚举，定义不同深浅的主题色系（基于主题主色派生） """
    PRIMARY = "ThemeColorPrimary"   # 主题主色（原始主题色）
    DARK_1 = "ThemeColorDark1"   # 主题深色1（比主色暗10%）
    DARK_2 = "ThemeColorDark2"   # 主题深色2（比主色暗18%）
    DARK_3 = "ThemeColorDark3"   # 主题深色3（比主色暗30%）

    LIGHT_1 = "ThemeColorLight1"   # 主题浅色1（比主色亮5%）    
    LIGHT_2 = "ThemeColorLight2"    # 主题浅色2（比主色亮15%，饱和度降低22%）
    LIGHT_3 = "ThemeColorLight3"   # 主题浅色3（比主色亮25%，饱和度降低35%）

    def name(self):
        return self.color().name()

    def color(self):
        """ 获取当前主题色的QColor对象（根据当前主题动态调整HSV值）"""

        color = qconfig.get(qconfig.themeColor) 

        h, s, v, _ = color.getHsvF()

        if isDarkTheme():
            # 深色主题：降低饱和度，固定明度为1（最亮）
            s *= 0.84
            v = 1
            if self == self.DARK_1:
                v *= 0.9
            elif self == self.DARK_2:
                s *= 0.977
                v *= 0.82 
            elif self == self.DARK_3:
                s *= 0.95 
                v *= 0.7    
            elif self == self.LIGHT_1:
                s *= 0.92   
            elif self == self.LIGHT_2:
                s *= 0.78   
            elif self == self.LIGHT_3:
                s *= 0.65   
        else:
            # 浅色主题：根据颜色类型调整明度和饱和度
            if self == self.DARK_1:
                v *= 0.75 
            elif self == self.DARK_2:
                s *= 1.05 
                v *= 0.5 
            elif self == self.DARK_3:
                s *= 1.1 
                v *= 0.4    
            elif self == self.LIGHT_1:
                v *= 1.05   
            elif self == self.LIGHT_2:
                s *= 0.75   
                v *= 1.05   
            elif self == self.LIGHT_3:
                s *= 0.65   
                v *= 1.05   

        return QColor.fromHsvF(h, min(s, 1), min(v, 1))


def themeColor():
    return ThemeColor.PRIMARY.color()


def setShadowEffect(view, blurRadius=30, offset=(0, 8), color=QColor(0, 0, 0, 30)):
    """ 为对话框添加阴影效果
    blurRadius: 模糊半径
    offset: 阴影偏移量
    color: 阴影颜色
    """
    shadowEffect = QGraphicsDropShadowEffect(view)
    shadowEffect.setBlurRadius(blurRadius)
    shadowEffect.setOffset(*offset)
    shadowEffect.setColor(color)
    view.setGraphicsEffect(None)
    view.setGraphicsEffect(shadowEffect)
