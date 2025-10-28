# 数据模型：动态 Stage 特性系统

**日期**: 2025-10-28  
**目的**: 定义系统核心实体、关系和验证规则

---

## 实体概览

本系统包含 4 个核心实体：

1. **StageContext** - 执行上下文数据
2. **Feature** - 抽象特性基类
3. **AOPClass** - AOP 能力基类
4. **FeatureError** - 异常类型

---

## 实体详细定义

### 1. StageContext（数据类）

**职责**: 封装 stage 执行的所有上下文信息，传递给 Feature 钩子。

**字段**:

| 字段名 | 类型 | 必需 | 默认值 | 描述 | 验证规则 |
|--------|------|------|--------|------|----------|
| `stage_name` | `str` | ✅ | - | Stage 名称 | 非空字符串 |
| `instance` | `Any` | ✅ | - | 方法所属对象实例（self） | 必须是 AOPClass 子类实例 |
| `method` | `Callable` | ✅ | - | 原始方法对象 | 可调用对象 |
| `args` | `tuple` | ✅ | - | 方法位置参数（不含 self） | 任意元组 |
| `kwargs` | `dict` | ✅ | - | 方法关键字参数 | 任意字典 |
| `result` | `Any` | ❌ | `None` | 方法返回值 | 仅在 after_stage 时有效 |
| `exception` | `Optional[Exception]` | ❌ | `None` | 方法执行异常 | 必须是 Exception 子类或 None |

**约束**:
- `result` 和 `exception` 互斥（最多一个非 None）
- `stage_name` 不能为空字符串
- 在 `before_stage` 阶段，`result` 和 `exception` 均为 None

**实现**:
```python
from dataclasses import dataclass
from typing import Any, Callable, Optional

@dataclass
class StageContext:
    stage_name: str
    instance: Any
    method: Callable
    args: tuple
    kwargs: dict
    result: Any = None
    exception: Optional[Exception] = None
```

**使用示例**:
```python
# before_stage
context = StageContext(
    stage_name="process",
    instance=app_instance,
    method=app_instance.process,
    args=(data,),
    kwargs={},
    result=None,
    exception=None
)

# after_stage (正常)
context.result = "processed"

# after_stage (异常)
context.exception = ValueError("Invalid data")
```

---

### 2. Feature（抽象基类）

**职责**: 定义特性/插件的接口契约，提供拦截钩子。

**属性**:

| 属性名 | 类型 | 访问 | 默认值 | 描述 | 验证规则 |
|--------|------|------|--------|------|----------|
| `enabled` | `bool` | 公开 | `True` | Feature 是否启用 | True 或 False |

**方法**:

| 方法名 | 参数 | 返回值 | 描述 | 必需重写 |
|--------|------|--------|------|----------|
| `before_stage(context)` | `StageContext` | `None` | Stage 执行前调用 | ❌（默认空实现） |
| `after_stage(context)` | `StageContext` | `None` | Stage 执行后调用 | ❌（默认空实现） |
| `enable()` | 无 | `None` | 启用 Feature | ❌（已实现） |
| `disable()` | 无 | `None` | 禁用 Feature | ❌（已实现） |
| `is_enabled()` | 无 | `bool` | 查询启用状态 | ❌（已实现） |

**约束**:
- 子类必须继承自 `Feature`
- `before_stage` 和 `after_stage` 可选重写（至少重写一个才有意义）
- 钩子方法不应修改 `context.result`（只读原则）
- 钩子方法应快速返回（避免长时间阻塞）

**实现**:
```python
from abc import ABC

class Feature(ABC):
    def __init__(self):
        self.enabled = True
    
    def before_stage(self, context: StageContext) -> None:
        pass  # 默认空实现
    
    def after_stage(self, context: StageContext) -> None:
        pass  # 默认空实现
    
    def enable(self) -> None:
        self.enabled = True
    
    def disable(self) -> None:
        self.enabled = False
    
    def is_enabled(self) -> bool:
        return self.enabled
```

**子类示例**:
```python
class LoggingFeature(Feature):
    def before_stage(self, context):
        print(f"[LOG] 进入 {context.stage_name}")
    
    def after_stage(self, context):
        if context.exception:
            print(f"[LOG] {context.stage_name} 失败")
        else:
            print(f"[LOG] {context.stage_name} 完成")
```

