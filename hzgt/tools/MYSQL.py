# -*- coding: utf-8 -*-
import datetime
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
            ">": ">",
            ">=": ">=",
            "<": "<",
            "<=": "<=",
            "=": "=",
            "!=": "!=",
            "LIKE": "LIKE",  # 模糊查询
            "IN": "IN",  # 在范围内
            "BETWEEN": "BETWEEN",  # 范围查询

            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<=",
            "$eq": "=",
            "$ne": "!=",
        }

class Mysqlop:
    def __init__(self, host: str, port: int, user: str, passwd: str, charset: str = "utf8", logger: Logger = None):
        """
        初始化mmysql类

        :param host: MYSQL数据库地址
        :param port: 端口
        :param user: 用户名
        :param passwd: 密码
        :param charset: 编码 默认 UTF8

        :param logger: 日志记录器
        """
        self.__config = {"host": str(host),
                         "port": int(port),
                         "user": str(user),
                         "passwd": str(passwd),
                         'charset': charset}
        self.__con = None
        self.__cur = None
        self.__selected_db = None  # 已选择的数据库
        self.__selected_table = None  # 已选择的数据库表

        if logger is None:
            self.__logger = set_log("hzgt.mysql", os.path.join("logs", "mysql.log"), level=2)
        else:
            self.__logger = logger
        self.__logger.info(f'MYSQL类初始化完成 "host": {str(host)}, "port": {int(port)}, "user": {str(user)}')

    def start(self):
        """
        启动服务器连接

        :return:
        """
        try:
            self.__con = pymysql.connect(**self.__config, autocommit=False)
            self.__cur = self.__con.cursor()
            self.__logger.info(f"MYSQL数据库连接成功")
        except Exception as e:
            self.__logger.error(f"MYSQL数据库连接失败, 错误原因: {e}")
            raise Exception(f'数据库连接失败. Error: {e.__class__.__name__}: {e}') from None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        return self.start()

    def close(self):
        if self.__con:
            self.__con.rollback()  # 确保回滚任何待处理的事务
            self.__cur.close()
            self.__con.close()
            self.__con = None
            self.__cur = None
            self.__logger.info(f"MYSQL数据库连接已关闭")

    def __execute(self, sql: str, args = None, bool_commit: bool = True):
        """
        执行sql语句

        :param sql: sql语句
        :param args: 其它参数
        :param bool_commit: 是否自动提交 默认 True
        :return:
        """
        try:
            if args:
                self.__cur.execute(sql, args)
            else:
                self.__cur.execute(sql)
            if bool_commit:
                self.__con.commit()
            return self.__cur.fetchall()
        except AttributeError as attrerr:
            self.__logger.error(f"MYSQL未登录, 无法执行SQL语句")
            raise Exception(f'MYSQL未登录, 无法执行SQL语句')
        except Exception as e:
            self.__logger.error(f"执行数据库SQL语句失败, 错误原因: {e.__class__.__name__}: {e}")
            self.__con.rollback()
            raise Exception(f'执行数据库SQL语句失败: {e.__class__.__name__}: {e}') from None

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
        """
        选择数据库

        :param dbname: 数据库名
        :return:
        """
        self.__con.select_db(dbname)
        self.__selected_db = dbname
        self.__logger.debug(f"已选择MYSQL数据库[{dbname}]")

    def create_db(self, dbname: str, bool_autoselect: bool = True):
        """
        创建数据库

        :param dbname: 需要创建的数据库名
        :param bool_autoselect: 是否自动选择该数据库
        :return:
        """
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
        self.__execute(f"DROP DATABASE IF EXISTS `{dbname}`")
        self.__logger.info(f"MYSQL数据库[{dbname}]删除成功")
        if dbname == self.__selected_db:
            self.__selected_db = None
            self.__logger.debug(f"MYSQL数据库[{dbname}]已清除选择")

    def select_table(self, tablename: str):
        """
        选择数据库表

        :param tablename: 需要选择的表名
        :return:
        """
        self.__selected_table = tablename
        self.__logger.debug(f"已选择MYSQL数据库表[{self.__selected_db}.{tablename}]")

    def create_table(self, tablename: str, attr_dict: dict, primary_key: list[str] = None,
                     bool_id: bool = True, bool_autoselect: bool = True):
        """
        创建表

        '''

        attr_dict:

        + 整数类型

            + TINYINT:  1字节, 范围从-128到127（有符号）, 0到255（无符号）. 适用于存储小整数值, 如状态标志或性别.
            + SMALLINT:  2字节, 范围从-32,768到32,767（有符号）, 0到65,535（无符号）. 用于中等大小的整数.
            + INT或INTEGER:  4字节, 范围从-2,147,483,648到2,147,483,647（有符号）, 0到4,294,967,295（无符号）. 通常用于存储一般整数数据.
            + BIGINT:  8字节, 范围更大, 适用于非常大的整数, 如用户ID或订单号.

        + 浮点数类型

            + FLOAT:  4字节, 单精度浮点数. 用于存储大约7位有效数字的浮点数.
            + DOUBLE:  8字节, 双精度浮点数. 用于存储大约15位有效数字的浮点数.

        + 定点数类型

            + DECIMAL:  根据指定的精度和小数位数占用不同字节数. 适用于货币和精确计算, 因为它不会引入浮点数舍入误差.

        + 日期和时间类型

            + DATE:  3字节, 用于存储日期（年、月、日）.
            + TIME:  3字节, 用于存储时间（时、分、秒）.
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

        # 检查tablename是否是有效的表名
        if not re.match(r'^[a-zA-Z0-9_]+$', tablename):
            self.__logger.error("tablename无效, 只能包含字母、数字和下划线.")
            raise ValueError("tablename只能包含字母、数字和下划线.")

        # 检查attr_dict是否为字典类型
        if not isinstance(attr_dict, dict):
            self.__logger.error("attr_dict必须是一个字典.")
            raise TypeError("attr_dict必须是一个字典.")

        if primary_key is None:
            primary_key = []

        if bool_id:
            if "id" not in list(attr_dict.keys()):
                primary_key.append("id")

        # 检查attr_dict的键和值是否符合要求
        for col_name, data_type in attr_dict.items():
            if not re.match(r'^[a-zA-Z0-9_]+$', col_name):
                self.__logger.error("列名无效, 只能包含字母、数字和下划线.")
                raise ValueError("列名只能包含字母、数字和下划线.")
            data_type = data_type.upper()

            # 验证数据类型是否有效, 考虑带参数的数据类型
            match = re.match(r'(' + '|'.join(VALID_MYSQL_DATA_TYPES) + ')', data_type)
            if not match:
                self.__logger.error(f"{data_type}不是有效的MySQL数据类型")
                raise ValueError(f"{data_type}不是有效的MySQL数据类型.")

        # 检查primary_key中是否有重复元素
        if len(set(primary_key)) != len(primary_key):
            self.__logger.error("primary_key中有重复元素")
            raise ValueError("primary_key中不能有重复元素")

        # 检查primary_key中的元素是否为字符串
        for key in primary_key:
            if not isinstance(key, str):
                self.__logger.error("primary_key中的元素类型不是字符串")
                raise TypeError("primary_key中的元素必须是字符串.")

        # 检查primary_key中的元素是否为空字符串
        for key in primary_key:
            if key == "":
                self.__logger.error("primary_key中的元素为空字符串")
                raise ValueError("primary_key中的元素不能为空字符串")

        col_definitions = []
        if bool_id and 'id' not in attr_dict:
            col_definitions.append("`id` INT AUTO_INCREMENT")
        for col_name, data_type in attr_dict.items():
            col_definitions.append(f"`{col_name}` {data_type}")
        columns = ', '.join(col_definitions)
        pk_definition = f"PRIMARY KEY (`{', '.join(primary_key)}`)"

        sql = f"CREATE TABLE IF NOT EXISTS `{tablename}` ({columns}, {pk_definition}) ENGINE=InnoDB DEFAULT CHARSET=utf8"
        self.__execute(sql)
        self.__logger.info(f"创建表{tablename}成功")
        if bool_autoselect:
            self.select_table(tablename)

    # =-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=
    def insert(self, tablename: str = '', record: dict = None, ignore_duplicates: bool = False):
        """
        插入数据

        :param tablename: 数据库表名, 如果未提供则使用当前选择的表
        :param record: 需要插入的数据, 格式为字典 {列名: 值}
        :param ignore_duplicates: 是否忽略重复数据（如果数据已存在, 是否跳过插入）
        :return: 无返回值
        """
        if not record:
            self.__logger.error("插入数据失败: record 参数不能为空")
            raise ValueError("record 参数不能为空")

        tablename = tablename or self.__selected_table
        if not tablename:
            self.__logger.error("插入数据失败: 未选择表名")
            raise ValueError("未选择表名")

        columns = list(record.keys())
        values = list(record.values())

        # 构建参数化查询的占位符
        placeholders = ', '.join(['%s'] * len(values))
        columns_str = ', '.join(columns)

        # 构建 SQL 语句
        if ignore_duplicates:
            sql = f"INSERT IGNORE INTO {tablename} ({columns_str}) VALUES ({placeholders})"
        else:
            sql = f"INSERT INTO {tablename} ({columns_str}) VALUES ({placeholders})"

        try:
            self.__execute(sql, values)
            self.__logger.info(f"插入数据成功")
        except Exception as e:
            self.__logger.error(f"插入数据失败: {e.__class__.__name__}: {e}")
            raise Exception(f"插入数据失败: {e.__class__.__name__}: {e}") from None

    def select(self, tablename: str = "", conditions: dict = None, order: dict = None, fields=None):
        """
        查询数据

        :param tablename: 数据库表名.默认使用 self.__selected_table.
        :param conditions: 查询条件, 支持操作符: `>`、`>=`、`<`、`<=`、`=`、`!=`、`LIKE`、`IN`、`BETWEEN`.
            例如: 
            {
                "creat_at": {">=": "2023-01-01", "<": "2023-02-01"},
                "status": "active",
                "age": {">": 18, "<": 30}
            }
        :param order: 排序方式, 如 {"timestamp": "DESC"}.
        :param fields: 返回字段, 默认所有字段.
        :return: 查询结果.
        """
        if fields is None:
            fields = ['*']
        tablename = tablename or self.__selected_table
        conditions = conditions or {}
        order = order or {}

        def _format_value(v):
            """处理时间戳和字符串转义"""
            if isinstance(v, datetime.datetime):
                # 将 datetime 对象转为标准格式字符串
                return f"'{v.strftime('%Y-%m-%d %H:%M:%S')}'"
            elif v is None:
                return 'NULL'
            elif isinstance(v, str):
                escaped = v.replace("'", "''")
                return f"'{escaped}'"
            elif isinstance(v, (int, float)):
                return str(v)
            else:
                return str(v)

        where_clause_parts = []
        for column, value in conditions.items():
            if isinstance(value, dict):
                # 处理操作符条件（如 {">": 100}）
                conditions_list = []
                for op, op_value in value.items():
                    # 检查操作符是否合法
                    sql_op = AVAILABLE_OPERATORS.get(op.upper() if op.startswith("$") else op)
                    if not sql_op:
                        raise ValueError(f"无效操作符: {op}, 可用的操作符为: {list(AVAILABLE_OPERATORS.keys())}")

                    # 处理特殊操作符
                    if sql_op == "BETWEEN":
                        if not isinstance(op_value, (list, tuple)) or len(op_value) != 2:
                            raise ValueError("BETWEEN 需要两个值的列表, 如 [start, end]")
                        val1 = _format_value(op_value[0])
                        val2 = _format_value(op_value[1])
                        conditions_list.append(f"`{column}` BETWEEN {val1} AND {val2}")
                    elif sql_op == "IN":
                        if not isinstance(op_value, (list, tuple)):
                            raise ValueError("IN 需要列表或元组")
                        formatted_values = [_format_value(v) for v in op_value]
                        conditions_list.append(f"`{column}` IN ({', '.join(formatted_values)})")
                    else:
                        # 常规操作符（如 >、>= 等）
                        formatted_value = _format_value(op_value)
                        conditions_list.append(f"`{column}` {sql_op} {formatted_value}")

                # 合并同一字段的多个条件（如 > 20 AND < 40）
                where_clause_parts.append(f"({' AND '.join(conditions_list)})")
            else:
                # 简单等值条件（如 "status": "active"）
                formatted_value = _format_value(value)
                where_clause_parts.append(f"`{column}` = {formatted_value}")

        # 构建 SQL
        fields_clause = ", ".join(fields) if fields != ['*'] else '*'
        sql = f"SELECT {fields_clause} FROM {tablename}"
        if where_clause_parts:
            sql += f" WHERE {' AND '.join(where_clause_parts)}"
        if order:
            order_clauses = []
            for col, dir in order.items():
                dir = dir.upper() if dir else "ASC"
                if dir not in ("ASC", "DESC"):
                    raise ValueError("排序方向必须是 ASC 或 DESC")
                order_clauses.append(f"`{col}` {dir}")
            sql += f" ORDER BY {', '.join(order_clauses)}"

        try:
            print(sql)
            result = self.__execute(sql)
            self.__logger.info(f"查询数据成功")
            return result
        except Exception as e:
            self.__logger.error(f"查询数据失败: {e.__class__.__name__}: {e}")
            raise Exception(f"查询数据失败: {e.__class__.__name__}: {e}") from None

    def delete(self, tablename: str = '', conditions: dict = None):
        """
        删除数据

        :param tablename: 表名
        :param conditions: dict 删除
        :return:
        """
        tablename = tablename or self.__selected_table

        conditions = conditions or {}
        where_clause = ' AND '.join([f"`{k}` = %s" for k in conditions])
        sql = f"DELETE FROM {tablename}"
        if conditions:
            sql += f" WHERE {where_clause}"

        try:
            self.__execute(sql, list(conditions.values()))
            self.__logger.info(f"删除数据成功")
        except Exception as e:
            self.__logger.error(f"删除数据失败: {e.__class__.__name__}: {e}")
            raise Exception(f"删除数据失败: {e.__class__.__name__}: {e}") from None

    def update(self, tablename: str = '', update_values: dict = None, conditions: dict = None):
        """
        更新数据

        :param tablename: 数据库表名
        :param update_values: 新数据
        :param conditions: 匹配数据字典(原数据)
        :return:
        """
        tablename = tablename or self.__selected_table

        conditions = conditions or {}
        set_clause = ', '.join([f"`{k}` = %s" for k in update_values])
        where_clause = ' AND '.join([f"`{k}` = %s" for k in conditions])
        sql = f"UPDATE {tablename} SET {set_clause}"
        if conditions:
            sql += f" WHERE {where_clause}"

        try:
            self.__execute(sql, list(update_values.values()) + list(conditions.values()))
            self.__logger.info(f"更新数据成功")
        except Exception as e:
            self.__logger.error(f"更新数据失败: {e.__class__.__name__}: {e}")
            raise Exception(f"更新数据失败: {e.__class__.__name__}: {e}") from None

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

        :return: 字典. 键为数据库名（如 '*.*', 'dbname.*'）, 值为权限列表（如 ['SELECT', 'INSERT']）
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
            error = '执行查询用户权限的SQL语句失败: %s' % (e.args)
            self.__logger.error(error)
            raise Exception(error + f" {e.__class__.__name__}: {e}") from None
