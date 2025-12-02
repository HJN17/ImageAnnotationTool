# coding:utf-8
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRegExp
from PyQt5.QtGui import QBrush, QColor, QPixmap,QPainter, QPen, QIntValidator, QRegExpValidator
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QFrame, QVBoxLayout
from ...common.style_sheet import FluentStyleSheet, isDarkTheme,setShadowEffect
from ..widgets import ClickableSlider, SingleDirectionScrollArea, PrimaryPushButton
from ..widgets.line_edit import LineEdit

from .mask_dialog_base import MaskDialogBase


class HuePanel(QWidget):
    """ 色相面板组件
    
    用于可视化选择颜色的色相(Hue)和饱和度(Saturation)，通过鼠标点击和拖动调整。
    面板显示色相-饱和度二维平面，纵轴表示饱和度(0-255)，横轴表示色相(0-360°)。
    
    信号:
        colorChanged: 当选择的颜色发生变化时发射，携带当前QColor对象
    """
    colorChanged = pyqtSignal(QColor)

    def __init__(self, color=QColor(255, 0, 0), parent=None):
        """ 初始化色相面板
        
        参数:
            color: QColor，初始颜色，默认为红色(255,0,0)
            parent: QWidget，父部件，默认为None
        """
        super().__init__(parent=parent)
        self.setFixedSize(256, 256)  # 设置面板固定尺寸为256x256像素
        # 加载色相面板背景图（资源路径通过Qt资源系统访问）
        self.huePixmap = QPixmap(":/resource/images/color_dialog/HuePanel.png")
        self.setColor(color)  # 初始化颜色

    def mousePressEvent(self, e):
      
        self.setPickerPosition(e.pos())

    def mouseMoveEvent(self, e):
        
        self.setPickerPosition(e.pos()) 

    def setPickerPosition(self, pos):
        """ 设置选择器位置并更新颜色
        
        根据鼠标位置计算色相和饱和度，更新当前颜色并发射信号。
        
        参数:
            pos: QPoint，鼠标在面板上的位置（相对于面板左上角）
        """
        self.pickerPos = pos  # 保存选择器位置
        # 计算色相：x坐标归一化到[0,1]后乘以360°（色相范围0-360）
        hue = int(max(0, min(1, pos.x() / self.width())) * 360)
        # 计算饱和度：y坐标归一化到[0,1]后反转（面板底部为0，顶部为255）再乘以255
        saturation = int(max(0, min(1, (self.height() - pos.y()) / self.height())) * 255)
        self.color.setHsv(hue, saturation, 255)  # 设置颜色的HSV值（明度固定为255）
        self.update()  # 触发重绘
        self.colorChanged.emit(self.color)  # 发射颜色变化信号

    def setColor(self, color):
        """ 设置面板当前颜色
        
        根据输入颜色更新选择器位置，并刷新面板显示。
        
        参数:
            color: QColor，要设置的初始颜色
        """
        self.color = QColor(color)  # 保存颜色副本
        # 固定明度为255（色相面板仅调整色相和饱和度）
        self.color.setHsv(self.color.hue(), self.color.saturation(), 255)
        # 计算选择器初始位置：根据色相和饱和度反推坐标
        self.pickerPos = QPoint(
            int(self.hue / 360 * self.width()),  # 色相对应的x坐标
            int((255 - self.saturation) / 255 * self.height())  # 饱和度对应的y坐标（反转）
        )
        self.update()  # 触发重绘

    @property
    def hue(self):
        """ 获取当前色相值（0-360） """
        return self.color.hue()

    @property
    def saturation(self):
        """ 获取当前饱和度值（0-255） """
        return self.color.saturation()

    def paintEvent(self, e):
        """ 重绘事件处理
        
        绘制色相面板背景和选择器（圆形指示器）。
        
        参数:
            e: QPaintEvent，绘图事件对象
        """
        painter = QPainter(self)
        # 设置渲染提示：抗锯齿和平滑像素图变换（提升绘制质量）
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)


        # 绘制色相面板背景
        painter.setBrush(QBrush(self.huePixmap))  # 使用色相面板图片作为画刷
        painter.setPen(QPen(QColor(0, 0, 0, 15), 2.4))  # 黑色半透明边框（透明度15，宽度2.4）
        painter.drawRoundedRect(self.rect(), 5.6, 5.6)  # 绘制圆角矩形面板（圆角半径5.6）

        # 绘制选择器（圆形指示器）
        # 根据饱和度和色相选择指示器颜色（确保与背景对比度）
        if self.saturation > 153 or (40 < self.hue < 180):
            color = Qt.black  # 高饱和度或黄绿区域使用黑色指示器
        else:
            color = QColor(255, 253, 254)  # 低饱和度或红蓝区域使用白色指示器

        painter.setPen(QPen(color, 3))  # 指示器边框（颜色为上述计算结果，宽度3）
        painter.setBrush(Qt.NoBrush)  # 无填充（空心圆）
        # 绘制圆形指示器：中心为pickerPos，半径8（直径16）
        painter.drawEllipse(self.pickerPos.x() - 8, self.pickerPos.y() - 8, 16, 16)

