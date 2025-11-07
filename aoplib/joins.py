"""
Joinpoint装饰器
"""

from .context import JoinPropContext
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, List
from .context import JoinMethodContext
from .aspect import AdviceType, Aspect, get_enable_aspects
from types import MethodType

# 方法相关


class ProceedingJoinPoint(ABC):
    def __init__(self, context: JoinMethodContext):
        self.context = context

    @abstractmethod
    def proceed(self, *args, **kwargs):
        pass


class ProceedingHandler(ProceedingJoinPoint):
    def __init__(
        self, handler: Callable, pjp: ProceedingJoinPoint, context: JoinMethodContext
    ):
        super().__init__(context)
        self.pjp = pjp
        self.handler = handler

    def proceed(self):
        return self.handler(self.pjp)


class ProceedingMethod(ProceedingJoinPoint):
    def __init__(self, context: JoinMethodContext):
        super().__init__(context)
        self.context = context

    def proceed(self):
        return self.context.method(
            self.context.instance, *self.context.args, **self.context.kwargs
        )


def _handler_iter(aspects: List[Aspect], type: AdviceType, context: JoinMethodContext):
    for aspect in aspects:
        yield from aspect.get_handlers(type, context)


class JoinMethod:
    """
    类版本的 join_method，类似 Python 内置的 property

    支持两种用法：
    1. 装饰器方式：@join_method
    2. 类方式：name = JoinMethod(func, **meta)
    """

    def __init__(self, func: Callable = None, **meta):
        """
        参数:
            func: 被装饰的方法
            **meta: 额外的元数据
        """
        self.func = func
        self.meta = meta
        self.name = None  # 将在 __set_name__ 中设置

    def __call__(self, func: Callable = None, **meta) -> Any:
        """
        装饰器支持，允许 @JoinMethod 或 @JoinMethod(**meta) 的用法
        
        用法1: @JoinMethod
        用法2: @JoinMethod(tags=["important"])
        """
        # 合并 self.meta 和传入的 meta（传入的优先级更高）
        merged_meta = {**self.meta, **meta}
        
        if func is not None and callable(func):
            # 实例被调用：instance(func)，func 是被装饰的函数
            instance = type(self)(func=func, **merged_meta)
            instance.name = func.__name__
            return instance
        else:
            # 有括号用法：@JoinMethod(**meta) 返回的实例再次被调用
            # 返回一个装饰器函数
            def decorator(f: Callable) -> 'JoinMethod':
                instance = type(self)(func=f, **merged_meta)
                instance.name = f.__name__
                return instance
            return decorator

    def __set_name__(self, owner, name):
        """设置方法名称"""
        self.name = name

    def __get__(self, instance, owner=None):
        """描述符协议：返回包装后的方法"""
        if instance is None:
            return self

        # 创建包装函数并绑定到实例
        return self._create_wrapper(instance)

    def _create_wrapper(self, instance):
        """创建包装函数并绑定到实例"""
        func = self.func
        meta = self.meta

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            aspects = get_enable_aspects(self)
            if not aspects:
                return func(self, *args, **kwargs)

            # 构造上下文
            context = JoinMethodContext(
                meta=meta,
                instance=self,
                method=func,
                args=args,
                kwargs=kwargs,
            )

            # 调用 Before 钩子
            for handler in _handler_iter(aspects, AdviceType.Before, context):
                handler(context)

            # 执行原方法
            has_exception = False
            try:
                # 调用 Around 钩子
                pjp = ProceedingMethod(context)
                for handler in _handler_iter(aspects, AdviceType.Around, context):
                    pjp = ProceedingHandler(handler, pjp, context)
                context.return_value = pjp.proceed()

            except Exception as e:
                has_exception = True
                context.exception = e
                # 调用 AfterThrowing 钩子
                for handler in _handler_iter(
                    aspects, AdviceType.AfterThrowing, context
                ):
                    handler(context)
                # 如果异常被抑制，不再抛出
                if not context.suppressed:
                    # 可能已被替换
                    raise context.exception

            # 成功时调用 AfterReturning 钩子
            if not has_exception:
                for handler in _handler_iter(
                    aspects, AdviceType.AfterReturning, context
                ):
                    handler(context)

            # 最后调用 After 钩子（无论成功或失败，类似 finally）
            for handler in _handler_iter(aspects, AdviceType.After, context):
                handler(context)

            return context.return_value

        # 绑定到实例，使其成为方法
        return MethodType(wrapper, instance)



# 属性相关的 AOP 钩子
def _apply_hooks(
    instance,
    advice_type: AdviceType,
    context: JoinPropContext,
    return_value=False,
    reversed_order=False
):
    """
    应用属性相关的 AOP 钩子

    参数:
        instance: 实例对象
        advice_type: 通知类型
        context: 属性上下文
        return_value: 如果为True，handler的返回值会更新context.value
        reversed_order: 如果为True，按相反顺序遍历aspects
    """
    aspects = get_enable_aspects(instance)
    if reversed_order:
        aspects = list(reversed(aspects))

    for aspect in aspects:
        for handler in aspect.get_handlers(advice_type, context):
            if return_value:
                # handler 返回新值，更新 context.value
                context.value = handler(context)
            else:
                # handler 只执行副作用，不返回值
                handler(context)
    return context.value if return_value else None


