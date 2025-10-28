"""
Feature基类和AOPClass
"""
from typing import Any
from abc import ABC
from functools import wraps


class Feature(ABC):
    """Feature抽象基类，定义拦截钩子接口"""

    def __init__(self):
        self.enabled = True

    def before_stage(self, context):
        """在stage执行前调用，可选重写"""
        pass

    def after_stage(self, context):
        """在stage执行后调用，可选重写"""
        pass

    def enable(self):
        """启用Feature"""
        self.enabled = True

    def disable(self):
        """禁用Feature"""
        self.enabled = False

    def is_enabled(self):
        """查询Feature是否启用"""
        return self.enabled


def aop_class(cls):
    """
    类装饰器：为类添加AOP能力，不需要继承AOPClass

    使用方式:
        @aop_class
        class MyApp:
            @stage
            def process(self, data):
                return data
    """
    # 保存原始__init__
    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        # 初始化Feature列表
        self._features = []
        # 调用原始__init__
        original_init(self, *args, **kwargs)

    # 替换__init__
    cls.__init__ = new_init

    # 添加Feature管理方法
    cls.add_feature = lambda self, feature: _add_feature(self, feature)
    cls.remove_feature = lambda self, feature: _remove_feature(self, feature)
    cls.get_features = lambda self: list(self._features)
    cls.has_feature = lambda self, feature: feature in self._features
    cls.clear_features = lambda self: self._features.clear()

    return cls


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
