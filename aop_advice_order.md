# AOP 通知执行顺序详解

## 标准 AOP 通知类型和执行顺序

### 完整执行流程

```
┌─────────────────────────────────────────────────────┐
│  方法调用: service.calculate(100)                    │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  ① BEFORE_METHOD                                    │
│     - 方法执行前的处理                                │
│     - 可以访问参数                                    │
│     - 不能修改返回值（还没有）                         │
│     - 用途：验证、日志、准备                          │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  ② 执行原方法                                        │
│     result = calculate(100)                         │
└─────────────────────────────────────────────────────┘
         ↓ 成功                          ↓ 异常
┌──────────────────┐         ┌───────────────────────┐
│  ③ AROUND_METHOD │         │  ③' ON_METHOD_        │
│     _RETURN      │         │     EXCEPTION         │
│  - 可以修改返回值 │         │  - 处理异常            │
│  - 用途：缓存、   │         │  - 可以抑制异常        │
│    转换、增强    │         │  - 可以替换异常        │
└──────────────────┘         └───────────────────────┘
         ↓                              ↓
┌─────────────────────────────────────────────────────┐
│  ④ AFTER_METHOD                                     │
│     - 方法执行后的处理                                │
│     - 可以访问最终返回值                              │
│     - 不能修改返回值                                  │
│     - 用途：日志、监控、通知                          │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  ⑤ 返回给调用者                                      │
│     return result                                   │
└─────────────────────────────────────────────────────┘
```

## 详细说明

### 1. BEFORE_METHOD（前置通知）

**执行时机**: 方法调用前

**能力**:
- ✓ 访问方法参数
- ✓ 访问实例 (self)
- ✗ 不能访问返回值（还未执行）
- ✗ 不能修改返回值

**典型用途**:
```python
@before_method
def validate_params(self, context):
    """参数验证"""
    if context.args[0] < 0:
        raise ValueError("参数不能为负数")

@before_method
def log_entry(self, context):
    """记录方法调用"""
    print(f"调用 {context.name}，参数: {context.args}")
```

### 2. 原方法执行

执行被拦截的方法，获得返回值或异常。

### 3. AROUND_METHOD_RETURN（环绕返回通知）

**执行时机**: 方法执行成功后、返回前

**能力**:
- ✓ 访问方法参数
- ✓ 访问原始返回值
- ✓ **可以修改返回值** ⭐
- ✓ 访问实例 (self)

**典型用途**:
```python
@around_method_return
def cache_result(self, context):
    """使用缓存替换返回值"""
    cache_key = f"{context.name}:{context.args}"
    if cache_key in self.cache:
        context.result = self.cache[cache_key]  # 修改返回值
    else:
        self.cache[cache_key] = context.result

@around_method_return
def format_result(self, context):
    """格式化返回值"""
    context.result = f"¥{context.result:.2f}"  # 修改返回值
```

### 3'. ON_METHOD_EXCEPTION（异常通知）

**执行时机**: 方法抛出异常时

**能力**:
- ✓ 访问异常对象
- ✓ 访问方法参数
- ✓ 可以抑制异常（不再抛出）
- ✓ 可以替换异常

**典型用途**:
```python
@on_method_exception
def handle_error(self, context):
    """异常处理"""
    print(f"错误: {context.exception}")
    if isinstance(context.exception, ValueError):
        context.suppress_exception()  # 抑制异常
        context.result = 0  # 设置默认值

@on_method_exception
def convert_exception(self, context):
    """转换异常"""
    if isinstance(context.exception, ValueError):
        context.replace_exception(
            BusinessError("业务错误")
        )
```

### 4. AFTER_METHOD（后置通知）

**执行时机**: 方法执行后（无论成功或失败）

**能力**:
- ✓ 访问方法参数
- ✓ 访问最终返回值（经过 around 修改后）
- ✓ 访问实例 (self)
- ✗ **不能修改返回值** ⭐

**典型用途**:
```python
@after_method
def log_result(self, context):
    """记录返回值（只读）"""
    print(f"{context.name} 返回: {context.result}")

@after_method
def send_notification(self, context):
    """发送通知"""
    notify_service.send(f"操作完成: {context.name}")

@after_method
def update_metrics(self, context):
    """更新统计"""
    self.call_count += 1
```

## 关键区别对比

