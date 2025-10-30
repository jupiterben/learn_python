"""
Feature基类和AOPClass
"""
from typing import Callable
from abc import ABC
from functools import wraps
from fnmatch import fnmatch
from aoplib.stage import StageContext


# Stage特定的方法装饰器
def before_stage(stage_name) -> Callable:
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
        if isinstance(stage_name, str):
            func._stage_names = [stage_name]
        else:
            func._stage_names = list(stage_name)
        func._hook_type = 'before'
        return func
    return decorator


def after_stage(stage_name) -> Callable:
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
        if isinstance(stage_name, str):
            func._stage_names = [stage_name]
        else:
            func._stage_names = list(stage_name)
        func._hook_type = 'after'
        return func
    return decorator


class Feature(ABC):
    """Feature抽象基类，定义拦截钩子接口"""

    def __init__(self):
        self.enabled = True
        self.match_tags = []
        # 精确匹配的handler映射
        self._before_handlers = {}
        self._after_handlers = {}
        # 通配符模式的handler列表 [(pattern, handler), ...]
        self._before_patterns = []
        self._after_patterns = []
        self._build_stage_handlers()

    def _build_stage_handlers(self):
        """构建stage名称到处理方法的映射"""
        for name in dir(self):
            if name.startswith('_'):
                continue
            attr = getattr(self, name)
            if callable(attr) and hasattr(attr, '_stage_names'):
                stage_names = attr._stage_names
                hook_type = attr._hook_type
                # 将同一个方法注册到多个stage
                for stage_name in stage_names:
                    # 检查是否是通配符模式
                    is_pattern = '*' in stage_name or '?' in stage_name

                    if hook_type == 'before':
                        if is_pattern:
                            self._before_patterns.append((stage_name, attr))
                        else:
                            self._before_handlers[stage_name] = attr
                    elif hook_type == 'after':
                        if is_pattern:
                            self._after_patterns.append((stage_name, attr))
                        else:
                            self._after_handlers[stage_name] = attr

    def before_stage(self, context: StageContext):
        """在stage执行前调用"""
        # 1. 先尝试精确匹配
        handler = self._before_handlers.get(context.stage_name)
        if handler:
            handler(context)
            return

        # 2. 再尝试通配符匹配
        for pattern, handler in self._before_patterns:
            if fnmatch(context.stage_name, pattern):
                handler(context)
                return

    def after_stage(self, context: StageContext):
        """在stage执行后调用"""
        # 1. 先尝试精确匹配
        handler = self._after_handlers.get(context.stage_name)
        if handler:
            handler(context)
            return

        # 2. 再尝试通配符匹配
        for pattern, handler in self._after_patterns:
            if fnmatch(context.stage_name, pattern):
                handler(context)
                return

    def enable(self):
        """启用Feature"""
        self.enabled = True

    def disable(self):
        """禁用Feature"""
        self.enabled = False

    def filter(self, context: StageContext):
        """过滤Feature"""
        if not self.enabled:
            return False
        if self.match_tags:
            for tag in self.match_tags:
                if tag in context.stage_tags:
                    return False
        return True

    def is_enabled(self, context: StageContext):
        """查询Feature是否启用"""
        return True


def aop_class(cls=None, features=None):
    """
    类装饰器：为类添加AOP能力，不需要继承AOPClass

    使用方式:
        # 方式1: 不带参数
        @aop_class
        class MyApp:
            @stage
            def process(self, data):
                return data

        # 方式2: 带features列表
        @aop_class(features=[LogFeature(), CacheFeature()])
        class MyApp:
            @stage
            def process(self, data):
                return data
    """
    def decorator(target_cls):
        # 保存原始__init__
        original_init = target_cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            # 初始化Feature列表
            self._features = []
            # 添加Features
            if features:
                for feature in features:
                    # 如果是Feature类，实例化
                    if isinstance(feature, type) and issubclass(feature, Feature):
                        _add_feature(self, feature())
                    # 如果已经是Feature实例，直接添加
                    elif isinstance(feature, Feature):
                        _add_feature(self, feature)
            # 调用原始__init__
            original_init(self, *args, **kwargs)

        # 替换__init__
        target_cls.__init__ = new_init

        # 添加Feature管理方法
        target_cls.add_feature = lambda self, feature: _add_feature(
            self, feature)
        target_cls.remove_feature = lambda self, feature: _remove_feature(
            self, feature)
        target_cls.get_features = lambda self: list(self._features)
        target_cls.has_feature = lambda self, feature: feature in self._features
        target_cls.clear_features = lambda self: self._features.clear()

        return target_cls

    # 支持 @aop_class 和 @aop_class(features=[...]) 两种用法
    if cls is not None:
        # @aop_class 直接装饰类
        return decorator(cls)
    else:
        # @aop_class(features=[...]) 带参数
        return decorator


# 辅助方法
def _add_feature(self, feature):
    """添加Feature"""
    if feature in self._features:
        raise ValueError(f"Feature {feature} already registered")
    self._features.append(feature)
    return self


def _remove_feature(self, feature):
    """移除Feature"""
    try:
        self._features.remove(feature)
    except ValueError:
        pass
    return self
