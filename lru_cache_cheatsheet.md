# @lru_cache 快速参考

## 基本用法

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 使用
fibonacci(100)              # 计算
fibonacci(100)              # 从缓存返回

# 管理
fibonacci.cache_info()      # CacheInfo(hits=..., misses=..., ...)
fibonacci.cache_clear()     # 清空缓存
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `maxsize` | 最大缓存条目数 | 128 |
| | `None` = 无限缓存 | |
| | `0` = 禁用缓存 | |
| `typed` | 区分参数类型 | False |

```python
@lru_cache(maxsize=None)  # 无限缓存
@lru_cache(maxsize=0)     # 禁用缓存
@lru_cache(typed=True)    # 1 和 1.0 视为不同
```

## 核心原理

### 数据结构
```
双向链表 + 哈希表
root ←→ 最旧 ←→ ... ←→ 最新 ←→ root
         ↑删除           ↑插入
```

### LRU 策略
- **命中**: 移到链表末尾（最近使用）
- **未命中**: 插入链表末尾
- **满时**: 删除链表头部（最久未使用）

### 性能
- 查询: O(1)
- 插入: O(1)  
- 删除: O(1)
- 线程安全: ✓

## 使用规则

### ✅ 适合

```python
# 纯函数
@lru_cache()
def add(a, b):
    return a + b

# 递归
@lru_cache()
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)

# 计算密集型
@lru_cache()
def heavy_compute(x):
    return sum(i**2 for i in range(x))
```

### ❌ 不适合

```python
# 有副作用
@lru_cache()  # ❌
def update_db(data):
    db.save(data)

# 返回可变对象
@lru_cache()  # ❌
def get_list():
    return [1, 2, 3]

# 参数不可哈希
@lru_cache()  # ❌
def process(lst):  # list 不可哈希
    return sum(lst)
```

## 常见问题

### Q1: 为什么实例方法缓存不生效？

```python
class A:
    @lru_cache()  # ❌ self 会影响缓存键
    def method(self, x):
        return x * 2

a1 = A()
a2 = A()
a1.method(10)  # 缓存
a2.method(10)  # 未命中！(不同的 self)
```

**解决**:
```python
# 方案1: 类级别缓存
@lru_cache()
def _helper(x):
    return x * 2

class A:
    def method(self, x):
        return _helper(x)

# 方案2: 实例级别缓存
class A:
    def __init__(self):
        self._cache = {}
```

### Q2: 如何缓存可变参数？

```python
# ❌ 错误
@lru_cache()
def process(data):
    return sum(data)

process([1,2,3])  # TypeError: unhashable

# ✓ 正确：转为 tuple
@lru_cache()
def process(data: tuple):
    return sum(data)

process((1,2,3))  # OK

# 或者包装
def process_list(data: list):
    return _process_tuple(tuple(data))

@lru_cache()
def _process_tuple(data: tuple):
    return sum(data)
```

### Q3: 何时清空缓存？

```python
@lru_cache()
def get_user(user_id):
    return db.query(user_id)

# 数据更新后清空
def update_user(user_id, data):
    db.update(user_id, data)
    get_user.cache_clear()  # 清空缓存
```

## 性能优化

```python
# 根据使用频率设置 maxsize
@lru_cache(maxsize=32)    # 小数据集
@lru_cache(maxsize=1024)  # 大数据集
@lru_cache(maxsize=None)  # 无限制（递归）

# 监控缓存效果
info = func.cache_info()
hit_rate = info.hits / (info.hits + info.misses)
print(f"命中率: {hit_rate:.1%}")

# 如果命中率低，考虑：
# 1. 增加 maxsize
# 2. 调整算法
# 3. 使用其他缓存策略
```

## 源码位置

```bash
# 查看源码
python -c "import functools; print(functools.__file__)"

# 位置
Lib/functools.py              # Python 实现
Modules/_functoolsmodule.c    # C 实现（更快）
```

## 备选方案

```python
# 1. 手动实现
cache = {}
def func(x):
    if x not in cache:
        cache[x] = expensive_compute(x)
    return cache[x]

# 2. functools.cache (Python 3.9+)
from functools import cache

@cache  # 等价于 @lru_cache(maxsize=None)
def func(x):
    return x ** 2

# 3. 第三方库
from cachetools import LRUCache, cached

cache = LRUCache(maxsize=128)
@cached(cache)
def func(x):
    return x ** 2
```

## 总结

| 特性 | @lru_cache |
|------|-----------|
| **实现** | 双向链表 + 字典 |
| **复杂度** | O(1) |
| **线程安全** | ✓ |
| **递归支持** | ✓ |
| **参数要求** | 可哈希 |
| **最佳用途** | 纯函数、递归 |
| **限制** | 不适合实例方法 |



