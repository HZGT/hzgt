import atexit
import inspect
import json
import logging
import os
import queue
import sys
import threading
import time
import weakref
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union, Dict, Any, List, Literal

from .Decorator import vargs
from .fileop import ensure_file, ensure_suffix
from .strop import restrop

# ======================
# 常量与映射表
# ======================
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


# ======================
# 全局异步处理器管理器
# ======================
class _AsyncHandlerRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._handlers = weakref.WeakSet()
                    cls._instance._closed = False
                    atexit.register(cls._instance.close_all)
        return cls._instance

    def register(self, handler):
        if not self._closed:
            self._handlers.add(handler)

    def close_all(self):
        if self._closed:
            return
        self._closed = True
        for handler in list(self._handlers):
            try:
                handler.stop()
            except Exception:
                pass
        self._handlers.clear()


# ======================
# 上下文过滤器
# ======================
class _ContextFilter(logging.Filter):
    # 显式列出 LogRecord 的所有标准属性（依据官方文档）
    STANDARD_ATTRS = {
        'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
        'funcName', 'levelname', 'levelno', 'lineno', 'message', 'module',
        'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
        'relativeCreated', 'stack_info', 'thread', 'threadName'
    }

    def __init__(self, extra_fields: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.extra_fields = extra_fields or {}

    def filter(self, record):
        # 添加系统辅助信息（它们也不会进入 ctx_dict）
        record.pid = os.getpid()
        record.thread_id = threading.get_ident()
        record.thread_name = threading.current_thread().name
        record.module_path = os.path.abspath(sys.argv[0])

        ctx_dict = {}

        # 1. 固定上下文字段（来自 context_fields）
        for key, value in self.extra_fields.items():
            setattr(record, key, value)
            ctx_dict[key] = value

        # 2. 定义需要排除的属性集合
        exclude_attrs = self.STANDARD_ATTRS | {
            'pid', 'thread_id', 'thread_name', 'module_path', 'ctx_dict'
        }

        # 3. 遍历 record 的所有属性，只收集非标准、非内部、非私有、非方法的属性
        for attr in dir(record):
            if attr.startswith('_'):          # 忽略私有属性
                continue
            if attr in exclude_attrs:         # 忽略标准属性和内部辅助属性
                continue
            value = getattr(record, attr)
            if callable(value):               # 忽略方法
                continue
            if attr not in ctx_dict:          # 避免覆盖已有键
                ctx_dict[attr] = value

        # 4. 兼容旧用法：ctx_ 前缀的属性（如 ctx_user_id）
        for attr in dir(record):
            if attr.startswith("ctx_") and not attr.startswith("ctx_dict"):
                clean_key = attr[4:]
                if clean_key not in ctx_dict:
                    ctx_dict[clean_key] = getattr(record, attr)

        # 如果 ctx_dict 为空，存空字符串以便格式化时显示干净
        record.ctx_dict = ctx_dict if ctx_dict else ""
        return True


# ======================
# JSON 格式化器
# ======================
class _JSONFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.include_fields = kwargs.pop("include_fields", None)
        self.exclude_fields = kwargs.pop("exclude_fields", None)
        super().__init__(*args, **kwargs)

    def format(self, record):
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

        if record.exc_info:
            base_record["exception"] = self.formatException(record.exc_info)

        context_record = {}
        if hasattr(record, "ctx_dict") and isinstance(record.ctx_dict, dict):
            context_record = record.ctx_dict.copy()

        if self.include_fields:
            base_record = {k: v for k, v in base_record.items() if k in self.include_fields}
            context_record = {k: v for k, v in context_record.items() if k in self.include_fields}

        if self.exclude_fields:
            base_record = {k: v for k, v in base_record.items() if k not in self.exclude_fields}
            context_record = {k: v for k, v in context_record.items() if k not in self.exclude_fields}

        log_record = {"log": base_record, "context": context_record}
        return json.dumps(log_record, ensure_ascii=False)


# ======================
# Loguru 风格过滤器
# ======================
class _LoguruStyleFilter(logging.Filter):
    def __init__(self, module_format: str = "module", project_root: Optional[str] = None):
        super().__init__()
        self.module_format = module_format
        self.project_root = project_root

    def filter(self, record):
        module_name, func_name, lineno, abs_path, rel_path = _get_caller_info(self.project_root)

        if self.module_format == "module":
            if module_name == "__main__" and abs_path:
                module_name = Path(abs_path).stem
            record.name = module_name
        elif self.module_format == "relpath":
            record.name = rel_path if rel_path else (abs_path if abs_path else module_name)
        elif self.module_format == "abspath":
            record.name = abs_path if abs_path else module_name
        else:
            record.name = module_name

        record.funcName = func_name
        record.lineno = lineno
        return True


# ======================
# 辅助函数
# ======================
def _get_caller_info(project_root: Optional[str] = None):
    frame = inspect.currentframe()
    try:
        frame = frame.f_back
        while frame:
            mod = inspect.getmodule(frame)
            mod_name = mod.__name__ if mod else ""
            if mod_name not in ("logging", "logging.handlers", __name__):
                break
            frame = frame.f_back

        if frame is None:
            return "unknown", "unknown", 0, "", ""

        module_name = inspect.getmodule(frame).__name__ if inspect.getmodule(frame) else "unknown"
        func_name = frame.f_code.co_name
        if func_name == "<module>":
            func_name = "<module>"
        lineno = frame.f_lineno
        filepath = frame.f_code.co_filename

        rel_path = ""
        if project_root and filepath:
            try:
                rel_path = Path(filepath).resolve().relative_to(Path(project_root).resolve()).as_posix()
            except ValueError:
                rel_path = filepath
        return module_name, func_name, lineno, filepath, rel_path
    finally:
        del frame


# ======================
# 异步日志处理器（最终修正版）
# ======================
class _AsyncLogHandler(logging.Handler):
    def __init__(self, base_handler: logging.Handler, queue_size: int = 10000,
                 batch_size: int = 100, flush_interval: float = 1.0):
        super().__init__()
        self.base_handler = base_handler
        self.queue = queue.Queue(maxsize=queue_size)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._stop_event = threading.Event()
        # 关键修改：工作线程设为守护线程，避免阻塞程序退出
        self._worker_thread = threading.Thread(target=self._process_logs, name="AsyncLogWorker", daemon=True)
        self._worker_thread.start()
        _AsyncHandlerRegistry().register(self)

    def emit(self, record):
        if self._stop_event.is_set():
            return
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            try:
                _ = self.queue.get_nowait()
                self.queue.put_nowait(record)
                sys.stderr.write(f"[AsyncLogHandler] Queue full, dropped oldest log: {record.getMessage()}\n")
            except queue.Empty:
                pass
            except Exception as e:
                sys.stderr.write(f"[AsyncLogHandler] Unexpected error: {str(e)}\n")

    def _process_logs(self):
        batch = []
        last_flush = time.time()
        while not self._stop_event.is_set() or not self.queue.empty():
            try:
                record = self.queue.get(timeout=0.1)
                batch.append(record)
                now = time.time()
                if len(batch) >= self.batch_size or self.queue.empty() or (now - last_flush) >= self.flush_interval:
                    self._process_batch(batch)
                    batch.clear()
                    last_flush = now
                self.queue.task_done()
            except queue.Empty:
                now = time.time()
                if batch and (now - last_flush) >= self.flush_interval:
                    self._process_batch(batch)
                    batch.clear()
                    last_flush = now
                # 如果已停止且队列空，退出循环
                if self._stop_event.is_set() and self.queue.empty():
                    break
                continue
            except Exception as e:
                sys.stderr.write(f"[AsyncLogHandler] Worker thread error: {str(e)}\n")
                break

        if batch:
            self._process_batch(batch)

    def _process_batch(self, batch):
        try:
            for record in batch:
                self.base_handler.handle(record)
        except Exception as e:
            sys.stderr.write(f"[AsyncLogHandler] Failed to write batch: {str(e)}\n")

    def stop(self):
        """停止处理器，等待队列中所有日志处理完成（不等待工作线程退出）"""
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        # 等待所有已放入队列的记录被处理完成
        self.queue.join()
        # 关闭基础处理器
        self.base_handler.close()

    def close(self):
        self.stop()
        super().close()


# ======================
# 配置辅助函数
# ======================
def _setup_console_handler(logger, console_enabled, console_format, datefmt, style):
    if not console_enabled:
        return
    if console_format is None:
        if style == "loguru":
            console_format = (
                    restrop("%(asctime)s", f=2) + " | " +
                    restrop("%(levelname)-8s", f=3) + " | " +
                    restrop("%(name)s", f=6) + ":" +
                    restrop("%(funcName)s", f=6) + ":" +
                    restrop("%(lineno)d", f=6) + " | " +
                    restrop("%(message)s", m=1, f=9)
            )
        else:
            console_format = (
                    restrop("[%(asctime)s] ", f=6) +
                    restrop("[%(threadName)s] ", f=5) +
                    restrop("[%(filename)s:%(lineno)-4d] ", f=4) +
                    restrop("[%(levelname)-7s] ", f=3) +
                    f"%(message)s" +
                    restrop(" %(ctx_dict)s", f=2)
            )
    elif console_format == "":
        console_format = (
                restrop("[%(asctime)s] ", f=6) +
                restrop("[%(threadName)s] ", f=5) +
                restrop("[%(filename)s:%(lineno)-4d] ", f=4) +
                restrop("[%(levelname)-7s] ", f=3) +
                f"%(message)s"
        )

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(console_format, datefmt=datefmt))
    logger.addHandler(handler)


