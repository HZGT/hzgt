# # -*- coding: utf-8 -*-
# import os
# import re
# import time
# from contextlib import contextmanager
# from logging import Logger
# from typing import Dict, Optional, Any, List, Tuple, Union
#
# import cx_Oracle
#
# from ...log import set_log
# from .sqlcore import SQLutilop, ConnectionPool, QueryBuilder, DBAdapter, JoinType
#
# # Oracle数据类型映射
# ORACLE_DATA_TYPES = {
#     'INTEGER': 'NUMBER(10)',
#     'BIGINT': 'NUMBER(19)',
#     'FLOAT': 'NUMBER',
#     'DOUBLE': 'FLOAT',
#     'DECIMAL': 'NUMBER',
#     'CHAR': 'CHAR',
#     'VARCHAR': 'VARCHAR2',
#     'TEXT': 'CLOB',
#     'DATE': 'DATE',
#     'DATETIME': 'TIMESTAMP',
#     'TIMESTAMP': 'TIMESTAMP',
#     'BLOB': 'BLOB',
#     'CLOB': 'CLOB',
#     'BOOLEAN': 'NUMBER(1)',
# }
#
#
# class OracleAdapter(DBAdapter):
#     """Oracle数据库适配器实现"""
#
#     def __init__(self, host: str, port: int, service_name: str, user: str, password: str,
#                  encoding: str = "UTF8", logger: Optional[Logger] = None):
#         """
#         初始化Oracle适配器
#
#         Args:
#             host: Oracle服务器主机名
#             port: 端口号
#             service_name: 服务名
#             user: 用户名
#             password: 密码
#             encoding: 字符集编码
#             logger: 日志记录器
#         """
#         self.dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
#         self.user = user
#         self.password = password
#         self.encoding = encoding
#         self.logger = logger
#
#     def get_connection(self) -> cx_Oracle.Connection:
#         """获取数据库连接"""
#         try:
#             conn = cx_Oracle.connect(
#                 user=self.user,
#                 password=self.password,
#                 dsn=self.dsn,
#                 encoding=self.encoding
#             )
#             # 设置自动提交
#             conn.autocommit = True
#
#             if self.logger:
#                 self.logger.debug("Oracle数据库连接已建立")
#             return conn
#         except cx_Oracle.Error as e:
#             if self.logger:
#                 self.logger.error(f"Oracle连接失败: {e}")
#             raise RuntimeError(f"Oracle数据库连接失败: {e}") from e
#
#     def close_connection(self, connection: cx_Oracle.Connection):
#         """关闭数据库连接"""
#         if connection:
#             try:
#                 connection.close()
#                 if self.logger:
#                     self.logger.debug("Oracle数据库连接已关闭")
#             except cx_Oracle.Error as e:
#                 if self.logger:
#                     self.logger.error(f"关闭Oracle连接时出错: {e}")
#
#     def execute_query(self, connection: cx_Oracle.Connection, sql: str,
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
#         """
#         cursor = None
#         try:
#             cursor = connection.cursor()
#             if params is None:
#                 params = {}
#             cursor.execute(sql, params)
#
#             # 获取列名
#             if cursor.description:
#                 columns = [col[0] for col in cursor.description]
#
#                 # 转换结果为字典列表
#                 results = []
#                 for row in cursor:
#                     results.append({columns[i]: row[i] for i in range(len(columns))})
#
#                 return results, cursor.rowcount
#             else:
#                 # 非查询操作
#                 return [], cursor.rowcount
#
#         except cx_Oracle.Error as e:
#             if self.logger:
#                 self.logger.error(f"执行SQL失败: {sql} | 参数: {params} | 错误: {e}")
#             raise
#         finally:
#             if cursor:
#                 cursor.close()
#
#     def get_last_insert_id(self, connection: cx_Oracle.Connection, table_name: str = None) -> int:
#         """获取最后插入的ID（需要提供序列名）"""
#         cursor = None
#         try:
#             cursor = connection.cursor()
#             cursor.execute(f"SELECT {table_name}.CURRVAL FROM DUAL")
#             result = cursor.fetchone()
#             return result[0] if result else None
#         except cx_Oracle.Error as e:
#             if self.logger:
#                 self.logger.error(f"获取最后插入ID失败: {e}")
#             raise
#         finally:
#             if cursor:
#                 cursor.close()
#
#     def get_placeholder_style(self) -> str:
#         """获取参数占位符样式"""
#         return ":param"
#
#
# class OracleQueryBuilder(QueryBuilder):
#     """Oracle查询构建器实现"""
#
#     def __init__(self, logger: Optional[Logger] = None):
#         """
#         初始化Oracle查询构建器
#
#         Args:
#             logger: 日志记录器
#         """
#         self.logger = logger
#         self.param_index = 0  # 用于生成唯一命名参数
#
#     def reset_param_index(self):
#         """重置参数索引"""
#         self.param_index = 0
#
#     def next_param_name(self) -> str:
#         """生成下一个唯一参数名"""
#         self.param_index += 1
#         return f"p{self.param_index}"
#
#     @staticmethod
#     def _escape_identifier(identifier: str) -> str:
#         """转义标识符(表名、列名)"""
#         # Oracle使用双引号转义标识符
#         return f'"{identifier.replace("`", "")}"'
#
#     def _build_where_clause(self, conditions: Optional[Dict]) -> Tuple[str, Dict]:
#         """构建WHERE子句和参数"""
#         if not conditions:
#             return "", {}
#
#         self.reset_param_index()
#         where_parts = []
#         params = {}
#
#         # 处理逻辑组合
#         if '$or' in conditions or '$and' in conditions:
#             if '$or' in conditions:
#                 subclauses = []
#                 for subcond in conditions['$or']:
#                     subwhere, subparams = self._build_where_clause(subcond)
#                     if subwhere:
#                         subclauses.append(f"({subwhere})")
#                         params.update(subparams)
#                 if subclauses:
#                     where_parts.append(f"({' OR '.join(subclauses)})")
#
#             if '$and' in conditions:
#                 subclauses = []
#                 for subcond in conditions['$and']:
#                     subwhere, subparams = self._build_where_clause(subcond)
#                     if subwhere:
#                         subclauses.append(f"({subwhere})")
#                         params.update(subparams)
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
#                     params.update(subparams)
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
#                             'IN': 'IN', 'NOT IN': 'NOT IN',
#                             'BETWEEN': 'BETWEEN', 'NOT BETWEEN': 'NOT BETWEEN',
#                             'IS': 'IS', 'IS NOT': 'IS NOT',
#                             # MongoDB风格操作符
#                             '$gt': '>', '$lt': '<', '$gte': '>=', '$lte': '<=',
#                             '$eq': '=', '$ne': '!=',
#                             '$like': 'LIKE', '$nlike': 'NOT LIKE',
#                             '$in': 'IN', '$nin': 'NOT IN',
#                             '$between': 'BETWEEN', '$nbetween': 'NOT BETWEEN',
#                             '$is': 'IS', '$isNot': 'IS NOT',
#                         }
#
#                         op = op_map.get(
#                             op_symbol.upper() if op_symbol.startswith('$') else op_symbol
#                         )
#                         if not op:
#                             raise ValueError(f"无效操作符: {op_symbol}")
#
#                         if op in ('BETWEEN', 'NOT BETWEEN'):
#                             if not isinstance(op_value, (list, tuple)) or len(op_value) != 2:
#                                 raise ValueError(f"{op} 需要两个值的列表")
#                             param1 = self.next_param_name()
#                             param2 = self.next_param_name()
#                             where_parts.append(f"{safe_col} {op} :{param1} AND :{param2}")
#                             params[param1] = op_value[0]
#                             params[param2] = op_value[1]
#                         elif op in ('IN', 'NOT IN'):
#                             if not isinstance(op_value, (list, tuple)):
#                                 raise ValueError(f"{op} 需要列表或元组")
#                             in_params = []
#                             for i, val in enumerate(op_value):
#                                 param_name = f"{self.next_param_name()}"
#                                 in_params.append(f":{param_name}")
#                                 params[param_name] = val
#                             where_parts.append(f"{safe_col} {op} ({', '.join(in_params)})")
#                         elif op in ('IS', 'IS NOT'):
#                             # IS NULL 和 IS NOT NULL 不需要参数
#                             where_parts.append(f"{safe_col} {op} NULL"
#                                                if op_value is None else f"{safe_col} {op} :{self.next_param_name()}")
#                             if op_value is not None:
#                                 param_name = self.next_param_name()
#                                 params[param_name] = op_value
#                         else:
#                             param_name = self.next_param_name()
#                             where_parts.append(f"{safe_col} {op} :{param_name}")
#                             params[param_name] = op_value
#                 else:
#                     # 简单等值条件
#                     if value is None:
#                         where_parts.append(f"{safe_col} IS NULL")
#                     else:
#                         param_name = self.next_param_name()
#                         where_parts.append(f"{safe_col} = :{param_name}")
#                         params[param_name] = value
#
#         return (" AND ".join(where_parts), params) if where_parts else ("", {})
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
#                      **kwargs) -> Tuple[str, Dict]:
#         """构建SELECT语句"""
#         # 重置参数索引
#         self.reset_param_index()
#
#         # 处理表名和字段
#         safe_table = self._escape_identifier(tablename)
#         fields_str = "*"
#         if fields:
#             safe_fields = [self._escape_identifier(f) for f in fields]
#             fields_str = ", ".join(safe_fields)
#
#         # 构建基础查询
#         base_sql = f"SELECT {fields_str} FROM {safe_table}"
#         params = {}
#
#         # 处理WHERE条件
#         where_clause, where_params = self._build_where_clause(conditions)
#         if where_clause:
#             base_sql += f" WHERE {where_clause}"
#             params.update(where_params)
#
#         # 处理GROUP BY
#         if group_by:
#             group_by_fields = [self._escape_identifier(g) for g in group_by]
#             base_sql += f" GROUP BY {', '.join(group_by_fields)}"
#
#             # 处理HAVING
#             if having:
#                 having_clause, having_params = self._build_where_clause(having)
#                 if having_clause:
#                     base_sql += f" HAVING {having_clause}"
#                     params.update(having_params)
#
#         # 处理排序
#         if order:
#             order_parts = []
#             for col, asc in order.items():
#                 direction = "ASC" if asc else "DESC"
#                 order_parts.append(f"{self._escape_identifier(col)} {direction}")
#             if order_parts:
#                 base_sql += f" ORDER BY {', '.join(order_parts)}"
#
#         # 构建分页查询
#         # Oracle 12c+支持OFFSET-FETCH语法
#         use_modern_paging = kwargs.get("use_modern_paging", True)
#
#         if limit is not None:
#             if use_modern_paging:
#                 # 使用现代语法 (Oracle 12c+)
#                 if offset is not None:
#                     base_sql += f" OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
#                 else:
#                     base_sql += f" FETCH FIRST {limit} ROWS ONLY"
#             else:
#                 # 使用传统的ROWNUM方法 (Oracle 11g及以下)
#                 if offset is not None:
#                     # 需要使用子查询和ROW_NUMBER()
#                     inner_sql = base_sql
#                     row_num_col = "row_num"
#
#                     if order:
#                         # 将排序条件移到内部查询
#                         inner_sql = base_sql
#
#                     sql = f"""
#                     SELECT * FROM (
#                         SELECT a.*, ROWNUM as {row_num_col} FROM (
#                             {inner_sql}
#                         ) a WHERE ROWNUM <= :{self.next_param_name()}
#                     ) WHERE {row_num_col} > :{self.next_param_name()}
#                     """
#                     params[f"p{self.param_index - 1}"] = offset + limit
#                     params[f"p{self.param_index}"] = offset
#                 else:
#                     # 简单的ROWNUM限制
#                     sql = f"""
#                     SELECT * FROM (
#                         {base_sql}
#                     ) WHERE ROWNUM <= :{self.next_param_name()}
#                     """
#                     params[f"p{self.param_index}"] = limit
#
#                 return sql, params
#
#         return base_sql, params
#
#     def build_insert(self,
#                      tablename: str,
#                      data: Union[Dict[str, Any], List[Dict[str, Any]]],
#                      **kwargs) -> Tuple[str, Dict]:
#         """构建INSERT语句"""
#         self.reset_param_index()
#         safe_table = self._escape_identifier(tablename)
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
#         # Oracle不支持多行插入语法，返回的是单行插入的SQL和参数
#         record = records[0]
#         params = {}
#
#         # 构建占位符
#         placeholder_parts = []
#         for field in fields:
#             param_name = self.next_param_name()
#             placeholder_parts.append(f":{param_name}")
#             params[param_name] = record[field]
#
#         values_placeholder = ", ".join(placeholder_parts)
#
#         # 构建SQL
#         sql = f"INSERT INTO {safe_table} ({fields_str}) VALUES ({values_placeholder})"
#
#         # 添加RETURNING子句（如果需要）
#         returning = kwargs.get("returning_id")
#         if returning and isinstance(returning, str):
#             sql += f" RETURNING {self._escape_identifier(returning)} INTO :{self.next_param_name()}"
#             params[f"p{self.param_index}"] = None  # 输出参数
#
#         # 返回单行插入的SQL和参数
#         # 多行处理需要在上层处理
#         return sql, params
#
#     def build_update(self,
#                      tablename: str,
#                      update_values: Dict[str, Any],
#                      conditions: Optional[Dict] = None,
#                      **kwargs) -> Tuple[str, Dict]:
#         """构建UPDATE语句"""
#         self.reset_param_index()
#         if not update_values:
#             raise ValueError("没有要更新的数据")
#
#         safe_table = self._escape_identifier(tablename)
#
#         # 构建SET子句
#         set_parts = []
#         params = {}
#         for field, value in update_values.items():
#             param_name = self.next_param_name()
#             safe_field = self._escape_identifier(field)
#             set_parts.append(f"{safe_field} = :{param_name}")
#             params[param_name] = value
#
#         # 构建WHERE子句
#         where_clause, where_params = self._build_where_clause(conditions)
#
#         # 构建SQL
#         sql = f"UPDATE {safe_table} SET {', '.join(set_parts)}"
#
#         if where_clause:
#             sql += f" WHERE {where_clause}"
#             params.update(where_params)
#
#         return sql, params
#
#     def build_delete(self,
#                      tablename: str,
#                      conditions: Optional[Dict] = None,
#                      **kwargs) -> Tuple[str, Dict]:
#         """构建DELETE语句"""
#         self.reset_param_index()
#         safe_table = self._escape_identifier(tablename)
#
#         # 构建WHERE子句
#         where_clause, where_params = self._build_where_clause(conditions)
#
#         # 构建SQL
#         sql = f"DELETE FROM {safe_table}"
#         params = {}
#
#         if where_clause:
#             sql += f" WHERE {where_clause}"
#             params.update(where_params)
#
#         return sql, params
#
#     def build_create_table(self,
#                            tablename: str,
#                            schema: Dict[str, Any],
#                            primary_key: Optional[List[str]] = None,
#                            if_not_exists: bool = True,
#                            **kwargs) -> str:
#         """构建CREATE TABLE语句"""
#         # 验证表名
#         if not re.match(r'^[a-zA-Z0-9_]+$', tablename):
#             raise ValueError("表名只能包含字母、数字和下划线")
#
#         safe_table = self._escape_identifier(tablename)
#
#         # Oracle不支持IF NOT EXISTS语法，需要单独处理
#         table_check_sql = f"""
#         SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = '{tablename.upper()}'
#         """
#
#         # 处理列定义
#         column_defs = []
#         for column, details in schema.items():
#             col_def = None
#
#             if isinstance(details, str):
#                 # 简单格式: {column: "NUMBER"}
#                 col_def = f"{self._escape_identifier(column)} {details}"
#             elif isinstance(details, dict):
#                 # 详细格式: {column: {type: "NUMBER", constraint: "NOT NULL"}}
#                 col_type = details.get("type", "VARCHAR2(255)")
#                 constraint = details.get("constraint", "")
#                 # 转换MySQL类型到Oracle类型
#                 if col_type.upper() in ORACLE_DATA_TYPES:
#                     col_type = ORACLE_DATA_TYPES[col_type.upper()]
#                 col_def = f"{self._escape_identifier(column)} {col_type} {constraint}".strip()
#
#             if col_def:
#                 column_defs.append(col_def)
#
#         # 处理主键
#         if primary_key:
#             safe_pk = [self._escape_identifier(pk) for pk in primary_key]
#             pk_name = f"PK_{tablename}"
#             column_defs.append(f"CONSTRAINT {pk_name} PRIMARY KEY ({', '.join(safe_pk)})")
#
#         # 构建创建表语句
#         create_table_sql = f"""
#         CREATE TABLE {safe_table} (
#             {', '.join(column_defs)}
#         )
#         """
#
#         # 处理自增列（Oracle需要序列和触发器）
#         id_column = kwargs.get("id_column")
#         if id_column:
#             seq_name = f"{tablename}_SEQ"
#             trig_name = f"{tablename}_TRG"
#
#             # 创建序列
#             seq_sql = f"""
#             CREATE SEQUENCE {seq_name}
#             START WITH 1
#             INCREMENT BY 1
#             NOCACHE
#             NOCYCLE
#             """
#
#             # 创建触发器
#             trig_sql = f"""
#             CREATE OR REPLACE TRIGGER {trig_name}
#             BEFORE INSERT ON {safe_table}
#             FOR EACH ROW
#             BEGIN
#                 IF :NEW.{self._escape_identifier(id_column)} IS NULL THEN
#                     SELECT {seq_name}.NEXTVAL INTO :NEW.{self._escape_identifier(id_column)} FROM DUAL;
#                 END IF;
#             END;
#             """
#
#             return table_check_sql, create_table_sql, seq_sql, trig_sql
#
#         return table_check_sql, create_table_sql
#
#     def build_drop_table(self,
#                          tablename: str,
#                          if_exists: bool = True) -> str:
#         """构建DROP TABLE语句"""
#         safe_table = self._escape_identifier(tablename)
#
#         # Oracle不支持IF EXISTS，需要单独检查表是否存在
#         if if_exists:
#             check_sql = f"""
#             SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = '{tablename.upper()}'
#             """
#             return check_sql, f"DROP TABLE {safe_table}"
#         else:
#             return None, f"DROP TABLE {safe_table}"
#
#     def build_join(self,
#                    main_table: str,
#                    joins: List[Tuple[str, str, JoinType, Dict[str, str]]],
#                    fields: Optional[Dict[str, List[str]]] = None,
#                    conditions: Optional[Dict] = None,
#                    order: Optional[Dict[str, bool]] = None,
#                    limit: Optional[int] = None,
#                    offset: Optional[int] = None,
#                    **kwargs) -> Tuple[str, Dict]:
#         """构建连接查询语句"""
#         self.reset_param_index()
#
#         # 处理主表
#         safe_main_table = self._escape_identifier(main_table)
#         main_alias = kwargs.get("main_alias", "t0")
#         from_clause = f"{safe_main_table} {main_alias}"
#
#         # 处理连接
#         join_clauses = []
#         for i, (table, alias, join_type, join_conds) in enumerate(joins, 1):
#             safe_table = self._escape_identifier(table)
#             join_conditions = []
#
#             # 构建连接条件
#             for main_col, join_col in join_conds.items():
#                 main_table_prefix = kwargs.get("main_alias", "t0")
#                 join_conditions.append(
#                     f"{main_table_prefix}.{self._escape_identifier(main_col)} = {alias}.{self._escape_identifier(join_col)}"
#                 )
#
#             join_clause = f"{join_type.value} {safe_table} {alias} ON ({' AND '.join(join_conditions)})"
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
#         params = {}
#         sql = f"SELECT {', '.join(select_fields)} FROM {from_clause} {' '.join(join_clauses)}"
#
#         # 处理WHERE条件
#         if conditions:
#             where_clause, where_params = self._build_where_clause(conditions)
#             if where_clause:
#                 sql += f" WHERE {where_clause}"
#                 params.update(where_params)
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
#             # 添加分页逻辑
#             use_modern_paging = kwargs.get("use_modern_paging", True)
#
#             if use_modern_paging:
#                 # 使用现代语法 (Oracle 12c+)
#                 if offset is not None:
#                     sql += f" OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
#                 else:
#                     sql += f" FETCH FIRST {limit} ROWS ONLY"
#             else:
#                 # 使用传统的ROWNUM方法
#                 if offset is not None:
#                     param1 = self.next_param_name()
#                     param2 = self.next_param_name()
#                     sql = f"""
#                     SELECT * FROM (
#                         SELECT a.*, ROWNUM as rnum FROM (
#                             {sql}
#                         ) a WHERE ROWNUM <= :{param1}
#                     ) WHERE rnum > :{param2}
#                     """
#                     params[param1] = offset + limit
#                     params[param2] = offset
#                 else:
#                     param = self.next_param_name()
#                     sql = f"""
#                     SELECT * FROM (
#                         {sql}
#                     ) WHERE ROWNUM <= :{param}
#                     """
#                     params[param] = limit
#
#         return sql, params
#
#
# class OracleConnectionPool(ConnectionPool):
#     """Oracle连接池实现"""
#
#     def __init__(self, adapter: OracleAdapter, min_connections: int = 1, max_connections: int = 5,
#                  connection_timeout: int = 5, logger: Optional[Logger] = None):
#         """
#         初始化连接池
#
#         Args:
#             adapter: Oracle适配器
#             min_connections: 最小连接数
#             max_connections: 最大连接数
#             connection_timeout: 连接超时时间(秒)
#             logger: 日志记录器
#         """
#         self.adapter = adapter
#         self.min_connections = min_connections
#         self.max_connections = max_connections
#         self.connection_timeout = connection_timeout
#         self.logger = logger
#
#         self._pool = []  # 空闲连接池
#         self._active = 0  # 活跃连接数
#
#         # 初始化连接池
#         self._initialize_pool()
#
#     def _initialize_pool(self):
#         """初始化连接池"""
#         try:
#             for _ in range(self.min_connections):
#                 conn = self.adapter.get_connection()
#                 self._pool.append(conn)
#                 self._active += 1
#             if self.logger:
#                 self.logger.debug(f"连接池初始化完成，初始连接数: {len(self._pool)}")
#         except Exception as e:
#             if self.logger:
#                 self.logger.error(f"初始化连接池失败: {e}")
#             raise
#
#     def get_connection(self) -> cx_Oracle.Connection:
#         """获取连接"""
#         # 首先尝试从池中获取
#         if self._pool:
#             conn = self._pool.pop()
#             # 检查连接是否有效
#             try:
#                 # 简单查询测试连接
#                 cursor = conn.cursor()
#                 cursor.execute("SELECT 1 FROM DUAL")
#                 cursor.close()
#
#                 if self.logger:
#                     self.logger.debug("从连接池获取连接")
#                 return conn
#             except cx_Oracle.Error:
#                 # 连接无效，丢弃并创建新连接
#                 try:
#                     conn.close()
#                 except:
#                     pass
#
#                 if self.logger:
#                     self.logger.debug("连接池中的连接无效，创建新连接")
#                 self._active -= 1  # 减少计数，因为这个连接已经无效
#
#         # 如果没有可用连接或连接无效，创建新连接
#         if self._active >= self.max_connections:
#             # 等待连接释放
#             wait_time = 0
#             while self._active >= self.max_connections and wait_time < self.connection_timeout:
#                 time.sleep(0.1)
#                 wait_time += 0.1
#
#             if self._active >= self.max_connections:
#                 if self.logger:
#                     self.logger.error("连接池已满，无法创建新连接")
#                 raise RuntimeError("连接池已满，无法获取连接")
#
#         # 创建新连接
#         conn = self.adapter.get_connection()
#         self._active += 1
#         if self.logger:
#             self.logger.debug(f"创建新连接，当前活跃连接: {self._active}")
#         return conn
#
#     def release_connection(self, connection: cx_Oracle.Connection):
#         """释放连接回池"""
#         if connection is None:
#             return
#
#         try:
#             # 检查连接是否有效
#             cursor = connection.cursor()
#             cursor.execute("SELECT 1 FROM DUAL")
#             cursor.close()
#
#             # 回收到池中
#             self._pool.append(connection)
#             if self.logger:
#                 self.logger.debug("连接释放回连接池")
#         except cx_Oracle.Error:
#             # 连接无效，关闭
#             try:
#                 connection.close()
#             except:
#                 pass
#             if self.logger:
#                 self.logger.debug("无效连接已关闭")
#         finally:
#             self._active -= 1
#
#     def close_all(self):
#         """关闭所有连接"""
#         for conn in self._pool:
#             try:
#                 conn.close()
#             except:
#                 pass
#         self._pool.clear()
#         self._active = 0
#         if self.logger:
#             self.logger.info("所有连接已关闭")
#
#
# class Oracleop(SQLutilop):
#     """Oracle数据库操作工具类"""
#
#     def __init__(self, host: str, port: int, service_name: str, user: str, password: str, encoding: str = "UTF8",
#                  logger: Logger = None, default_level: int = 2, autoreconnect: bool = True, reconnect_retries: int = 3,
#                  pool_size: int = 5):
#         """
#         初始化Oracle操作工具
#
#         Args:
#             host: Oracle服务器地址
#             port: Oracle服务器端口
#             service_name: 服务名
#             user: 用户名
#             password: 密码
#             encoding: 字符集
#             logger: 日志记录器
#             default_level: 默认日志等级
#             autoreconnect: 是否自动重连
#             reconnect_retries: 重连次数
#             pool_size: 连接池大小
#         """
#         # 日志配置
#         super().__init__(logger)
#         self.adapter = OracleAdapter(host, port, service_name, user, password, encoding, self.logger)
#         self.query_builder = OracleQueryBuilder(self.logger)
#         self.connection_pool = OracleConnectionPool(self.adapter, max_connections=pool_size, logger=self.logger)
#
#         self.autoreconnect = autoreconnect
#         self.reconnect_retries = reconnect_retries
#         self.__connection = None
#         self.__in_transaction = False
#         self.__schema = user.upper()  # Oracle中默认schema是用户名的大写
#         self.__selected_table = None
#
#         self.logger.info(f'Oracle工具初始化完成 host: {host}, port: {port}, service: {service_name}, user: {user}')
#
#     def _create_default_logger(self) -> Logger:
#         """
#         创建默认日志记录器
#
#         Returns:
#             Logger: 日志记录器实例
#         """
#         return set_log("hzgt.oracle", "logs")
#
#     def __enter__(self):
#         """上下文管理器入口"""
#         self.connect()
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """上下文管理器出口"""
#         if exc_type is not None:
#             self.logger.error(f"发生异常: {exc_val}")
#             self.rollback()
#         elif self.__in_transaction:
#             self.commit()
#         self.close()
#
#     def connect(self):
#         """建立数据库连接"""
#         for attempt in range(1, self.reconnect_retries + 1):
#             try:
#                 if self.__connection is not None:
#                     self.close()
#                 self.__connection = self.connection_pool.get_connection()
#                 self.__connection.autocommit = True  # 默认自动提交
#                 self.logger.info(f"Oracle连接成功")
#                 return
#             except Exception as e:
#                 self.logger.error(f"连接失败(尝试 {attempt}/{self.reconnect_retries}): {e}")
#                 if attempt == self.reconnect_retries:
#                     raise RuntimeError(f"数据库连接失败, 重试{self.reconnect_retries}次后仍不可用: {e}") from e
#                 time.sleep(1)  # 等待后重试
#
#
#     def start(self):
#         self.connect()
#
#     def _ensure_connection(self):
#         """确保数据库连接有效"""
#         if self.__connection is None:
#             self.connect()
#             return
#
#         try:
#             # 检查连接是否有效
#             cursor = self.__connection.cursor()
#             cursor.execute("SELECT 1 FROM DUAL")
#             cursor.close()
#         except:
#             if self.autoreconnect:
#                 self.logger.warning("连接已断开，尝试重新连接")
#                 self.connect()
#             else:
#                 raise RuntimeError("数据库连接已断开，且未启用自动重连")
#
#     def close(self):
#         """关闭数据库连接"""
#         if self.__connection:
#             try:
#                 if self.__in_transaction:
#                     self.logger.warning("关闭连接时有未提交的事务，执行回滚")
#                     self.rollback()
#                 self.connection_pool.release_connection(self.__connection)
#                 self.logger.debug("Oracle连接已归还到连接池")
#             finally:
#                 self.__connection = None
#
#    def disconnect(self):
#        self.close()
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
#         """结束事务"""
#         if commit:
#             self.commit()
#         else:
#             self.rollback()
#         # 恢复自动提交模式
#         if self.__connection:
#             self.__connection.autocommit = True
#
#     @contextmanager
#     def transaction(self):
#         """事务上下文管理器"""
#         self._begin_transaction()
#         try:
#             yield
#             self._end_transaction(commit=True)
#         except Exception as e:
#             self._end_transaction(commit=False)
#             raise e
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
#         """
#         for attempt in range(2):  # 最多重试1次
#             try:
#                 self._ensure_connection()
#                 cursor = self.__connection.cursor()
#                 try:
#                     if args is None:
#                         args = {}
#
#                     cursor.execute(sql, args)
#
#                     # 如果是查询，获取结果集
#                     if cursor.description:
#                         columns = [col[0] for col in cursor.description]
#                         results = []
#
#                         for row in cursor:
#                             results.append({columns[i]: row[i] for i in range(len(columns))})
#                         return results
#                     else:
#                         # 非查询操作
#                         if not self.__in_transaction and sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
#                             self.__connection.commit()
#                         return cursor.rowcount
#                 finally:
#                     cursor.close()
#             except cx_Oracle.OperationalError as e:
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
#     def executemany(self, sql: str, args_list: List[Dict]) -> Any:
#         """批量执行SQL语句"""
#         if not args_list:
#             return None
#
#         for attempt in range(2):  # 最多重试1次
#             try:
#                 self._ensure_connection()
#                 cursor = self.__connection.cursor()
#                 try:
#                     # Oracle cx_Oracle 需要特殊处理executemany
#                     # 需要转换参数格式
#                     cursor.executemany(sql, args_list)
#
#                     if not self.__in_transaction:
#                         self.__connection.commit()
#
#                     return cursor.rowcount
#                 finally:
#                     cursor.close()
#             except cx_Oracle.OperationalError as e:
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
#             查询结果列表，每项为一个字典
#         """
#         self._ensure_connection()
#         cursor = None
#         try:
#             cursor = self.__connection.cursor()
#             if args is None:
#                 args = {}
#
#             cursor.execute(sql, args)
#
#             # 获取列名
#             columns = [col[0] for col in cursor.description]
#
#             # 转换结果为字典列表
#             results = []
#             for row in cursor:
#                 results.append({columns[i]: row[i] for i in range(len(columns))})
#
#             return results
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
#             单条记录字典，未找到时返回None
#         """
#         results = self.query(sql, args)
#         return results[0] if results else None
#
#     def select_table(self, tablename: str):
#         """
#         选择表
#
#         Args:
#             tablename: 表名
#         """
#         self.__selected_table = tablename
#         self.logger.debug(f"已记录选择表: {tablename}")
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
#         result = self.query_one(
#             "SELECT COUNT(*) AS CNT FROM USER_TABLES WHERE TABLE_NAME = :table_name",
#             {"table_name": tablename.upper()}
#         )
#         return result and result["CNT"] > 0
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
#         result = self.query(
#             "SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = :table_name",
#             {"table_name": tablename.upper()}
#         )
#         return [row["COLUMN_NAME"] for row in result]
#
#     def create_sequence(self, seq_name: str, start_with: int = 1, increment_by: int = 1):
#         """
#         创建序列
#
#         Args:
#             seq_name: 序列名
#             start_with: 起始值
#             increment_by: 增量
#         """
#         # 检查序列是否存在
#         seq_exists = self.query_one(
#             "SELECT COUNT(*) AS CNT FROM USER_SEQUENCES WHERE SEQUENCE_NAME = :seq_name",
#             {"seq_name": seq_name.upper()}
#         )
#
#         if seq_exists and seq_exists["CNT"] > 0:
#             self.logger.info(f"序列 {seq_name} 已存在")
#             return
#
#         # 创建序列
#         sql = f"""
#         CREATE SEQUENCE {self._escape_identifier(seq_name)}
#         START WITH {start_with}
#         INCREMENT BY {increment_by}
#         NOCACHE
#         NOCYCLE
#         """
#
#         self.execute(sql)
#         self.logger.info(f"序列 {seq_name} 创建成功")
#
#     def drop_sequence(self, seq_name: str):
#         """
#         删除序列
#
#         Args:
#             seq_name: 序列名
#         """
#         # 检查序列是否存在
#         seq_exists = self.query_one(
#             "SELECT COUNT(*) AS CNT FROM USER_SEQUENCES WHERE SEQUENCE_NAME = :seq_name",
#             {"seq_name": seq_name.upper()}
#         )
#
#         if not seq_exists or seq_exists["CNT"] == 0:
#             self.logger.info(f"序列 {seq_name} 不存在，无需删除")
#             return
#
#         # 删除序列
#         sql = f"DROP SEQUENCE {self._escape_identifier(seq_name)}"
#         self.execute(sql)
#         self.logger.info(f"序列 {seq_name} 删除成功")
#
#     def create_trigger(self, trigger_name: str, tablename: str, id_column: str, seq_name: str):
#         """
#         创建自增触发器
#
#         Args:
#             trigger_name: 触发器名称
#             tablename: 表名
#             id_column: 自增列名
#             seq_name: 序列名
#         """
#         # 检查触发器是否存在
#         trig_exists = self.query_one(
#             "SELECT COUNT(*) AS CNT FROM USER_TRIGGERS WHERE TRIGGER_NAME = :trig_name",
#             {"trig_name": trigger_name.upper()}
#         )
#
#         if trig_exists and trig_exists["CNT"] > 0:
#             # 删除现有触发器
#             self.execute(f"DROP TRIGGER {self._escape_identifier(trigger_name)}")
#
#         # 创建触发器
#         sql = f"""
#         CREATE OR REPLACE TRIGGER {self._escape_identifier(trigger_name)}
#         BEFORE INSERT ON {self._escape_identifier(tablename)}
#         FOR EACH ROW
#         BEGIN
#             IF :NEW.{self._escape_identifier(id_column)} IS NULL THEN
#                 SELECT {self._escape_identifier(seq_name)}.NEXTVAL
#                 INTO :NEW.{self._escape_identifier(id_column)}
#                 FROM DUAL;
#             END IF;
#         END;
#         """
#
#         self.execute(sql)
#         self.logger.info(f"触发器 {trigger_name} 创建成功")
#
#     def get_schemas(self) -> List[str]:
#         """获取所有模式名列表"""
#         result = self.query("SELECT USERNAME FROM ALL_USERS ORDER BY USERNAME")
#         return [row["USERNAME"] for row in result]
#
#     def get_tables(self, schema: str = None) -> List[str]:
#         """
#         获取指定模式的所有表
#
#         Args:
#             schema: 模式名，默认为当前用户
#
#         Returns:
#             表名列表
#         """
#         schema = schema or self.__schema
#         result = self.query(
#             "SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER = :schema",
#             {"schema": schema.upper()}
#         )
#         return [row["TABLE_NAME"] for row in result]
#
#     def get_sequences(self, schema: str = None) -> List[str]:
#         """
#         获取指定模式的所有序列
#
#         Args:
#             schema: 模式名，默认为当前用户
#
#         Returns:
#             序列名列表
#         """
#         schema = schema or self.__schema
#         result = self.query(
#             "SELECT SEQUENCE_NAME FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = :schema",
#             {"schema": schema.upper()}
#         )
#         return [row["SEQUENCE_NAME"] for row in result]
#
#     def create_table(self, tablename: str, attr_dict: Dict[str, str], primary_key: List[str] = None,
#                      bool_id: bool = True, bool_autoselect: bool = True, **kwargs):
#         """
#         创建表
#
#         Args:
#             tablename: 需要创建的表名
#             attr_dict: 字典 {列名: 数据类型}
#             primary_key: 主键列表
#             bool_id: 是否添加 id 为自增主键
#             bool_autoselect: 创建表后是否自动选择该表
#             **kwargs: 额外参数
#         """
#         # 检查表名有效性
#         if not re.match(r'^[a-zA-Z0-9_]+$', tablename):
#             self.logger.error("表名无效, 只能包含字母、数字和下划线")
#             raise ValueError("表名只能包含字母、数字和下划线")
#
#         # 将表名转为大写 (Oracle惯例)
#         tablename = tablename.upper()
#
#         # 检查表是否已存在
#         if self.table_exists(tablename):
#             self.logger.info(f"表 {tablename} 已存在")
#             if bool_autoselect:
#                 self.select_table(tablename)
#             return
#
#         # 处理自增ID
#         id_column = None
#         seq_name = f"{tablename}_SEQ"
#         trigger_name = f"{tablename}_TRG"
#
#         if bool_id:
#             if 'id' in attr_dict:
#                 # 用户定义了id列，确认类型
#                 attr_dict['id'] = "NUMBER(38)"
#                 id_column = 'id'
#                 # 确保ID在主键中
#                 if primary_key and 'id' not in primary_key:
#                     primary_key.append('id')
#                 elif not primary_key:
#                     primary_key = ['id']
#             else:
#                 # 添加id列
#                 attr_dict = {'id': "NUMBER(38)"} | attr_dict
#                 id_column = 'id'
#                 if not primary_key:
#                     primary_key = ['id']
#
#         # 调用查询构建器生成建表SQL
#         check_sql, create_sql = self.query_builder.build_create_table(
#             tablename=tablename,
#             schema=attr_dict,
#             primary_key=primary_key,
#             id_column=id_column
#         )
#
#         # 执行SQL
#         with self.transaction():
#             # 创建表
#             self.execute(create_sql)
#
#             # 如果需要自增ID，创建序列和触发器
#             if bool_id and id_column:
#                 self.create_sequence(seq_name)
#                 self.create_trigger(trigger_name, tablename, id_column, seq_name)
#
#         self.logger.info(f"创建表 {tablename} 成功")
#         if bool_autoselect:
#             self.select_table(tablename)
#
#     def drop_table(self, tablename: str = '', if_exists: bool = True):
#         """
#         删除表
#
#         Args:
#             tablename: 表名，默认为当前选择的表
#             if_exists: 是否在表不存在时忽略错误
#         """
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         tablename = tablename.upper()  # Oracle表名通常为大写
#
#         # 检查表是否存在
#         if if_exists and not self.table_exists(tablename):
#             self.logger.info(f"表 {tablename} 不存在，无需删除")
#             return
#
#         # 检查相关对象
#         seq_name = f"{tablename}_SEQ"
#         trigger_name = f"{tablename}_TRG"
#
#         # 执行删除
#         with self.transaction():
#             # 删除表
#             self.execute(f"DROP TABLE {self._escape_identifier(tablename)}")
#
#             # 尝试删除关联的序列和触发器
#             try:
#                 self.drop_sequence(seq_name)
#             except:
#                 pass
#
#         self.logger.info(f"删除表 {tablename} 成功")
#         if tablename == self.__selected_table:
#             self.__selected_table = None
#
#     def insert(self, tablename: str = '', record: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
#                return_id: bool = False, **kwargs):
#         """
#         插入数据
#
#         Args:
#             tablename: 表名，默认为当前选择的表
#             record: 要插入的记录或记录列表
#             return_id: 是否返回插入ID
#             **kwargs: 其他参数
#
#         Returns:
#             如果return_id为True，返回插入ID；否则返回None
#         """
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         if not record:
#             self.logger.error("插入数据失败: record 参数不能为空")
#             raise ValueError("record 参数不能为空")
#
#         # Oracle表名通常为大写
#         tablename = tablename.upper()
#
#         is_batch = isinstance(record, list)
#         if is_batch:
#             # 批量插入
#             if not record:
#                 return None
#
#             # 获取所有字段名
#             fields = list(record[0].keys())
#
#             # Oracle不支持标准的批量插入语法，需要单独处理每条记录
#             # 或者使用cx_Oracle的executemany功能
#             total_inserted = 0
#             returning_values = []
#
#             # 构建单条插入SQL
#             sql, _ = self.query_builder.build_insert(
#                 tablename=tablename,
#                 data={f: None for f in fields}  # 使用空值构建SQL模板
#             )
#
#             # 准备批量参数
#             batch_params = []
#             for r in record:
#                 # 确保所有记录有相同的字段
#                 if set(r.keys()) != set(fields):
#                     raise ValueError("批量插入中的记录必须具有相同的字段")
#                 param_dict = {f: r.get(f) for f in fields}
#                 batch_params.append(param_dict)
#
#             # 执行批量插入
#             cursor = None
#             try:
#                 self._ensure_connection()
#                 cursor = self.__connection.cursor()
#                 cursor.executemany(sql, batch_params)
#                 if not self.__in_transaction:
#                     self.__connection.commit()
#                 total_inserted = cursor.rowcount
#                 self.logger.info(f"成功批量插入{total_inserted}条数据到表 {tablename}")
#             except Exception as e:
#                 if not self.__in_transaction:
#                     self.__connection.rollback()
#                 self.logger.error(f"批量插入数据失败: {e}")
#                 raise
#             finally:
#                 if cursor:
#                     cursor.close()
#
#             return total_inserted if not return_id else None  # Oracle批量插入无法直接返回ID
#
#         else:
#             # 单条插入
#             # 构建插入SQL
#             sql, params = self.query_builder.build_insert(
#                 tablename=tablename,
#                 data=record
#             )
#
#             # 处理返回ID
#             id_field = None
#             out_param = None
#             returning_clause = ""
#
#             if return_id:
#                 # 判断主键字段
#                 id_field = kwargs.get("id_field", "id")
#                 out_param = f"out_{id_field}"
#                 # 添加RETURNING子句
#                 returning_clause = f" RETURNING {self._escape_identifier(id_field)} INTO :{out_param}"
#                 sql += returning_clause
#                 # 添加输出参数
#                 params[out_param] = None
#
#             # 执行SQL
#             cursor = None
#             try:
#                 self._ensure_connection()
#                 cursor = self.__connection.cursor()
#
#                 if return_id:
#                     # 需要处理输出参数
#                     out_var = cursor.var(cx_Oracle.NUMBER)
#                     exec_params = params.copy()
#                     exec_params[out_param] = out_var
#                     cursor.execute(sql, exec_params)
#                     if not self.__in_transaction:
#                         self.__connection.commit()
#                     self.logger.info(f"成功插入数据到表 {tablename}")
#                     return out_var.getvalue()
#                 else:
#                     # 普通插入
#                     cursor.execute(sql, params)
#                     if not self.__in_transaction:
#                         self.__connection.commit()
#                     self.logger.info(f"成功插入数据到表 {tablename}")
#                     return None
#             except Exception as e:
#                 if not self.__in_transaction:
#                     self.__connection.rollback()
#                 self.logger.error(f"插入数据失败: {e}")
#                 raise
#             finally:
#                 if cursor:
#                     cursor.close()
#
#     def select(self, tablename: str = "", conditions: Dict = None,
#                order: Dict[str, bool] = None, fields: List[str] = None,
#                limit: int = None, offset: int = None, bool_dict: bool = False, **kwargs):
#         """
#         查询数据
#
#         Args:
#             tablename: 表名，默认为当前选择的表
#             conditions: 查询条件
#             order: 排序 {列名: 是否升序}
#             fields: 要查询的字段列表
#             limit: 限制返回记录数
#             offset: 跳过前N条记录
#             bool_dict: 是否以字典形式返回结果 {列名: [列值列表]}，默认为False
#             **kwargs: 其他参数
#
#         Returns:
#             查询结果列表或字典
#         """
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         # Oracle表名通常为大写
#         tablename = tablename.upper()
#
#         # 构建查询SQL
#         sql, params = self.query_builder.build_select(
#             tablename=tablename,
#             fields=fields,
#             conditions=conditions,
#             order=order,
#             limit=limit,
#             offset=offset,
#             **kwargs
#         )
#
#         # 执行查询
#         results = self.query(sql, params)
#
#         # 如果需要字典形式返回
#         if bool_dict:
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
#         # 默认返回行记录列表
#         return results
#
#     def update(self, tablename: str = '', update_values: Dict[str, Any] = None,
#                conditions: Dict = None, **kwargs):
#         """
#         更新数据
#
#         Args:
#             tablename: 表名，默认为当前选择的表
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
#         # Oracle表名通常为大写
#         tablename = tablename.upper()
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
#         cursor = None
#         try:
#             self._ensure_connection()
#             cursor = self.__connection.cursor()
#             cursor.execute(sql, params)
#             affected_rows = cursor.rowcount
#             if not self.__in_transaction:
#                 self.__connection.commit()
#             self.logger.info(f"更新表 {tablename} 成功，受影响行数: {affected_rows}")
#             return affected_rows
#         except Exception as e:
#             if not self.__in_transaction:
#                 self.__connection.rollback()
#             self.logger.error(f"更新数据失败: {e}")
#             raise
#         finally:
#             if cursor:
#                 cursor.close()
#
#     def delete(self, tablename: str = '', conditions: Dict = None, **kwargs):
#         """
#         删除数据
#
#         Args:
#             tablename: 表名，默认为当前选择的表
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
#         # Oracle表名通常为大写
#         tablename = tablename.upper()
#
#         # 构建删除SQL
#         sql, params = self.query_builder.build_delete(
#             tablename=tablename,
#             conditions=conditions,
#             **kwargs
#         )
#
#         # 执行删除
#         cursor = None
#         try:
#             self._ensure_connection()
#             cursor = self.__connection.cursor()
#             cursor.execute(sql, params)
#             affected_rows = cursor.rowcount
#             if not self.__in_transaction:
#                 self.__connection.commit()
#             self.logger.info(f"从表 {tablename} 删除数据成功，受影响行数: {affected_rows}")
#             return affected_rows
#         except Exception as e:
#             if not self.__in_transaction:
#                 self.__connection.rollback()
#             self.logger.error(f"删除数据失败: {e}")
#             raise
#         finally:
#             if cursor:
#                 cursor.close()
#
#     def purge(self, tablename: str = ''):
#         """
#         清空表数据
#
#         Args:
#             tablename: 表名，默认为当前选择的表
#         """
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         # Oracle表名通常为大写
#         tablename = tablename.upper()
#
#         safe_table = self._escape_identifier(tablename)
#         sql = f"TRUNCATE TABLE {safe_table}"
#         self.execute(sql)
#         self.logger.info(f"表 {tablename} 已清空")
#
#     def join(self, main_table: str, joins: List[Tuple[str, str, JoinType, Dict[str, str]]],
#              conditions: Dict = None, fields: Dict[str, List[str]] = None,
#              order: Dict[str, bool] = None, limit: int = None, offset: int = None, **kwargs):
#         """
#         执行连接查询
#
#         Args:
#             main_table: 主表
#             joins: 连接表定义 [(表名, 别名, 连接类型, {主表字段: 连接表字段}), ...]
#             conditions: 查询条件
#             fields: 查询字段 {表别名: [字段名, ...], ...}
#             order: 排序 {字段名: 是否升序}
#             limit: 限制返回记录数
#             offset: 跳过前N条记录
#             **kwargs: 其他参数
#
#         Returns:
#             查询结果
#         """
#         # Oracle表名通常为大写
#         main_table = main_table.upper()
#         joins = [(t.upper(), alias, join_type, cond) for t, alias, join_type, cond in joins]
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
#     def batch_insert(self, tablename: str, records: List[Dict[str, Any]],
#                      batch_size: int = 1000, **kwargs):
#         """
#         批量插入数据
#
#         Args:
#             tablename: 表名
#             records: 记录列表
#             batch_size: 每批大小
#             **kwargs: 其他参数
#
#         Returns:
#             插入的记录数
#         """
#         if not records:
#             return 0
#
#         tablename = tablename or self.__selected_table
#         if not tablename:
#             raise ValueError("未指定表名")
#
#         # Oracle表名通常为大写
#         tablename = tablename.upper()
#
#         total = 0
#         for i in range(0, len(records), batch_size):
#             batch = records[i:i + batch_size]
#             result = self.insert(tablename, batch, **kwargs)
#             total += len(batch)
#
#         return total
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
#         for line in script.split('\n'):
#             line = line.strip()
#             if not line or line.startswith('--'):  # 忽略空行和注释
#                 continue
#
#             current_stmt.append(line)
#             if line.endswith(';'):
#                 statements.append(' '.join(current_stmt))
#                 current_stmt = []
#
#         # 如果有未结束的语句
#         if current_stmt:
#             statements.append(' '.join(current_stmt))
#
#         # 执行每个语句
#         result = None
#         with self.transaction():
#             for stmt in statements:
#                 stmt = stmt.strip()
#                 if stmt.endswith(';'):
#                     stmt = stmt[:-1]  # 移除末尾分号
#                 if stmt:
#                     result = self.execute(stmt)
#
#         return result
#
#     def export_to_csv(self, tablename: str, filepath: str, delimiter: str = ',',
#                       include_header: bool = True, encoding: str = 'utf-8'):
#         """
#         导出表数据到CSV文件
#
#         Args:
#             tablename: 表名
#             filepath: 输出文件路径
#             delimiter: 分隔符
#             include_header: 是否包含表头
#             encoding: 文件编码
#
#         Returns:
#             导出的记录数
#         """
#         import csv
#
#         # 获取表数据
#         data = self.select(tablename)
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
#                         has_header: bool = True, encoding: str = 'utf-8', batch_size: int = 1000):
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
#
#         Returns:
#             导入的记录数
#         """
#         import csv
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
#                     self.insert(tablename, records)
#                     total_imported += len(records)
#                     records = []
#
#             # 处理剩余记录
#             if records:
#                 self.insert(tablename, records)
#                 total_imported += len(records)
#
#         self.logger.info(f"成功从 {filepath} 导入 {total_imported} 条记录到表 {tablename}")
#         return total_imported
