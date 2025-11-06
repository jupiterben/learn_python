# Python @lru_cache 内部实现详解

## 1. 核心数据结构

### 双向链表 + 哈希表

```
【哈希表】              【双向链表】
cache = {               root ←→ node1 ←→ node2 ←→ node3 ←→ root
  key1: node1,           ↑                              ↓
  key2: node2,         最旧（头部）              最新（末尾）
  key3: node3
}

链表节点结构：
[PREV, NEXT, KEY, RESULT]
  ↓     ↓     ↓     ↓
 上一个 下一个 键   缓存值
```

## 2. LRU 工作流程图解

### 场景1: 缓存命中

```
初始状态:
root ←→ [key1, val1] ←→ [key2, val2] ←→ [key3, val3] ←→ root
        最旧                                 最新

访问 key1 (命中):
1. 在哈希表中找到 node1
2. 从链表中摘除 node1
3. 将 node1 插入到末尾

结果:
root ←→ [key2, val2] ←→ [key3, val3] ←→ [key1, val1] ←→ root
        最旧                                 最新 ✓
```

### 场景2: 缓存未命中（容量未满）

```
初始状态 (maxsize=4, 当前3个):
root ←→ [key1, val1] ←→ [key2, val2] ←→ [key3, val3] ←→ root

访问 key4 (未命中，需计算):
1. 计算 func(key4) = val4
2. 创建新节点
3. 插入到末尾

结果:
root ←→ [key1, val1] ←→ [key2, val2] ←→ [key3, val3] ←→ [key4, val4] ←→ root
```

### 场景3: 缓存未命中（容量已满，触发淘汰）

```
初始状态 (maxsize=3, 已满):
root ←→ [key1, val1] ←→ [key2, val2] ←→ [key3, val3] ←→ root
        最旧 ✗                               最新

访问 key4 (未命中，需计算):
1. 计算 func(key4) = val4
2. 删除最旧节点 (key1) - LRU淘汰
3. 创建新节点并插入末尾

结果:
root ←→ [key2, val2] ←→ [key3, val3] ←→ [key4, val4] ←→ root
        最旧                                 最新 ✓
```

## 3. 源码核心逻辑（简化）

### 初始化

```python
def lru_cache(maxsize=128, typed=False):
    def decorating_function(user_function):
        # 创建哨兵节点（双向链表）
        root = []
        root[:] = [root, root, None, None]  # [PREV, NEXT, KEY, RESULT]
        
        # 缓存字典
        cache = {}
        
        # 统计
        hits = misses = 0
        
        # 线程锁
        lock = RLock()
        
        # 索引常量
        PREV, NEXT, KEY, RESULT = 0, 1, 2, 3
```

### 缓存查询（命中）

```python
def wrapper(*args, **kwds):
    nonlocal hits, misses
    
    # 生成缓存键
    key = make_key(args, kwds, typed)
    
    with lock:
        link = cache.get(key)
        if link is not None:
            # 缓存命中！
            hits += 1
            
            # 从链表当前位置摘除
            link_prev, link_next, _key, result = link
            link_prev[NEXT] = link_next
            link_next[PREV] = link_prev
            
            # 插入到末尾（root之前）
            last = root[PREV]
            last[NEXT] = root[PREV] = link
            link[PREV] = last
            link[NEXT] = root
            
            return result
```

### 缓存更新（未命中）

```python
    # 缓存未命中，计算结果
    result = user_function(*args, **kwds)
    
    with lock:
        misses += 1
        
        if key in cache:
            # 已存在（多线程情况）
            pass
        elif len(cache) < maxsize:
            # 未满，直接插入
            link = [last, root, key, result]
            last[NEXT] = root[PREV] = cache[key] = link
        else:
            # 已满，淘汰最旧的（root后第一个）
            oldroot = root
            oldroot[KEY] = key
            oldroot[RESULT] = result
            
            # 移动 root 到下一个节点
            root = oldroot[NEXT]
            oldkey = root[KEY]
            
            # 更新缓存
            cache[key] = oldroot
            del cache[oldkey]
    
    return result
```

## 4. 关键技术点

### 4.1 为什么用双向链表？

| 操作 | 双向链表 | OrderedDict | 普通dict |
|------|---------|-------------|----------|
| 查询 | O(1) 通过哈希表 | O(1) | O(1) |
| 移到末尾 | O(1) | O(1) | ❌ 无序 |
| 删除头部 | O(1) | O(n) popitem(False) | ❌ 无序 |
| 空间开销 | 中 | 高 | 低 |

**结论**: 双向链表 + 哈希表是最优方案

### 4.2 线程安全

```python
from threading import RLock

lock = RLock()  # 可重入锁

def wrapper(*args, **kwds):
    with lock:
        # 访问缓存
        if key in cache:
            return cache[key]
    
    # 计算结果（不持有锁）
    result = user_function(*args, **kwds)
    
    with lock:
        # 更新缓存
        cache[key] = result
```

**为什么用 RLock？**
- 支持递归调用（如 fibonacci）
- 同一线程可以多次获取锁

### 4.3 参数哈希

