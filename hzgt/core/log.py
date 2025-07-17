import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Union

from hzgt.core.Decorator import vargs
from hzgt.core.fileop import ensure_file, make_filename
from hzgt.core.strop import restrop

__LOG_LEVEL_DICT = {
    0: logging.NOTSET,
    1: logging.DEBUG,
    2: logging.INFO,
    3: logging.WARNING,
    4: logging.ERROR,
    5: logging.CRITICAL,

    logging.NOTSET: logging.NOTSET,
    logging.DEBUG: logging.DEBUG,
    logging.INFO: logging.INFO,
    logging.WARNING: logging.WARNING,
    logging.ERROR: logging.ERROR,
    logging.CRITICAL: logging.CRITICAL,

    "notset": logging.NOTSET,
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "fatal": logging.CRITICAL,
    "critical": logging.CRITICAL,

    "NOTSET": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.CRITICAL,
    "CRITICAL": logging.CRITICAL,
}

__LEVEL_NAME_DICT = {
    0: "NOTSET",
    1: "DEBUG",
    2: "INFO",
    3: "WARNING",
    4: "ERROR",
    5: "CRITICAL",

    logging.NOTSET: "NOTSET",
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",

    "notset": "NOTSET",
    "debug": "DEBUG",
    "info": "INFO",
    "warn": "WARNING",
    "warning": "WARNING",
    "error": "ERROR",
    "fatal": "CRITICAL",
    "critical": "CRITICAL",

    "NOTSET": "NOTSET",
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARN": "WARNING",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "FATAL": "CRITICAL",
    "CRITICAL": "CRITICAL",
}


@vargs({"level": set(__LOG_LEVEL_DICT.keys())})
def set_log(
        name: Optional[str] = None,
        fpath: Optional[str] = ".",
        fname: Optional[str] = None,
        level: Union[int, str] = 2,
        print_prefix: str = f'{restrop("[%(asctime)s | %(filename)s[%(lineno)-3s]", f=3)} {restrop("[%(levelname)s]", f=5)}\t{restrop("%(message)s", f=1)}',
        file_prefix: str = '[%(asctime)s | %(filename)s[%(lineno)-3s] [%(levelname)s]\t%(message)s',
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        maxBytes: int = 2 * 1024 * 1024,
        backupCount: int = 3,
        encoding: str = "utf-8",
        force_reconfigure: bool = False
) -> logging.Logger:
    """
    创建或获取日志记录器，支持控制台和文件日志输出

    :param name: 日志器名称，None 表示根日志器
    :param fpath: 日志文件存放目录路径 默认当前目录 如果为 None 则不输出日志文件
    :param fname: 日志文件名 如果为 None 则为 "{name}.log"
    :param level: 日志级别，支持多种格式 (默认: INFO/2)
    :param print_prefix: 控制台日志格式
    :param file_prefix: 文件日志格式
    :param datefmt: 日期格式
    :param maxBytes: 日志文件最大字节数 (默认: 2MB)
    :param backupCount: 备份文件数量 (默认: 3)
    :param encoding: 文件编码 (默认: utf-8)
    :param force_reconfigure: 强制重新配置现有日志器
    :return: 配置好的日志记录器
    """
    # 获取日志器
    logger = logging.getLogger(name)

    # 检查是否已有处理器，避免重复添加
    if logger.handlers and not force_reconfigure:
        logger.setLevel(__LOG_LEVEL_DICT[level])
        return logger

    # 清理现有处理器（如果需要重新配置）
    if force_reconfigure:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    # 设置日志级别
    logger.setLevel(__LOG_LEVEL_DICT[level])
    logger.propagate = False  # 防止日志传播到根日志器

    # 创建控制台处理器
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(print_prefix, datefmt=datefmt))
    logger.addHandler(stream_handler)

    # 创建文件处理器（如果指定了日志文件路径）
    if fpath:
        # 确定日志文件名
        log_name = make_filename(name, fname=fname, suffix=".log")
        logfile = os.path.join(fpath, log_name)

        # 确保日志文件存在
        ensure_file(logfile)

        # 创建旋转文件处理器
        file_handler = RotatingFileHandler(
            filename=logfile,
            encoding=encoding,
            maxBytes=maxBytes,
            backupCount=backupCount
        )
        file_handler.setFormatter(logging.Formatter(file_prefix, datefmt=datefmt))
        logger.addHandler(file_handler)

        # 可选：记录日志文件路径
        logger.debug(f"日志文件路径: {os.path.abspath(logfile)}")

    # 可选：记录日志级别
    level_name = __LEVEL_NAME_DICT[level]
    logger.debug(f"日志级别: {level} - {level_name}")

    return logger
