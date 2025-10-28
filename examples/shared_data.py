"""
Feature 之间共享数据示例
"""
from aoplib import stage, Feature, aop_class
import time


class TimingFeature(Feature):
    """计时Feature - 在data中存储开始时间"""

    def __init__(self):
        super().__init__()

    def before_stage(self, context):
        # 在共享数据中存储开始时间
        context.data['start_time'] = time.time()
        print(f"[TIMING] 开始计时: {context.stage_name}")

    def after_stage(self, context):
        # 从共享数据中读取开始时间
        start_time = context.data.get('start_time')
        if start_time:
            elapsed = time.time() - start_time
            context.data['elapsed_time'] = elapsed  # 存储耗时供其他Feature使用
            print(f"[TIMING] {context.stage_name} 耗时: {elapsed:.4f}秒")


class LoggingFeature(Feature):
    """日志Feature - 可以访问Timing存储的数据"""

    def __init__(self):
        super().__init__()

    def before_stage(self, context):
        print(f"[LOG] 调用: {context.stage_name}")

    def after_stage(self, context):
        # 读取TimingFeature存储的耗时数据
        elapsed = context.data.get('elapsed_time')
        if elapsed:
            print(f"[LOG] 完成: {context.stage_name}，耗时 {elapsed:.4f}秒")
        else:
            print(f"[LOG] 完成: {context.stage_name}")


class CacheFeature(Feature):
    """缓存Feature - 在data中标记是否使用缓存"""

    def __init__(self):
        super().__init__()
        self.cache = {}

    def before_stage(self, context):
        # 检查缓存
        cache_key = f"{context.stage_name}:{context.args}"
        if cache_key in self.cache:
            context.data['cache_hit'] = True
            context.data['cached_result'] = self.cache[cache_key]
            print(f"[CACHE] 命中缓存: {cache_key}")
        else:
            context.data['cache_hit'] = False
            print(f"[CACHE] 未命中缓存: {cache_key}")

    def after_stage(self, context):
        # 如果未命中缓存，存储结果
        if not context.data.get('cache_hit'):
            cache_key = f"{context.stage_name}:{context.args}"
            self.cache[cache_key] = context.result
            print(f"[CACHE] 缓存结果: {cache_key}")


class MetricsFeature(Feature):
    """监控Feature - 收集所有Feature的数据进行统计"""

    def __init__(self):
        super().__init__()
        self.metrics = []

    def after_stage(self, context):
        # 收集所有共享数据
        metric = {
            'stage_name': context.stage_name,
            'elapsed_time': context.data.get('elapsed_time'),
            'cache_hit': context.data.get('cache_hit'),
            'result': context.result
        }
        self.metrics.append(metric)
        print(f"[METRICS] 收集数据: {metric}")


@aop_class
class Calculator:
    """计算器示例"""

    @stage
    def fibonacci(self, n):
        """计算斐波那契数"""
        if n < 2:
            return n
        return self.fibonacci(n - 1) + self.fibonacci(n - 2)

    @stage
    def factorial(self, n):
        """计算阶乘"""
        if n <= 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result


if __name__ == "__main__":
    print("=" * 60)
    print("示例1: Feature 共享数据 - Timing + Logging")
    print("=" * 60)

    calc = Calculator()
    calc.add_feature(TimingFeature()).add_feature(LoggingFeature())

    result = calc.factorial(5)
    print(f"\n结果: {result}\n")

    print("=" * 60)
    print("示例2: 多个 Feature 协作 - Timing + Cache + Metrics")
    print("=" * 60)

    calc2 = Calculator()
    timing = TimingFeature()
    cache = CacheFeature()
    metrics = MetricsFeature()

    calc2.add_feature(timing).add_feature(cache).add_feature(metrics)

    # 第一次调用（未缓存）
    print("\n--- 第一次调用 fibonacci(10) ---")
    result1 = calc2.fibonacci(10)
    print(f"结果: {result1}")

    # 第二次调用（命中缓存）
    print("\n--- 第二次调用 fibonacci(10) ---")
    result2 = calc2.fibonacci(10)
    print(f"结果: {result2}")

    # 显示收集的监控数据
    print("\n--- 监控数据摘要 ---")
    print(f"总调用次数: {len(metrics.metrics)}")
    cache_hits = sum(1 for m in metrics.metrics if m.get('cache_hit'))
    print(f"缓存命中: {cache_hits}/{len(metrics.metrics)}")

    print("\n" + "=" * 60)
    print("示例3: 自定义共享数据")
    print("=" * 60)

    class CustomFeature(Feature):
        """自定义Feature - 演示任意数据共享"""

        def __init__(self):
            super().__init__()

        def before_stage(self, context):
            # 存储自定义数据
            context.data['user_info'] = {'name': 'Alice', 'role': 'admin'}
            context.data['request_id'] = '12345'
            context.data['tags'] = ['important', 'monitored']

        def after_stage(self, context):
            # 读取和使用共享数据
            user = context.data.get('user_info', {})
            request_id = context.data.get('request_id')
            print(f"[CUSTOM] 用户 {user.get('name')} 完成操作 {request_id}")

    calc3 = Calculator()
    calc3.add_feature(CustomFeature())
    calc3.factorial(3)

    print("\n" + "=" * 60)
    print("共享数据的优势:")
    print("  1. Feature 之间可以协作（如 Timing 提供数据，Logging 使用）")
    print("  2. 避免在 instance 上添加临时属性")
    print("  3. 每次调用的数据隔离（不会相互干扰）")
    print("  4. 灵活存储任意类型数据（dict, list, object）")
    print("=" * 60)

