# -*- coding: utf-8 -*-
"""
LRU Cache (Least Recently Used Cache) 的多种实现

LRU: 最近最少使用缓存淘汰策略
- 缓存满时，优先淘汰最久未使用的项
- 常用于限制内存占用
"""

from functools import lru_cache
from collections import OrderedDict
import time


# ============================================================
# 方式1: Python内置的 @lru_cache 装饰器（最简单）
# ============================================================

print("=" * 60)
print("方式1: 使用内置 @lru_cache 装饰器")
print("=" * 60)

@lru_cache(maxsize=128)  # 最多缓存128个结果
def fibonacci(n):
    """计算斐波那契数列（使用缓存优化）"""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# 测试性能
start = time.time()
result = fibonacci(100)
end = time.time()

print(f"fibonacci(100) = {result}")
print(f"耗时: {(end - start) * 1000:.2f}ms")
print(f"缓存信息: {fibonacci.cache_info()}")
print(f"  - hits: 缓存命中次数")
print(f"  - misses: 缓存未命中次数")
print(f"  - maxsize: 最大缓存容量")
print(f"  - currsize: 当前缓存大小")

# 清空缓存
fibonacci.cache_clear()
print(f"\n清空缓存后: {fibonacci.cache_info()}")


# ============================================================
# 方式2: 手动实现简单的LRU Cache
# ============================================================

print("\n" + "=" * 60)
print("方式2: 手动实现LRU Cache（基于OrderedDict）")
print("=" * 60)

class LRUCache:
    """
    LRU缓存实现
    
    原理：
    - 使用OrderedDict保持插入顺序
    - 每次访问时将项移到末尾（最近使用）
    - 缓存满时删除开头的项（最久未使用）
    """
    
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
    
    def get(self, key):
        """获取缓存值"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        # 命中：移到末尾表示最近使用
        self.hits += 1
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        """设置缓存值"""
        if key in self.cache:
            # 已存在：移到末尾
            self.cache.move_to_end(key)
        else:
            # 新增：检查容量
            if len(self.cache) >= self.capacity:
                # 删除最久未使用的项（开头）
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                print(f"    [淘汰] key={oldest}")
        
        self.cache[key] = value
    
    def __repr__(self):
        return f"LRUCache(capacity={self.capacity}, size={len(self.cache)}, hits={self.hits}, misses={self.misses})"


# 测试LRU Cache
cache = LRUCache(capacity=3)

print("\n演示LRU缓存淘汰策略:")
print(f"容量: 3\n")

print("1. 添加 key=1, value='A'")
cache.put(1, 'A')
print(f"   缓存: {list(cache.cache.keys())}")

print("\n2. 添加 key=2, value='B'")
cache.put(2, 'B')
print(f"   缓存: {list(cache.cache.keys())}")

print("\n3. 添加 key=3, value='C'")
cache.put(3, 'C')
print(f"   缓存: {list(cache.cache.keys())} (已满)")

print("\n4. 访问 key=1")
value = cache.get(1)
print(f"   返回: {value}")
print(f"   缓存: {list(cache.cache.keys())} (1移到末尾)")

print("\n5. 添加 key=4, value='D' (触发淘汰)")
cache.put(4, 'D')
print(f"   缓存: {list(cache.cache.keys())} (淘汰了最久未使用的2)")

print(f"\n{cache}")


# ============================================================
# 方式3: 完整的LRU Cache（带过期时间）
# ============================================================

print("\n" + "=" * 60)
print("方式3: 带过期时间的LRU Cache")
print("=" * 60)

class LRUCacheWithTTL:
    """带过期时间的LRU缓存"""
    
    def __init__(self, capacity: int, ttl: float = None):
        """
        Args:
            capacity: 最大容量
            ttl: 过期时间（秒），None表示永不过期
        """
        self.cache = OrderedDict()
        self.capacity = capacity
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
    
    def get(self, key):
        """获取缓存值"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        value, timestamp = self.cache[key]
        
        # 检查是否过期
        if self.ttl and (time.time() - timestamp) > self.ttl:
            del self.cache[key]
            self.misses += 1
            print(f"    [过期] key={key}")
            return None
        
        # 命中：移到末尾
        self.hits += 1
        self.cache.move_to_end(key)
        return value
    
    def put(self, key, value):
        """设置缓存值"""
        timestamp = time.time()
        
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                print(f"    [淘汰] key={oldest}")
        
        self.cache[key] = (value, timestamp)
    
    def clear_expired(self):
        """清理所有过期项"""
        if not self.ttl:
            return
        
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if (current_time - timestamp) > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
            print(f"    [清理过期] key={key}")
        
        return len(expired_keys)


# 测试带TTL的缓存
print("\n演示过期时间:")
cache_ttl = LRUCacheWithTTL(capacity=5, ttl=2.0)  # 2秒过期

