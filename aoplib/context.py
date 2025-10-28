"""
Stage执行上下文
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Dict


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