class BrightnessSlider(ClickableSlider):
    """ 亮度滑块组件
    
    用于调整颜色的亮度（明度），继承自可点击滑块，支持通过滑块位置控制亮度值。
    
    信号:
        colorChanged: 当亮度变化时发射，携带当前QColor对象
    """

    colorChanged = pyqtSignal(QColor)  # 亮度变化信号，参数为当前颜色

    def __init__(self, color, parent=None):
        """ 初始化亮度滑块
        
        参数:
            color: QColor，初始颜色（用于提取初始亮度）
            parent: QWidget，父部件，默认为None
        """
        super().__init__(Qt.Horizontal, parent=parent)  # 水平方向滑块
        self.setRange(0, 255)  # 亮度范围0-255
        self.setSingleStep(1)  # 步长为1
        self.setColor(color)  # 初始化颜色
        # 连接滑块值变化信号到内部处理函数
        self.valueChanged.connect(self.__onValueChanged)

    def setColor(self, color):
        """ 设置滑块关联的颜色
        
        根据颜色更新滑块位置，并重新应用样式（滑块背景色随颜色变化）。
        
        参数:
            color: QColor，要关联的颜色
        """
        self.color = QColor(color)  # 保存颜色副本
        self.setValue(self.color.value())  # 设置滑块值为当前颜色的亮度（明度）
        # 动态修改QSS样式：替换滑块的色相和饱和度变量
        qss = FluentStyleSheet.COLOR_DIALOG.content()
        qss = qss.replace('--slider-hue', str(self.color.hue()))  # 色相变量
        qss = qss.replace('--slider-saturation', str(self.color.saturation()))  # 饱和度变量
        self.setStyleSheet(qss)

    def __onValueChanged(self, value):
        """ 滑块值变化处理函数
        
        当滑块值变化时，更新颜色的亮度，并发射颜色变化信号。
        
        参数:
            value: int，滑块当前值（0-255），对应亮度值
        """
        # 保持色相和饱和度不变，仅更新亮度（value）和透明度（alpha）
        self.color.setHsv(self.color.hue(), self.color.saturation(), value, self.color.alpha())
        self.setColor(self.color)  # 更新滑块样式（依赖当前颜色）
        self.colorChanged.emit(self.color)  # 发射颜色变化信号

