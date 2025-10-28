# aoplib 使用示例

## 快速开始

### 1. 装饰器方式（推荐 - 不占用继承链）

```python
from aoplib import stage, Feature, aop_class

# 定义Feature
class LoggingFeature(Feature):
    def __init__(self):
        super().__init__()
    
    def before_stage(self, context):
        print(f"进入: {context.stage_name}")
    
    def after_stage(self, context):
        print(f"退出: {context.stage_name}, 结果: {context.result}")

# 使用装饰器添加AOP能力
@aop_class
class MyApp:
    @stage
    def process(self, data):
        return f"处理 {data}"

# 使用
app = MyApp()
app.add_feature(LoggingFeature())
result = app.process("数据")
```

### 2. 继承方式（传统方式）

```python
from aoplib import stage, Feature, AOPClass

# 继承AOPClass
class MyApp(AOPClass):
    @stage
    def process(self, data):
        return f"处理 {data}"

# 使用
app = MyApp()
app.add_feature(LoggingFeature())
result = app.process("数据")
```

**两种方式对比**：

| 特性 | @aop_class装饰器 | 继承AOPClass |
|------|-----------------|--------------|
| 继承链占用 | ❌ 不占用 | ✅ 占用 |
| 改造已有类 | ✅ 容易 | ❌ 需要重构 |
| 代码简洁度 | ✅ 更简洁 | 一般 |
| 多重继承兼容 | ✅ 友好 | ⚠️ 可能冲突 |

### 3. 运行示例

```bash
# 简单日志示例
PYTHONPATH=. python3 examples/simple_logging.py

# Feature共享数据示例
PYTHONPATH=. python3 examples/shared_data.py

# Stage特定处理器示例（推荐查看）
PYTHONPATH=. python3 examples/stage_specific_handlers.py

# 多Stage处理器示例
PYTHONPATH=. python3 examples/multi_stage_handler.py

# 通配符匹配示例（推荐查看）
PYTHONPATH=. python3 examples/wildcard_stage.py
```

## Feature开发模板

### 1. 通用处理器（处理所有stage）

```python
class MyFeature(Feature):
    def __init__(self):
        super().__init__()  # 必须调用父类初始化

    def before_stage(self, context):
        # 在方法执行前做什么
        pass

    def after_stage(self, context):
        # 在方法执行后做什么
        # context.result 包含返回值
        pass
```

### 2. Stage特定处理器（针对特定stage）

```python
from aoplib import Feature, before_stage, after_stage

class MyFeature(Feature):
    def __init__(self):
        super().__init__()

    @before_stage("login")
    def handle_login_before(self, context):
        # 只在 stage 名称为 "login" 时执行
        print(f"用户登录: {context.args}")

    @after_stage("process")
    def handle_process_after(self, context):
        # 只在 stage 名称为 "process" 时执行
        print(f"处理完成: {context.result}")

    @before_stage(["create", "update", "delete"])
    def handle_crud_before(self, context):
        # 在 create、update、delete 任意一个 stage 时都会执行
        print(f"数据修改操作: {context.stage_name}")

    @before_stage("process_*")
    def handle_all_process(self, context):
        # 使用通配符：匹配所有 process_ 开头的 stage
        print(f"处理 {context.stage_name}")

    @after_stage("*_data")
    def handle_all_data_ops(self, context):
        # 匹配所有 _data 结尾的 stage
        print(f"数据操作: {context.stage_name}")

    # 没有特定handler的stage会被忽略
```

**对比**：

| 方式 | 适用场景 | 示例 |
|------|---------|------|
| 通用处理器 | 所有stage都需要相同逻辑 | 日志、计时 |
| 单个stage处理器 | 某个stage需要特殊逻辑 | `@before_stage("login")` |
| 多个stage处理器 | 一组stage需要相同逻辑 | `@before_stage(["create", "update", "delete"])` |
| 通配符处理器 | 匹配一类stage名称模式 | `@before_stage("process_*")` |
| 混合使用 | 部分stage特殊处理，其他使用通用逻辑 | 精确 + 通配符 + 通用 |

**通配符规则**：
- `*` - 匹配任意数量的任意字符
- `?` - 匹配单个任意字符
- 精确匹配优先级 > 通配符匹配 > 通用处理器

### 3. 混合使用（推荐模式）

```python
class LoggingFeature(Feature):
    def __init__(self):
        super().__init__()

    @before_stage("login")
    def log_login(self, context):
        # login stage 特殊处理
        print(f"[安全] 登录尝试: {context.args[0]}")

    @after_stage("delete_user")
    def log_deletion(self, context):
        # delete_user stage 特殊处理
        print(f"[警告] 用户删除: {context.result}")

    def before_stage(self, context):
        # 其他所有stage的通用处理
        print(f"[LOG] {context.stage_name} 开始")

    def after_stage(self, context):
        # 其他所有stage的通用处理
        print(f"[LOG] {context.stage_name} 完成")
```

**执行规则**：
- 如果有 `@before_stage(stage_name)` 装饰的方法，**只执行**装饰的方法
- 如果没有特定装饰器，**执行**通用 `before_stage()` 方法
- `after_stage` 同理

## Feature启用/禁用

```python
# 创建并添加Feature
feature = LoggingFeature()
app.add_feature(feature)

# 禁用Feature（不会被调用）
feature.disable()
app.process("data")  # 无日志输出

# 重新启用Feature
feature.enable()
app.process("data")  # 有日志输出

# 查询状态
if feature.is_enabled():
    print("Feature已启用")
```

## StageContext属性

- `stage_name`: stage名称
- `instance`: 对象实例(self)
- `method`: 原始方法
- `args`: 位置参数
- `kwargs`: 关键字参数
- `result`: 返回值(after_stage时有效)
- `exception`: 异常对象(如有)
- `data`: Feature共享数据字典(Dict[str, Any])

## Feature共享数据

Feature之间可以通过 `context.data` 字典共享数据：

```python
class TimingFeature(Feature):
    def before_stage(self, context):
        context.data['start_time'] = time.time()
    
    def after_stage(self, context):
        elapsed = time.time() - context.data['start_time']
        context.data['elapsed_time'] = elapsed  # 供其他Feature使用

class LoggingFeature(Feature):
    def after_stage(self, context):
        # 读取Timing存储的数据
        elapsed = context.data.get('elapsed_time')
        if elapsed:
            print(f"耗时: {elapsed:.4f}秒")
```

**优势**:
- Feature协作：一个Feature提供数据，另一个使用
- 避免污染instance：不在对象上添加临时属性
- 数据隔离：每次调用的data独立，不会相互干扰