```python
def _make_key(args, kwds, typed, kwd_mark=(object(),)):
    """生成缓存键"""
    key = args
    if kwds:
        key += kwd_mark
        for item in kwds.items():
            key += item
    
    if typed:
        # 区分类型
        key += tuple(type(v) for v in args)
    
    return hash(key)
```

**要求**:
- 参数必须是不可变类型（可哈希）
- int, str, tuple ✓
- list, dict, set ✗

## 5. 特殊情况处理

### maxsize = None（无限缓存）

```python
if maxsize is None:
    # 退化为普通字典（无淘汰）
    def wrapper(*args, **kwds):
        key = make_key(args, kwds)
        result = cache.get(key, sentinel)
        if result is not sentinel:
            hits += 1
            return result
        
        result = user_function(*args, **kwds)
        cache[key] = result
        return result
```

### maxsize = 0（禁用缓存）

```python
if maxsize == 0:
    def wrapper(*args, **kwds):
        # 直接调用，不缓存
        return user_function(*args, **kwds)
```

## 6. 性能分析

### 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| 查询 | O(1) | 哈希表查找 |
| 插入 | O(1) | 链表末尾插入 |
| 删除 | O(1) | 链表头部删除 |
| 移动 | O(1) | 链表节点调整 |

### 空间复杂度

```
空间 = O(maxsize) = maxsize × (节点大小 + 键大小 + 值大小)

示例:
maxsize=128
节点: 4个指针 (32字节)
键: 假设平均 24字节
值: 假设平均 40字节

总计: 128 × (32 + 24 + 40) = 12KB
```

## 7. 使用最佳实践

### ✅ 适合使用的场景

```python
# 1. 纯函数
@lru_cache(maxsize=128)
def calculate_price(quantity, unit_price):
    return quantity * unit_price * 1.1  # 加税

# 2. 递归算法
@lru_cache(maxsize=None)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 3. 计算密集型
@lru_cache(maxsize=256)
def matrix_multiply(a, b):
    # 复杂计算...
    return result
```

### ❌ 不适合使用的场景

```python
# 1. 有副作用的函数
@lru_cache()  # ❌ 错误！
def update_database(user_id, data):
    db.update(user_id, data)  # 副作用

# 2. 返回可变对象
@lru_cache()  # ❌ 危险！
def get_list():
    return [1, 2, 3]  # 可变对象

result1 = get_list()
result1.append(4)  # 修改了缓存的值！
result2 = get_list()  # 返回被修改的缓存

# 3. 参数是可变对象
@lru_cache()
def process(data):
    return sum(data)

process([1, 2, 3])  # ❌ TypeError: unhashable type: 'list'
```

### 正确的使用方式

```python
# 使用不可变类型
@lru_cache()
def process(data: tuple):  # tuple 是不可变的
    return sum(data)

process((1, 2, 3))  # ✓ 正确

# 返回不可变对象
@lru_cache()
def get_tuple():
    return (1, 2, 3)  # tuple 不可变

# 或者返回副本
@lru_cache()
def get_list_copy():
    return [1, 2, 3]

result = get_list_copy().copy()  # 获取副本再修改
```

## 8. 实例方法的特殊处理

### 问题

```python
class Calculator:
    def __init__(self, tax_rate):
        self.tax_rate = tax_rate
    
    @lru_cache()  # ❌ self 会成为缓存键的一部分
    def calculate(self, amount):
        return amount * (1 + self.tax_rate)

calc1 = Calculator(0.1)
calc2 = Calculator(0.1)

calc1.calculate(100)  # 缓存: (calc1, 100) -> 110
calc2.calculate(100)  # 未命中！缓存键是 (calc2, 100)
```

### 解决方案

```python
# 方案1: 使用 functools.cached_property (Python 3.8+)
from functools import cached_property

class Calculator:
    @cached_property
    def cached_calculate(self):
        @lru_cache()
        def _calculate(amount):
            return amount * (1 + self.tax_rate)
        return _calculate

# 方案2: 手动实现
class Calculator:
    def __init__(self):
        self._cache = {}
    
    def calculate(self, amount):
        if amount not in self._cache:
            self._cache[amount] = amount * (1 + self.tax_rate)
        return self._cache[amount]

# 方案3: 使用 methodtools.lru_cache (第三方库)
from methodtools import lru_cache

class Calculator:
    @lru_cache()  # 忽略 self
    def calculate(self, amount):
        return amount * (1 + self.tax_rate)
```

## 9. 源码位置

### Python 实现
```
Python安装目录/Lib/functools.py
```

### C 实现（更快）
```
Python源码/Modules/_functoolsmodule.c
```

查看源码:
```bash
python -c "import functools; print(functools.__file__)"
```

## 10. 总结

| 特性 | 说明 |
|------|------|
| **数据结构** | 双向链表 + 哈希表 |
| **时间复杂度** | O(1) 查询、插入、删除 |
| **空间复杂度** | O(maxsize) |
| **线程安全** | 是（RLock） |
| **支持递归** | 是 |
| **参数要求** | 可哈希（不可变） |
| **最佳场景** | 纯函数、计算密集型 |

**核心思想**: 
- 最近使用的在末尾
- 最久未用的在头部
- 满时删除头部
- O(1) 高效操作



