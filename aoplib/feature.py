"""
Feature基类和AOPClass
"""

import enum
from functools import wraps
from typing import Callable, List
from abc import ABC
from fnmatch import fnmatch
from aoplib.context import StageContext, IStageFilter, StageInfo


class StageHookType(enum.Enum):
    BEFORE = "before"
    AFTER = "after"


def convert_to_list(value: str | List[str] | None) -> List[str]:
    """
    将单个字符串或列表转换为列表
    """
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


# Stage特定的方法装饰器
def before_stage(filter: IStageFilter = None) -> Callable:
    """
    装饰器：标记方法为特定stage的before钩子

    参数:
        filter: IStageFilter - stage过滤器，可以是 WithTag(...) 或 WithName(...)

    使用方式:
        class MyFeature(Feature):
            # 无括号用法
            @before_stage
            def handle_all(self, context):
                print("处理所有stage的before逻辑")

            # 指定标签
            @before_stage(WithTag("security"))
            def handle_security(self, context):
                print("处理security标签的before逻辑")

            # 指定名称
            @before_stage(WithName("login", "logout"))
            def handle_auth_before(self, context):
                print("处理认证相关的before逻辑")
    """

    def decorator(func: Callable) -> Callable:
        func._stage_filter = filter if not callable(filter) else None
        func._stage_hook_type = StageHookType.BEFORE
        return func

    # 支持@before_stage和@before_stage(...)两种用法
    if callable(filter):
        # 无括号用法，filter实际上是被装饰的函数
        func = filter
        return decorator(func)

    return decorator


def after_stage(filter: IStageFilter = None) -> Callable:
    """
    装饰器：标记方法为特定stage的after钩子

    参数:
        filter: IStageFilter - stage过滤器，可以是 WithTag(...) 或 WithName(...)

    使用方式:
        class MyFeature(Feature):
            # 无括号用法
            @after_stage
            def handle_all(self, context):
                print("处理所有stage的after逻辑")

            # 指定标签
            @after_stage(WithTag("security"))
            def handle_security(self, context):
                print("处理security标签的after逻辑")

            # 指定名称
            @after_stage(WithName("create", "update"))
            def handle_crud_after(self, context):
                print("处理CRUD操作的after逻辑")
    """

    def decorator(func: Callable) -> Callable:
        func._stage_filter = filter if not callable(filter) else None
        func._stage_hook_type = StageHookType.AFTER
        return func

    # 支持@after_stage和@after_stage(...)两种用法
    if callable(filter):
        # 无括号用法，filter实际上是被装饰的函数
        func = filter
        return decorator(func)

    return decorator


class SFilter(IStageFilter):
    def __init__(
        self, name: str | List[str] = None, tag: str | List[str] = None
    ) -> None:
        self.names = []
        self.patterns = []
        for name in convert_to_list(name):
            if "*" in name or "?" in name:
                self.patterns.append(name)
            else:
                self.names.append(name)
        self.tags = convert_to_list(tag)

    def filter(self, stage_info: StageInfo):
        if stage_info.name in self.names:
            return True
        if stage_info.simple_name in self.names:
            return True
        for pattern in self.patterns:
            if fnmatch(stage_info.name, pattern):
                return True
            if fnmatch(stage_info.simple_name, pattern):
                return True
        if (
            self.tags
            and stage_info.tags
            and any(tag in stage_info.tags for tag in self.tags)
        ):
            return True
        return False


def with_tag(*tags: str) -> IStageFilter:
    return SFilter(tag=list(tags))


def with_name(*names: str) -> IStageFilter:
    return SFilter(name=list(names))


class _StageHookHandlers:
    def __init__(self) -> None:
        self._handlers = []

    def add_handler(self, filter: IStageFilter | None, callable: Callable):
        self._handlers.append((filter, callable))

    def get_handlers(self, stage_info: StageInfo | None):
        handlers = []
        for filter, callable in self._handlers:
            if filter and filter.filter(stage_info):
                handlers.append(callable)
            if not filter:
                handlers.append(callable)
        return handlers


