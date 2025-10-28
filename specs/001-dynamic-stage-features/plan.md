# 实施计划：动态 Stage 特性系统

**日期**: 2025-10-28  
**负责人**: 开发团队  
**预计工期**: 2-3 周

---

## 目标

实现完整的 AOP 拦截器系统，允许开发者：
1. 使用 `@stage` 装饰器标记方法为阶段方法
2. 动态添加/移除 Feature（插件）
3. 在每个 stage 执行前后自动调用 Feature 钩子
4. 支持 Feature 的启用/禁用控制
5. 提供完善的异常处理策略

**核心价值**：为 Python 应用提供插件化架构，将横切关注点（日志、监控、权限）与业务逻辑解耦。

---

## 宪章合规性检查

在开始实施前，必须验证以下各项：

- [x] **原则 1 (标准库优先)**: 是否评估过标准库方案？
  - 使用的标准库模块：`functools.wraps`, `abc.ABC`, `dataclasses`, `inspect`, `typing`
  - 无法使用标准库的原因：N/A（完全使用标准库）

- [x] **原则 2 (零依赖目标)**: 核心功能是否零外部依赖？
  - 核心功能依赖：无
  - 可选功能依赖：无（当前版本），未来计划 `extras_require['async']` 用于异步支持

- [x] **原则 3 (依赖审计)**: 新依赖是否通过审计？
  - 依赖名称及理由：N/A（无新增外部依赖）
  - 传递依赖数量：0

- [x] **原则 4 (API 简洁性)**: 新增公开 API 数量？
  - 新增函数/类：
    1. `@stage` 装饰器
    2. `AOPClass` 类（增强现有）
    3. `Feature` 抽象基类
    4. `StageContext` 数据类
    5. `FeatureError` 异常类
  - 当前总 API 数：15（含现有 10 个装饰器示例 + 5 个新增）< 20 ✅

- [x] **原则 5 (渐进式复杂度)**: 功能属于哪一层？
  - [x] 核心层 / [ ] 扩展层 / [ ] 集成层
  - 如是扩展/集成层，extras 组名：N/A（属于核心层）

**合规性结论**: ✅ 完全符合宪章所有原则

---

## 技术上下文

### 使用的标准库模块

| 模块 | 用途 | 版本要求 |
|------|------|----------|
| `functools` | `@wraps` 保留装饰器元数据 | Python 3.8+ |
| `abc` | 定义 `Feature` 抽象基类 | Python 3.8+ |
| `dataclasses` | `StageContext` 数据类 | Python 3.8+ |
| `inspect` | 获取函数签名信息 | Python 3.8+ |
| `typing` | 类型注解（`Optional`, `List`, `Callable`, `Any`） | Python 3.8+ |

### 核心设计模式

1. **装饰器模式**：`@stage` 包装方法，注入拦截逻辑
2. **观察者模式**：Feature 作为观察者，监听 stage 执行事件
3. **责任链模式**：多个 Feature 按注册顺序依次处理
4. **模板方法模式**：`Feature` 抽象类定义钩子接口

### 架构决策

| 决策 | 选项 | 选择理由 |
|------|------|----------|
| Feature 注册位置 | 类级别 vs 实例级别 | **实例级别** - 更灵活，支持运行时动态修改 |
| 钩子调用顺序 | FIFO vs 优先级 | **FIFO**（注册顺序）- 简单直观，首版不需要优先级 |
| 异常传播策略 | 静默 vs 传播 | **混合** - before 传播，after 记录但不传播 |
| 上下文传递方式 | 字典 vs 数据类 | **数据类** - 类型安全，IDE 友好 |
| Feature 状态管理 | 移除 vs 禁用 | **两者都支持** - 禁用更方便临时控制 |

---

## 实施步骤

### 第 1 阶段：核心拦截机制（M1）

**时间**: 5 天

#### 步骤 1: 实现 `StageContext` 数据类
- 定义所有上下文字段
- 添加类型注解
- 实现 `__repr__` 便于调试

#### 步骤 2: 实现 `@stage` 装饰器
- 支持无参数使用（stage 名 = 方法名）
- 支持带参数使用（自定义 stage 名）
- 使用 `functools.wraps` 保留元数据
- 存储 stage 元数据到方法属性

#### 步骤 3: 实现基础拦截逻辑
- 检测方法所属对象是否为 `AOPClass` 实例
- 获取对象的 Feature 列表
- 构造 `StageContext` 对象
- 调用 before/after 钩子

