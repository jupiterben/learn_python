# API 契约：动态 Stage 特性系统

**版本**: 1.0.0  
**日期**: 2025-10-28  
**类型**: Python Library API

---

## 契约概述

本文档定义 aoplib 库的公开 API 契约，包括函数签名、类接口、异常行为和保证。

**保证级别**:
- **MUST**: 保证行为，破坏即为 bug
- **SHOULD**: 推荐行为，可能有例外
- **MAY**: 可选行为，实现可变

---

## 1. 装饰器 API

### `@stage(name: Optional[str] = None)`

**描述**: 将方法标记为 stage，启用 Feature 拦截。

**签名**:
```python
def stage(name: Optional[str] = None) -> Callable[[Callable], Callable]
```

**参数**:
- `name` (str, 可选): Stage 名称
  - 默认值: `None`（使用方法名）
  - 约束: 如果提供，必须为非空字符串

**返回值**: 装饰后的方法

**保证**:
- **MUST** 保留原方法的 `__name__`, `__doc__`, `__module__`, `__qualname__`, `__annotations__`
- **MUST** 在方法被调用时触发 Feature 拦截（如果实例是 AOPClass）
- **MUST** 支持链式装饰（与其他装饰器组合）
- **SHOULD** 性能开销在零 Feature 时 < 5%

**使用约束**:
- **MUST** 用于 AOPClass 子类的实例方法
- **MUST NOT** 用于类方法（`@classmethod`）或静态方法（`@staticmethod`）

**示例**:
```python
# 无参数使用
class MyApp(AOPClass):
    @stage  # stage_name = "process"
    def process(self, data):
        return data

# 带参数使用
class MyApp(AOPClass):
    @stage("数据处理")  # stage_name = "数据处理"
    def process(self, data):
        return data
```

**异常**:
- 不直接抛出异常，但会传播被装饰方法或 Feature 钩子的异常

---

## 2. 类 API

### `AOPClass`

**描述**: 提供 Feature 管理能力的基类。

**继承**: 无

**构造函数**:
```python
def __init__(self)
```

#### 方法：`add_feature`

**签名**:
```python
def add_feature(self, feature: Feature) -> AOPClass
```

**参数**:
- `feature` (Feature): 要添加的 Feature 实例

**返回值**: `self`（支持链式调用）

**保证**:
- **MUST** 将 Feature 添加到实例的 Feature 列表末尾（FIFO）
- **MUST** 保持注册顺序
- **MUST** 防止重复添加同一 Feature 实例

**异常**:
- `ValueError`: Feature 已经注册时抛出

**示例**:
```python
app = MyApp()
app.add_feature(LoggingFeature()).add_feature(TimingFeature())
```

#### 方法：`remove_feature`

**签名**:
```python
def remove_feature(self, feature: Feature) -> AOPClass
```

**参数**:
- `feature` (Feature): 要移除的 Feature 实例

**返回值**: `self`（支持链式调用）

**保证**:
- **MUST** 移除指定的 Feature 实例（基于对象标识 `is`）
- **MUST** 静默处理不存在的 Feature（不抛出异常）

**异常**: 无

**示例**:
```python
feature = LoggingFeature()
app.add_feature(feature)
app.remove_feature(feature)
```

#### 方法：`get_features`

**签名**:
```python
def get_features(self) -> List[Feature]
```

**返回值**: Feature 列表的副本

**保证**:
- **MUST** 返回列表副本（修改返回值不影响内部状态）
- **MUST** 保持注册顺序

**异常**: 无

**示例**:
```python
features = app.get_features()
print(f"已注册 {len(features)} 个 Feature")
```

#### 方法：`has_feature`

**签名**:
```python
def has_feature(self, feature: Feature) -> bool
```

**参数**:
- `feature` (Feature): 要检查的 Feature 实例

**返回值**: 如果 Feature 已注册返回 `True`，否则 `False`

**保证**:
- **MUST** 基于对象标识（`is`）判断

**异常**: 无

**示例**:
```python
feature = LoggingFeature()
app.add_feature(feature)
assert app.has_feature(feature) == True
```

#### 方法：`clear_features`

**签名**:
```python
def clear_features(self) -> None
```

**返回值**: 无

**保证**:
- **MUST** 移除所有 Feature

**异常**: 无

**示例**:
```python
app.clear_features()
assert len(app.get_features()) == 0
```

---

### `Feature`（抽象基类）

**描述**: 定义 Feature 接口契约。

**继承**: `abc.ABC`

**构造函数**:
```python
def __init__(self)
```

**保证**:
- **MUST** 初始化 `enabled = True`

#### 方法：`before_stage`

**签名**:
```python
def before_stage(self, context: StageContext) -> None
```

**参数**:
- `context` (StageContext): Stage 执行上下文

**返回值**: 无

**保证**:
- **MUST** 在 stage 方法执行前调用（如果 Feature 启用）
- **SHOULD** 快速返回（< 100ms）
- **MUST NOT** 修改 `context.result`（在 before 阶段为 None）

**异常**:
- 任何异常 → 终止 stage 执行，不调用原方法和后续钩子

**默认实现**: 空操作（pass）

#### 方法：`after_stage`

**签名**:
```python
def after_stage(self, context: StageContext) -> None
```

**参数**:
- `context` (StageContext): Stage 执行上下文（包含 `result` 或 `exception`）

**返回值**: 无

**保证**:
- **MUST** 在 stage 方法执行后调用（如果 Feature 启用且原方法未抛异常）
- **SHOULD** 快速返回（< 100ms）
- **MUST NOT** 修改 `context.result`

**异常**:
- 任何异常 → 记录警告，继续调用后续 Feature 的 `after_stage`，不影响返回值

**默认实现**: 空操作（pass）