class Feature(ABC):
    """Feature抽象基类，定义拦截钩子接口"""

    def __init__(self, uniq_id: str = None):
        self.uniq_id = uniq_id or self.__class__.__name__
        self.enabled = True

        self._hook_handlers = {}
        self._build_stage_handlers()

    def _build_stage_handlers(self):
        """构建stage名称到处理方法的映射"""
        for name in dir(self):
            if name.startswith("_"):
                continue
            attr = getattr(self, name)
            if callable(attr) and hasattr(attr, "_stage_hook_type"):
                hook_type = attr._stage_hook_type
                filter = attr._stage_filter
                hook_handler = self._hook_handlers.setdefault(
                    hook_type, _StageHookHandlers()
                )
                hook_handler.add_handler(filter, attr)

    def before_stage(self, context: StageContext):
        """在stage执行前调用"""
        hook_handler: _StageHookHandlers = self._hook_handlers.get(StageHookType.BEFORE)
        if hook_handler:
            handlers = hook_handler.get_handlers(context.stage_info)
            for handler in handlers:
                handler(context)

    def after_stage(self, context: StageContext):
        hook_handler: _StageHookHandlers = self._hook_handlers.get(StageHookType.AFTER)
        if hook_handler:
            handlers = hook_handler.get_handlers(context.stage_info)
            for handler in handlers:
                handler(context)

    def enable(self):
        """启用Feature"""
        self.enabled = True

    def disable(self):
        """禁用Feature"""
        self.enabled = False

    def is_enabled(self, context: StageContext):
        """查询Feature是否启用"""
        return True


def add_feature(clsOrInstance, feature: Feature, replace=False):
    """
    将Feature添加到类或实例中

    参数:
        clsOrInstance: 类或实例对象
        feature: 要添加的Feature
        replace: 如果已存在相同uniq_id的Feature，是否替换（默认False）

    返回:
        bool: True表示添加成功，False表示已存在且未替换
    """
    if not hasattr(clsOrInstance, "_features"):
        setattr(clsOrInstance, "_features", [])

    features = clsOrInstance._features

    # 检查是否已存在相同uniq_id的Feature
    for i, existing_feature in enumerate(features):
        if existing_feature.uniq_id == feature.uniq_id:
            if replace:
                # 替换已存在的Feature
                features[i] = feature
                return clsOrInstance
            else:
                # 已存在且不替换
                return clsOrInstance

    # 不存在，直接添加
    features.append(feature)
    return clsOrInstance


def remove_feature(clsOrInstance, feature_or_id: Feature | str):
    """
    从类或实例中移除Feature

    参数:
        clsOrInstance: 类或实例对象
        feature_or_id: Feature对象或uniq_id字符串

    返回:
        bool: True表示移除成功，False表示未找到
    """
    if not hasattr(clsOrInstance, "_features"):
        return clsOrInstance

    features = clsOrInstance._features

    # 确定要移除的uniq_id
    if isinstance(feature_or_id, str):
        target_id = feature_or_id
    elif isinstance(feature_or_id, Feature):
        target_id = feature_or_id.uniq_id
    else:
        return clsOrInstance

    # 查找并移除匹配的Feature
    for i, feature in enumerate(features):
        if feature.uniq_id == target_id:
            features.pop(i)
            return True

    return clsOrInstance


def get_feature(clsOrInstance, feature_id: str) -> Feature | None:
    """
    根据uniq_id获取Feature

    参数:
        clsOrInstance: 类或实例对象
        feature_id: Feature的uniq_id

    返回:
        Feature对象或None
    """
    if not hasattr(clsOrInstance, "_features"):
        return None

    for feature in clsOrInstance._features:
        if feature.uniq_id == feature_id:
            return feature

    return None


def features(*feature_list):
    """
    类装饰器：为类添加features能力

    使用方式:
        # 方式1: 传入Feature实例
        @features(LogFeature(), CacheFeature())
        class MyApp:
            @stage
            def process(self, data):
                return data

        # 方式2: 传入Feature类
        @features(LogFeature, CacheFeature)
        class MyApp:
            pass

        # 方式3: 空装饰器，仅添加Feature管理能力
        @features()
        class MyApp:
            pass
    """

    def decorator(target_cls):
        # 保存原始__init__
        original_init = target_cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            # 初始化Feature列表
            self._features = []
            # 添加Features
            if feature_list:
                for feature in feature_list:
                    # 如果是Feature类，实例化
                    if isinstance(feature, type) and issubclass(feature, Feature):
                        add_feature(self, feature())
                    # 如果已经是Feature实例，直接添加
                    elif isinstance(feature, Feature):
                        add_feature(self, feature)
            # 调用原始__init__
            original_init(self, *args, **kwargs)

        # 替换__init__
        target_cls.__init__ = new_init

        # 添加Feature管理方法
        target_cls.add_feature = lambda self, feature: add_feature(self, feature)
        target_cls.remove_feature = lambda self, feature: remove_feature(self, feature)
        target_cls.get_features = lambda self: list(self._features)
        target_cls.has_feature = lambda self, feature: feature in self._features
        target_cls.clear_features = lambda self: self._features.clear()
        target_cls.get_feature = lambda self, feature_id: get_feature(self, feature_id)

        return target_cls

    # 支持@features和@features()两种用法
    if (
        feature_list
        and isinstance(feature_list[0], type)
        and not issubclass(feature_list[0], Feature)
    ):
        # @features 无括号用法，第一个参数是被装饰的类
        target_cls = feature_list[0]
        return decorator(target_cls)

    return decorator
