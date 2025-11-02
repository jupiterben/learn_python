"""
快速对比：单个 stage vs 多个 stage 装饰器
"""
from aoplib import stage, Feature, before_stage, after_stage
from aoplib.feature import features


# ✅ 推荐：一个方法处理多个stage（简洁清晰）
class SecurityFeature(Feature):
    def __init__(self):
        super().__init__()

    @before_stage(tags=["security"])
    def handle_auth(self, context):
        print(f"[安全] 认证操作: {context.stage_name}")

    @after_stage(tags=["security"])
    def audit_auth(self, context):
        print(f"[安全] 认证审计: {context.stage_name}")

    @before_stage("test")
    def handle_log(self, context):
        print(f"[安全] 测试操作: {context.stage_name}")


@features(SecurityFeature())
class Service:
    @stage("security")
    def login(self):
        return "登录"

    @stage("security")
    def logout(self):
        return "登出"

    @stage("security")
    def register(self):
        return "注册"

    @stage
    def test(self):
        return "测试"


if __name__ == "__main__":

    print("\n--- 新方式：1个方法（3行代码） ---")
    service2 = Service()

    service2.test()
    service2.login()
    service2.logout()
    service2.register()
