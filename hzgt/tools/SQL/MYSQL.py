# -*- coding: utf-8 -*-
import re
import time
from contextlib import contextmanager
from enum import Enum
from logging import Logger
from typing import Dict, Optional, Any, List, Tuple, Union, Generator, Callable

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor, SSCursor

from hzgt.core.log import set_log
from .sqlcore import SQLutilop, ConnectionPool, QueryBuilder, DBAdapter

# 有效的MySQL数据类型
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

# 可用的操作符映射
AVAILABLE_OPERATORS = {
    '>': '>', '<': '<', '>=': '>=', '<=': '<=',
    '=': '=', '!=': '!=', '<>': '<>',
    'LIKE': 'LIKE', 'NOT LIKE': 'NOT LIKE',
    'IN': 'IN', 'NOT IN': 'NOT IN',
    'BETWEEN': 'BETWEEN', 'NOT BETWEEN': 'NOT BETWEEN',
    'IS': 'IS', 'IS NOT': 'IS NOT',
    # MongoDB风格操作符
    '$gt': '>', '$lt': '<', '$gte': '>=', '$lte': '<=',
    '$eq': '=', '$ne': '!=',
    '$like': 'LIKE', '$nlike': 'NOT LIKE',
    '$in': 'IN', '$nin': 'NOT IN',
    '$between': 'BETWEEN', '$nbetween': 'NOT BETWEEN',
    '$is': 'IS', '$isNot': 'IS NOT',
    # 额外操作符
    '$regex': 'REGEXP', '$not': 'NOT', '$or': 'OR', '$and': 'AND'
}


class JoinType(Enum):
    """连接类型枚举"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL JOIN"


class MySQLAdapter(DBAdapter):
    """MySQL数据库适配器实现"""

    def __init__(self, host: str, port: int, user: str, passwd: str,
                 database: str = None, charset: str = "utf8", logger: Logger = None):
        """
        初始化MySQL适配器

        Args:
            host: MySQL数据库地址
            port: 端口
            user: 用户名
            passwd: 密码
            database: 数据库名
            charset: 字符集
            logger: 日志记录器
        """
        self.config = {
            "host": str(host),
            "port": int(port),
            "user": str(user),
            "password": str(passwd),
            "database": database,
            "charset": charset,
            "autocommit": True,
            "cursorclass": DictCursor  # 使用字典游标
        }
        self.logger = logger

    def get_connection(self) -> Connection:
        """获取数据库连接"""
        try:
            conn = pymysql.connect(**self.config)
            if self.logger:
                self.logger.debug("MySQL数据库连接已建立")
            return conn
        except pymysql.Error as e:
            if self.logger:
                self.logger.error(f"MySQL连接失败: {e}")
            raise RuntimeError(f"MySQL数据库连接失败: {e}") from None

    def close_connection(self, connection: Connection):
        """关闭数据库连接"""
        if connection and connection.open:
            connection.close()
            if self.logger:
                self.logger.debug("MySQL数据库连接已关闭")

    def execute_query(self, connection: Connection, sql: str,
                      params: Any = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        执行查询并返回结果

        Args:
            connection: 数据库连接
            sql: SQL语句
            params: 参数

        Returns:
            (结果集, 影响行数)
        """
        cursor = None
        try:
            cursor = connection.cursor()
            affected_rows = cursor.execute(sql, params)
            results = cursor.fetchall() if cursor.description else []
            return results, affected_rows
        except pymysql.Error as e:
            if self.logger:
                self.logger.error(f"执行SQL失败: {sql} | 参数: {params} | 错误: {e}")
            raise RuntimeError(f"执行SQL失败: {sql} | 错误: {e}")
        finally:
            if cursor:
                cursor.close()

    def get_last_insert_id(self, connection: Connection, table_name: str = None) -> Optional[tuple[Any, ...]]:
        """获取最后插入的ID"""
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT LAST_INSERT_ID()")
            result = cursor.fetchone()
            return result
        finally:
            if cursor:
                cursor.close()

    def get_placeholder_style(self) -> str:
        """获取参数占位符样式"""
        return "%s"

    @staticmethod
    def format_table_creation(tablename: str,
                              columns: Dict[str, Dict[str, str]],
                              primary_keys: List[str],
                              **kwargs) -> str:
        """
        格式化建表语句

        Args:
            tablename: 表名
            columns: 列定义 {列名: {type: 类型, constraint: 约束}}
            primary_keys: 主键列表
            **kwargs: 额外参数

        Returns:
            建表SQL
        """
        column_defs = []
        for column, details in columns.items():
            if isinstance(details, str):
                # 简单类型定义
                column_defs.append(f"`{column}` {details}")
            else:
                # 详细定义
                type_def = details.get("type", "VARCHAR(255)")
                constraint = details.get("constraint", "")
                column_defs.append(f"`{column}` {type_def} {constraint}".strip())

        # 添加主键定义
        if primary_keys:
            pk_cols = ", ".join([f"`{pk}`" for pk in primary_keys])
            column_defs.append(f"PRIMARY KEY ({pk_cols})")

        # 添加索引定义
        indices = kwargs.get("indices", [])
        for idx in indices:
            if isinstance(idx, dict):
                idx_name = idx.get("name", "")
                idx_type = idx.get("type", "INDEX")
                idx_cols = idx.get("columns", [])
                if idx_cols:
                    idx_cols_str = ", ".join([f"`{col}`" for col in idx_cols])
                    column_defs.append(f"{idx_type} {idx_name}({idx_cols_str})")

        # 添加表选项
        engine = kwargs.get("engine", "InnoDB")
        charset = kwargs.get("charset", "utf8")
        collate = kwargs.get("collate", "utf8_general_ci")

        sql = (f"CREATE TABLE {'IF NOT EXISTS ' if kwargs.get('if_not_exists', True) else ''}`{tablename}` (\n"
               f"  {',  '.join(column_defs)}\n"
               f") ENGINE={engine} DEFAULT CHARSET={charset} COLLATE={collate}")

        return sql


