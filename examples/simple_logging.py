"""
简单日志Feature示例
"""
from aoplib import aop_class, stage, Feature


class LoggingFeature(Feature):
    """日志Feature - 记录stage执行情况"""

    def __init__(self):
        super().__init__()

    def before_stage(self, context):
        print(f"[LOG] before stage: {context.stage_name}， 输入: {context.args}")

    def after_stage(self, context):
        print(
            f"[LOG] after stage : {context.stage_name}， 输出: {context.result}")


class TimingFeature(Feature):
    """计时Feature"""

    def __init__(self):
        super().__init__()

    def before_stage(self, context):
        import time
        context.start_time = time.time()

    def after_stage(self, context):
        import time
        elapsed = time.time() - context.start_time
        print(f"[TIME] {context.stage_name} 耗时: {elapsed:.4f}秒")


@aop_class
class App():
    """示例应用"""

    def __init__(self, name):
        super().__init__()
        self.name = name

    @stage
    def initialize(self):
        """初始化"""
        return "初始化完成"

    @stage("数据处理")
    def process(self, data):
        """处理数据"""
        result = data.upper()
        return result

    @stage
    def cleanup(self):
        """清理"""
        return "清理完成"


if __name__ == "__main__":

    app2 = App("应用2")
    app2.add_feature(LoggingFeature()).add_feature(TimingFeature())
    app2.process("test data")
    app2.cleanup()
