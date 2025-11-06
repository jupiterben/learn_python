"""
Joinpoint装饰器
"""

from functools import wraps
from typing import Any, Callable, List
from .context import JoinMethodContext, JoinPropContext
from .aspect import AdviceType, Aspect, get_enable_aspects


def join_method(f=None, **meta):

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            aspects = get_enable_aspects(self)
            if not aspects:
                return func(self, *args, **kwargs)

            # 构造上下文
            context = JoinMethodContext(
                meta=meta,
                instance=self,
                method=func,
                args=args,
                kwargs=kwargs,
            )

            # 调用method_before钩子（隔离异常）
            for aspect in aspects:
                aspect.handle_point(AdviceType.METHOD_BEFORE, context)

            # 执行原方法
            try:
                context.result = func(self, *args, **kwargs)
            except Exception as e:
                context.exception = e
                # 调用 method_exception 钩子（隔离异常）
                for aspect in aspects:
                    try:
                        aspect.handle_point(
                            AdviceType.METHOD_EXCEPTION, context)
                    except Exception as advice_error:
                        # method_exception 的异常不应阻断其他 aspect
                        import warnings
                        warnings.warn(
                            f"Aspect {aspect.uniq_id} method_exception failed: {advice_error}")

                # 如果异常被抑制，不再抛出
                if not context.suppressed:
                    # 可能已被替换
                    raise context.exception

            # 调用method_after钩子（隔离异常）
            for aspect in reversed(aspects):
                try:
                    aspect.handle_point(AdviceType.METHOD_AFTER, context)
                except Exception as e:
                    import warnings
                    warnings.warn(
                        f"Aspect {aspect.uniq_id} method_after failed: {e}")

            # 调用method_return钩子（隔离异常）
            for aspect in aspects:
                try:
                    aspect.handle_point(AdviceType.METHOD_RETURN, context)
                except Exception as e:
                    import warnings
                    warnings.warn(
                        f"Aspect {aspect.uniq_id} method_return failed: {e}")

            return context.result

        return wrapper

    if callable(f):
        # 无括号用法，filter实际上是被装饰的函数
        return decorator(f)

    return decorator


def join_property(f=None, **meta):

    def decorator(func: Callable) -> property:
        private_attr = f"_{func.__name__}"

        # 提取已知参数
        default = meta.pop('default', None)

        def init(self, aspects: List[Aspect], context: JoinPropContext) -> None:
            if hasattr(self, private_attr):
                return
            """获取属性值"""
            context.value = context.value or default
            for aspect in aspects:
                handlers = aspect.get_handlers(
                    AdviceType.PROP_INIT, context)
                for handler in handlers:
                    context.value = handler(context)
            setattr(self, private_attr, context.value)

        def getter(self) -> Any:
            aspects = get_enable_aspects(self)
            """获取属性值"""
            # 构造上下文
            context = JoinPropContext(
                meta=meta,
                instance=self,
                method=func
            )
            init(self, aspects, context)

            context.value = getattr(self, private_attr)
            for aspect in aspects:
                handlers = aspect.get_handlers(
                    AdviceType.PROP_GET, context)
                for handler in handlers:
                    context.value = handler(context)
            return context.value

        def setter(self, value: Any):
            """设置属性值"""
            aspects = get_enable_aspects(self)
            context = JoinPropContext(
                meta=meta,
                instance=self,
                method=func,
                value=value
            )
            init(self, aspects, context)

            for aspect in aspects:
                handlers = aspect.get_handlers(
                    AdviceType.PROP_BEFORE_SET, context)
                for handler in handlers:
                    handler(context)
            setattr(self, private_attr, value)
            for aspect in reversed(aspects):
                handlers = aspect.get_handlers(
                    AdviceType.PROP_AFTER_SET, context)
                for handler in handlers:
                    handler(context)

        def deleter(self):
            """删除属性值"""
            if not hasattr(self, private_attr):
                return
            aspects = get_enable_aspects(self)
            context = JoinPropContext(
                meta=meta,
                method=func,
                instance=self
            )
            for aspect in aspects:
                handlers = aspect.get_handlers(
                    AdviceType.PROP_BEFORE_DELETE, context)
                for handler in handlers:
                    handler(context)
            delattr(self, private_attr)

            for aspect in reversed(aspects):
                handlers = aspect.get_handlers(
                    AdviceType.PROP_AFTER_DELETE, context)
                for handler in handlers:
                    handler(context)

        return property(fget=getter, fset=setter, fdel=deleter, doc=func.__doc__)

    if callable(f):
        # 无括号用法，filter实际上是被装饰的函数
        return decorator(f)
    return decorator