class MySQLQueryBuilder(QueryBuilder):
    """MySQL查询构建器实现"""

    def __init__(self, logger: Optional[Logger] = None):
        """
        初始化MySQL查询构建器

        Args:
            logger: 日志记录器
        """
        self.logger = logger

    @staticmethod
    def escape_identifier(identifier: str) -> str:
        """转义标识符(表名、列名)"""
        return f"`{identifier.replace('`', '``')}`"

    def _build_where_clause(self, conditions: Optional[Dict]) -> Tuple[str, List]:
        """构建WHERE子句和参数"""
        if not conditions:
            return "", []

        where_parts = []
        params = []

        # 处理逻辑组合
        if '$or' in conditions or '$and' in conditions:
            if '$or' in conditions:
                subclauses = []
                for subcond in conditions['$or']:
                    subwhere, subparams = self._build_where_clause(subcond)
                    if subwhere:
                        subclauses.append(f"({subwhere})")
                        params.extend(subparams)
                if subclauses:
                    where_parts.append(f"({' OR '.join(subclauses)})")

            if '$and' in conditions:
                subclauses = []
                for subcond in conditions['$and']:
                    subwhere, subparams = self._build_where_clause(subcond)
                    if subwhere:
                        subclauses.append(f"({subwhere})")
                        params.extend(subparams)
                if subclauses:
                    where_parts.append(f"({' AND '.join(subclauses)})")

            # 处理其余普通条件
            other_conditions = {k: v for k, v in conditions.items()
                                if k not in ('$or', '$and')}
            if other_conditions:
                subwhere, subparams = self._build_where_clause(other_conditions)
                if subwhere:
                    where_parts.append(subwhere)
                    params.extend(subparams)
        else:
            # 处理普通条件
            for column, value in conditions.items():
                # 跳过特殊键
                if column.startswith('$'):
                    continue

                # 转义列名
                safe_col = self.escape_identifier(column.strip())

                if isinstance(value, dict):
                    # 处理操作符条件
                    for op_symbol, op_value in value.items():
                        op = AVAILABLE_OPERATORS.get(
                            op_symbol.lower() if op_symbol.startswith('$') else op_symbol
                        )
                        if not op:
                            raise ValueError(f"无效操作符: {op_symbol}")

                        if op in ('BETWEEN', 'NOT BETWEEN'):
                            if not isinstance(op_value, (list, tuple)) or len(op_value) != 2:
                                raise ValueError(f"{op} 需要两个值的列表")
                            where_parts.append(f"{safe_col} {op} %s AND %s")
                            params.extend(op_value)
                        elif op in ('IN', 'NOT IN'):
                            if not isinstance(op_value, (list, tuple)):
                                raise ValueError(f"{op} 需要列表或元组")
                            placeholders = ', '.join(['%s'] * len(op_value))
                            where_parts.append(f"{safe_col} {op} ({placeholders})")
                            params.extend(op_value)
                        elif op in ('IS', 'IS NOT'):
                            # IS NULL 和 IS NOT NULL 不需要参数
                            where_parts.append(f"{safe_col} {op} NULL"
                                               if op_value is None else f"{safe_col} {op} %s")
                            if op_value is not None:
                                params.append(op_value)
                        else:
                            where_parts.append(f"{safe_col} {op} %s")
                            params.append(op_value)
                else:
                    # 简单等值条件
                    if value is None:
                        where_parts.append(f"{safe_col} IS NULL")
                    else:
                        where_parts.append(f"{safe_col} = %s")
                        params.append(value)

        return (" AND ".join(where_parts), params) if where_parts else ("", [])

    def build_select(self,
                     tablename: str,
                     fields: Optional[List[str]] = None,
                     conditions: Optional[Dict] = None,
                     order: Optional[Dict[str, bool]] = None,
                     limit: Optional[int] = None,
                     offset: Optional[int] = None,
                     group_by: Optional[List[str]] = None,
                     having: Optional[Dict] = None,
                     **kwargs) -> Tuple[str, List]:
        """构建SELECT语句"""
        # 处理表名和字段
        safe_table = self.escape_identifier(tablename)
        fields_str = "*"
        if fields:
            safe_fields = [self.escape_identifier(f) for f in fields]
            fields_str = ", ".join(safe_fields)

        # 基础查询
        sql = f"SELECT {fields_str} FROM {safe_table}"
        params = []

        # 处理WHERE条件
        where_clause, where_params = self._build_where_clause(conditions)
        if where_clause:
            sql += f" WHERE {where_clause}"
            params.extend(where_params)

        # 处理GROUP BY
        if group_by:
            group_by_fields = [self.escape_identifier(g) for g in group_by]
            sql += f" GROUP BY {', '.join(group_by_fields)}"

            # 处理HAVING
            if having:
                having_clause, having_params = self._build_where_clause(having)
                if having_clause:
                    sql += f" HAVING {having_clause}"
                    params.extend(having_params)

        # 处理排序
        if order:
            order_parts = []
            for col, asc in order.items():
                direction = "ASC" if asc else "DESC"
                order_parts.append(f"{self.escape_identifier(col)} {direction}")
            if order_parts:
                sql += f" ORDER BY {', '.join(order_parts)}"

        # 处理分页
        if limit is not None:
            sql += f" LIMIT %s"
            params.append(int(limit))
            if offset is not None:
                sql += f" OFFSET %s"
                params.append(int(offset))

        return sql, params

    def build_insert(self,
                     tablename: str,
                     data: Union[Dict[str, Any], List[Dict[str, Any]]],
                     **kwargs) -> Tuple[str, List]:
        """构建INSERT语句"""
        safe_table = self.escape_identifier(tablename)

        # 处理单行或多行插入
        is_batch = isinstance(data, list)
        records = data if is_batch else [data]
        if not records:
            raise ValueError("没有数据可插入")

        # 获取所有字段名
        fields = list(records[0].keys())
        safe_fields = [self.escape_identifier(field) for field in fields]
        fields_str = ", ".join(safe_fields)

        # 构建占位符
        values_placeholder = "(" + ", ".join(["%s"] * len(fields)) + ")"

        # 构建批量插入的值
        values = []
        for record in records:
            record_values = [record.get(field) for field in fields]
            values.extend(record_values)

        # 处理插入选项
        ignore = kwargs.get("ignore", False)
        update_on_duplicate = kwargs.get("on_duplicate", None)

        # 构建SQL
        sql = f"INSERT {'IGNORE ' if ignore else ''}INTO {safe_table} ({fields_str}) VALUES "

        if is_batch:
            sql += ", ".join([values_placeholder] * len(records))
        else:
            sql += values_placeholder

        # 处理UPSERT
        if update_on_duplicate and isinstance(update_on_duplicate, dict):
            updates = []
            for field, value in update_on_duplicate.items():
                safe_field = self.escape_identifier(field)
                if value == "VALUES(field)":
                    updates.append(f"{safe_field}=VALUES({safe_field})")
                else:
                    updates.append(f"{safe_field}=%s")
                    values.append(value)
            if updates:
                sql += f" ON DUPLICATE KEY UPDATE {', '.join(updates)}"

        return sql, values

    def build_update(self,
                     tablename: str,
                     update_values: Dict[str, Any],
                     conditions: Optional[Dict] = None,
                     **kwargs) -> Tuple[str, List]:
        """构建UPDATE语句"""
        if not update_values:
            raise ValueError("没有要更新的数据")

        safe_table = self.escape_identifier(tablename)

        # 构建SET子句
        set_parts = []
        set_params = []
        for field, value in update_values.items():
            safe_field = self.escape_identifier(field)
            set_parts.append(f"{safe_field}=%s")
            set_params.append(value)

        # 构建WHERE子句
        where_clause, where_params = self._build_where_clause(conditions)

        # 构建SQL
        sql = f"UPDATE {safe_table} SET {', '.join(set_parts)}"
        params = set_params

        if where_clause:
            sql += f" WHERE {where_clause}"
            params.extend(where_params)

        # 处理LIMIT
        limit = kwargs.get("limit")
        if limit is not None:
            sql += f" LIMIT %s"
            params.append(int(limit))

        return sql, params

    def build_delete(self,
                     tablename: str,
                     conditions: Optional[Dict] = None,
                     **kwargs) -> Tuple[str, List]:
        """构建DELETE语句"""
        safe_table = self.escape_identifier(tablename)

        # 构建WHERE子句
        where_clause, where_params = self._build_where_clause(conditions)

        # 构建SQL
        sql = f"DELETE FROM {safe_table}"
        params = []

        if where_clause:
            sql += f" WHERE {where_clause}"
            params.extend(where_params)

        # 处理LIMIT
        limit = kwargs.get("limit")
        if limit is not None:
            sql += f" LIMIT %s"
            params.append(int(limit))

        return sql, params

    def build_create_table(self,
                           tablename: str,
                           schema: Dict[str, Any],
                           primary_key: Optional[List[str]] = None,
                           if_not_exists: bool = True,
                           **kwargs) -> str:
        """构建CREATE TABLE语句"""
        # 验证表名
        if not re.match(r'^[a-zA-Z0-9_]+$', tablename):
            raise ValueError("表名只能包含字母、数字和下划线")

        safe_table = self.escape_identifier(tablename)

        # 处理列定义
        column_defs = []
        for column, details in schema.items():
            col_def = None

            if isinstance(details, str):
                # 简单格式: {column: "INT NOT NULL"}
                col_def = f"{self.escape_identifier(column)} {details}"
            elif isinstance(details, dict):
                # 详细格式: {column: {type: "INT", constraint: "NOT NULL"}}
                col_type = details.get("type", "VARCHAR(255)")
                constraint = details.get("constraint", "")
                col_def = f"{self.escape_identifier(column)} {col_type} {constraint}".strip()

            if col_def:
                column_defs.append(col_def)

        # 处理主键
        if primary_key:
            safe_pk = [self.escape_identifier(pk) for pk in primary_key]
            column_defs.append(f"PRIMARY KEY ({', '.join(safe_pk)})")

        # 处理索引
        indices = kwargs.get("indices", [])
        for idx in indices:
            if isinstance(idx, dict):
                idx_name = idx.get("name", "")
                idx_type = idx.get("type", "INDEX")
                idx_cols = idx.get("columns", [])
                if idx_cols:
                    safe_idx_cols = [self.escape_identifier(col) for col in idx_cols]
                    idx_name_part = f"{self.escape_identifier(idx_name)} " if idx_name else ""
                    column_defs.append(f"{idx_type} {idx_name_part}({', '.join(safe_idx_cols)})")

        # 处理表选项
        engine = kwargs.get("engine", "InnoDB")
        charset = kwargs.get("charset", "utf8")
        collate = kwargs.get("collate", "utf8_general_ci")

        sql = (f"CREATE TABLE {f'IF NOT EXISTS ' if if_not_exists else ''}{safe_table} (\n"
               f"  {',  '.join(column_defs)}\n"
               f") ENGINE={engine} DEFAULT CHARSET={charset} COLLATE={collate}")

        return sql

    def build_drop_table(self,
                         tablename: str,
                         if_exists: bool = True) -> str:
        """构建DROP TABLE语句"""
        safe_table = self.escape_identifier(tablename)
        return f"DROP TABLE {f'IF EXISTS ' if if_exists else ''}{safe_table}"

    def build_join(self,
                   main_table: str,
                   joins: List[Tuple[str, str, JoinType, Dict[str, str]]],
                   fields: Optional[Dict[str, List[str]]] = None,
                   conditions: Optional[Dict] = None,
                   order: Optional[Dict[str, bool]] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None,
                   **kwargs) -> Tuple[str, List]:
        """构建连接查询语句"""
        # 处理主表
        safe_main_table = self.escape_identifier(main_table)
        main_alias = kwargs.get("main_alias", "t0")
        from_clause = f"{safe_main_table} AS {main_alias}"

        # 处理连接
        join_clauses = []
        join_params = []
        for i, (table, alias, join_type, join_conds) in enumerate(joins, 1):
            safe_table = self.escape_identifier(table)
            join_conditions = []

            # 构建连接条件
            for main_col, join_col in join_conds.items():
                main_table_prefix = kwargs.get("main_alias", "t0")
                join_conditions.append(
                    f"{main_table_prefix}.{self.escape_identifier(main_col)} = {alias}.{self.escape_identifier(join_col)}"
                )

            join_clause = f"{join_type.value} {safe_table} AS {alias} ON {' AND '.join(join_conditions)}"
            join_clauses.append(join_clause)

        # 处理字段选择
        select_fields = []
        if fields:
            for table_alias, cols in fields.items():
                for col in cols:
                    select_fields.append(f"{table_alias}.{self.escape_identifier(col)} AS {table_alias}_{col}")
        else:
            # 默认选择所有字段
            select_fields.append(f"{main_alias}.*")
            for _, alias, _, _ in joins:
                select_fields.append(f"{alias}.*")

        # 构建基础查询
        sql = f"SELECT {', '.join(select_fields)} FROM {from_clause} {' '.join(join_clauses)}"
        params = join_params.copy()

        # 处理WHERE条件
        if conditions:
            # 需要特殊处理条件，因为它们可能引用表别名
            where_clause, where_params = self._build_where_clause(conditions)
            if where_clause:
                sql += f" WHERE {where_clause}"
                params.extend(where_params)

        # 处理排序
        if order:
            order_parts = []
            for col, asc in order.items():
                direction = "ASC" if asc else "DESC"
                # 检查是否包含表别名
                if "." in col:
                    order_parts.append(f"{col} {direction}")
                else:
                    # 假设是主表字段
                    order_parts.append(f"{main_alias}.{self.escape_identifier(col)} {direction}")

            if order_parts:
                sql += f" ORDER BY {', '.join(order_parts)}"

        # 处理分页
        if limit is not None:
            sql += f" LIMIT %s"
            params.append(int(limit))
            if offset is not None:
                sql += f" OFFSET %s"
                params.append(int(offset))

        return sql, params


