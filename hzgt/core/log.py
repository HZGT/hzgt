import atexit
import json
import logging
import os
import queue
import sys
import threading
from logging.handlers import RotatingFileHandler
from typing import Optional, Union, Dict, Any, List

from hzgt.core import ensure_file, vargs, restrop, make_filename

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


class _ContextFilter(logging.Filter):
    """添加额外上下文信息的日志过滤器"""

    def __init__(self, extra_fields: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.extra_fields = extra_fields or {}

    def filter(self, record):
        # 添加基础上下文信息
        record.pid = os.getpid()
        record.thread_id = threading.get_ident()
        record.thread_name = threading.current_thread().name
        record.module_path = os.path.abspath(sys.argv[0])

        # 创建上下文字典
        ctx_dict = {}

        # 添加自定义字段
        for key, value in self.extra_fields.items():
            setattr(record, key, value)
            ctx_dict[key] = value

        # 添加来自日志调用的上下文
        for attr in dir(record):
            if attr.startswith("ctx_") and not attr.startswith("ctx_dict"):
                clean_key = attr[4:]  # 去掉 ctx_ 前缀
                ctx_dict[clean_key] = getattr(record, attr)

        # 设置上下文字典属性
        record.ctx_dict = ctx_dict if ctx_dict else ""

        return True


class _JSONFormatter(logging.Formatter):
    """结构化JSON日志格式化器 - 分离原始字段和上下文字段"""

    def __init__(self, *args, **kwargs):
        self.include_fields = kwargs.pop("include_fields", None)
        self.exclude_fields = kwargs.pop("exclude_fields", None)
        super().__init__(*args, **kwargs)

    def format(self, record):
        # 创建基础日志字典（原始日志字段）
        base_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
            "pid": getattr(record, "pid", os.getpid()),
            "thread_id": getattr(record, "thread_id", threading.get_ident()),
            "thread_name": getattr(record, "thread_name", threading.current_thread().name),
        }

        # 添加异常信息
        if record.exc_info:
            base_record["exception"] = self.formatException(record.exc_info)

        # 创建上下文字典（用户传入的字段）
        context_record = {}

        # 收集所有 ctx_ 前缀的字段
        for attr in dir(record):
            if attr.startswith("ctx_"):
                # 去掉 ctx_ 前缀
                clean_key = attr[4:]
                # 排除特殊字段（如 ctx_dict）
                if clean_key not in ["dict", "json_enabled", "log_level", "log_path"]:
                    value = getattr(record, attr)
                    context_record[clean_key] = value

        # 处理 ctx_dict 字段（如果存在）
        if hasattr(record, "ctx_dict") and isinstance(record.ctx_dict, dict):
            for item in record.ctx_dict.items():
                key, value = item
                # 只添加不在 context_record 中的键
                if key not in context_record:
                    context_record[key] = value

        # 创建最终日志记录
        log_record = {
            "log": base_record,  # 原始日志字段
            "context": context_record  # 用户传入的上下文字段
        }

        # 字段过滤
        if self.include_fields:
            # 分别过滤基础日志字段和上下文字段
            filtered_base = {k: v for k, v in base_record.items() if k in self.include_fields}
            filtered_context = {k: v for k, v in context_record.items() if k in self.include_fields}
            log_record = {"log": filtered_base, "context": filtered_context}

        if self.exclude_fields:
            # 分别排除基础日志字段和上下文字段
            filtered_base = {k: v for k, v in base_record.items() if k not in self.exclude_fields}
            filtered_context = {k: v for k, v in context_record.items() if k not in self.exclude_fields}
            log_record = {"log": filtered_base, "context": filtered_context}

        return json.dumps(log_record, ensure_ascii=False)


