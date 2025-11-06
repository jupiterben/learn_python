"""
快速对比：单个 joinpoint vs 多个 joinpoint 装饰器
"""

from aoplib import Aspect, JoinMethodContext, before_method, after_method, join_method, join_property, aop_class
from aoplib import after_property_set, around_property_init
from aoplib.context import JoinPropContext
from aoplib.joincut import with_name


class LogAspect(Aspect):
    def __init__(self):
        super().__init__()

    @before_method
    def before(self, context):
        print(f"log before: {context.name}")

    @after_method
    def after(self, context):
        print(f"log after: {context.name}")

# ✅ 推荐：一个方法处理多个point（简洁清晰）


class SecurityFeature(Aspect):
    def __init__(self):
        super().__init__()

    @before_method(with_name("login", "register", "logout"))
    def handle_auth(self, context: JoinMethodContext):
        print(f"[安全] 认证操作: {context.name}")


class LocalStoreProps(Aspect):
    def __init__(self):
        super().__init__()

    @around_property_init
    def load_storage(self, context: JoinPropContext):
        print(f"load storage")
        return context.value

    @after_property_set
    def store_name(self, context):
        print(f"[存储] 存储属性: {context.value}")


@aop_class(SecurityFeature)
class Service:
    def __init__(self):
        super().__init__()

    @join_property
    def name(self):
        pass

    @join_method
    def login(self):
        self.name = "张三"
        print(self.name)
        return "登录阶段"

    @join_method
    def logout(self):
        return "登出阶段"

    @join_method
    def register(self):
        return "注册阶段"

    @join_method
    def test(self):
        return "测试阶段"


class Service2:
    @join_method
    def login(self):
        return "登录中..."


if __name__ == "__main__":

    service1 = Service()
    service1.test()
    service1.login()
    service1.logout()
    service1.register()
