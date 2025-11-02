# 类级别 vs 实例级别 Features

## 概述

aoplib 支持在两个层级定义 Features：
- **类级别** (`self.__class__._features`) - 所有实例共享
- **实例级别** (`self._features`) - 每个实例独立

## 收集顺序

```python
# stage.py 中的收集逻辑
all_features = []

# 1. 先收集类级别的features
if hasattr(self.__class__, '_features'):
    all_features.extend(self.__class__._features)

# 2. 再收集实例级别的features  
if hasattr(self, '_features'):
    all_features.extend(self._features)
```

**执行顺序：**
- before_stage: 类级别 → 实例级别
- after_stage: 实例级别 → 类级别（反向）

## 使用场景

### 场景1：全局功能（类级别）

适合所有实例都需要的功能：

```python
class UserService:
    # 所有实例都启用日志
    _features = [LogFeature(), MetricsFeature()]
    
    @stage("创建用户")
    def create_user(self, name):
        return User(name)

# 所有实例自动包含日志和监控
service1 = UserService()
service2 = UserService()
```

**优点：**
- ✅ 集中管理
- ✅ 无需每个实例单独配置
- ✅ 减少重复代码

### 场景2：可选功能（实例级别）

适合根据配置动态启用的功能：

```python
class DataProcessor:
    def __init__(self, enable_cache=False, enable_retry=False):
        self._features = []
        
        if enable_cache:
            self._features.append(CacheFeature())
        
        if enable_retry:
            self._features.append(RetryFeature())
    
    @stage("处理数据")
    def process(self, data):
        return data

# 不同实例有不同功能
proc1 = DataProcessor(enable_cache=True)   # 启用缓存
proc2 = DataProcessor(enable_retry=True)   # 启用重试
proc3 = DataProcessor()                    # 无额外功能
```

**优点：**
- ✅ 灵活配置
- ✅ 按需启用
- ✅ 实例独立

### 场景3：混合使用（推荐）

类级别提供基础功能，实例级别提供可选功能：

```python
class OrderService:
    # 基础功能：所有实例都需要
    _features = [
        LogFeature(),
        ValidationFeature()
    ]
    
    def __init__(self, region, use_cache=False):
        self.region = region
        
        # 可选功能：根据配置启用
        self._features = []
        
        if use_cache:
            self._features.append(CacheFeature())
        
        # 区域特定功能
        if region == "CN":
            self._features.append(LocalizationFeature("zh-CN"))
        elif region == "US":
            self._features.append(LocalizationFeature("en-US"))
    
    @stage("创建订单")
    def create_order(self, items):
        return Order(items)

# 不同区域、不同配置
cn_service = OrderService("CN", use_cache=True)
us_service = OrderService("US", use_cache=False)
```

**优点：**
- ✅ 基础功能统一
- ✅ 可选功能灵活
- ✅ 平衡性最好

## 详细示例

### 示例1：只使用类级别

```python
class Calculator:
    _features = [LogFeature(), TimingFeature()]
    
    @stage("计算")
    def add(self, a, b):
        return a + b

calc = Calculator()
result = calc.add(1, 2)  # 自动启用日志和计时
```

### 示例2：只使用实例级别

```python
class Reporter:
    def __init__(self, features):
        self._features = features
    
    @stage("生成报告")
    def generate(self, data):
        return Report(data)

# 不同实例有不同features
reporter1 = Reporter([EmailFeature()])
reporter2 = Reporter([SlackFeature(), EmailFeature()])
```

### 示例3：混合使用

```python
class APIClient:
    # 类级别：基础功能
    _features = [
        LogFeature(),
        MetricsFeature()
    ]
    
    def __init__(self, config):
        # 实例级别：可选功能
        self._features = []
        
        if config.get('enable_retry'):
            self._features.append(RetryFeature(max_attempts=3))
        
        if config.get('enable_cache'):
            self._features.append(CacheFeature(ttl=300))
        
        if config.get('enable_rate_limit'):
            self._features.append(RateLimitFeature(rpm=100))
    
    @stage("API请求")
    def request(self, endpoint):
        return self._do_request(endpoint)
```

### 示例4：动态修改

