# coding: utf-8
from functools import singledispatch, update_wrapper

class singledispatchmethod:
    """
    单分派泛型方法描述符类
    
    该类用于创建单分派泛型方法，根据参数的类型动态选择不同的实现方法。
    它基于Python标准库的functools.singledispatch实现，支持方法重载。
    
    属性：
        dispatcher (singledispatch): 单分派泛型方法调度器，用于根据参数类型选择实现方法
        func (callable): 原始函数，作为默认实现方法
    """


    def __init__(self, func):
        if not callable(func) and not hasattr(func, "__get__"):
            raise TypeError(f"{func!r} is not callable or a descriptor")
        
        self.dispatcher = singledispatch(func)

        self.func = func

    
    def register(self, cls, method=None):
        # 调用调度器的register方法，注册类型cls和对应的实现方法method
        return self.dispatcher.register(cls, func=method)

    def __get__(self, obj, cls=None):
        def _method(*args, **kwargs):
            if args:
                method = self.dispatcher.dispatch(args[0].__class__)
            else:
                method = self.func
                for v in kwargs.values():
                    if v.__class__ in self.dispatcher.registry:
                        method = self.dispatcher.dispatch(v.__class__)
                        if method is not self.func:
                            break

            return method.__get__(obj, cls)(*args, **kwargs)

        _method.__isabstractmethod__ = self.__isabstractmethod__
        _method.register = self.register
        update_wrapper(_method, self.func)
        return _method

    @property
    def __isabstractmethod__(self):
        """获取原始函数的抽象方法标志"""
        return getattr(self.func, '__isabstractmethod__', False)
