"""
aoplib - 动态Joinpoint特性系统

提供AOP拦截器，支持插件化架构
"""
from .joins import JoinMethod, ProceedingJoinPoint, JoinProperty
from .context import JoinMethodContext, JoinPropContext
from .pointcut import with_name, with_tag
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
    'JoinMethod',
    'JoinProperty',
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
    'JoinPropContext',
    'ProceedingJoinPoint',
    'add_aspect',
    'remove_aspect',
    'get_aspect',
    'with_name',
    'with_tag'
]
__version__ = '0.3.0'
