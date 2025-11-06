"""
Aspect基类和AOPClass
"""

import enum
from functools import wraps
from typing import Callable, Dict, List
from abc import ABC
from .pointcut import IJoinFilter
from .context import JoinContext


class AdviceType(enum.Enum):
    Before = "before_method"
    After = "after_method"
    AfterReturning = "after_method_returning"
    AfterThrowing = "after_method_throwing"
    Around = "around_method"

    BeforeSet = "before_property_set"
    AfterSet = "after_property_set"
    AfterGet = "after_property_get"
    BeforeInit = "before_property_init"
    BeforeDelete = "before_property_delete"
    AfterDelete = "after_property_delete"


def _make_advice_decorator(advice_type: AdviceType) -> Callable:
    """工厂函数：生成advice装饰器，消除重复代码"""

    def decorator(filter: IJoinFilter = None) -> Callable:
        def inner_decorator(func: Callable) -> Callable:
            func._pointcut = filter if not callable(filter) else None
            func._advice_type = advice_type
            return func

        # 支持@decorator和@decorator(...)两种用法
        if callable(filter):
            # 无括号用法，filter实际上是被装饰的函数
            return inner_decorator(filter)

        return inner_decorator

    return decorator


# 使用工厂函数生成所有装饰器
# 方法通知
before = _make_advice_decorator(AdviceType.Before)
after = _make_advice_decorator(AdviceType.After)
after_returning = _make_advice_decorator(AdviceType.AfterReturning)
after_throwing = _make_advice_decorator(AdviceType.AfterThrowing)
around = _make_advice_decorator(AdviceType.Around)

# 属性通知
before_set = _make_advice_decorator(AdviceType.BeforeSet)
after_set = _make_advice_decorator(AdviceType.AfterSet)
after_get = _make_advice_decorator(AdviceType.AfterGet)
before_init = _make_advice_decorator(AdviceType.BeforeInit)
before_delete = _make_advice_decorator(AdviceType.BeforeDelete)
after_delete = _make_advice_decorator(AdviceType.AfterDelete)


class _PointHookHandlers:
    def __init__(self) -> None:
        self._handlers = []

    def add_handler(self, filter: IJoinFilter | None, handler: Callable):
        self._handlers.append((filter, handler))

    def get_handlers(self, context: JoinContext):
        for filter_obj, handler in self._handlers:
            if filter_obj is not None:
                if filter_obj.filter(context.method, context.meta):
                    yield handler
            else:
                yield handler


class Aspect(ABC):
    """Aspect抽象基类，定义拦截钩子接口"""

    def __init__(self, uniq_id: str = None):
        self.uniq_id = uniq_id or self.__class__.__name__
        self.enabled = True

        self._hook_handlers: Dict[AdviceType, _PointHookHandlers] = {}
        self._build_point_handlers()

    def _build_point_handlers(self):
        """构建point名称到处理方法的映射"""
        # 用集合记录已处理的方法名，避免重复添加
        processed = set()
        # 遍历类及其父类的所有属性（性能优化：避免使用dir()）
        for cls in type(self).__mro__:
            for name, attr in cls.__dict__.items():
                if name.startswith("_") or name in processed:
                    continue
                # 绑定方法到实例
                bound_attr = getattr(self, name, None)
                if (
                    bound_attr
                    and callable(bound_attr)
                    and hasattr(bound_attr, "_advice_type")
                ):
                    hook_type = bound_attr._advice_type
                    filter_obj = bound_attr._pointcut
                    hook_handler = self._hook_handlers.setdefault(
                        hook_type, _PointHookHandlers()
                    )
                    hook_handler.add_handler(filter_obj, bound_attr)
                    processed.add(name)

    def get_handlers(self, adType: AdviceType, context: JoinContext):
        hook_handler = self._hook_handlers.get(adType)
        if hook_handler:
            yield from hook_handler.get_handlers(context)

    def enable(self):
        """启用Aspect"""
        self.enabled = True

    def disable(self):
        """禁用Aspect"""
        self.enabled = False


