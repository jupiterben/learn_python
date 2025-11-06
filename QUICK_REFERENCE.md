# AOP框架快速参考

## 通知装饰器

### 方法通知

```python
from aoplib import before, after, after_returning, after_throwing

@before                  # 方法执行前
def validate(ctx): ...

@after_returning         # 成功返回后（可修改返回值）
def cache(ctx): ...

@after_throwing          # 抛出异常后
def handle_error(ctx): ...

@after                   # 最终执行（无论成功失败）
def log(ctx): ...
```

### 属性通知

```python
from aoplib import before_set, after_set, after_get, before_init

@before_set              # 属性设置前（可跳过）
def validate(ctx): ...

@after_set               # 属性设置后
def log(ctx): ...

@after_get               # 属性读取后（可转换）
def encrypt(ctx): ...

@before_init             # 属性初始化
def set_default(ctx): ...
```

## 执行顺序

### 成功执行

```
before → 原方法 → after_returning → after
```

### 异常执行

```
before → 原方法 → after_throwing → after
```

## 快速示例

```python
from aoplib import Aspect, before, after_returning, join_method, add_aspect

class LogAspect(Aspect):
    @before
    def log_entry(self, ctx):
        print(f"→ {ctx.method.__name__}{ctx.args}")
    
    @after_returning
    def log_result(self, ctx):
        print(f"← {ctx.result}")
        ctx.result *= 2  # 可以修改返回值

class Calculator:
    @join_method
    def add(self, a, b):
        return a + b

# 使用
calc = Calculator()
add_aspect(calc, LogAspect())
result = calc.add(10, 20)  # 输出: → add(10, 20), ← 30, 返回: 60
```

## Context属性

### JoinMethodContext

```python
ctx.method        # 方法对象
ctx.args          # 位置参数
ctx.kwargs        # 关键字参数
ctx.instance      # self
ctx.result        # 返回值（可修改）
ctx.exception     # 异常对象
ctx.suppressed    # 是否抑制异常
```

### JoinPropContext

```python
ctx.method        # 属性方法
ctx.value         # 属性值（可修改）
ctx.instance      # self
ctx.skip_set      # 跳过设置
ctx.skip_delete   # 跳过删除
```

## 常用操作

```python
# 修改返回值
@after_returning
def double(ctx):
    ctx.result *= 2

# 跳过设置
@before_set
def validate(ctx):
    if ctx.value < 0:
        ctx.skip_setter()

# 抑制异常
@after_throwing
def handle(ctx):
    ctx.suppress_exception()
    ctx.result = 0

# 转换读取值
@after_get
def encrypt(ctx):
    return "***" + ctx.value[-4:]
```

## 对应关系

| Spring AOP | 本框架 |
|-----------|--------|
| `@Before` | `@before` |
| `@After` | `@after` |
| `@AfterReturning` | `@after_returning` |
| `@AfterThrowing` | `@after_throwing` |
| `@Around` | `@around` |

