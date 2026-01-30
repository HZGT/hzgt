# SQLiteop 类

## 功能说明
SQLiteop 是一个封装了 SQLite 数据库操作的类，支持连接管理、数据 CRUD 操作、事务处理等功能。**无需编写 SQL 语句**，通过简单的方法调用即可完成数据库操作。

## 初始化方法

### `__init__(self, db_name: str, logger: Optional[Logger] = None)`

**参数说明：**
- `db_name` (str): 数据库文件路径
- `logger` (logging.Logger, 可选): 日志记录器

**返回值：**
- 无

**示例：**
```python
from hzgt.tools import SQLiteop

# 基本用法
db = SQLiteop('test.db')

# 使用自定义日志记录器
db = SQLiteop('test.db', logger=custom_logger)
```

## 主要方法

### 连接管理

#### `connect(self)`

**功能：** 建立数据库连接

**参数说明：**
- 无

**返回值：**
- 无

#### `close(self)`

**功能：** 关闭数据库连接

**参数说明：**
- 无

**返回值：**
- 无

#### `start(self)`

**功能：** 建立数据库连接（与connect方法相同）

**参数说明：**
- 无

**返回值：**
- 无

#### `disconnect(self)`

**功能：** 关闭数据库连接（与close方法相同）

**参数说明：**
- 无

**返回值：**
- 无

#### `commit(self)`

**功能：** 提交事务

**参数说明：**
- 无

**返回值：**
- 无

#### `rollback(self)`

**功能：** 回滚事务

**参数说明：**
- 无

**返回值：**
- 无

#### `transaction(self)`

**功能：** 事务上下文管理器

**参数说明：**
- 无

**返回值：**
- 上下文管理器

**示例：**
```python
with db.transaction():
    db.insert('users', {'name': 'John', 'age': 30})
    db.insert('users', {'name': 'Jane', 'age': 25})
    # 如果发生异常，事务会自动回滚
```

### 表操作

#### `select_table(self, table_name: str)`

**功能：** 选择表

**参数说明：**
- `table_name` (str): 表名

**返回值：**
- 无

#### `get_tables(self) -> list[str]`

**功能：** 获取所有的表名

**参数说明：**
- 无

**返回值：**
- `list`: 表名列表

#### `table_exists(self, table_name: str) -> bool`

**功能：** 检查表是否存在

**参数说明：**
- `table_name` (str): 表名

**返回值：**
- `bool`: 表是否存在

#### `create_table(self, table_name: str, columns: Dict[str, str], primary_key: List[str] = None, if_not_exists: bool = True, **kwargs)`

**功能：** 创建表

**参数说明：**
- `table_name` (str): 表名
- `columns` (dict): 列定义 {列名: 类型}
- `primary_key` (list, 可选): 主键列表
- `if_not_exists` (bool, 可选): 是否添加IF NOT EXISTS子句
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- 无

**示例：**
```python
# 创建用户表
db.create_table(
    'users',
    {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'name': 'TEXT NOT NULL',
        'age': 'INTEGER',
        'email': 'TEXT UNIQUE'
    }
)
```

#### `drop_table(self, table_name: str = '', if_exists: bool = True)`

**功能：** 删除表

**参数说明：**
- `table_name` (str, 可选): 表名
- `if_exists` (bool, 可选): 是否添加IF EXISTS子句

**返回值：**
- 无

#### `get_columns(self, table_name: str) -> List[str]`

**功能：** 获取表的列名列表

**参数说明：**
- `table_name` (str): 表名

**返回值：**
- `list`: 列名列表

#### `column_exists(self, table_name: str, column_name: str) -> bool`

**功能：** 检查表中是否存在某列

**参数说明：**
- `table_name` (str): 表名
- `column_name` (str): 列名

**返回值：**
- `bool`: 列是否存在

### 数据操作

#### `insert(self, table_name: str = '', record: Union[Dict[str, Any], List[Dict[str, Any]]] = None, return_id: bool = False, **kwargs)`

**功能：** 插入数据

**参数说明：**
- `table_name` (str, 可选): 表名
- `record` (dict/list, 可选): 记录或记录列表
- `return_id` (bool, 可选): 是否返回插入ID
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `int` 或 `None`: 插入ID（如果return_id为True）

**示例：**
```python
# 插入单条记录
user_id = db.insert('users', {'name': 'John', 'age': 30}, return_id=True)
print(f"插入的用户ID: {user_id}")

# 批量插入
users = [
    {'name': 'Alice', 'age': 28},
    {'name': 'Bob', 'age': 32},
    {'name': 'Charlie', 'age': 25}
]
db.insert('users', users)
print("批量插入完成")
```

