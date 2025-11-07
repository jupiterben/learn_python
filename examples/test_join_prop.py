

from aoplib import Aspect, JoinProperty, add_aspect, after_set, aop_class, before_init, before_set, with_name


class PropAspect(Aspect):
    @before_init
    def init(self, context):
        print("before init")
        return context.value

    @before_set
    def before_set_value(self, context):
        print("before set")

    @after_set
    def after_set_value(self, context):
        print("after set")


class TestJoin:
    _aspects = [PropAspect()]
    name = JoinProperty(default="d_name", tags=[])

    def __init__(self, name, value):
        self.name = name


if __name__ == '__main__':
    t = TestJoin("name", "value")
    print(t.name)

    t2 = TestJoin("name2", "value2")

    print(t2.name)
    print(t.name)