cache_ttl.put("user:1", {"name": "张三", "age": 25})
cache_ttl.put("user:2", {"name": "李四", "age": 30})

print("1. 立即读取 user:1")
print(f"   结果: {cache_ttl.get('user:1')}")

print("\n2. 等待2.5秒后读取 user:1")
time.sleep(2.5)
print(f"   结果: {cache_ttl.get('user:1')} (已过期)")


# ============================================================
# 方式4: 在AOP框架中使用LRU Cache（切面方式）
# ============================================================

print("\n" + "=" * 60)
print("方式4: AOP切面式缓存（结合around_method_return）")
print("=" * 60)

print("""
这是最优雅的方式！无需修改业务代码，只需添加切面：

from aoplib import Aspect, around_method_return, add_aspect
from aoplib.joins import join_method
from aoplib.context import JoinMethodContext

class LRUCacheAspect(Aspect):
    \"\"\"LRU缓存切面\"\"\"
    
    def __init__(self, capacity=128):
        super().__init__()
        self.cache = LRUCache(capacity)
    
    @around_method_return
    def cache_result(self, context: JoinMethodContext):
        \"\"\"拦截方法返回值，使用缓存\"\"\"
        # 生成缓存键
        cache_key = f"{context.name}:{context.args}:{context.kwargs}"
        
        # 尝试从缓存获取
        cached = self.cache.get(cache_key)
        if cached is not None:
            print(f"[缓存命中] {context.method.__name__}{context.args}")
            context.result = cached  # 替换为缓存值
        else:
            print(f"[缓存未命中] {context.method.__name__}{context.args}")
            # 保存到缓存
            self.cache.put(cache_key, context.result)


# 使用示例
class Calculator:
    @join_method
    def expensive_calc(self, n):
        \"\"\"模拟耗时计算\"\"\"
        time.sleep(0.5)  # 假装很慢
        return n * n

calc = Calculator()
add_aspect(calc, LRUCacheAspect(capacity=10))

# 第一次调用：慢
result1 = calc.expensive_calc(10)  # 0.5秒

# 第二次调用：快（从缓存读取）
result2 = calc.expensive_calc(10)  # 立即返回

优势：
✓ 业务代码无需修改
✓ 缓存逻辑集中管理
✓ 可以动态启用/禁用
✓ 支持多种缓存策略
✓ 便于测试和维护
""")


# ============================================================
# 性能对比
# ============================================================

print("\n" + "=" * 60)
print("性能对比：有缓存 vs 无缓存")
print("=" * 60)

def slow_function(n):
    """模拟耗时计算（无缓存）"""
    total = 0
    for i in range(n):
        total += i
    return total

@lru_cache(maxsize=128)
def fast_function(n):
    """模拟耗时计算（有缓存）"""
    total = 0
    for i in range(n):
        total += i
    return total

n = 10_000_000

# 无缓存：每次都要计算
print("\n无缓存版本:")
start = time.time()
slow_function(n)
slow_function(n)
slow_function(n)
end = time.time()
print(f"调用3次耗时: {(end - start) * 1000:.2f}ms")

# 有缓存：第一次计算，后续直接返回
print("\n有缓存版本:")
start = time.time()
fast_function(n)
fast_function(n)
fast_function(n)
end = time.time()
print(f"调用3次耗时: {(end - start) * 1000:.2f}ms")
print(f"缓存信息: {fast_function.cache_info()}")

speedup = ((end - start) * 1000) / ((end - start) * 1000)
print(f"\n性能提升: 约 {speedup:.0f}x 倍")


# ============================================================
# 总结
# ============================================================

print("\n" + "=" * 60)
print("总结")
print("=" * 60)
print("""
【内置 @lru_cache】
  ✓ 最简单，一行代码搞定
  ✓ 性能优秀（C语言实现）
  ✓ 适合：纯函数、计算密集型
  ✗ 不支持实例方法（self会影响缓存键）
  ✗ 不支持过期时间

【手动实现 LRUCache】
  ✓ 完全可控，可自定义
  ✓ 支持过期时间、统计等
  ✓ 适合：复杂场景、特殊需求
  ✗ 需要自己管理缓存逻辑

【AOP切面式缓存】
  ✓ 业务代码零侵入
  ✓ 缓存策略集中管理
  ✓ 灵活：可动态启用/禁用
  ✓ 适合：企业级应用、微服务
  
【何时使用LRU Cache】
  ✓ 计算成本高，结果可复用
  ✓ 相同参数频繁调用
  ✓ 需要限制内存占用
  ✓ 递归算法优化（如斐波那契）
  
【注意事项】
  ✗ 不要缓存有副作用的函数
  ✗ 参数必须可哈希（不可变）
  ✗ 注意内存占用（设置maxsize）
  ✗ 考虑线程安全问题
""")



