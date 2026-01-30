# Mysqlop 类

## 功能说明
Mysqlop 是一个封装了 MySQL 数据库操作的类，支持连接管理、数据 CRUD 操作、事务处理等功能。**无需编写 SQL 语句**，通过简单的方法调用即可完成数据库操作。

## 初始化方法

### `__init__(self, host: str, port: int, user: str, passwd: str, database: str = None, charset: str = "utf8", logger: Logger= None, autoreconnect: bool = True, reconnect_retries: int = 3, pool_size: int = 5, enable_history: bool = True, history_max_records: int = 100, history_auto_save: bool = False, history_save_path: Optional[str] = None)`

**参数说明：**
- `host` (str): MySQL数据库地址
- `port` (int): 端口
- `user` (str): 用户名
- `passwd` (str): 密码
- `database` (str, 可选): 初始连接的数据库名
- `charset` (str, 可选): 编码，默认 UTF8
- `logger` (logging.Logger, 可选): 日志记录器
- `autoreconnect` (bool, 可选): 是否自动重连，默认 True
- `reconnect_retries` (int, 可选): 重连次数
- `pool_size` (int, 可选): 连接池大小
- `enable_history` (bool, 可选): 是否启用SQL历史记录功能
- `history_max_records` (int, 可选): 历史记录最大数量
- `history_auto_save` (bool, 可选): 是否自动保存历史记录到文件
- `history_save_path` (str, 可选): 历史记录保存路径

**返回值：**
- 无

**示例：**
```python
from hzgt.tools import Mysqlop

# 基本用法
db1 = Mysqlop(host='localhost', port=3306, user='root', passwd='password', database='test_db')

# 
db2 = Mysqlop(
    host='localhost', port=3306, 
    user='root', passwd='password', 
    database='test_db',
    pool_size=10,
    enable_history=True,
    history_max_records=500
)
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

### 数据库操作

#### `select_db(self, dbname: str)`

**功能：** 选择数据库

**参数说明：**
- `dbname` (str): 数据库名

**返回值：**
- 无

#### `get_all_db(self) -> List[str]`

**功能：** 获取所有数据库名

**参数说明：**
- 无

**返回值：**
- `list`: 所有数据库名列表

#### `get_all_nonsys_db(self) -> List[str]`

**功能：** 获取除系统数据库外的所有数据库名

**参数说明：**
- 无

**返回值：**
- `list`: 非系统数据库名列表

#### `create_db(self, dbname: str, bool_autoselect: bool = True)`

**功能：** 创建数据库

**参数说明：**
- `dbname` (str): 需要创建的数据库名
- `bool_autoselect` (bool, 可选): 是否自动选择该数据库

**返回值：**
- 无

#### `drop_db(self, dbname: str)`

**功能：** 删除数据库

**参数说明：**
- `dbname` (str): 需要删除的数据库名

**返回值：**
- 无

### 表操作

#### `select_table(self, tablename: str)`

**功能：** 选择表

**参数说明：**
- `tablename` (str): 表名

**返回值：**
- 无

#### `get_tables(self, dbname: str = "") -> List[str]`

**功能：** 获取指定数据库的所有表

**参数说明：**
- `dbname` (str, 可选): 数据库名，默认为当前选择的数据库

**返回值：**
- `list`: 表名列表

#### `table_exists(self, tablename: str) -> bool`

**功能：** 检查表是否存在

**参数说明：**
- `tablename` (str): 表名

**返回值：**
- `bool`: 表是否存在

#### `create_table(self, tablename: str, attr_dict: Dict[str, str], primary_key: List[str] = None, bool_id: bool = True, bool_autoselect: bool = True, **kwargs)`

**功能：** 创建表

**参数说明：**
- `tablename` (str): 需要创建的表名
- `attr_dict` (dict): 字典 {列名: MySQL数据类型}, 表示表中的列及其数据类型
- `primary_key` (list, 可选): 主键列表
- `bool_id` (bool, 可选): 是否添加 id 为自增主键
- `bool_autoselect` (bool, 可选): 创建表格后是否自动选择该表格
- `**kwargs` (dict, 可选): 额外参数 (如 engine, charset, collate, indices)

**返回值：**
- 无

**示例：**
```python
# 创建用户表
db.create_table(
    'users',
    {
        'name': 'VARCHAR(255) NOT NULL',
        'age': 'INT',
        'email': 'VARCHAR(255) UNIQUE'
    },
    primary_key=['id'],
    bool_id=True
)
```

#### `drop_table(self, tablename: str = '', if_exists: bool = True)`

**功能：** 删除表

**参数说明：**
- `tablename` (str, 可选): 表名，默认为当前选择的表
- `if_exists` (bool, 可选): 是否添加IF EXISTS子句

**返回值：**
- 无

#### `purge(self, tablename: str = '')`

**功能：** 清空表数据

**参数说明：**
- `tablename` (str, 可选): 表名，默认为当前选择的表

**返回值：**
- 无

### 数据操作

#### `insert(self, tablename: str = '', record: Union[Dict[str, Any], List[Dict[str, Any]]] = None, ignore_duplicates: bool = False, return_id: bool = False, **kwargs)`

**功能：** 插入数据

**参数说明：**
- `tablename` (str, 可选): 表名，默认为当前选择的表
- `record` (dict/list, 可选): 要插入的记录或记录列表
- `ignore_duplicates` (bool, 可选): 是否忽略重复记录
- `return_id` (bool, 可选): 是否返回插入ID
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `int` 或 `None`: 如果return_id为True，返回插入ID；否则返回None

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

#### `select(self, tablename: str = "", conditions: Dict = None, order: Dict[str, bool] = None, fields: List[str] = None, limit: int = None, offset: int = None, bool_dict: bool = False, stream: bool = False, size: int = 5000, use_server_side_cursor: bool = True, **kwargs) -> Union[list[dict[str, Any]], dict[str, Any], Generator[dict[str, Any], None, None]]`

**功能：** 查询数据

**参数说明：**
- `tablename` (str, 可选): 表名，默认为当前选择的表
- `conditions` (dict, 可选): 查询条件
- `order` (dict, 可选): 排序 {列名: 是否升序}
- `fields` (list, 可选): 要查询的字段列表
- `limit` (int, 可选): 限制返回记录数
- `offset` (int, 可选): 跳过前N条记录
- `bool_dict` (bool, 可选): 是否以字典形式返回结果 {列名: [列值列表]}
- `stream` (bool, 可选): 是否以流式方式返回结果，优先级高于bool_dict
- `size` (int, 可选): 流式查询时的批量大小
- `use_server_side_cursor` (bool, 可选): 是否使用服务器端游标（减少内存使用）
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- 如果stream为True: 返回结果迭代器
- 如果bool_dict为False: 返回查询结果列表
- 如果bool_dict为True: 返回字典 {列名: [列值列表]}

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

# 流式查询（适合大数据量）
for user in db.select('users', stream=True, size=1000):
    print(user)
```

