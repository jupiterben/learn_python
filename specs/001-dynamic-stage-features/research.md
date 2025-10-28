# 研究报告：动态 Stage 特性系统

**日期**: 2025-10-28  
**目的**: 解决技术选型和设计决策问题

---

## 1. 装饰器元数据保留方案

### 决策
使用 `functools.wraps` 保留原函数的元数据。

### 理由
- **标准库方案**：`functools.wraps` 是 Python 标准库提供的官方解决方案
- **自动处理**：自动复制 `__name__`, `__doc__`, `__module__`, `__qualname__`, `__annotations__`, `__dict__`
- **零依赖**：无需外部库，符合宪章原则
- **广泛使用**：Python 社区标准实践

### 替代方案考虑
- **手动复制属性**：容易遗漏，维护成本高
- **decorator 库**：外部依赖，违反零依赖原则
- **不保留元数据**：破坏函数签名，IDE 无法正确识别

### 实现要点
```python
from functools import wraps

def stage(name=None):
    def decorator(func):
        @wraps(func)  # 保留原函数元数据
        def wrapper(*args, **kwargs):
            # 拦截逻辑
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 2. Feature 抽象基类设计

### 决策
使用 `abc.ABC` 定义 Feature 抽象基类，钩子方法提供默认空实现（不强制重写）。

### 理由
- **灵活性**：子类可选择性重写 `before_stage` 或 `after_stage`
- **标准库支持**：`abc.ABC` 是 Python 3.4+ 标准库
- **类型检查友好**：IDE 和 mypy 可识别抽象类
- **语义清晰**：明确表达 Feature 是接口契约

### 设计模式
- **模板方法模式**：定义算法骨架，子类实现细节
- **不使用 `@abstractmethod`**：允许可选实现，更灵活

### 实现要点
```python
from abc import ABC

class Feature(ABC):
    """Feature 基类，定义拦截钩子接口"""
    
    def __init__(self):
        self.enabled = True
    
    def before_stage(self, context):
        """在 stage 执行前调用，可选重写"""
        pass
    
    def after_stage(self, context):
        """在 stage 执行后调用，可选重写"""
        pass
    
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False
    
    def is_enabled(self):
        return self.enabled
```

### 替代方案考虑
- **不使用抽象基类**：缺乏类型约束，容易误用
- **使用 Protocol（typing）**：需要 Python 3.8+，语法较复杂
- **强制实现钩子（@abstractmethod）**：过于严格，不够灵活

---

## 3. 上下文传递机制

### 决策
使用 `dataclasses.dataclass` 定义 `StageContext` 封装上下文信息。

### 理由
- **类型安全**：字段有明确类型，mypy 可检查
- **IDE 友好**：自动补全、字段提示
- **零样板代码**：自动生成 `__init__`, `__repr__`, `__eq__`
- **不可变性**：可选设置 `frozen=True` 防止意外修改
- **标准库方案**：Python 3.7+ 标准库

### 实现要点
```python
from dataclasses import dataclass
from typing import Any, Callable, Optional

@dataclass
class StageContext:
    """Stage 执行上下文"""
    stage_name: str               # stage 名称
    instance: Any                 # 对象实例（self）
    method: Callable              # 原始方法对象
    args: tuple                   # 位置参数（不含 self）
    kwargs: dict                  # 关键字参数
    result: Any = None            # 方法返回值（after_stage 有效）
    exception: Optional[Exception] = None  # 异常对象
```

### 替代方案考虑
- **字典传递**：灵活但无类型检查，容易拼写错误
- **命名元组（namedtuple）**：不可变但不支持默认值和类型注解
- **普通类**：需手写 `__init__` 和 `__repr__`，样板代码多

### 设计权衡
- **可变 vs 不可变**：选择可变（不用 `frozen=True`），允许 Feature 在 context 上附加自定义数据
- **字段数量**：平衡信息完整性和复杂度，7 个字段适中

---

## 4. 异常处理策略

### 决策
采用**分层异常策略**：
- `before_stage` 异常 → 终止执行，传播异常
- 原方法异常 → 跳过 `after_stage`，传播异常
- `after_stage` 异常 → 记录警告，继续执行后续 Feature

### 理由
- **安全优先**：`before_stage` 失败应阻止方法执行（如权限检查失败）
- **结果保护**：原方法异常不应被 Feature 干扰
- **容错性**：`after_stage` 失败（如日志写入失败）不应影响业务逻辑

### 行为矩阵

| 异常位置 | 行为 | 理由 |
|---------|------|------|
| Feature.before_stage() | 终止，不调用原方法和后续钩子，向上传播 | 前置条件失败应阻止执行 |
| 原方法 | 设置 context.exception，跳过所有 after_stage，向上传播 | 业务逻辑异常不应被掩盖 |
| Feature.after_stage() | 记录警告，继续调用后续 Feature 的 after_stage，不传播 | 后置处理失败不应影响结果 |

### 配置选项
提供 `strict_mode` 参数（默认 `False`）：
- `False`：宽松模式，`after_stage` 异常仅记录
- `True`：严格模式，所有异常都传播

### 实现要点
```python
import logging

