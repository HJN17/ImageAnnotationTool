# coding: utf-8 
from enum import Enum
from PyQt5.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, QPoint, QPointF,pyqtProperty
from PyQt5.QtGui import QMouseEvent, QEnterEvent, QColor
from PyQt5.QtWidgets import QWidget, QLineEdit

from .config import qconfig

class AnimationBase(QObject):
    """ 动画基类 """
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
        parent.installEventFilter(self)

    def _onHover(self, e: QEnterEvent):
        pass  # 鼠标悬停事件处理方法

    def _onLeave(self, e: QEvent):
        pass  # 鼠标离开事件处理方法

    def _onPress(self, e: QMouseEvent):
        pass  # 鼠标按下事件处理方法

    def _onRelease(self, e: QMouseEvent):
        pass  # 鼠标释放事件处理方法

    def eventFilter(self, obj, e: QEvent):
        if obj is self.parent():
            if e.type() == QEvent.MouseButtonPress:
                self._onPress(e)
            elif e.type() == QEvent.MouseButtonRelease: 
                self._onRelease(e)
            elif e.type() == QEvent.Enter:
                self._onHover(e)
            elif e.type() == QEvent.Leave:
                self._onLeave(e)

        return super().eventFilter(obj, e)

class TranslateYAnimation(AnimationBase): 
    """ 垂直平移动画类 """

    def __init__(self, parent: QWidget, offset=2):
        super().__init__(parent)
        self._y = 0
        self.maxOffset = offset
        self.ani = QPropertyAnimation(self, b'y', self) # 创建垂直平移动画对象，目标属性为'y'，目标对象为当前实例self

    @pyqtProperty(float)
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y 
        self.parent().update()
       
    def _onPress(self, e):
        self.ani.setEndValue(self.maxOffset)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)  # 设置缓动曲线为OutQuad（先快后慢）
        self.ani.setDuration(150)
        self.ani.start()

    def _onRelease(self, e):
        """ 释放事件处理方法 """
        self.ani.setEndValue(0)
        self.ani.setDuration(500) 
        self.ani.setEasingCurve(QEasingCurve.OutElastic) # 设置缓动曲线为OutElastic（弹性效果）
        self.ani.start()

class BackgroundAnimation:
    """ 背景动画部件类 """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.isHover = False 
        self.isPressed = False  
        self.bgColorObject = BackgroundColorObject(self)
        self.backgroundColorAni = QPropertyAnimation(self.bgColorObject, b'backgroundColor', self)
        self.backgroundColorAni.setDuration(500)
        self.installEventFilter(self)

        qconfig.themeChanged.connect(self._updateBackgroundColor) 

    def eventFilter(self, obj, e):
        if obj is self:
            if e.type() == QEvent.Type.EnabledChange:  # 若事件为部件启用状态变化事件
                if self.isEnabled():  # 若部件当前已启用
                    self.setBackgroundColor(self._normalBackgroundColor())
                else:
                    self.setBackgroundColor(self._disabledBackgroundColor())

        return super().eventFilter(obj, e) 

    def mousePressEvent(self, e):
        self.isPressed = True
        self._updateBackgroundColor()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        self._updateBackgroundColor()
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self._updateBackgroundColor()

    def leaveEvent(self, e):
        self.isHover = False 
        self._updateBackgroundColor() 

    def focusInEvent(self, e):
        super().focusInEvent(e) 
        self._updateBackgroundColor()

    def _normalBackgroundColor(self):
        return QColor(0, 0, 0, 0)

    def _hoverBackgroundColor(self):
        return self._normalBackgroundColor() 

    def _pressedBackgroundColor(self):
        return self._normalBackgroundColor() 

    def _focusInBackgroundColor(self):
        return self._normalBackgroundColor() 

    def _disabledBackgroundColor(self):
        return self._normalBackgroundColor() 

    def _updateBackgroundColor(self):
        if not self.isEnabled():
            color = self._disabledBackgroundColor()
        elif isinstance(self, QLineEdit) and self.hasFocus():
            color = self._focusInBackgroundColor() 
        elif self.isPressed:
            color = self._pressedBackgroundColor()  
        elif self.isHover: 
            color = self._hoverBackgroundColor()  
        else: 
            color = self._normalBackgroundColor()

        self.backgroundColorAni.stop()
        self.backgroundColorAni.setEndValue(color) 
        self.backgroundColorAni.start()

    def getBackgroundColor(self):
        return self.bgColorObject.backgroundColor

    def setBackgroundColor(self, color: QColor):
        self.bgColorObject.backgroundColor = color 

    @property
    def backgroundColor(self):
        return self.getBackgroundColor() 