#### `update(self, tablename: str = '', update_values: Dict[str, Any] = None, conditions: Dict = None, **kwargs)`

**功能：** 更新数据

**参数说明：**
- `tablename` (str, 可选): 表名，默认为当前选择的表
- `update_values` (dict, 可选): 要更新的值
- `conditions` (dict, 可选): 更新条件
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `bool`: 更新是否成功

**示例：**
```python
# 更新用户信息
db.update('users', {'age': 31}, conditions={'name': 'John'})
print("用户信息更新成功")

# 批量更新
db.update('users', {'status': 'active'}, conditions={'age': {'>=': 18}})
print("批量更新成功")
```

#### `delete(self, tablename: str = '', conditions: Dict = None, **kwargs)`

**功能：** 删除数据

**参数说明：**
- `tablename` (str, 可选): 表名，默认为当前选择的表
- `conditions` (dict, 可选): 删除条件
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- `bool`: 删除是否成功

**示例：**
```python
# 删除特定用户
db.delete('users', conditions={'name': 'John'})
print("用户删除成功")

# 批量删除
db.delete('users', conditions={'age': {'<': 18}})
print("批量删除成功")
```

#### `paginate(self, tablename: str = "", conditions: Dict = None, fields: List[str] = None, order: Dict[str, bool] = None, page: int = 1, page_size: int = 100) -> Tuple[List[Dict[str, Any]], int]`

**功能：** 分页查询