**状态转换**:
```
[创建] → enabled=True
  ↓ disable()
enabled=False
  ↓ enable()
enabled=True
```

---

### 3. AOPClass（基类）

**职责**: 提供 Feature 管理能力，作为所有支持 AOP 的类的基类。

**属性**:

| 属性名 | 类型 | 访问 | 默认值 | 描述 | 验证规则 |
|--------|------|------|--------|------|----------|
| `_features` | `List[Feature]` | 私有 | `[]` | 已注册的 Feature 列表 | 不可为 None |

**方法**:

| 方法名 | 参数 | 返回值 | 描述 | 约束 |
|--------|------|--------|------|------|
| `add_feature(feature)` | `Feature` | `AOPClass` | 添加 Feature | 不允许重复添加同一实例 |
| `remove_feature(feature)` | `Feature` | `AOPClass` | 移除 Feature | Feature 不存在时静默忽略 |
| `get_features()` | 无 | `List[Feature]` | 获取 Feature 列表 | 返回副本，不可直接修改 |
| `has_feature(feature)` | `Feature` | `bool` | 检查 Feature 是否存在 | 基于对象标识（is）判断 |
| `clear_features()` | 无 | `None` | 清空所有 Feature | - |

**约束**:
- Feature 列表按注册顺序维护（FIFO）
- 同一 Feature 实例不能重复添加（基于 `is` 判断）
- `get_features()` 返回列表副本，防止外部直接修改
- 所有修改方法支持链式调用

**实现**:
```python
class AOPClass:
    def __init__(self):
        self._features = []
    
    def add_feature(self, feature: Feature):
        if feature in self._features:
            raise ValueError(f"Feature {feature} already registered")
        self._features.append(feature)
        return self
    
    def remove_feature(self, feature: Feature):
        try:
            self._features.remove(feature)
        except ValueError:
            pass  # 静默忽略
        return self
    
    def get_features(self):
        return list(self._features)  # 返回副本
    
    def has_feature(self, feature: Feature):
        return feature in self._features
    
    def clear_features(self):
        self._features.clear()
```

**使用示例**:
```python
class MyApp(AOPClass):
    @stage
    def process(self, data):
        return f"处理 {data}"

app = MyApp()
app.add_feature(LoggingFeature()).add_feature(TimingFeature())
app.process("数据")  # 两个 Feature 的钩子会被调用
```

**Feature 列表状态**:
```
初始: []
  ↓ add_feature(f1)
[f1]
  ↓ add_feature(f2)
[f1, f2]  # FIFO 顺序
  ↓ remove_feature(f1)
[f2]
  ↓ clear_features()
[]
```

---

### 4. FeatureError（异常类）

**职责**: 表示 Feature 特定的错误。

**继承**: `Exception`

**字段**:

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `message` | `str` | 错误消息 |
| `feature` | `Optional[Feature]` | 引发错误的 Feature 实例 |

**实现**:
```python
class FeatureError(Exception):
    def __init__(self, message: str, feature: Optional[Feature] = None):
        super().__init__(message)
        self.message = message
        self.feature = feature
```

**使用场景**:
```python
class AuthFeature(Feature):
    def before_stage(self, context):
        if not self.check_permission(context.instance):
            raise FeatureError("权限不足", feature=self)
```

---

## 实体关系图

```
┌─────────────┐
│  AOPClass   │
│  (基类)     │
│             │
│ - features  │◆────────────┐
│             │              │ 1..*
│ + add()     │              │
│ + remove()  │              │
└─────────────┘              │
       △                     │
       │ 继承                 │
       │                     │
┌─────────────┐              │
│   MyApp     │              │
│             │              │
│  @stage     │              ▼
│  process()  │         ┌──────────┐
└─────────────┘         │ Feature  │
                        │ (抽象类)  │
       │                │          │
       │ 调用            │ enabled  │
       │                │          │
       ▼                │ before() │
┌─────────────┐         │ after()  │
│   @stage    │         └──────────┘
│  装饰器     │              △
│             │              │ 继承
│ 拦截逻辑    │              │
└─────────────┘         ┌──────────┐
       │                │ Logging  │
       │ 创建            │ Feature  │
       ▼                └──────────┘
┌─────────────┐
│StageContext │         ┌──────────┐
│  (数据类)   │         │ Feature  │
│             │         │  Error   │
│ stage_name  │         └──────────┘
│ instance    │
│ method      │
│ args/kwargs │
│ result      │
│ exception   │
└─────────────┘
```

