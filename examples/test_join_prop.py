

from aoplib import Aspect, JoinProperty, add_aspect, after_set, before_init, before_set, with_name


class TestJoinProp:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"{self.name}={self.value}"

    def __repr__(self):
        return f"TestJoinProp(name={self.name}, value={self.value})"

    @JoinProperty(tags=[])
    def name_value(self):
        return f"{self.name}={self.value}"

    @name_value.setter
    def name_value(self, value):
        self.name, self.value = value.split("=")

    @JoinProperty
    def some(self):
        return self.name


class PropAspect(Aspect):
    @before_init
    def before(self, context):
        print("before init")

    @before_set(with_name("name_value"))
    def before_set_value(self, context):
        print("before set")

    @after_set(with_name("name_value"))
    def after_set_value(self, context):
        print("after set")


if __name__ == '__main__':
    t = TestJoinProp("name", "value")
    add_aspect(t, PropAspect())
    print(t.name_value)

    t.name_value = "new_name=new_value"
