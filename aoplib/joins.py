"""
Joinpoint装饰器
"""

from functools import wraps
from typing import Any, Callable, List
from .context import JoinMethodContext, JoinPropContext
from .aspect import AdviceType, Aspect, get_enable_aspects


class ProceedingJoinPoint:
    def __init__(self, context: JoinMethodContext):
        self.context = context
        self.wrap_proceeding = None

    def proceed(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        if self.wrap_proceeding:
            return self.wrap_proceeding(self.context.instance, *args, **kwargs)
        else:
            return self.context.method(self.context.instance, *args, **kwargs)


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

            # 调用 Before 钩子
            for aspect in aspects:
                handlers = aspect.get_handlers(AdviceType.Before, context)
                for h in handlers:
                    h(context)

            # 执行原方法
            has_exception = False
            try:
                # 调用 Around 钩子
                for aspect in aspects:
                    handlers = aspect.get_handlers(AdviceType.Around, context)
                    for h in handlers:
                        h(ProceedingJoinPoint(context))

                    context.result = func(self, *args, **kwargs)
            except Exception as e:
                has_exception = True
                context.exception = e
                # 调用 AfterThrowing 钩子
                for aspect in aspects:
                    try:
                        aspect.handle_point(AdviceType.AfterThrowing, context)
                    except Exception as advice_error:
                        import warnings
                        warnings.warn(
                            f"Aspect {aspect.uniq_id} after_throwing failed: {advice_error}")

                # 如果异常被抑制，不再抛出
                if not context.suppressed:
                    # 可能已被替换
                    raise context.exception

            # 成功时调用 AfterReturning 钩子
            if not has_exception:
                for aspect in aspects:
                    try:
                        aspect.handle_point(AdviceType.AfterReturning, context)
                    except Exception as e:
                        import warnings
                        warnings.warn(
                            f"Aspect {aspect.uniq_id} after_returning failed: {e}")

            # 最后调用 After 钩子（无论成功或失败）
            for aspect in aspects:
                try:
                    aspect.handle_point(AdviceType.After, context)
                except Exception as e:
                    import warnings
                    warnings.warn(
                        f"Aspect {aspect.uniq_id} after failed: {e}")

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
                    AdviceType.BeforeInit, context)
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
                    AdviceType.AfterGet, context)
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

            # 调用 BeforeSet 钩子
            for aspect in aspects:
                handlers = aspect.get_handlers(
                    AdviceType.BeforeSet, context)
                for handler in handlers:
                    handler(context)

            # 检查是否跳过设置
            if context.skip_set:
                return

            # 执行实际的属性设置
            setattr(self, private_attr, value)

            # 调用 AfterSet 钩子
            for aspect in reversed(aspects):
                handlers = aspect.get_handlers(
                    AdviceType.AfterSet, context)
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

            # 调用 BeforeDelete 钩子
            for aspect in aspects:
                handlers = aspect.get_handlers(
                    AdviceType.BeforeDelete, context)
                for handler in handlers:
                    handler(context)

            # 检查是否跳过删除
            if context.skip_delete:
                return

            # 执行实际的属性删除
            delattr(self, private_attr)

            # 调用 AfterDelete 钩子
            for aspect in reversed(aspects):
                handlers = aspect.get_handlers(
                    AdviceType.AfterDelete, context)
                for handler in handlers:
                    handler(context)

        return property(fget=getter, fset=setter, fdel=deleter, doc=func.__doc__)

    if callable(f):
        # 无括号用法，filter实际上是被装饰的函数
        return decorator(f)
    return decorator