# ======================
# 异步日志处理器
# ======================
class _AsyncLogHandler(logging.Handler):
    """异步日志处理器，使用队列和工作线程处理日志写入"""

    def __init__(self, base_handler: logging.Handler, queue_size: int = 10000, batch_size: int = 100):
        """
        初始化异步日志处理器

        :param base_handler: 基础日志处理器（如文件处理器）
        :param queue_size: 队列大小（默认10000）
        :param batch_size: 批量写入大小（默认100）
        """
        super().__init__()
        self.base_handler = base_handler
        self.queue = queue.Queue(maxsize=queue_size)
        self.batch_size = batch_size
        self._stop_event = threading.Event()

        # 设置工作线程
        self.worker_thread = threading.Thread(
            target=self._process_logs,
            name="AsyncLogWorker",
            daemon=True
        )
        self.worker_thread.start()

        # 注册退出处理
        atexit.register(self.stop)

    def emit(self, record):
        """将日志记录放入队列"""
        try:
            if not self._stop_event.is_set():
                # 如果队列已满，丢弃最旧的记录
                if self.queue.full():
                    try:
                        self.queue.get_nowait()
                    except queue.Empty:
                        pass
                self.queue.put_nowait(record)
        except Exception:
            # 避免日志记录失败导致程序崩溃
            pass

    def _process_logs(self):
        """工作线程处理日志的方法"""
        batch = []

        while not self._stop_event.is_set() or not self.queue.empty():
            try:
                # 批量获取日志记录
                record = self.queue.get(timeout=0.1)
                if record is None:  # 停止信号
                    break

                batch.append(record)

                # 达到批量大小或队列为空时处理
                if len(batch) >= self.batch_size or self.queue.empty():
                    self._process_batch(batch)
                    batch = []

                self.queue.task_done()
            except queue.Empty:
                # 处理剩余批次
                if batch:
                    self._process_batch(batch)
                    batch = []

        # 处理最后的批次
        if batch:
            self._process_batch(batch)

    def _process_batch(self, batch):
        """批量处理日志记录"""
        try:
            for record in batch:
                self.base_handler.handle(record)
        except Exception as e:
            # 处理日志写入错误
            sys.stderr.write(f"Async log handler error: {str(e)}\n")

    def stop(self):
        """停止异步处理器，处理剩余日志"""
        if not self._stop_event.is_set():
            self._stop_event.set()
            # 发送停止信号
            self.queue.put(None)
            # 等待工作线程完成
            self.worker_thread.join(timeout=5.0)
            # 关闭基础处理器
            self.base_handler.close()

    def close(self):
        """关闭处理器"""
        self.stop()
        super().close()