**交付物**:
- [ ] `aoplib/context.py` - `StageContext` 数据类
- [ ] `aoplib/stage.py` - `@stage` 装饰器及拦截逻辑
- [ ] `tests/test_stage_decorator.py` - 装饰器单元测试
- [ ] `tests/test_context.py` - 上下文对象测试

### 第 2 阶段：Feature 管理（M2）

**时间**: 3 天

#### 步骤 1: 实现 `Feature` 抽象基类
- 继承 `abc.ABC`
- 定义 `before_stage` 和 `after_stage` 方法（默认空实现）
- 添加 `enabled` 属性和 `enable()`/`disable()` 方法

#### 步骤 2: 增强 `AOPClass`
- 优化 `add_feature` 防止重复添加
- 实现 `has_feature` 方法
- 实现 `clear_features` 方法
- 添加链式调用支持

#### 步骤 3: 集成测试
- 单 Feature 拦截
- 多 Feature 按序执行
- Feature 启用/禁用

**交付物**:
- [ ] `aoplib/feature.py` - `Feature` 和增强的 `AOPClass`
- [ ] `tests/test_feature.py` - Feature 基类测试
- [ ] `tests/test_aop_class.py` - AOPClass 管理测试
- [ ] `tests/test_integration.py` - 集成测试

### 第 3 阶段：异常处理（M3）

**时间**: 3 天

#### 步骤 1: 定义异常类
- 实现 `FeatureError` 异常

#### 步骤 2: 实现异常处理策略
- `before_stage` 异常 → 终止执行并传播
- 原方法异常 → 跳过 `after_stage`，设置 `context.exception`
- `after_stage` 异常 → 记录警告，继续后续 Feature

#### 步骤 3: 配置化异常模式
- 添加 `strict_mode` 参数（默认 `False`）
- 严格模式下所有异常都传播

**交付物**:
- [ ] `aoplib/exceptions.py` - `FeatureError` 异常类
- [ ] 异常处理逻辑集成到 `stage.py`
- [ ] `tests/test_exception_handling.py` - 异常场景测试
- [ ] `docs/exception-handling.md` - 异常策略文档

### 第 4 阶段：优化与边界情况（M3 续）

**时间**: 2 天

#### 步骤 1: 性能优化
- 零 Feature 时快速路径（避免不必要开销）
- 缓存 Feature 列表（如不频繁变动）

#### 步骤 2: 边界情况处理
- 嵌套 stage 调用（一个 stage 调用另一个 stage）
- 多线程环境警告（文档说明不保证线程安全）
- 递归 stage 调用

#### 步骤 3: 性能基准测试
- 无 Feature vs 1/10/100 个 Feature 的性能对比
- 确保零 Feature 开销 < 5%

**交付物**:
- [ ] 性能优化代码
- [ ] `tests/test_edge_cases.py` - 边界情况测试
- [ ] `tests/benchmark_performance.py` - 性能基准脚本
- [ ] 性能测试报告

### 第 5 阶段：文档与示例（M4）

**时间**: 3 天

#### 步骤 1: 编写 API 文档
- 所有公开 API 的完整 docstring
- 使用 Google 风格或 NumPy 风格
- 添加类型注解

#### 步骤 2: 创建使用示例
- 日志 Feature 示例
- 监控 Feature 示例
- 缓存 Feature 示例
- 重试 Feature 示例

#### 步骤 3: 生成文档
- 使用 `pdoc` 生成 HTML 文档（零依赖）
- 创建架构流程图

**交付物**:
- [ ] README 更新（快速开始、使用示例）
- [ ] `docs/api-reference.md` - API 参考
- [ ] `docs/architecture.md` - 架构设计文档
- [ ] `docs/best-practices.md` - Feature 开发指南
- [ ] `examples/logging_feature.py` - 日志示例
- [ ] `examples/monitoring_feature.py` - 监控示例
- [ ] `examples/cache_feature.py` - 缓存示例

### 第 6 阶段：测试与发布（M5）

**时间**: 2 天

#### 步骤 1: 测试覆盖率检查
- 运行 `pytest --cov=aoplib --cov-report=html`
- 确保核心逻辑 > 95%，整体 > 85%
- 补充缺失的测试

