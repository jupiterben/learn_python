"""
演示Feature管理功能：基于uniq_id的添加、删除、查询
"""
from aoplib.feature import Feature, add_feature, remove_feature, get_feature, has_feature
from aoplib.stage import stage


class LogFeature(Feature):
    """日志Feature"""
    def __init__(self, level="INFO"):
        super().__init__(uniq_id="log")
        self.level = level
    
    def before_stage(self, context):
        print(f"[{self.level}] 进入stage: {context.stage_name}")


class CacheFeature(Feature):
    """缓存Feature"""
    def __init__(self):
        super().__init__(uniq_id="cache")
        self.cache = {}
    
    def before_stage(self, context):
        print(f"[CACHE] 检查缓存: {context.stage_name}")


class MetricsFeature(Feature):
    """监控Feature"""
    def __init__(self):
        super().__init__(uniq_id="metrics")
    
    def after_stage(self, context):
        print(f"[METRICS] 记录指标: {context.stage_name}")


class DataProcessor:
    def __init__(self):
        self._features = []
    
    @stage("处理数据")
    def process(self, data):
        print(f"    [核心] 处理数据: {data}")
        return data


# 示例1：基础添加和删除
print("=" * 60)
print("示例1：基础添加和删除")
print("=" * 60)

processor = DataProcessor()

# 添加Features
log_feature = LogFeature(level="DEBUG")
cache_feature = CacheFeature()

result1 = add_feature(processor, log_feature)
print(f"添加LogFeature: {result1}")  # True

result2 = add_feature(processor, cache_feature)
print(f"添加CacheFeature: {result2}")  # True

print(f"\n当前Features数量: {len(processor._features)}")
processor.process("test1")


# 示例2：防止重复添加（相同uniq_id）
print("\n" + "=" * 60)
print("示例2：防止重复添加")
print("=" * 60)

# 尝试添加相同uniq_id的Feature
another_log = LogFeature(level="INFO")
result3 = add_feature(processor, another_log)
print(f"添加相同uniq_id的LogFeature: {result3}")  # False

print(f"Features数量未变: {len(processor._features)}")


# 示例3：替换已存在的Feature
print("\n" + "=" * 60)
print("示例3：替换已存在的Feature")
print("=" * 60)

# 用replace=True替换
new_log = LogFeature(level="ERROR")
result4 = add_feature(processor, new_log, replace=True)
print(f"替换LogFeature: {result4}")  # True

print(f"Features数量保持: {len(processor._features)}")
print("\n查看新的日志级别：")
processor.process("test2")


# 示例4：通过uniq_id字符串删除
print("\n" + "=" * 60)
print("示例4：通过uniq_id删除")
print("=" * 60)

result5 = remove_feature(processor, "cache")  # 使用字符串
print(f"删除CacheFeature: {result5}")  # True

print(f"删除后Features数量: {len(processor._features)}")
processor.process("test3")

# 尝试删除不存在的
result6 = remove_feature(processor, "not_exist")
print(f"\n删除不存在的Feature: {result6}")  # False


# 示例5：通过Feature对象删除
print("\n" + "=" * 60)
print("示例5：通过Feature对象删除")
print("=" * 60)

metrics = MetricsFeature()
add_feature(processor, metrics)
print(f"添加MetricsFeature")
processor.process("test4")

result7 = remove_feature(processor, metrics)  # 使用Feature对象
print(f"\n删除MetricsFeature: {result7}")  # True
print(f"删除后Features数量: {len(processor._features)}")


# 示例6：查询Feature
print("\n" + "=" * 60)
print("示例6：查询Feature")
print("=" * 60)

# 检查是否存在
exists1 = has_feature(processor, "log")
exists2 = has_feature(processor, "cache")
print(f"存在LogFeature: {exists1}")    # True
print(f"存在CacheFeature: {exists2}")  # False

# 获取Feature对象
log_feat = get_feature(processor, "log")
if log_feat:
    print(f"\n获取到LogFeature，级别: {log_feat.level}")