**关系说明**:
1. `AOPClass` **组合** `Feature` 列表（1 对多）
2. 用户类 **继承** `AOPClass`
3. `@stage` 装饰器 **创建** `StageContext` 并传递给 `Feature`
4. `Feature` 是 **抽象基类**，具体 Feature **继承** 它
5. `FeatureError` 可由 `Feature` **抛出**

---

## 数据流

### 正常执行流程

```
1. 用户调用: app.process(data)
   ↓
2. @stage 拦截器触发
   ↓
3. 构造 StageContext:
   - stage_name = "process"
   - args = (data,)
   - result = None
   ↓
4. 调用所有 Feature.before_stage(context)
   ↓
5. 执行原方法: result = process(data)
   ↓
6. 更新 context.result = result
   ↓
7. 调用所有 Feature.after_stage(context)
   ↓
8. 返回 result
```

### 异常处理流程

#### 场景 A: before_stage 异常
```
1. Feature1.before_stage(context) ✅
2. Feature2.before_stage(context) ❌ 抛出异常
   ↓
3. 终止执行，不调用原方法
4. 不调用任何 after_stage
5. 向上传播异常
```

#### 场景 B: 原方法异常
```
1. 所有 Feature.before_stage(context) ✅
2. 原方法执行 ❌ 抛出异常
   ↓
3. 设置 context.exception = 异常对象
4. 跳过所有 after_stage
5. 向上传播异常
```

#### 场景 C: after_stage 异常
```
1. 所有 before_stage ✅
2. 原方法执行 ✅
3. Feature1.after_stage(context) ✅
4. Feature2.after_stage(context) ❌ 抛出异常
   ↓
5. 记录警告日志
6. 继续调用 Feature3.after_stage(context)
7. 返回原方法的结果（不传播 after 异常）
```

---

## 验证规则总结

### StageContext
- ✅ `stage_name` 非空
- ✅ `instance` 是 AOPClass 实例
- ✅ `method` 可调用
- ✅ `result` 和 `exception` 互斥

### Feature
- ✅ 必须继承 `Feature` 抽象类
- ✅ 钩子方法不应修改 `context.result`
- ✅ 钩子方法应快速返回（< 100ms 建议）

### AOPClass
- ✅ 不允许重复添加同一 Feature 实例
- ✅ Feature 列表维护注册顺序
- ✅ `get_features()` 返回副本

### Stage 装饰器
- ✅ 只能装饰 AOPClass 子类的实例方法
- ✅ 支持嵌套装饰（但不建议）
- ✅ 保留原方法元数据

---

## 扩展性设计

### 未来扩展点

1. **Feature 优先级**（v0.4.0）
   ```python
   class Feature:
       priority = 0  # 新增字段
   ```

2. **异步支持**（v0.3.0）
   ```python
   class AsyncFeature(Feature):
       async def before_stage(self, context):
           await async_operation()
   ```

3. **条件拦截**（v0.4.0）
   ```python
   @stage(when="method_name == 'process' and len(args) > 0")
   def process(self, data):
       ...
   ```

4. **Feature 生命周期钩子**
   ```python
   class Feature:
       def on_register(self, instance):
           """Feature 被添加到实例时调用"""
       
       def on_remove(self, instance):
           """Feature 被移除时调用"""
   ```

---

## 性能考虑

### 内存占用
- `StageContext` 每次创建约 200 字节（7 个字段）
- `Feature` 列表每个元素 8 字节（引用）
- 100 个 Feature 约 800 字节

### 时间复杂度
- `add_feature()`: O(1)（追加到列表）
- `remove_feature()`: O(n)（列表遍历）
- `get_features()`: O(n)（复制列表）
- `has_feature()`: O(n)（列表遍历）
- Stage 拦截: O(n)（遍历 Feature 列表）

### 优化建议
- Feature 数量 < 10 时性能最优
- Feature 数量 > 100 时考虑使用有序集合（OrderedSet）
- 使用 `__slots__` 减少 `StageContext` 内存

---

**数据模型定义完成，可进入契约生成阶段。**

