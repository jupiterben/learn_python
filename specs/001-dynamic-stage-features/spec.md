# 需求规格：动态 Stage 特性系统

**版本**: 1.0.0  
**创建日期**: 2025-10-28  
**最后更新**: 2025-10-28  
**作者**: AI Assistant

---

## 概述

### 功能描述

实现一个完整的 AOP（面向切面编程）拦截器系统，允许开发者：
1. 使用 `@stage` 装饰器标记对象方法为"阶段方法"
2. 动态注册 Feature（特性/插件）到对象实例
3. 在每个 stage 方法执行前后自动调用所有已注册 Feature 的钩子方法

这个系统为 Python 应用提供了灵活的插件化架构，类似于中间件模式，使得横切关注点（如日志、监控、权限检查）可以通过 Feature 统一管理，而不侵入业务逻辑。

**解决的问题**：
- 避免在每个方法中重复编写日志、监控、事务管理等横切逻辑
- 支持运行时动态启用/禁用功能特性
- 提供清晰的扩展点，便于第三方插件集成

### 用户故事

> 作为 Python 应用开发者，我希望能够声明式地标记关键业务方法为"stage"，并在运行时动态添加监控、日志、缓存等特性，以便在不修改业务代码的情况下增强功能。

### 范围界定

**包含**:
- `@stage` 装饰器：支持可选的 stage 名称参数
- `@aop_class` 装饰器：为任何类添加 AOP 能力，不占用继承链
- `Feature` 抽象基类：定义 `before_stage()` 和 `after_stage()` 钩子
- Stage 拦截机制：在 stage 方法执行前后自动调用所有 Feature 的钩子
- 上下文传递：钩子方法接收 stage 名称、方法参数、执行结果等上下文信息
- 异常处理：Feature 钩子抛出异常时的处理策略

**不包含**:
- 条件拦截（基于表达式的 pointcut）- 理由：首版保持简单，所有 stage 统一拦截
- Feature 执行顺序控制（优先级）- 理由：按注册顺序执行即可，后续版本可扩展
- 异步 Stage 支持（async/await）- 理由：先支持同步场景，异步归入扩展层
- 类级别的 Stage（修改类而非实例）- 理由：实例级别更灵活，符合动态特性目标

---

## 宪章对齐

### 最小化原则评估

| 原则 | 对齐说明 | 状态 |
|------|----------|------|
| 标准库优先 | 使用 `functools.wraps` 保留元数据，`dataclasses` 定义数据类，无需外部依赖 | ✅ |
| 零依赖目标 | 核心功能完全基于标准库实现（`functools`, `abc`, `dataclasses`） | ✅ |
| 依赖审计 | 无新增外部依赖 | ✅ |
| API 简洁性 | 新增 4 个公开 API：`@stage`, `@aop_class`, `Feature`, `StageContext`，总数不超过 15 个 | ✅ |
| 渐进式复杂度 | 属于核心层（零依赖），未来可扩展异步支持（extras: async）和条件拦截（extras: advanced） | ✅ |

**例外说明**: 无

---

## 功能需求

### FR-1: Stage 装饰器

**优先级**: 高  
**描述**: 提供 `@stage` 装饰器，用于标记方法为 stage method。装饰器接受可选的 stage 名称参数，未指定时使用方法名作为 stage 名称。

**验收标准**:
- [ ] 支持无参数使用：`@stage` → stage 名称为方法名
- [ ] 支持带参数使用：`@stage("custom_name")` → stage 名称为 "custom_name"
- [ ] 装饰后的方法保留原函数的元数据（`__name__`, `__doc__`）
- [ ] 装饰器可用于实例方法（`self` 作为第一个参数）
- [ ] 装饰器标记方法时存储 stage 元数据，供后续拦截使用

### FR-2: Feature 基类

**优先级**: 高  
**描述**: 提供 `Feature` 抽象基类，定义 Feature 必须实现的钩子方法接口。