class MySQLConnectionPool(ConnectionPool):
    """简单的MySQL连接池实现"""

    def __init__(self, adapter: MySQLAdapter, max_connections: int = 5,
                 connection_timeout: int = 5, logger: Optional[Logger] = None):
        """
        初始化连接池

        Args:
            adapter: MySQL适配器
            max_connections: 最大连接数
            connection_timeout: 连接超时时间(秒)
            logger: 日志记录器
        """
        self.adapter = adapter
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.logger = logger

        self._pool = []  # 空闲连接池
        self._active = 0  # 活跃连接数

    def get_connection(self) -> pymysql.connections.Connection:
        """获取连接"""
        # 首先尝试从池中获取
        if self._pool:
            conn = self._pool.pop()
            # 检查连接是否有效
            try:
                conn.ping(reconnect=True)
                if self.logger:
                    self.logger.debug("从连接池获取连接")
                return conn
            except pymysql.Error:
                # 连接无效，丢弃并创建新连接
                if self.logger:
                    self.logger.debug("连接池中的连接无效，创建新连接")
                self._active -= 1  # 减少计数，因为这个连接已经无效

        # 如果没有可用连接或连接无效，创建新连接
        if self._active >= self.max_connections:
            # 等待连接释放
            wait_time = 0
            while self._active >= self.max_connections and wait_time < self.connection_timeout:
                time.sleep(0.1)
                wait_time += 0.1

            if self._active >= self.max_connections:
                if self.logger:
                    self.logger.error("连接池已满，无法创建新连接")
                raise RuntimeError("连接池已满，无法获取连接")

        # 创建新连接
        conn = self.adapter.get_connection()
        self._active += 1
        if self.logger:
            self.logger.debug(f"创建新连接，当前活跃连接: {self._active}")
        return conn

    def release_connection(self, connection: pymysql.connections.Connection):
        """释放连接回池"""
        if connection is None:
            return

        if connection.open:
            # 重置连接状态
            try:
                connection.ping(reconnect=True)
                self._pool.append(connection)
                if self.logger:
                    self.logger.debug("连接释放回连接池")
            except pymysql.Error:
                # 连接无效，关闭
                try:
                    connection.close()
                except:
                    pass
                if self.logger:
                    self.logger.debug("无效连接已关闭")
        else:
            # 连接已关闭，减少计数
            if self.logger:
                self.logger.debug("连接已关闭")

        self._active -= 1

    def close_all(self):
        """关闭所有连接"""
        for conn in self._pool:
            try:
                conn.close()
            except:
                pass
        self._pool.clear()
        self._active = 0
        if self.logger:
            self.logger.info("所有连接已关闭")