logger = logging.getLogger(__name__)

def _call_features(features, stage_name, context, phase):
    """调用 Feature 钩子"""
    for feature in features:
        if not feature.is_enabled():
            continue
        
        try:
            if phase == 'before':
                feature.before_stage(context)
            else:
                feature.after_stage(context)
        except Exception as e:
            if phase == 'before':
                # before 异常终止执行
                raise
            else:
                # after 异常仅记录警告
                logger.warning(
                    f"Feature {feature.__class__.__name__}.after_stage() "
                    f"failed: {e}", exc_info=True
                )
```

### 替代方案考虑
- **所有异常都传播**：过于严格，日志失败会破坏业务
- **所有异常都静默**：过于宽松，前置检查失败无法阻止执行
- **使用 try-except 包装原方法**：会改变异常堆栈，不利于调试

---

## 5. Feature 注册与执行顺序

### 决策
- **注册位置**：实例级别（`AOPClass` 实例属性）
- **执行顺序**：FIFO（先注册先执行）

### 理由
- **实例级别优势**：
  - 运行时动态修改 Feature
  - 不同实例可有不同 Feature 配置
  - 避免类级别的线程安全问题
- **FIFO 优势**：
  - 直观易理解（注册顺序即执行顺序）
  - 实现简单
  - 符合大多数使用场景

### 实现要点
```python
class AOPClass:
    def __init__(self):
        self._features = []  # 实例属性
    
    def add_feature(self, feature):
        if feature in self._features:
            raise ValueError("Feature already added")
        self._features.append(feature)  # FIFO
        return self  # 链式调用
    
    def get_features(self):
        return list(self._features)  # 返回副本
```

### 替代方案考虑
- **类级别注册**：所有实例共享 Feature，不够灵活
- **优先级排序**：增加复杂度，首版不需要
- **按依赖关系排序**：过于复杂，类似 Spring AOP 的 @Order

### 未来扩展
v0.4.0 可引入优先级：
```python
class Feature:
    priority = 0  # 数字越小优先级越高

# 执行时按 priority 排序
sorted_features = sorted(features, key=lambda f: f.priority)
```

---

## 6. 性能优化策略

### 决策
实现**零 Feature 快速路径**，避免不必要的开销。

### 理由
- **常见场景**：开发环境启用 Feature，生产环境可能禁用
- **性能目标**：零 Feature 时开销 < 5%
- **实现成本**：低，仅需一次条件判断

### 实现要点
```python
def stage(name=None):
    def decorator(func):
        stage_name = name or func.__name__
        
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 快速路径：无 Feature 或非 AOPClass 实例
            if not isinstance(self, AOPClass) or not self._features:
                return func(self, *args, **kwargs)
            
            # 正常拦截逻辑
            context = StageContext(...)
            _call_before_features(...)
            result = func(self, *args, **kwargs)
            context.result = result
            _call_after_features(...)
            return result
        
        return wrapper
    return decorator
```

### 性能基准目标

| 场景 | 性能损失 | 验证方法 |
|------|----------|----------|
| 零 Feature | < 5% | 运行 1000 次方法调用，对比有/无装饰器 |
| 1 个空 Feature | < 10% | 同上 |
| 10 个空 Feature | < 15% | 同上 |
| 100 个空 Feature | < 30% | 边界测试 |

### 优化技巧
- **避免重复计算**：缓存 Feature 列表长度
- **减少对象创建**：复用 StageContext（如果不存在线程问题）
- **使用 `__slots__`**：`StageContext` 可用 slots 减少内存

---

## 7. 线程安全考虑

### 决策
**不保证线程安全**，在文档中明确说明。

### 理由
- **复杂度**：线程安全需要锁机制，增加实现复杂度和性能开销
- **使用场景**：大多数 Python 应用是单线程或使用多进程（GIL 限制）
- **变通方案**：用户可为每个线程创建独立的对象实例

### 文档说明
在 README 和 API 文档中添加：
```markdown
## 线程安全

aoplib 核心功能**不保证线程安全**。如果在多线程环境使用：

1. **推荐方案**：每个线程创建独立的对象实例
2. **不推荐**：多线程共享同一实例并动态修改 Feature

原因：Feature 列表修改（add/remove）和遍历（stage 执行）未加锁。

未来版本可能提供线程安全的 `ThreadSafeAOPClass`（归入 extras）。
```

### 未来扩展
v0.5.0 可提供线程安全版本：
```python
from threading import RLock

class ThreadSafeAOPClass(AOPClass):
    def __init__(self):
        super().__init__()
        self._lock = RLock()
    
    def add_feature(self, feature):
        with self._lock:
            return super().add_feature(feature)
