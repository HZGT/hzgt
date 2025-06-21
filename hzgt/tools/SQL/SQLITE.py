# -*- coding: utf-8 -*-
import csv
import os
import re
import sqlite3
from contextlib import contextmanager
from enum import Enum
from logging import Logger
from typing import Dict, Optional, Any, List, Tuple, Union

from .core import SQLutilop, QueryBuilder, DBAdapter
from ...log import set_log


class JoinType(Enum):
    """连接类型枚举"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"  # SQLite不完全支持FULL JOIN


class SQLiteAdapter(DBAdapter):
    """SQLite数据库适配器实现"""

    def __init__(self, db_name: str, logger: Optional[Logger] = None):
        """
        初始化SQLite适配器

        Args:
            db_name: 数据库文件路径
            logger: 日志记录器
        """
        self.db_name = db_name
        self.logger = logger

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        try:
            # 启用外键约束
            conn = sqlite3.connect(self.db_name)
            conn.execute("PRAGMA foreign_keys = ON")

            # 配置连接以返回行为字典
            conn.row_factory = sqlite3.Row

            if self.logger:
                self.logger.debug(f"SQLite数据库连接已建立: {self.db_name}")
            return conn
        except sqlite3.Error as e:
            if self.logger:
                self.logger.error(f"SQLite连接失败: {e}")
            raise RuntimeError(f"SQLite数据库连接失败: {e}") from None

    def close_connection(self, connection: sqlite3.Connection):
        """关闭数据库连接"""
        if connection:
            connection.close()
            if self.logger:
                self.logger.debug("SQLite数据库连接已关闭")

    def execute_query(self, connection: sqlite3.Connection, sql: str,
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
            cursor.execute(sql, params or ())

            # 获取结果
            if cursor.description:  # SELECT查询有结果
                # 将结果转换为字典列表
                columns = [col[0] for col in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append({columns[i]: row[i] for i in range(len(columns))})
                return results, cursor.rowcount
            else:
                # 非SELECT查询，无结果集
                return [], cursor.rowcount
        except sqlite3.Error as e:
            if self.logger:
                self.logger.error(f"执行SQL失败: {sql} | 参数: {params} | 错误: {e}")
            raise RuntimeError(e) from None
        finally:
            if cursor:
                cursor.close()

    def get_last_insert_id(self, connection: sqlite3.Connection, table_name: str = None) -> int:
        """获取最后插入的ID"""
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            if cursor:
                cursor.close()

    def get_placeholder_style(self) -> str:
        """获取参数占位符样式"""
        return "?"

    @staticmethod
    def format_table_creation(tablename: str,
                              columns: Dict[str, Dict[str, str]],
                              primary_keys: List[str],
                              **kwargs) -> tuple[str, list[str]]:
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
                column_defs.append(f'"{column}" {details}')
            else:
                # 详细定义
                type_def = details.get("type", "TEXT")
                constraint = details.get("constraint", "")
                column_defs.append(f'"{column}" {type_def} {constraint}'.strip())

        # 添加主键定义
        if primary_keys:
            pk_cols = ", ".join([f'"{pk}"' for pk in primary_keys])
            column_defs.append(f"PRIMARY KEY ({pk_cols})")

        # 添加索引定义
        indices = kwargs.get("indices", [])
        foreign_keys = kwargs.get("foreign_keys", {})

        # 添加外键约束
        for fk_col, fk_def in foreign_keys.items():
            ref_table = fk_def.get("table")
            ref_col = fk_def.get("column", "id")
            on_delete = fk_def.get("on_delete", "CASCADE")
            on_update = fk_def.get("on_update", "CASCADE")
            column_defs.append(
                f'FOREIGN KEY ("{fk_col}") REFERENCES "{ref_table}"("{ref_col}") '
                f'ON DELETE {on_delete} ON UPDATE {on_update}'
            )

        # WITHOUT ROWID优化
        without_rowid = kwargs.get("without_rowid", False)
        without_rowid_clause = "WITHOUT ROWID" if without_rowid else ""

        sql = (f'CREATE TABLE {"IF NOT EXISTS " if kwargs.get("if_not_exists", True) else ""}"{tablename}" (\n'
               f'  {",  ".join(column_defs)}\n'
               f') {without_rowid_clause}')

        # 构建索引创建语句（SQLite中通常作为单独的语句）
        index_statements = []
        for idx in indices:
            if isinstance(idx, dict):
                idx_name = idx.get("name", f"idx_{tablename}_{'_'.join(idx.get('columns', []))}")
                idx_type = "UNIQUE INDEX" if idx.get("unique", False) else "INDEX"
                idx_cols = idx.get("columns", [])
                if idx_cols:
                    idx_cols_str = ", ".join([f'"{col}"' for col in idx_cols])
                    index_sql = f'CREATE {idx_type} IF NOT EXISTS "{idx_name}" ON "{tablename}"({idx_cols_str})'
                    index_statements.append(index_sql)

        return sql, index_statements


class SQLiteQueryBuilder(QueryBuilder):
    """SQLite查询构建器实现"""

    def __init__(self, logger: Optional[Logger] = None):
        """
        初始化SQLite查询构建器

        Args:
            logger: 日志记录器
        """
        self.logger = logger

    @staticmethod
    def escape_identifier(identifier: str) -> str:
        """转义标识符(表名、列名)"""
        return f'"{identifier.replace("`", "")}"'

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
                        # 映射操作符
                        op_map = {
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
                        }

                        op = op_map.get(
                            op_symbol.lower() if op_symbol.startswith('$') else op_symbol
                        )
                        if not op:
                            raise ValueError(f"无效操作符: {op_symbol}")

                        if op in ('BETWEEN', 'NOT BETWEEN'):
                            if not isinstance(op_value, (list, tuple)) or len(op_value) != 2:
                                raise ValueError(f"{op} 需要两个值的列表")
                            where_parts.append(f"{safe_col} {op} ? AND ?")
                            params.extend(op_value)
                        elif op in ('IN', 'NOT IN'):
                            if not isinstance(op_value, (list, tuple)):
                                raise ValueError(f"{op} 需要列表或元组")
                            placeholders = ', '.join(['?'] * len(op_value))
                            where_parts.append(f"{safe_col} {op} ({placeholders})")
                            params.extend(op_value)
                        elif op in ('IS', 'IS NOT'):
                            # IS NULL 和 IS NOT NULL 不需要参数
                            where_parts.append(f"{safe_col} {op} NULL"
                                               if op_value is None else f"{safe_col} {op} ?")
                            if op_value is not None:
                                params.append(op_value)
                        else:
                            where_parts.append(f"{safe_col} {op} ?")
                            params.append(op_value)
                else:
                    # 简单等值条件
                    if value is None:
                        where_parts.append(f"{safe_col} IS NULL")
                    else:
                        where_parts.append(f"{safe_col} = ?")
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
            sql += f" LIMIT ?"
            params.append(int(limit))
            if offset is not None:
                sql += f" OFFSET ?"
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
        values_placeholder = "(" + ", ".join(["?"] * len(fields)) + ")"

        # 构建批量插入的值
        values = []
        for record in records:
            record_values = [record.get(field) for field in fields]
            values.extend(record_values)

        # 处理插入选项
        ignore = kwargs.get("ignore", False)
        conflict_action = kwargs.get("conflict_action", "ABORT")
        conflict_columns = kwargs.get("conflict_columns", [])

        # 构建SQL (SQLite 使用 INSERT OR 语法)
        if ignore:
            conflict_action = "IGNORE"

        sql = f"INSERT OR {conflict_action} INTO {safe_table} ({fields_str}) VALUES "

        if is_batch:
            # SQLite不支持多行语法，需要返回多个语句
            placeholders = []
            for i in range(len(records)):
                placeholders.append(values_placeholder)

            sql += values_placeholder

            # 如果是批量插入，我们需要单独处理每个INSERT
            # 返回单条SQL和所有值，在上层函数中处理实际的批量执行

        else:
            sql += values_placeholder

        # SQLite ON CONFLICT 子句 (类似于MySQL的ON DUPLICATE KEY UPDATE)
        if conflict_columns and kwargs.get("update_on_conflict") and not ignore:
            update_values = kwargs.get("update_values", {})
            if update_values:
                conflict_fields = ", ".join([self.escape_identifier(col) for col in conflict_columns])
                update_parts = []
                for field, value in update_values.items():
                    update_parts.append(f"{self.escape_identifier(field)} = ?")
                    values.append(value)
                sql += f" ON CONFLICT({conflict_fields}) DO UPDATE SET {', '.join(update_parts)}"

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
            set_parts.append(f"{safe_field} = ?")
            set_params.append(value)

        # 构建WHERE子句
        where_clause, where_params = self._build_where_clause(conditions)

        # 构建SQL
        sql = f"UPDATE {safe_table} SET {', '.join(set_parts)}"
        params = set_params

        if where_clause:
            sql += f" WHERE {where_clause}"
            params.extend(where_params)

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

        return sql, params

    def build_create_table(self,
                           tablename: str,
                           schema: Dict[str, Any],
                           primary_key: Optional[List[str]] = None,
                           if_not_exists: bool = True,
                           **kwargs) -> tuple[str, list[str]]:
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
                # 简单格式: {column: "INTEGER PRIMARY KEY"}
                col_def = f"{self.escape_identifier(column)} {details}"
            elif isinstance(details, dict):
                # 详细格式: {column: {type: "INTEGER", constraint: "PRIMARY KEY"}}
                col_type = details.get("type", "TEXT")
                constraint = details.get("constraint", "")
                col_def = f"{self.escape_identifier(column)} {col_type} {constraint}".strip()

            if col_def:
                column_defs.append(col_def)

        # 处理主键
        if primary_key:
            # 检查是否已经在列定义中指定了主键
            has_primary_key = any("PRIMARY KEY" in str(details).upper() for details in schema.values())
            if not has_primary_key:
                safe_pk = [self.escape_identifier(pk) for pk in primary_key]
                column_defs.append(f"PRIMARY KEY ({', '.join(safe_pk)})")

        # 处理外键
        foreign_keys = kwargs.get("foreign_keys", {})
        for fk_col, fk_def in foreign_keys.items():
            ref_table = fk_def.get("table")
            ref_col = fk_def.get("column", "id")
            on_delete = fk_def.get("on_delete", "CASCADE")
            on_update = fk_def.get("on_update", "CASCADE")
            column_defs.append(
                f'FOREIGN KEY ({self.escape_identifier(fk_col)}) '
                f'REFERENCES {self.escape_identifier(ref_table)}({self.escape_identifier(ref_col)}) '
                f'ON DELETE {on_delete} ON UPDATE {on_update}'
            )

        # 处理索引
        indices = []
        for idx in kwargs.get("indices", []):
            if isinstance(idx, dict):
                idx_name = idx.get("name", f"idx_{tablename}_{'_'.join(idx.get('columns', []))}")
                idx_type = "UNIQUE" if idx.get("unique", False) else ""
                idx_cols = [self.escape_identifier(col) for col in idx.get("columns", [])]
                if idx_cols:
                    indices.append((idx_name, idx_type, idx_cols))

        # 其他选项
        without_rowid = "WITHOUT ROWID" if kwargs.get("without_rowid", False) else ""

        # 构建最终SQL
        sql = (f"CREATE TABLE {f'IF NOT EXISTS ' if if_not_exists else ''}{safe_table} (\n"
               f"  {',  '.join(column_defs)}\n"
               f") {without_rowid}")

        # SQLite不在CREATE TABLE中创建索引，需要额外的语句
        index_sqls = []
        for idx_name, idx_type, idx_cols in indices:
            index_sqls.append(
                f"CREATE {idx_type} INDEX IF NOT EXISTS {self.escape_identifier(idx_name)} "
                f"ON {safe_table}({', '.join(idx_cols)})"
            )

        return sql, index_sqls

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
            sql += f" LIMIT ?"
            params.append(int(limit))
            if offset is not None:
                sql += f" OFFSET ?"
                params.append(int(offset))

        return sql, params


class SQLiteop(SQLutilop):
    """SQLite操作工具，基于抽象框架实现"""

    def __init__(self, db_name: str, logger: Optional[Logger] = None):
        """
        初始化SQLite操作工具

        Args:
            db_name: 数据库文件路径
            logger: 日志记录器
        """
        # 日志配置
        super().__init__(logger)

        self.db_name = db_name
        self.adapter = SQLiteAdapter(db_name, self.logger)
        self.query_builder = SQLiteQueryBuilder(self.logger)

        self.__connection = None
        self.__in_transaction = False
        self.__selected_table = None

        self.logger.info(f'SQLite工具初始化完成，数据库: {db_name}')

    def _create_default_logger(self) -> Logger:
        """
        创建默认日志记录器

        Returns:
            Logger: 日志记录器实例
        """
        return set_log("hzgt.sqlite", os.path.join("logs", "sqlite.log"))

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
        try:
            self.__connection = self.adapter.get_connection()
            self.logger.info(f"SQLite连接成功: {self.db_name}")
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            raise RuntimeError(f"数据库连接失败: {e}") from None

    def start(self):
        """建立数据库连接"""
        self.connect()

    def close(self):
        """关闭数据库连接"""
        if self.__connection:
            try:
                if self.__in_transaction:
                    self.logger.warning("关闭连接时有未提交的事务，执行回滚")
                    self.rollback()
                self.adapter.close_connection(self.__connection)
                self.logger.debug("SQLite连接已关闭")
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
        if not self.__connection:
            self.connect()
        if not self.__in_transaction:
            self.__connection.execute("BEGIN")
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
        if not self.__connection:
            self.connect()

        try:
            cursor = self.__connection.cursor()
            try:
                cursor.execute(sql, args or ())
                if not self.__in_transaction and sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    self.__connection.commit()

                # 检查是否为SELECT查询有结果
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        if isinstance(row, sqlite3.Row):
                            results.append(dict(row))
                        else:
                            results.append({columns[i]: row[i] for i in range(len(columns))})
                    return results
                else:
                    return cursor.rowcount  # 返回影响行数
            finally:
                cursor.close()
        except sqlite3.Error as e:
            if not self.__in_transaction:
                self.__connection.rollback()
            self.logger.error(f"执行SQL失败: {sql} | 参数: {args} | 错误: {e}")
            raise RuntimeError(e) from None

    def executemany(self, sql: str, args_list: List[Union[tuple, dict]]) -> Any:
        """批量执行SQL语句"""
        if not args_list:
            return None

        if not self.__connection:
            self.connect()

        try:
            cursor = self.__connection.cursor()
            try:
                result = cursor.executemany(sql, args_list)
                if not self.__in_transaction:
                    self.__connection.commit()
                return result
            finally:
                cursor.close()
        except sqlite3.Error as e:
            if not self.__in_transaction:
                self.__connection.rollback()
            self.logger.error(f"执行批量SQL失败: {sql} | 错误: {e}")
            raise RuntimeError(e) from None

    def query(self, sql: str, args: Optional[Union[tuple, dict, list]] = None,
              bool_dict: bool = False) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        执行查询并返回结果集

        Args:
            sql: SQL查询语句
            args: 查询参数
            bool_dict: 返回格式为 True 字典Dict[str, Any] False 列表List[Dict[str, Any]]

        Returns:
            查询结果列表，每项为一个字典
        """
        if not self.__connection:
            self.connect()

        cursor = None
        try:
            cursor = self.__connection.cursor()
            cursor.execute(sql, args or ())

            # 获取列名
            columns = [col[0] for col in cursor.description]

            # 转换结果为字典列表
            results = []
            for row in cursor.fetchall():
                if isinstance(row, sqlite3.Row):
                    results.append(dict(row))
                else:
                    results.append({columns[i]: row[i] for i in range(len(columns))})

            if bool_dict:
                if not results:
                    return {}
                return {key: [item[key] for item in results] for key in results[0]}

            return results
        except sqlite3.Error as e:
            self.logger.error(f"执行查询失败: {sql} | 错误: {e}")
            raise RuntimeError(e) from None
        finally:
            if cursor:
                cursor.close()

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

    # 获取所有的表名
    def get_tables(self) -> list[str]:
        return self.query("SELECT name FROM sqlite_master WHERE type='table'", bool_dict=True)["name"]

    def select_table(self, table_name: str):
        """
        选择表

        Args:
            table_name: 表名
        """
        self.__selected_table = table_name
        self.logger.debug(f"已记录选择表: {table_name}")

    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在

        Args:
            table_name: 表名

        Returns:
            表是否存在
        """
        result = self.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None

    def get_columns(self, table_name: str) -> List[str]:
        """
        获取表的列名列表

        Args:
            table_name: 表名

        Returns:
            列名列表
        """
        if not table_name:
            raise ValueError("未指定表名")

        result = self.query(f"PRAGMA table_info({self._escape_identifier(table_name)})")
        return [row["name"] for row in result]

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """
        检查表中是否存在某列

        Args:
            table_name: 表名
            column_name: 列名

        Returns:
            列是否存在
        """
        columns = self.get_columns(table_name)
        return column_name in columns

    def create_table(self, table_name: str, columns: Dict[str, str], primary_key: List[str] = None,
                     if_not_exists: bool = True, **kwargs):
        """
        创建表

        Args:
            table_name: 表名
            columns: 列定义 {列名: 类型}
            primary_key: 主键列表
            if_not_exists: 是否添加IF NOT EXISTS子句
            **kwargs: 其他参数
        """
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            self.logger.error("表名无效，只能包含字母、数字和下划线")
            raise ValueError("表名只能包含字母、数字和下划线")

        # 构建表定义
        sql, index_sqls = self.query_builder.build_create_table(
            tablename=table_name,
            schema=columns,
            primary_key=primary_key,
            if_not_exists=if_not_exists,
            **kwargs
        )

        if not self.__connection:
            self.connect()

        # 创建表
        try:
            with self.transaction():
                self.execute(sql)

                # 创建索引
                for index_sql in index_sqls:
                    self.execute(index_sql)

            self.logger.info(f"表 {table_name} 创建成功")
            self.select_table(table_name)
        except sqlite3.Error as e:
            self.logger.error(f"创建表 {table_name} 失败: {e}")
            raise RuntimeError(e) from None

    def drop_table(self, table_name: str = '', if_exists: bool = True):
        """
        删除表

        Args:
            table_name: 表名
            if_exists: 是否添加IF EXISTS子句
        """
        table_name = table_name or self.__selected_table
        if not table_name:
            raise ValueError("未指定表名")

        sql = self.query_builder.build_drop_table(table_name, if_exists)
        self.execute(sql)
        self.logger.info(f"表 {table_name} 删除成功")

        if table_name == self.__selected_table:
            self.__selected_table = None

    def insert(self, table_name: str = '', record: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
               return_id: bool = False, **kwargs):
        """
        插入数据

        Args:
            table_name: 表名
            record: 记录或记录列表
            return_id: 是否返回插入ID
            **kwargs: 其他参数

        Returns:
            如果return_id为True，返回插入ID
        """
        table_name = table_name or self.__selected_table
        if not table_name:
            raise ValueError("未指定表名")

        if not record:
            self.logger.error("插入数据失败: record 参数不能为空")
            raise ValueError("record 参数不能为空")

        # 构建SQL
        sql, params = self.query_builder.build_insert(
            tablename=table_name,
            data=record,
            **kwargs
        )

        if not self.__connection:
            self.connect()

        # 执行插入
        if isinstance(record, list):  # 批量插入
            rows = []
            for i in range(len(record)):
                item = record[i]
                values = [item.get(field) for field in record[0].keys()]
                rows.append(tuple(values))

            cursor = self.__connection.cursor()
            try:
                cursor.executemany(sql, rows)
                if not self.__in_transaction:
                    self.__connection.commit()
                self.logger.info(f"成功批量插入 {len(rows)} 条记录到表 {table_name}")

                if return_id:
                    # SQLite不支持批量插入返回ID
                    self.logger.warning("SQLite不支持批量插入时返回ID")
                    return None
            finally:
                cursor.close()
        else:  # 单条插入
            cursor = self.__connection.cursor()
            try:
                cursor.execute(sql, params)
                if not self.__in_transaction:
                    self.__connection.commit()
                self.logger.info(f"成功插入数据到表 {table_name}")

                if return_id:
                    last_id = cursor.lastrowid
                    return last_id
            finally:
                cursor.close()

        return None

    def select(self, table_name: str = "", conditions: Dict = None,
               order: Dict[str, bool] = None, fields: List[str] = None,
               limit: int = None, offset: int = None, bool_dict: bool = False, **kwargs):
        """
        查询数据

        Args:
            table_name: 表名
            conditions: 查询条件
            order: 排序条件
            fields: 查询字段
            limit: 限制记录数
            offset: 跳过记录数
            bool_dict: 返回格式为 True 字典Dict[str, Any] False 列表List[Dict[str, Any]]
            **kwargs: 其他参数

        Returns:
            查询结果列表
        """
        table_name = table_name or self.__selected_table
        if not table_name:
            raise ValueError("未指定表名")

        # 构建SQL
        sql, params = self.query_builder.build_select(
            tablename=table_name,
            fields=fields,
            conditions=conditions,
            order=order,
            limit=limit,
            offset=offset,
            **kwargs
        )

        # 执行查询
        return self.query(sql, params, bool_dict)

    def update(self, table_name: str = '', update_values: Dict[str, Any] = None,
               conditions: Dict = None, **kwargs):
        """
        更新数据

        Args:
            table_name: 表名
            update_values: 更新值
            conditions: 更新条件
            **kwargs: 其他参数

        Returns:
            更新的行数
        """
        table_name = table_name or self.__selected_table
        if not table_name:
            raise ValueError("未指定表名")

        if not update_values:
            raise ValueError("update_values 不能为空")

        # 构建SQL
        sql, params = self.query_builder.build_update(
            tablename=table_name,
            update_values=update_values,
            conditions=conditions,
            **kwargs
        )

        # 执行更新
        return self.execute(sql, params)

    def delete(self, table_name: str = '', conditions: Dict = None, **kwargs):
        """
        删除数据

        Args:
            table_name: 表名
            conditions: 删除条件
            **kwargs: 其他参数

        Returns:
            删除的行数
        """
        table_name = table_name or self.__selected_table
        if not table_name:
            raise ValueError("未指定表名")

        # 检查危险操作
        if not conditions:
            self.logger.warning("警告: 正在执行全表删除操作!")

        # 构建SQL
        sql, params = self.query_builder.build_delete(
            tablename=table_name,
            conditions=conditions,
            **kwargs
        )

        # 执行删除
        return self.execute(sql, params)

    def join(self, main_table: str, joins: List[Tuple[str, str, JoinType, Dict[str, str]]],
             conditions: Dict = None, fields: Dict[str, List[str]] = None,
             order: Dict[str, bool] = None, limit: int = None, offset: int = None,
             bool_dict: bool = False, **kwargs):
        """
        执行连接查询

        Args:
            main_table: 主表
            joins: 连接定义
            conditions: 查询条件
            fields: 查询字段
            order: 排序条件
            limit: 限制记录数
            offset: 跳过记录数
            bool_dict: 返回格式为 True 字典Dict[str, Any] False 列表List[Dict[str, Any]]
            **kwargs: 其他参数

        Returns:
            查询结果
        """
        # 构建SQL
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
        return self.query(sql, params, bool_dict)

    def batch_insert(self, table_name: str, records: List[Dict[str, Any]],
                     batch_size: int = 1000, **kwargs):
        """
        批量插入数据

        Args:
            table_name: 表名
            records: 记录列表
            batch_size: 每批大小
            **kwargs: 其他参数

        Returns:
            插入的记录数
        """
        if not records:
            return 0

        table_name = table_name or self.__selected_table
        if not table_name:
            raise ValueError("未指定表名")

        total = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            self.insert(table_name, batch, **kwargs)
            total += len(batch)

        return total

    def _escape_identifier(self, identifier: str) -> str:
        """
        转义标识符

        Args:
            identifier: 标识符

        Returns:
            转义后的标识符
        """
        return self.query_builder.escape_identifier(identifier)

    # -------- 原有SQLiteop特有方法 --------

    def start(self):
        """连接到数据库（保持与原接口兼容）"""
        self.connect()

    def enable_wal_mode(self) -> None:
        """
        启用 WAL 模式（Write-Ahead Logging）, 提高并发性能.
        """
        try:
            self.execute("PRAGMA journal_mode=WAL")
            self.logger.info("已启用 WAL 模式")
        except sqlite3.Error as e:
            self.logger.error(f"启用 WAL 模式失败: {e}")
            raise RuntimeError(e) from None

    def migrate_db(self, table_name: str, new_columns: Dict[str, str]) -> None:
        """
        数据库迁移: 添加新列.

        Args:
            table_name: 表名
            new_columns: 新列名和类型的字典
        """
        try:
            for col, dtype in new_columns.items():
                if not self.column_exists(table_name, col):
                    self.execute(f"ALTER TABLE {self._escape_identifier(table_name)} ADD COLUMN {col} {dtype}")
                    self.logger.info(f"已添加列 {col} 到表 {table_name}")
            if not self.__in_transaction:
                self.__connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"数据库迁移失败: {e}")
            raise RuntimeError(e) from None

    def export_to_csv(self, table_name: str, csv_path: str) -> None:
        """
        将表数据导出到 CSV 文件.

        Args:
            table_name: 表名
            csv_path: CSV 文件路径
        """
        try:
            rows = self.select(table_name)

            if not rows:
                self.logger.warning(f"表 {table_name} 没有数据可导出")
                return

            columns = list(rows[0].keys())

            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(columns)  # 写入列名
                for row in rows:
                    writer.writerow([row[col] for col in columns])  # 写入数据
            self.logger.info(f"数据已导出到 {csv_path}")
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            raise RuntimeError(e) from None

    def import_from_csv(self, table_name: str, csv_path: str) -> None:
        """
        从 CSV 文件导入数据到表.

        Args:
            table_name: 表名
            csv_path: CSV 文件路径
        """
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                columns = next(reader)  # 读取列名

                # 验证列是否存在于表中
                table_columns = self.get_columns(table_name)
                for col in columns:
                    if col not in table_columns:
                        raise ValueError(f"列 '{col}' 不存在于表 {table_name}")

                records = []
                for row in reader:
                    record = {columns[i]: row[i] for i in range(len(columns))}
                    records.append(record)

            if records:
                self.batch_insert(table_name, records)

            self.logger.info(f"数据已从 {csv_path} 导入到 {table_name}")
        except Exception as e:
            self.logger.error(f"导入数据失败: {e}")
            raise RuntimeError(e) from None

    def execute_sql_script(self, script_path: str) -> None:
        """
        执行 SQL 脚本文件.

        Args:
            script_path: SQL 脚本文件路径
        """
        try:
            with open(script_path, 'r') as f:
                sql_script = f.read()

            if not self.__connection:
                self.connect()

            self.__connection.executescript(sql_script)
            if not self.__in_transaction:
                self.__connection.commit()

            self.logger.info(f"已执行 SQL 脚本: {script_path}")
        except Exception as e:
            self.logger.error(f"执行 SQL 脚本失败: {e}")
            raise RuntimeError(e) from None

    def backup_db(self, target_db: str) -> None:
        """
        备份数据库.

        Args:
            target_db: 目标数据库文件名
        """
        if not self.__connection:
            self.connect()

        try:
            target_conn = sqlite3.connect(target_db)
            with target_conn:
                self.__connection.backup(target_conn)
            target_conn.close()
            self.logger.info(f"数据库已备份到 {target_db}")
        except sqlite3.Error as e:
            self.logger.error(f"备份数据库失败: {e}")
            raise RuntimeError(e) from None
