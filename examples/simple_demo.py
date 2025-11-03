"""
快速对比：单个 stage vs 多个 stage 装饰器
"""

from aoplib import stage, Feature, before_stage, after_stage
from aoplib.feature import with_tag, features


# ✅ 推荐：一个方法处理多个stage（简洁清晰）
class SecurityFeature(Feature):
    def __init__(self):
        super().__init__()

    @before_stage(with_tag("security"))
    def handle_auth(self, context):
        print(f"[安全] 认证操作: {context.stage_info.name}")
        raise Exception("认证失败")

    @after_stage(with_tag("security"))
    def audit_auth(self, context):
        print(f"[安全] 认证审计: {context.stage_info.name}")

    @after_stage 
    def do_log(self, context):
        print(f"do log:  {context.stage_info.name}")


@features(SecurityFeature)
class Service:
    @stage("security")
    def login(self):
        return "登录阶段"

    @stage("security")
    def logout(self):
        return "登出阶段"

    @stage("security")
    def register(self):
        return "注册阶段"

    @stage
    def test(self):
        return "测试阶段"


@features
class Service2:
    @stage("security")
    def login(self):
        return "登录"


if __name__ == "__main__":

    print("\n--- 新方式：1个方法（3行代码） ---")
    service1 = Service()

    service1.test()
    service1.login()
    service1.logout()
    service1.register()

    print("\n--- 新方式：1个方法（3行代码） ---")
    service2 = Service2()
    service2.add_feature(SecurityFeature())
    service2.login()