```

---

## 8. 测试策略总结

### 单元测试覆盖
- **装饰器测试**（`test_stage_decorator.py`）：
  - 无参数/带参数装饰器
  - 元数据保留
  - 多次装饰
- **Feature 测试**（`test_feature.py`）：
  - 抽象基类子类化
  - 可选重写 before/after
  - enable/disable 功能
- **AOPClass 测试**（`test_aop_class.py`）：
  - add/remove/has/clear 操作
  - 重复添加检测
  - 链式调用
- **拦截测试**（`test_interception.py`）：
  - 无 Feature、单 Feature、多 Feature
  - 按序执行验证
  - 上下文正确传递
- **异常测试**（`test_exceptions.py`）：
  - before/after/原方法异常的所有组合
  - strict_mode 开关
- **边界测试**（`test_edge_cases.py`）：
  - 嵌套 stage 调用
  - 递归调用
  - 空方法、无参数方法

### 集成测试
- 完整应用场景：多个 stage + 多个 Feature
- 实用 Feature 示例：日志、监控、缓存、重试

### 性能测试
- 基准脚本：`benchmark_performance.py`
- 对比场景：无装饰器、零 Feature、1/10/100 个 Feature
- 性能目标验证

---

## 9. 最佳实践建议

### Feature 开发指南

#### DO ✅
1. **单一职责**：每个 Feature 只做一件事（日志、监控、缓存各自独立）
2. **无状态优先**：尽量设计为无状态或状态最小化
3. **幂等性**：before/after 钩子应幂等，多次调用结果一致
4. **快速失败**：在 before_stage 中检查前置条件，失败立即抛异常
5. **容错设计**：after_stage 捕获内部异常，不影响主流程

#### DON'T ❌
1. **不要修改 context.result**：保持透明，不改变方法返回值
2. **不要长时间阻塞**：避免网络 IO、文件写入等耗时操作阻塞钩子
3. **不要依赖执行顺序**：Feature 之间应独立，不依赖其他 Feature 的执行
4. **不要在钩子中再次调用 stage**：避免递归和性能问题
5. **不要假设线程安全**：多线程环境使用独立实例

### 常见模式

#### 模式 1: 日志 Feature
```python
class LoggingFeature(Feature):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
    
    def before_stage(self, ctx):
        self.logger.info(f"Entering {ctx.stage_name}")
    
    def after_stage(self, ctx):
        if ctx.exception:
            self.logger.error(f"{ctx.stage_name} failed", exc_info=ctx.exception)
        else:
            self.logger.info(f"{ctx.stage_name} completed")
```

#### 模式 2: 性能监控 Feature
```python
import time

class TimingFeature(Feature):
    def before_stage(self, ctx):
        ctx.instance._start_time = time.perf_counter()
    
    def after_stage(self, ctx):
        elapsed = time.perf_counter() - ctx.instance._start_time
        print(f"{ctx.stage_name} took {elapsed:.3f}s")
```

#### 模式 3: 重试 Feature
```python
class RetryFeature(Feature):
    def __init__(self, max_retries=3):
        super().__init__()
        self.max_retries = max_retries
    
    def before_stage(self, ctx):
        ctx._retry_count = 0
    
    def after_stage(self, ctx):
        if ctx.exception and ctx._retry_count < self.max_retries:
            ctx._retry_count += 1
            print(f"Retry {ctx._retry_count}/{self.max_retries}")
            # 注意：实际重试需要更复杂的机制
```

---

## 10. 技术债务与未来改进

### 已知限制
1. **线程安全**：当前版本不支持，需在文档中说明
2. **异步支持**：不支持 `async def` 方法，需等待 v0.3.0
3. **条件拦截**：无法按条件选择性拦截，需等待 v0.4.0
4. **Feature 优先级**：按注册顺序执行，无法指定优先级

### 改进方向
1. **性能优化**：
   - 使用 `__slots__` 减少内存
   - 缓存 Feature 列表快照
   - 考虑 Cython 加速核心路径
2. **功能增强**：
   - 支持 `@classmethod` 和 `@staticmethod`
   - 提供装饰器参数控制是否拦截
   - 支持 Feature 生命周期钩子（on_register/on_remove）
3. **工具支持**：
   - 提供 Feature 调试工具（可视化执行流程）
   - 性能分析器（统计各 Feature 耗时）
   - Feature 管理 CLI

---

## 研究结论

所有技术选型和设计决策已明确，无需进一步澄清。核心设计基于以下原则：

1. ✅ **标准库优先**：所有功能使用 Python 标准库实现
2. ✅ **简单直观**：FIFO 执行顺序、可选钩子实现
3. ✅ **类型安全**：使用 dataclass 和类型注解
4. ✅ **性能优化**：零 Feature 快速路径
5. ✅ **容错设计**：分层异常策略
6. ✅ **文档完善**：明确说明限制和最佳实践

**可进入 Phase 1（设计与契约）阶段。**