```python
class DynamicService:
    _features = [LogFeature()]
    
    def __init__(self):
        self._features = []
    
    def enable_feature(self, feature):
        """动态添加feature"""
        self._features.append(feature)
    
    def disable_all_features(self):
        """清空实例级别features"""
        self._features = []
    
    @stage("处理")
    def process(self, data):
        return data

service = DynamicService()
service.process("test1")  # 只有类级别的LogFeature

service.enable_feature(CacheFeature())
service.process("test2")  # LogFeature + CacheFeature

service.disable_all_features()
service.process("test3")  # 又恢复为只有LogFeature
```

## 注意事项

### 1. 类级别Features被所有实例共享

```python
class SharedState:
    _features = [CounterFeature()]  # 共享状态！
    
    @stage("计数")
    def count(self):
        pass

obj1 = SharedState()
obj2 = SharedState()

obj1.count()  # CounterFeature的计数器+1
obj2.count()  # 同一个CounterFeature，计数器+1
# 两个实例共享同一个CounterFeature实例
```

**解决方案：**
- 类级别Feature应该是无状态的
- 或者在Feature中使用实例ID区分状态

```python
class CounterFeature(Feature):
    def __init__(self):
        super().__init__()
        self.counters = {}  # 使用字典存储每个实例的计数
    
    def before_stage(self, context):
        instance_id = id(context.instance)
        self.counters[instance_id] = self.counters.get(instance_id, 0) + 1
```

### 2. 避免重复添加

```python
class BadExample:
    _features = [LogFeature()]
    
    def __init__(self):
        # ❌ 错误：会导致LogFeature执行两次
        self._features = [LogFeature()]

class GoodExample:
    _features = [LogFeature()]
    
    def __init__(self):
        # ✅ 正确：只添加额外的features
        self._features = [CacheFeature()]
```

### 3. Features顺序很重要

```python
class OrderMatters:
    _features = [
        ValidationFeature(),  # 1. 先验证
        CacheFeature(),       # 2. 再缓存
        LogFeature()          # 3. 最后日志
    ]
    
    def __init__(self, enable_retry=False):
        self._features = []
        if enable_retry:
            # 4. 重试在最后
            self._features.append(RetryFeature())
```

**执行顺序：**
```
before_stage:
  1. ValidationFeature
  2. CacheFeature
  3. LogFeature
  4. RetryFeature (如果启用)
  
[执行核心方法]

after_stage:
  4. RetryFeature (如果启用)
  3. LogFeature
  2. CacheFeature
  1. ValidationFeature
```

## 最佳实践

### ✅ 推荐做法

```python
class BestPractice:
    # 1. 类级别：稳定的、所有实例都需要的功能
    _features = [
        LogFeature(),
        MetricsFeature(),
        ValidationFeature()
    ]
    
    def __init__(self, config):
        # 2. 实例级别：可选的、配置驱动的功能
        self._features = []
        
        # 3. 根据配置动态添加
        if config.get('enable_cache'):
            self._features.append(CacheFeature(config['cache_ttl']))
        
        if config.get('enable_retry'):
            self._features.append(RetryFeature(config['max_retries']))
    
    def add_feature(self, feature):
        """4. 提供方法动态管理features"""
        self._features.append(feature)
    
    @stage("处理")
    def process(self, data):
        return data
```

### ❌ 不推荐做法

```python
class BadPractice:
    # ❌ 所有功能都放在类级别，不灵活
    _features = [
        LogFeature(),
        CacheFeature(),
        RetryFeature(),
        RateLimitFeature()
    ]
    
    def __init__(self):
        # ❌ 实例级别重复定义相同功能
        self._features = [
            LogFeature(),  # 重复！
            CacheFeature() # 重复！
        ]
```

## 总结

| 特性 | 类级别 | 实例级别 |
|------|--------|----------|
| 定义位置 | `class._features` | `self._features` |
| 作用范围 | 所有实例共享 | 单个实例独立 |
| 适用场景 | 通用基础功能 | 可选/配置功能 |
| 状态管理 | 需谨慎处理 | 可自由使用 |
| 修改方式 | 类定义时固定 | 运行时动态 |
| 执行顺序 | 优先执行 | 后执行 |

**选择建议：**
- 🔹 通用功能 → 类级别
- 🔹 可选功能 → 实例级别  
- 🔹 混合使用 → 最佳实践