class _BoundContextLogger(logging.LoggerAdapter):
    """
    绑定到特定日志记录器的上下文日志记录器
    继承自 logging.LoggerAdapter，提供更贴近底层的实现
    """

    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """
        初始化绑定上下文日志记录器

        :param logger: 绑定的日志记录器实例
        :param extra: 额外的上下文信息（字典）
        """
        super().__init__(logger, extra or {})
        self.logger = logger
        self.extra = extra or {}

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        处理日志消息和关键字参数，添加上下文信息

        重写 LoggerAdapter 的 process 方法
        """
        # 获取传入的上下文（如果有）
        context = kwargs.pop("context", None) or {}

        # 合并实例级上下文和本次日志上下文
        merged_extra = {**self.extra, **context}

        # 构建 extra 字典（添加 ctx_ 前缀）
        extra = {}
        for key, value in merged_extra.items():
            extra[f"ctx_{key}"] = value

        # 更新 kwargs 中的 extra
        if "extra" in kwargs:
            # 合并已有的 extra
            kwargs["extra"] = {**kwargs["extra"], **extra}
        else:
            kwargs["extra"] = extra

        return msg, kwargs

    def log(
            self,
            level: int,
            msg: str,
            context: Optional[Dict[str, Any]] = None,
            exc_info: Optional[Union[bool, BaseException]] = None,
            stack_info: bool = False,
            stacklevel: int = 3,  # 默认跳过 3 层封装
            **kwargs
    ) -> None:
        """
        带上下文的日志记录方法

        :param level: 日志级别
        :param msg: 日志消息
        :param context: 本次日志的上下文数据（字典）
        :param exc_info: 异常信息（True 或 Exception 实例）
        :param stack_info: 是否包含堆栈信息
        :param stacklevel: 堆栈级别（设置为 3 跳过封装层）
        """
        # 确保使用正确的堆栈级别
        if stacklevel < 3:
            stacklevel = 3  # 最少需要跳过 3 层封装

        # 添加上下文到 kwargs
        if context is not None:
            kwargs["context"] = context

        # 调用底层 logger 的 log 方法
        super().log(
            level,
            msg,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            **kwargs
        )

    # 以下方法保持与原有接口兼容
    def debug(
            self,
            msg: str,
            context: Optional[Dict[str, Any]] = None,
            exc_info: Optional[Union[bool, BaseException]] = None,
            stack_info: bool = False,
            stacklevel: int = 3,
            **kwargs
    ) -> None:
        """
        DEBUG级别带上下文的日志记录

        :param msg: 日志消息
        :param context: 上下文数据（字典）
        :param exc_info: 异常信息（True 或 Exception 实例）
        :param stack_info: 是否包含堆栈信息
        :param stacklevel: 堆栈级别（设置为 3 跳过封装层）
        """
        # 设置合适的堆栈级别（跳过 3 层封装）
        if stacklevel < 3:
            stacklevel = 3

        # 添加上下文到 kwargs
        if context is not None:
            kwargs["context"] = context

        super().debug(
            msg,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            **kwargs
        )

    def info(
            self,
            msg: str,
            context: Optional[Dict[str, Any]] = None,
            exc_info: Optional[Union[bool, BaseException]] = None,
            stack_info: bool = False,
            stacklevel: int = 3,
            **kwargs
    ) -> None:
        """
        INFO级别带上下文的日志记录

        :param msg: 日志消息
        :param context: 上下文数据（字典）
        :param exc_info: 异常信息（True 或 Exception 实例）
        :param stack_info: 是否包含堆栈信息
        :param stacklevel: 堆栈级别（设置为 3 跳过封装层）
        """
        if stacklevel < 3:
            stacklevel = 3

        if context is not None:
            kwargs["context"] = context

        super().info(
            msg,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            **kwargs
        )

    def warning(
            self,
            msg: str,
            context: Optional[Dict[str, Any]] = None,
            exc_info: Optional[Union[bool, BaseException]] = None,
            stack_info: bool = False,
            stacklevel: int = 3,
            **kwargs
    ) -> None:
        """
        WARNING级别带上下文的日志记录

        :param msg: 日志消息
        :param context: 上下文数据（字典）
        :param exc_info: 异常信息（True 或 Exception 实例）
        :param stack_info: 是否包含堆栈信息
        :param stacklevel: 堆栈级别（设置为 3 跳过封装层）
        """
        if stacklevel < 3:
            stacklevel = 3

        if context is not None:
            kwargs["context"] = context

        super().warning(
            msg,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            **kwargs
        )

    def error(
            self,
            msg: str,
            context: Optional[Dict[str, Any]] = None,
            exc_info: Optional[Union[bool, BaseException]] = None,
            stack_info: bool = False,
            stacklevel: int = 3,
            **kwargs
    ) -> None:
        """
        ERROR级别带上下文的日志记录

        :param msg: 日志消息
        :param context: 上下文数据（字典）
        :param exc_info: 异常信息（True 或 Exception 实例）
        :param stack_info: 是否包含堆栈信息
        :param stacklevel: 堆栈级别（设置为 3 跳过封装层）
        """
        if stacklevel < 3:
            stacklevel = 3

        if context is not None:
            kwargs["context"] = context

        super().error(
            msg,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            **kwargs
        )

    def critical(
            self,
            msg: str,
            context: Optional[Dict[str, Any]] = None,
            exc_info: Optional[Union[bool, BaseException]] = None,
            stack_info: bool = False,
            stacklevel: int = 3,
            **kwargs
    ) -> None:
        """
        CRITICAL级别带上下文的日志记录

        :param msg: 日志消息
        :param context: 上下文数据（字典）
        :param exc_info: 异常信息（True 或 Exception 实例）
        :param stack_info: 是否包含堆栈信息
        :param stacklevel: 堆栈级别（设置为 3 跳过封装层）
        """
        if stacklevel < 3:
            stacklevel = 3

        if context is not None:
            kwargs["context"] = context

        super().critical(
            msg,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            **kwargs
        )

    def with_context(self, **context) -> "_BoundContextLogger":
        """
        创建带有额外上下文的新日志记录器

        :param context: 要添加的上下文键值对
        :return: 新的绑定上下文日志记录器
        """
        # 合并现有上下文和新上下文
        new_extra = {**self.extra, **context}
        return _BoundContextLogger(self.logger, new_extra)


# ======================
# 公开接口函数
# ======================
@vargs({"level": set(LOG_LEVEL_DICT.keys())})
def set_log(
        name: Optional[str] = None,
        fpath: Optional[str] = "logs",
        fname: Optional[str] = None,
        level: Union[int, str] = 2,
        # 控制台日志配置
        console_enabled: bool = True,
        console_format: Optional[str] = None,
        # 文件日志配置
        file_enabled: bool = True,
        file_format: Optional[str] = None,
        # 结构化日志配置
        json_enabled: bool = False,
        json_include_fields: Optional[List[str]] = None,
        json_exclude_fields: Optional[List[str]] = None,
        # 通用配置
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        maxBytes: int = 2 * 1024 * 1024,
        backupCount: int = 3,
        encoding: str = "utf-8",
        force_reconfigure: bool = False,
        # 上下文信息
        context_fields: Optional[Dict[str, Any]] = None,
        # 自定义处理器
        custom_handlers: Optional[List[logging.Handler]] = None,
        # 异步日志配置
        async_logging: bool = True,
        async_queue_size: int = 10000,
        async_batch_size: int = 100
) -> logging.Logger:
    """
    创建或获取高级日志记录器，支持控制台、文件和JSON日志输出

    :param name: 日志器名称，None 表示根日志器
    :param fpath: 日志文件存放目录路径（默认同目录的logs目录里）
    :param fname: 日志文件名（默认："{name}.log"）
    :param level: 日志级别（默认: 2/INFO）

    :param console_enabled: 是否启用控制台日志（默认：True）
    :param console_format: 控制台日志格式（默认：结构化文本格式）

    :param file_enabled: 是否启用文件日志（默认：True）
    :param file_format: 文件日志格式（默认：详细文本格式）

    :param json_enabled: 是否启用JSON日志（默认：False）
    :param json_include_fields: JSON日志包含字段（默认：全部）
    :param json_exclude_fields: JSON日志排除字段（默认：无）

    :param datefmt: 日期格式（默认："%Y-%m-%d %H:%M:%S"）
    :param maxBytes: 日志文件最大字节数（默认：2MB）
    :param backupCount: 备份文件数量（默认：3）
    :param encoding: 文件编码（默认：utf-8）
    :param force_reconfigure: 强制重新配置现有日志器（默认：False）

    :param context_fields: 额外上下文字段（字典格式）
    :param custom_handlers: 自定义日志处理器列表

    :param async_logging: 是否启用异步日志（默认True）
    :param async_queue_size: 异步队列大小（默认10000）
    :param async_batch_size: 异步批量写入大小（默认100）

    :return: 配置好的日志记录器
    """
    # 获取日志器
    logger = logging.getLogger(name)

    # 检查是否已有处理器，避免重复添加
    if logger.handlers and not force_reconfigure:
        logger.setLevel(LOG_LEVEL_DICT[level])
        return logger

    # 清理现有处理器（如果需要重新配置）
    if force_reconfigure:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    # 设置日志级别
    logger.setLevel(LOG_LEVEL_DICT[level])
    logger.propagate = False  # 防止日志传播到根日志器

    # 添加上下文过滤器
    context_filter = _ContextFilter(context_fields)
    logger.addFilter(context_filter)

    # 默认日志格式
    if console_format is None:
        console_format = (
                restrop("[%(asctime)s] ", f=6) +
                restrop("[%(threadName)s] ", f=5) +
                restrop("[%(filename)s:%(lineno)-4d] ", f=4) +
                restrop("[%(levelname)-7s] ", f=3) +
                f"%(message)s" +
                restrop(" %(ctx_dict)s", f=2)  # 只在有上下文时显示
        )

    if file_format is None:
        file_format = (
                "[%(asctime)s] " +
                "[%(threadName)s] " +
                "[%(filename)s:%(lineno)d] " +
                "%(levelname)-7s " +
                "%(message)s" +
                " %(ctx_dict)s"  # 直接显示字典
        )

    # 创建控制台处理器（如果启用）
    if console_enabled:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(console_format, datefmt=datefmt))
        logger.addHandler(stream_handler)

    # 创建文件处理器（如果启用）
    if file_enabled and fpath:
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
        file_handler.setFormatter(logging.Formatter(file_format, datefmt=datefmt))

        # 包装为异步处理器
        if async_logging:
            file_handler = _AsyncLogHandler(
                file_handler,
                queue_size=async_queue_size,
                batch_size=async_batch_size
            )

        logger.addHandler(file_handler)

    # 创建JSON日志处理器（如果启用）
    if json_enabled:
        # 确定JSON日志文件名
        json_log_name = make_filename(name, fname=fname, suffix=".json.log")
        json_logfile = os.path.join(fpath, json_log_name)

        # 确保日志文件存在
        ensure_file(json_logfile)

        # 创建JSON文件处理器
        json_handler = RotatingFileHandler(
            filename=json_logfile,
            encoding=encoding,
            maxBytes=maxBytes,
            backupCount=backupCount
        )

        # 设置JSON格式化器
        json_formatter = _JSONFormatter(
            datefmt=datefmt,
            include_fields=json_include_fields,
            exclude_fields=json_exclude_fields
        )
        json_handler.setFormatter(json_formatter)

        # 包装为异步处理器
        if async_logging:
            json_handler = _AsyncLogHandler(
                json_handler,
                queue_size=async_queue_size,
                batch_size=async_batch_size
            )

        logger.addHandler(json_handler)

    # 添加自定义处理器
    if custom_handlers:
        for handler in custom_handlers:
            # 如果是文件处理器，包装为异步
            if async_logging and isinstance(handler, (RotatingFileHandler, logging.FileHandler)):
                handler = _AsyncLogHandler(
                    handler,
                    queue_size=async_queue_size,
                    batch_size=async_batch_size
                )
            logger.addHandler(handler)

    # 记录配置信息
    logger.debug("日志器配置完成", extra={
        "ctx_log_level": LEVEL_NAME_DICT[level],
        "ctx_log_path": fpath,
        "ctx_json_enabled": json_enabled,
        "ctx_async_enabled": async_logging
    })

    return logger


def bind_logger(logger: logging.Logger, **context) -> "_BoundContextLogger":
    """
    创建绑定到指定日志记录器的上下文日志记录器

    >>> from hzgt import set_log, bind_logger
    >>> testlogger = set_log("test", fpath="logs")
    >>> testlogger.info("Hello World")
    >>> blogger = bind_logger(testlogger)
    >>> blogger.info("Test info 2", context={"anything": "context"})

    :param logger: 要绑定的日志记录器实例
    :param context: 初始上下文信息（可选）
    :return: 绑定后的上下文日志记录器
    """
    return _BoundContextLogger(logger, context)
