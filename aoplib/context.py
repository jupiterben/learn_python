from dataclasses import dataclass
from typing import Any, Callable, Optional


# @dataclass
# class JoinInfo:
#     name: str
#     simple_name: str
#     meta: dict
@dataclass
class JoinContext:
    method: Callable  # 原始方法
    meta: dict  # JoinPoint信息
    instance: Any  # 对象实例(self)


@dataclass
class JoinMethodContext(JoinContext):
    """Stage执行上下文，传递给Feature钩子"""
    args: tuple  # 位置参数(不含self)
    kwargs: dict  # 关键字参数
    result: Any = None  # 方法返回值()
    exception: Optional[Exception] = None  # 异常对象(如有)
    suppressed: bool = False  # 异常是否被抑制（不再传播）

    @property
    def name(self):
        return self.method.__qualname__

    @property
    def short_name(self):
        return self.meta.get("name") or self.method.__name__

    def suppress_exception(self):
        """标记异常已处理，不再向外传播"""
        self.suppressed = True

    def replace_exception(self, new_exception: Exception):
        """替换当前异常"""
        self.exception = new_exception
        self.suppressed = False


@dataclass
class JoinPropContext(JoinContext):
    """Stage执行上下文，传递给Feature钩子"""
    value: Any = None
