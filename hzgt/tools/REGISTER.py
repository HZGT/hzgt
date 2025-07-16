# -*- coding: utf-8 -*-

from hzgt.core.strop import restrop


class Func_Register(dict):
    """
    函数注册器
    """
    def __init__(self, *args, **kwargs):
        super(Func_Register, self).__init__(*args, **kwargs)
        self._dict = {}

    def __call__(self, target):
        return self.register(target)

    def register(self, target):
        """
        将函数添加至注册器中

        :param target: 函数名
        :return:
        """
        def add_item(key, value):
            if not callable(value):
                raise ValueError(f'{restrop("Error:")} {value} 必须是可调用的!')
            if key in self._dict:
                print(f'{restrop("Warning:", f=3)} {value.__name__} 已存在，将被覆盖!')
            self[key] = value
            return value

        if callable(target):    # 传入的target可调用 --> 没有给注册名 --> 传入的函数名或类名作为注册名
            return add_item(target.__name__, target)
        else:                   # 不可调用 --> 传入了注册名 --> 作为可调用对象的注册名
            return lambda x: add_item(target, x)

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        return self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def __str__(self):
        return str(self._dict)

    def keys(self):
        """

        :return:
        """
        return self._dict.keys()

    def values(self):
        """

        :return:
        """
        return self._dict.values()

    def items(self):
        """

        :return:
        """
        return self._dict.items()


class Class_Register(dict):
    """
    类注册器
    """
    def __init__(self, registry_name, *args, **kwargs):
        super(Class_Register, self).__init__(*args, **kwargs)
        self._dict = {}
        self._name = registry_name

    def __setitem__(self, key, value):
        if not callable(value):
            raise ValueError(f'注册器的值必须是可调用的! 值: {value}')
        if key is None:
            key = value.__name__
        if key in self._dict:
            print("键 %s 已经在注册器中 -> %s." % (key, self._name))
        self._dict[key] = value

    def __call__(self, target):
        return self.register(target)

    def register(self, target):
        """
        :param target:
        :return:
        """
        def add(key, value):
            self[key] = value
            return value

        if callable(target):
            # @reg.register
            return add(None, target)
        # @reg.register('alias')
        return lambda x: add(target, x)

    def __getitem__(self, key):
        return self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def keys(self):
        """

        :return:
        """
        return self._dict.keys()

    def items(self):
        """

        :return:
        """
        return self._dict.items()