def _setup_file_handler(logger, file_enabled, fpath, name, fname, level,
                        file_format, datefmt, maxBytes, backupCount, encoding,
                        style, async_logging, async_queue_size, async_batch_size):
    if not file_enabled or not fpath:
        return
    log_name = ensure_suffix(name, fname=fname, suffix=".log")
    logfile = os.path.join(fpath, log_name)
    ensure_file(logfile)

    if file_format is None:
        if style == "loguru":
            file_format = (
                "%(asctime)s | %(levelname)-8s | "
                "%(name)s:%(funcName)s:%(lineno)d | %(message)s"
            )
        else:
            file_format = (
                "[%(asctime)s] [%(threadName)s] [%(filename)s:%(lineno)d] "
                "%(levelname)-7s %(message)s %(ctx_dict)s"
            )
    elif file_format == "":
        file_format = (
            "[%(asctime)s] [%(threadName)s] [%(filename)s:%(lineno)d] "
            "%(levelname)-7s %(message)s"
        )

    try:
        file_handler = RotatingFileHandler(
            filename=logfile, encoding=encoding,
            maxBytes=maxBytes, backupCount=backupCount
        )
        file_handler.setFormatter(logging.Formatter(file_format, datefmt=datefmt))
        if async_logging:
            file_handler = _AsyncLogHandler(file_handler, queue_size=async_queue_size, batch_size=async_batch_size)
        logger.addHandler(file_handler)
    except Exception as e:
        sys.stderr.write(f"[set_log] Failed to create file handler: {str(e)}\n")


