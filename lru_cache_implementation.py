# -*- coding: utf-8 -*-
"""
深入理解 Python @lru_cache 的实现原理

@lru_cache 是 functools 模块提供的装饰器，用于缓存函数调用结果
位于: Lib/functools.py (Python实现) 和 Modules/_functoolsmodule.c (C实现)
"""

from functools import wraps, lru_cache as builtin_lru_cache
from collections import OrderedDict
from threading import RLock
import time


# ============================================================
# Part 1: @lru_cache 的基本使用
# ============================================================

print("=" * 70)
print("Part 1: @lru_cache 的基本使用")
print("=" * 70)

@builtin_lru_cache(maxsize=128)
def fibonacci(n):
    """使用内置 @lru_cache 的斐波那契数列"""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print("\n基本用法:")
print(f"fibonacci(10) = {fibonacci(10)}")
print(f"缓存信息: {fibonacci.cache_info()}")
print(f"  - hits: {fibonacci.cache_info().hits} (命中次数)")
print(f"  - misses: {fibonacci.cache_info().misses} (未命中次数)")
print(f"  - maxsize: {fibonacci.cache_info().maxsize} (最大容量)")
print(f"  - currsize: {fibonacci.cache_info().currsize} (当前大小)")

# 清空缓存
fibonacci.cache_clear()
print("\n提供的方法:")
print("  - cache_info(): 获取缓存统计")
print("  - cache_clear(): 清空缓存")


# ============================================================
# Part 2: 简化版实现 - 理解核心原理
# ============================================================

print("\n" + "=" * 70)
print("Part 2: 简化版 LRU Cache 实现（理解核心原理）")
print("=" * 70)

def simple_lru_cache(maxsize=128):
    """
    简化版 @lru_cache 实现
    
    核心思想：
    1. 使用字典存储缓存
    2. 使用参数作为键
    3. LRU淘汰策略
    """
    def decorator(func):
        # 缓存字典
        cache = OrderedDict()
        # 统计信息
        hits = misses = 0
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal hits, misses
            
            # 生成缓存键
            key = _make_key(args, kwargs)
            
            # 尝试从缓存获取
            if key in cache:
                hits += 1
                # 移到末尾（最近使用）
                cache.move_to_end(key)
                return cache[key]
            
            # 缓存未命中，调用原函数
            misses += 1
            result = func(*args, **kwargs)
            
            # 保存到缓存
            cache[key] = result
            
            # 检查容量，淘汰最久未使用的
            if maxsize and len(cache) > maxsize:
                cache.popitem(last=False)  # 删除最旧的
            
            return result
        
        def cache_info():
            """返回缓存统计"""
            return {
                'hits': hits,
                'misses': misses,
                'maxsize': maxsize,
                'currsize': len(cache)
            }
        
        def cache_clear():
            """清空缓存"""
            nonlocal hits, misses
            cache.clear()
            hits = misses = 0
        
        # 添加辅助方法
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        wrapper._cache = cache  # 用于调试
        
        return wrapper
    
    return decorator


def _make_key(args, kwargs):
    """
    生成缓存键
    
    要求：参数必须是可哈希的（不可变类型）
    """
    # 简单版本：直接用元组作为键
    if kwargs:
        # 包含关键字参数
        items = tuple(sorted(kwargs.items()))
        return args + (items,)
    return args


# 测试简化版实现
@simple_lru_cache(maxsize=3)
def add(a, b):
    print(f"    [计算] {a} + {b}")
    return a + b

print("\n测试简化版 LRU Cache:")
print("maxsize=3, 观察淘汰策略\n")

print("1. add(1, 2):", add(1, 2))
print("2. add(2, 3):", add(2, 3))
print("3. add(3, 4):", add(3, 4))
print(f"   缓存键: {list(add._cache.keys())}\n")

print("4. add(1, 2):", add(1, 2), "(缓存命中)")
print(f"   缓存键: {list(add._cache.keys())} (1,2移到末尾)\n")

print("5. add(4, 5):", add(4, 5), "(触发淘汰)")
print(f"   缓存键: {list(add._cache.keys())} (淘汰了2,3)\n")

print(f"统计: {add.cache_info()}")


# ============================================================
# Part 3: 完整版实现 - 接近真实源码
# ============================================================

print("\n" + "=" * 70)
print("Part 3: 完整版 LRU Cache 实现（接近真实源码）")
print("=" * 70)