def add_aspect(clsOrInstance, aspect: Aspect, replace=False):
    """
    将Aspect添加到类或实例中

    参数:
        clsOrInstance: 类或实例对象
        aspect: 要添加的Aspect
        replace: 如果已存在相同uniq_id的Aspect，是否替换（默认False）

    返回:
        bool: True表示添加成功，False表示已存在且未替换
    """
    if not hasattr(clsOrInstance, "_aspects"):
        setattr(clsOrInstance, "_aspects", [])

    aspects = clsOrInstance._aspects

    # 检查是否已存在相同uniq_id的Aspect
    for i, existing_aspect in enumerate(aspects):
        if existing_aspect.uniq_id == aspect.uniq_id:
            if replace:
                # 替换已存在的Aspect
                aspects[i] = aspect
                return clsOrInstance
            else:
                # 已存在且不替换
                return clsOrInstance

    # 不存在，直接添加
    aspects.append(aspect)
    return clsOrInstance


def remove_aspect(clsOrInstance, aspect_or_id: Aspect | str):
    """
    从类或实例中移除Aspect

    参数:
        clsOrInstance: 类或实例对象
        aspect_or_id: Aspect对象或uniq_id字符串

    返回:
        clsOrInstance: 返回对象本身，支持链式调用
    """
    if not hasattr(clsOrInstance, "_aspects"):
        return clsOrInstance

    aspects = clsOrInstance._aspects

    # 确定要移除的uniq_id
    if isinstance(aspect_or_id, str):
        target_id = aspect_or_id
    elif isinstance(aspect_or_id, Aspect):
        target_id = aspect_or_id.uniq_id

    # 查找并移除匹配的Aspect
    for i, aspect in enumerate(aspects):
        if aspect.uniq_id == target_id:
            aspects.pop(i)
            break

    return clsOrInstance


def get_aspect(clsOrInstance, aspect_id: str) -> Aspect | None:
    """
    根据uniq_id获取Aspect

    参数:
        clsOrInstance: 类或实例对象
        aspect_id: Aspect的uniq_id

    返回:
        Aspect对象或None
    """
    if not hasattr(clsOrInstance, "_aspects"):
        return None

    for aspect in clsOrInstance._aspects:
        if aspect.uniq_id == aspect_id:
            return aspect

    return None


def aop_class(*aspects):
    """
    类装饰器：为类添加aspects能力

    使用方式:
        # 方式1: 传入Aspect实例
        @aspects(LogAspect(), CacheAspect())
        class MyApp:
            @joinpoint
            def process(self, data):
                return data

        # 方式2: 传入Aspect类
        @aspects(LogAspect, CacheAspect)
        class MyApp:
            pass

        # 方式3: 空装饰器，仅添加Aspect管理能力
        @aspects()
        class MyApp:
            pass
    """

    def decorator(target_cls):
        # 保存原始__init__
        original_init = target_cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            # 初始化Aspect列表
            self._aspects = []
            # 添加Aspects
            if aspects:
                for aspect in aspects:
                    # 如果是Aspect类，实例化
                    if isinstance(aspect, type) and issubclass(aspect, Aspect):
                        add_aspect(self, aspect())
                    # 如果已经是Aspect实例，直接添加
                    elif isinstance(aspect, Aspect):
                        add_aspect(self, aspect)
            # 调用原始__init__
            original_init(self, *args, **kwargs)

        # 替换__init__
        target_cls.__init__ = new_init

        # 添加Aspect管理方法
        target_cls.add_aspect = lambda self, aspect: add_aspect(self, aspect)
        target_cls.remove_aspect = lambda self, aspect: remove_aspect(self, aspect)
        target_cls.get_aspects = lambda self: list(self._aspects)
        target_cls.has_aspect = lambda self, aspect: aspect in self._aspects
        target_cls.clear_aspects = lambda self: self._aspects.clear()
        target_cls.get_aspect = lambda self, aspect_id: get_aspect(self, aspect_id)

        return target_cls

    # 支持@aspects和@aspects()两种用法
    if aspects and isinstance(aspects[0], type) and not issubclass(aspects[0], Aspect):
        # @aspects 无括号用法，第一个参数是被装饰的类
        target_cls = aspects[0]
        return decorator(target_cls)

    return decorator


def get_enable_aspects(obj):
    """
    获取当前实例启用的aspects
    """
    all_aspects: List[Aspect] = []

    # 收集实例级别的aspects
    if hasattr(obj, "_aspects"):
        instance_aspects = getattr(obj, "_aspects")
        if isinstance(instance_aspects, list):
            all_aspects.extend(instance_aspects)

    return [f for f in all_aspects if f.enabled]