class BackgroundColorObject(QObject): 
    """ 背景色对象类 """

    def __init__(self, parent: BackgroundAnimation):
        super().__init__(parent)
        self._backgroundColor = parent._normalBackgroundColor()

    @pyqtProperty(QColor) 
    def backgroundColor(self):
        return self._backgroundColor

    @backgroundColor.setter 
    def backgroundColor(self, color: QColor):
        self._backgroundColor = color 
        self.parent().update()


class FluentAnimationSpeed(Enum):
    FAST = 0       # 快速（短持续时间）
    MEDIUM = 1     # 中等（中等持续时间）
    SLOW = 2       # 慢速（长持续时间）

class FluentAnimationType(Enum): 
    FAST_INVOKE = 0    # 快速唤起（如弹窗快速显示）
    STRONG_INVOKE = 1  # 强调唤起（如重要元素突出显示）
    FAST_DISMISS = 2   # 快速消失（如弹窗快速关闭）
    SOFT_DISMISS = 3   # 柔和消失（如元素平滑退出）
    POINT_TO_POINT = 4 # 点到点移动（如元素位置过渡）
    FADE_IN_OUT = 5    # 淡入淡出（如元素显隐）

class FluentAnimationProperty(Enum):  # Fluent动画属性枚举类（指定动画目标属性）
    POSITION = "position"  # 位置属性（QPoint类型）
    SCALE = "scale"        # 缩放属性（float类型）
    ANGLE = "angle"        # 角度属性（float类型，旋转角度）
    OPACITY = "opacity"    # 透明度属性（float类型，0.0-1.0）

class FluentAnimationProperObject(QObject):  # Fluent动画属性对象基类（管理可动画属性）
    """动画属性对象基类
    管理可动画属性的基类，提供属性值获取和设置的接口。
    
    """
    objects = {} 

    def __init__(self, parent=None):
        super().__init__(parent=parent) 

    def getValue(self):
        return 0  

    def setValue(self):
        pass  

    @classmethod
    def register(cls, name):

        def wrapper(Manager):
            if name not in cls.objects:  
                cls.objects[name] = Manager 

            return Manager 

        return wrapper

    @classmethod
    def create(cls, propertyType: FluentAnimationProperty, parent=None):
        if propertyType not in cls.objects:  
            raise ValueError(f"`{propertyType}` has not been registered") 

        return cls.objects[propertyType](parent)  


@FluentAnimationProperObject.register(FluentAnimationProperty.POSITION) 
class PositionObject(FluentAnimationProperObject): 

    def __init__(self, parent=None):
        super().__init__(parent) 
        self._position = QPoint() 

    def getValue(self):
        return self._position 
    def setValue(self, pos: QPoint):
        self._position = pos 
        self.parent().update() 

    position = pyqtProperty(QPoint, getValue, setValue) 

