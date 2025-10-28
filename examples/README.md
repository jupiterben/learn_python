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

### 2. 运行示例

```bash
# 简单日志示例（继承方式）
PYTHONPATH=. python3 examples/simple_logging.py

# 装饰器方式示例（推荐）
PYTHONPATH=. python3 examples/decorator_style.py
```

## Feature开发模板

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

