# -*- coding: utf-8 -*-

import datetime
import time
import inspect
import sys
import traceback
import logging
import os
from functools import wraps


LOG_LEVEL = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }

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


class IndentLogger:
    def __init__(self):
        self.indent_level = 0

    def log(self, message, end="\n"):
        print(" " * self.indent_level * 1 + message, end=end)

    def inc_indent(self):
        self.indent_level += 1

    def dec_indent(self):
        if self.indent_level > 0:
            self.indent_level -= 1


indent_logger = IndentLogger()

@vargs({"precision": [i for i in range(0, 10)]})
def gettime(precision=2, date_format='%Y-%m-%d %H:%M:%S'):
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

            indent_logger.log(f"开始时间 {start_str} {module_name}.{func_name}")
            indent_logger.inc_indent()
            try:
                result = func(*args, **kwargs)
            finally:
                pass
            end_time = datetime.datetime.now()
            end_str = end_time.strftime(date_format)
            spent_time = (end_time - start_time).total_seconds()
            indent_logger.dec_indent()
            indent_logger.log(f"结束时间 {end_str} {module_name}.{func_name} 总耗时 {spent_time:.{precision}f} s")

            return result

        return wrapper

    return decorator


@vargs({"loglevel": {"debug", "info", "warning", "error", "critical"}})
def log_func(loglevel="debug", encoding="utf-8", bool_raise_error=False):
    """
    使用方法：装饰器

    在需要日志的函数前加 @timelog()

    loglevel
        * "debug": logging.DEBUG,
        * "info": logging.INFO,
        * "warning": logging.WARNING,
        * "error": logging.ERROR,
        * "critical": logging.CRITICAL

    :param loglevel: str 日志等级
    :param encoding: 编码方式 默认 UTF-8
    :param bool_raise_error: 遇到 Error 是否使用 raise 报错
    """

    def _log(func):
        logger = logging.getLogger(__name__)
        logger.setLevel(LOG_LEVEL[loglevel])

        # 控制台输出渠道
        ch = logging.StreamHandler()
        logger.addHandler(ch)

        # 创建目录&.log文件
        log_dir = os.path.join(os.getcwd(), "logs")
        lt = time.localtime(time.time())
        ymd = time.strftime('%Y%m%d', lt)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, ymd + ".log")

        # 文件输出渠道
        file_handler = logging.FileHandler(log_path, encoding=encoding)
        logger.addHandler(file_handler)

        def inner(*args, **kwargs):
            frame = inspect.currentframe().f_back
            info = {
                "filename": frame.f_code.co_filename,
                "function_name": frame.f_code.co_name,
                "line_number": frame.f_lineno,
                "total_lines": len(inspect.getsourcelines(frame.f_code))
            }

            formatter = logging.Formatter(
                f'%(asctime)s -- [{info["filename"]}][{info["line_number"]}] -- %(levelname)s: %(message)s',
                )

            ch.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            try:
                res = func(*args, **kwargs)

                if args and not kwargs:
                    logger.info(f"{func.__name__} {args} -> {res}")
                elif kwargs and not args:
                    logger.info(f"{func.__name__} {kwargs} -> {res}")
                elif args and kwargs:
                    logger.info(f"{func.__name__} {args, kwargs} -> {res}")
                else:
                    logger.info(f"{func.__name__} -> {res}")

                return res
            except Exception as e:
                errfs = traceback.extract_tb(sys.exc_info()[2])[-1]
                errfile = errfs.filename
                errline = errfs.lineno
                err = f"[{errfile}][{errline}] -> {e.__class__.__name__}: {e}"
                if args and not kwargs:
                    logger.error(f"{func.__name__} {args} -- {err}")
                elif kwargs and not args:
                    logger.error(f"{func.__name__} {kwargs} -- {err}")
                elif args and kwargs:
                    logger.error(f"{func.__name__} {args, kwargs} -- {err}")
                else:
                    logger.error(f"{func.__name__} -- {err}")

                if bool_raise_error:
                    raise e
                else:
                    return err

        return inner

    return _log