| 通知类型 | 能否修改返回值 | 执行时机 | 主要用途 |
|---------|--------------|---------|---------|
| **before_method** | ✗ 没有返回值 | 方法前 | 验证、准备 |
| **around_method_return** | ✓ **可以修改** | 方法后、返回前 | 缓存、转换、增强 |
| **after_method** | ✗ **只读取** | 方法后 | 日志、监控、通知 |
| **on_method_exception** | - | 异常时 | 异常处理 |

## 完整示例

```python
from aoplib import Aspect, before_method, around_method_return, after_method
from aoplib.context import JoinMethodContext

class DemoAspect(Aspect):
    
    @before_method
    def step1_before(self, context: JoinMethodContext):
        print(f"1️⃣ [before] 调用 {context.method.__name__}")
        print(f"   参数: {context.args}")
    
    @around_method_return
    def step2_around(self, context: JoinMethodContext):
        print(f"3️⃣ [around] 原返回值: {context.result}")
        context.result = context.result * 2  # 修改返回值
        print(f"   修改后: {context.result}")
    
    @after_method
    def step3_after(self, context: JoinMethodContext):
        print(f"4️⃣ [after] 最终返回值: {context.result}")
        print(f"   (只能读取，不能修改)")

# 使用
class Calculator:
    @join_method
    def add(self, a, b):
        result = a + b
        print(f"2️⃣ [原方法] 计算结果: {result}")
        return result

calc = Calculator()
add_aspect(calc, DemoAspect())

result = calc.add(10, 20)
print(f"5️⃣ [调用者] 收到: {result}")

# 输出:
# 1️⃣ [before] 调用 add
#    参数: (10, 20)
# 2️⃣ [原方法] 计算结果: 30
# 3️⃣ [around] 原返回值: 30
#    修改后: 60
# 4️⃣ [after] 最终返回值: 60
#    (只能读取，不能修改)
# 5️⃣ [调用者] 收到: 60
```

## 多个切面的执行顺序

当有多个切面时:

```python
add_aspect(obj, AspectA())  # 先添加
add_aspect(obj, AspectB())  # 后添加

# 执行顺序:
# before:  A → B
# around:  A → B  (依次修改返回值)
# after:   A → B  (都观察最终值)
```

```
AspectA.before
  ↓
AspectB.before
  ↓
原方法执行
  ↓
AspectA.around (修改: result = 30 → 60)
  ↓
AspectB.around (修改: result = 60 → 120)
  ↓
AspectA.after (读取: 120)
  ↓
AspectB.after (读取: 120)
  ↓
返回: 120
```

## Spring AOP 对比

与 Spring AOP 的对应关系:

| Spring AOP | 本框架 | 说明 |
|-----------|--------|------|
| `@Before` | `@before_method` | 前置通知 |
| `@AfterReturning` | `@around_method_return` | 返回后通知（可修改） |
| `@After` | `@after_method` | 后置通知（只读） |
| `@AfterThrowing` | `@on_method_exception` | 异常通知 |
| `@Around` | - | 完全环绕（本框架拆分为多个） |

## 最佳实践

### 1. 选择正确的通知类型

```python
# ✓ 需要修改返回值 → around_method_return
@around_method_return
def add_tax(self, context):
    context.result *= 1.1

# ✓ 只需观察 → after_method
@after_method
def log_result(self, context):
    logger.info(f"Result: {context.result}")

# ✓ 验证参数 → before_method
@before_method
def validate(self, context):
    if context.args[0] < 0:
        raise ValueError()
```

### 2. 避免在 after 中修改

```python
# ❌ 错误：在 after 中修改无效
@after_method
def try_modify(self, context):
    context.result = 999  # 无效！不会影响返回值

# ✓ 正确：使用 around
@around_method_return
def modify_correctly(self, context):
    context.result = 999  # 有效！
```

### 3. around 中的修改会被 after 看到

```python
@around_method_return
def double_it(self, context):
    context.result *= 2

@after_method
def log_it(self, context):
    # 这里看到的是翻倍后的值
    print(context.result)
```

## 总结

**执行顺序记忆口诀**:
```
前(before) → 执行 → 环绕改(around) → 后观察(after) → 返回
```

**关键点**:
1. `around_method_return` 在 `after_method` **之前**执行
2. `around_method_return` **可以修改**返回值
3. `after_method` **只能读取**最终返回值
4. `after_method` 看到的是 `around_method_return` 修改后的值

