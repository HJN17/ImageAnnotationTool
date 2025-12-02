# coding:utf-8
from enum import Enum 
from typing import Union 
import json 

from PyQt5.QtXml import QDomDocument
from PyQt5.QtCore import QRectF, Qt, QFile, QObject, QRect
from PyQt5.QtGui import (QIcon, QIconEngine, QColor, QPixmap, QImage, QPainter,QFontDatabase, QFont, QPainterPath)
from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtSvg import QSvgRenderer

from .config import isDarkTheme, Theme
from .overload import singledispatchmethod

class FluentIconEngine(QIconEngine):
    """ 自定义Fluent风格图标引擎，支持主题自适应和图标主题反转 """

    def __init__(self, icon, reverse=False):
       
        super().__init__() 
        self.icon = icon
        self.isThemeReversed = reverse  # 存储主题反转状态

    def paint(self, painter, rect, mode, state):
        
        painter.save() 

        if mode == QIcon.Disabled: 
            painter.setOpacity(0.5)
        elif mode == QIcon.Selected: 
            painter.setOpacity(0.7)

        if not self.isThemeReversed:
            theme = Theme.AUTO 
        else:
            theme = Theme.LIGHT if isDarkTheme() else Theme.DARK

        icon = self.icon
        if isinstance(self.icon, Icon):
            icon = self.icon.fluentIcon.icon(theme)
        elif isinstance(self.icon, FluentIconBase): 
            icon = self.icon.icon(theme) 

        if rect.x() == 19:
            rect = rect.adjusted(-1, 0, 0, 0)  

        icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal, state)
        painter.restore()  

    def clone(self) -> QIconEngine:
        return FluentIconEngine(self.icon, self.isThemeReversed)  # 返回新的引擎实例

    def pixmap(self, size, mode, state):
        
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)  
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)  

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height()) 
        self.paint(painter, rect, mode, state)
        return pixmap  

class SvgIconEngine(QIconEngine):
    """ SVG图标引擎（用于渲染SVG格式图标） """

    def __init__(self, svg: str):
        super().__init__()
        self.svg = svg

    def paint(self, painter, rect, mode, state):
        drawSvgIcon(self.svg.encode(), painter, rect)  # 编码为bytes后绘制

    def clone(self) -> QIconEngine:
        """ 创建引擎副本 """
        return SvgIconEngine(self.svg)

    def pixmap(self, size, mode, state):
        """ 生成SVG图标像素图（逻辑与FluentIconEngine类似） """
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height())
        self.paint(painter, rect, mode, state)
        return pixmap


def getIconColor(theme=Theme.AUTO, reverse=False):

    if not reverse:
        lc, dc = "black", "white"
    else:
        lc, dc = "white", "black"

    if theme == Theme.AUTO:
        color = dc if isDarkTheme() else lc 
    else:
        color = dc if theme == Theme.DARK else lc 

    return color


def drawSvgIcon(icon, painter, rect):
    renderer = QSvgRenderer(icon) # 创建SVG渲染器
    renderer.render(painter, QRectF(rect)) # 渲染图标到指定矩形区域


def writeSvg(iconPath: str, indexes=None, **attributes):
    """ 修改SVG图标属性并返回修改后的SVG代码    """

    if not iconPath.lower().endswith('.svg'):
        return ""
  
    f = QFile(iconPath)
    f.open(QFile.ReadOnly)
    dom = QDomDocument()
    dom.setContent(f.readAll()) 
    f.close() 

    pathNodes = dom.elementsByTagName('path') 
    indexes = range(pathNodes.length()) if not indexes else indexes
    for i in indexes:
        element = pathNodes.at(i).toElement() 
        for k, v in attributes.items(): 
            element.setAttribute(k, v)

    return dom.toString() 


def drawIcon(icon, painter, rect, state=QIcon.Off, **attributes):
    """ 统一绘制图标（支持多种图标类型）"""
    if isinstance(icon, FluentIconBase): 
        icon.render(painter, rect, **attributes)
    elif isinstance(icon, Icon): 
        icon.fluentIcon.render(painter, rect, **attributes)
    else:
        icon = QIcon(icon)
        icon.paint(painter, QRectF(rect).toRect(), Qt.AlignCenter, state=state)


class FluentIconBase:
    """ Fluent图标基类（定义Fluent风格图标的基本接口） """
    
    def path(self, theme=Theme.AUTO) -> str:
        raise NotImplementedError

    def icon(self, theme=Theme.AUTO, color: QColor = None) -> QIcon:

        path = self.path(theme) 

        if not (path.endswith('.svg') and color):
            return QIcon(self.path(theme))

        color = QColor(color).name() # 转换颜色为十六进制字符串（如"#FF0000"）
        return QIcon(SvgIconEngine(writeSvg(path, fill=color)))
    
    
    def qicon(self, reverse=False) -> QIcon:
       
        return QIcon(FluentIconEngine(self, reverse))

    def render(self, painter, rect, theme=Theme.AUTO, indexes=None, **attributes):

        """
        直接渲染图标到指定区域  """

        icon = self.path(theme)

        if icon.endswith('.svg'): 
            if attributes:
                icon = writeSvg(icon, indexes, **attributes).encode()
            drawSvgIcon(icon, painter, rect)
        else:  
            icon = QIcon(icon)
            rect = QRectF(rect).toRect()
            painter.drawPixmap(rect, icon.pixmap(rect.size()))