def _setup_json_handler(logger, json_enabled, fpath, name, fname,
                        datefmt, maxBytes, backupCount, encoding,
                        json_include_fields, json_exclude_fields,
                        async_logging, async_queue_size, async_batch_size):
    if not json_enabled or not fpath:
        return
    json_log_name = ensure_suffix(name, fname=fname, suffix=".json.log")
    json_logfile = os.path.join(fpath, json_log_name)
    ensure_file(json_logfile)

    try:
        json_handler = RotatingFileHandler(
            filename=json_logfile, encoding=encoding,
            maxBytes=maxBytes, backupCount=backupCount
        )
        json_formatter = _JSONFormatter(
            datefmt=datefmt,
            include_fields=json_include_fields,
            exclude_fields=json_exclude_fields
        )
        json_handler.setFormatter(json_formatter)
        if async_logging:
            json_handler = _AsyncLogHandler(json_handler, queue_size=async_queue_size, batch_size=async_batch_size)
        logger.addHandler(json_handler)
    except Exception as e:
        sys.stderr.write(f"[set_log] Failed to create JSON handler: {str(e)}\n")


def _add_custom_handlers(logger, custom_handlers, async_logging, async_queue_size, async_batch_size):
    if not custom_handlers:
        return
    for handler in custom_handlers:
        if async_logging and isinstance(handler, (RotatingFileHandler, logging.FileHandler)):
            handler = _AsyncLogHandler(handler, queue_size=async_queue_size, batch_size=async_batch_size)
        logger.addHandler(handler)