# 示例7：类级别和实例级别混合管理
print("\n" + "=" * 60)
print("示例7：类级别和实例级别混合管理")
print("=" * 60)

class MixedProcessor:
    _features = []  # 类级别
    
    def __init__(self):
        self._features = []  # 实例级别
    
    @stage("混合处理")
    def process(self, data):
        print(f"    [核心] 处理: {data}")

# 类级别添加
add_feature(MixedProcessor, LogFeature(level="CLASS"))
print("类级别添加LogFeature")

# 实例级别添加
proc1 = MixedProcessor()
proc2 = MixedProcessor()

add_feature(proc1, MetricsFeature())
print("实例1添加MetricsFeature")

print("\n实例1处理：")
proc1.process("data1")

print("\n实例2处理（没有实例级别Features）：")
proc2.process("data2")


# 示例8：动态管理Feature
print("\n" + "=" * 60)
print("示例8：动态管理Feature")
print("=" * 60)

class DynamicProcessor:
    def __init__(self):
        self._features = []
    
    def enable_logging(self, level="INFO"):
        """启用日志"""
        if not has_feature(self, "log"):
            add_feature(self, LogFeature(level))
            return True
        return False
    
    def disable_logging(self):
        """禁用日志"""
        return remove_feature(self, "log")
    
    def enable_cache(self):
        """启用缓存"""
        if not has_feature(self, "cache"):
            add_feature(self, CacheFeature())
            return True
        return False
    
    def get_feature_list(self):
        """获取所有Feature的uniq_id列表"""
        return [f.uniq_id for f in self._features]
    
    @stage("动态处理")
    def process(self, data):
        print(f"    [核心] 处理: {data}")

dyn_proc = DynamicProcessor()

print("初始状态：")
print(f"Features: {dyn_proc.get_feature_list()}")

print("\n启用日志：")
dyn_proc.enable_logging("DEBUG")
print(f"Features: {dyn_proc.get_feature_list()}")
dyn_proc.process("test1")

print("\n启用缓存：")
dyn_proc.enable_cache()
print(f"Features: {dyn_proc.get_feature_list()}")
dyn_proc.process("test2")

print("\n禁用日志：")
dyn_proc.disable_logging()
print(f"Features: {dyn_proc.get_feature_list()}")
dyn_proc.process("test3")


# 示例9：替换Feature的实际应用
print("\n" + "=" * 60)
print("示例9：替换Feature实现热更新")
print("=" * 60)

class ConfigurableProcessor:
    def __init__(self):
        self._features = []
        add_feature(self, LogFeature(level="INFO"))
    
    def update_log_level(self, new_level):
        """更新日志级别"""
        new_log = LogFeature(level=new_level)
        result = add_feature(self, new_log, replace=True)
        print(f"更新日志级别到 {new_level}: {result}")
    
    @stage("配置处理")
    def process(self, data):
        print(f"    [核心] 处理: {data}")

config_proc = ConfigurableProcessor()

print("初始日志级别（INFO）：")
config_proc.process("test1")

print("\n更新日志级别到DEBUG：")
config_proc.update_log_level("DEBUG")
config_proc.process("test2")

print("\n更新日志级别到ERROR：")
config_proc.update_log_level("ERROR")
config_proc.process("test3")


print("\n" + "=" * 60)
print("总结")
print("=" * 60)
print("""
Feature管理功能：
1. add_feature(obj, feature, replace=False)
   - 根据uniq_id防止重复添加
   - replace=True时可以替换已存在的Feature
   
2. remove_feature(obj, feature_or_id)
   - 支持Feature对象或uniq_id字符串
   - 返回bool表示是否成功

3. get_feature(obj, feature_id)
   - 根据uniq_id获取Feature对象
   - 未找到返回None

4. has_feature(obj, feature_or_id)
   - 检查Feature是否存在
   - 支持Feature对象或uniq_id字符串
""")