**参数说明：**
- `tablename` (str, 可选): 表名，默认为当前选择的表
- `conditions` (dict, 可选): 查询条件
- `fields` (list, 可选): 要查询的字段列表
- `order` (dict, 可选): 排序 {列名: 是否升序}
- `page` (int, 可选): 页码，从1开始
- `page_size` (int, 可选): 每页记录数

**返回值：**
- `tuple`: (当前页数据, 总记录数)

**示例：**
```python
# 分页查询第2页，每页10条
users, total = db.paginate('users', page=2, page_size=10)
print(f"第2页用户数据: {users}")
print(f"总用户数: {total}")
```

### 高级功能

#### `analyze_query(self, sql: str, args: Optional[Union[tuple, dict, list]] = None) -> Dict[str, Any]`

**功能：** 分析查询执行计划并提供优化建议

**参数说明：**
- `sql` (str): SQL查询语句
- `args` (tuple/dict/list, 可选): 查询参数

**返回值：**
- `dict`: 分析报告

#### `shard_query(self, tablename: str, id_field: str, conditions: Dict = None, fields: List[str] = None, shard_size: int = 10000, process_func: Callable = None)`

**功能：** 分片查询大表，自动按主键或指定字段进行分片查询

**参数说明：**
- `tablename` (str): 表名
- `id_field` (str): 用于分片的ID字段（应该有索引）
- `conditions` (dict, 可选): 查询条件
- `fields` (list, 可选): 要查询的字段列表
- `shard_size` (int, 可选): 每个分片大小
- `process_func` (callable, 可选): 处理每个分片数据的函数

**返回值：**
- `list`: 处理结果列表，如果没有process_func则返回所有数据

**示例：**
```python
def process_shard(data):
    """处理每个分片的数据"""
    # 计算分片内的平均年龄
    if not data:
        return 0
    total_age = sum(user['age'] for user in data)
    return total_age / len(data)

# 分片查询并处理结果
avg_ages = db.shard_query('users', 'id', process_func=process_shard)
print(f"各分片的平均年龄: {avg_ages}")
print(f"总体平均年龄: {sum(avg_ages) / len(avg_ages)}")
```

#### `join(self, main_table: str, joins: List[Tuple[str, str, JoinType, Dict[str, str]]], conditions: Dict = None, fields: Dict[str, List[str]] = None, order: Dict[str, bool] = None, limit: int = None, offset: int = None, bool_dict: bool = False, **kwargs)`

**功能：** 执行连接查询

**参数说明：**
- `main_table` (str): 主表
- `joins` (list): 连接表定义 [(表名, 别名, 连接类型, {主表字段: 连接表字段}), ...]
- `conditions` (dict, 可选): 查询条件
- `fields` (dict, 可选): 查询字段 {表别名: [字段名, ...], ...}
- `order` (dict, 可选): 排序 {字段名: 是否升序}
- `limit` (int, 可选): 限制返回记录数
- `offset` (int, 可选): 跳过前N条记录
- `bool_dict` (bool, 可选): 返回格式为 True 字典Dict[str, Any] False 列表List[Dict[str, Any]]
- `**kwargs` (dict, 可选): 其他参数

**返回值：**
- 查询结果

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

## 上下文管理器

Mysqlop 类支持上下文管理器协议，可以使用 `with` 语句自动管理连接：

```python
with Mysqlop(host='localhost', user='root', password='password', database='test_db') as db:
    db.insert('users', {'name': 'John', 'age': 30})
    result = db.select('users')
    print(result)
# 离开上下文时，连接会自动关闭
```

## 错误处理

Mysqlop 类内部会捕获并记录数据库操作中的错误，同时提供详细的错误信息。如果需要自定义错误处理，可以通过捕获 `RuntimeError` 异常来实现。

## 注意事项

1. **无需编写 SQL 语句**：所有数据库操作都通过方法调用完成，内部会自动生成和执行 SQL 语句
2. **参数化查询**：内部使用参数化查询，防止 SQL 注入攻击
3. **连接池管理**：支持连接池，提高并发性能
4. **自动重连**：支持自动重连功能，提高稳定性
5. **流式查询**：支持流式查询，适合处理大数据量
6. **SQL 历史记录**：支持 SQL 执行历史记录，方便调试和审计
7. **事务支持**：支持事务处理，确保数据一致性

## 条件表达式

Mysqlop 支持多种条件表达式，用于 `select`、`update`、`delete` 等方法的 `conditions` 参数：

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