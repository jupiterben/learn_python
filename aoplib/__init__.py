"""
aoplib - 动态Stage特性系统

提供AOP拦截器，支持插件化架构
"""
from .stage import stage
from .context import StageContext
from .feature import (
    Feature,
    features,
    before_stage,
    after_stage,
    add_feature,
    remove_feature,
    get_feature)

__all__ = [
    'stage',
    'Feature',
    'features',
    'before_stage',
    'after_stage',
    'StageContext',
    'add_feature',
    'remove_feature',
    'get_feature'
]
__version__ = '0.3.0'