@FluentAnimationProperObject.register(FluentAnimationProperty.SCALE) 
class ScaleObject(FluentAnimationProperObject):
    """缩放属性对象类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1 

    def getValue(self):
        return self._scale 

    def setValue(self, scale: float):
        self._scale = scale 
        self.parent().update() 

    scale = pyqtProperty(float, getValue, setValue) 

@FluentAnimationProperObject.register(FluentAnimationProperty.ANGLE) 
class AngleObject(FluentAnimationProperObject): 
    """ 角度属性对象类 """

    def __init__(self, parent=None):
        super().__init__(parent) 
        self._angle = 0  # 初始化旋转角度（默认0度）

    def getValue(self):
        return self._angle 

    def setValue(self, angle: float):
        self._angle = angle 
        self.parent().update() 

    angle = pyqtProperty(float, getValue, setValue) 

@FluentAnimationProperObject.register(FluentAnimationProperty.OPACITY) 
class OpacityObject(FluentAnimationProperObject): 
    """ 透明度属性对象类 """

    def __init__(self, parent=None):
        super().__init__(parent) 
        self._opacity = 0 

    def getValue(self):
        return self._opacity 

    def setValue(self, opacity: float):
        self._opacity = opacity 
        self.parent().update() 

    opacity = pyqtProperty(float, getValue, setValue) 


class FluentAnimation(QPropertyAnimation):  

    animations = {} 

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setSpeed(FluentAnimationSpeed.FAST) 
        self.setEasingCurve(self.curve()) 

    @classmethod
    def createBezierCurve(cls, x1, y1, x2, y2):
        curve = QEasingCurve(QEasingCurve.BezierSpline)
        curve.addCubicBezierSegment(QPointF(x1, y1), QPointF(x2, y2), QPointF(1, 1))
        return curve  

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0, 0, 1, 1) 

    def setSpeed(self, speed: FluentAnimationSpeed):
        
        self.setDuration(self.speedToDuration(speed)) 

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 100 

    def startAnimation(self, endValue, startValue=None):
        self.stop() 
        
        if startValue is None:
            self.setStartValue(self.value()) 
        else: 
            self.setStartValue(startValue) 

        self.setEndValue(endValue) 
        self.start() 

    def value(self):
        return self.targetObject().getValue() # 获取当前属性值

    def setValue(self, value):
        self.targetObject().setValue(value) 

    @classmethod
    def register(cls, name):
        
        def wrapper(Manager):
            if name not in cls.animations: 
                cls.animations[name] = Manager  

            return Manager  

        return wrapper 

    @classmethod
    def create(cls, aniType: FluentAnimationType, propertyType: FluentAnimationProperty,
               speed=FluentAnimationSpeed.FAST, value=None, parent=None) -> "FluentAnimation":
        if aniType not in cls.animations:  
            raise ValueError(f"`{aniType}` has not been registered.") 

        obj = FluentAnimationProperObject.create(propertyType, parent)  # 创建属性对象实例
        ani = cls.animations[aniType](parent)  

        ani.setSpeed(speed) 
        ani.setTargetObject(obj)  # 设置动画目标对象为属性对象实例
        ani.setPropertyName(propertyType.value.encode()) 

        if value is not None:
            ani.setValue(value)  # 设置初始值

        return ani 

@FluentAnimation.register(FluentAnimationType.FAST_INVOKE)  
class FastInvokeAnimation(FluentAnimation):

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0, 0, 0, 1) 

    def speedToDuration(self, speed: FluentAnimationSpeed):
        if speed == FluentAnimationSpeed.FAST:  
            return 187 
        if speed == FluentAnimationSpeed.MEDIUM:
            return 333  

        return 500  

@FluentAnimation.register(FluentAnimationType.STRONG_INVOKE) 
class StrongInvokeAnimation(FluentAnimation): 

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0.13, 1.62, 0, 0.92)  

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 667 


@FluentAnimation.register(FluentAnimationType.FAST_DISMISS) 
class FastDismissAnimation(FastInvokeAnimation): 
    """ Fast dismiss animation """


@FluentAnimation.register(FluentAnimationType.SOFT_DISMISS) 
class SoftDismissAnimation(FluentAnimation): 

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(1, 0, 1, 1)  

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 167 


@FluentAnimation.register(FluentAnimationType.POINT_TO_POINT) 
class PointToPointAnimation(FastDismissAnimation): 

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0.55, 0.55, 0, 1) 


@FluentAnimation.register(FluentAnimationType.FADE_IN_OUT) 
class FadeInOutAnimation(FluentAnimation): 

    def speedToDuration(self, speed: FluentAnimationSpeed): # 淡入淡出动画速度到持续时间
        return 500  

