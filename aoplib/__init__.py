"""
aoplib - 动态Joinpoint特性系统

提供AOP拦截器，支持插件化架构
"""
from .joins import join_method, join_property
from .context import JoinMethodContext
from .joincut import with_name
from .aspect import (
    Aspect,
    aop_class,
    method_before,
    method_after,
    method_exception,
    method_return,
    prop_before_set,
    prop_after_set,
    prop_get,
    prop_init,
    prop_before_delete,
    add_aspect,
    remove_aspect,
    get_aspect
)

__all__ = [
    'join_method',
    'join_property',
    'Aspect',
    'aop_class',
    'method_before',
    'method_after',
    'method_exception',
    'method_return',
    'prop_before_set',
    'prop_after_set',
    'prop_get',
    'prop_init',
    'prop_before_delete',
    'JoinMethodContext',
    'add_aspect',
    'remove_aspect',
    'get_aspect',
    'with_name'
]
__version__ = '0.3.0'