#### 步骤 2: 代码质量检查
- 运行 `black .` 格式化
- 运行 `mypy aoplib/` 类型检查
- 运行 `radon cc aoplib/ -a` 复杂度分析（< 10）
- 修复所有 linter 错误

#### 步骤 3: 合规性审查
- 创建 `aoplib/COMPLIANCE.md` 说明遵守宪章情况
- 确认零外部依赖
- 更新 `docs/dependencies.md`

#### 步骤 4: 发布准备
- 更新 CHANGELOG.md
- 打标签 `v0.2.0`
- 创建发布说明

**交付物**:
- [ ] 测试覆盖率报告（> 85%）
- [ ] 代码质量报告（复杂度 < 10）
- [ ] `aoplib/COMPLIANCE.md` - 合规性声明
- [ ] CHANGELOG.md 更新
- [ ] 发布标签 `v0.2.0`

---

## 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 性能开销超预期（> 15%） | 高 | 中 | 早期进行性能基准测试，零 Feature 时实现快速路径 |
| 异常处理逻辑复杂导致 bug | 中 | 中 | 编写详尽的异常场景测试，覆盖所有组合 |
| Feature 状态管理线程不安全 | 中 | 低 | 文档明确说明不保证线程安全，建议每线程独立实例 |
| 嵌套 stage 调用导致意外行为 | 中 | 中 | 编写嵌套调用测试，确保每个 stage 独立拦截 |
| API 设计不够灵活需要破坏性变更 | 高 | 低 | 充分评审 API 设计，参考成熟 AOP 框架（Spring AOP、AspectJ） |

---

## 验收标准

- [ ] 功能符合需求文档（FR-1 到 FR-7 所有验收标准）
- [ ] 单元测试覆盖率 > 85%，核心拦截逻辑 > 95%
- [ ] 文档已更新：
  - [ ] README 包含快速开始
  - [ ] API 文档完整
  - [ ] 架构文档清晰
  - [ ] 示例代码可运行
- [ ] 通过所有宪章合规性检查：
  - [ ] 零外部依赖
  - [ ] API 数量 < 20
  - [ ] 代码复杂度 < 10
- [ ] Code review 通过（至少 1 位资深开发者）
- [ ] 无新增 linter 错误（black、mypy、radon 全部通过）
- [ ] 性能基准：
  - [ ] 零 Feature 开销 < 5%
  - [ ] 10 个 Feature 场景性能损失 < 15%

---

## 成功指标

根据规格定义的成功标准：

1. **易用性**: ✅ 5 行代码添加横切关注点
   - 验证：编写快速开始示例，计算代码行数

2. **性能**: ✅ 10 个 Feature 场景下性能损失 < 15%
   - 验证：运行 `tests/benchmark_performance.py`

3. **学习曲线**: ✅ 10 分钟实现自定义 Feature
   - 验证：让新开发者按 README 操作并计时

4. **零依赖**: ✅ 无外部依赖
   - 验证：检查 `requirements.txt` 和 `setup.py`

5. **测试覆盖**: ✅ 核心逻辑 > 95%，整体 > 85%
   - 验证：`pytest --cov` 报告

---

## 后续行动

### 发布后立即
- 收集用户反馈（GitHub Issues）
- 监控性能报告
- 编写博客文章介绍 aoplib

### 未来版本计划

#### v0.3.0 - 异步支持（扩展层）
- 实现 `@async_stage` 装饰器
- 支持 `async def before_stage` 和 `async def after_stage`
- 归入 `extras_require['async']`
- 依赖：纯 `asyncio`（标准库）或可选 `aiohttp`

#### v0.4.0 - 条件拦截（扩展层）
- 实现 pointcut 表达式（类似 AspectJ）
- 支持按方法名模式、参数条件拦截
- 归入 `extras_require['advanced']`

#### v1.0.0 - 稳定版
- API 冻结，向后兼容承诺
- 完整的类型存根文件（`.pyi`）
- 性能进一步优化
- 多语言文档（中文、英文）

---

## 参考资料

- 项目规格：`specs/001-dynamic-stage-features/spec.md`
- 项目宪章：`.specify/memory/constitution.md`
- Python 装饰器文档：https://docs.python.org/3/glossary.html#term-decorator
- Python ABC 文档：https://docs.python.org/3/library/abc.html
- Python dataclasses：https://docs.python.org/3/library/dataclasses.html
- Spring AOP 参考（设计灵感）：https://docs.spring.io/spring-framework/reference/core/aop.html
