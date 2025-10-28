"""
通配符匹配示例 - 使用 * 和 ? 匹配多个stage
"""
from aoplib import stage, Feature, aop_class, before_stage, after_stage


class WildcardFeature(Feature):
    """演示通配符匹配"""

    def __init__(self):
        super().__init__()

    @before_stage("process_*")
    def handle_all_process(self, context):
        """匹配所有 process_ 开头的stage"""
        print(f"[通配符] 处理 process_* : {context.stage_name}")

    @after_stage("*_data")
    def handle_all_data(self, context):
        """匹配所有 _data 结尾的stage"""
        print(f"[通配符] 数据操作 *_data : {context.stage_name}")

    @before_stage("save_user_?")
    def handle_save_user_single(self, context):
        """匹配 save_user_ 后跟单个字符的stage"""
        print(f"[通配符] 保存用户 save_user_? : {context.stage_name}")


class MonitoringFeature(Feature):
    """精确匹配优先于通配符"""

    def __init__(self):
        super().__init__()
        self.exact_count = 0
        self.wildcard_count = 0

    @before_stage("process_order")
    def handle_specific_order(self, context):
        """精确匹配 process_order"""
        self.exact_count += 1
        print(f"[监控] 精确匹配: {context.stage_name} (优先级更高)")

    @before_stage("process_*")
    def handle_all_process(self, context):
        """通配符匹配 process_*（如果有精确匹配就不会执行）"""
        self.wildcard_count += 1
        print(f"[监控] 通配符匹配: {context.stage_name}")


class UniversalLogger(Feature):
    """使用 * 匹配所有stage"""

    def __init__(self):
        super().__init__()

    @before_stage("*")
    def log_all_before(self, context):
        """匹配所有stage"""
        print(f"[全局] 进入: {context.stage_name}")

    @after_stage("*")
    def log_all_after(self, context):
        """匹配所有stage"""
        print(f"[全局] 退出: {context.stage_name} -> {context.result}")


@aop_class
class DataService:
    """数据服务"""

    @stage
    def process_order(self):
        return "订单处理完成"

    @stage
    def process_payment(self):
        return "支付处理完成"

    @stage
    def process_refund(self):
        return "退款处理完成"

    @stage
    def load_data(self):
        return "加载数据"

    @stage
    def save_data(self):
        return "保存数据"

    @stage
    def validate_data(self):
        return "验证数据"

    @stage
    def save_user_a(self):
        return "保存用户A"

    @stage
    def save_user_b(self):
        return "保存用户B"

    @stage
    def save_user_ab(self):
        return "保存用户AB"


if __name__ == "__main__":
    print("=" * 70)
    print("示例1: 通配符匹配")
    print("=" * 70)

    service = DataService()
    wildcard = WildcardFeature()
    service.add_feature(wildcard)

    print("\n--- process_* 匹配 ---")
    service.process_order()
    service.process_payment()
    service.process_refund()

    print("\n--- *_data 匹配 ---")
    service.load_data()
    service.save_data()
    service.validate_data()

    print("\n--- save_user_? 匹配 ---")
    service.save_user_a()
    service.save_user_b()
    service.save_user_ab()  # 不匹配（两个字符）

    print("\n" + "=" * 70)
    print("示例2: 精确匹配优先于通配符")
    print("=" * 70)

    service2 = DataService()
    monitoring = MonitoringFeature()
    service2.add_feature(monitoring)

    print("\n--- process_order 有精确匹配 ---")
    service2.process_order()

    print("\n--- process_payment 只有通配符匹配 ---")
    service2.process_payment()

    print(f"\n精确匹配次数: {monitoring.exact_count}")
    print(f"通配符匹配次数: {monitoring.wildcard_count}")

    print("\n" + "=" * 70)
    print("示例3: 使用 * 匹配所有stage")
    print("=" * 70)

    service3 = DataService()
    universal = UniversalLogger()
    service3.add_feature(universal)

    print()
    service3.process_order()
    print()
    service3.save_data()

    print("\n" + "=" * 70)
    print("通配符规则:")
    print("  * - 匹配任意数量的任意字符")
    print("  ? - 匹配单个任意字符")
    print("  精确匹配优先级 > 通配符匹配")
    print("  通配符按注册顺序匹配，找到第一个就返回")
    print("=" * 70)

