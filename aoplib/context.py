from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Dict, List


@dataclass
class StageInfo:
    name: str
    simple_name: str
    tags: List[str]


@dataclass
class StageContext:
    """Stage执行上下文，传递给Feature钩子"""

    stage_info: StageInfo  # Stage名称
    instance: Any  # 对象实例(self)
    method: Callable  # 原始方法
    args: tuple  # 位置参数(不含self)
    kwargs: dict  # 关键字参数
    result: Any = None  # 方法返回值(after_stage时有效)
    exception: Optional[Exception] = None  # 异常对象(如有)
    data: Dict[str, Any] = field(default_factory=dict)  # Feature共享数据


class IStageFilter(ABC):
    @abstractmethod
    def filter(self, stage_info: StageInfo):
        pass