#### 方法：`enable`

**签名**:
```python
def enable(self) -> None
```

**保证**:
- **MUST** 设置 `enabled = True`

**异常**: 无

#### 方法：`disable`

**签名**:
```python
def disable(self) -> None
```

**保证**:
- **MUST** 设置 `enabled = False`

**异常**: 无

#### 方法：`is_enabled`

**签名**:
```python
def is_enabled(self) -> bool
```

**返回值**: Feature 是否启用

**保证**:
- **MUST** 返回当前 `enabled` 状态

**异常**: 无

---

## 3. 数据类 API

### `StageContext`

**描述**: 封装 stage 执行上下文。

**类型**: `dataclasses.dataclass`

**字段**:

```python
@dataclass
class StageContext:
    stage_name: str                    # Stage 名称
    instance: Any                      # 对象实例
    method: Callable                   # 原始方法
    args: tuple                        # 位置参数
    kwargs: dict                       # 关键字参数
    result: Any = None                 # 返回值（after_stage 有效）
    exception: Optional[Exception] = None  # 异常对象
```

**保证**:
- **MUST** 所有必需字段在构造时提供
- **MUST** `result` 和 `exception` 互斥（最多一个非 None）
- **MUST** 在 `before_stage` 时 `result` 和 `exception` 均为 None
- **MUST** 在 `after_stage` 时 `result` 或 `exception` 之一非 None

**不可变性**: 字段可变（允许 Feature 附加自定义属性）

**示例**:
```python
def before_stage(self, context):
    print(f"Stage: {context.stage_name}")
    print(f"Args: {context.args}")

def after_stage(self, context):
    if context.exception:
        print(f"失败: {context.exception}")
    else:
        print(f"成功: {context.result}")
```

---

## 4. 异常 API

### `FeatureError`

**描述**: Feature 特定错误。

**继承**: `Exception`

**构造函数**:
```python
def __init__(self, message: str, feature: Optional[Feature] = None)
```

**参数**:
- `message` (str): 错误消息
- `feature` (Feature, 可选): 引发错误的 Feature 实例

**属性**:
- `message` (str): 错误消息
- `feature` (Optional[Feature]): Feature 实例

**使用场景**:
```python
class AuthFeature(Feature):
    def before_stage(self, context):
        if not self.authorized:
            raise FeatureError("权限不足", feature=self)
```

---

## 5. 执行契约

### Stage 拦截执行顺序

**保证**:
```
1. 检查实例是否为 AOPClass ✓
2. 获取 Feature 列表 ✓
3. 构造 StageContext ✓
4. 按注册顺序调用 Feature.before_stage(context) ✓
5. 执行原方法 ✓
6. 更新 context.result 或 context.exception ✓
7. 按注册顺序调用 Feature.after_stage(context) ✓
8. 返回原方法结果 ✓
```

### 异常处理契约

| 异常位置 | 行为 | 保证级别 |
|---------|------|----------|
| Feature.before_stage() | 终止执行，传播异常，不调用原方法和 after_stage | **MUST** |
| 原方法 | 设置 context.exception，跳过所有 after_stage，传播异常 | **MUST** |
| Feature.after_stage() | 记录警告，继续后续 Feature 的 after_stage，不传播 | **MUST** |

### 性能契约

| 场景 | 性能要求 | 保证级别 |
|------|----------|----------|
| 零 Feature | 开销 < 5% | **MUST** |
| 10 个空 Feature | 开销 < 15% | **SHOULD** |
| Feature 钩子调用 | 每次 < 0.1ms | **MAY** |

---

## 6. 线程安全契约

**保证**:
- **NOT GUARANTEED**: 本版本不保证线程安全
- **MUST** 在文档中明确说明
- **RECOMMENDATION**: 每个线程使用独立实例

**示例**:
```python
# 不推荐：多线程共享实例
app = MyApp()
thread1 = Thread(target=app.process, args=(data1,))
thread2 = Thread(target=app.process, args=(data2,))

# 推荐：每线程独立实例
def worker(data):
    app = MyApp()
    app.add_feature(LoggingFeature())
    app.process(data)

thread1 = Thread(target=worker, args=(data1,))
thread2 = Thread(target=worker, args=(data2,))
```

---

## 7. 兼容性契约

### Python 版本
- **MUST** 支持 Python 3.8+
- **MUST** 使用标准库特性（`dataclasses`, `abc`, `functools`, `typing`）

### 依赖
- **MUST** 零外部依赖

### 向后兼容
- **MINOR 版本**（0.x.0）：可添加新 API，不破坏现有代码
- **MAJOR 版本**（x.0.0）：可破坏 API，需迁移指南

---

## 8. 测试契约

### 单元测试保证
- **MUST** 覆盖所有公开 API
- **MUST** 覆盖所有异常路径
- **MUST** 覆盖率 > 85%（核心拦截逻辑 > 95%）

### 集成测试保证
- **MUST** 测试完整应用场景（多 stage + 多 Feature）
- **MUST** 测试边界情况（嵌套调用、递归）

---

## 9. 文档契约

### Docstring 要求
- **MUST** 所有公开 API 有完整 docstring
- **MUST** 包含参数、返回值、异常说明
- **SHOULD** 包含使用示例

### 类型注解
- **MUST** 所有公开 API 有类型注解
- **SHOULD** 兼容 mypy 静态检查

---

## 10. 契约验证清单

实现完成后验证：

- [ ] 所有签名与契约一致
- [ ] 所有保证（MUST）通过测试
- [ ] 异常行为符合契约
- [ ] 性能符合要求
- [ ] 文档完整且准确
- [ ] 类型注解通过 mypy 检查

---

**契约版本**: 1.0.0  
**更新日期**: 2025-10-28  
**状态**: 已批准