class Mysqlop(SQLutilop):
    """MySQL操作工具，基于抽象框架实现"""

    def __init__(self, host: str, port: int, user: str, passwd: str, database: str = None, charset: str = "utf8",
                 logger: Logger = None, autoreconnect: bool = True, reconnect_retries: int = 3,
                 pool_size: int = 5):
        """
        初始化MySQL操作工具

        Args:
            host: MySQL数据库地址
            port: 端口
            user: 用户名
            passwd: 密码
            database: 初始连接的数据库名(可选)
            charset: 编码 默认 UTF8
            logger: 日志记录器
            autoreconnect: 是否自动重连 默认 True
            reconnect_retries: 重连次数
            pool_size: 连接池大小
        """
        # 日志配置
        super().__init__(logger)

        self.adapter = MySQLAdapter(host, port, user, passwd, database, charset, self.logger)
        self.query_builder = MySQLQueryBuilder(self.logger)
        self.connection_pool = MySQLConnectionPool(self.adapter, pool_size, logger=self.logger)

        self.autoreconnect = autoreconnect
        self.reconnect_retries = reconnect_retries
        self.__selected_db = database
        self.__selected_table = None
        self.__connection = None
        self.__in_transaction = False

        self.logger.info(f'MySQL工具初始化完成 host: {host}, port: {port}, user: {user}, database: {database}')

    def _create_default_logger(self) -> Logger:
        """
        创建默认日志记录器

        Returns:
            Logger: 日志记录器实例
        """
        return set_log("hzgt.mysql", "logs")

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type is not None:
            self.logger.error(f"发生异常: {exc_val}")
            self.rollback()
        elif self.__in_transaction:
            self.commit()
        self.close()

    def connect(self):
        """建立数据库连接"""
        for attempt in range(1, self.reconnect_retries + 1):
            try:
                if self.__connection is not None:
                    self.close()
                self.__connection = self.connection_pool.get_connection()
                self.logger.info(f"MySQL连接成功(数据库: {self.__selected_db})")
                return
            except Exception as e:
                self.logger.error(f"连接失败(尝试 {attempt}/{self.reconnect_retries}): {e}")
                if attempt == self.reconnect_retries:
                    raise RuntimeError(f"数据库连接失败, 重试{self.reconnect_retries}次后仍不可用: {e}") from None
                time.sleep(1)  # 等待后重试

    def start(self):
        """建立数据库连接"""
        self.connect()

    def _ensure_connection(self):
        """确保数据库连接有效"""
        if self.__connection is None:
            self.connect()
            return

        try:
            # 检查连接是否有效
            self.__connection.ping(reconnect=True)
        except:
            if self.autoreconnect:
                self.logger.warning("连接已断开，尝试重新连接")
                self.connect()
            else:
                raise RuntimeError("数据库连接已断开，且未启用自动重连")

    def close(self):
        """关闭数据库连接"""
        if self.__connection:
            try:
                if self.__in_transaction:
                    self.logger.warning("关闭连接时有未提交的事务，执行回滚")
                    self.rollback()
                self.connection_pool.release_connection(self.__connection)
                self.logger.debug("MySQL连接已归还到连接池")
            finally:
                self.__connection = None

    def disconnect(self):
        """关闭数据库连接"""
        self.close()

    def commit(self):
        """提交事务"""
        if self.__connection and self.__in_transaction:
            self.__connection.commit()
            self.__in_transaction = False
            self.logger.debug("事务已提交")

    def rollback(self):
        """回滚事务"""
        if self.__connection and self.__in_transaction:
            self.__connection.rollback()
            self.__in_transaction = False
            self.logger.debug("事务已回滚")

    def _begin_transaction(self):
        """开始事务"""
        self._ensure_connection()
        if not self.__in_transaction:
            self.__connection.begin()
            self.__in_transaction = True
            self.logger.debug("开始新事务")

    def _end_transaction(self, commit: bool = True):
        """结束事务"""
        if commit:
            self.commit()
        else:
            self.rollback()

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        self._begin_transaction()
        try:
            yield
            self._end_transaction(commit=True)
        except Exception as e:
            self._end_transaction(commit=False)
            raise RuntimeError(e) from None

    def execute(self, sql: str, args: Optional[Union[tuple, dict, list]] = None) -> Any:
        """
        执行SQL语句

        Args:
            sql: SQL语句
            args: 参数

        Returns:
            执行结果
        """
        for attempt in range(2):  # 最多重试1次
            try:
                self._ensure_connection()
                cursor = self.__connection.cursor()
                try:
                    cursor.execute(sql, args)
                    if not self.__in_transaction and sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                        self.__connection.commit()
                    return cursor.fetchall()
                finally:
                    cursor.close()
            except pymysql.OperationalError as e:
                if attempt == 0 and self.autoreconnect:
                    self.logger.warning(f"执行SQL失败, 尝试重新连接: {e}")
                    self.connect()
                    continue
                if not self.__in_transaction:
                    self.__connection.rollback()
                self.logger.error(f"执行SQL失败: {sql} | 参数: {args}")
                raise RuntimeError(e) from None
            except Exception as e:
                if not self.__in_transaction:
                    self.__connection.rollback()
                self.logger.error(f"执行SQL时发生错误: {e}")
                raise RuntimeError(e) from None

    def executemany(self, sql: str, args_list: List[Union[tuple, dict]]) -> Any:
        """批量执行SQL语句"""
        if not args_list:
            return None

        for attempt in range(2):  # 最多重试1次
            try:
                self._ensure_connection()
                cursor = self.__connection.cursor()
                try:
                    result = cursor.executemany(sql, args_list)
                    if not self.__in_transaction:
                        self.__connection.commit()
                    return result
                finally:
                    cursor.close()
            except pymysql.OperationalError as e:
                if attempt == 0 and self.autoreconnect:
                    self.logger.warning(f"执行批量SQL失败, 尝试重新连接: {e}")
                    self.connect()
                    continue
                if not self.__in_transaction:
                    self.__connection.rollback()
                self.logger.error(f"执行批量SQL失败: {sql}")
                raise RuntimeError(e) from None
            except Exception as e:
                if not self.__in_transaction:
                    self.__connection.rollback()
                self.logger.error(f"执行批量SQL时发生错误: {e}")
                raise RuntimeError(e) from None

    def query(self, sql: str, args: Optional[Union[tuple, dict, list]] = None,
              bool_dict: bool = False, size: Optional[int] = None) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        执行查询并返回结果集

        Args:
            sql: SQL查询语句
            args: 查询参数
            bool_dict: 返回格式为 True 字典Dict[str, Any] False 列表List[Dict[str, Any]]
            size: 批量获取大小，若不指定则一次性获取全部结果

        Returns:
            查询结果列表，每项为一个字典
        """
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.__connection.cursor(DictCursor)
            cursor.execute(sql, args)

            if size is None:
                # 原有行为，一次获取所有结果
                result = list(cursor.fetchall())
            else:
                # 分批获取
                result = []
                while True:
                    batch = cursor.fetchmany(size)
                    if not batch:
                        break
                    result.extend(batch)

            if bool_dict and result:
                return {key: [item[key] for item in result] for key in result[0]}
            return result
        except Exception as e:
            self.logger.error(f"执行查询失败: {sql} | {e}")
            raise RuntimeError(e) from None
        finally:
            if cursor:
                cursor.close()

    def stream_query(self, sql: str, args: Optional[Union[tuple, dict, list]] = None,
                     size: int = 5000, bool_dict: bool = False,
                     use_server_side_cursor: bool = True) -> Generator[
            Union[Dict[str, Any], Dict[str, List]], None, None]:
        """
        流式执行查询，以迭代器方式返回结果，适合大数据量查询

        Args:
            sql: SQL查询语句
            args: 查询参数
            size: 每次获取的批量大小
            bool_dict: 是否以字典形式返回结果 {列名: [列值列表]}
            use_server_side_cursor: 是否使用服务器端游标，可减少内存占用

        Yields:
            如果bool_dict为False: 每条查询结果记录
            如果bool_dict为True: 批量记录的字典表示 {列名: [批次中该列的所有值]}
        """
        self._ensure_connection()
        cursor = None
        try:
            # 添加SQL_NO_CACHE提示，避免缓存影响测试结果
            if sql.upper().startswith("SELECT") and "SQL_NO_CACHE" not in sql.upper():
                sql = sql.replace("SELECT", "SELECT SQL_NO_CACHE", 1)

            # 使用SSCursor实现服务器端游标，显著减少客户端内存占用
            if use_server_side_cursor:
                cursor = self.__connection.cursor(SSCursor)
            else:
                cursor = self.__connection.cursor(DictCursor)

            start_time = time.time()
            self.logger.debug(f"执行查询: {sql}")
            cursor.execute(sql, args)
            query_time = time.time() - start_time
            self.logger.debug(f"SQL执行时间: {query_time:.2f}秒")

            # 针对bool_dict模式的优化
            if bool_dict:
                # 预初始化字段名列表，避免每批数据都重新检查
                field_names = None

                while True:
                    start_fetch = time.time()
                    batch = cursor.fetchmany(size)
                    fetch_time = time.time() - start_fetch
                    if not batch:
                        break

                    self.logger.debug(f"获取{len(batch)}行数据用时: {fetch_time:.2f}秒")

                    if not field_names and batch:
                        # 第一批时初始化字段名
                        if isinstance(batch[0], dict):
                            field_names = list(batch[0].keys())
                        else:
                            # SSCursor返回元组，需要从游标描述中获取字段名
                            field_names = [desc[0] for desc in cursor.description]

                    # 更高效地构建字典结果
                    start_conv = time.time()
                    result_dict = {field: [] for field in field_names}

                    if isinstance(batch[0], dict):
                        # DictCursor返回的是字典
                        for row in batch:
                            for field in field_names:
                                result_dict[field].append(row[field])
                    else:
                        # SSCursor返回的是元组
                        for row in batch:
                            for i, field in enumerate(field_names):
                                result_dict[field].append(row[i])

                    conv_time = time.time() - start_conv
                    self.logger.debug(f"转换数据格式用时: {conv_time:.2f}秒")

                    yield result_dict
            else:
                # 普通模式逐行返回
                for row in cursor:
                    if isinstance(row, dict):
                        yield row
                    else:
                        # SSCursor返回元组，转为字典
                        field_names = [desc[0] for desc in cursor.description]
                        yield {field_names[i]: value for i, value in enumerate(row)}

        except Exception as e:
            self.logger.error(f"流式查询失败: {sql} | {e}")
            raise RuntimeError(f"流式查询失败: {e}") from None
        finally:
            if cursor:
                cursor.close()

    def paginate(self, tablename: str = "", conditions: Dict = None,
                 fields: List[str] = None, order: Dict[str, bool] = None,
                 page: int = 1, page_size: int = 100) -> Tuple[List[Dict[str, Any]], int]:
        """
        分页查询

        Args:
            tablename: 表名，默认为当前选择的表
            conditions: 查询条件
            fields: 要查询的字段列表
            order: 排序 {列名: 是否升序}
            page: 页码，从1开始
            page_size: 每页记录数

        Returns:
            (当前页数据, 总记录数)
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        # 计算总记录数
        count_sql, count_params = self.query_builder.build_select(
            tablename=tablename,
            fields=["COUNT(*) as total"],
            conditions=conditions
        )
        total_result = self.query_one(count_sql, count_params)
        total = total_result["total"] if total_result else 0

        # 空结果快速返回
        if total == 0:
            return [], 0

        # 查询分页数据
        offset = (page - 1) * page_size
        data = self.select(
            tablename=tablename,
            conditions=conditions,
            fields=fields,
            order=order,
            limit=page_size,
            offset=offset
        )

        return data, total

    def analyze_query(self, sql: str, args: Optional[Union[tuple, dict, list]] = None) -> Dict[str, Any]:
        """
        分析查询执行计划并提供优化建议

        Args:
            sql: SQL查询语句
            args: 查询参数

        Returns:
            分析报告
        """
        self._ensure_connection()

        # 获取执行计划
        explain_sql = f"EXPLAIN {sql}"
        explain_result = self.query(explain_sql, args)

        # 分析执行计划
        analysis = {
            "execution_plan": explain_result,
            "recommendations": []
        }

        # 检查是否使用索引
        for row in explain_result:
            if row.get("key") is None and row.get("type") not in ["system", "const"]:
                table = row.get("table", "")
                analysis["recommendations"].append(f"表'{table}'未使用索引，考虑为查询条件添加索引")

            if row.get("rows", 0) > 10000:
                analysis["recommendations"].append(f"扫描行数较多({row.get('rows')}行)，考虑优化查询或添加索引")

        return analysis

    def shard_query(self, tablename: str, id_field: str,
                    conditions: Dict = None, fields: List[str] = None,
                    shard_size: int = 10000, process_func: Callable = None):
        """
        分片查询大表，自动按主键或指定字段进行分片查询

        Args:
            tablename: 表名
            id_field: 用于分片的ID字段（应该有索引）
            conditions: 查询条件
            fields: 要查询的字段列表
            shard_size: 每个分片大小
            process_func: 处理每个分片数据的函数

        Returns:
            处理结果列表，如果没有process_func则返回所有数据
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        # 获取最小和最大ID
        min_max_sql, min_max_params = self.query_builder.build_select(
            tablename=tablename,
            fields=[f"MIN({id_field}) as min_id", f"MAX({id_field}) as max_id"],
            conditions=conditions
        )

        result = self.query_one(min_max_sql, min_max_params)
        if not result or result['min_id'] is None:
            return []

        min_id, max_id = result['min_id'], result['max_id']

        # 分片处理
        results = []
        for start_id in range(min_id, max_id + 1, shard_size):
            end_id = min(start_id + shard_size - 1, max_id)

            # 构建分片条件
            shard_conditions = conditions.copy() if conditions else {}
            shard_conditions[id_field] = {"$between": [start_id, end_id]}

            # 查询分片
            shard_sql, shard_params = self.query_builder.build_select(
                tablename=tablename,
                fields=fields,
                conditions=shard_conditions,
                order={id_field: True}
            )

            self.logger.debug(f"查询ID范围 {start_id} 到 {end_id}")
            shard_data = self.query(shard_sql, shard_params)

            # 处理分片数据
            if process_func:
                shard_result = process_func(shard_data)
                if shard_result:
                    results.append(shard_result)
            else:
                results.extend(shard_data)

            # 记录进度
            progress = (end_id - min_id) / (max_id - min_id) * 100 if max_id > min_id else 100
            self.logger.info(f"分片查询进度: {progress:.1f}%")

        return results

    def query_one(self, sql: str, args: Optional[Union[tuple, dict, list]] = None) -> Optional[Dict[str, Any]]:
        """
        查询单条记录

        Args:
            sql: SQL查询语句
            args: 查询参数

        Returns:
            单条记录字典，未找到时返回None
        """
        results = self.query(sql, args)
        return results[0] if results else None

    # ------------------ 业务方法 ------------------

    def select_db(self, dbname: str):
        """
        选择数据库

        Args:
            dbname: 数据库名
        """
        self.__selected_db = dbname
        self.logger.info(f"选择数据库[{dbname}]")

        # 更新连接配置
        self.adapter.config["database"] = dbname
        # 如果已连接，需要重新连接以应用新配置
        if self.__connection:
            self.close()
            self.connect()

    def select_table(self, tablename: str):
        """
        选择表

        Args:
            tablename: 表名
        """
        self.__selected_table = tablename
        self.logger.debug(f"已记录选择表: {tablename}")

    def get_curuser(self) -> List[Dict[str, Any]]:
        """
        获取当前用户名

        Returns:
            当前用户信息
        """
        return self.query("SELECT USER()")

    def get_version(self) -> List[Dict[str, Any]]:
        """
        获取数据库版本

        Returns:
            数据库版本信息
        """
        self.logger.debug(f"获取数据库版本")
        return self.query("SELECT VERSION()")

    def get_all_db(self) -> List[str]:
        """
        获取所有数据库名

        Returns:
            所有数据库名列表
        """
        self.logger.debug(f"获取数据库名")
        result = self.query("SHOW DATABASES")
        return [row["Database"] for row in result]

    def get_all_nonsys_db(self) -> List[str]:
        """
        获取除系统数据库外的所有数据库名

        Returns:
            非系统数据库名列表
        """
        exclude_list = ["sys", "information_schema", "mysql", "performance_schema"]
        self.logger.debug(f"获取除系统数据库外的所有数据库名")
        all_dbs = self.get_all_db()
        return [db for db in all_dbs if db not in exclude_list]

    def get_tables(self, dbname: str = "") -> List[str]:
        """
        获取指定数据库的所有表

        Args:
            dbname: 数据库名，默认为当前选择的数据库

        Returns:
            表名列表
        """
        dbname = dbname or self.__selected_db
        if not dbname:
            self.logger.error(f"未选择数据库, 无法获取表名")
            raise ValueError(f'未选择数据库, 无法获取表名')

        safe_db = self._escape_identifier(dbname)
        self.logger.debug(f"获取数据库[{dbname}]的所有表")
        result = self.query(f"SHOW TABLES FROM {safe_db}")
        table_column = f"Tables_in_{dbname}"
        return [row[table_column] for row in result]

    def table_exists(self, tablename: str) -> bool:
        """
        检查表是否存在

        Args:
            tablename: 表名

        Returns:
            表是否存在
        """
        if not self.__selected_db:
            raise ValueError("未选择数据库")

        tables = self.get_tables()
        return tablename in tables

    def get_columns(self, tablename: str) -> List[str]:
        """
        获取表的列名列表

        Args:
            tablename: 表名

        Returns:
            列名列表
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        result = self.query(f"DESCRIBE {self._escape_identifier(tablename)}")
        return [row["Field"] for row in result]

    def get_table_index(self, tablename: str = '') -> List[Dict[str, Any]]:
        """
        获取表的索引信息

        Args:
            tablename: 表名，默认为当前选择的表

        Returns:
            索引信息列表
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        self.logger.debug(f"获取表[{tablename}]的索引信息")
        return self.query(f"SHOW INDEX FROM {self._escape_identifier(tablename)}")

    def create_db(self, dbname: str, bool_autoselect: bool = True):
        """
        创建数据库

        Args:
            dbname: 需要创建的数据库名
            bool_autoselect: 是否自动选择该数据库
        """
        # 注入sql检验
        if not re.match(r'^[a-zA-Z0-9_$#@]+$', dbname):
            self.logger.error(f"数据库名[{dbname}]不合法, 请使用以下符号: 字母、数字、下划线、美元符号、井号、@")
            raise ValueError(f'数据库名[{dbname}]不合法, 请使用以下符号: 字母、数字、下划线、美元符号、井号、@')

        self.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8 COLLATE utf8_general_ci")
        self.logger.info(f"MySQL数据库[{dbname}]创建成功")
        if bool_autoselect:
            self.select_db(dbname)

    def drop_db(self, dbname: str):
        """
        删除数据库

        Args:
            dbname: 需要删除的数据库名
        """
        safe_db = self._escape_identifier(dbname)
        self.execute(f"DROP DATABASE IF EXISTS {safe_db}")
        self.logger.info(f"MySQL数据库[{dbname}]删除成功")
        if dbname == self.__selected_db:
            self.__selected_db = None
            self.logger.debug(f"MySQL数据库[{dbname}]已清除选择")

    def create_table(self, tablename: str, attr_dict: Dict[str, str], primary_key: List[str] = None,
                     bool_id: bool = True, bool_autoselect: bool = True, **kwargs):
        """
        创建表

        Args:
            tablename: 需要创建的表名
            attr_dict: 字典 {列名: MySQL数据类型}, 表示表中的列及其数据类型
            primary_key: 主键列表
            bool_id: 是否添加 id 为自增主键
            bool_autoselect: 创建表格后是否自动选择该表格
            **kwargs: 额外参数 (如 engine, charset, collate, indices)
        """
        # 检查表名有效性
        if not re.match(r'^[a-zA-Z0-9_]+$', tablename):
            self.logger.error("表名无效, 只能包含字母、数字和下划线")
            raise ValueError("表名只能包含字母、数字和下划线")

        # 检查attr_dict类型
        if not isinstance(attr_dict, dict):
            self.logger.error("attr_dict必须为字典类型")
            raise TypeError("attr_dict必须为字典类型")

        # 初始化主键列表
        primary_key = primary_key.copy() if primary_key else []

        # 处理自增ID逻辑
        schema = {}
        if bool_id:
            if 'id' in attr_dict:
                # 用户自定义了id列, 验证数据类型并添加AUTO_INCREMENT
                data_type = attr_dict['id'].upper()
                base_type = re.match(r'^\w+', data_type).group()
                allowed_types = ['INT', 'INTEGER', 'TINYINT', 'SMALLINT', 'BIGINT']
                if base_type not in allowed_types:
                    self.logger.error(f"ID列的数据类型{data_type}不支持自增")
                    raise ValueError("ID列必须为整数类型以支持自增")
                if 'AUTO_INCREMENT' not in data_type:
                    data_type += ' AUTO_INCREMENT'
                schema['id'] = data_type
                # 确保ID在主键中
                if 'id' not in primary_key:
                    primary_key.append('id')
                # 添加其他列(排除ID)
                for col, dtype in attr_dict.items():
                    if col != 'id':
                        schema[col] = dtype
            else:
                # 自动添加ID列
                schema['id'] = "INT AUTO_INCREMENT"
                if 'id' not in primary_key:
                    primary_key.append('id')
                # 添加所有列
                schema.update(attr_dict)
        else:
            # 无自增ID, 直接添加所有列
            schema = attr_dict.copy()

        # 生成建表SQL
        sql = self.query_builder.build_create_table(
            tablename=tablename,
            schema=schema,
            primary_key=primary_key,
            if_not_exists=True,
            **kwargs
        )

        # 执行SQL
        self.execute(sql)
        self.logger.info(f"创建表 {tablename} 成功")
        if bool_autoselect:
            self.select_table(tablename)

    def drop_table(self, tablename: str = '', if_exists: bool = True):
        """
        删除表

        Args:
            tablename: 表名，默认为当前选择的表
            if_exists: 是否添加IF EXISTS子句
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        sql = self.query_builder.build_drop_table(tablename, if_exists)
        self.execute(sql)
        self.logger.info(f"删除表 {tablename} 成功")
        if tablename == self.__selected_table:
            self.__selected_table = None

    def insert(self, tablename: str = '', record: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
               ignore_duplicates: bool = False, return_id: bool = False, **kwargs):
        """
        插入数据

        Args:
            tablename: 表名，默认为当前选择的表
            record: 要插入的记录或记录列表
            ignore_duplicates: 是否忽略重复记录
            return_id: 是否返回插入ID
            **kwargs: 其他参数

        Returns:
            如果return_id为True，返回插入ID；否则返回None
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        if not record:
            self.logger.error("插入数据失败: record 参数不能为空")
            raise ValueError("record 参数不能为空")

        # 构建插入SQL
        sql, params = self.query_builder.build_insert(
            tablename=tablename,
            data=record,
            ignore=ignore_duplicates,
            **kwargs
        )

        # 执行SQL
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.__connection.cursor()
            cursor.execute(sql, params)
            if not self.__in_transaction:
                self.__connection.commit()
            self.logger.info(f"成功插入数据到表 {tablename}")

            # 返回插入ID
            if return_id:
                last_id = cursor.lastrowid
                return last_id
        except Exception as e:
            if not self.__in_transaction:
                self.__connection.rollback()
            self.logger.error(f"插入数据失败: {e}")
            raise RuntimeError(e) from None
        finally:
            if cursor:
                cursor.close()

        return None

    def select(self, tablename: str = "", conditions: Dict = None,
               order: Dict[str, bool] = None, fields: List[str] = None,
               limit: int = None, offset: int = None, bool_dict: bool = False,
               stream: bool = False, size: int = 5000,
               use_index_hint: bool = False, use_server_side_cursor: bool = True, **kwargs) -> Union[
            list[dict[str, Any]], dict[str, Any], Generator[dict[str, Any], None, None]]:
        """
        查询数据

        Args:
            tablename: 表名，默认为当前选择的表
            conditions: 查询条件
            order: 排序 {列名: 是否升序}
            fields: 要查询的字段列表
            limit: 限制返回记录数
            offset: 跳过前N条记录
            bool_dict: 是否以字典形式返回结果 {列名: [列值列表]}，默认为False
            stream: 是否以流式方式返回结果，优先级高于bool_dict
            size: 流式查询时的批量大小
            use_index_hint: 是否添加索引提示
            use_server_side_cursor: 是否使用服务器端游标（减少内存使用）
            **kwargs: 其他参数

        Returns:
            如果stream为True，返回结果迭代器；
            如果bool_dict为False，返回查询结果列表；
            如果bool_dict为True，返回字典 {列名: [列值列表]}
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        # 构建查询SQL
        sql, params = self.query_builder.build_select(
            tablename=tablename,
            fields=fields,
            conditions=conditions,
            order=order,
            limit=limit,
            offset=offset,
            **kwargs
        )

        # 添加索引提示
        if use_index_hint and conditions:
            # 根据条件猜测可能的索引
            index_candidates = []
            for col in conditions:
                if isinstance(col, str):
                    index_candidates.append(col)

            if index_candidates:
                # 检查表是否有这些索引
                safe_table = self.query_builder.escape_identifier(tablename)
                indexes = self.get_table_index(tablename)
                available_indexes = []

                for index in indexes:
                    if index["Column_name"] in index_candidates:
                        available_indexes.append(index["Key_name"])

                if available_indexes:
                    # 在FROM子句后添加USE INDEX提示
                    sql = sql.replace(f"FROM {safe_table}",
                                      f"FROM {safe_table} USE INDEX ({', '.join(set(available_indexes))})", 1)

        # 流式查询
        if stream:
            return self.stream_query(
                sql=sql,
                args=params,
                size=size,
                bool_dict=bool_dict,
                use_server_side_cursor=use_server_side_cursor
            )

        # 普通查询
        return self.query(sql, params, bool_dict=bool_dict)

    def update(self, tablename: str = '', update_values: Dict[str, Any] = None,
               conditions: Dict = None, **kwargs):
        """
        更新数据

        Args:
            tablename: 表名，默认为当前选择的表
            update_values: 要更新的值
            conditions: 更新条件
            **kwargs: 其他参数

        Returns:
            更新的行数
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        if not update_values:
            raise ValueError("update_values 不能为空")

        # 构建更新SQL
        sql, params = self.query_builder.build_update(
            tablename=tablename,
            update_values=update_values,
            conditions=conditions,
            **kwargs
        )

        # 执行更新
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.__connection.cursor()
            cursor.execute(sql, params)
            if not self.__in_transaction:
                self.__connection.commit()
            self.logger.info(f"更新表 {tablename} 成功，受影响行数: {cursor.rowcount}")
            return cursor.rowcount
        except Exception as e:
            if not self.__in_transaction:
                self.__connection.rollback()
            self.logger.error(f"更新数据失败: {e}")
            raise RuntimeError(e) from None
        finally:
            if cursor:
                cursor.close()

    def delete(self, tablename: str = '', conditions: Dict = None, **kwargs):
        """
        删除数据

        Args:
            tablename: 表名，默认为当前选择的表
            conditions: 删除条件
            **kwargs: 其他参数

        Returns:
            删除的行数
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        # 检查危险操作
        if not conditions:
            self.logger.warning("警告: 正在执行全表删除操作!")

        # 构建删除SQL
        sql, params = self.query_builder.build_delete(
            tablename=tablename,
            conditions=conditions,
            **kwargs
        )

        # 执行删除
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.__connection.cursor()
            cursor.execute(sql, params)
            if not self.__in_transaction:
                self.__connection.commit()
            self.logger.info(f"从表 {tablename} 删除数据成功，受影响行数: {cursor.rowcount}")
            return cursor.rowcount
        except Exception as e:
            if not self.__in_transaction:
                self.__connection.rollback()
            self.logger.error(f"删除数据失败: {e}")
            raise RuntimeError(e) from None
        finally:
            if cursor:
                cursor.close()

    def purge(self, tablename: str = ''):
        """
        清空表数据

        Args:
            tablename: 表名，默认为当前选择的表
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        safe_table = self._escape_identifier(tablename)
        sql = f"TRUNCATE TABLE {safe_table}"
        self.execute(sql)
        self.logger.info(f"表 {tablename} 已清空")

    def join(self, main_table: str, joins: List[Tuple[str, str, JoinType, Dict[str, str]]],
             conditions: Dict = None, fields: Dict[str, List[str]] = None,
             order: Dict[str, bool] = None, limit: int = None, offset: int = None,
             bool_dict: bool = False, **kwargs):
        """
        执行连接查询

        Args:
            main_table: 主表
            joins: 连接表定义 [(表名, 别名, 连接类型, {主表字段: 连接表字段}), ...]
            conditions: 查询条件
            fields: 查询字段 {表别名: [字段名, ...], ...}
            order: 排序 {字段名: 是否升序}
            limit: 限制返回记录数
            offset: 跳过前N条记录
            bool_dict: 返回格式为 True 字典Dict[str, Any] False 列表List[Dict[str, Any]]
            **kwargs: 其他参数

        Returns:
            查询结果
        """
        # 构建连接查询SQL
        sql, params = self.query_builder.build_join(
            main_table=main_table,
            joins=joins,
            fields=fields,
            conditions=conditions,
            order=order,
            limit=limit,
            offset=offset,
            **kwargs
        )

        # 执行查询
        return self.query(sql, params, bool_dict=bool_dict)

    def upsert(self, tablename: str, record: Dict[str, Any], unique_fields: List[str], **kwargs):
        """
        更新插入操作

        Args:
            tablename: 表名
            record: 记录
            unique_fields: 唯一标识字段
            **kwargs: 其他参数

        Returns:
            是否成功
        """
        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        # MySQL支持ON DUPLICATE KEY UPDATE
        fields = list(record.keys())
        values = list(record.values())

        # 构建字段和占位符
        fields_str = ", ".join([f"`{field}`" for field in fields])
        placeholders = ", ".join(["%s"] * len(fields))

        # 构建UPDATE部分
        # 排除唯一字段
        update_parts = []
        for field in fields:
            if field not in unique_fields:
                update_parts.append(f"`{field}`=VALUES(`{field}`)")

        # 构建SQL
        sql = f"INSERT INTO `{tablename}` ({fields_str}) VALUES ({placeholders})"
        if update_parts:
            sql += f" ON DUPLICATE KEY UPDATE {', '.join(update_parts)}"

        # 执行SQL
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.__connection.cursor()
            cursor.execute(sql, values)
            if not self.__in_transaction:
                self.__connection.commit()
            self.logger.info(f"Upsert到表 {tablename} 成功")
            return True
        except Exception as e:
            if not self.__in_transaction:
                self.__connection.rollback()
            self.logger.error(f"Upsert失败: {e}")
            raise RuntimeError(e) from None
        finally:
            if cursor:
                cursor.close()

    def batch_insert(self, tablename: str, records: List[Dict[str, Any]],
                     size: int = 1000, **kwargs):
        """
        批量插入数据

        Args:
            tablename: 表名
            records: 记录列表
            size: 每批数量
            **kwargs: 其他参数

        Returns:
            插入的记录数
        """
        if not records:
            return 0

        tablename = tablename or self.__selected_table
        if not tablename:
            raise ValueError("未指定表名")

        total = 0
        for i in range(0, len(records), size):
            batch = records[i:i + size]
            # 构建批量插入SQL
            sql, params = self.query_builder.build_insert(
                tablename=tablename,
                data=batch,
                **kwargs
            )

            # 执行插入
            self._ensure_connection()
            cursor = None
            try:
                cursor = self.__connection.cursor()
                cursor.execute(sql, params)
                if not self.__in_transaction:
                    self.__connection.commit()
                total += len(batch)
                self.logger.info(f"批量插入到表 {tablename} 成功，本批插入 {len(batch)} 条")
            except Exception as e:
                if not self.__in_transaction:
                    self.__connection.rollback()
                self.logger.error(f"批量插入失败: {e}")
                raise RuntimeError(e) from None
            finally:
                if cursor:
                    cursor.close()

        return total

    def change_passwd(self, username: str, new_password: str, host: str = "localhost"):
        """
        修改密码

        Args:
            username: 用户名
            new_password: 新密码
            host: 用户登录主机，默认localhost
        """
        host = host or "localhost"
        sql = f"ALTER USER '{username}'@'{host}' IDENTIFIED BY '{new_password}'"
        self.execute(sql)
        self.logger.info("修改密码成功")

    def get_permissions(self):
        """
        获取当前用户权限

        Returns:
            权限信息字典
        """
        # SQL语句用于查询当前用户的权限
        sql = "SHOW GRANTS FOR CURRENT_USER();"

        def parse_grants(_grants):
            """解析GRANT语句"""
            permissions = {}
            for grant in _grants:
                if not grant.startswith('GRANT '):
                    continue

                # 提取权限部分和数据库名
                grant_part = grant[6:].split(' ON ', 1)
                if len(grant_part) != 2:
                    continue

                privs_str, db_part = grant_part[0], grant_part[1]
                db_name = db_part.split(' TO ')[0].strip().replace('`', '')

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

        result = self.query(sql)
        privileges = [row[f"Grants for {self.adapter.config['user']}@%"] for row in result]
        self.logger.info("查询当前用户权限成功")
        return parse_grants(privileges)

    def _escape_identifier(self, identifier: str) -> str:
        """
        转义标识符

        Args:
            identifier: 标识符

        Returns:
            转义后的标识符
        """
        return self.query_builder.escape_identifier(identifier)
