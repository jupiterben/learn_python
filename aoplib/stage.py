"""
Stage装饰器
"""

from abc import ABC
from functools import wraps
from typing import List, Optional
from aoplib.context import StageContext, StageInfo
from aoplib.feature import Feature


def stage(*tags):
    """
    标记方法为stage，启用Feature拦截

    参数:
        name: stage名称，默认使用方法名

    示例:
        @stage
        def process(self, data):
            return data

        @stage("处理阶段")
        def process(self, data):
            return data
    """

    def decorator(func):
        stage_name = func.__qualname__
        stage_info = StageInfo(
            name=stage_name,
            tags=list(tags) or [],
            simple_name=stage_name.split(".")[-1],
        )

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            all_features: List[Feature] = []

            # 收集实例级别的features
            if hasattr(self, "_features"):
                instance_features = getattr(self, "_features")
                if isinstance(instance_features, list):
                    all_features.extend(instance_features)

            features = [f for f in all_features if f.enabled]
            if not features:
                return func(self, *args, **kwargs)

            # 构造上下文
            context = StageContext(
                stage_info=stage_info,
                instance=self,
                method=func,
                args=args,
                kwargs=kwargs,
            )

            # 调用before_stage钩子
            for feature in features:
                if feature.is_enabled(context):
                    feature.before_stage(context)

            # 执行原方法
            result = func(self, *args, **kwargs)
            context.result = result

            # 调用after_stage钩子
            for feature in reversed(features):
                if feature.is_enabled(context):
                    feature.after_stage(context)

            return result

        return wrapper

    # 支持@stage和@stage()两种用法
    if tags and callable(tags[0]):
        func = tags[0]
        tags = tags[1:]
        return decorator(func)

    return decorator