**验收标准**:
- [ ] `Feature` 继承自 `abc.ABC`（标准库抽象基类）
- [ ] 定义 `before_stage(self, context: StageContext)` 方法（可选实现，默认空实现）
- [ ] 定义 `after_stage(self, context: StageContext)` 方法（可选实现，默认空实现）
- [ ] 子类可以选择性重写 `before_stage` 或 `after_stage` 或两者
- [ ] Feature 实例可存储状态（如计数器、配置）

### FR-3: StageContext 上下文对象

**优先级**: 高  
**描述**: 定义 `StageContext` 数据类，封装传递给 Feature 钩子的上下文信息。

**验收标准**:
- [ ] 包含 `stage_name: str` - stage 名称
- [ ] 包含 `instance: Any` - 调用方法的对象实例（`self`）
- [ ] 包含 `method: Callable` - 原始方法对象
- [ ] 包含 `args: tuple` - 方法位置参数（不含 `self`）
- [ ] 包含 `kwargs: dict` - 方法关键字参数
- [ ] 包含 `result: Any` - 方法执行结果（仅 `after_stage` 时有效）
- [ ] 包含 `exception: Optional[Exception]` - 方法执行异常（如有）
- [ ] 使用 `dataclasses.dataclass` 实现（标准库）

### FR-4: @aop_class 装饰器与 Feature 管理

**优先级**: 高  
**描述**: 提供 `@aop_class` 类装饰器，为任何类动态添加 Feature 管理能力，不占用继承链。

**验收标准**:
- [ ] `@aop_class` 装饰器可用于任何类
- [ ] 装饰后的类实例支持 `add_feature(feature: Feature) -> self` - 添加 Feature，支持链式调用
- [ ] 装饰后的类实例支持 `remove_feature(feature: Feature) -> self` - 移除 Feature，支持链式调用
- [ ] 装饰后的类实例支持 `get_features() -> List[Feature]` - 获取所有已注册的 Feature
- [ ] 装饰后的类实例支持 `has_feature(feature: Feature) -> bool` - 检查 Feature 是否已注册
- [ ] 装饰后的类实例支持 `clear_features()` - 清空所有 Feature
- [ ] Feature 列表按注册顺序维护
- [ ] 同一个 Feature 实例不能重复添加
- [ ] 装饰器不影响原类的继承关系

### FR-5: Stage 拦截执行

**优先级**: 高  
**描述**: 在 stage 方法执行时，自动拦截并调用所有已注册 Feature 的钩子。

**验收标准**:
- [ ] 执行顺序：`before_stage(所有 Feature)` → 原方法 → `after_stage(所有 Feature)`
- [ ] 按 Feature 注册顺序依次调用 `before_stage`
- [ ] 原方法正常执行后，按 Feature 注册顺序依次调用 `after_stage`
- [ ] `after_stage` 接收的 `context.result` 为原方法返回值
- [ ] 原方法的返回值透明传递（不被 Feature 修改）
- [ ] 仅对使用 `@aop_class` 装饰的类实例生效
- [ ] 未注册任何 Feature 时，stage 方法正常执行（无额外开销）

### FR-6: 异常处理策略

**优先级**: 中  
**描述**: 定义 Feature 钩子和原方法抛出异常时的处理行为。

**验收标准**:
- [ ] `before_stage` 抛出异常 → 终止执行，不调用原方法和后续钩子，向上传播异常
- [ ] 原方法抛出异常 → 跳过所有 `after_stage`，向上传播异常，`context.exception` 设置为异常对象
- [ ] `after_stage` 抛出异常 → 向上传播异常（简化版暂时不做静默处理）

**注**: 完整的异常处理策略（静默 after_stage 异常、FeatureError 异常类、strict_mode 配置）留待后续版本实现

### FR-7: Feature 启用/禁用

**优先级**: 低  
**描述**: Feature 支持运行时启用/禁用，无需从列表中移除。

