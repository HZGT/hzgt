# # -*- coding: utf-8 -*-
# import os
# import re
# import time
# from logging import Logger
# from typing import Dict, Optional, Any, List, Tuple, Union
#
# import psycopg2
# import psycopg2.extras
# import psycopg2.pool
#
# from .core.SQLutil import SQLutilop, ConnectionPool, QueryBuilder, DBAdapter, JoinType
# from ... import set_log
#
# # PostgreSQL数据类型映射
# PG_DATA_TYPES = {
#     'INTEGER': 'INTEGER',
#     'BIGINT': 'BIGINT',
#     'SMALLINT': 'SMALLINT',
#     'FLOAT': 'REAL',
#     'DOUBLE': 'DOUBLE PRECISION',
#     'DECIMAL': 'DECIMAL',
#     'NUMERIC': 'NUMERIC',
#     'CHAR': 'CHAR',
#     'VARCHAR': 'VARCHAR',
#     'TEXT': 'TEXT',
#     'DATE': 'DATE',
#     'DATETIME': 'TIMESTAMP',
#     'TIMESTAMP': 'TIMESTAMP',
#     'TIME': 'TIME',
#     'BOOLEAN': 'BOOLEAN',
#     'BLOB': 'BYTEA',
#     'BINARY': 'BYTEA',
#     'JSON': 'JSONB',
#     'JSONB': 'JSONB',
#     'ARRAY': 'ARRAY',
#     'UUID': 'UUID',
#     'INET': 'INET',
#     'CIDR': 'CIDR'
# }
#
#
# class PostgreSQLAdapter(DBAdapter[psycopg2._ext.connection]):
#     """PostgreSQL数据库适配器实现"""
#
#     def __init__(self, host: str, port: int, dbname: str, user: str, password: str,
#                  sslmode: str = "prefer", logger: Optional[Logger] = None):
#         """
#         初始化PostgreSQL适配器
#
#         Args:
#             host: 服务器主机名
#             port: 端口号
#             dbname: 数据库名
#             user: 用户名
#             password: 密码
#             sslmode: SSL模式
#             logger: 日志记录器
#         """
#         self.connection_params = {
#             "host": host,
#             "port": port,
#             "dbname": dbname,
#             "user": user,
#             "password": password,
#             "sslmode": sslmode
#         }
#         self.logger = logger
#
#     def get_connection(self, **kwargs) -> psycopg2._ext.connection:
#         """
#         获取数据库连接
#
#         Args:
#             **kwargs: 额外连接参数
#
#         Returns:
#             PostgreSQL连接对象
#
#         Raises:
#             RuntimeError: 连接失败时抛出
#         """
#         params = {**self.connection_params, **kwargs}
#         try:
#             # 创建连接
#             conn = psycopg2.connect(**params)
#
#             # 设置隔离级别和自动提交
#             conn.set_session(autocommit=True)
#
#             # 使用RealDictCursor，让查询结果以字典形式返回
#             conn.cursor_factory = psycopg2.extras.RealDictCursor
#
#             if self.logger:
#                 self.logger.debug(f"PostgreSQL数据库连接已建立: {params['dbname']}")
#
#             return conn
#         except psycopg2.Error as e:
#             if self.logger:
#                 self.logger.error(f"PostgreSQL连接失败: {e}")
#             raise RuntimeError(f"PostgreSQL数据库连接失败: {e}") from e
#
#     def close_connection(self, connection: psycopg2._ext.connection):
#         """
#         关闭数据库连接
#
#         Args:
#             connection: 要关闭的连接
#         """
#         if connection:
#             try:
#                 connection.close()
#                 if self.logger:
#                     self.logger.debug("PostgreSQL数据库连接已关闭")
#             except psycopg2.Error as e:
#                 if self.logger:
#                     self.logger.error(f"关闭PostgreSQL连接时出错: {e}")
#
#     def execute_query(self, connection: psycopg2._ext.connection, sql: str,
#                       params: Any = None) -> Tuple[List[Dict[str, Any]], int]:
#         """
#         执行查询并返回结果
#
#         Args:
#             connection: 数据库连接
#             sql: SQL语句
#             params: 参数
#
#         Returns:
#             (结果集, 影响行数)
#
#         Raises:
#             psycopg2.Error: 执行查询失败时抛出
#         """
#         cursor = None
#         try:
#             cursor = connection.cursor()
#
#             # 执行查询
#             cursor.execute(sql, params if params is not None else None)
#
#             # 处理SELECT查询结果
#             if cursor.description:
#                 results = cursor.fetchall()
#                 # psycopg2的RealDictCursor已经将结果转为字典列表
#                 return list(results), cursor.rowcount
#             else:
#                 # 非查询语句，返回影响的行数
#                 return [], cursor.rowcount
#
#         except psycopg2.Error as e:
#             if self.logger:
#                 self.logger.error(f"执行SQL失败: {sql} | 参数: {params} | 错误: {e}")
#             raise
#         finally:
#             if cursor:
#                 cursor.close()
#
#     def get_last_insert_id(self, connection: psycopg2._ext.connection, table_name: str = None) -> int:
#         """
#         获取最后插入的ID
#
#         Args:
#             connection: 数据库连接
#             table_name: 表名(PostgreSQL中，每个表的序列都有特定命名)
#
#         Returns:
#             最后插入的ID
#         """
#         cursor = None
#         try:
#             cursor = connection.cursor()
#             # PostgreSQL需要指定序列名或使用RETURNING子句
#             # 这里使用currval获取最后一个序列值
#             if table_name:
#                 # 假设序列名为tablename_id_seq
#                 seq_name = f"{table_name}_id_seq"
#                 cursor.execute(f"SELECT currval(%s)", (seq_name,))
#             else:
#                 # 使用最后一个插入语句的RETURNING子句结果
#                 cursor.execute("SELECT lastval()")
#
#             result = cursor.fetchone()
#             return result[0] if result else None
#         except psycopg2.Error as e:
#             if self.logger:
#                 self.logger.error(f"获取最后插入ID失败: {e}")
#             raise
#         finally:
#             if cursor:
#                 cursor.close()
#
#     def get_placeholder_style(self) -> str:
#         """
#         获取参数占位符样式
#
#         Returns:
#             PostgreSQL的占位符样式(%s)
#         """
#         return "%s"
#
#     def format_table_creation(self,
#                               tablename: str,
#                               columns: Dict[str, Dict[str, str]],
#                               primary_keys: List[str],
#                               **kwargs) -> str:
#         """
#         格式化建表语句
#
#         Args:
#             tablename: 表名
#             columns: 列定义 {列名: {type: 类型, constraint: 约束}}
#             primary_keys: 主键列表
#             **kwargs: 额外参数
#
#         Returns:
#             建表SQL
#         """
#         column_defs = []
#
#         # 处理架构
#         schema_name = kwargs.get("schema", "public")
#         table_with_schema = f"{schema_name}.{tablename}" if schema_name != "public" else tablename
#
#         for column, details in columns.items():
#             if isinstance(details, str):
#                 # 简单类型定义
#                 column_defs.append(f'"{column}" {details}')
#             else:
#                 # 详细定义
#                 type_def = details.get("type", "VARCHAR(255)")
#                 # 转换通用SQL类型到PostgreSQL类型
#                 if type_def.upper() in PG_DATA_TYPES:
#                     type_def = PG_DATA_TYPES[type_def.upper()]
#
#                 constraint = details.get("constraint", "")
#                 column_defs.append(f'"{column}" {type_def} {constraint}'.strip())
#
#         # 添加主键定义
#         if primary_keys:
#             pk_cols = ", ".join([f'"{pk}"' for pk in primary_keys])
#             column_defs.append(f"PRIMARY KEY ({pk_cols})")
#
#         # 添加外键约束
#         foreign_keys = kwargs.get("foreign_keys", {})
#         for fk_col, fk_def in foreign_keys.items():
#             ref_table = fk_def.get("table")
#             ref_col = fk_def.get("column", "id")
#             on_delete = fk_def.get("on_delete", "CASCADE")
#             fk_name = fk_def.get("name", f"fk_{tablename}_{fk_col}")
#
#             column_defs.append(
#                 f'CONSTRAINT {fk_name} FOREIGN KEY ("{fk_col}") '
#                 f'REFERENCES "{ref_table}"("{ref_col}") '
#                 f'ON DELETE {on_delete}'
#             )
#
#         # 构建建表SQL
#         sql = f'CREATE TABLE "{table_with_schema}" (\n  {",  ".join(column_defs)}\n)'
#
#         # 添加表选项
#         if kwargs.get("unlogged", False):
#             sql = sql.replace("CREATE TABLE", "CREATE UNLOGGED TABLE")
#
#         if kwargs.get("temp", False):
#             sql = sql.replace("CREATE TABLE", "CREATE TEMPORARY TABLE")
#
#         return sql
#
#
# class PostgreSQLQueryBuilder(QueryBuilder):
#     """PostgreSQL查询构建器实现"""
#
#     def __init__(self, logger: Optional[Logger] = None):
#         """
#         初始化PostgreSQL查询构建器
#
#         Args:
#             logger: 日志记录器
#         """
#         self.logger = logger
#         self.param_index = 0  # 用于生成参数占位符
#
#     def reset_param_index(self):
#         """重置参数索引"""
#         self.param_index = 0
#
#     @staticmethod
#     def next_param() -> str:
#         """
#         生成下一个参数占位符
#
#         Returns:
#             参数占位符(%s)
#         """
#         # PostgreSQL使用位置参数，但在这里我们使用%s，psycopg2会处理参数替换
#         return "%s"
#
#     def next_param_index(self) -> int:
#         """
#         获取并递增参数索引
#
#         Returns:
#             参数索引
#         """
#         self.param_index += 1
#         return self.param_index
#
#     @staticmethod
#     def _escape_identifier(identifier: str) -> str:
#         """
#         转义标识符(表名、列名)
#
#         Args:
#             identifier: 标识符
#
#         Returns:
#             转义后的标识符
#         """
#         # PostgreSQL使用双引号转义标识符
#         return f'"{identifier.replace("`", "")}"'
#
#     def _build_where_clause(self, conditions: Optional[Dict]) -> Tuple[str, List]:
#         """
#         构建WHERE子句和参数
#
#         Args:
#             conditions: 查询条件
#
#         Returns:
#             (WHERE子句, 参数列表)
#
#         Raises:
#             ValueError: 无效的操作符
#         """
#         if not conditions:
#             return "", []
#
#         self.reset_param_index()
#         where_parts = []
#         params = []
#
#         # 处理逻辑组合
#         if '$or' in conditions or '$and' in conditions:
#             if '$or' in conditions:
#                 subclauses = []
#                 for subcond in conditions['$or']:
#                     subwhere, subparams = self._build_where_clause(subcond)
#                     if subwhere:
#                         subclauses.append(f"({subwhere})")
#                         params.extend(subparams)
#                 if subclauses:
#                     where_parts.append(f"({' OR '.join(subclauses)})")
#
#             if '$and' in conditions:
#                 subclauses = []
#                 for subcond in conditions['$and']:
#                     subwhere, subparams = self._build_where_clause(subcond)
#                     if subwhere:
#                         subclauses.append(f"({subwhere})")
#                         params.extend(subparams)
#                 if subclauses:
#                     where_parts.append(f"({' AND '.join(subclauses)})")
#
#             # 处理其余普通条件
#             other_conditions = {k: v for k, v in conditions.items()
#                                 if k not in ('$or', '$and')}
#             if other_conditions:
#                 subwhere, subparams = self._build_where_clause(other_conditions)
#                 if subwhere:
#                     where_parts.append(subwhere)
#                     params.extend(subparams)
#         else:
#             # 处理普通条件
#             for column, value in conditions.items():
#                 # 跳过特殊键
#                 if column.startswith('$'):
#                     continue
#
#                 # 转义列名
#                 safe_col = self._escape_identifier(column.strip())
#
#                 if isinstance(value, dict):
#                     # 处理操作符条件
#                     for op_symbol, op_value in value.items():
#                         # 映射操作符
#                         op_map = {
#                             '>': '>', '<': '<', '>=': '>=', '<=': '<=',
#                             '=': '=', '!=': '!=', '<>': '<>',
#                             'LIKE': 'LIKE', 'NOT LIKE': 'NOT LIKE',
#                             'ILIKE': 'ILIKE', 'NOT ILIKE': 'NOT ILIKE',  # PostgreSQL特有
#                             'IN': 'IN', 'NOT IN': 'NOT IN',
#                             'BETWEEN': 'BETWEEN', 'NOT BETWEEN': 'NOT BETWEEN',
#                             'IS': 'IS', 'IS NOT': 'IS NOT',
#                             # MongoDB风格操作符
#                             '$gt': '>', '$lt': '<', '$gte': '>=', '$lte': '<=',
#                             '$eq': '=', '$ne': '!=',
#                             '$like': 'LIKE', '$nlike': 'NOT LIKE',
#                             '$ilike': 'ILIKE', '$nilike': 'NOT ILIKE',  # PostgreSQL特有
#                             '$in': 'IN', '$nin': 'NOT IN',
#                             '$between': 'BETWEEN', '$nbetween': 'NOT BETWEEN',
#                             '$is': 'IS', '$isNot': 'IS NOT',
#                             # PostgreSQL特有操作符
#                             '$contains': '@>', '$contained': '<@',
#                             '$overlap': '&&', '$regex': '~', '$iregex': '~*',
#                             '$jsonpath': '@?', '$jsonpathexists': '@?'
#                         }
#
#                         op = op_map.get(
#                             op_symbol if op_symbol.startswith('$') else op_symbol.upper()
#                         )
#                         if not op:
#                             raise ValueError(f"无效操作符: {op_symbol}")
#
#                         if op in ('BETWEEN', 'NOT BETWEEN'):
#                             if not isinstance(op_value, (list, tuple)) or len(op_value) != 2:
#                                 raise ValueError(f"{op} 需要两个值的列表")
#                             where_parts.append(f"{safe_col} {op} %s AND %s")
#                             params.extend(op_value)
#                         elif op in ('IN', 'NOT IN'):
#                             if not isinstance(op_value, (list, tuple)):
#                                 raise ValueError(f"{op} 需要列表或元组")
#                             if not op_value:  # 空列表处理
#                                 if op == 'IN':
#                                     where_parts.append("FALSE")  # PostgreSQL中的空IN列表总是假
#                                 else:  # NOT IN
#                                     where_parts.append("TRUE")  # 空NOT IN列表总是真
#                             else:
#                                 placeholders = ', '.join(['%s'] * len(op_value))
#                                 where_parts.append(f"{safe_col} {op} ({placeholders})")
#                                 params.extend(op_value)
#                         elif op in ('IS', 'IS NOT'):
#                             # IS NULL 和 IS NOT NULL 不需要参数
#                             where_parts.append(f"{safe_col} {op} NULL"
#                                                if op_value is None else f"{safe_col} {op} %s")
#                             if op_value is not None:
#                                 params.append(op_value)
#                         elif op in ('@>', '<@', '&&', '@?'):  # JSON和数组操作符
#                             where_parts.append(f"{safe_col} {op} %s")
#                             params.append(op_value)
#                         elif op in ('~', '~*'):  # 正则表达式操作符
#                             where_parts.append(f"{safe_col} {op} %s")
#                             params.append(op_value)
#                         else:
#                             where_parts.append(f"{safe_col} {op} %s")
#                             params.append(op_value)
#                 else:
#                     # 简单等值条件
#                     if value is None:
#                         where_parts.append(f"{safe_col} IS NULL")
#                     else:
#                         where_parts.append(f"{safe_col} = %s")
#                         params.append(value)
#
#         return (" AND ".join(where_parts), params) if where_parts else ("", [])
#
#     def build_select(self,
#                      tablename: str,
#                      fields: Optional[List[str]] = None,
#                      conditions: Optional[Dict] = None,
#                      order: Optional[Dict[str, bool]] = None,
#                      limit: Optional[int] = None,
#                      offset: Optional[int] = None,
#                      group_by: Optional[List[str]] = None,
#                      having: Optional[Dict] = None,
#                      **kwargs) -> Tuple[str, List]:
#         """
#         构建SELECT语句
#
#         Args:
#             tablename: 表名
#             fields: 字段列表
#             conditions: 查询条件
#             order: 排序条件 {字段: 是否升序}
#             limit: 限制记录数
#             offset: 跳过记录数
#             group_by: 分组字段列表
#             having: 分组后筛选条件
#             **kwargs: 其他参数
#
#         Returns:
#             (SQL语句, 参数列表)
#         """
#         # 处理表名和字段
#         schema = kwargs.get("schema", "public")
#         safe_table = f'"{schema}"."{tablename}"' if schema != "public" else f'"{tablename}"'
#
#         fields_str = "*"
#         if fields:
#             safe_fields = [self._escape_identifier(f) for f in fields]
#             fields_str = ", ".join(safe_fields)
#
#         # 构建基础查询
#         sql = f"SELECT {fields_str} FROM {safe_table}"
#         params = []
#
#         # 处理WITH查询（CTE）
#         with_queries = kwargs.get("with_queries", [])
#         if with_queries:
#             with_clauses = []
#             for with_name, with_query, with_params in with_queries:
#                 with_clauses.append(f"{with_name} AS ({with_query})")
#                 params.extend(with_params)
#
#             sql = f"WITH {', '.join(with_clauses)}\n{sql}"
#
#         # 处理连接
#         joins = kwargs.get("joins", [])
#         if joins:
#             join_clauses = []
#             for table, alias, join_type, on_clause, join_params in joins:
#                 safe_join_table = f'"{table}"'
#                 join_clauses.append(f"{join_type.value} {safe_join_table} AS {alias} ON {on_clause}")
#                 params.extend(join_params)
#
#             sql += f" {' '.join(join_clauses)}"
#
#         # 处理WHERE条件
#         where_clause, where_params = self._build_where_clause(conditions)
#         if where_clause:
#             sql += f" WHERE {where_clause}"
#             params.extend(where_params)
#
#         # 处理GROUP BY
#         if group_by:
#             group_by_fields = [self._escape_identifier(g) for g in group_by]
#             sql += f" GROUP BY {', '.join(group_by_fields)}"
#
#             # 处理HAVING
#             if having:
#                 having_clause, having_params = self._build_where_clause(having)
#                 if having_clause:
#                     sql += f" HAVING {having_clause}"
#                     params.extend(having_params)
#
#         # 处理排序
#         if order:
#             order_parts = []
#             for col, asc in order.items():
#                 direction = "ASC" if asc else "DESC"
#                 order_parts.append(f"{self._escape_identifier(col)} {direction}")
#             if order_parts:
#                 sql += f" ORDER BY {', '.join(order_parts)}"
#
#         # 处理分页
#         if limit is not None:
#             sql += f" LIMIT %s"
#             params.append(limit)
#
#         if offset is not None:
#             sql += f" OFFSET %s"
#             params.append(offset)
#
#         return sql, params
#
#     def build_insert(self,
#                      tablename: str,
#                      data: Union[Dict[str, Any], List[Dict[str, Any]]],
#                      **kwargs) -> Tuple[str, List]:
#         """
#         构建INSERT语句
#
#         Args:
#             tablename: 表名
#             data: 插入数据（单条或多条）
#             **kwargs: 其他参数
#
#         Returns:
#             (SQL语句, 参数列表)
#
#         Raises:
#             ValueError: 没有数据可插入时
#         """
#         # 处理表名
#         schema = kwargs.get("schema", "public")
#         safe_table = f'"{schema}"."{tablename}"' if schema != "public" else f'"{tablename}"'
#
#         # 处理单行或多行插入
#         is_batch = isinstance(data, list)
#         records = data if is_batch else [data]
#         if not records:
#             raise ValueError("没有数据可插入")
#
#         # 获取所有字段名
#         fields = list(records[0].keys())
#         safe_fields = [self._escape_identifier(field) for field in fields]
#         fields_str = ", ".join(safe_fields)
#
#         # 构建参数和值部分
#         params = []
#         value_clauses = []
#
#         if is_batch:
#             # 批量插入
#             for record in records:
#                 values = []
#                 for field in fields:
#                     values.append(record.get(field))
#                 params.extend(values)
#
#                 placeholders = ", ".join(["%s"] * len(fields))
#                 value_clauses.append(f"({placeholders})")
#
#             values_str = ", ".join(value_clauses)
#         else:
#             # 单行插入
#             for field in fields:
#                 params.append(records[0].get(field))
#
#             placeholders = ", ".join(["%s"] * len(fields))
#             values_str = f"({placeholders})"
#
#         # 构建SQL
#         sql = f"INSERT INTO {safe_table} ({fields_str}) VALUES {values_str}"
#
#         # 处理冲突解决策略（PostgreSQL的ON CONFLICT）
#         on_conflict = kwargs.get("on_conflict")
#         if on_conflict:
#             conflict_target = on_conflict.get("target")
#             conflict_action = on_conflict.get("action", "NOTHING")  # 默认为NOTHING
#
#             if conflict_target and isinstance(conflict_target, (list, tuple)):
#                 target_cols = ", ".join([self._escape_identifier(col) for col in conflict_target])
#                 sql += f" ON CONFLICT ({target_cols})"
#
#                 if conflict_action == "UPDATE":
#                     # 获取要更新的值
#                     update_fields = on_conflict.get("update_fields", fields)
#                     update_excluded = on_conflict.get("update_excluded", True)  # 默认使用EXCLUDED
#
#                     update_parts = []
#                     for field in update_fields:
#                         if field not in fields:
#                             continue  # 跳过不在fields中的字段
#
#                         safe_field = self._escape_identifier(field)
#                         if update_excluded:
#                             update_parts.append(f"{safe_field} = EXCLUDED.{safe_field}")
#                         else:
#                             # 使用参数更新
#                             update_parts.append(f"{safe_field} = %s")
#                             params.append(on_conflict.get("values", {}).get(field))
#
#                     if update_parts:
#                         sql += f" DO UPDATE SET {', '.join(update_parts)}"
#                     else:
#                         sql += " DO NOTHING"
#                 else:
#                     sql += " DO NOTHING"
#
#         # 处理返回值 (PostgreSQL支持RETURNING子句)
#         returning = kwargs.get("returning")
#         if returning:
#             if isinstance(returning, list):
#                 returning_fields = ", ".join([self._escape_identifier(f) for f in returning])
#                 sql += f" RETURNING {returning_fields}"
#             elif isinstance(returning, str):
#                 sql += f" RETURNING {self._escape_identifier(returning)}"
#             else:
#                 sql += " RETURNING id"  # 默认返回ID
#
#         return sql, params
#
#     def build_update(self,
#                      tablename: str,
#                      update_values: Dict[str, Any],
#                      conditions: Optional[Dict] = None,
#                      **kwargs) -> Tuple[str, List]:
#         """
#         构建UPDATE语句
#
#         Args:
#             tablename: 表名
#             update_values: 更新值
#             conditions: 更新条件
#             **kwargs: 其他参数
#
#         Returns:
#             (SQL语句, 参数列表)
#
#         Raises:
#             ValueError: 没有更新值时
#         """
#         if not update_values:
#             raise ValueError("没有要更新的数据")
#
#         # 处理表名
#         schema = kwargs.get("schema", "public")
#         safe_table = f'"{schema}"."{tablename}"' if schema != "public" else f'"{tablename}"'
#
#         # 构建SET子句
#         set_parts = []
#         params = []
#
#         for field, value in update_values.items():
#             safe_field = self._escape_identifier(field)
#             if value is None:
#                 set_parts.append(f"{safe_field} = NULL")
#             else:
#                 set_parts.append(f"{safe_field} = %s")
#                 params.append(value)
#
#         # 构建WHERE子句
#         where_clause, where_params = self._build_where_clause(conditions)
#
#         # 构建SQL
#         sql = f"UPDATE {safe_table} SET {', '.join(set_parts)}"
#
#         if where_clause:
#             sql += f" WHERE {where_clause}"
#             params.extend(where_params)
#
#         # 处理RETURNING子句
#         returning = kwargs.get("returning")
#         if returning:
#             if isinstance(returning, list):
#                 returning_fields = ", ".join([self._escape_identifier(f) for f in returning])
#                 sql += f" RETURNING {returning_fields}"
#             elif isinstance(returning, str):
#                 sql += f" RETURNING {self._escape_identifier(returning)}"
#
#         return sql, params
#
#     def build_delete(self,
#                      tablename: str,
#                      conditions: Optional[Dict] = None,
#                      **kwargs) -> Tuple[str, List]:
#         """
#         构建DELETE语句
#
#         Args:
#             tablename: 表名
#             conditions: 删除条件
#             **kwargs: 其他参数
#
#         Returns:
#             (SQL语句, 参数列表)
#         """
#         # 处理表名
#         schema = kwargs.get("schema", "public")
#         safe_table = f'"{schema}"."{tablename}"' if schema != "public" else f'"{tablename}"'
#
#         # 构建WHERE子句
#         where_clause, where_params = self._build_where_clause(conditions)
#
#         # 构建SQL
#         sql = f"DELETE FROM {safe_table}"
#         params = []
#
#         if where_clause:
#             sql += f" WHERE {where_clause}"
#             params.extend(where_params)
#
#         # 处理RETURNING子句
#         returning = kwargs.get("returning")
#         if returning:
#             if isinstance(returning, list):
#                 returning_fields = ", ".join([self._escape_identifier(f) for f in returning])
#                 sql += f" RETURNING {returning_fields}"
#             elif isinstance(returning, str):
#                 sql += f" RETURNING {self._escape_identifier(returning)}"
#
#         return sql, params
#
#     def build_create_table(self,
#                            tablename: str,
#                            schema: Dict[str, Any],
#                            primary_key: Optional[List[str]] = None,
#                            if_not_exists: bool = True,
#                            **kwargs) -> list[str]:
#         """
#         构建CREATE TABLE语句
#
#         Args:
#             tablename: 表名
#             schema: 表结构定义
#             primary_key: 主键字段列表
#             if_not_exists: 是否添加IF NOT EXISTS选项
#             **kwargs: 其他参数
#
#         Returns:
#             SQL语句(PostgreSQL特有的返回多条语句的功能)
#         """
#         # 验证表名
#         if not re.match(r'^[a-zA-Z0-9_]+$', tablename):
#             raise ValueError("表名只能包含字母、数字和下划线")
#
#         # 处理架构
#         schema_name = kwargs.get("schema", "public")
#         table_with_schema = f"{schema_name}.{tablename}" if schema_name != "public" else tablename
#         safe_table = f'"{table_with_schema}"'
#
#         # 处理列定义
#         column_defs = []
#         serial_columns = []  # 记录需要创建序列的列
#
#         for column, details in schema.items():
#             col_def = None
#
#             if isinstance(details, str):
#                 # 简单格式: {column: "INTEGER"}
#                 if details.upper() == "SERIAL" or details.upper() == "BIGSERIAL":
#                     # 自增列
#                     serial_type = "INT" if details.upper() == "SERIAL" else "BIGINT"
#                     col_def = f'"{column}" {serial_type}'
#                     serial_columns.append((column, details.upper()))
#                 else:
#                     col_def = f'"{column}" {details}'
#             elif isinstance(details, dict):
#                 # 详细格式: {column: {type: "INTEGER", constraint: "NOT NULL"}}
#                 col_type = details.get("type", "VARCHAR(255)")
#                 # 处理自增列
#                 if col_type.upper() == "SERIAL" or col_type.upper() == "BIGSERIAL":
#                     serial_type = "INT" if col_type.upper() == "SERIAL" else "BIGINT"
#                     col_def = f'"{column}" {serial_type}'
#                     serial_columns.append((column, col_type.upper()))
#                 else:
#                     # 转换通用SQL类型到PostgreSQL类型
#                     if col_type.upper() in PG_DATA_TYPES:
#                         col_type = PG_DATA_TYPES[col_type.upper()]
#
#                     constraint = details.get("constraint", "")
#                     col_def = f'"{column}" {col_type} {constraint}'.strip()
#
#             if col_def:
#                 column_defs.append(col_def)
#
#         # 处理主键
#         if primary_key:
#             safe_pk = [f'"{pk}"' for pk in primary_key]
#             pk_name = f"pk_{tablename}"
#             column_defs.append(f"CONSTRAINT {pk_name} PRIMARY KEY ({', '.join(safe_pk)})")
#
#         # 处理唯一约束
#         unique_constraints = kwargs.get("unique_constraints", [])
#         for unique_def in unique_constraints:
#             if isinstance(unique_def, list):
#                 # 列名列表
#                 unique_cols = [f'"{col}"' for col in unique_def]
#                 constraint_name = f"uq_{tablename}_{'_'.join(unique_def)}"
#                 column_defs.append(f"CONSTRAINT {constraint_name} UNIQUE ({', '.join(unique_cols)})")
#             elif isinstance(unique_def, dict):
#                 # 详细定义
#                 constraint_name = unique_def.get("name", f"uq_{tablename}")
#                 unique_cols = [f'"{col}"' for col in unique_def.get("columns", [])]
#                 if unique_cols:
#                     column_defs.append(f"CONSTRAINT {constraint_name} UNIQUE ({', '.join(unique_cols)})")
#
#         # 构建创建表语句
#         if_not_exists_clause = "IF NOT EXISTS " if if_not_exists else ""
#         create_table_sql = f"CREATE TABLE {if_not_exists_clause}{safe_table} (\n  {',  '.join(column_defs)}\n)"
#
#         # 处理表选项
#         table_options = []
#
#         if kwargs.get("unlogged", False):
#             create_table_sql = create_table_sql.replace("CREATE TABLE", "CREATE UNLOGGED TABLE")
#
#         if kwargs.get("temp", False) or kwargs.get("temporary", False):
#             create_table_sql = create_table_sql.replace("CREATE TABLE", "CREATE TEMPORARY TABLE")
#
#         # 添加Storage参数
#         with_options = []
#
#         # FILLFACTOR
#         if "fillfactor" in kwargs:
#             with_options.append(f"fillfactor = {kwargs['fillfactor']}")
#
#         # TOAST配置
#         toast_options = kwargs.get("toast_options", {})
#         for opt, val in toast_options.items():
#             with_options.append(f"{opt} = {val}")
#
#         if with_options:
#             table_options.append(f"WITH ({', '.join(with_options)})")
#
#         # 表空间
#         if "tablespace" in kwargs:
#             table_options.append(f"TABLESPACE {kwargs['tablespace']}")
#
#         # 集成表选项
#         if table_options:
#             create_table_sql += " " + " ".join(table_options)
#
#         # 构建序列和默认值SQL
#         extra_sqls = []
#
#         for column, serial_type in serial_columns:
#             seq_name = f"{tablename}_{column}_seq"
#
#             # 创建序列
#             seq_sql = f"""
#             CREATE SEQUENCE IF NOT EXISTS "{schema_name}"."{seq_name}"
#             """
#
#             # 设置默认值
#             alter_sql = f"""
#             ALTER TABLE {safe_table} ALTER COLUMN "{column}"
#             SET DEFAULT nextval('"{schema_name}"."{seq_name}"')
#             """
#
#             extra_sqls.append(seq_sql)
#             extra_sqls.append(alter_sql)
#
#         if extra_sqls:
#             return [create_table_sql] + extra_sqls
#
#         return [create_table_sql]
#
#     def build_drop_table(self,
#                          tablename: str,
#                          if_exists: bool = True) -> str:
#         """
#         构建DROP TABLE语句
#
#         Args:
#             tablename: 表名
#             if_exists: 是否添加IF EXISTS子句
#
#         Returns:
#             SQL语句
#         """
#         safe_table = f'"{tablename}"'
#
#         # PostgreSQL支持IF EXISTS
#         if_exists_clause = "IF EXISTS " if if_exists else ""
#         return f"DROP TABLE {if_exists_clause}{safe_table}"
#
#     def build_join(self,
#                    main_table: str,
#                    joins: List[Tuple[str, str, JoinType, Dict[str, str]]],
#                    fields: Optional[Dict[str, List[str]]] = None,
#                    conditions: Optional[Dict] = None,
#                    order: Optional[Dict[str, bool]] = None,
#                    limit: Optional[int] = None,
#                    offset: Optional[int] = None,
#                    **kwargs) -> Tuple[str, List]:
#         """
#         构建连接查询语句
#
#         Args:
#             main_table: 主表
#             joins: 连接定义列表
#             fields: 查询字段
#             conditions: 查询条件
#             order: 排序条件
#             limit: 限制记录数
#             offset: 跳过记录数
#             **kwargs: 其他参数
#
#         Returns:
#             (SQL语句, 参数列表)
#         """
#         self.reset_param_index()
#
#         # 处理主表
#         schema = kwargs.get("schema", "public")
#         safe_main_table = f'"{schema}"."{main_table}"' if schema != "public" else f'"{main_table}"'
#         main_alias = kwargs.get("main_alias", "t0")
#         from_clause = f"{safe_main_table} AS {main_alias}"
#
#         # 处理连接
#         join_clauses = []
#         params = []
#
#         for i, (table, alias, join_type, join_conds) in enumerate(joins, 1):
#             safe_table = f'"{table}"'
#             join_conditions = []
#
#             # 构建连接条件
#             for main_col, join_col in join_conds.items():
#                 main_table_prefix = kwargs.get("main_alias", "t0")
#                 join_conditions.append(
#                     f"{main_table_prefix}.{self._escape_identifier(main_col)} = {alias}.{self._escape_identifier(join_col)}"
#                 )
#
#             join_clause = f"{join_type.value} {safe_table} AS {alias} ON ({' AND '.join(join_conditions)})"
#             join_clauses.append(join_clause)
#
#         # 处理字段选择
#         select_fields = []
#         if fields:
#             for table_alias, cols in fields.items():
#                 for col in cols:
#                     select_fields.append(f"{table_alias}.{self._escape_identifier(col)} AS {table_alias}_{col}")
#         else:
#             # 默认选择所有字段
#             select_fields.append(f"{main_alias}.*")
#             for _, alias, _, _ in joins:
#                 select_fields.append(f"{alias}.*")
#
#         # 构建基础查询
#         sql = f"SELECT {', '.join(select_fields)} FROM {from_clause} {' '.join(join_clauses)}"
#
#         # 处理WHERE条件
#         if conditions:
#             where_clause, where_params = self._build_where_clause(conditions)
#             if where_clause:
#                 sql += f" WHERE {where_clause}"
#                 params.extend(where_params)
#
#         # 处理排序
#         if order:
#             order_parts = []
#             for col, asc in order.items():
#                 direction = "ASC" if asc else "DESC"
#                 # 检查是否包含表别名
#                 if "." in col:
#                     order_parts.append(f"{col} {direction}")
#                 else:
#                     # 假设是主表字段
#                     order_parts.append(f"{main_alias}.{self._escape_identifier(col)} {direction}")
#
#             if order_parts:
#                 sql += f" ORDER BY {', '.join(order_parts)}"
#
#         # 处理分页
#         if limit is not None:
#             sql += f" LIMIT %s"
#             params.append(limit)
#
#         if offset is not None:
#             sql += f" OFFSET %s"
#             params.append(offset)
#
#         return sql, params
#
#
# class PostgreSQLConnectionPool(ConnectionPool):
#     """PostgreSQL连接池实现，支持线程安全的连接管理"""
#
#     def __init__(self, adapter: PostgreSQLAdapter, min_conn: int = 1, max_conn: int = 10,
#                  logger: Optional[Logger] = None):
#         """
#         初始化连接池
#
#         Args:
#             adapter: PostgreSQL适配器
#             min_conn: 最小连接数
#             max_conn: 最大连接数
#             logger: 日志记录器
#         """
#         self.adapter = adapter
#         self.min_conn = min_conn
#         self.max_conn = max_conn
#         self.logger = logger
#
#         # 创建连接池
#         try:
#             # PostgreSQL 有内置的连接池
#             self.pool = psycopg2.pool.ThreadedConnectionPool(
#                 minconn=min_conn,
#                 maxconn=max_conn,
#                 **adapter.connection_params
#             )
#
#             # 配置连接工厂
#             kwargs = {"cursor_factory": psycopg2.extras.RealDictCursor}
#             self.pool.kwargs.update(kwargs)
#
#             if self.logger:
#                 self.logger.debug(f"PostgreSQL连接池已创建: 最小连接{min_conn}, 最大连接{max_conn}")
#         except Exception as e:
#             if self.logger:
#                 self.logger.error(f"创建连接池失败: {e}")
#             raise RuntimeError(f"无法创建连接池: {e}") from None
#
#     def get_connection(self) -> psycopg2._ext.connection:
#         """
#         从连接池获取连接
#
#         Returns:
#             数据库连接
#
#         Raises:
#             RuntimeError: 无法获取连接时
#         """
#         try:
#             conn = self.pool.getconn()
#
#             # 重置连接状态
#             conn.set_session(autocommit=True)
#             conn.cursor_factory = psycopg2.extras.RealDictCursor
#
#             if self.logger:
#                 self.logger.debug("从连接池获取连接")
#             return conn
#         except psycopg2.pool.PoolError as e:
#             if self.logger:
#                 self.logger.error(f"从连接池获取连接失败: {e}")
#             raise RuntimeError(f"无法获取数据库连接: {e}") from e
#
#     def release_connection(self, connection: psycopg2._ext.connection):
#         """
#         释放连接回池
#
#         Args:
#             connection: 要释放的连接
#         """
#         try:
#             # 检查连接是否有效
#             if connection and not connection.closed:
#                 # 回滚任何未提交的事务
#                 try:
#                     if connection.status != psycopg2.extensions.STATUS_READY:
#                         connection.rollback()
#                 except:
#                     pass
#
#                 # 将连接恢复到自动提交模式
#                 try:
#                     connection.autocommit = True
#                 except:
#                     pass
#
#                 # 返回给连接池
#                 self.pool.putconn(connection)
#                 if self.logger:
#                     self.logger.debug("连接已返回到连接池")
#         except Exception as e:
#             if self.logger:
#                 self.logger.error(f"释放连接失败: {e}")
#
#     def close_all(self):
#         """关闭所有连接并清理连接池"""
#         if self.pool:
#             try:
#                 self.pool.closeall()
#                 if self.logger:
#                     self.logger.info("关闭所有数据库连接")
#             except Exception as e:
#                 if self.logger:
#                     self.logger.error(f"关闭所有连接失败: {e}")
#
#
# class PostgreSQLop(SQLutilop):
#     """PostgreSQL数据库操作工具类，继承自SQLutilop抽象基类"""
#
#     def __init__(self, host: str, port: int, dbname: str, user: str, password: str,
#                  schema: str = "public", logger: Logger = None,
#                  sslmode: str = "prefer", autoreconnect: bool = True, reconnect_retries: int = 3,
#                  min_pool_size: int = 1, max_pool_size: int = 10):
#         """
#         初始化PostgreSQL操作工具
#
#         Args:
#             host: 服务器地址
#             port: 服务器端口
#             dbname: 数据库名
#             user: 用户名
#             password: 密码
#             schema: 默认模式
#             logger: 日志记录器
#             sslmode: SSL连接模式
#             autoreconnect: 是否自动重连
#             reconnect_retries: 重连尝试次数
#             min_pool_size: 连接池最小连接数
#             max_pool_size: 连接池最大连接数
#         """
#         # 初始化父类
#         super().__init__(logger)
#
#         self.host = host
#         self.port = port
#         self.dbname = dbname
#         self.user = user
#         self.password = password
#         self.schema = schema
#         self.autoreconnect = autoreconnect
#         self.reconnect_retries = reconnect_retries
#
#         # 创建适配器和构建器
#         self.adapter = PostgreSQLAdapter(host, port, dbname, user, password, sslmode, self.logger)
#         self.query_builder = PostgreSQLQueryBuilder(self.logger)
#         self.connection_pool = PostgreSQLConnectionPool(
#             self.adapter,
#             min_conn=min_pool_size,
#             max_conn=max_pool_size,
#             logger=self.logger
#         )
#
#         self.__connection = None
#         self.__in_transaction = False
#         self.__selected_table = None
#
#         self.logger.info(
#             f'PostgreSQL工具初始化完成 host: {host}, port: {port}, db: {dbname}, user: {user}, schema: {schema}')
#
#     def _create_default_logger(self) -> Logger:
#         """
#         创建默认日志记录器
#
#         Returns:
#             日志记录器
#         """
#         return set_log("hzgt.postgre", os.path.join("logs", "postgre.log"))
#
#     def connect(self):
#         """
#         建立数据库连接
#
#         Raises:
#             RuntimeError: 连接失败时
#         """
#         for attempt in range(1, self.reconnect_retries + 1):
#             try:
#                 if self.__connection is not None:
#                     self.close()
#                 self.__connection = self.connection_pool.get_connection()
#                 # 确认连接
#                 cursor = self.__connection.cursor()
#                 cursor.execute("SELECT 1")
#                 cursor.close()
#
#                 self.logger.info(f"PostgreSQL连接成功，数据库: {self.dbname}")
#                 return
#             except Exception as e:
#                 self.logger.error(f"连接失败(尝试 {attempt}/{self.reconnect_retries}): {e}")
#                 if attempt == self.reconnect_retries:
#                     raise RuntimeError(f"数据库连接失败, 重试{self.reconnect_retries}次后仍不可用: {e}") from e
#                 time.sleep(1)  # 等待后重试
#
#     def _ensure_connection(self):
#         """
#         确保数据库连接有效
#
#         Raises:
#             RuntimeError: 无法建立连接时
#         """
#         if self.__connection is None:
#             self.connect()
#             return
#
#         try:
#             # 检查连接是否有效
#             cursor = self.__connection.cursor()
#             cursor.execute("SELECT 1")
#             cursor.close()
#         except:
#             if self.autoreconnect:
#                 self.logger.warning("连接已断开，尝试重新连接")
#                 self.connect()
#             else:
#                 raise RuntimeError("数据库连接已断开，且未启用自动重连")
#
#     def close(self):
#         """关闭数据库连接，归还连接到连接池"""
#         if self.__connection:
#             try:
#                 if self.__in_transaction:
#                     self.logger.warning("关闭连接时有未提交的事务，执行回滚")
#                     self.rollback()
#                 self.connection_pool.release_connection(self.__connection)
#                 self.logger.debug("PostgreSQL连接已归还到连接池")
#             finally:
#                 self.__connection = None
#
#     def commit(self):
#         """提交事务"""
#         if self.__connection and self.__in_transaction:
#             self.__connection.commit()
#             self.__in_transaction = False
#             self.logger.debug("事务已提交")
#
#     def rollback(self):
#         """回滚事务"""
#         if self.__connection and self.__in_transaction:
#             self.__connection.rollback()
#             self.__in_transaction = False
#             self.logger.debug("事务已回滚")
#
#     def _begin_transaction(self):
#         """开始事务"""
#         self._ensure_connection()
#         if not self.__in_transaction:
#             # 禁用自动提交以开始事务
#             self.__connection.autocommit = False
#             self.__in_transaction = True
#             self.logger.debug("开始新事务")
#
#     def _end_transaction(self, commit: bool = True):
#         """
#         结束事务
#
#         Args:
#             commit: 是否提交，False为回滚
#         """
#         if commit:
#             self.commit()
#         else:
#             self.rollback()
#         # 恢复自动提交模式
#         if self.__connection:
#             self.__connection.autocommit = True
#
#     def execute(self, sql: str, args: Optional[Union[tuple, dict, list]] = None) -> Any:
#         """
#         执行SQL语句
#
#         Args:
#             sql: SQL语句
#             args: 参数
#
#         Returns:
#             执行结果
#
#         Raises:
#             Exception: 执行失败时
#         """
#         for attempt in range(2):  # 最多重试1次
#             try:
#                 self._ensure_connection()
#                 cursor = self.__connection.cursor()
#                 try:
#                     cursor.execute(sql, args)
#
#                     # 如果是查询，获取结果集
#                     if cursor.description:
#                         results = cursor.fetchall()
#                         return list(results)  # 已是字典列表格式
#                     else:
#                         # 非查询操作
#                         if not self.__in_transaction and sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
#                             self.__connection.commit()
#                         return cursor.rowcount
#                 finally:
#                     cursor.close()
#             except psycopg2.OperationalError as e:
#                 if attempt == 0 and self.autoreconnect:
#                     self.logger.warning(f"执行SQL失败, 尝试重新连接: {e}")
#                     self.connect()
#                     continue
#                 if not self.__in_transaction:
#                     self.__connection.rollback()
#                 self.logger.error(f"执行SQL失败: {sql} | 参数: {args}")
#                 raise
#             except Exception as e:
#                 if not self.__in_transaction:
#                     self.__connection.rollback()
#                 self.logger.error(f"执行SQL时发生错误: {e}")
#                 raise
#
#     def executemany(self, sql: str, args_list: List[Union[tuple, dict]]) -> Any:
#         """
#         批量执行SQL语句
#
#         Args:
#             sql: SQL语句模板
#             args_list: 参数列表
#
#         Returns:
#             执行结果
#         """
#         if not args_list:
#             return None
#
#         for attempt in range(2):  # 最多重试1次
#             try:
#                 self._ensure_connection()
#                 cursor = self.__connection.cursor()
#                 try:
#                     cursor.executemany(sql, args_list)
#
#                     if not self.__in_transaction:
#                         self.__connection.commit()
#
#                     return cursor.rowcount
#                 finally:
#                     cursor.close()
#             except psycopg2.OperationalError as e:
#                 if attempt == 0 and self.autoreconnect:
#                     self.logger.warning(f"执行批量SQL失败, 尝试重新连接: {e}")
#                     self.connect()
#                     continue
#                 if not self.__in_transaction:
#                     self.__connection.rollback()
#                 self.logger.error(f"执行批量SQL失败: {sql}")
#                 raise
#             except Exception as e:
#                 if not self.__in_transaction:
#                     self.__connection.rollback()
#                 self.logger.error(f"执行批量SQL时发生错误: {e}")
#                 raise
#
#     def query(self, sql: str, args: Optional[Union[tuple, dict, list]] = None) -> List[Dict[str, Any]]:
#         """
#         执行查询并返回结果集
#
#         Args:
#             sql: SQL查询语句
#             args: 查询参数
#
#         Returns:
#             查询结果列表
#         """
#         self._ensure_connection()
#         cursor = None
#         try:
#             cursor = self.__connection.cursor()
#             cursor.execute(sql, args)
#
#             # psycopg2 RealDictCursor 已经将结果转为字典格式
#             results = cursor.fetchall()
#             return list(results)
#         except Exception as e:
#             self.logger.error(f"执行查询失败: {sql} | {e}")
#             raise
#         finally:
#             if cursor:
#                 cursor.close()
#
#     def query_one(self, sql: str, args: Optional[Union[tuple, dict, list]] = None) -> Optional[Dict[str, Any]]:
#         """
#         查询单条记录
#
#         Args:
#             sql: SQL查询语句
#             args: 查询参数
#
#         Returns:
#             单条记录字典
#         """
#         self._ensure_connection()
#         cursor = None
#         try:
#             cursor = self.__connection.cursor()
#             cursor.execute(sql, args)
#             result = cursor.fetchone()
#             return dict(result) if result else None
#         except Exception as e:
#             self.logger.error(f"执行单条查询失败: {sql} | {e}")
#             raise
#         finally:
#             if cursor:
#                 cursor.close()
#
#     def table_exists(self, tablename: str) -> bool:
#         """
#         检查表是否存在
#
#         Args:
#             tablename: 表名
#
#         Returns:
#             表是否存在
#         """
#         schema = self.schema
#         sql = """
#         SELECT EXISTS(
#             SELECT 1 FROM information_schema.tables
#             WHERE table_schema = %s AND table_name = %s
#         ) AS exists
#         """
#         result = self.query_one(sql, (schema, tablename))
#         return result and result["exists"]
#
#     def get_columns(self, tablename: str) -> List[str]:
#         """
#         获取表的列名列表
#
#         Args:
#             tablename: 表名
#
#         Returns:
#             列名列表
#         """
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         schema = self.schema
#         sql = """
#         SELECT column_name
#         FROM information_schema.columns
#         WHERE table_schema = %s AND table_name = %s
#         ORDER BY ordinal_position
#         """
#         result = self.query(sql, (schema, tablename))
#         return [row["column_name"] for row in result]
#
#     def create_table(self,
#                      tablename: str,
#                      schema: Union[Dict[str, str], Dict[str, Dict]],
#                      primary_key: Optional[List[str]] = None,
#                      if_not_exists: bool = True,
#                      **kwargs) -> bool:
#         """
#         创建表
#
#         Args:
#             tablename: 表名
#             schema: 表结构
#             primary_key: 主键列表
#             if_not_exists: 是否在表不存在时才创建
#             **kwargs: 其他参数
#
#         Returns:
#             是否成功创建
#         """
#         # 检查表名有效性
#         self._validate_table_name(tablename)
#
#         # 添加当前schema
#         kwargs["schema"] = kwargs.get("schema", self.schema)
#
#         # 检查表是否已存在
#         if if_not_exists and self.table_exists(tablename):
#             self.logger.info(f"表 {tablename} 已存在")
#             if kwargs.get("bool_autoselect", True):
#                 self.select_table(tablename)
#             return True
#
#         # 处理自增ID
#         bool_id = kwargs.get("bool_id", False)
#
#         if bool_id:
#             if 'id' in schema:
#                 # 用户定义了id列，确认类型
#                 if isinstance(schema['id'], str):
#                     schema['id'] = "SERIAL"
#                 else:
#                     schema['id'] = {"type": "SERIAL", "constraint": schema['id'].get("constraint", "")}
#                 # 确保ID在主键中
#                 if not primary_key:
#                     primary_key = ['id']
#                 elif 'id' not in primary_key:
#                     primary_key.append('id')
#             else:
#                 # 添加id列
#                 if isinstance(schema, dict):
#                     schema = {'id': "SERIAL"} | schema
#                 else:
#                     schema['id'] = "SERIAL"
#                 if not primary_key:
#                     primary_key = ['id']
#
#         # 调用查询构建器生成建表SQL
#         result = self.query_builder.build_create_table(
#             tablename=tablename,
#             schema=schema,
#             primary_key=primary_key,
#             if_not_exists=if_not_exists,
#             **kwargs
#         )
#
#         # 执行SQL
#         success = False
#         try:
#             with self.transaction():
#                 # 执行所有SQL语句（可能有多个，例如创建序列等）
#                 for sql in result:
#                     self.execute(sql)
#
#                 success = True
#         except Exception as e:
#             self.logger.error(f"创建表 {tablename} 失败: {e}")
#             success = False
#             raise
#
#         if success:
#             self.logger.info(f"创建表 {tablename} 成功")
#             if kwargs.get("bool_autoselect", True):
#                 self.select_table(tablename)
#
#         return success
#
#     def drop_table(self, tablename: str, if_exists: bool = True) -> bool:
#         """
#         删除表
#
#         Args:
#             tablename: 表名
#             if_exists: 是否在表存在时才删除
#
#         Returns:
#             是否成功删除
#         """
#         if not tablename:
#             tablename = self.__selected_table
#
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         # 获取删除SQL
#         sql = self.query_builder.build_drop_table(tablename, if_exists)
#
#         # 执行删除
#         try:
#             self.execute(sql)
#             self.logger.info(f"删除表 {tablename} 成功")
#
#             # 如果是当前选择的表，清除选择
#             if tablename == self.__selected_table:
#                 self.__selected_table = None
#
#             return True
#         except Exception as e:
#             self.logger.error(f"删除表 {tablename} 失败: {e}")
#             return False
#
#     def select_table(self, tablename: str):
#         """
#         选择表
#
#         Args:
#             tablename: 表名
#         """
#         self.__selected_table = tablename
#         if self.__selected_table:
#             self.logger.debug(f"已记录选择表: {self.__selected_table}")
#
#     def insert(self,
#                tablename: str,
#                record: Union[Dict[str, Any], List[Dict[str, Any]]],
#                return_id: bool = False,
#                **kwargs) -> Union[int, List[int], None]:
#         """
#         插入数据
#
#         Args:
#             tablename: 表名
#             record: 要插入的记录或记录列表
#             return_id: 是否返回插入ID
#             **kwargs: 其他参数
#
#         Returns:
#             插入ID或影响行数
#         """
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         if not record:
#             self.logger.error("插入数据失败: record 参数不能为空")
#             raise ValueError("record 参数不能为空")
#
#         # 添加schema
#         kwargs["schema"] = kwargs.get("schema", self.schema)
#
#         # 添加RETURNING子句
#         if return_id:
#             kwargs["returning"] = kwargs.get("returning", "id")
#
#         # 构建插入SQL
#         is_batch = isinstance(record, list)
#         sql, params = self.query_builder.build_insert(
#             tablename=tablename,
#             data=record,
#             **kwargs
#         )
#
#         # 执行SQL
#         try:
#             self._ensure_connection()
#             cursor = self.__connection.cursor()
#
#             cursor.execute(sql, params)
#
#             # 处理返回值
#             if return_id and "returning" in kwargs:
#                 if is_batch:
#                     # 批量插入时返回多个ID
#                     ids = [row[0] for row in cursor.fetchall()]
#                     if not self.__in_transaction:
#                         self.__connection.commit()
#                     self.logger.info(f"成功批量插入数据到表 {tablename}，返回ID: {ids}")
#                     return ids
#                 else:
#                     # 单条插入返回单个ID
#                     result = cursor.fetchone()
#                     if result:
#                         id_value = result[0]
#                         if not self.__in_transaction:
#                             self.__connection.commit()
#                         self.logger.info(f"成功插入数据到表 {tablename}，返回ID: {id_value}")
#                         return id_value
#
#             # 无返回值或返回影响行数
#             affected_rows = cursor.rowcount
#             if not self.__in_transaction:
#                 self.__connection.commit()
#
#             msg = "批量" if is_batch else ""
#             self.logger.info(f"成功{msg}插入数据到表 {tablename}，影响行数: {affected_rows}")
#             return affected_rows
#
#         except Exception as e:
#             if not self.__in_transaction:
#                 try:
#                     self.__connection.rollback()
#                 except:
#                     pass
#             self.logger.error(f"插入数据失败: {e}")
#             raise
#
#     def select(self,
#                tablename: str,
#                conditions: Optional[Dict] = None,
#                order: Optional[Dict[str, bool]] = None,
#                fields: Optional[List[str]] = None,
#                limit: Optional[int] = None,
#                offset: Optional[int] = None,
#                group_by: Optional[List[str]] = None,
#                having: Optional[Dict] = None,
#                **kwargs) -> List[Dict[str, Any]]:
#         """
#         查询数据
#
#         Args:
#             tablename: 表名
#             conditions: 查询条件
#             order: 排序
#             fields: 字段列表
#             limit: 限制数量
#             offset: 偏移量
#             group_by: 分组字段
#             having: 分组后筛选
#             **kwargs: 其他参数
#
#         Returns:
#             查询结果
#         """
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         # 添加schema
#         kwargs["schema"] = kwargs.get("schema", self.schema)
#
#         # 构建查询SQL
#         sql, params = self.query_builder.build_select(
#             tablename=tablename,
#             fields=fields,
#             conditions=conditions,
#             order=order,
#             limit=limit,
#             offset=offset,
#             group_by=group_by,
#             having=having,
#             **kwargs
#         )
#
#         # 执行查询
#         results = self.query(sql, params)
#
#         # 是否以字典形式返回
#         if kwargs.get("bool_dict", False):
#             result_dict = {}
#
#             # 如果有结果
#             if results:
#                 # 初始化字典，为每个列创建一个空列表
#                 for key in results[0].keys():
#                     result_dict[key] = []
#
#                 # 填充每一列的值
#                 for row in results:
#                     for key, value in row.items():
#                         result_dict[key].append(value)
#
#             return result_dict
#
#         # 返回行记录列表
#         return results
#
#     def update(self,
#                tablename: str,
#                update_values: Dict[str, Any],
#                conditions: Optional[Dict] = None,
#                **kwargs) -> int:
#         """
#         更新数据
#
#         Args:
#             tablename: 表名
#             update_values: 要更新的值
#             conditions: 更新条件
#             **kwargs: 其他参数
#
#         Returns:
#             更新的行数
#         """
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         if not update_values:
#             raise ValueError("update_values 不能为空")
#
#         # 添加schema
#         kwargs["schema"] = kwargs.get("schema", self.schema)
#
#         # 构建更新SQL
#         sql, params = self.query_builder.build_update(
#             tablename=tablename,
#             update_values=update_values,
#             conditions=conditions,
#             **kwargs
#         )
#
#         # 执行更新
#         try:
#             self._ensure_connection()
#             cursor = self.__connection.cursor()
#             cursor.execute(sql, params)
#             affected_rows = cursor.rowcount
#
#             # 处理RETURNING子句
#             returning = kwargs.get("returning")
#             if returning:
#                 result = cursor.fetchall()
#                 # 如果没有提交事务，则提交
#                 if not self.__in_transaction:
#                     self.__connection.commit()
#                 self.logger.info(f"更新表 {tablename} 成功，受影响行数: {affected_rows}，返回值: {result}")
#                 return result
#
#             # 常规更新，返回影响行数
#             if not self.__in_transaction:
#                 self.__connection.commit()
#             self.logger.info(f"更新表 {tablename} 成功，受影响行数: {affected_rows}")
#             return affected_rows
#         except Exception as e:
#             if not self.__in_transaction:
#                 try:
#                     self.__connection.rollback()
#                 except:
#                     pass
#             self.logger.error(f"更新数据失败: {e}")
#             raise
#
#     def delete(self,
#                tablename: str,
#                conditions: Optional[Dict] = None,
#                **kwargs) -> int:
#         """
#         删除数据
#
#         Args:
#             tablename: 表名
#             conditions: 删除条件
#             **kwargs: 其他参数
#
#         Returns:
#             删除的行数
#         """
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         # 检查危险操作
#         if not conditions:
#             self.logger.warning("警告: 正在执行全表删除操作!")
#
#         # 添加schema
#         kwargs["schema"] = kwargs.get("schema", self.schema)
#
#         # 构建删除SQL
#         sql, params = self.query_builder.build_delete(
#             tablename=tablename,
#             conditions=conditions,
#             **kwargs
#         )
#
#         # 执行删除
#         try:
#             self._ensure_connection()
#             cursor = self.__connection.cursor()
#             cursor.execute(sql, params)
#             affected_rows = cursor.rowcount
#
#             # 处理RETURNING子句
#             returning = kwargs.get("returning")
#             if returning:
#                 result = cursor.fetchall()
#                 # 如果没有提交事务，则提交
#                 if not self.__in_transaction:
#                     self.__connection.commit()
#                 self.logger.info(f"从表 {tablename} 删除数据成功，受影响行数: {affected_rows}，返回值: {result}")
#                 return result
#
#             # 常规删除，返回影响行数
#             if not self.__in_transaction:
#                 self.__connection.commit()
#             self.logger.info(f"从表 {tablename} 删除数据成功，受影响行数: {affected_rows}")
#             return affected_rows
#         except Exception as e:
#             if not self.__in_transaction:
#                 try:
#                     self.__connection.rollback()
#                 except:
#                     pass
#             self.logger.error(f"删除数据失败: {e}")
#             raise
#
#     def join(self,
#              main_table: str,
#              joins: List[Tuple[str, str, JoinType, Dict[str, str]]],
#              conditions: Optional[Dict] = None,
#              fields: Optional[Dict[str, List[str]]] = None,
#              order: Optional[Dict[str, bool]] = None,
#              limit: Optional[int] = None,
#              offset: Optional[int] = None,
#              **kwargs) -> List[Dict[str, Any]]:
#         """
#         执行连接查询
#
#         Args:
#             main_table: 主表
#             joins: 连接表定义
#             conditions: 查询条件
#             fields: 字段定义
#             order: 排序条件
#             limit: 限制数量
#             offset: 偏移量
#             **kwargs: 其他参数
#
#         Returns:
#             查询结果
#         """
#         # 添加schema
#         kwargs["schema"] = kwargs.get("schema", self.schema)
#
#         # 构建连接查询SQL
#         sql, params = self.query_builder.build_join(
#             main_table=main_table,
#             joins=joins,
#             fields=fields,
#             conditions=conditions,
#             order=order,
#             limit=limit,
#             offset=offset,
#             **kwargs
#         )
#
#         # 执行查询
#         return self.query(sql, params)
#
#     def _escape_identifier(self, identifier: str) -> str:
#         """
#         转义标识符
#
#         Args:
#             identifier: 标识符
#
#         Returns:
#             转义后的标识符
#         """
#         return self.query_builder._escape_identifier(identifier)
#
#     # ---- PostgreSQL特有功能 ----
#
#     def execute_script(self, script: str):
#         """
#         执行SQL脚本
#
#         Args:
#             script: SQL脚本内容
#
#         Returns:
#             最后一个语句的执行结果
#         """
#         self._ensure_connection()
#
#         # 分割脚本为单独的语句
#         statements = []
#         current_stmt = []
#         in_function = False
#         function_delimiter = '$BODY$'
#
#         for line in script.split('\n'):
#             line = line.strip()
#             if not line or line.startswith('--'):  # 忽略空行和注释
#                 continue
#
#             if 'CREATE OR REPLACE FUNCTION' in line.upper() or 'CREATE FUNCTION' in line.upper():
#                 # 开始函数定义
#                 in_function = True
#                 current_stmt = [line]
#
#                 # 寻找自定义分隔符
#                 if '$BODY$' in line:
#                     function_delimiter = '$BODY$'
#                 elif '$$' in line:
#                     function_delimiter = '$$'
#
#             elif in_function:
#                 current_stmt.append(line)
#
#                 # 检查函数结束
#                 if function_delimiter in line and 'LANGUAGE' in line.upper():
#                     statements.append('\n'.join(current_stmt))
#                     current_stmt = []
#                     in_function = False
#             else:
#                 # 普通SQL语句
#                 current_stmt.append(line)
#                 if line.endswith(';'):
#                     statements.append(' '.join(current_stmt))
#                     current_stmt = []
#
#         # 处理最后可能未结束的语句
#         if current_stmt:
#             statements.append('\n'.join(current_stmt) if in_function else ' '.join(current_stmt))
#
#         # 执行每个语句
#         result = None
#         with self.transaction():
#             for stmt in statements:
#                 stmt = stmt.strip()
#                 if stmt.endswith(';') and not in_function:
#                     stmt = stmt[:-1]  # 移除末尾分号
#                 if stmt:
#                     result = self.execute(stmt)
#
#         return result
#
#     def create_schema(self, schema_name: str, if_not_exists: bool = True) -> bool:
#         """
#         创建数据库模式
#
#         Args:
#             schema_name: 模式名称
#             if_not_exists: 是否在模式不存在时才创建
#
#         Returns:
#             是否成功创建
#         """
#         if_not_exists_clause = "IF NOT EXISTS " if if_not_exists else ""
#         sql = f'CREATE SCHEMA {if_not_exists_clause}"{schema_name}"'
#
#         try:
#             self.execute(sql)
#             self.logger.info(f"创建模式 {schema_name} 成功")
#             return True
#         except Exception as e:
#             self.logger.error(f"创建模式失败: {e}")
#             return False
#
#     def drop_schema(self, schema_name: str, cascade: bool = False, if_exists: bool = True) -> bool:
#         """
#         删除数据库模式
#
#         Args:
#             schema_name: 模式名称
#             cascade: 是否级联删除模式中的所有对象
#             if_exists: 是否在模式存在时才删除
#
#         Returns:
#             是否成功删除
#         """
#         if_exists_clause = "IF EXISTS " if if_exists else ""
#         cascade_clause = "CASCADE" if cascade else "RESTRICT"
#         sql = f'DROP SCHEMA {if_exists_clause}"{schema_name}" {cascade_clause}'
#
#         try:
#             self.execute(sql)
#             self.logger.info(f"删除模式 {schema_name} 成功")
#             return True
#         except Exception as e:
#             self.logger.error(f"删除模式失败: {e}")
#             return False
#
#     def get_schemas(self) -> List[str]:
#         """
#         获取所有模式名列表
#
#         Returns:
#             模式名列表
#         """
#         sql = """
#         SELECT schema_name
#         FROM information_schema.schemata
#         WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema'
#         ORDER BY schema_name
#         """
#         result = self.query(sql)
#         return [row["schema_name"] for row in result]
#
#     def get_tables(self, schema: str = None) -> List[str]:
#         """
#         获取指定模式的所有表
#
#         Args:
#             schema: 模式名，默认为当前模式
#
#         Returns:
#             表名列表
#         """
#         schema = schema or self.schema
#         sql = """
#         SELECT table_name
#         FROM information_schema.tables
#         WHERE table_schema = %s AND table_type = 'BASE TABLE'
#         ORDER BY table_name
#         """
#         result = self.query(sql, (schema,))
#         return [row["table_name"] for row in result]
#
#     def create_index(self, tablename: str, columns: List[str],
#                      index_name: str = None, unique: bool = False,
#                      method: str = "btree", where: str = None,
#                      schema: str = None) -> bool:
#         """
#         创建索引
#
#         Args:
#             tablename: 表名
#             columns: 索引列
#             index_name: 索引名，如果未指定则自动生成
#             unique: 是否唯一索引
#             method: 索引方法 (btree, hash, gist, gin等)
#             where: 条件表达式
#             schema: 模式名
#
#         Returns:
#             是否创建成功
#         """
#         schema = schema or self.schema
#
#         # 自动生成索引名
#         if not index_name:
#             col_names = "_".join(columns)
#             prefix = "idx" if not unique else "udx"
#             index_name = f"{prefix}_{tablename}_{col_names}"
#
#             # 索引名最长为63个字符
#             if len(index_name) > 63:
#                 index_name = index_name[:63]
#
#         # 构建索引定义
#         unique_clause = "UNIQUE " if unique else ""
#         method_clause = f"USING {method}" if method else ""
#         columns_clause = ", ".join([f'"{col}"' for col in columns])
#         where_clause = f"WHERE {where}" if where else ""
#
#         table_with_schema = f'"{schema}"."{tablename}"'
#
#         sql = f"CREATE {unique_clause}INDEX {index_name} ON {table_with_schema} {method_clause} ({columns_clause}) {where_clause}"
#
#         try:
#             self.execute(sql)
#             self.logger.info(f"创建索引 {index_name} 成功")
#             return True
#         except Exception as e:
#             self.logger.error(f"创建索引失败: {e}")
#             return False
#
#     def export_to_csv(self, tablename: str, filepath: str, delimiter: str = ',',
#                       include_header: bool = True, encoding: str = 'utf-8',
#                       schema: str = None, conditions: Dict = None):
#         """
#         导出表数据到CSV文件
#
#         Args:
#             tablename: 表名
#             filepath: 输出文件路径
#             delimiter: 分隔符
#             include_header: 是否包含表头
#             encoding: 文件编码
#             schema: 模式名
#             conditions: 导出条件
#
#         Returns:
#             导出的记录数
#         """
#         import csv
#
#         schema = schema or self.schema
#
#         # 构建查询
#         conditions_clause = ""
#         params = []
#
#         if conditions:
#             where_clause, where_params = self.query_builder._build_where_clause(conditions)
#             if where_clause:
#                 conditions_clause = f"WHERE {where_clause}"
#                 params = where_params
#
#         # 获取表数据
#         table_with_schema = f'"{schema}"."{tablename}"'
#         sql = f"SELECT * FROM {table_with_schema} {conditions_clause}"
#         data = self.query(sql, params)
#
#         if not data:
#             self.logger.warning(f"表 {tablename} 没有数据可导出")
#             return 0
#
#         # 写入CSV文件
#         with open(filepath, 'w', newline='', encoding=encoding) as f:
#             writer = csv.writer(f, delimiter=delimiter)
#
#             # 写入表头
#             if include_header and data:
#                 writer.writerow(data[0].keys())
#
#             # 写入数据行
#             for row in data:
#                 writer.writerow(row.values())
#
#         self.logger.info(f"已将{len(data)}条记录从表 {tablename} 导出到 {filepath}")
#         return len(data)
#
#     def import_from_csv(self, tablename: str, filepath: str, delimiter: str = ',',
#                         has_header: bool = True, encoding: str = 'utf-8',
#                         batch_size: int = 1000, schema: str = None):
#         """
#         从CSV文件导入数据到表
#
#         Args:
#             tablename: 表名
#             filepath: CSV文件路径
#             delimiter: 分隔符
#             has_header: 是否包含表头行
#             encoding: 文件编码
#             batch_size: 批处理大小
#             schema: 模式名
#
#         Returns:
#             导入的记录数
#         """
#         import csv
#
#         schema = schema or self.schema
#
#         # 检查表是否存在
#         if not self.table_exists(tablename):
#             self.logger.error(f"表 {tablename} 不存在")
#             raise ValueError(f"表 {tablename} 不存在")
#
#         # 获取表结构
#         columns = self.get_columns(tablename)
#         columns_lower = [col.lower() for col in columns]
#
#         # 读取CSV文件
#         records = []
#         total_imported = 0
#
#         with open(filepath, 'r', encoding=encoding) as f:
#             reader = csv.reader(f, delimiter=delimiter)
#
#             # 处理表头
#             if has_header:
#                 header_row = next(reader)
#                 # 验证或创建字段映射
#                 field_map = {}
#                 for i, name in enumerate(header_row):
#                     name_lower = name.lower()
#                     if name_lower in columns_lower:
#                         # 找到匹配的列（不区分大小写）
#                         original_col = columns[columns_lower.index(name_lower)]
#                         field_map[i] = original_col
#                     else:
#                         self.logger.warning(f"CSV中的列 '{name}' 在表 {tablename} 中不存在，将被忽略")
#             else:
#                 # 没有表头，假设CSV列与表列一一对应
#                 field_map = {i: col for i, col in enumerate(columns) if i < len(columns)}
#
#             # 处理数据行
#             for row in reader:
#                 record = {}
#                 for i, value in enumerate(row):
#                     if i in field_map:
#                         # 将值添加到记录中
#                         record[field_map[i]] = value if value else None
#
#                 records.append(record)
#
#                 # 批处理导入
#                 if len(records) >= batch_size:
#                     self.insert(tablename, records, schema=schema)
#                     total_imported += len(records)
#                     records = []
#
#             # 处理剩余记录
#             if records:
#                 self.insert(tablename, records, schema=schema)
#                 total_imported += len(records)
#
#         self.logger.info(f"成功从 {filepath} 导入 {total_imported} 条记录到表 {tablename}")
#         return total_imported
#
#     def vacuum(self, tablename: str = None, analyze: bool = True, full: bool = False):
#         """
#         执行VACUUM操作，回收空间并优化表
#
#         Args:
#             tablename: 要清理的表名，None表示所有表
#             analyze: 是否同时执行分析
#             full: 是否执行完整清理
#         """
#         # VACUUM需要连接处于自动提交模式
#         self._ensure_connection()
#
#         # 关闭事务，VACUUM不能在事务内执行
#         if self.__in_transaction:
#             self.commit()
#
#         # 构建VACUUM命令
#         options = []
#         if analyze:
#             options.append("ANALYZE")
#         if full:
#             options.append("FULL")
#
#         options_str = " ".join(options)
#
#         if tablename:
#             schema = self.schema
#             table_with_schema = f'"{schema}"."{tablename}"'
#             sql = f"VACUUM {options_str} {table_with_schema}"
#         else:
#             sql = f"VACUUM {options_str}"
#
#         try:
#             # 执行VACUUM
#             # 注意：在某些PostgreSQL版本中，VACUUM的输出可能无法通过正常的游标方式获取
#             self.execute(sql)
#             self.logger.info(f"成功执行VACUUM操作 {options_str} {'表 ' + tablename if tablename else '所有表'}")
#         except Exception as e:
#             self.logger.error(f"执行VACUUM操作失败: {e}")
#             raise
#
#     def get_function_definition(self, function_name: str, schema: str = None) -> str:
#         """
#         获取函数的定义
#
#         Args:
#             function_name: 函数名
#             schema: 模式名
#
#         Returns:
#             函数定义
#         """
#         schema = schema or self.schema
#
#         sql = """
#         SELECT pg_get_functiondef(p.oid) as definition
#         FROM pg_proc p
#         JOIN pg_namespace n ON p.pronamespace = n.oid
#         WHERE n.nspname = %s AND p.proname = %s
#         """
#
#         result = self.query_one(sql, (schema, function_name))
#         return result["definition"] if result else None
