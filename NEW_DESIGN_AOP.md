# 新AOP设计 - 基于Spring AOP风格

## 设计理念

采用Spring AOP的命名风格，更简洁、更符合业界标准。

## 通知类型（Advice Types）

### 方法通知

| 通知类型 | 装饰器 | 执行时机 | 能力 | Spring对应 |
|---------|-------|---------|-----|-----------|
| **Before** | `@before` | 方法执行前 | 访问参数 | `@Before` |
| **After** | `@after` | 方法执行后（无论成功失败） | 访问结果/异常 | `@After` |
| **AfterReturning** | `@after_returning` | 方法成功返回后 | 访问&修改返回值 | `@AfterReturning` |
| **AfterThrowing** | `@after_throwing` | 方法抛出异常后 | 处理异常 | `@AfterThrowing` |
| **Around** | `@around` | 完全控制方法执行 | 完全控制 | `@Around` |

### 属性通知

| 通知类型 | 装饰器 | 执行时机 | 能力 |
|---------|-------|---------|-----|
| **BeforeSet** | `@before_set` | 属性设置前 | 验证、可跳过 |
| **AfterSet** | `@after_set` | 属性设置后 | 通知、记录 |
| **AfterGet** | `@after_get` | 属性读取后 | 转换返回值 |
| **BeforeInit** | `@before_init` | 属性初始化时 | 设置默认值 |
| **BeforeDelete** | `@before_delete` | 属性删除前 | 验证、可跳过 |
| **AfterDelete** | `@after_delete` | 属性删除后 | 清理、通知 |

## 执行顺序

### 方法成功执行

```
┌──────────────────────┐
│  ① Before            │  访问参数
└──────────────────────┘
         ↓
┌──────────────────────┐
│  ② 执行原方法         │  获得返回值
└──────────────────────┘
         ↓
┌──────────────────────┐
│  ③ AfterReturning    │  可以修改返回值 ⭐
└──────────────────────┘
         ↓
┌──────────────────────┐
│  ④ After             │  最终处理
└──────────────────────┘
         ↓
    返回给调用者
```

### 方法抛出异常

```
┌──────────────────────┐
│  ① Before            │
└──────────────────────┘
         ↓
┌──────────────────────┐
│  ② 执行原方法         │  抛出异常
└──────────────────────┘
         ↓
┌──────────────────────┐
│  ③ AfterThrowing     │  处理异常
└──────────────────────┘
         ↓
┌──────────────────────┐
│  ④ After             │  最终处理
└──────────────────────┘
         ↓
  抛出异常（除非被抑制）
```

## 快速示例

### 方法拦截

```python
from aoplib import Aspect, before, after_returning, after_throwing, after
from aoplib import join_method, add_aspect

class LogAspect(Aspect):
    """日志切面"""
    
    @before
    def log_entry(self, context):
        """方法调用前"""
        print(f"→ 调用 {context.method.__name__}{context.args}")
    
    @after_returning
    def log_result(self, context):
        """成功返回时"""
        print(f"← 返回 {context.result}")
    
    @after_throwing
    def log_error(self, context):
        """异常时"""
        print(f"✗ 异常 {context.exception}")
    
    @after
    def log_finally(self, context):
        """最终"""
        print(f"■ 完成")


class Calculator:
    @join_method
    def add(self, a, b):
        return a + b


# 使用
calc = Calculator()
add_aspect(calc, LogAspect())

result = calc.add(10, 20)
# 输出:
# → 调用 add(10, 20)
# ← 返回 30
# ■ 完成
```

### 属性拦截

```python
from aoplib import Aspect, before_set, after_set, after_get
from aoplib import join_property, add_aspect

class ValidationAspect(Aspect):
    """验证切面"""
    
    @before_set
    def validate(self, context):
        """设置前验证"""
        if context.value < 0:
            print(f"✗ 拒绝负数")
            context.skip_setter()  # 跳过设置
    
    @after_get
    def encrypt(self, context):
        """读取后加密"""
        if context.method.__name__ == "password":
            return "***" + context.value[-4:]
        return context.value


class User:
    @join_property
    def age(self):
        pass
    
    @join_property
    def password(self):
        pass


# 使用
user = User()
add_aspect(user, ValidationAspect())

user.age = 25   # ✓ 通过
user.age = -5   # ✗ 拒绝，age保持25

user.password = "secret123"
print(user.password)  # 输出: ***t123
```

## 与旧版本对比

| 旧版本 | 新版本 | 说明 |
|--------|--------|------|
| `before_method` | `before` | 更简洁 |
| `after_method` | `after` | 更简洁 |
| `around_method_return` | `after_returning` | 更准确 |
| `on_method_exception` | `after_throwing` | Spring风格 |
| - | `around` | 新增 |
| `before_property_set` | `before_set` | 更简洁 |
| `after_property_set` | `after_set` | 更简洁 |
| `around_property_get` | `after_get` | 更准确 |
| `around_property_init` | `before_init` | 更准确 |

## 核心改进

### 1. 更清晰的语义

```python
# 旧版本：不够清晰
@around_method_return  # 环绕？还是返回后？
def modify(ctx):
    ctx.result *= 2

# 新版本：清晰明确
@after_returning  # 明确是"返回后"
def modify(ctx):
    ctx.result *= 2
```

### 2. 标准化命名

采用Spring AOP的命名规范，降低学习成本。

### 3. 更准确的分类

- `after_returning`：成功返回后（可修改返回值）
- `after_throwing`：抛出异常后（处理异常）
- `after`：最终执行（无论成功失败）

### 4. 简洁的API

```python
# 新版本更简洁
from aoplib import before, after, after_returning

@before
def validate(ctx): ...

@after_returning
def cache(ctx): ...

@after
def log(ctx): ...
```

## 迁移指南

```python
# 旧代码
from aoplib import before_method, after_method, around_method_return

@before_method
def before_hook(ctx): pass

@after_method  
def after_hook(ctx): pass

@around_method_return
def modify_result(ctx): pass


# 新代码
from aoplib import before, after, after_returning

@before
def before_hook(ctx): pass

@after
def after_hook(ctx): pass

@after_returning
def modify_result(ctx): pass
```

## 完整的通知生命周期

```python
class CompleteAspect(Aspect):
    """演示完整的通知生命周期"""
    
    @before
    def step1(self, ctx):
        print("1. Before - 方法执行前")
    
    # 如果成功:
    @after_returning
    def step2a(self, ctx):
        print("2a. AfterReturning - 成功返回")
        ctx.result *= 2  # 可以修改
    
    # 如果异常:
    @after_throwing
    def step2b(self, ctx):
        print("2b. AfterThrowing - 抛出异常")
        ctx.suppress_exception()  # 可以抑制
    
    # 无论如何:
    @after
    def step3(self, ctx):
        print("3. After - 最终执行")
```

## 总结

新设计的优势：

1. ✅ **简洁** - 更短的装饰器名
2. ✅ **标准** - 符合Spring AOP规范
3. ✅ **清晰** - 语义更明确
4. ✅ **强大** - 功能更完善
5. ✅ **易学** - 降低学习成本

核心思想：**简洁、标准、清晰**

