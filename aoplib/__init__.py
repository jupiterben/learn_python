"""
aoplib - 动态Stage特性系统

提供AOP拦截器，支持插件化架构
"""
from .stage import stage
from .feature import Feature, aop_class
from .context import StageContext

__all__ = ['stage', 'Feature', 'aop_class', 'StageContext']
__version__ = '0.2.0'
