"""
演示类级别和实例级别的Features混合使用
"""
from aoplib.feature import Feature
from aoplib.stage import stage


class LogFeature(Feature):
    """日志Feature（类级别）"""
    def __init__(self, prefix="[LOG]"):
        super().__init__()
        self.prefix = prefix
    
    def before_stage(self, context):
        print(f"{self.prefix} 进入stage: {context.stage_name}")
    
    def after_stage(self, context):
        print(f"{self.prefix} 离开stage: {context.stage_name}")


class TimingFeature(Feature):
    """计时Feature（实例级别）"""
    def __init__(self):
        super().__init__()
        self.start_time = None
    
    def before_stage(self, context):
        import time
        self.start_time = time.time()
        print(f"[TIMING] 开始计时: {context.stage_name}")
    
    def after_stage(self, context):
        import time
        elapsed = time.time() - self.start_time
        print(f"[TIMING] 耗时: {elapsed:.4f}秒")


class DataProcessor:
    """数据处理器 - 使用类级别Features"""
    
    # 类级别的features - 所有实例共享
    _features = [
        LogFeature(prefix="[类级别]")
    ]
    
    def __init__(self, name):
        self.name = name
        # 实例级别的features - 每个实例独立
        self._features = [
            TimingFeature()
        ]
    
    @stage("处理数据")
    def process(self, data):
        """处理数据"""
        print(f"[{self.name}] 正在处理: {data}")
        return data.upper()


class AdvancedProcessor:
    """高级处理器 - 同时使用类级别和实例级别Features"""
    
    # 类级别 - 所有实例都会记录日志
    _features = [
        LogFeature(prefix="[全局日志]")
    ]
    
    def __init__(self, enable_timing=False):
        # 实例级别 - 可选功能
        self._features = []
        if enable_timing:
            self._features.append(TimingFeature())
    
    @stage("计算")
    def calculate(self, x, y):
        """计算"""
        result = x + y
        print(f"计算结果: {x} + {y} = {result}")
        return result


# 示例1：基础使用
print("=" * 50)
print("示例1：类级别 + 实例级别Features")
print("=" * 50)

processor = DataProcessor("处理器1")
result = processor.process("hello")
print(f"返回值: {result}\n")


# 示例2：多个实例共享类级别Features
print("=" * 50)
print("示例2：多个实例共享类级别Features")
print("=" * 50)

proc1 = AdvancedProcessor(enable_timing=True)
proc2 = AdvancedProcessor(enable_timing=False)

print("处理器1（启用计时）：")
proc1.calculate(10, 20)

print("\n处理器2（禁用计时）：")
proc2.calculate(30, 40)


# 示例3：动态添加实例Features
print("\n" + "=" * 50)
print("示例3：动态添加实例Features")
print("=" * 50)

proc3 = DataProcessor("处理器3")
# 动态添加一个新Feature到实例
proc3._features.append(LogFeature(prefix="[实例新增]"))

proc3.process("world")


# 示例4：只有类级别Features的情况
print("\n" + "=" * 50)
print("示例4：只有类级别Features")
print("=" * 50)

class SimpleProcessor:
    """只使用类级别Features"""
    _features = [LogFeature(prefix="[简单处理器]")]
    
    @stage("转换")
    def transform(self, text):
        return text.lower()

simple = SimpleProcessor()
result = simple.transform("HELLO WORLD")
print(f"返回值: {result}")


# 示例5：Feature执行顺序
print("\n" + "=" * 50)
print("示例5：Feature执行顺序（类级别优先）")
print("=" * 50)

class OrderDemo:
    _features = [LogFeature(prefix="[1.类级别]")]
    
    def __init__(self):
        self._features = [LogFeature(prefix="[2.实例级别]")]
    
    @stage("测试顺序")
    def test(self):
        print("    [核心逻辑] 执行方法")

demo = OrderDemo()
demo.test()

print("\n说明：")
print("- 类级别Features先被收集")
print("- 实例级别Features后被收集")
print("- before_stage按收集顺序执行")
print("- after_stage按相反顺序执行")

