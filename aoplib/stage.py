"""
Stage装饰器
"""
from functools import wraps
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Dict


@dataclass
class StageContext:
    """Stage执行上下文，传递给Feature钩子"""
    stage_name: str                    # Stage名称
    instance: Any                      # 对象实例(self)
    method: Callable                   # 原始方法
    args: tuple                        # 位置参数(不含self)
    kwargs: dict                       # 关键字参数
    result: Any = None                 # 方法返回值(after_stage时有效)
    exception: Optional[Exception] = None  # 异常对象(如有)
    data: Dict[str, Any] = field(default_factory=dict)  # Feature共享数据


def stage(name=None):
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
        stage_name = name if name is not None else func.__qualname__

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 快速路径：没有_features属性时直接执行
            if not hasattr(self, '_features'):
                return func(self, *args, **kwargs)

            features = self._features
            # 构造上下文
            context = StageContext(
                stage_name=stage_name,
                instance=self,
                method=func,
                args=args,
                kwargs=kwargs
            )

            # 调用before_stage钩子
            for feature in features:
                if feature.is_enabled(context):
                    feature.before_stage(context)

            # 执行原方法
            result = func(self, *args, **kwargs)
            context.result = result

            # 调用after_stage钩子
            for feature in features:
                if feature.is_enabled(context):
                    feature.after_stage(context)

            return result

        return wrapper

    # 支持@stage和@stage()两种用法
    if callable(name):
        func = name
        name = None
        return decorator(func)

    return decorator
