# SQLHistoryRecord 和 SQLHistory 类

## 功能说明
SQLHistoryRecord 是一个数据类，用于存储 SQL 执行历史记录的详细信息。SQLHistory 是一个管理 SQL 历史记录的类，支持添加、查询、统计和导出历史记录等功能。

## SQLHistoryRecord 类

### 初始化方法

### `__init__(self, id: int, sql: str, params: Optional[Any], execution_time: datetime, duration: float, status: SQLExecutionStatus, affected_rows: Optional[int], result_count: Optional[int], error_message: Optional[str], database: Optional[str], table: Optional[str], operation_type: str, user_tag: Optional[str])`

**参数说明：**
- `id` (int): 记录ID
- `sql` (str): SQL语句
- `params` (Any, 可选): 参数
- `execution_time` (datetime): 执行时间
- `duration` (float): 执行耗时(秒)
- `status` (SQLExecutionStatus): 执行状态
- `affected_rows` (int, 可选): 影响行数
- `result_count` (int, 可选): 结果行数
- `error_message` (str, 可选): 错误信息
- `database` (str, 可选): 数据库名
- `table` (str, 可选): 表名
- `operation_type` (str): 操作类型 (SELECT, INSERT, UPDATE, DELETE, etc.)
- `user_tag` (str, 可选): 用户标签

**返回值：**
- 无

### 主要方法

#### `to_dict(self) -> Dict[str, Any]`

**功能：** 转换为字典

**参数说明：**
- 无

**返回值：**
- `dict`: 转换后的字典

#### `from_dict(cls, data: Dict[str, Any]) -> 'SQLHistoryRecord'`

**功能：** 从字典创建实例

**参数说明：**
- `data` (dict): 字典数据

**返回值：**
- `SQLHistoryRecord`: 创建的实例

#### `get_sql_preview(self, max_length: int = 100) -> str`

**功能：** 获取SQL预览（截断长SQL）

**参数说明：**
- `max_length` (int, 可选): 最大长度，默认100

**返回值：**
- `str`: SQL预览

#### `is_query_operation(self) -> bool`

**功能：** 判断是否为查询操作

**参数说明：**
- 无

**返回值：**
- `bool`: 是否为查询操作

#### `is_modification_operation(self) -> bool`

**功能：** 判断是否为修改操作

**参数说明：**
- 无

**返回值：**
- `bool`: 是否为修改操作

## SQLHistory 类

### 初始化方法

### `__init__(self, max_records: int = 100, auto_save: bool = False, save_path: Optional[str] = None, logger: Optional[Logger] = None)`

**参数说明：**
- `max_records` (int, 可选): 最大记录数，超过时自动清理旧记录，默认100
- `auto_save` (bool, 可选): 是否自动保存到文件，默认False
- `save_path` (str, 可选): 保存文件路径
- `logger` (logging.Logger, 可选): 日志记录器

**返回值：**
- 无

**示例：**
```python
from hzgt.tools import SQLHistory

# 基本用法
history = SQLHistory()

# 配置自动保存
history = SQLHistory(auto_save=True, save_path='sql_history.json')

# 配置最大记录数
history = SQLHistory(max_records=500)
```

### 主要方法

#### `add_record(self, sql: str, params: Optional[Any] = None, duration: float = 0.0, status: SQLExecutionStatus = SQLExecutionStatus.SUCCESS, affected_rows: Optional[int] = None, result_count: Optional[int] = None, error_message: Optional[str] = None, database: Optional[str] = None, table: Optional[str] = None, user_tag: Optional[str] = None) -> SQLHistoryRecord`

**功能：** 添加历史记录

**参数说明：**
- `sql` (str): SQL语句
- `params` (Any, 可选): 参数
- `duration` (float, 可选): 执行耗时，默认0.0
- `status` (SQLExecutionStatus, 可选): 执行状态，默认SUCCESS
- `affected_rows` (int, 可选): 影响行数
- `result_count` (int, 可选): 结果行数
- `error_message` (str, 可选): 错误信息
- `database` (str, 可选): 数据库名
- `table` (str, 可选): 表名
- `user_tag` (str, 可选): 用户标签