#### `select(self, table_name: str = "", conditions: Dict = None, order: Dict[str, bool] = None, fields: List[str] = None, limit: int = None, offset: int = None, bool_dict: bool = False, **kwargs)`

**功能：** 查询数据

**参数说明：**
- `table_name` (str, 可选): 表名
- `conditions` (dict, 可选): 查询条件
- `order` (dict, 可选): 排序条件
- `fields` (list, 可选): 查询字段
- `limit` (int, 可选): 限制记录数
- `offset` (int, 可选): 跳过记录数
- `bool_dict` (bool, 可选): 返回格式为 True 字典Dict[str, Any] False 列表List[Dict[str, Any]]
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `list` 或 `dict`: 查询结果列表或字典

**示例：**
```python
# 基本查询
users = db.select('users')
print(users)

# 带条件查询
adult_users = db.select('users', conditions={'age': {'>=': 18}})
print(adult_users)

# 带排序和限制
users_sorted = db.select('users', order={'age': False}, limit=10)
print(users_sorted)

# 只查询特定字段
user_names = db.select('users', fields=['name', 'email'])
print(user_names)
```

#### `update(self, table_name: str = '', update_values: Dict[str, Any] = None, conditions: Dict = None, **kwargs)`

**功能：** 更新数据

**参数说明：**
- `table_name` (str, 可选): 表名
- `update_values` (dict, 可选): 更新值
- `conditions` (dict, 可选): 更新条件
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `int`: 更新的行数

**示例：**
```python
# 更新用户信息
rows_updated = db.update('users', {'age': 31}, conditions={'name': 'John'})
print(f"更新了 {rows_updated} 条记录")

# 批量更新
rows_updated = db.update('users', {'status': 'active'}, conditions={'age': {'>=': 18}})
print(f"批量更新了 {rows_updated} 条记录")
```

#### `delete(self, table_name: str = '', conditions: Dict = None, **kwargs)`

**功能：** 删除数据

**参数说明：**
- `table_name` (str, 可选): 表名
- `conditions` (dict, 可选): 删除条件
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `int`: 删除的行数

**示例：**
```python
# 删除特定用户
rows_deleted = db.delete('users', conditions={'name': 'John'})
print(f"删除了 {rows_deleted} 条记录")

# 批量删除
rows_deleted = db.delete('users', conditions={'age': {'<': 18}})
print(f"批量删除了 {rows_deleted} 条记录")
```

#### `batch_insert(self, table_name: str, records: List[Dict[str, Any]], batch_size: int = 1000, **kwargs)`

**功能：** 批量插入数据

**参数说明：**
- `table_name` (str): 表名
- `records` (list): 记录列表
- `batch_size` (int, 可选): 每批大小
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `int`: 插入的记录数

**示例：**
```python
# 批量插入大量数据
users = []
for i in range(10000):
    users.append({
        'name': f'User {i}',
        'age': 20 + i % 30,
        'email': f'user{i}@example.com'
    })

inserted = db.batch_insert('users', users, batch_size=500)
print(f"成功插入 {inserted} 条记录")
```

### 高级功能

#### `join(self, main_table: str, joins: List[Tuple[str, str, JoinType, Dict[str, str]]], conditions: Dict = None, fields: Dict[str, List[str]] = None, order: Dict[str, bool] = None, limit: int = None, offset: int = None, bool_dict: bool = False, **kwargs)`

**功能：** 执行连接查询

**参数说明：**
- `main_table` (str): 主表
- `joins` (list): 连接定义
- `conditions` (dict, 可选): 查询条件
- `fields` (dict, 可选): 查询字段
- `order` (dict, 可选): 排序条件
- `limit` (int, 可选): 限制记录数
- `offset` (int, 可选): 跳过记录数
- `bool_dict` (bool, 可选): 返回格式为 True 字典Dict[str, Any] False 列表List[Dict[str, Any]]
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `list` 或 `dict`: 查询结果列表或字典

**示例：**
```python
from hzgt.tools import JoinType

# 执行内连接查询
results = db.join(
    'users',
    [('orders', 'o', JoinType.INNER, {'id': 'user_id'})],
    conditions={'users.age': {'>=': 18}},
    fields={'users': ['name', 'age'], 'o': ['order_id', 'amount']}
)
print(results)
```

#### `migrate_db(self, table_name: str, new_columns: Dict[str, str]) -> None`

**功能：** 数据库迁移: 添加新列

**参数说明：**
- `table_name` (str): 表名
- `new_columns` (dict): 新列名和类型的字典

