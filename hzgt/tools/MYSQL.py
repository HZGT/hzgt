# -*- coding: utf-8 -*-
import os
import re
from logging import Logger

import pymysql

from ..log import set_log

VALID_MYSQL_DATA_TYPES = ['TINYINT', 'SMALLINT', 'INT', 'INTEGER', 'BIGINT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'DATE',
                          'TIME', 'DATETIME', 'TIMESTAMP', 'CHAR', 'VARCHAR', 'TEXT', 'BLOB', 'LONGBLOB', 'ENUM',
                          'SET', 'JSON']
# 权限英文到中文的映射字典
PRIVILEGE_TRANSLATION = {
    # 基本权限
    'SELECT': '查询数据',
    'INSERT': '插入数据',
    'UPDATE': '更新数据',
    'DELETE': '删除数据',
    'CREATE': '创建数据库/表',
    'DROP': '删除数据库/表',
    'RELOAD': '重新加载',
    'SHUTDOWN': '关闭服务器',
    'PROCESS': '查看进程',
    'FILE': '文件操作',
    'REFERENCES': '外键约束',
    'INDEX': '创建索引',
    'ALTER': '修改数据库/表',
    'SHOW DATABASES': '显示数据库',
    'SUPER': '超级权限',
    'CREATE TEMPORARY TABLES': '创建临时表',
    'LOCK TABLES': '锁定表',
    'EXECUTE': '执行存储过程',
    'REPLICATION SLAVE': '复制从属',
    'REPLICATION CLIENT': '复制客户端',
    'CREATE VIEW': '创建视图',
    'SHOW VIEW': '显示视图',
    'CREATE ROUTINE': '创建例程',
    'ALTER ROUTINE': '修改例程',
    'CREATE USER': '创建用户',
    'EVENT': '事件管理',
    'TRIGGER': '触发器',
    'CREATE TABLESPACE': '创建表空间',
    'CREATE ROLE': '创建角色',
    'DROP ROLE': '删除角色',
    # 高级权限
    'ALLOW_NONEXISTENT_DEFINER': '允许不存在的定义者',
    'APPLICATION_PASSWORD_ADMIN': '应用密码管理',
    'AUDIT_ABORT_EXEMPT': '审计中止豁免',
    'AUDIT_ADMIN': '审计管理',
    'AUTHENTICATION_POLICY_ADMIN': '认证策略管理',
    'BACKUP_ADMIN': '备份管理',
    'BINLOG_ADMIN': '二进制日志管理',
    'BINLOG_ENCRYPTION_ADMIN': '二进制日志加密管理',
    'CLONE_ADMIN': '克隆管理',
    'CONNECTION_ADMIN': '连接管理',
    'ENCRYPTION_KEY_ADMIN': '加密密钥管理',
    'FIREWALL_EXEMPT': '防火墙豁免',
    'FLUSH_OPTIMIZER_COSTS': '刷新优化器成本',
    'FLUSH_STATUS': '刷新状态',
    'FLUSH_TABLES': '刷新表',
    'FLUSH_USER_RESOURCES': '刷新用户资源',
    'GROUP_REPLICATION_ADMIN': '组复制管理',
    'GROUP_REPLICATION_STREAM': '组复制流',
    'INNODB_REDO_LOG_ARCHIVE': 'InnoDB重做日志归档',
    'INNODB_REDO_LOG_ENABLE': '启用InnoDB重做日志',
    'PASSWORDLESS_USER_ADMIN': '无密码用户管理',
    'PERSIST_RO_VARIABLES_ADMIN': '持久化只读变量管理',
    'REPLICATION_APPLIER': '复制应用者',
    'REPLICATION_SLAVE_ADMIN': '复制从属管理员',
    'RESOURCE_GROUP_ADMIN': '资源组管理',
    'RESOURCE_GROUP_USER': '资源组用户',
    'ROLE_ADMIN': '角色管理',
    'SENSITIVE_VARIABLES_OBSERVER': '敏感变量观察者',
    'SERVICE_CONNECTION_ADMIN': '服务连接管理',
    'SESSION_VARIABLES_ADMIN': '会话变量管理',
    'SET_ANY_DEFINER': '设置任何定义者',
    'SHOW_ROUTINE': '显示例程',
    'SYSTEM_USER': '系统用户',
    'SYSTEM_VARIABLES_ADMIN': '系统变量管理',
    'TABLE_ENCRYPTION_ADMIN': '表加密管理',
    'TELEMETRY_LOG_ADMIN': '遥测日志管理',
    'TRANSACTION_GTID_TAG': '交易GTID标记',
    'XA_RECOVER_ADMIN': 'XA恢复管理',

    # 其它权限
    'USAGE': '访客权限',
    'ALL PRIVILEGES': '所有权限',
}