**返回值：**
- `SQLHistoryRecord`: 创建的历史记录

#### `get_all_records(self) -> List[SQLHistoryRecord]`

**功能：** 获取所有历史记录

**参数说明：**
- 无

**返回值：**
- `list`: 历史记录列表

#### `get_recent_records(self, count: int = 10) -> List[SQLHistoryRecord]`

**功能：** 获取最近的N条记录

**参数说明：**
- `count` (int, 可选): 记录数，默认10

**返回值：**
- `list`: 最近的历史记录列表

#### `get_records_by_time_range(self, start_time: datetime, end_time: Optional[datetime] = None) -> List[SQLHistoryRecord]`

**功能：** 按时间范围获取记录

**参数说明：**
- `start_time` (datetime): 开始时间
- `end_time` (datetime, 可选): 结束时间，默认为当前时间

**返回值：**
- `list`: 符合条件的记录列表

#### `get_records_by_operation(self, operation_type: str) -> List[SQLHistoryRecord]`

**功能：** 按操作类型获取记录

**参数说明：**
- `operation_type` (str): 操作类型

**返回值：**
- `list`: 符合条件的记录列表

#### `get_records_by_status(self, status: SQLExecutionStatus) -> List[SQLHistoryRecord]`

**功能：** 按执行状态获取记录

**参数说明：**
- `status` (SQLExecutionStatus): 执行状态

**返回值：**
- `list`: 符合条件的记录列表

#### `get_records_by_database(self, database: str) -> List[SQLHistoryRecord]`

**功能：** 按数据库获取记录

**参数说明：**
- `database` (str): 数据库名

**返回值：**
- `list`: 符合条件的记录列表

#### `get_records_by_table(self, table: str) -> List[SQLHistoryRecord]`

**功能：** 按表名获取记录

**参数说明：**
- `table` (str): 表名

**返回值：**
- `list`: 符合条件的记录列表

#### `search_records(self, keyword: str, case_sensitive: bool = False) -> List[SQLHistoryRecord]`

**功能：** 搜索包含关键词的记录

**参数说明：**
- `keyword` (str): 搜索关键词
- `case_sensitive` (bool, 可选): 是否区分大小写，默认False

**返回值：**
- `list`: 匹配的记录列表

#### `get_statistics(self) -> Dict[str, Any]`

**功能：** 获取历史记录统计信息

**参数说明：**
- 无

**返回值：**
- `dict`: 统计信息

#### `get_slow_queries(self, threshold: float = 1.0) -> List[SQLHistoryRecord]`

**功能：** 获取慢查询记录

**参数说明：**
- `threshold` (float, 可选): 慢查询阈值(秒)，默认1.0

**返回值：**
- `list`: 慢查询记录列表

#### `get_failed_queries(self) -> List[SQLHistoryRecord]`

**功能：** 获取失败的查询记录

**参数说明：**
- 无

**返回值：**
- `list`: 失败的查询记录列表

#### `clear_records(self, keep_recent: int = 0)`

**功能：** 清空历史记录

**参数说明：**
- `keep_recent` (int, 可选): 保留最近N条记录，默认0

**返回值：**
- 无

#### `export_to_dict(self) -> List[Dict[str, Any]]`

**功能：** 导出为字典列表

**参数说明：**
- 无

**返回值：**
- `list`: 字典列表

#### `import_from_dict(self, data: List[Dict[str, Any]])`

**功能：** 从字典列表导入

**参数说明：**
- `data` (list): 字典列表

**返回值：**
- 无

#### `save_to_file(self, file_path: Optional[str] = None)`

**功能：** 保存历史记录到文件

**参数说明：**
- `file_path` (str, 可选): 文件路径，默认使用初始化时的路径

**返回值：**
- 无

#### `load_from_file(self, file_path: Optional[str] = None)`

**功能：** 从文件加载历史记录

**参数说明：**
- `file_path` (str, 可选): 文件路径，默认使用初始化时的路径

**返回值：**
- 无