**验收标准**:
- [ ] `Feature` 基类包含 `enabled: bool` 属性（默认 `True`）
- [ ] `disable()` 方法设置 `enabled = False`
- [ ] `enable()` 方法设置 `enabled = True`
- [ ] 拦截器跳过 `enabled=False` 的 Feature
- [ ] 禁用状态可通过 `is_enabled()` 方法查询

---

## 非功能需求

### 性能

- Stage 拦截开销：每个 Feature 钩子调用 < 0.1ms（Python 3.10, Intel i5）
- 零 Feature 时开销：相比原方法 < 5% 性能损失
- 支持 100 个并发 Feature 注册而不显著影响性能

### 兼容性

- Python 版本: 3.8+（使用 `dataclasses` 和 `abc`）
- 操作系统: Linux/macOS/Windows（纯 Python 实现）
- 依赖约束: 零外部依赖

### 安全性

- Feature 钩子运行在与主方法相同的上下文，不隔离（用户需信任 Feature 代码）
- 不提供沙箱或权限控制（不在本版本范围）

### 可维护性

- 代码复杂度: McCabe < 10
- 测试覆盖率: > 85%（核心拦截逻辑 > 95%）
- 文档完整性: 所有公开 API 有完整 docstring 和使用示例

---

## API 设计

### 模块结构

```
aoplib/
├── __init__.py         # 公开 API: stage, aop_class, Feature, StageContext
├── stage.py            # @stage 装饰器实现
├── feature.py          # Feature 基类和 @aop_class 装饰器实现
├── context.py          # StageContext 数据类
└── _internal.py        # 内部工具（私有，不导出）
```

### 公开接口

#### 装饰器：`@stage(name: Optional[str] = None)`

**参数**:
- `name` (str, 可选): stage 名称，默认为方法名

**返回**: 装饰后的方法

**示例**:
```python
from aoplib import stage, aop_class

@aop_class
class MyApp:
    @stage  # stage 名称为 "initialize"
    def initialize(self):
        print("初始化")
    
    @stage("启动阶段")  # stage 名称为 "启动阶段"
    def start(self):
        print("启动")
```

#### 装饰器：`@aop_class`

**描述**: 类装饰器，为任何类添加 AOP 能力，不占用继承链。

**使用方式**:
```python
@aop_class
class MyApp:
    @stage
    def process(self, data):
        return data
```

**添加的方法**:

- `add_feature(feature: Feature) -> self`
  - 添加 Feature 到实例
  - 返回 `self` 支持链式调用

- `remove_feature(feature: Feature) -> self`
  - 移除指定 Feature
  - 若 Feature 不存在则静默忽略

- `get_features() -> List[Feature]`
  - 返回所有已注册的 Feature 列表（副本）

- `has_feature(feature: Feature) -> bool`
  - 检查 Feature 是否已注册

- `clear_features() -> None`
  - 清空所有 Feature

**示例**:
```python
@aop_class
class MyApp:
    def __init__(self, name):
        self.name = name
    
    @stage
    def process(self, data):
        return f"{self.name}: {data}"

app = MyApp("应用1")
app.add_feature(LoggingFeature()).add_feature(MonitoringFeature())
app.process("数据")  # 两个 Feature 的钩子会被调用
```

**优势**:
- 不占用继承链，可与其他基类组合
- 可用于改造已有类
- 多重继承友好

#### 抽象类：`Feature`

**方法**:

- `before_stage(self, context: StageContext) -> None`
  - 在 stage 方法执行前调用
  - 可访问方法参数，但不能修改

- `after_stage(self, context: StageContext) -> None`
  - 在 stage 方法执行后调用
  - 可访问方法返回值

- `enable() -> None` / `disable() -> None`
  - 启用/禁用 Feature

- `is_enabled() -> bool`
  - 查询 Feature 状态

**示例**:
```python
from aoplib import Feature, StageContext

class LoggingFeature(Feature):
    def before_stage(self, context: StageContext):
        print(f"[LOG] 进入 stage: {context.stage_name}")
    
    def after_stage(self, context: StageContext):
        print(f"[LOG] 退出 stage: {context.stage_name}, 结果: {context.result}")
```