class CacheInfo:
    """缓存信息（类似 functools.CacheInfo）"""
    __slots__ = ['hits', 'misses', 'maxsize', 'currsize']
    
    def __init__(self, hits, misses, maxsize, currsize):
        self.hits = hits
        self.misses = misses
        self.maxsize = maxsize
        self.currsize = currsize
    
    def __repr__(self):
        return f"CacheInfo(hits={self.hits}, misses={self.misses}, maxsize={self.maxsize}, currsize={self.currsize})"


def lru_cache_full(maxsize=128, typed=False):
    """
    完整版 LRU Cache 实现
    
    参数：
        maxsize: 最大缓存容量
                 None = 无限缓存（退化为简单字典）
                 0 = 禁用缓存
        typed: 是否区分参数类型 (True: 1 和 1.0 视为不同)
    
    实现要点：
    1. 线程安全（使用锁）
    2. 支持 typed 参数
    3. 支持 maxsize=None（无限缓存）
    4. 哈希参数生成键
    5. 双向链表 + 字典（真实实现）
    """
    
    # maxsize=None 的特殊处理（无限缓存）
    if maxsize == 0:
        # 禁用缓存
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            wrapper.cache_info = lambda: CacheInfo(0, 0, 0, 0)
            wrapper.cache_clear = lambda: None
            return wrapper
        return decorator
    
    def decorator(func):
        # 缓存存储
        cache = OrderedDict()
        # 线程锁（线程安全）
        lock = RLock()
        # 统计信息
        hits = misses = 0
        
        def make_key(args, kwargs):
            """生成缓存键"""
            key = args
            if kwargs:
                # 排序关键字参数
                key += tuple(sorted(kwargs.items()))
            
            if typed:
                # 区分类型：添加类型信息
                key += tuple(type(v) for v in args)
                if kwargs:
                    key += tuple(type(v) for _, v in sorted(kwargs.items()))
            
            return key
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal hits, misses
            
            # 生成键
            try:
                key = make_key(args, kwargs)
            except TypeError:
                # 参数不可哈希，无法缓存
                return func(*args, **kwargs)
            
            # 线程安全访问缓存
            with lock:
                if key in cache:
                    # 缓存命中
                    hits += 1
                    cache.move_to_end(key)
                    return cache[key]
            
            # 缓存未命中，计算结果
            result = func(*args, **kwargs)
            
            with lock:
                misses += 1
                
                if key in cache:
                    # 可能在计算时被其他线程添加
                    cache.move_to_end(key)
                else:
                    cache[key] = result
                    
                    # LRU淘汰
                    if maxsize is not None and len(cache) > maxsize:
                        cache.popitem(last=False)
            
            return result
        
        def cache_info():
            """获取缓存统计"""
            with lock:
                return CacheInfo(hits, misses, maxsize, len(cache))
        
        def cache_clear():
            """清空缓存"""
            nonlocal hits, misses
            with lock:
                cache.clear()
                hits = misses = 0
        
        # 添加方法
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        
        return wrapper
    
    return decorator


# 测试完整版实现
@lru_cache_full(maxsize=128)
def factorial(n):
    """阶乘函数"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print("\n测试完整版 LRU Cache:")
result = factorial(10)
print(f"factorial(10) = {result}")
print(f"缓存信息: {factorial.cache_info()}")


# ============================================================
# Part 4: typed 参数的作用
# ============================================================

print("\n" + "=" * 70)
print("Part 4: typed 参数的作用")
print("=" * 70)

@lru_cache_full(maxsize=128, typed=False)
def func_untyped(x):
    print(f"  [计算] x={x}, type={type(x)}")
    return x * 2

@lru_cache_full(maxsize=128, typed=True)
def func_typed(x):
    print(f"  [计算] x={x}, type={type(x)}")
    return x * 2

print("\ntyped=False (默认):")
print("1. func_untyped(1):", func_untyped(1))
print("2. func_untyped(1.0):", func_untyped(1.0), "(缓存命中，1 和 1.0 视为相同)")

print("\ntyped=True:")
print("1. func_typed(1):", func_typed(1))
print("2. func_typed(1.0):", func_typed(1.0), "(缓存未命中，1 和 1.0 视为不同)")


# ============================================================
# Part 5: 真实源码的关键点
# ============================================================

print("\n" + "=" * 70)
print("Part 5: Python 真实源码的关键实现")
print("=" * 70)

print("""
Python 的 @lru_cache 实际实现（简化说明）：

【数据结构】
- 使用 **双向链表 + 字典** 实现（非 OrderedDict）
- 链表节点：[PREV, NEXT, KEY, RESULT]
- 字典：key -> 链表节点