class ColorCard(QWidget):
    """ 颜色卡片组件
    
    用于预览颜色（如当前选择颜色和原始颜色对比），支持透明度预览（通过棋盘格背景）。
    """

    def __init__(self, color, parent=None):
        """ 初始化颜色卡片"""
        super().__init__(parent=parent)
        self.setFixedSize(35, 118)  # 固定尺寸：宽44px，高128px
        self.setColor(color)  # 设置初始颜色
        self.titledPixmap = self._createTitledBackground()  # 创建棋盘格背景图


    def _createTitledBackground(self):
        """ 创建透明度预览的棋盘格背景图
        
        返回:
            QPixmap，8x8像素的棋盘格图片（用于透明度预览）
        """
        pixmap = QPixmap(8, 8)  # 创建8x8的像素图
        pixmap.fill(Qt.transparent)  # 透明背景
        painter = QPainter(pixmap)

        # 根据当前主题模式确定棋盘格颜色（深色主题用白色，浅色用黑色，透明度26）
        c = 255 if isDarkTheme() else 0
        color = QColor(c, c, c, 26)
        # 绘制2x2的棋盘格（左上角和右下角为透明，其余为上述颜色）
        painter.fillRect(4, 0, 4, 4, color)
        painter.fillRect(0, 4, 4, 4, color)
        painter.end()
        return pixmap

    def setColor(self, color):
        """ 设置卡片显示的颜色
        
        参数:
            color: QColor，要显示的颜色
        """
        self.color = QColor(color)  # 保存颜色副本
        self.update()  # 触发重绘

    def paintEvent(self, e):
        """ 重绘事件处理
        
        绘制颜色卡片，若启用透明度则先绘制棋盘格背景。
        
        参数:
            e: QPaintEvent，绘图事件对象
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)  # 抗锯齿

        painter.setBrush(self.color)  # 使用当前颜色作为画刷
        painter.setPen(QColor(0, 0, 0, 13))  # 黑色边框（透明度13）
        painter.drawRoundedRect(self.rect(), 4, 4)  # 圆角矩形（半径4px）

class ColorLineEdit(LineEdit):
    """ 颜色通道输入框
    
    用于输入颜色通道值（如RGB的红、绿、蓝通道），仅允许输入0-255的整数。
    
    信号:
        valueChanged: 当输入值合法时发射，携带输入的字符串值
    """

    valueChanged = pyqtSignal(str)  # 输入值变化信号（仅在合法时发射）


    def __init__(self, value, parent=None):
        """ 初始化颜色通道输入框
        
        参数:
            value: int，初始值（0-255）
            parent: QWidget，父部件，默认为None
        """
        super().__init__(parent=parent)
        self.setText(str(value))  # 设置初始文本
        self.setFixedSize(136, 33)  # 固定尺寸：宽136px，高33px
        self.setClearButtonEnabled(True)  # 启用清除按钮
        self.setValidator(QIntValidator(0, 255, self))  # 仅允许0-255的整数输入


        self.textEdited.connect(self._onTextEdited) # 连接文本编辑信号到内部处理函数

    def _onTextEdited(self, text):
        """ 文本编辑处理函数
        
        当文本编辑完成且验证通过时，发射valueChanged信号。
        
        参数:
            text: str，编辑后的文本
        """
        # 验证输入文本是否合法（0-255的整数）
        state = self.validator().validate(text, 0)[0]
        if state == QIntValidator.Acceptable:  # 输入合法
            self.valueChanged.emit(text)  # 发射信号

class HexColorLineEdit(ColorLineEdit):
    """ 十六进制颜色输入框"""
    
    def __init__(self, color, parent=None):
    
        self.colorFormat = QColor.HexRgb # 颜色格式：HexRgb（6位）

        # 调用父类构造函数：初始值为颜色的十六进制字符串（去除前缀'#'）
        super().__init__(QColor(color).name(self.colorFormat)[1:], parent)

        self.setValidator(QRegExpValidator(QRegExp(r'[A-Fa-f0-9]{6}'))) # 正则验证器：6位十六进制字符

        # 设置文本边距（右侧预留33px用于显示'#'前缀）
        self.setTextMargins(4, 0, 33, 0)
        # 创建'#'前缀标签
        self.prefixLabel = QLabel('#', self)
        self.prefixLabel.move(7, 2)  # 定位到输入框左侧（x=7, y=2）
        self.prefixLabel.setObjectName('prefixLabel')  # 设置对象名（用于QSS样式）



    def setColor(self, color):
        """ 设置输入框的颜色值"""
        # 生成十六进制字符串（去除前缀'#'）并设置到输入框
        self.setText(color.name(self.colorFormat)[1:])


"""
Displayable Components  """

class ColorDialog(MaskDialogBase):
    """ 颜色选择对话框"""

    colorChanged = pyqtSignal(QColor)  # 颜色选择完成信号

    def __init__(self, color, title: str, parent=None):
        """ 初始化颜色选择对话框
        
        参数:
            color: QColor | GlobalColor | str，初始颜色（支持QColor、全局颜色或颜色字符串）
            title: str，对话框标题
            parent: QWidget，父部件，默认为None
        """
        super().__init__(parent)
       
        color = QColor(color)
        color.setAlpha(255)

        self.oldColor = QColor(color)  # 保存原始颜色（用于取消时恢复）
        self.color = QColor(color)  # 当前选择的颜色

        # 创建滚动区域（用于内容超出时滚动）
        self.scrollArea = SingleDirectionScrollArea(self.widget)
        self.scrollWidget = QWidget(self.scrollArea)  # 滚动区域的内容部件


        # 创建按钮组（确定/取消按钮）
        self.buttonGroup = QFrame(self.widget)
        self.yesButton = PrimaryPushButton('确定', self.buttonGroup)  # 确定按钮
        self.cancelButton = QPushButton('取消', self.buttonGroup)  # 取消按钮

        # 创建界面元素
        self.titleLabel = QLabel(title, self.scrollWidget)  # 标题标签
        self.huePanel = HuePanel(color, self.scrollWidget)  # 色相面板
        self.newColorCard = ColorCard(color, self.scrollWidget)  # 新颜色预览卡片
        self.oldColorCard = ColorCard(color, self.scrollWidget)  # 原始颜色预览卡片
        self.brightSlider = BrightnessSlider(color, self.scrollWidget)  # 亮度滑块


        # 创建颜色编辑区域的标签和输入框
        self.editLabel = QLabel('编辑颜色', self.scrollWidget)  # "编辑颜色"标签
        self.redLabel = QLabel('红色', self.scrollWidget)  # "红色"标签
        self.blueLabel = QLabel('蓝色', self.scrollWidget)  # "蓝色"标签
        self.greenLabel = QLabel('绿色', self.scrollWidget)  # "绿色"标签
        self.hexLineEdit = HexColorLineEdit(color, self.scrollWidget)  # 十六进制输入框
        self.redLineEdit = ColorLineEdit(self.color.red(), self.scrollWidget)  # 红色通道输入框
        self.greenLineEdit = ColorLineEdit(self.color.green(), self.scrollWidget)  # 绿色通道输入框
        self.blueLineEdit = ColorLineEdit(self.color.blue(), self.scrollWidget)  # 蓝色通道输入框

        self.vBoxLayout = QVBoxLayout(self.widget)  # 主布局（对话框内容区域）

        self.__initWidget() # 初始化界面布局和信号连接

    def __initWidget(self):
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        self.scrollArea.setViewportMargins(48, 24, 0, 24)  # 视口边距：左48，上24，下24
        self.scrollArea.setWidget(self.scrollWidget)  # 设置滚动内容部件

        # 设置对话框尺寸（根据是否启用透明度调整高度）
        self.widget.setMaximumSize(458, 696)
        self.widget.resize(458, 696)
        self.scrollWidget.resize(410, 560)

        self.buttonGroup.setFixedSize(456, 81)
        self.yesButton.setFixedWidth(192) 
        self.cancelButton.setFixedWidth(192)

        self.__setQss()  # 应用样式
        self.__initLayout()  # 初始化控件布局
        self.__connectSignalToSlot()  # 连接信号与槽函数

    def __initLayout(self):
        """ 初始化控件位置布局 """
        # 定位各控件（通过绝对坐标定位，因未使用布局管理器）
        self.huePanel.move(0, 46)  # 色相面板位置
        self.newColorCard.move(278, 51)  # 新颜色卡片位置
        self.oldColorCard.move(278, self.newColorCard.geometry().bottom() + 6)  # 原始颜色卡片位置
        self.brightSlider.move(0, 324)  # 亮度滑块位置

        self.editLabel.move(0, 385)  # "编辑颜色"标签位置
        self.redLineEdit.move(0, 426)  # 红色输入框位置
        self.greenLineEdit.move(0, 470)  # 绿色输入框位置
        self.blueLineEdit.move(0, 515)  # 蓝色输入框位置
        self.redLabel.move(144, 434)  # "红色"标签位置
        self.greenLabel.move(144, 478)  # "绿色"标签位置
        self.blueLabel.move(144, 524)  # "蓝色"标签位置
        self.hexLineEdit.move(196, 381)  # 十六进制输入框位置
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.scrollArea, 1)
        self.vBoxLayout.addWidget(self.buttonGroup, 0, Qt.AlignBottom)

        self.yesButton.move(24, 25)
        self.cancelButton.move(self.yesButton.geometry().right() + 24, 25)

    def __setQss(self):
        """ 设置控件样式 """
        # 设置对象名（用于QSS选择器）
        self.editLabel.setObjectName('editLabel')
        self.titleLabel.setObjectName('titleLabel')
        self.yesButton.setObjectName('yesButton')
        self.cancelButton.setObjectName('cancelButton')
        self.buttonGroup.setObjectName('buttonGroup')
        FluentStyleSheet.COLOR_DIALOG.apply(self)  # 应用颜色对话框样式表
        self.titleLabel.adjustSize()  # 调整标题标签尺寸（适应文本）
        self.editLabel.adjustSize()  # 调整"编辑颜色"标签尺寸

    def setColor(self, color, movePicker=True):
        """ 设置对话框当前颜色，并更新所有相关控件
        
        参数:
            color: QColor，要设置的颜色
            movePicker: bool，是否移动色相面板的选择器，默认为True
        """
        self.color = QColor(color)
        self.brightSlider.setColor(color)  # 更新亮度滑块
        self.newColorCard.setColor(color)  # 更新新颜色卡片
        self.hexLineEdit.setColor(color)  # 更新十六进制输入框
        self.redLineEdit.setText(str(color.red()))  # 更新红色通道输入框
        self.blueLineEdit.setText(str(color.blue()))  # 更新蓝色通道输入框
        self.greenLineEdit.setText(str(color.green()))  # 更新绿色通道输入框
        if movePicker:
            self.huePanel.setColor(color)  # 移动色相面板选择器

    def __onHueChanged(self, color):
        """ 色相变化处理槽函数"""
        self.color.setHsv(color.hue(), color.saturation(), self.color.value(), self.color.alpha())
        self.setColor(self.color) 

    def __onBrightnessChanged(self, color):
        """ 亮度变化处理槽函数"""
        self.color.setHsv(self.color.hue(), self.color.saturation(), color.value(), self.color.alpha())
        self.setColor(self.color, False)

    def __onRedChanged(self, red):
        """ 红色通道变化处理槽函数 """
        self.color.setRed(int(red)) 
        self.setColor(self.color)

    def __onBlueChanged(self, blue):
        """ 蓝色通道变化处理槽函数 """
        self.color.setBlue(int(blue)) 
        self.setColor(self.color)

    def __onGreenChanged(self, green):
        """ 绿色通道变化处理槽函数 """
        self.color.setGreen(int(green)) 
        self.setColor(self.color)

    def __onHexColorChanged(self, color):
        """ 十六进制颜色变化处理槽函数"""
        self.color.setNamedColor("#" + color)
        self.setColor(self.color)

    def __onYesButtonClicked(self):
        """ 确定按钮点击槽函数 """
        self.accept()
        if self.color != self.oldColor:
            self.colorChanged.emit(self.color)

    def updateStyle(self):
        """ 更新样式（主题切换时调用） """
        self.setStyle(QApplication.style())  # 重新应用样式
        self.titleLabel.adjustSize()
        self.editLabel.adjustSize()
        self.redLabel.adjustSize()
        self.greenLabel.adjustSize()
        self.blueLabel.adjustSize()

    def showEvent(self, e):
        """ 显示事件处理"""
        self.updateStyle()
        super().showEvent(e)

    def __connectSignalToSlot(self):
        """ 连接信号与槽函数 """
        # 按钮信号
        self.cancelButton.clicked.connect(self.reject)  # 取消按钮：关闭对话框
        self.yesButton.clicked.connect(self.__onYesButtonClicked)  # 确定按钮：处理颜色变化

        # 色相面板和亮度滑块信号
        self.huePanel.colorChanged.connect(self.__onHueChanged)  # 色相变化
        self.brightSlider.colorChanged.connect(self.__onBrightnessChanged)  # 亮度变化

        # 颜色通道输入框信号
        self.redLineEdit.valueChanged.connect(self.__onRedChanged)  # 红色通道变化
        self.blueLineEdit.valueChanged.connect(self.__onBlueChanged)  # 蓝色通道变化
        self.greenLineEdit.valueChanged.connect(self.__onGreenChanged)  # 绿色通道变化
        self.hexLineEdit.valueChanged.connect(self.__onHexColorChanged)  # 十六进制颜色变化