#### 数据类：`StageContext`

**属性**:
- `stage_name: str` - stage 名称
- `instance: Any` - 对象实例
- `method: Callable` - 原始方法
- `args: tuple` - 位置参数
- `kwargs: dict` - 关键字参数
- `result: Any` - 返回值（after_stage 时有效）
- `exception: Optional[Exception]` - 异常对象（如有）

**示例**:
```python
def after_stage(self, context: StageContext):
    if context.exception:
        print(f"方法 {context.stage_name} 抛出异常: {context.exception}")
    else:
        print(f"方法 {context.stage_name} 返回: {context.result}")
```

---

## 用户场景与测试

### 场景 1: 基础 Stage 拦截

```python
from aoplib import stage, aop_class, Feature, StageContext

class TimingFeature(Feature):
    def __init__(self):
        super().__init__()
    
    def before_stage(self, context):
        context.instance._start_time = time.time()
    
    def after_stage(self, context):
        elapsed = time.time() - context.instance._start_time
        print(f"{context.stage_name} 耗时: {elapsed:.2f}s")

@aop_class
class MyApp:
    @stage
    def process(self):
        time.sleep(1)
        return "完成"

app = MyApp()
app.add_feature(TimingFeature())
result = app.process()  # 输出: process 耗时: 1.00s
assert result == "完成"
```

### 场景 2: 多 Feature 按序执行

```python
class Feature1(Feature):
    def __init__(self):
        super().__init__()
    
    def before_stage(self, ctx):
        print("Feature1 before")
    
    def after_stage(self, ctx):
        print("Feature1 after")

class Feature2(Feature):
    def __init__(self):
        super().__init__()
    
    def before_stage(self, ctx):
        print("Feature2 before")
    
    def after_stage(self, ctx):
        print("Feature2 after")

@aop_class
class MyApp:
    @stage
    def process(self):
        return "完成"

app = MyApp()
app.add_feature(Feature1()).add_feature(Feature2())
app.process()
# 输出顺序:
# Feature1 before
# Feature2 before
# [原方法执行]
# Feature1 after
# Feature2 after
```

### 场景 3: Feature 异常处理

```python
class FailingFeature(Feature):
    def __init__(self):
        super().__init__()
    
    def before_stage(self, ctx):
        raise ValueError("Feature 错误")

@aop_class
class MyApp:
    @stage
    def process(self):
        return "完成"

app = MyApp()
app.add_feature(FailingFeature())
try:
    app.process()
except ValueError as e:
    print(f"捕获异常: {e}")  # Feature 错误导致方法未执行
```

### 场景 4: 动态启用/禁用

```python
@aop_class
class MyApp:
    @stage
    def process(self, data):
        return data.upper()

feature = LoggingFeature()
app = MyApp()
app.add_feature(feature)

app.process("test")  # 有日志输出

feature.disable()
app.process("test")  # 无日志输出

feature.enable()
app.process("test")  # 恢复日志输出
```

---

## 依赖清单

### 核心依赖（必须）

无（遵循零依赖原则）

**使用的标准库**:
- `functools` - `@wraps` 保留元数据（用于装饰器）
- `abc` - 抽象基类（Feature 基类）
- `dataclasses` - `StageContext` 数据类
- `typing` - 类型注解

### 可选依赖（extras）

无（当前版本）

**未来扩展计划**:
- `extras_require['async']` - 异步 Stage 支持（需 `aiohttp` 或纯 `asyncio`）
- `extras_require['advanced']` - 条件拦截（pointcut 表达式）

### 开发依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| pytest | >=7.0 | 测试框架 |
| pytest-cov | >=4.0 | 覆盖率 |
| black | >=23.0 | 格式化 |
| mypy | >=1.0 | 类型检查 |

---

## 测试策略

### 单元测试