【为什么用双向链表？】
- O(1) 移动节点到末尾（最近使用）
- O(1) 删除头节点（最久未使用）
- OrderedDict 虽然方便，但性能略低

【线程安全】
- 使用 RLock（可重入锁）
- 在访问缓存时加锁
- 支持递归调用（如 fibonacci）

【特殊优化】
- maxsize=None: 退化为普通字典（无淘汰）
- maxsize=0: 完全禁用缓存
- 小 maxsize (≤128): 使用特殊优化

【关键代码片段】（简化自 functools.py）

```python
def lru_cache(maxsize=128, typed=False):
    def decorating_function(user_function):
        # 双向链表哨兵节点
        root = []
        root[:] = [root, root, None, None]  # [PREV, NEXT, KEY, RESULT]
        
        cache = {}
        hits = misses = 0
        lock = RLock()
        
        def wrapper(*args, **kwds):
            nonlocal hits, misses
            
            # 生成键
            key = make_key(args, kwds, typed)
            
            with lock:
                link = cache.get(key)
                if link is not None:
                    # 缓存命中：移到末尾
                    hits += 1
                    link_prev, link_next, _key, result = link
                    # 从当前位置摘除
                    link_prev[NEXT] = link_next
                    link_next[PREV] = link_prev
                    # 插入末尾
                    last = root[PREV]
                    last[NEXT] = root[PREV] = link
                    link[PREV] = last
                    link[NEXT] = root
                    return result
            
            # 缓存未命中：计算结果
            result = user_function(*args, **kwds)
            
            with lock:
                misses += 1
                # 插入新节点
                # ...
                if len(cache) > maxsize:
                    # 删除最旧节点（root后的第一个）
                    # ...
            
            return result
        
        return wrapper
    return decorating_function
```

【性能特点】
- 时间复杂度：O(1) 查询、插入、删除
- 空间复杂度：O(maxsize)
- C语言实现更快（_functoolsmodule.c）

【使用建议】
✓ 纯函数（无副作用）
✓ 参数可哈希（int, str, tuple）
✓ 计算成本高，结果可复用
✗ 不要缓存 I/O 操作
✗ 不要缓存有副作用的函数
✗ 参数不能是 list, dict, set
""")


# ============================================================
# Part 6: 性能对比
# ============================================================

print("\n" + "=" * 70)
print("Part 6: 性能对比")
print("=" * 70)

def fib_no_cache(n):
    """无缓存版本"""
    if n < 2:
        return n
    return fib_no_cache(n - 1) + fib_no_cache(n - 2)

@builtin_lru_cache(maxsize=None)
def fib_with_cache(n):
    """有缓存版本"""
    if n < 2:
        return n
    return fib_with_cache(n - 1) + fib_with_cache(n - 2)

n = 30

print(f"\n计算 fibonacci({n}):\n")

# 无缓存
start = time.time()
result1 = fib_no_cache(n)
time1 = time.time() - start

print(f"无缓存: {result1}")
print(f"耗时: {time1:.4f}秒")

# 有缓存
start = time.time()
result2 = fib_with_cache(n)
time2 = time.time() - start

print(f"\n有缓存: {result2}")
print(f"耗时: {time2:.6f}秒")
if time2 > 0:
    print(f"加速比: {time1 / time2:.0f}x")
else:
    print(f"加速比: >1000x (太快了，无法精确测量)")
print(f"缓存信息: {fib_with_cache.cache_info()}")


# ============================================================
# 总结
# ============================================================

print("\n" + "=" * 70)
print("总结")
print("=" * 70)

print("""
【@lru_cache 的核心原理】

1. 数据结构
   - 双向链表 + 哈希表
   - O(1) 查询、插入、删除

2. LRU 策略
   - 命中：移到链表末尾（最近使用）
   - 满时：删除链表头部（最久未使用）

3. 线程安全
   - 使用 RLock 保护缓存
   - 支持递归调用

4. 参数处理
   - 参数必须可哈希
   - typed=True 区分参数类型

【何时使用】
✓ 纯函数（相同输入 → 相同输出）
✓ 计算成本高
✓ 频繁重复调用
✓ 递归算法优化

【注意事项】
✗ 不要缓存有副作用的函数
✗ 注意内存占用（设置 maxsize）
✗ 参数必须不可变
✗ 实例方法需要特殊处理（self 会影响缓存）

【源码位置】
- Python 实现: Lib/functools.py
- C 实现: Modules/_functoolsmodule.c
""")

