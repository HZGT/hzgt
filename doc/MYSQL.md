
---
`类[class]: Mysqlop()`
---

`Mysqlop` 是一个用于简化 `MySQL数据库操作` 的 Python 类, 它封装了数据库连接、表管理、数据操作及权限控制等核心功能. 以下将详细介绍该类的使用方法和内部机制. 

`Mysqlop` is a Python class for simplifying `MySQL database operations`, which encapsulates core functionalities such as connection management, table operations, data manipulation, and privilege control. The following describes in detail how to use the Mysqlop class and how it works.

---
- [构造函数参数](#constructor-parameters)
- [核心方法](#core-methods)
  - [连接与断开](#connect-and-disconnect)
  - [数据库管理](#database-management)
  - [表操作](#table-operations)
  - [数据操作](#data-operations)
  - [权限管理](#permission-management)
- [使用示例](#examples)
- [注意事项](#important-notes)
---

### constructor parameters
### 构造函数参数[Constructor Parameters]
- `host`: MySQL 服务器地址(必填), 例如 `"localhost"`
- `port`: MySQL 服务器端口(必填), 例如 `3306`
- `user`: 数据库用户名(必填)
- `passwd`: 数据库密码(必填)
- `charset`: 字符编码(默认 `"utf8"`)
- `logger`: 自定义日志记录器. 若未提供, 将自动创建默认日志(保存至 `"logs/mysql.log"`)
- `autocommit`: 是否自动提交处理(默认`False`)
- `autoreconnect`: 是否自动重连(默认`True`)
- `reconnect_retries`: 重连次数(默认`3`)
### core methods
### 核心方法[Core Methods]
#### connect and disconnect
#### 连接与断开
1. `start()` / `connect()`
- 功能:  建立数据库连接
- 日志提示:  
  - 成功:  MYSQL数据库连接成功
  - 失败:  抛出连接异常(如认证失败、网络错误)

2. `close()`
- 功能:  关闭数据库连接
- 日志提示:  
  - MYSQL数据库连接已关闭

#### database management
#### 数据库管理
1. `create_db(dbname, bool_autoselect=True)`
- 功能:  创建数据库
- 参数:  
  - `dbname`: 数据库名
  - `bool_autoselect`: 创建后自动选择该数据库
- 示例:  
  ```python
  from hzgt.tools import Mysqlop
  
  mysql = Mysqlop(host="localhost", port=3306, user="root", passwd="123456")
  mysql.start()
  mysql.create_db("test_db")  # 自动选择新库
  ```

2. `drop_db(dbname)`
- 功能:  删除指定数据库
- 示例:  
  ```
  mysql.drop_db("test_db")
  ```

3. `select_db(dbname)`
- 功能:  选择指定数据库
- 示例:  
  ```
  mysql.select_db("test_db")
  ```
    
4. `get_all_db()`
- 功能:  获取所有数据库名称
- 示例:  
  ```
  print(mysql.get_all_db())
  ```
5. `get_all_nonsys_db()`
- 功能:  获取所有非系统数据库名称
- 示例:  
  ```
  print(mysql.get_all_nonsys_db())
  ```
      
#### table operations
#### 表操作
1. create_table(tablename, attr_dict, primary_key=None, bool_id=True)
- 功能:  创建数据表 
- 参数:  
  - `attr_dict`: 字段定义字典(格式:  {"字段名": "数据类型"})
  - `primary_key:` 主键列表(默认自动添加id字段为主键)
  - `bool_id`: 是否自动添加自增ID字段
- 字典的值详见[支持的数据类型](#supported-data-types)
- 示例:  
  ```
  fields = {
      "name": "VARCHAR(50)",
      "age": "INT",
      "create_time": "DATETIME"
  }
  mysql.create_table("users", fields, primary_key=["name"])
  ```

2. `drop_table(tablename)`
- 功能:  删除指定数据表
- 示例:  
  ```
  mysql.drop_table("users")
  ```

3. `get_tables(dbname)`
- 功能:  获取指定数据库的所有数据表名称
- 示例:  
  ```
  mysql.get_tables("test_db")
  ```

4. `get_table_index(tablename)`
- 功能:  获取指定数据表的索引信息
- 示例:  
  ```
  mysql.get_table_index("users")
  ```
    
5. `select_table(tablename)`
- 功能:  选择指定数据表
- 示例:  
  ```
  mysql.select_table("users")
  ```
  
#### data operations
#### 数据操作
1. `insert(tablename, record, ignore_duplicates=False)`
- 功能:  插入单条数据
- 参数:  
  - `record`: 数据字典({"字段": 值})
  - `ignore_duplicates`: 是否忽略重复数据
- 示例:  
  ```
  data = {"name": "Alice", "age": 30}
  mysql.insert("users", data)
  ```

2. `select(tablename, conditions=None, fields=None, order=None)`
- 功能:  查询数据
- 参数:  
  - `conditions`: 条件字典, 键为列名, 值为str 或 [操作符](#operators-map),  例如: 
    ```
    {
      "creat_at": {">=": "2023-01-01", "<": "2023-02-01"},
      "status": "active",
      "age": {">": 18, "<": 30}
    }
    ```
  - `fields`: 返回字段列表(默认所有字段)
  - `order`: 排序规则({"create_time": "DESC"})

3. `update(tablename, update_values, conditions)`
- 功能:  更新符合条件的数据
- 示例:  
  ```
  mysql.update("users", {"age": 31}, {"name": "Alice"})
  ```
  
4. `delete(tablename, conditions)`
- 功能:  删除符合条件的数据
- 示例:  
  ```
  mysql.delete("users", {"name": "Alice"})
  ```

#### permission management
#### 权限管理
1. `change_passwd(username, new_password, host="localhost")`
- 功能:  修改用户密码

2. `get_curuser_permissions()`
- 功能:  获取当前用户权限
- 返回格式:  
{
    '\*.\*': ['USAGE'],
    'test_db.\*': ['SELECT', 'INSERT']
}

### Examples
### 使用示例[Examples]
基本操作流程
```python
from hzgt.tools import Mysqlop

# 初始化连接
mysql = Mysqlop(
    host="localhost", 
    port=3306, 
    user="root",
    passwd="123456"
)
mysql.start()

# 创建数据库
mysql.create_db("school")
mysql.select_db("school")

# 创建学生表
fields = {
    "id": "INT AUTO_INCREMENT",
    "name": "VARCHAR(50)",
    "score": "FLOAT",
    "enrollment_date": "DATE"
}
mysql.create_table("students", fields, primary_key=["id"])
mysql.select_table("students")

# 插入数据
student_data = {
    "name": "Bob",
    "score": 89.5,
    "enrollment_date": "2023-09-01"
}
mysql.insert("students", student_data)

# 查询数据
results = mysql.select(
    "students", 
    conditions={"score": ">=80"},
    fields=["name", "score"],
    order={"score": "DESC"}
)
print(results)
```

### Important Notes
### 注意事项
- `字符集兼容性`
建库时默认使用 utf8 字符集, 确保与现有系统兼容

- `事务管理`
默认关闭自动提交(**autocommit=False**), 需手动执行 ```self.__con.commit()```

- `线程安全`
每个实例应在独立线程中使用, 避免多线程共享连接

- `错误处理`
操作失败时**自动回滚事务**, 需在代码中捕获异常:  
  ```
  try:
      mysql.insert(...)
  except Exception as e:
      print(f"操作失败: {str(e)}")
  ```
  
- `性能建议`
批量插入数据时建议使用事务包裹
频繁查询场景建议使用连接池管理

### supported data types
### 支持的数据类型

| 数据类型      | 中文描述      |
|-----------|-----------|
| TINYINT   | 小整数       |
| SMALLINT  | 小整数       |
| INT       | 整数        |
| INTEGER   | 整数        |
| BIGINT    | 大整数       |
| FLOAT     | 浮点数       |
| DOUBLE    | 双精度浮点数    |
| DECIMAL   | 十进制数      |
| DATE      | 日期        |
| TIME      | 时间        |
| DATETIME  | 日期和时间     |
| TIMESTAMP | 时间戳       |
| CHAR      | 字符串       |
| VARCHAR   | 可变长度字符串   |
| TEXT      | 长文本       |
| BLOB      | 二进制大对象    |
| LONGBLOB  | 长二进制大对象   |
| ENUM      | 枚举类型      |
| SET       | 集合类型      |
| JSON      | JSON 数据类型 |

### operators map
### 操作符对照表[Operators Map]
|    操作符     |   描述    |
|:----------:|:-------:|
| `=`, `==`  |   等于    |
| `!=`, `<>` |   不等于   |
| `>`, `>=`  | 大于/大于等于 |
| `<`, `<=`  | 小于/小于等于 |
|   `LIKE`   |  模糊匹配   |
|    `IN`    |  集合匹配   |
| `BETWEEN`  |  范围匹配   |

### supported data types
### 权限对照表[Privilege Codes]

| 权限名称                      | 类型   | 描述      |
|---------------------------|------|---------|
| `SELECT`                  | 基本权限 | 查询数据    |
| `INSERT`                  | 基本权限 | 插入数据    |
| `UPDATE`                  | 基本权限 | 更新数据    |
| `DELETE`                  | 基本权限 | 删除数据    |
| `CREATE`                  | 基本权限 | 创建数据库/表 |
| `DROP`                    | 基本权限 | 删除数据库/表 |
| `RELOAD`                  | 基本权限 | 重新加载    |
| `SHUTDOWN`                | 基本权限 | 关闭服务器   |
| `PROCESS`                 | 基本权限 | 查看进程    |
| `FILE`                    | 基本权限 | 文件操作    |
| `REFERENCES`              | 基本权限 | 外键约束    |
| `INDEX`                   | 基本权限 | 创建索引    |
| `ALTER`                   | 基本权限 | 修改数据库/表 |
| `SHOW DATABASES`          | 基本权限 | 显示数据库   |
| `SUPER`                   | 基本权限 | 超级权限    |
| `CREATE TEMPORARY TABLES` | 基本权限 | 创建临时表   |
| `LOCK TABLES`             | 基本权限 | 锁定表     |
| `EXECUTE`                 | 基本权限 | 执行存储过程  |
| `REPLICATION SLAVE`       | 基本权限 | 复制从属    |
| `REPLICATION CLIENT`      | 基本权限 | 复制客户端   |
| `CREATE VIEW`             | 基本权限 | 创建视图    |
| `SHOW VIEW`               | 基本权限 | 显示视图    |
| `CREATE ROUTINE`          | 基本权限 | 创建例程    |
| `ALTER ROUTINE`           | 基本权限 | 修改例程    |
| `CREATE USER`             | 基本权限 | 创建用户    |
| `EVENT`                   | 基本权限 | 事件管理    |
| `TRIGGER`                 | 基本权限 | 触发器     |
| `CREATE TABLESPACE`       | 基本权限 | 创建表空间   |
| `CREATE ROLE`             | 基本权限 | 创建角色    |
| `DROP ROLE`               | 基本权限 | 删除角色    |

| 权限名称                           | 类型   | 描述           |
|--------------------------------|------|--------------|
| `ALLOW_NONEXISTENT_DEFINER`    | 高级权限 | 允许不存在的定义者    |
| `APPLICATION_PASSWORD_ADMIN`   | 高级权限 | 应用密码管理       |
| `AUDIT_ABORT_EXEMPT`           | 高级权限 | 审计中止豁免       |
| `AUDIT_ADMIN`                  | 高级权限 | 审计管理         |
| `AUTHENTICATION_POLICY_ADMIN`  | 高级权限 | 认证策略管理       |
| `BACKUP_ADMIN`                 | 高级权限 | 备份管理         |
| `BINLOG_ADMIN`                 | 高级权限 | 二进制日志管理      |
| `BINLOG_ENCRYPTION_ADMIN`      | 高级权限 | 二进制日志加密管理    |
| `CLONE_ADMIN`                  | 高级权限 | 克隆管理         |
| `CONNECTION_ADMIN`             | 高级权限 | 连接管理         |
| `ENCRYPTION_KEY_ADMIN`         | 高级权限 | 加密密钥管理       |
| `FIREWALL_EXEMPT`              | 高级权限 | 防火墙豁免        |
| `FLUSH_OPTIMIZER_COSTS`        | 高级权限 | 刷新优化器成本      |
| `FLUSH_STATUS`                 | 高级权限 | 刷新状态         |
| `FLUSH_TABLES`                 | 高级权限 | 刷新表          |
| `FLUSH_USER_RESOURCES`         | 高级权限 | 刷新用户资源       |
| `GROUP_REPLICATION_ADMIN`      | 高级权限 | 组复制管理        |
| `GROUP_REPLICATION_STREAM`     | 高级权限 | 组复制流         |
| `INNODB_REDO_LOG_ARCHIVE`      | 高级权限 | InnoDB重做日志归档 |
| `INNODB_REDO_LOG_ENABLE`       | 高级权限 | 启用InnoDB重做日志 |
| `PASSWORDLESS_USER_ADMIN`      | 高级权限 | 无密码用户管理      |
| `PERSIST_RO_VARIABLES_ADMIN`   | 高级权限 | 持久化只读变量管理    |
| `REPLICATION_APPLIER`          | 高级权限 | 复制应用者        |
| `REPLICATION_SLAVE_ADMIN`      | 高级权限 | 复制从属管理员      |
| `RESOURCE_GROUP_ADMIN`         | 高级权限 | 资源组管理        |
| `RESOURCE_GROUP_USER`          | 高级权限 | 资源组用户        |
| `ROLE_ADMIN`                   | 高级权限 | 角色管理         |
| `SENSITIVE_VARIABLES_OBSERVER` | 高级权限 | 敏感变量观察者      |
| `SERVICE_CONNECTION_ADMIN`     | 高级权限 | 服务连接管理       |
| `SESSION_VARIABLES_ADMIN`      | 高级权限 | 会话变量管理       |
| `SET_ANY_DEFINER`              | 高级权限 | 设置任何定义者      |
| `SHOW_ROUTINE`                 | 高级权限 | 显示例程         |
| `SYSTEM_USER`                  | 高级权限 | 系统用户         |
| `SYSTEM_VARIABLES_ADMIN`       | 高级权限 | 系统变量管理       |
| `TABLE_ENCRYPTION_ADMIN`       | 高级权限 | 表加密管理        |
| `TELEMETRY_LOG_ADMIN`          | 高级权限 | 遥测日志管理       |
| `TRANSACTION_GTID_TAG`         | 高级权限 | 交易GTID标记     |
| `XA_RECOVER_ADMIN`             | 高级权限 | XA恢复管理       |

| 权限名称             | 类型   | 描述   |
|------------------|------|------|
| `USAGE`          | 其它权限 | 访客权限 |
| `ALL PRIVILEGES` | 其它权限 | 所有权限 |