class JoinProperty:
    """
    类版本的 join_property，类似 Python 内置的 property

    支持两种用法：
    1. 装饰器方式：@join_property
    2. 类方式：name = JoinProperty(fget=..., fset=..., fdel=..., default=...)
    """
    def __call__(self, fget: Callable = None, **meta) -> Any:
        """
        装饰器支持，允许 @JoinProperty 或 @JoinProperty(**meta) 的用法
        
        用法1: @JoinProperty
        用法2: @JoinProperty(default=value, tags=["tag"])
        """
        # 合并 self.meta 和传入的 meta（传入的优先级更高）
        merged_meta = {**self.meta, **meta}
        
        if fget is not None and callable(fget):
            # 实例被调用：instance(func)，fget 是被装饰的函数
            return type(self)(fget=fget, fset=self.fset, fdel=self.fdel,
                            doc=self.__doc__, default=self.default, **merged_meta)
        else:
            # 有括号用法：@JoinProperty(**meta) 返回的实例再次被调用
            # 返回一个装饰器函数
            def decorator(func: Callable) -> 'JoinProperty':
                return type(self)(fget=func, fset=self.fset, fdel=self.fdel,
                                doc=self.__doc__, default=self.default, **merged_meta)
            return decorator

    def __init__(
        self,
        fget: Callable = None,
        fset: Callable = None,
        fdel: Callable = None,
        doc: str = None,
        default: Any = None,
        **meta
    ):
        """
        参数:
            fget: getter 函数
            fset: setter 函数
            fdel: deleter 函数
            doc: 文档字符串
            default: 默认值
            **meta: 额外的元数据
        """
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.__doc__ = doc or (fget.__doc__ if fget else None)
        self.default = default
        self.meta = meta
        self.name = None  # 将在 __set_name__ 中设置

    def __set_name__(self, owner, name):
        """设置属性名称"""
        self.name = name
        self.private_attr = f"_{name}"

    def _init_value(self, instance):
        """初始化属性值"""
        if hasattr(instance, self.private_attr):
            return

        context = JoinPropContext(
            meta=self.meta,
            instance=instance,
            method=self.fget or (lambda: None)
        )
        context.value = self.default

        # 应用 BeforeInit 钩子
        _apply_hooks(instance, AdviceType.BeforeInit,
                     context, return_value=True)

        setattr(instance, self.private_attr, context.value)

    def __get__(self, instance, owner=None):
        """描述符协议：获取属性值"""
        if instance is None:
            return self

        # 初始化（如果需要）
        self._init_value(instance)

        context = JoinPropContext(
            meta=self.meta,
            instance=instance,
            method=self.fget or (lambda: None)
        )

        # 获取原始值
        if self.fget:
            context.value = self.fget(instance)
        else:
            context.value = getattr(instance, self.private_attr)

        # 应用 AfterGet 钩子（返回值会被更新）
        _apply_hooks(instance, AdviceType.AfterGet, context, return_value=True)

        return context.value

    def __set__(self, instance, value):
        """描述符协议：设置属性值"""
        # 如果没有 setter，抛出异常（只读属性）
        if self.fset is None:
            raise AttributeError("can't set attribute")

        context = JoinPropContext(
            meta=self.meta,
            instance=instance,
            method=self.fset or (lambda v: None),
            value=value
        )

        # 初始化（如果需要）
        self._init_value(instance)

        # 应用 BeforeSet 钩子
        _apply_hooks(instance, AdviceType.BeforeSet, context)

        # 检查是否跳过设置
        if context.skip_set:
            return

        # 执行实际的设置
        if self.fset:
            self.fset(instance, value)
        else:
            # 如果没有自定义 setter，使用默认的私有属性存储
            setattr(instance, self.private_attr, value)

        # 应用 AfterSet 钩子（反向顺序）
        _apply_hooks(instance, AdviceType.AfterSet,
                     context, reversed_order=True)

    def __delete__(self, instance):
        """描述符协议：删除属性值"""
        if not hasattr(instance, self.private_attr):
            return

        context = JoinPropContext(
            meta=self.meta,
            instance=instance,
            method=self.fdel or (lambda: None)
        )

        # 应用 BeforeDelete 钩子
        _apply_hooks(instance, AdviceType.BeforeDelete, context)

        # 检查是否跳过删除
        if context.skip_delete:
            return

        # 执行实际的删除
        if self.fdel:
            self.fdel(instance)
        else:
            delattr(instance, self.private_attr)

        # 应用 AfterDelete 钩子（反向顺序）
        _apply_hooks(instance, AdviceType.AfterDelete,
                     context, reversed_order=True)

    def getter(self, fget: Callable):
        """设置 getter，支持链式调用"""
        return type(self)(fget=fget, fset=self.fset, fdel=self.fdel,
                          doc=self.__doc__, default=self.default, **self.meta)

    def setter(self, fset: Callable):
        """设置 setter，支持链式调用"""
        return type(self)(fget=self.fget, fset=fset, fdel=self.fdel,
                          doc=self.__doc__, default=self.default, **self.meta)

    def deleter(self, fdel: Callable):
        """设置 deleter，支持链式调用"""
        return type(self)(fget=self.fget, fset=self.fset, fdel=fdel,
                          doc=self.__doc__, default=self.default, **self.meta)
