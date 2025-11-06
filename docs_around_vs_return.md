# AOP通知类型对比：Around vs After/Return

## 1. 概念区别

### Around（环绕通知）
- **目的**：拦截并**修改**目标值
- **能力**：可以读取和修改返回值/属性值
- **执行时机**：在目标操作后、返回给调用者前
- **典型用途**：数据转换、结果增强、缓存替换

### After/Return（后置通知）
- **目的**：观察目标值，执行**副作用**操作
- **能力**：只能读取返回值，不能修改
- **执行时机**：在目标操作完成后
- **典型用途**：日志记录、监控统计、事件发布

---

## 2. 在当前框架中的对应

| 类型 | 方法通知 | 属性通知 | 说明 |
|------|---------|---------|------|
| **Before** | `before_method` | `before_property_set` | 执行前，可阻止操作 |
| **After** | `after_method` | `after_property_set` | 执行后，仅观察 |
| **Around** | `around_method_return` | `around_property_get`<br>`around_property_init` | 可修改值 |
| **Exception** | `on_method_exception` | - | 异常处理 |

---

## 3. 使用示例对比

### Around - 修改返回值

```python
class CacheAspect(Aspect):
    @around_method_return
    def use_cache(self, context: JoinMethodContext):
        """从缓存中获取结果，替换实际返回值"""
        cache_key = f"{context.name}:{context.args}"
        
        # 如果有缓存，替换返回值
        if cache_key in self.cache:
            print("[缓存] 使用缓存值")
            context.result = self.cache[cache_key]
        else:
            # 保存到缓存
            self.cache[cache_key] = context.result


class DataTransformAspect(Aspect):
    @around_property_get
    def encrypt_data(self, context: JoinPropContext):
        """读取属性时加密"""
        if context.method.__name__ == "password":
            return "***" + context.value[-4:]  # 只显示后4位
        return context.value
```

### After - 观察和记录

```python
class LogAspect(Aspect):
    @after_method
    def log_result(self, context: JoinMethodContext):
        """记录方法返回值，不修改"""
        print(f"[日志] {context.name} 返回: {context.result}")
        # 不能修改 context.result

    
class MetricsAspect(Aspect):
    @after_property_set
    def track_change(self, context: JoinPropContext):
        """追踪属性变化"""
        self.metrics[context.name] = self.metrics.get(context.name, 0) + 1
        print(f"[统计] {context.name} 已修改 {self.metrics[context.name]} 次")
```

---

## 4. 执行顺序

```python
@join_method
def calculate(self, x):
    return x * 2

# 执行顺序：
1. before_method          # 方法执行前
2. [原方法执行]           # calculate() 执行
3. around_method_return   # 可以修改返回值 ⭐
4. after_method          # 只能观察返回值
```

---

## 5. 典型应用场景

### Around 适用场景
- ✅ **缓存替换**：用缓存值替换真实返回值
- ✅ **数据转换**：JSON序列化、加密解密
- ✅ **结果增强**：给返回值添加额外信息
- ✅ **默认值处理**：返回None时替换为默认值
- ✅ **权限过滤**：根据权限过滤返回的数据

### After/Return 适用场景
- ✅ **日志记录**：记录方法调用和返回值
- ✅ **监控统计**：性能监控、调用次数统计
- ✅ **事件发布**：方法完成后发布事件
- ✅ **审计追踪**：记录谁在什么时候调用了什么
- ✅ **通知机制**：操作完成后发送通知

---

## 6. 代码示例

### 示例1：Around修改返回值

```python
class PriceAspect(Aspect):
    """价格处理切面"""
    
    @around_method_return
    def apply_discount(self, context: JoinMethodContext):
        """给价格打折"""
        if context.method.__name__ == "get_price":
            original_price = context.result
            discounted_price = original_price * 0.8  # 8折
            print(f"[折扣] 原价: {original_price}, 折后: {discounted_price}")
            context.result = discounted_price  # 修改返回值
```

### 示例2：After观察返回值

```python
class AuditAspect(Aspect):
    """审计切面"""
    
    @after_method
    def log_operation(self, context: JoinMethodContext):
        """记录操作（不修改返回值）"""
        self.audit_log.append({
            'method': context.name,
            'args': context.args,
            'result': context.result,  # 只读取
            'timestamp': time.time()
        })
        # 不修改 context.result
```

---

## 7. 何时使用哪个？

| 需求 | 使用 |
|------|------|
| 需要修改返回值/属性值 | `around_*` |
| 只需观察，不修改 | `after_*` |
| 需要缓存功能 | `around_method_return` |
| 需要数据转换 | `around_*` |
| 只是记录日志 | `after_method` |
| 发送通知/事件 | `after_method` |
| 统计监控 | `after_method` |

---

## 8. 性能考虑

```python
# Around - 每个handler都可能修改值
@around_method_return
def handler1(ctx):
    ctx.result = transform1(ctx.result)  # 第一次转换

@around_method_return
def handler2(ctx):
    ctx.result = transform2(ctx.result)  # 第二次转换
# 结果会被多次转换

# After - 只观察，不产生额外的修改开销
@after_method
def handler1(ctx):
    log(ctx.result)  # 只读取

@after_method
def handler2(ctx):
    metric(ctx.result)  # 只读取
# 性能开销更小
```

---

## 总结

- **Around** = 可以**改变**目标值，用于转换、增强、替换
- **After** = 只能**观察**目标值，用于日志、监控、通知
- **Around** 更强大但应谨慎使用，避免多个切面相互干扰
- **After** 更安全，适合只需要读取结果的场景



