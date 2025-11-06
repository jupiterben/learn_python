"""
aoplib - 动态Joinpoint特性系统

提供AOP拦截器，支持插件化架构
"""
from .joins import join_method, join_property
from .context import JoinMethodContext
from .pointcut import with_name
from .aspect import (
    Aspect,
    aop_class,
    # 方法通知
    before,
    after,
    after_returning,
    after_throwing,
    around,
    # 属性通知
    before_set,
    after_set,
    after_get,
    before_init,
    before_delete,
    after_delete,
    # 管理函数
    add_aspect,
    remove_aspect,
    get_aspect
)

__all__ = [
    'join_method',
    'join_property',
    'Aspect',
    'aop_class',
    # 方法通知
    'before',
    'after',
    'after_returning',
    'after_throwing',
    'around',
    # 属性通知
    'before_set',
    'after_set',
    'after_get',
    'before_init',
    'before_delete',
    'after_delete',
    # 其他
    'JoinMethodContext',
    'add_aspect',
    'remove_aspect',
    'get_aspect',
    'with_name'
]
__version__ = '0.3.0'
