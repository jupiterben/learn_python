"""
使用 @before_stage 和 @after_stage 装饰器为特定stage定义处理逻辑
"""
from aoplib import stage, Feature, aop_class, before_stage, after_stage


class ValidationFeature(Feature):
    """数据验证Feature - 针对不同stage有不同的验证规则"""

    def __init__(self):
        super().__init__()

    @before_stage("login")
    def validate_login(self, context):
        username = context.args[0] if context.args else None
        password = context.kwargs.get('password')
        print(
            f"[验证] 登录数据: 用户名={username}, 密码长度={len(password) if password else 0}")
        if not username or not password:
            raise ValueError("用户名和密码不能为空")

    @before_stage("process_data")
    def validate_data(self, context):
        data = context.args[0] if context.args else None
        print(f"[验证] 数据类型: {type(data).__name__}")
        if not isinstance(data, (str, int, list)):
            raise TypeError("数据类型不支持")

    @after_stage("process_data")
    def check_result(self, context):
        result_len = len(str(context.result))
        print(f"[验证] 结果长度: {result_len}")


class MetricsFeature(Feature):
    """监控Feature - 只统计特定stage"""

    def __init__(self):
        super().__init__()
        self.call_counts = {}
        self.total_time = {}

    @before_stage("process_data")
    def start_timing(self, context):
        import time
        context.data['metrics_start'] = time.time()
        print("[监控] 开始计时: process_data")

    @after_stage("process_data")
    def record_metrics(self, context):
        import time
        if 'metrics_start' in context.data:
            elapsed = time.time() - context.data['metrics_start']
            stage = context.stage_name
            self.call_counts[stage] = self.call_counts.get(stage, 0) + 1
            self.total_time[stage] = self.total_time.get(stage, 0) + elapsed
            print(
                f"[监控] {stage} 调用次数: {self.call_counts[stage]}, 总耗时: {self.total_time[stage]:.4f}秒")

    @after_stage("login")
    def log_login_success(self, context):
        print(f"[监控] 用户 {context.args[0]} 登录成功")


class LoggingFeature(Feature):
    """通用日志Feature - 处理所有未特别指定的stage"""

    def __init__(self):
        super().__init__()

    def before_stage(self, context):
        # 只有没有特定handler的stage才会执行这里
        print(f"[日志] 通用before: {context.stage_name}")

    def after_stage(self, context):
        # 只有没有特定handler的stage才会执行这里
        print(f"[日志] 通用after: {context.stage_name}")


@aop_class
class UserService:
    """用户服务"""

    def __init__(self):
        self.logged_in_user = None

    @stage
    def login(self, username, password=None):
        """登录"""
        self.logged_in_user = username
        return f"欢迎, {username}!"

    @stage
    def process_data(self, data):
        """处理数据"""
        import time
        time.sleep(0.01)  # 模拟处理时间
        return f"已处理: {data}"

    @stage
    def logout(self):
        """登出"""
        user = self.logged_in_user
        self.logged_in_user = None
        return f"{user} 已登出"


if __name__ == "__main__":
    print("=" * 60)
    print("示例：Stage特定的处理器")
    print("=" * 60)

    service = UserService()

    # 添加Features
    validation = ValidationFeature()
    metrics = MetricsFeature()
    logging = LoggingFeature()

    service.add_feature(validation)
    service.add_feature(metrics)
    service.add_feature(logging)

    print("\n--- 1. 登录（有特定handler） ---")
    try:
        result = service.login("alice", password="secret123")
        print(f"结果: {result}")
    except ValueError as e:
        print(f"错误: {e}")

    print("\n--- 2. 处理数据（有多个特定handler） ---")
    result = service.process_data("test data")
    print(f"结果: {result}")

    print("\n--- 3. 再次处理数据 ---")
    result = service.process_data([1, 2, 3])
    print(f"结果: {result}")

    print("\n--- 4. 登出（只有通用handler） ---")
    result = service.logout()
    print(f"结果: {result}")

    print("\n" + "=" * 60)
    print("优势说明:")
    print("  1. 一个Feature可以针对不同stage定义不同逻辑")
    print("  2. 使用装饰器明确标注，代码清晰易读")
    print("  3. 如果没有特定handler，会回退到通用before_stage/after_stage")
    print("  4. 灵活组合多个Feature的特定handler")
    print("=" * 60)
