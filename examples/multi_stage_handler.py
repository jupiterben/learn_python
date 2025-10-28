"""
演示：一个处理器方法处理多个stage
"""
from aoplib import stage, Feature, aop_class, before_stage, after_stage


class SecurityFeature(Feature):
    """安全特性 - 对所有认证相关操作进行统一处理"""

    def __init__(self):
        super().__init__()
        self.auth_log = []

    @before_stage(["login", "logout", "register"])
    def handle_auth_operations(self, context):
        """统一处理所有认证相关操作"""
        operation = context.stage_name
        print(f"[安全] 认证操作: {operation}")
        self.auth_log.append(f"before_{operation}")

    @after_stage(["login", "logout", "register"])
    def audit_auth_operations(self, context):
        """审计所有认证操作"""
        print(f"[审计] {context.stage_name} 完成，结果: {context.result}")
        self.auth_log.append(f"after_{context.stage_name}")


class CRUDFeature(Feature):
    """CRUD特性 - 对所有数据修改操作进行统一处理"""

    def __init__(self):
        super().__init__()
        self.modified_count = 0

    @before_stage(["create", "update", "delete"])
    def before_data_modification(self, context):
        """数据修改前的验证"""
        print(f"[CRUD] 准备{context.stage_name}数据")
        context.data['start_time'] = __import__('time').time()

    @after_stage(["create", "update", "delete"])
    def after_data_modification(self, context):
        """数据修改后的处理"""
        elapsed = __import__('time').time() - context.data['start_time']
        self.modified_count += 1
        print(
            f"[CRUD] {context.stage_name}完成，耗时: {elapsed:.4f}秒，累计修改: {self.modified_count}次")

    @after_stage("read")
    def after_read(self, context):
        """读取操作不计入修改"""
        print(f"[CRUD] 读取操作，不计入修改统计")


@aop_class
class UserService:
    """用户服务"""

    def __init__(self):
        self.users = {}
        self.current_user = None

    @stage
    def register(self, username):
        """注册"""
        self.users[username] = {"name": username, "active": True}
        return f"用户 {username} 注册成功"

    @stage
    def login(self, username):
        """登录"""
        if username in self.users:
            self.current_user = username
            return f"用户 {username} 登录成功"
        return f"用户 {username} 不存在"

    @stage
    def logout(self):
        """登出"""
        user = self.current_user
        self.current_user = None
        return f"用户 {user} 已登出"

    @stage
    def create(self, data):
        """创建数据"""
        __import__('time').sleep(0.01)
        return f"创建: {data}"

    @stage
    def update(self, data):
        """更新数据"""
        __import__('time').sleep(0.01)
        return f"更新: {data}"

    @stage
    def delete(self, data):
        """删除数据"""
        __import__('time').sleep(0.01)
        return f"删除: {data}"

    @stage
    def read(self, data):
        """读取数据"""
        return f"读取: {data}"


if __name__ == "__main__":
    print("=" * 60)
    print("示例：多Stage处理器")
    print("=" * 60)

    service = UserService()
    security = SecurityFeature()
    crud = CRUDFeature()

    service.add_feature(security)
    service.add_feature(crud)

    print("\n--- 1. 认证操作（被同一个方法处理） ---")
    service.register("alice")
    print()
    service.login("alice")
    print()
    service.logout()

    print("\n--- 2. CRUD操作（被同一个方法处理） ---")
    service.create("新记录")
    print()
    service.update("记录1")
    print()
    service.delete("记录2")
    print()
    service.read("记录3")

    print("\n--- 3. 统计信息 ---")
    print(f"认证日志: {security.auth_log}")
    print(f"数据修改次数: {crud.modified_count}")

    print("\n" + "=" * 60)
    print("多Stage处理器的优势:")
    print("  1. 减少代码重复 - 相似逻辑只写一次")
    print("  2. 代码更清晰 - 明确表达哪些stage是一组的")
    print("  3. 易于维护 - 统一修改一组stage的处理逻辑")
    print("  4. 灵活组合 - 既可单个stage，也可多个stage")
    print("=" * 60)