AVAILABLE_OPERATORS = {
    '>': '>', '<': '<', '>=': '>=', '<=': '<=',
    '=': '=', '!=': '!=',
    'LIKE': 'LIKE', 'IN': 'IN', 'BETWEEN': 'BETWEEN',
    '$gt': '>', '$lt': '<', '$gte': '>=', '$lte': '<=',
    '$eq': '=', '$ne': '!=',
    '$like': 'LIKE', '$in': 'IN', '$between': 'BETWEEN'
}


class Mysqlop:
    def __init__(self, host: str, port: int, user: str, passwd: str,
                 database: str = None,
                 charset: str = "utf8", logger: Logger = None,
                 autoreconnect: bool = True, reconnect_retries: int = 3):
        """
        初始化mmysql类

        :param host: MYSQL数据库地址
        :param port: 端口
        :param user: 用户名
        :param passwd: 密码
        :param database: 初始连接的数据库名(可选)
        :param charset: 编码 默认 UTF8

        :param logger: 日志记录器
        :param autoreconnect: 是否自动重连 默认 True
        :param reconnect_retries: 重连次数
        """
        self.__config = {
            "host": str(host),
            "port": int(port),
            "user": str(user),
            "password": str(passwd),
            "database": database,
            "charset": charset,
            "autocommit": True
        }
        self.__con = None
        self.__selected_db = None
        self.__selected_table = None
        self.autoreconnect = autoreconnect
        self.reconnect_retries = reconnect_retries

        # 日志配置
        if logger is None:
            self.__logger = set_log("hzgt.mysql", os.path.join("logs", "mysql.log"), level=2)
        else:
            self.__logger = logger
        self.__logger.info(f'MYSQL类初始化完成 "host": {str(host)}, "port": {int(port)}, "user": {str(user)}')

    def _ensure_connection(self):
        """确保连接有效(核心方法)"""
        if self.__con is None:
            self.start()
            return

        try:
            # 当reconnect=True时, ping会自动尝试重新连接
            self.__con.ping(reconnect=True)
            self.__logger.debug("数据库连接状态检查通过")
        except pymysql.OperationalError as e:
            if self.autoreconnect:
                self.__logger.warning(f"连接丢失(错误码 {e.args[0]}), 尝试重新连接...")
                self._safe_connect()
            else:
                raise

    def _safe_connect(self):
        """安全的连接方法(带重试机制)"""
        for attempt in range(1, self.reconnect_retries + 1):
            try:
                self.close()  # 先关闭旧连接
                # 连接时自动使用最新的数据库配置
                self.__con = pymysql.connect(**self.__config)
                self.__logger.info(f"MySQL连接成功(数据库: {self.__selected_db})")

                return
            except pymysql.OperationalError as e:
                self.__logger.error(f"连接失败(尝试 {attempt}/{self.reconnect_retries}): {e}")
                if attempt == self.reconnect_retries:
                    raise RuntimeError(f"数据库连接失败, 重试{self.reconnect_retries}次后仍不可用: {e}") from e

    def start(self):
        """启动服务器连接"""
        self._safe_connect()

    def __enter__(self):
        self._ensure_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """安全关闭连接"""
        if self.__con:
            try:
                self.__con.rollback()
                if self.__con.open:
                    self.__con.close()
                self.__logger.info("MYSQL数据库连接已安全关闭")
            except Exception as e:
                self.__logger.error(f"关闭连接时发生错误: {e}")
            finally:
                self.__con = None

    def __execute(self, sql: str, args=None):
        """
        执行sql语句(带自动重连机制)
        """
        for attempt in range(2):  # 最多重试1次
            try:
                self._ensure_connection()
                with self.__con.cursor() as cursor:  # 使用新的游标
                    cursor.execute(sql, args)
                    return cursor.fetchall()
            except pymysql.OperationalError as e:
                if attempt == 0 and self.autoreconnect:
                    self.__logger.warning(f"执行失败, 尝试重新连接后重试: {e}")
                    self._safe_connect()
                    continue
                self.__con.rollback()
                self.__logger.error(f"执行SQL失败: {sql} | 参数: {args}")
                raise
            except Exception as e:
                self.__con.rollback()
                self.__logger.error(f"执行SQL时发生意外错误: {e}")
                raise

    def get_curuser(self):
        self.__logger.debug(f"获取当前用户名")
        return self.__execute("SELECT USER()")

    def get_version(self):
        self.__logger.debug(f"获取数据库版本")
        return self.__execute("SELECT VERSION()")

    def get_all_db(self):
        """
        获取所有数据库名

        :return: list: 返回所有数据库名
        """
        self.__logger.debug(f"获取数据库名")
        return [db[0] for db in self.__execute("SHOW DATABASES")]

    def get_all_nonsys_db(self):
        """
        获取除系统数据库外的所有数据库名

        :return: list: 返回所有非系统数据库名
        """
        exclude_list = ["sys", "information_schema", "mysql", "performance_schema"]
        self.__logger.debug(f"获取除系统数据库外的所有数据库名")
        return [db for db in self.get_all_db() if db not in exclude_list]

    def get_tables(self, dbname: str = ""):
        """
        获取已选择的数据库的所有表

        :return: list: 返回已选择的数据库的所有表
        """
        dbname = dbname or self.__selected_db
        dbname = self.__escape_identifier(dbname)
        if not dbname:
            self.__logger.error(f"未选择数据库, 无法获取表名")
            raise Exception(f'未选择数据库, 无法获取表名')
        self.__logger.debug(f"获取数据库[{dbname}]的所有表")
        return [table[0] for table in self.__execute(f"SHOW TABLES FROM {dbname}")]

    def get_table_index(self, tablename: str = ''):
        """
        获取已选择的表的索引信息

        :return: list: 返回已选择的表的索引信息
        """
        tablename = tablename or self.__selected_table
        self.__logger.debug(f"获取表[{tablename}]的索引信息")
        return self.__execute(f"DESCRIBE {tablename}")

    def select_db(self, dbname: str):
        """选择数据库，更新配置并重新连接"""
        self.__selected_db = dbname
        self.__config["database"] = dbname  # 更新连接配置中的数据库名
        if self.__con:  # 若已连接，则重新连接以应用新配置
            self._safe_connect()

    def create_db(self, dbname: str, bool_autoselect: bool = True):
        """
        创建数据库

        :param dbname: 需要创建的数据库名
        :param bool_autoselect: 是否自动选择该数据库
        :return:
        """
        dbname = self.__escape_identifier(dbname)
        # 注入sql检验
        if not re.match(r'^[a-zA-Z0-9_$#@]+$', dbname):
            self.__logger.error(f"数据库名[{dbname}]不合法, 请使用以下符号: 字母、数字、下划线、美元符号、井号、@")
            raise Exception(f'数据库名[{dbname}]不合法, 请使用以下符号: 字母、数字、下划线、美元符号、井号、@')

        self.__execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8 COLLATE utf8_general_ci")
        self.__logger.info(f"MYSQL数据库[{dbname}]创建成功")
        if bool_autoselect:
            self.select_db(dbname)

    def drop_db(self, dbname: str):
        """
        删除数据库

        :param dbname: 需要删除的数据库名
        :return:
        """
        dbname = self.__escape_identifier(dbname)
        self.__execute(f"DROP DATABASE IF EXISTS `{dbname}`")
        self.__logger.info(f"MYSQL数据库[{dbname}]删除成功")
        if dbname == self.__selected_db:
            self.__selected_db = None
            self.__logger.debug(f"MYSQL数据库[{dbname}]已清除选择")

    def select_table(self, table_name: str):
        """记录选择的表(实际不执行SQL)"""
        self.__selected_table = table_name
        self.__logger.debug(f"已记录选择表: {table_name}")

    def create_table(self, tablename: str, attr_dict: dict, primary_key: list[str] = None,
                     bool_id: bool = True, bool_autoselect: bool = True):
        """
        创建表

        '''

        attr_dict:

        + 整数类型

            + TINYINT:  1字节, 范围从-128到127(有符号), 0到255(无符号). 适用于存储小整数值, 如状态标志或性别.
            + SMALLINT:  2字节, 范围从-32,768到32,767(有符号), 0到65,535(无符号). 用于中等大小的整数.
            + INT或INTEGER:  4字节, 范围从-2,147,483,648到2,147,483,647(有符号), 0到4,294,967,295(无符号). 通常用于存储一般整数数据.
            + BIGINT:  8字节, 范围更大, 适用于非常大的整数, 如用户ID或订单号.

        + 浮点数类型

            + FLOAT:  4字节, 单精度浮点数. 用于存储大约7位有效数字的浮点数.
            + DOUBLE:  8字节, 双精度浮点数. 用于存储大约15位有效数字的浮点数.

        + 定点数类型

            + DECIMAL:  根据指定的精度和小数位数占用不同字节数. 适用于货币和精确计算, 因为它不会引入浮点数舍入误差.

        + 日期和时间类型

            + DATE:  3字节, 用于存储日期(年、月、日).
            + TIME:  3字节, 用于存储时间(时、分、秒).
            + DATETIME:  8字节, 用于存储日期和时间.
            + TIMESTAMP:  4字节, 通常用于记录创建和修改时间, 存储范围受限于32位UNIX时间戳.

        + 字符串类型

            + CHAR:  定长字符串, 占用的字节数等于指定的长度, 最大长度为255个字符. 适用于固定长度的数据, 如国家代码.
            + VARCHAR:  可变长度字符串, 占用的字节数根据存储的数据长度而变化, 最多65,535字节. 适用于可变长度的文本数据, 如用户名和评论.
            + TEXT:  用于存储长文本数据, 有TINYTEXT、TEXT、MEDIUMTEXT和LONGTEXT四种类型, 分别对应不同的存储长度.

        + 二进制类型

            + BLOB:  用于存储二进制数据, 可变长度, 最大容量根据存储引擎和配置设置而不同.
            + LONGBLOB:  用于存储更大的二进制数据.

        + 特殊类型

            + ENUM:  枚举类型, 用于存储单一值, 可以选择一个预定义的集合.
            + SET:  集合类型, 用于存储多个值, 可以选择多个预定义的集合.
            + JSON:  用于存储JSON数据, 从MySQL 5.7版本开始支持.
        '''

        :param tablename: 需要创建的表名
        :param attr_dict: 字典 {列名: MYSQL数据类型}, 表示表中的列及其数据类型
        :param primary_key: 主键列表. 其中的元素应为字符串
        :param bool_id: 是否添加 id 为自增主键
        :param bool_autoselect: 创建表格后是否自动选择该表格, 默认为自动选择
        :return: 无返回值, 在数据库中创建指定的表
        """
        tablename = tablename or self.__selected_table

        # 检查表名有效性
        if not re.match(r'^[a-zA-Z0-9_]+$', tablename):
            self.__logger.error("表名无效, 只能包含字母、数字和下划线")
            raise ValueError("表名只能包含字母、数字和下划线")

        # 检查attr_dict类型
        if not isinstance(attr_dict, dict):
            self.__logger.error("attr_dict必须为字典类型")
            raise TypeError("attr_dict必须为字典类型")

        # 初始化主键列表
        primary_key = primary_key.copy() if primary_key else []

        # 处理自增ID逻辑
        col_definitions = []
        if bool_id:
            if 'id' in attr_dict:
                # 用户自定义了id列, 验证数据类型并添加AUTO_INCREMENT
                data_type = attr_dict['id'].upper()
                base_type = re.match(r'^\w+', data_type).group()
                allowed_types = ['INT', 'INTEGER', 'TINYINT', 'SMALLINT', 'BIGINT']
                if base_type not in allowed_types:
                    self.__logger.error(f"ID列的数据类型{data_type}不支持自增")
                    raise ValueError("ID列必须为整数类型以支持自增")
                if 'AUTO_INCREMENT' not in data_type:
                    data_type += ' AUTO_INCREMENT'
                col_definitions.append(f"`id` {data_type}")
                # 确保ID在主键中
                if 'id' not in primary_key:
                    primary_key.append('id')
                # 添加其他列(排除ID)
                for col, dtype in attr_dict.items():
                    if col != 'id':
                        col_definitions.append(f"`{col}` {dtype}")
            else:
                # 自动添加ID列
                col_definitions.append("`id` INT AUTO_INCREMENT")
                primary_key.append('id')
                # 添加所有列
                for col, dtype in attr_dict.items():
                    col_definitions.append(f"`{col}` {dtype}")
        else:
            # 无自增ID, 直接添加所有列
            for col, dtype in attr_dict.items():
                col_definitions.append(f"`{col}` {dtype}")

        # 检查列定义非空
        if not col_definitions:
            self.__logger.error("无法创建无列的表")
            raise ValueError("表必须包含至少一列")

        # 收集所有列名
        column_names = []
        for col_def in col_definitions:
            match = re.match(r'^`([a-zA-Z0-9_]+)`', col_def)
            if match:
                column_names.append(match.group(1))
            else:
                self.__logger.error(f"列定义格式错误: {col_def}")
                raise ValueError(f"列定义格式错误: {col_def}")

        # 验证主键列存在
        for pk in primary_key:
            if pk not in column_names:
                self.__logger.error(f"主键列{pk}不存在")
                raise ValueError(f"主键列{pk}不存在")

        # 主键重复性检查
        if len(primary_key) != len(set(primary_key)):
            self.__logger.error("主键列表中存在重复列名")
            raise ValueError("主键列表中存在重复列名")

        # 构建主键定义
        pk_clause = ""
        if primary_key:
            pk_clause = f", PRIMARY KEY (`{'`, `'.join(primary_key)}`)"

        # 构建并执行SQL
        columns_sql = ', '.join(col_definitions)
        sql = (f"CREATE TABLE IF NOT EXISTS `{tablename}` "
               f"({columns_sql}{pk_clause}) ENGINE=InnoDB DEFAULT CHARSET=utf8")
        self.__execute(sql)

        self.__logger.info(f"创建表 {tablename} 成功")
        if bool_autoselect:
            self.select_table(tablename)

    # =-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=
    @staticmethod
    def __escape_identifier(identifier: str) -> str:
        """转义标识符(表名、列名), 防止SQL注入和关键字冲突"""
        return '`' + identifier.replace('`', '``') + '`'

    def __build_where_clause(self, conditions: dict) -> tuple:
        """
        构建WHERE子句和参数列表(支持复杂条件)
        返回: (where_clause_str, parameter_list)
        """
        where_parts = []
        params = []

        for column, value in conditions.items():
            # 转义列名
            safe_col = self.__escape_identifier(column.strip())

            if isinstance(value, dict):
                # 处理操作符条件
                for op_symbol, op_value in value.items():
                    op = AVAILABLE_OPERATORS.get(
                        op_symbol.upper() if op_symbol.startswith('$') else op_symbol
                    )
                    if not op:
                        raise ValueError(f"无效操作符: {op_symbol}")

                    if op == 'BETWEEN':
                        if not isinstance(op_value, (list, tuple)) or len(op_value) != 2:
                            raise ValueError("BETWEEN 需要两个值的列表")
                        where_parts.append(f"{safe_col} BETWEEN %s AND %s")
                        params.extend(op_value)
                    elif op == 'IN':
                        if not isinstance(op_value, (list, tuple)):
                            raise ValueError("IN 需要列表或元组")
                        placeholders = ', '.join(['%s'] * len(op_value))
                        where_parts.append(f"{safe_col} IN ({placeholders})")
                        params.extend(op_value)
                    else:
                        where_parts.append(f"{safe_col} {op} %s")
                        params.append(op_value)
            else:
                # 简单等值条件
                where_parts.append(f"{safe_col} = %s")
                params.append(value)

        return (" AND ".join(where_parts), params) if where_parts else ("", [])

    # =-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=
    def insert(self, tablename: str = '', record: dict = None, ignore_duplicates: bool = False):
        """
        插入数据

        :param tablename: 数据库表名, 如果未提供则使用当前选择的表
        :param record: 需要插入的数据, 格式为字典 {列名: 值}
        :param ignore_duplicates: 是否忽略重复数据(如果数据已存在, 是否跳过插入)
        :return: 无返回值
        """
        if not record:
            self.__logger.error("插入数据失败: record 参数不能为空")
            raise ValueError("record 参数不能为空")

        # 检查列名有效性
        columns = list(record.keys())
        if not columns:
            self.__logger.error("插入数据失败: record 中无列名")
            raise ValueError("record 中无列名")
        for col in columns:
            if not col.strip():
                self.__logger.error("插入数据失败: 列名不能为空或仅包含空格")
                raise ValueError("列名不能为空或仅包含空格")

        # 处理表名
        tablename = tablename or self.__selected_table
        if not tablename:
            self.__logger.error("插入数据失败: 未选择表名")
            raise ValueError("未选择表名")
        if not tablename.strip():
            self.__logger.error("插入数据失败: 表名不能为空或仅包含空格")
            raise ValueError("表名不能为空或仅包含空格")

        # 转义表名和列名
        try:
            safe_tablename = self.__escape_identifier(tablename.strip())
            safe_columns = [self.__escape_identifier(col.strip()) for col in columns]
        except Exception as e:
            self.__logger.error(f"转义表名或列名失败: {e}")
            raise ValueError("无效的表名或列名") from e

        # 构造SQL
        values = list(record.values())
        columns_str = ', '.join(safe_columns)
        placeholders = ', '.join(['%s'] * len(values))
        if ignore_duplicates:
            sql = f"INSERT IGNORE INTO {safe_tablename} ({columns_str}) VALUES ({placeholders})"
        else:
            sql = f"INSERT INTO {safe_tablename} ({columns_str}) VALUES ({placeholders})"

        # 执行插入
        try:
            self.__execute(sql, values)
            self.__logger.info(f"成功插入数据到表 {tablename}")
        except Exception as e:
            self.__logger.error(f"插入数据到表 {tablename} 失败: {e}")
            raise  # 重新抛出原始异常, 保留堆栈信息

    def select(self, tablename: str = "", conditions: dict = None, order: dict = None, fields=None):
        """
        查询数据

        :param tablename: 表名
        :param conditions: 支持复杂操作符的查询条件
        :param order: 返回结果排序的字典 键为列名, 值为 `DESC` 或者 `ASC`
        :param fields: 返回该列名列表的结果, 默认返回所有列
        :return: 查询结果
        """
        # 参数校验
        tablename = tablename or self.__selected_table
        if not tablename.strip():
            raise ValueError("表名不能为空")

        try:
            safe_table = self.__escape_identifier(tablename.strip())
        except Exception as e:
            self.__logger.error(f"表名转义失败: {e}")
            raise ValueError("无效表名") from e

        # 构建 WHERE 子句
        where_clause, where_params = self.__build_where_clause(conditions or {})

        # 构建 SQL
        fields_clause = "*" if not fields else ", ".join(
            [self.__escape_identifier(f.strip()) for f in fields]
        )
        sql = f"SELECT {fields_clause} FROM {safe_table}"
        if where_clause:
            sql += f" WHERE {where_clause}"

        # 添加排序
        if order:
            order_clauses = []
            for col, _dir in order.items():
                safe_col = self.__escape_identifier(col.strip())
                _dir = _dir.upper() if _dir else "ASC"
                if _dir not in ("ASC", "DESC"):
                    raise ValueError("排序方向必须是 `ASC` 或 `DESC`")
                order_clauses.append(f"{safe_col} {_dir}")
            sql += f" ORDER BY {', '.join(order_clauses)}"

        try:
            result = self.__execute(sql, where_params)
            self.__logger.info(f"查询表 {tablename} 成功, 条件: {list(conditions.keys()) if conditions else '无'}")
            return result
        except Exception as e:
            self.__logger.error(f"查询表 {tablename} 失败: {str(e)}")
            raise

    def delete(self, tablename: str = '', conditions: dict = None):
        """
        删除数据(支持复杂条件)

        :param tablename: 表名
        :param conditions: 支持操作符的删除条件
        """
        tablename = tablename or self.__selected_table
        if not tablename.strip():
            raise ValueError("表名不能为空")

        try:
            safe_table = self.__escape_identifier(tablename.strip())
        except Exception as e:
            self.__logger.error(f"表名转义失败: {e}")
            raise ValueError("无效表名") from e

        # 构建 WHERE 子句
        where_clause, where_params = self.__build_where_clause(conditions or {})

        # 危险操作检查
        if not where_clause:
            self.__logger.warning("正在执行全表删除操作！")

        sql = f"DELETE FROM {safe_table}"
        if where_clause:
            sql += f" WHERE {where_clause}"

        try:
            self.__execute(sql, where_params)
            self.__logger.info(f"删除表 {tablename} 数据成功, 条件: {list(conditions.keys()) if conditions else '全部'}")
        except Exception as e:
            self.__logger.error(f"删除表 {tablename} 数据失败: {str(e)}")
            raise

    def update(self, tablename: str = '', update_values: dict = None, conditions: dict = None):
        """
        更新数据(支持复杂条件)

        :param tablename: 表名
        :param update_values: 要更新的键值对
        :param conditions: 支持操作符的更新条件
        """
        # 参数校验
        tablename = tablename or self.__selected_table
        if not tablename.strip():
            raise ValueError("表名不能为空")
        if not update_values:
            raise ValueError("update_values 不能为空")

        try:
            safe_table = self.__escape_identifier(tablename.strip())
            safe_columns = [self.__escape_identifier(k.strip()) for k in update_values]
        except Exception as e:
            self.__logger.error(f"标识符转义失败: {e}")
            raise ValueError("无效表名或列名") from e

        # 构建 SET 子句
        set_clause = ", ".join([f"{col} = %s" for col in safe_columns])
        set_params = list(update_values.values())

        # 构建 WHERE 子句
        where_clause, where_params = self.__build_where_clause(conditions or {})

        # 危险操作检查
        if not where_clause:
            self.__logger.warning("正在执行全表更新操作！")

        # 组合 SQL
        sql = f"UPDATE {safe_table} SET {set_clause}"
        if where_clause:
            sql += f" WHERE {where_clause}"

        try:
            self.__execute(sql, set_params + where_params)
            self.__logger.info(f"更新表 {tablename} 成功, 更新列: {list(update_values.keys())}")
        except Exception as e:
            self.__logger.error(f"更新表 {tablename} 失败: {str(e)}")
            raise

    def drop_table(self, tablename: str = ''):
        """
        删除数据库表

        :param tablename: 数据库表名
        """
        tablename = tablename or self.__selected_table

        sql = f"DROP TABLE IF EXISTS {tablename}"
        try:
            self.__execute(sql)
            self.__logger.info(f"数据库表[{tablename}]删除成功")
        except Exception as e:
            self.__logger.error(f"数据库表删除失败: {e.__class__.__name__}: {e}")
            raise Exception(f"数据库表删除失败: {e.__class__.__name__}: {e}") from None

    def purge(self, tablename: str = ''):
        """
        清除数据库表的数据

        :param tablename: 数据库表名
        :return:
        """
        tablename = tablename or self.__selected_table

        sql = f"TRUNCATE TABLE {tablename}"
        try:
            self.__execute(sql)
            self.__logger.info(f"数据库表[{tablename}]数据清除成功")
        except Exception as e:
            self.__logger.error(f"数据库表数据清除失败: {e.__class__.__name__}: {e}")
            raise Exception(f"数据库表数据清除失败: {e.__class__.__name__}: {e}") from None

    # =-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=
    def change_passwd(self, username: str, new_password: str, host: str = "localhost"):
        """
        修改密码

        :param username: 用户名
        :param new_password: 新密码
        :param host: 用户登录数据库的主机地址 默认 localhost
        :return:
        """
        host = host or "localhost"
        sql = f"ALTER USER '{username}'@'{host}' IDENTIFIED BY '{new_password}'"
        try:
            self.__execute(sql)
            self.__logger.info(f"修改密码成功")
            self.close()
        except Exception as e:
            self.__logger.error(f"修改密码失败: {e.__class__.__name__}: {e}")
            raise Exception(f"修改密码失败: {e.__class__.__name__}: {e}") from None

    def get_curuser_permissions(self):
        """
        查询当前用户的权限信息

        :return: 字典. 键为数据库名(如 '*.*', 'dbname.*'), 值为权限列表(如 ['SELECT', 'INSERT'])
        """
        # SQL语句用于查询当前用户的权限
        # SHOW GRANTS FOR CURRENT_USER() 显示当前用户的权限
        sql = "SHOW GRANTS FOR CURRENT_USER();"

        def parse_grants(_grants: list[str]):
            """
            解析GRANT语句, 返回按数据库分类的权限字典

            :param _grants: GRANT语句列表, 如 ['GRANT USAGE ON *.* TO ...', 'GRANT SELECT ON db.* TO ...']
            :return: { '数据库名': [权限1, 权限2], ... }
            """
            permissions = {}
            for grant in _grants:
                if not grant.startswith('GRANT '):
                    continue

                # 提取权限部分和数据库名
                grant_part = grant[6:].split(' ON ', 1)  # 分割权限和数据库部分
                if len(grant_part) != 2:
                    continue

                privs_str, db_part = grant_part[0], grant_part[1]
                db_name = db_part.split(' TO ')[0].strip().replace('`', '')  # 去除反引号

                # 处理权限字符串
                if 'ALL PRIVILEGES' in privs_str:
                    privs = ['ALL PRIVILEGES']
                else:
                    privs = [p.strip() for p in privs_str.split(',')]

                # 合并到字典
                if db_name in permissions:
                    permissions[db_name].extend(privs)
                else:
                    permissions[db_name] = privs

            return permissions

        try:
            privileges = [grants[0] for grants in self.__execute(sql)]
            self.__logger.info(f"查询当前用户的权限信息成功")
            return parse_grants(privileges)
        except Exception as e:
            error = '执行查询用户权限的SQL语句失败: %s' % e.args
            self.__logger.error(error)
            raise Exception(error + f" {e.__class__.__name__}: {e}") from None