class FluentIcon(FluentIconBase, Enum):
    """ Fluent图标枚举（定义所有可用的Fluent风格图标） """

    UP = "Up"
    ADD = "Add"
    BUS = "Bus"
    CAR = "Car"
    CUT = "Cut"
    IOT = "IOT"
    PIN = "Pin"
    TAG = "Tag"
    VPN = "VPN"
    CAFE = "Cafe"
    CHAT = "Chat"
    COPY = "Copy"
    CODE = "Code"
    DOWN = "Down"
    EDIT = "Edit"
    FLAG = "Flag"
    FONT = "Font"
    GAME = "Game"
    HELP = "Help"
    HIDE = "Hide"
    HOME = "Home"
    INFO = "Info"
    LEAF = "Leaf"
    LINK = "Link"
    MAIL = "Mail"
    MENU = "Menu"
    MUTE = "Mute"
    MORE = "More"
    MOVE = "Move"
    PLAY = "Play"
    SAVE = "Save"
    SEND = "Send"
    SYNC = "Sync"
    UNIT = "Unit"
    VIEW = "View"
    WIFI = "Wifi"
    ZOOM = "Zoom"
    ALBUM = "Album"
    BRUSH = "Brush"
    BROOM = "Broom"
    CLOSE = "Close"
    CLOUD = "Cloud"
    EMBED = "Embed"
    GLOBE = "Globe"
    HEART = "Heart"
    LABEL = "Label"
    MEDIA = "Media"
    MOVIE = "Movie"
    MUSIC = "Music"
    ROBOT = "Robot"
    PAUSE = "Pause"
    PASTE = "Paste"
    PHOTO = "Photo"
    PHONE = "Phone"
    PRINT = "Print"
    SHARE = "Share"
    TILES = "Tiles"
    UNPIN = "Unpin"
    VIDEO = "Video"
    TRAIN = "Train"
    ADD_TO  ="AddTo"
    ACCEPT = "Accept"
    CAMERA = "Camera"
    CANCEL = "Cancel"
    DELETE = "Delete"
    FOLDER = "Folder"
    FILTER = "Filter"
    MARKET = "Market"
    SCROLL = "Scroll"
    LAYOUT = "Layout"
    GITHUB = "GitHub"
    UPDATE = "Update"
    REMOVE = "Remove"
    RETURN = "Return"
    PEOPLE = "People"
    QRCODE = "QRCode"
    RINGER = "Ringer"
    ROTATE = "Rotate"
    SEARCH = "Search"
    VOLUME = "Volume"
    FRIGID  = "Frigid"
    SAVE_AS = "SaveAs"
    ZOOM_IN = "ZoomIn"
    CONNECT  ="Connect"
    HISTORY = "History"
    SETTING = "Setting"
    PALETTE = "Palette"
    MESSAGE = "Message"
    FIT_PAGE = "FitPage"
    ZOOM_OUT = "ZoomOut"
    AIRPLANE = "Airplane"
    ASTERISK = "Asterisk"
    CALORIES = "Calories"
    CALENDAR = "Calendar"
    FEEDBACK = "Feedback"
    LIBRARY = "BookShelf"
    MINIMIZE = "Minimize"
    CHECKBOX = "CheckBox"
    DOCUMENT = "Document"
    LANGUAGE = "Language"
    DOWNLOAD = "Download"
    QUESTION = "Question"
    SPEAKERS = "Speakers"
    DATE_TIME = "DateTime"
    FONT_SIZE = "FontSize"
    HOME_FILL = "HomeFill"
    PAGE_LEFT = "PageLeft"
    SAVE_COPY = "SaveCopy"
    SEND_FILL = "SendFill"
    SKIP_BACK = "SkipBack"
    SPEED_OFF = "SpeedOff"
    ALIGNMENT = "Alignment"
    BLUETOOTH = "Bluetooth"
    COMPLETED = "Completed"
    CONSTRACT = "Constract"
    HEADPHONE = "Headphone"
    MEGAPHONE = "Megaphone"
    PROJECTOR = "Projector"
    EDUCATION = "Education"
    LEFT_ARROW = "LeftArrow"
    ERASE_TOOL = "EraseTool"
    PAGE_RIGHT = "PageRight"
    PLAY_SOLID = "PlaySolid"
    BOOK_SHELF = "BookShelf"
    HIGHTLIGHT = "Highlight"
    FOLDER_ADD = "FolderAdd"
    PAUSE_BOLD = "PauseBold"
    PENCIL_INK = "PencilInk"
    PIE_SINGLE = "PieSingle"
    QUICK_NOTE = "QuickNote"
    SPEED_HIGH = "SpeedHigh"
    STOP_WATCH = "StopWatch"
    ZIP_FOLDER = "ZipFolder"
    BASKETBALL = "Basketball"
    BRIGHTNESS = "Brightness"
    DICTIONARY = "Dictionary"
    MICROPHONE = "Microphone"
    ARROW_DOWN = "ChevronDown"
    FULL_SCREEN = "FullScreen"
    MIX_VOLUMES = "MixVolumes"
    REMOVE_FROM = "RemoveFrom"
    RIGHT_ARROW = "RightArrow"
    QUIET_HOURS  ="QuietHours"
    FINGERPRINT = "Fingerprint"
    APPLICATION = "Application"
    CERTIFICATE = "Certificate"
    TRANSPARENT = "Transparent"
    IMAGE_EXPORT = "ImageExport"
    SPEED_MEDIUM = "SpeedMedium"
    LIBRARY_FILL = "LibraryFill"
    MUSIC_FOLDER = "MusicFolder"
    POWER_BUTTON = "PowerButton"
    SKIP_FORWARD = "SkipForward"
    CARE_UP_SOLID = "CareUpSolid"
    ACCEPT_MEDIUM = "AcceptMedium"
    CANCEL_MEDIUM = "CancelMedium"
    CHEVRON_RIGHT = "ChevronRight"
    CLIPPING_TOOL = "ClippingTool"
    SEARCH_MIRROR = "SearchMirror"
    SHOPPING_CART = "ShoppingCart"
    FONT_INCREASE = "FontIncrease"
    BACK_TO_WINDOW = "BackToWindow"
    COMMAND_PROMPT = "CommandPrompt"
    CLOUD_DOWNLOAD = "CloudDownload"
    DICTIONARY_ADD = "DictionaryAdd"
    CARE_DOWN_SOLID = "CareDownSolid"
    CARE_LEFT_SOLID = "CareLeftSolid"
    CLEAR_SELECTION = "ClearSelection"
    DEVELOPER_TOOLS = "DeveloperTools"
    BACKGROUND_FILL = "BackgroundColor"
    CARE_RIGHT_SOLID = "CareRightSolid"
    CHEVRON_DOWN_MED = "ChevronDownMed"
    CHEVRON_RIGHT_MED = "ChevronRightMed"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"
    EXPRESSIVE_INPUT_ENTRY = "ExpressiveInputEntry"

    def path(self, theme=Theme.AUTO) -> str:

        color = getIconColor(theme)

        return f':/resource/images/icons/{self.value}_{color}.svg'
    
    

