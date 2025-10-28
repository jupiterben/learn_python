"""
快速对比：单个 stage vs 多个 stage 装饰器
"""
from aoplib import stage, Feature, aop_class, before_stage, after_stage


# ❌ 不推荐：每个stage写一个方法（代码重复）
class SecurityFeature_Old(Feature):
    def __init__(self):
        super().__init__()

    @before_stage("login")
    def handle_login(self, context):
        print("[安全] 认证操作: login")

    @before_stage("logout")
    def handle_logout(self, context):
        print("[安全] 认证操作: logout")

    @before_stage("register")
    def handle_register(self, context):
        print("[安全] 认证操作: register")


# ✅ 推荐：一个方法处理多个stage（简洁清晰）
class SecurityFeature_New(Feature):
    def __init__(self):
        super().__init__()

    @before_stage(["login", "logout", "register"])
    def handle_auth(self, context):
        print(f"[安全] 认证操作: {context.stage_name}")


@aop_class
class Service:
    @stage
    def login(self):
        return "登录"

    @stage
    def logout(self):
        return "登出"

    @stage
    def register(self):
        return "注册"


if __name__ == "__main__":
    print("=" * 60)
    print("对比：单个 vs 多个 stage 处理器")
    print("=" * 60)

    print("\n--- 旧方式：3个方法（9行代码） ---")
    service1 = Service()
    service1.add_feature(SecurityFeature_Old())
    service1.login()
    service1.logout()
    service1.register()

    print("\n--- 新方式：1个方法（3行代码） ---")
    service2 = Service()
    service2.add_feature(SecurityFeature_New())
    service2.login()
    service2.logout()
    service2.register()

    print("\n" + "=" * 60)
    print("代码行数对比: 9行 → 3行（减少 67%）")
    print("维护成本: 修改3处 → 修改1处")
    print("可读性: ⭐⭐⭐ → ⭐⭐⭐⭐⭐")
    print("=" * 60)

