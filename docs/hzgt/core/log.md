# log.py 文档

## 导航目录

- [set_log()](#set_log)

## 函数说明

### set_log()

**功能**：创建或获取高级日志记录器，支持控制台、文件和JSON日志输出，具有丰富的配置选项。

**参数**：
- `name`：日志器名称，None 表示根日志器
- `fpath`：日志文件存放目录路径（默认同目录的logs目录里）
- `fname`：日志文件名（默认: "{name}.log"）
- `level`：日志级别（默认: 2/INFO）
- `console_enabled`：是否启用控制台日志（默认: True）
- `console_format`：控制台日志格式（默认为None: 结构化文本模式）
- `file_enabled`：是否启用文件日志（默认: True）
- `file_format`：文件日志格式（默认为None: 详细文本格式）
- `json_enabled`：是否启用JSON日志（默认: False）
- `json_include_fields`：JSON日志包含字段（默认: 全部）
- `json_exclude_fields`：JSON日志排除字段（默认: 无）
- `datefmt`：日期格式（默认: "%Y-%m-%d %H:%M:%S"）
- `maxBytes`：日志文件最大字节数（默认: 2MB）
- `backupCount`：备份文件数量（默认: 3）
- `encoding`：文件编码（默认: utf-8）
- `force_reconfigure`：强制重新配置现有日志器（默认: False）
- `context_fields`：额外上下文字段（字典格式）
- `custom_handlers`：自定义日志处理器列表
- `async_logging`：是否启用异步日志（默认True）
- `async_queue_size`：异步队列大小（默认10000）
- `async_batch_size`：异步批量写入大小（默认100）

**返回值**：`logging.Logger` - 配置好的日志记录器

**使用示例**：

```python
from hzgt import set_log

# 基本用法
logger = set_log("myapp")
logger.info("Application started")

# 高级配置
logger = set_log(
    "myapp",
    fpath="logs",
    fname="application.log",
    level="debug",
    json_enabled=True,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

# 带上下文的日志
logger.info(
    "User logged in",
    extra={
        "ctx_user_id": 123,
        "ctx_username": "alice"
    }
)

# 记录异常
try:
    1 / 0
except Exception as e:
    logger.error("An error occurred", exc_info=True)
```

**日志级别说明**：
- 0: NOTSET
- 1: DEBUG
- 2: INFO
- 3: WARNING
- 4: ERROR
- 5: CRITICAL

也可以使用字符串形式的日志级别，如 "debug", "info", "warning", "error", "critical"。