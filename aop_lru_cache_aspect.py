# -*- coding: utf-8 -*-
"""
AOP方式实现LRU Cache切面
展示如何用around_method_return实现缓存功能
"""

import time
import hashlib
import json
from collections import OrderedDict
from aoplib import Aspect, around_method_return, add_aspect
from aoplib.joins import join_method
from aoplib.context import JoinMethodContext


class LRUCache:
    """简单的LRU缓存实现"""
    
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
    
    def get(self, key):
        if key not in self.cache:
            self.misses += 1
            return None
        
        self.hits += 1
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
        
        self.cache[key] = value
    
    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    @property
    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0


class LRUCacheAspect(Aspect):
    """
    LRU缓存切面
    
    使用 @around_method_return 拦截方法返回值
    实现透明的缓存功能
    """
    
    def __init__(self, capacity=128, enabled=True):
        super().__init__()
        self.cache = LRUCache(capacity)
        self.enabled = enabled
    
    def _make_cache_key(self, context: JoinMethodContext) -> str:
        """生成缓存键"""
        # 方法名 + 参数
        key_parts = [
            context.method.__name__,
            str(context.args),
            str(sorted(context.kwargs.items()))
        ]
        
        # 生成简短的哈希键
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    @around_method_return
    def cache_result(self, context: JoinMethodContext):
        """拦截方法返回值，使用缓存"""
        if not self.enabled:
            return  # 缓存已禁用
        
        cache_key = self._make_cache_key(context)
        
        # 尝试从缓存获取
        cached_value = self.cache.get(cache_key)
        
        if cached_value is not None:
            print(f"  ⚡ [缓存命中] {context.method.__name__}{context.args}")
            context.result = cached_value  # 用缓存值替换
        else:
            print(f"  💾 [缓存写入] {context.method.__name__}{context.args} = {context.result}")
            # 保存到缓存
            self.cache.put(cache_key, context.result)
    
    def get_stats(self):
        """获取缓存统计信息"""
        return {
            'capacity': self.cache.capacity,
            'size': len(self.cache.cache),
            'hits': self.cache.hits,
            'misses': self.cache.misses,
            'hit_rate': f"{self.cache.hit_rate * 100:.1f}%"
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


# ============================================================
# 示例1: 优化斐波那契数列计算
# ============================================================

class MathService:
    """数学计算服务"""
    
    @join_method
    def fibonacci(self, n: int) -> int:
        """计算斐波那契数列（递归）"""
        if n < 2:
            return n
        return self.fibonacci(n - 1) + self.fibonacci(n - 2)
    
    @join_method
    def factorial(self, n: int) -> int:
        """计算阶乘"""
        time.sleep(0.1)  # 模拟耗时计算
        if n <= 1:
            return 1
        return n * self.factorial(n - 1)


print("=" * 60)
print("示例1: 使用LRU Cache优化递归计算")
print("=" * 60)

math_service = MathService()
cache_aspect = LRUCacheAspect(capacity=100)
add_aspect(math_service, cache_aspect)

print("\n1. 计算 fibonacci(10) - 第一次（无缓存）")
start = time.time()
result1 = math_service.fibonacci(10)
time1 = (time.time() - start) * 1000

print(f"\n结果: {result1}, 耗时: {time1:.2f}ms")

print("\n2. 计算 fibonacci(10) - 第二次（有缓存）")
start = time.time()
result2 = math_service.fibonacci(10)
time2 = (time.time() - start) * 1000

print(f"\n结果: {result2}, 耗时: {time2:.2f}ms")
print(f"性能提升: {time1 / time2:.1f}x 倍")

print(f"\n缓存统计: {cache_aspect.get_stats()}")


# ============================================================
# 示例2: API数据缓存
# ============================================================

class APIService:
    """模拟API服务"""
    
    @join_method
    def get_user(self, user_id: int):
        """获取用户信息（模拟API调用）"""
        time.sleep(0.5)  # 模拟网络延迟
        return {
            'id': user_id,
            'name': f'User_{user_id}',
            'email': f'user{user_id}@example.com',
            'timestamp': time.time()
        }
    
    @join_method
    def search(self, keyword: str, page: int = 1):
        """搜索（模拟API调用）"""
        time.sleep(0.3)
        return {
            'keyword': keyword,
            'page': page,
            'results': [f'result_{i}' for i in range(10)]
        }


print("\n\n" + "=" * 60)
print("示例2: API响应缓存")
print("=" * 60)

api_service = APIService()
api_cache = LRUCacheAspect(capacity=50)
add_aspect(api_service, api_cache)

print("\n1. 首次请求用户数据（慢）")
start = time.time()
user1 = api_service.get_user(123)
time1 = (time.time() - start) * 1000
print(f"耗时: {time1:.0f}ms")

print("\n2. 再次请求相同用户（快）")
start = time.time()
user2 = api_service.get_user(123)
time2 = (time.time() - start) * 1000
print(f"耗时: {time2:.0f}ms")

print(f"\n加速比: {time1 / time2:.0f}x")

print("\n3. 多次搜索测试")
api_service.search("python", page=1)
api_service.search("python", page=2)
api_service.search("python", page=1)  # 缓存命中
api_service.search("java", page=1)

print(f"\n缓存统计: {api_cache.get_stats()}")


# ============================================================
# 示例3: 可控的缓存策略
# ============================================================

print("\n\n" + "=" * 60)
print("示例3: 动态控制缓存")
print("=" * 60)

class DataService:
    @join_method
    def expensive_query(self, query: str):
        """昂贵的查询操作"""
        time.sleep(0.2)
        return f"Result for: {query}"


data_service = DataService()
controllable_cache = LRUCacheAspect(capacity=10, enabled=True)
add_aspect(data_service, controllable_cache)

print("\n1. 缓存启用状态")
data_service.expensive_query("test1")
data_service.expensive_query("test1")  # 命中缓存

print("\n2. 禁用缓存")
controllable_cache.enabled = False
data_service.expensive_query("test2")
data_service.expensive_query("test2")  # 不使用缓存

print("\n3. 重新启用缓存")
controllable_cache.enabled = True
data_service.expensive_query("test3")
data_service.expensive_query("test3")  # 使用缓存

print("\n4. 清空缓存")
controllable_cache.clear_cache()
print(f"清空后统计: {controllable_cache.get_stats()}")


# ============================================================
# 总结
# ============================================================

print("\n\n" + "=" * 60)
print("总结：AOP方式实现缓存的优势")
print("=" * 60)

print("""
✅ 业务代码零侵入
   - 只需添加 @join_method 装饰器
   - 不需要修改方法实现
   
✅ 缓存逻辑集中管理
   - 统一的缓存策略
   - 易于维护和升级
   
✅ 灵活可控
   - 可动态启用/禁用
   - 可清空缓存
   - 可获取统计信息
   
✅ 可组合
   - 可以与其他切面组合
   - 如：日志 + 缓存 + 监控
   
✅ 易于测试
   - 可以单独测试缓存逻辑
   - 可以在测试时禁用缓存

【适用场景】
  • API响应缓存
  • 数据库查询缓存
  • 复杂计算结果缓存
  • 递归函数优化
  • 微服务间调用缓存

【与 @lru_cache 对比】
  内置 @lru_cache: 简单、快速，适合纯函数
  AOP LRUCacheAspect: 灵活、可控，适合企业应用
""")