- `test_stage_decorator.py`:
  - 无参数装饰器（stage 名称 = 方法名）
  - 带参数装饰器（自定义 stage 名称）
  - 保留原函数元数据
  - 装饰未使用 @aop_class 的类方法（应正常工作但不拦截）

- `test_feature.py`:
  - Feature 基类可子类化
  - 可选择性重写 before/after 方法
  - enable/disable 切换

- `test_aop_class.py`:
  - 添加/移除/查询 Feature
  - 重复添加同一 Feature（应拒绝）
  - 链式调用

- `test_stage_interception.py`:
  - 无 Feature 时正常执行
  - 单 Feature 拦截
  - 多 Feature 按序拦截
  - before_stage 异常终止执行
  - after_stage 异常继续执行
  - 原方法异常跳过 after_stage

- `test_context.py`:
  - 上下文对象正确传递所有参数
  - result 和 exception 互斥

### 集成测试

- 完整应用场景：App 类包含多个 stage，注册多个 Feature（日志、监控、缓存）
- 嵌套调用：一个 stage 方法调用另一个 stage 方法（Feature 应分别拦截）

### 性能测试

- 基准测试：无 Feature vs 1/10/100 个空 Feature 的性能对比
- 内存测试：大量 Feature 注册的内存占用

---

## 成功标准

1. **功能完整性**: 开发者能够用不超过 5 行代码为应用添加横切关注点（如日志）
2. **性能可接受**: 在 10 个 Feature 的场景下，性能损失 < 15%
3. **易用性**: 新用户阅读 README 示例后能在 10 分钟内实现自定义 Feature
4. **零依赖**: 核心功能无外部依赖，pip install 后即可使用
5. **测试覆盖率**: 核心拦截逻辑覆盖率 > 95%，整体 > 85%

---

## 文档要求

- [ ] README 更新：
  - 快速开始示例（5 分钟上手）
  - Feature 开发指南
  - 常见 Feature 模板（日志、监控、缓存、重试）
- [ ] API 文档：使用 `pdoc` 生成（零依赖）
- [ ] `docs/architecture.md`：拦截器执行流程图
- [ ] `docs/best-practices.md`：Feature 设计最佳实践
- [ ] CHANGELOG 条目：记录新增 API
- [ ] 类型存根文件（`.pyi`）：支持 IDE 自动补全

---

## 里程碑

- [ ] **M1**: 核心拦截机制实现 (第 1 周)
  - `@stage` 装饰器
  - `StageContext`
  - 基础拦截逻辑
- [ ] **M2**: Feature 管理完善 (第 1 周)
  - `@aop_class` 装饰器实现
  - `Feature` 抽象基类
  - 启用/禁用功能
- [ ] **M3**: 异常处理与边界情况 (第 2 周)
  - 各类异常处理策略
  - 嵌套调用测试
  - 性能优化
- [ ] **M4**: 测试与文档 (第 2 周)
  - 单元测试覆盖率 > 85%
  - 集成测试与性能基准
  - 完整文档
- [ ] **M5**: Code review 与发布 (第 3 周)
  - 宪章合规性审查
  - 发布 v0.2.0

---

## 假设与约束

### 假设

1. **单线程环境**: 首版不考虑线程安全，Feature 状态不跨线程共享
2. **信任 Feature 代码**: 不提供沙箱，用户需确保 Feature 安全
3. **实例级别拦截**: Feature 绑定到对象实例，不是类级别

### 约束

1. **不修改方法返回值**: Feature 不能修改原方法的返回值（保持透明）
2. **不支持类方法/静态方法**: `@stage` 仅支持实例方法
3. **按序执行**: Feature 按注册顺序执行，不支持优先级（未来可扩展）

---

## 参考资料

- [Python 装饰器官方文档](https://docs.python.org/3/glossary.html#term-decorator)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [AOP 概念介绍](https://en.wikipedia.org/wiki/Aspect-oriented_programming)
- 项目宪章：`.specify/memory/constitution.md`