**返回值：**
- 无

**示例：**
```python
# 添加新列
db.migrate_db('users', {
    'status': 'TEXT DEFAULT "active"',
    'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
})
print("数据库迁移完成")
```

#### `export_to_csv(self, table_name: str, csv_path: str) -> None`

**功能：** 将表数据导出到 CSV 文件

**参数说明：**
- `table_name` (str): 表名
- `csv_path` (str): CSV 文件路径

**返回值：**
- 无

**示例：**
```python
# 导出数据到CSV
db.export_to_csv('users', 'users.csv')
print("数据导出完成")
```

#### `import_from_csv(self, table_name: str, csv_path: str) -> None`

**功能：** 从 CSV 文件导入数据到表

**参数说明：**
- `table_name` (str): 表名
- `csv_path` (str): CSV 文件路径

**返回值：**
- 无

**示例：**
```python
# 从CSV导入数据
db.import_from_csv('users', 'users.csv')
print("数据导入完成")
```

#### `execute_sql_script(self, script_path: str) -> None`

**功能：** 执行 SQL 脚本文件

**参数说明：**
- `script_path` (str): SQL 脚本文件路径

**返回值：**
- 无

**示例：**
```python
# 执行SQL脚本
db.execute_sql_script('init.sql')
print("SQL脚本执行完成")
```

#### `backup_db(self, target_db: str) -> None`

**功能：** 备份数据库

**参数说明：**
- `target_db` (str): 目标数据库文件名

**返回值：**
- 无

**示例：**
```python
# 备份数据库
db.backup_db('backup.db')
print("数据库备份完成")
```

#### `enable_wal_mode(self) -> None`

**功能：** 启用 WAL 模式（Write-Ahead Logging）, 提高并发性能

**参数说明：**
- 无

**返回值：**
- 无

**示例：**
```python
# 启用WAL模式
db.enable_wal_mode()
print("WAL模式已启用")
```

## 上下文管理器

SQLiteop 类支持上下文管理器协议，可以使用 `with` 语句自动管理连接：

```python
with SQLiteop('test.db') as db:
    db.insert('users', {'name': 'John', 'age': 30})
    result = db.select('users')
    print(result)
# 离开上下文时，连接会自动关闭
```

## 错误处理

SQLiteop 类内部会捕获并记录数据库操作中的错误，同时提供详细的错误信息。如果需要自定义错误处理，可以通过捕获 `RuntimeError` 异常来实现。

## 注意事项

1. **无需编写 SQL 语句**：所有数据库操作都通过方法调用完成，内部会自动生成和执行 SQL 语句
2. **自动连接管理**：支持上下文管理器，自动处理连接的建立和关闭
3. **事务支持**：支持事务处理，确保数据一致性
4. **批量操作**：支持批量插入数据，提高性能
5. **数据导入导出**：支持从 CSV 文件导入数据和导出数据到 CSV 文件
6. **数据库备份**：支持数据库备份功能
7. **WAL 模式**：支持启用 WAL 模式，提高并发性能
8. **数据库迁移**：支持添加新列的数据库迁移功能

## 条件表达式

SQLiteop 支持多种条件表达式，用于 `select`、`update`、`delete` 等方法的 `conditions` 参数：

### 基本操作符

- `{'age': 18}`: 等于 (age = 18)
- `{'age': {'>': 18}}`: 大于 (age > 18)
- `{'age': {'<': 18}}`: 小于 (age < 18)
- `{'age': {'>=': 18}}`: 大于等于 (age >= 18)
- `{'age': {'<=': 18}}`: 小于等于 (age <= 18)
- `{'age': {'!=': 18}}`: 不等于 (age != 18)
- `{'name': {'LIKE': '%John%'}}`: 模糊匹配 (name LIKE '%John%')
- `{'age': {'IN': [18, 20, 22]}}`: 包含于 (age IN (18, 20, 22))
- `{'age': {'BETWEEN': [18, 30]}}`: 介于 (age BETWEEN 18 AND 30)
- `{'email': None}`: 为空 (email IS NULL)

### 逻辑组合

- `{'$and': [{'age': {'>=': 18}}, {'age': {'<=': 30}}]}`: 并且 (age >= 18 AND age <= 30)
- `{'$or': [{'age': {'<': 18}}, {'age': {'>': 60}}]}`: 或者 (age < 18 OR age > 60)

## 排序表达式

排序表达式用于 `select` 方法的 `order` 参数：

- `{'age': True}`: 按年龄升序排序
- `{'age': False}`: 按年龄降序排序
- `{'name': True, 'age': False}`: 先按姓名升序，再按年龄降序