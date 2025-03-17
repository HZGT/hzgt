import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from .Decorator import vargs
from .fileop import ensure_file
from .strop import restrop

LOG_LEVEL_DICT = {
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
    logging.CRITICAL: logging.CRITICAL
}

LEVEL_NAME_DICT = {
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
}


@vargs({"level": set(LOG_LEVEL_DICT.keys())})
def set_log(name: Optional[str], logfilename: str, level: int = 2,
            print_prefix: str = f'{restrop("[%(name)s %(asctime)s]", f=3)} {restrop("[%(levelname)s]", f=5)}\t{restrop("%(message)s")}',
            file_prefix: str = '[%(name)s %(asctime)s] [%(levelname)s]\t%(message)s',
            datefmt: str = "%Y-%m-%d %H:%M:%S",
            maxBytes: int = 2 * 1024 * 1024, backupCount: int = 3, encoding = "utf-8"):
    """
    创建一个具有指定名称、时间、级别、日志的日志记录器

    level
        - 0 -- logging.NOTSET
        - 1 -- logging.DEBUG
        - 2 -- logging.INFO
        - 3 -- logging.WARNING
        - 4 -- logging.ERROR
        - 5 -- logging.CRITICAL
    :param name: 
    :param logfilename: 日志文件路径  ***.log
    :param level: 日志级别，默认2 -- logging.INFO
    :param print_prefix:
    :param file_prefix:
    :param datefmt: 
    :param maxBytes: 日志文件最大字节数，默认2 * 1024 * 1024（2MB）
    :param backupCount: 备份文件数量，默认3
    :param encoding: 编码，默认utf-8
    :return:
    """
    ensure_file(logfilename)

    # print("日志路径: " + restrop(f"{os.path.abspath(logfilename)}", f=4))
    # print("日志等级: " + restrop(f"{level}\t{LEVEL_NAME_DICT[level]}", f=2))

    logger = logging.getLogger(name)
    # 检查是否已有处理器，避免重复添加
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL_DICT[level])

    print_formatter = logging.Formatter(print_prefix, datefmt=datefmt)
    file_formatter = logging.Formatter(file_prefix, datefmt=datefmt)

    stream = logging.StreamHandler()
    stream.setFormatter(print_formatter)

    log_file = RotatingFileHandler(filename=logfilename, encoding=encoding, maxBytes=maxBytes, backupCount=backupCount)
    log_file.setFormatter(file_formatter)

    logger.addHandler(stream)
    logger.addHandler(log_file)

    return logger

