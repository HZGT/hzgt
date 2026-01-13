# -*- coding: utf-8 -*-

import datetime
from functools import wraps


# 通用适配器，使任何装饰器都支持两种调用方式
def dual_support(decorator_factory):
    """
    装饰器

    将普通装饰器工厂转换为支持 @decorator 和 @decorator() 两种用法的装饰器

    >>> from hzgt import dual_support
    >>>
    >>> @ dual_support
    >>> def my_decorator(*arg, **kargs):
    ...     pass
    >>>
    """

    @wraps(decorator_factory)
    def wrapper(*args, **kwargs):
        # 如果没有参数且第一个参数是可调用对象，则使用默认参数
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # 使用默认参数
            import inspect
            sig = inspect.signature(decorator_factory)
            defaults = {}
            for param_name, param in sig.parameters.items():
                if param.default is not inspect.Parameter.empty:
                    defaults[param_name] = param.default
            return decorator_factory(**defaults)(args[0])
        # 否则，正常调用装饰器工厂
        return decorator_factory(*args, **kwargs)

    return wrapper


def vargs(valid_params: dict):
    """
    根据其有效集合验证函数参数


    >>> from hzgt import vargs
    >>>
    >>> @ vargs({'mode': {'read', 'write', 'append'}, 'type': {'text', 'binary'}, 'u': [1, 2, 3]})
    >>> def process_data(mode, type, u="1"):
    ...      print(f"Processing data in {mode} mode and {type} type, {u}")
    ...
    >>> process_data(mode="read", type="text", u="2")  # 正常执行
    >>> process_data(mode='read', type='text')  # 正常执行
    >>> # process_data(mode='delete', type='binary')  # 抛出ValueError
    >>> # process_data(mode='read', type='image')  # 抛出ValueError

    :param valid_params: dict 键为 arg/kargs 名称，值为 有效值的集合/列表

    """

    def decorator(func):
        def find_original_function(f):
            if hasattr(f, '__wrapped__'):
                return find_original_function(f.__wrapped__)
            return f

        original_func = find_original_function(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数的参数名称
            func_args = original_func.__code__.co_varnames[:original_func.__code__.co_argcount]

            # 验证位置参数
            for i, arg in enumerate(args):
                if func_args[i] in valid_params and arg not in valid_params[func_args[i]]:
                    raise ValueError(
                        f"值 '{func_args[i]} = {arg}' 无效: 有效集合为: {valid_params[func_args[i]]}")

            # 验证关键字参数
            for param_name, valid_set in valid_params.items():
                if param_name in kwargs and kwargs[param_name] not in valid_set:
                    raise ValueError(
                        f"值 `{param_name} = {kwargs[param_name]}` 无效: 有效集合为: {valid_set}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


class __IndentLogger:
    def __init__(self):
        self.indent_level = 0

    def log(self, message, end="\n"):
        print(" " * self.indent_level * 1 + message, end=end)

    def inc_indent(self):
        self.indent_level += 1

    def dec_indent(self):
        if self.indent_level > 0:
            self.indent_level -= 1


__indent_logger = __IndentLogger()
del __IndentLogger


@dual_support
@vargs({"precision": [i for i in range(0, 10)]})
def gettime(precision=6, date_format='%Y-%m-%d %H:%M:%S.%f'):
    """
    打印函数执行的时间
    :param precision: int 时间精度 范围为 0 到 9
    :param date_format: 时间格式
    :return:
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.datetime.now()
            start_str = start_time.strftime(date_format)
            module_name = func.__module__
            func_name = func.__name__

            __indent_logger.log(f"\n开始时间 {start_str} {module_name}.{func_name}")
            __indent_logger.inc_indent()
            try:
                result = func(*args, **kwargs)
            finally:
                pass
            end_time = datetime.datetime.now()
            end_str = end_time.strftime(date_format)
            spent_time = (end_time - start_time).total_seconds()
            __indent_logger.dec_indent()
            __indent_logger.log(f"结束时间 {end_str} {module_name}.{func_name} 总耗时 {spent_time:.{precision}f} s")

            return result

        return wrapper

    return decorator