class Icon(QIcon):
    """ 图标包装类（将FluentIcon转换为QIcon，并支持主题同步） """

    def __init__(self, fluentIcon: FluentIcon):
        """
        Parameters
        ----------
        fluentIcon: FluentIcon
            Fluent图标枚举成员
        """
        super().__init__(fluentIcon.qicon())  # 使用FluentIcon的qicon()方法创建QIcon
        self.fluentIcon = fluentIcon  # 存储原始FluentIcon


def toQIcon(icon: Union[QIcon, FluentIconBase, str]) -> QIcon:
    """ 将图标转换为QIcon（统一图标类型）"""
    if isinstance(icon, str):
        return QIcon(icon) 
    elif isinstance(icon, FluentIconBase):
        return icon.qicon() 
    return icon 


class Action(QAction):
    """ 支持Fluent图标的QAction（动作项） """

    @singledispatchmethod
    def __init__(self, parent: QObject = None, **kwargs):
        """ 多构造函数：无文本无图标 """
        super().__init__(parent, **kwargs)
        self.fluentIcon = None 

    @__init__.register
    def _(self, text: str, parent: QObject = None, **kwargs):
        """ 多构造函数：带文本 """
        super().__init__(text, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QObject = None, **kwargs):
        """ 多构造函数：带QIcon和文本 """
        super().__init__(icon, text, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QObject = None, **kwargs):
        """ 多构造函数：带Fluent图标和文本 """
        super().__init__(icon.icon(), text, parent, **kwargs)
        self.fluentIcon = icon

    @__init__.register
    def _(self, icon: QIcon, parent: QObject = None, **kwargs):
        """ 多构造函数：带QIcon """
        super().__init__(icon, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: FluentIconBase, parent: QObject = None, **kwargs):
        """ 多构造函数：带Fluent图标 """
        super().__init__(icon.icon(), parent, **kwargs) 
        self.fluentIcon = icon 


    def icon(self) -> QIcon:
        """ 重写icon方法，返回Fluent图标（主题同步） """
        if self.fluentIcon:
            return Icon(self.fluentIcon)
        return super().icon() 

    def setIcon(self, icon: Union[FluentIconBase, QIcon]):
        """ 设置图标（支持Fluent图标或QIcon） """
        if isinstance(icon, FluentIconBase):
            self.fluentIcon = icon
            icon = icon.icon() 
        super().setIcon(icon) 