# ======================
# 公开接口
# ======================
@vargs({"level": set(LOG_LEVEL_DICT.keys())})
def set_log(
        name: Optional[str] = None,
        fpath: Optional[str] = "logs",
        fname: Optional[str] = None,
        level: Union[int, str] = 2,

        console_enabled: bool = True,
        console_format: Optional[str] = None,

        file_enabled: bool = True,
        file_format: Optional[str] = None,

        json_enabled: bool = False,
        json_include_fields: Optional[List[str]] = None,
        json_exclude_fields: Optional[List[str]] = None,

        datefmt: str = "%Y-%m-%d %H:%M:%S",
        maxBytes: int = 2 * 1024 * 1024,
        backupCount: int = 3,
        encoding: str = "utf-8",
        style: Literal["default", "loguru"] = "default",
        force_reconfigure: bool = False,

        context_fields: Optional[Dict[str, Any]] = None,
        custom_handlers: Optional[List[logging.Handler]] = None,

        async_logging: bool = True,
        async_queue_size: int = 10000,
        async_batch_size: int = 100,

        propagate: bool = False
) -> logging.Logger:
    """
        创建或获取高级日志记录器，支持控制台、文件和JSON日志输出

        :param name: 日志器名称，None 表示根日志器
        :param fpath: 日志文件存放目录路径（默认同目录的logs目录里）
        :param fname: 日志文件名（默认: "{name}.log"）
        :param level: 日志级别（默认: 2/INFO）

        :param console_enabled: 是否启用控制台日志（默认: True）
        :param console_format: 控制台日志格式（默认为None: 结构化文本模式）普通文本模式参考使用""空字符串或者自定义

        :param file_enabled: 是否启用文件日志（默认: True）
        :param file_format: 文件日志格式（默认为None: 详细文本格式）普通文本模式参考使用""空字符串或者自定义

        :param json_enabled: 是否启用JSON日志（默认: False）
        :param json_include_fields: JSON日志包含字段（默认: 全部）
        :param json_exclude_fields: JSON日志排除字段（默认: 无）

        :param datefmt: 日期格式（默认: "%Y-%m-%d %H:%M:%S"）
        :param maxBytes: 日志文件最大字节数（默认: 2MB）
        :param backupCount: 备份文件数量（默认: 3）
        :param encoding: 文件编码（默认: utf-8）
        :param style: 日志格式风格，可选 "default"（原有格式）或 "loguru"（Loguru 风格，控制台带颜色，文件简洁）
        :param force_reconfigure: 强制重新配置现有日志器（默认: False）

        :param context_fields: 额外上下文字段（字典格式）
        :param custom_handlers: 自定义日志处理器列表

        :param async_logging: 是否启用异步日志（默认True）
        :param async_queue_size: 异步队列大小（默认10000）
        :param async_batch_size: 异步批量写入大小（默认100）

        :param propagate: 日志消息是否从当前 logger 传递给其父 logger 默认为 False

        :return: 配置好的日志记录器
        """
    logger = logging.getLogger(name)

    if logger.handlers and not force_reconfigure:
        logger.setLevel(LOG_LEVEL_DICT[level])
        return logger

    if force_reconfigure:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    logger.setLevel(LOG_LEVEL_DICT[level])
    logger.propagate = propagate

    if not any(isinstance(f, _ContextFilter) for f in logger.filters):
        context_filter = _ContextFilter(context_fields)
        logger.addFilter(context_filter)

    if style == "loguru" and not any(isinstance(f, _LoguruStyleFilter) for f in logger.filters):
        logger.addFilter(_LoguruStyleFilter(module_format="module", project_root="."))

    _setup_console_handler(logger, console_enabled, console_format, datefmt, style)
    _setup_file_handler(logger, file_enabled, fpath, name, fname, level,
                        file_format, datefmt, maxBytes, backupCount, encoding,
                        style, async_logging, async_queue_size, async_batch_size)
    _setup_json_handler(logger, json_enabled, fpath, name, fname,
                        datefmt, maxBytes, backupCount, encoding,
                        json_include_fields, json_exclude_fields,
                        async_logging, async_queue_size, async_batch_size)
    _add_custom_handlers(logger, custom_handlers, async_logging, async_queue_size, async_batch_size)

    return logger
