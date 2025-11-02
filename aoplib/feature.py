"""
Feature基类和AOPClass
"""
import enum
from functools import wraps
from typing import Callable, List
from abc import ABC
from fnmatch import fnmatch
from aoplib.context import StageContext, StageInfo

class StageHookType(enum):
    BEFORE = 'before'
    AFTER = 'after'

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


def before_stage(names: str | List[str] = None, tags: str | List[str] = None) -> Callable:
    """
    装饰器：标记方法为特定stage的before钩子

    参数:
        stage_name: str 或 List[str] - 单个stage名称或stage名称列表
        支持通配符: * 匹配任意字符, ? 匹配单个字符

    使用方式:
        class MyFeature(Feature):
            @before_stage("process")
            def handle_process_before(self, context):
                print("处理process的before逻辑")

            @before_stage(["login", "logout"])
            def handle_auth_before(self, context):
                print("处理认证相关的before逻辑")

            @before_stage("process_*")
            def handle_all_process(self, context):
                print("处理所有process_开头的stage")
    """
    def decorator(func: Callable) -> Callable:
        # 统一转换为列表
        func._stage_names = convert_to_list(names)
        func._stage_tags = convert_to_list(tags)
        func._stage_hook_type = StageHookType.BEFORE
        return func
    return decorator


def after_stage(names: str | List[str] = None, tags: str | List[str] = None) -> Callable:
    """
    装饰器：标记方法为特定stage的after钩子

    参数:
        stage_name: str 或 List[str] - 单个stage名称或stage名称列表
        支持通配符: * 匹配任意字符, ? 匹配单个字符

    使用方式:
        class MyFeature(Feature):
            @after_stage("process")
            def handle_process_after(self, context):
                print("处理process的after逻辑")

            @after_stage(["create", "update", "delete"])
            def handle_crud_after(self, context):
                print("处理CRUD操作的after逻辑")

            @after_stage("*_data")
            def handle_all_data(self, context):
                print("处理所有_data结尾的stage")
    """
    def decorator(func: Callable) -> Callable:
        # 统一转换为列表
        func._stage_names = convert_to_list(names)
        func._stage_tags = convert_to_list(tags)
        func._stage_hook_type = StageHookType.AFTER
        return func
    return decorator


class _StageHookHandlers:
    def __init__(self) -> None:
        self.name_handlers = {}
        self.pattern_handlers = []
        self.tag_handlers = {}

    def add_handler(self, stage_name: str,  stage_tags: List[str], call):
        pass

    def get_handler(self, stage_info:StageInfo):
        # 1. 先尝试精确匹配
        # handler = self.name_handlers.get(stage_name)
        # if handler:
        #     return handler
        # handler = self.name_handlers.get(simple_name)
        # if handler:
        #     return handler
        # # 2. 通配符匹配
        # for pattern, handler in self.pattern_handlers:
        #     if fnmatch(stage_name, pattern):
        #         return handler
        # # 3. 标签匹配
        # handler = self.tag_handlers.get('*')
        return None


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
            if name.startswith('_'):
                continue
            attr = getattr(self, name)
            if callable(attr) and hasattr(attr, '_stage_hook_type'):
                hook_type = attr._stage_hook_type
                hook_handlers = self._hook_handlers.setdefault(
                    hook_type, _StageHookHandlers())
                hook_handlers.add_handler(
                    attr._stage_names, attr._stage_tags, attr)

    def before_stage(self, context: StageContext):
        """在stage执行前调用"""
        # 1. 先尝试精确匹配
        handler = self._before_handlers.get(context.stage_name)
        if handler:
            handler(context)
            return

        handler = self._before_handlers.get(context.stage_simple_name)
        if handler:
            handler(context)
            return

        # 2. 再尝试通配符匹配
        for pattern, handler in self._before_patterns:
            if fnmatch(context.stage_name, pattern):
                handler(context)
                return

        # 3. 再尝试tag匹配
        for tag, handlers in self._before_tag_handlers.items():
            if tag in context.stage_tags:
                for handler in handlers:
                    handler(context)

    def after_stage(self, context: StageContext):
        simple_name = context.stage_name.split('.')[-1]
        """在stage执行后调用"""
        # 1. 先尝试精确匹配
        handler = self._after_handlers.get(context.stage_name)
        if handler:
            handler(context)
            return

        handler = self._after_handlers.get(simple_name)
        if handler:
            handler(context)
            return

        # 2. 再尝试通配符匹配
        for pattern, handler in self._after_patterns:
            if fnmatch(context.stage_name, pattern):
                handler(context)
                return

        # 3. 再尝试tag匹配
        for tag, handlers in self._after_tag_handlers.items():
            if tag in context.stage_tags:
                for handler in handlers:
                    handler(context)

    def enable(self):
        """启用Feature"""
        self.enabled = True

    def disable(self):
        """禁用Feature"""
        self.enabled = False

    def filter(self, stage_name: str, stage_tags: List[str]):
        """过滤Feature"""
        return True

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
    if not hasattr(clsOrInstance, '_features'):
        setattr(clsOrInstance, '_features', [])

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
    if not hasattr(clsOrInstance, '_features'):
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
    if not hasattr(clsOrInstance, '_features'):
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
        target_cls.add_feature = lambda self, feature: add_feature(
            self, feature)
        target_cls.remove_feature = lambda self, feature: remove_feature(
            self, feature)
        target_cls.get_features = lambda self: list(self._features)
        target_cls.has_feature = lambda self, feature: feature in self._features
        target_cls.clear_features = lambda self: self._features.clear()
        target_cls.get_feature = lambda self, feature_id: get_feature(
            self, feature_id)

        return target_cls

    return decorator
