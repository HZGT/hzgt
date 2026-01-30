import json
import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Union

import psycopg2
import pymysql

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s:%(lineno)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    MYSQL = "mysql"
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


@dataclass
class QueryResult:
    """查询结果封装"""
    success: bool
    data: List[Dict] = None
    message: str = ""
    rowcount: int = 0
    lastrowid: Any = None

    def __post_init__(self):
        if self.data is None:
            self.data = []

    def to_dict(self):
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "rowcount": self.rowcount,
            "lastrowid": self.lastrowid
        }


class ConnectionPool:
    """简单的连接池实现"""

    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.pool = []
        self.lock = threading.Lock()
        self.active_connections = 0

    def get_connection(self, db_manager):
        """从池中获取连接"""
        with self.lock:
            if self.pool:
                return self.pool.pop()
            elif self.active_connections < self.max_connections:
                self.active_connections += 1
                return self._create_connection(db_manager)
            else:
                raise Exception("连接池已满，无法获取新连接")

    def return_connection(self, connection):
        """归还连接到池中"""
        with self.lock:
            self.pool.append(connection)

    def _create_connection(self, db_manager):
        """创建新连接"""
        if db_manager.db_type == DatabaseType.SQLITE:
            db_path = db_manager.database
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
            return sqlite3.connect(db_path)
        elif db_manager.db_type == DatabaseType.MYSQL:
            params = db_manager.get_connection_params()
            return pymysql.connect(**params)
        elif db_manager.db_type == DatabaseType.POSTGRESQL:
            params = db_manager.get_connection_params()
            return psycopg2.connect(**params)
        else:
            raise ValueError(f"不支持的数据库类型: {db_manager.db_type}")

    def close_all(self):
        """关闭所有连接"""
        with self.lock:
            for conn in self.pool:
                try:
                    conn.close()
                except:
                    pass
            self.pool.clear()
            self.active_connections = 0


class DatabaseManager:
    def __init__(
            self,
            db_type: Union[str, DatabaseType],
            host: str = None,
            port: int = None,
            user: str = None,
            passwd: str = None,
            database: str = None,
            charset: str = "utf8",
            pool_size: int = 5
    ):
        if isinstance(db_type, str):
            self.db_type = DatabaseType(db_type.lower())
        else:
            self.db_type = db_type

        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.database = database
        self.charset = charset
        self.pool = ConnectionPool(max_connections=pool_size)
        self._transaction_depth = 0

    def get_connection_params(self) -> Dict:
        """获取连接参数"""
        if self.db_type == DatabaseType.SQLITE:
            return {"database": self.database}
        elif self.db_type == DatabaseType.POSTGRESQL:
            params = {
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "password": self.passwd,
                "dbname": self.database
            }
            # 移除空值
            return {k: v for k, v in params.items() if v is not None}
        else:
            params = {
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "password": self.passwd,
                "charset": self.charset
            }
            if self.database:
                params["database"] = self.database
            # 移除空值
            return {k: v for k, v in params.items() if v is not None}

    def create_database(self, database_name: str) -> bool:
        """创建数据库（MySQL/PostgreSQL）"""
        try:
            if self.db_type == DatabaseType.MYSQL:
                # 临时连接到无数据库的实例
                temp_params = self.get_connection_params()
                if 'database' in temp_params:
                    del temp_params['database']
                conn = pymysql.connect(**temp_params)
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET {self.charset}")
                cursor.close()
                conn.commit()
                conn.close()
                return True

            elif self.db_type == DatabaseType.POSTGRESQL:
                # PostgreSQL需要连接到template1数据库
                temp_params = self.get_connection_params()
                temp_params['dbname'] = 'template1'
                conn = psycopg2.connect(**temp_params)
                conn.autocommit = True  # 创建数据库需要自动提交
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE {database_name} ENCODING '{self.charset}'")
                cursor.close()
                conn.close()
                return True

            else:
                logger.warning("SQLite不支持动态创建数据库")
                return False

        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            return False

    def drop_database(self, database_name: str) -> bool:
        """删除数据库"""
        try:
            if self.db_type == DatabaseType.MYSQL:
                temp_params = self.get_connection_params()
                if 'database' in temp_params:
                    del temp_params['database']
                conn = pymysql.connect(**temp_params)
                cursor = conn.cursor()
                cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
                cursor.close()
                conn.commit()
                conn.close()
                return True

            elif self.db_type == DatabaseType.POSTGRESQL:
                temp_params = self.get_connection_params()
                temp_params['dbname'] = 'template1'
                conn = psycopg2.connect(**temp_params)
                conn.autocommit = True
                cursor = conn.cursor()
                cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
                cursor.close()
                conn.close()
                return True

            else:
                logger.warning("SQLite不支持删除数据库")
                return False

        except Exception as e:
            logger.error(f"删除数据库失败: {e}")
            return False

    def get_databases(self) -> List[str]:
        """获取所有数据库列表"""
        try:
            if self.db_type == DatabaseType.MYSQL:
                temp_params = self.get_connection_params()
                if 'database' in temp_params:
                    del temp_params['database']
                conn = pymysql.connect(**temp_params)
                cursor = conn.cursor()
                cursor.execute("SHOW DATABASES")
                databases = [row[0] for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                return databases

            elif self.db_type == DatabaseType.POSTGRESQL:
                temp_params = self.get_connection_params()
                temp_params['dbname'] = 'template1'
                conn = psycopg2.connect(**temp_params)
                cursor = conn.cursor()
                cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
                databases = [row[0] for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                return databases

            else:
                return [self.database] if self.database else []

        except Exception as e:
            logger.error(f"获取数据库列表失败: {e}")
            return []


class SQLop:
    def __init__(self, db_manager: DatabaseManager, autocommit: bool = True):
        self.db_manager = db_manager
        self.autocommit = autocommit
        self._connection = None
        self._cursor = None
        self._in_transaction = False

    @contextmanager
    def connection_context(self):
        """连接上下文管理器"""
        conn = None
        cursor = None
        try:
            conn = self.db_manager.pool.get_connection(self.db_manager)
            cursor = conn.cursor()
            yield cursor
            if self.autocommit and not self._in_transaction:
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.db_manager.pool.return_connection(conn)

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        if self._in_transaction:
            # 嵌套事务，使用保存点
            savepoint_name = f"savepoint_{self.db_manager._transaction_depth}"
            self.db_manager._transaction_depth += 1
            try:
                self._cursor.execute(f"SAVEPOINT {savepoint_name}")
                yield
                self._cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            except Exception as e:
                self._cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                raise e
            finally:
                self.db_manager._transaction_depth -= 1
        else:
            # 开始新事务
            self._in_transaction = True
            self._connection = self.db_manager.pool.get_connection(self.db_manager)
            self._cursor = self._connection.cursor()
            try:
                yield
                self._connection.commit()
            except Exception as e:
                self._connection.rollback()
                raise e
            finally:
                self._cursor.close()
                self.db_manager.pool.return_connection(self._connection)
                self._connection = None
                self._cursor = None
                self._in_transaction = False

    def _get_placeholder(self) -> str:
        """获取占位符"""
        if self.db_manager.db_type == DatabaseType.POSTGRESQL:
            return "%s"
        elif self.db_manager.db_type == DatabaseType.MYSQL:
            return "%s"
        else:
            return "?"

    def _convert_value(self, value):
        """转换值类型以适应数据库"""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (dict, list)):
            return json.dumps(value)
        return value

    def connect(self):
        """显式连接数据库（用于需要保持连接的情况）"""
        if not self._connection:
            self._connection = self.db_manager.pool.get_connection(self.db_manager)
            self._cursor = self._connection.cursor()

    def disconnect(self):
        """断开数据库连接"""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._connection:
            if not self._in_transaction:
                self.db_manager.pool.return_connection(self._connection)
            self._connection = None

    def select_database(self, database_name: str) -> QueryResult:
        """切换/选择数据库"""
        try:
            self.disconnect()
            self.db_manager.database = database_name
            return QueryResult(
                success=True,
                message=f"已切换到数据库: {database_name}"
            )
        except Exception as e:
            return QueryResult(
                success=False,
                message=f"切换数据库失败: {str(e)}"
            )

    def execute_raw_sql(self, sql: str, params: tuple = None) -> QueryResult:
        """执行原始SQL语句"""
        try:
            with self.connection_context() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                if sql.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                    data = [dict(zip(column_names, row)) for row in rows]
                    return QueryResult(
                        success=True,
                        data=data,
                        message="查询执行成功",
                        rowcount=len(data)
                    )
                else:
                    return QueryResult(
                        success=True,
                        message="SQL执行成功",
                        rowcount=cursor.rowcount,
                        lastrowid=cursor.lastrowid
                    )
        except Exception as e:
            logger.error(f"执行SQL失败: {e}")
            return QueryResult(
                success=False,
                message=f"执行SQL失败: {str(e)}"
            )

    def create_table(self, table_name: str, columns: dict, if_not_exists: bool = True) -> QueryResult:
        """创建表"""
        try:
            with self.connection_context() as cursor:
                # 构建列定义
                column_defs = []
                for col_name, col_def in columns.items():
                    # PostgreSQL的自增主键需要特殊处理
                    if self.db_manager.db_type == DatabaseType.POSTGRESQL and "AUTOINCREMENT" in col_def.upper():
                        col_def = col_def.upper().replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
                    column_defs.append(f"{col_name} {col_def}")

                # 构建创建表的SQL语句
                if_not_exists_clause = "IF NOT EXISTS " if if_not_exists else ""
                sql = f"CREATE TABLE {if_not_exists_clause}{table_name} ({', '.join(column_defs)})"

                cursor.execute(sql)
                return QueryResult(
                    success=True,
                    message=f"表 {table_name} 创建成功"
                )
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            return QueryResult(
                success=False,
                message=f"创建表失败: {str(e)}"
            )

    def drop_table(self, table_name: str, if_exists: bool = True) -> QueryResult:
        """删除表"""
        try:
            with self.connection_context() as cursor:
                if_exists_clause = "IF EXISTS " if if_exists else ""
                sql = f"DROP TABLE {if_exists_clause}{table_name}"
                cursor.execute(sql)
                return QueryResult(
                    success=True,
                    message=f"表 {table_name} 删除成功"
                )
        except Exception as e:
            logger.error(f"删除表失败: {e}")
            return QueryResult(
                success=False,
                message=f"删除表失败: {str(e)}"
            )

    def truncate_table(self, table_name: str) -> QueryResult:
        """清空表数据"""
        try:
            with self.connection_context() as cursor:
                sql = f"TRUNCATE TABLE {table_name}"
                cursor.execute(sql)
                return QueryResult(
                    success=True,
                    message=f"表 {table_name} 数据已清空"
                )
        except Exception as e:
            logger.error(f"清空表失败: {e}")
            return QueryResult(
                success=False,
                message=f"清空表失败: {str(e)}"
            )

    def insert(self, table_name: str, data: Union[Dict, List[Dict]],
               ignore_duplicate: bool = False, return_id: bool = False) -> QueryResult:
        """插入数据"""
        try:
            with self.connection_context() as cursor:
                if isinstance(data, dict):
                    data_list = [data]
                else:
                    data_list = data

                placeholder = self._get_placeholder()
                results = []

                for item in data_list:
                    # 转换值类型
                    item = {k: self._convert_value(v) for k, v in item.items()}

                    # 构建插入语句
                    columns = ', '.join(item.keys())
                    placeholders = ', '.join([placeholder for _ in item])

                    # 处理重复数据
                    insert_keyword = "INSERT"
                    if ignore_duplicate:
                        if self.db_manager.db_type == DatabaseType.MYSQL:
                            insert_keyword = "INSERT IGNORE"
                        elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                            # PostgreSQL使用ON CONFLICT DO NOTHING
                            # 需要知道冲突键，这里假设是主键冲突
                            insert_keyword = "INSERT"

                    sql = f"{insert_keyword} INTO {table_name} ({columns}) VALUES ({placeholders})"

                    # PostgreSQL的特殊处理
                    if ignore_duplicate and self.db_manager.db_type == DatabaseType.POSTGRESQL:
                        # 假设冲突发生在id列，实际使用时可能需要指定
                        sql += " ON CONFLICT (id) DO NOTHING"

                    cursor.execute(sql, list(item.values()))

                    if return_id and cursor.lastrowid:
                        results.append(cursor.lastrowid)

                return QueryResult(
                    success=True,
                    data=results if return_id else [],
                    message=f"成功插入 {len(data_list)} 条数据",
                    rowcount=len(data_list),
                    lastrowid=cursor.lastrowid if cursor.lastrowid else None
                )
        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            return QueryResult(
                success=False,
                message=f"插入数据失败: {str(e)}"
            )

    def select(
            self,
            table_name: str,
            columns: List[str] = None,
            conditions: Dict = None,
            order_by: List[str] = None,
            limit: int = None,
            offset: int = None,
            distinct: bool = False,
            group_by: List[str] = None,
            having: Dict = None,
            bool_dict: bool = False
    ) -> QueryResult:
        """查询数据"""
        try:
            with self.connection_context() as cursor:
                # 构建SELECT子句
                if columns:
                    if distinct:
                        columns_clause = "DISTINCT " + ', '.join(columns)
                    else:
                        columns_clause = ', '.join(columns)
                else:
                    columns_clause = "*"

                # 构建基础查询
                sql = f"SELECT {columns_clause} FROM {table_name}"
                values = []

                # 构建WHERE子句
                if conditions:
                    where_clauses = []
                    for key, value in conditions.items():
                        if isinstance(value, dict):
                            # 处理比较操作符
                            for op, val in value.items():
                                where_clauses.append(f"{key} {op} {self._get_placeholder()}")
                                values.append(self._convert_value(val))
                        else:
                            # 等值条件
                            where_clauses.append(f"{key} = {self._get_placeholder()}")
                            values.append(self._convert_value(value))

                    if where_clauses:
                        sql += f" WHERE {' AND '.join(where_clauses)}"

                # 构建GROUP BY子句
                if group_by:
                    sql += f" GROUP BY {', '.join(group_by)}"

                # 构建HAVING子句
                if having:
                    having_clauses = []
                    for key, value in having.items():
                        if isinstance(value, dict):
                            for op, val in value.items():
                                having_clauses.append(f"{key} {op} {self._get_placeholder()}")
                                values.append(self._convert_value(val))
                        else:
                            having_clauses.append(f"{key} = {self._get_placeholder()}")
                            values.append(self._convert_value(value))

                    if having_clauses:
                        sql += f" HAVING {' AND '.join(having_clauses)}"

                # 构建ORDER BY子句
                if order_by:
                    sql += f" ORDER BY {', '.join(order_by)}"

                # 构建LIMIT和OFFSET子句
                if limit is not None:
                    sql += f" LIMIT {limit}"

                if offset is not None:
                    sql += f" OFFSET {offset}"

                cursor.execute(sql, values)

                # 获取结果
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []

                # 转换为字典列表
                data = []
                for row in rows:
                    data.append(dict(zip(column_names, row)))

                # 根据bool_dict参数决定返回格式
                if bool_dict and not data:
                    return QueryResult(
                        success=False,
                        message="未找到匹配的数据"
                    )

                return QueryResult(
                    success=True,
                    data=data,
                    message=f"查询成功，找到 {len(data)} 条数据",
                    rowcount=len(data)
                )
        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            return QueryResult(
                success=False,
                message=f"查询数据失败: {str(e)}"
            )

    def update(self, table_name: str, data: Dict, conditions: Dict = None) -> QueryResult:
        """更新数据"""
        try:
            with self.connection_context() as cursor:
                # 转换值类型
                data = {k: self._convert_value(v) for k, v in data.items()}

                # 构建更新语句
                placeholder = self._get_placeholder()
                set_clauses = [f"{key} = {placeholder}" for key in data.keys()]
                sql = f"UPDATE {table_name} SET {', '.join(set_clauses)}"

                values = list(data.values())

                # 构建WHERE子句
                if conditions:
                    where_clauses = []
                    for key, value in conditions.items():
                        if isinstance(value, dict):
                            for op, val in value.items():
                                where_clauses.append(f"{key} {op} {placeholder}")
                                values.append(self._convert_value(val))
                        else:
                            where_clauses.append(f"{key} = {placeholder}")
                            values.append(self._convert_value(value))

                    if where_clauses:
                        sql += f" WHERE {' AND '.join(where_clauses)}"

                cursor.execute(sql, values)

                return QueryResult(
                    success=True,
                    message=f"成功更新 {cursor.rowcount} 条数据",
                    rowcount=cursor.rowcount
                )
        except Exception as e:
            logger.error(f"更新数据失败: {e}")
            return QueryResult(
                success=False,
                message=f"更新数据失败: {str(e)}"
            )

    def delete(self, table_name: str, conditions: Dict = None) -> QueryResult:
        """删除数据"""
        try:
            with self.connection_context() as cursor:
                sql = f"DELETE FROM {table_name}"
                values = []

                # 构建WHERE子句
                if conditions:
                    where_clauses = []
                    for key, value in conditions.items():
                        if isinstance(value, dict):
                            for op, val in value.items():
                                where_clauses.append(f"{key} {op} {self._get_placeholder()}")
                                values.append(self._convert_value(val))
                        else:
                            where_clauses.append(f"{key} = {self._get_placeholder()}")
                            values.append(self._convert_value(value))

                    if where_clauses:
                        sql += f" WHERE {' AND '.join(where_clauses)}"

                cursor.execute(sql, values)

                return QueryResult(
                    success=True,
                    message=f"成功删除 {cursor.rowcount} 条数据",
                    rowcount=cursor.rowcount
                )
        except Exception as e:
            logger.error(f"删除数据失败: {e}")
            return QueryResult(
                success=False,
                message=f"删除数据失败: {str(e)}"
            )

    def get_table_info(self, table_name: str) -> QueryResult:
        """获取表结构信息"""
        try:
            with self.connection_context() as cursor:
                if self.db_manager.db_type == DatabaseType.SQLITE:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    rows = cursor.fetchall()
                    column_names = ["cid", "name", "type", "notnull", "dflt_value", "pk"]

                elif self.db_manager.db_type == DatabaseType.MYSQL:
                    cursor.execute(f"DESCRIBE {table_name}")
                    rows = cursor.fetchall()
                    column_names = ["Field", "Type", "Null", "Key", "Default", "Extra"]

                elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    cursor.execute(f"""
                        SELECT 
                            column_name, 
                            data_type, 
                            is_nullable,
                            column_default,
                            character_maximum_length,
                            numeric_precision,
                            numeric_scale
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}'
                        ORDER BY ordinal_position
                    """)
                    rows = cursor.fetchall()
                    column_names = [
                        "column_name", "data_type", "is_nullable", "column_default",
                        "character_maximum_length", "numeric_precision", "numeric_scale"
                    ]
                else:
                    return QueryResult(
                        success=False,
                        message="不支持的数据库类型"
                    )

                # 构建结果
                data = []
                for row in rows:
                    data.append(dict(zip(column_names, row)))

                return QueryResult(
                    success=True,
                    data=data,
                    message=f"表 {table_name} 结构信息获取成功"
                )
        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
            return QueryResult(
                success=False,
                message=f"获取表信息失败: {str(e)}"
            )

    def get_tables(self) -> QueryResult:
        """获取所有表名"""
        try:
            with self.connection_context() as cursor:
                if self.db_manager.db_type == DatabaseType.SQLITE:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]

                elif self.db_manager.db_type == DatabaseType.MYSQL:
                    cursor.execute("SHOW TABLES")
                    tables = [row[0] for row in cursor.fetchall()]

                elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                else:
                    return QueryResult(
                        success=False,
                        message="不支持的数据库类型"
                    )

                return QueryResult(
                    success=True,
                    data=[{"table_name": table} for table in tables],
                    message=f"获取到 {len(tables)} 个表"
                )
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return QueryResult(
                success=False,
                message=f"获取表列表失败: {str(e)}"
            )

    def count(self, table_name: str, conditions: Dict = None) -> QueryResult:
        """统计记录数"""
        try:
            with self.connection_context() as cursor:
                sql = f"SELECT COUNT(*) as count FROM {table_name}"
                values = []

                if conditions:
                    where_clauses = []
                    for key, value in conditions.items():
                        if isinstance(value, dict):
                            for op, val in value.items():
                                where_clauses.append(f"{key} {op} {self._get_placeholder()}")
                                values.append(self._convert_value(val))
                        else:
                            where_clauses.append(f"{key} = {self._get_placeholder()}")
                            values.append(self._convert_value(value))

                    if where_clauses:
                        sql += f" WHERE {' AND '.join(where_clauses)}"

                cursor.execute(sql, values)
                count = cursor.fetchone()[0]

                return QueryResult(
                    success=True,
                    data=[{"count": count}],
                    message=f"表 {table_name} 共有 {count} 条记录"
                )
        except Exception as e:
            logger.error(f"统计记录数失败: {e}")
            return QueryResult(
                success=False,
                message=f"统计记录数失败: {str(e)}"
            )

    def join(
            self,
            table1: str,
            table2: str,
            join_type: str = "INNER",
            on_condition: str = None,
            columns: List[str] = None,
            conditions: Dict = None,
            order_by: List[str] = None,
            limit: int = None
    ) -> QueryResult:
        """连接查询"""
        try:
            with self.connection_context() as cursor:
                # 构建SELECT子句
                if columns:
                    columns_clause = ', '.join(columns)
                else:
                    columns_clause = f"{table1}.*, {table2}.*"

                # 构建JOIN语句
                join_type = join_type.upper()
                if join_type not in ["INNER", "LEFT", "RIGHT", "FULL"]:
                    join_type = "INNER"

                sql = f"SELECT {columns_clause} FROM {table1} {join_type} JOIN {table2}"

                if on_condition:
                    sql += f" ON {on_condition}"

                values = []

                # 构建WHERE子句
                if conditions:
                    where_clauses = []
                    for key, value in conditions.items():
                        if isinstance(value, dict):
                            for op, val in value.items():
                                where_clauses.append(f"{key} {op} {self._get_placeholder()}")
                                values.append(self._convert_value(val))
                        else:
                            where_clauses.append(f"{key} = {self._get_placeholder()}")
                            values.append(self._convert_value(value))

                    if where_clauses:
                        sql += f" WHERE {' AND '.join(where_clauses)}"

                # 构建ORDER BY子句
                if order_by:
                    sql += f" ORDER BY {', '.join(order_by)}"

                # 构建LIMIT子句
                if limit is not None:
                    sql += f" LIMIT {limit}"

                cursor.execute(sql, values)

                # 获取结果
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []

                # 转换为字典列表
                data = []
                for row in rows:
                    data.append(dict(zip(column_names, row)))

                return QueryResult(
                    success=True,
                    data=data,
                    message=f"连接查询成功，找到 {len(data)} 条数据",
                    rowcount=len(data)
                )
        except Exception as e:
            logger.error(f"连接查询失败: {e}")
            return QueryResult(
                success=False,
                message=f"连接查询失败: {str(e)}"
            )

    def bulk_insert(self, table_name: str, data_list: List[Dict]) -> QueryResult:
        """批量插入数据（优化性能）"""
        if not data_list:
            return QueryResult(success=True, message="没有数据需要插入", rowcount=0)

        try:
            with self.connection_context() as cursor:
                # 转换值类型
                converted_data = []
                for item in data_list:
                    converted_data.append({k: self._convert_value(v) for k, v in item.items()})

                # 获取列名
                first_item = converted_data[0]
                columns = ', '.join(first_item.keys())

                # 构建占位符
                placeholder = self._get_placeholder()
                placeholders = ', '.join([placeholder for _ in first_item])

                # 构建SQL
                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

                # 准备数据
                values = []
                for item in converted_data:
                    values.append(tuple(item.values()))

                # 执行批量插入
                if self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    # PostgreSQL使用executemany
                    cursor.executemany(sql, values)
                else:
                    # MySQL和SQLite支持executemany
                    cursor.executemany(sql, values)

                return QueryResult(
                    success=True,
                    message=f"批量插入 {len(data_list)} 条数据成功",
                    rowcount=len(data_list)
                )
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            return QueryResult(
                success=False,
                message=f"批量插入失败: {str(e)}"
            )

    def create_user(self, username: str, password: str,
                    host: str = "localhost") -> QueryResult:
        """创建用户"""
        try:
            with self.connection_context() as cursor:
                if self.db_manager.db_type == DatabaseType.MYSQL:
                    cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")
                    return QueryResult(
                        success=True,
                        message=f"MySQL用户 {username} 创建成功"
                    )

                elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    cursor.execute(f"CREATE USER {username} WITH PASSWORD '{password}'")
                    return QueryResult(
                        success=True,
                        message=f"PostgreSQL用户 {username} 创建成功"
                    )

                else:
                    return QueryResult(
                        success=False,
                        message="SQLite不支持用户管理"
                    )
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return QueryResult(
                success=False,
                message=f"创建用户失败: {str(e)}"
            )

    def drop_user(self, username: str, host: str = "localhost") -> QueryResult:
        """删除用户"""
        try:
            with self.connection_context() as cursor:
                if self.db_manager.db_type == DatabaseType.MYSQL:
                    cursor.execute(f"DROP USER '{username}'@'{host}'")
                    return QueryResult(
                        success=True,
                        message=f"MySQL用户 {username} 删除成功"
                    )

                elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    cursor.execute(f"DROP USER {username}")
                    return QueryResult(
                        success=True,
                        message=f"PostgreSQL用户 {username} 删除成功"
                    )

                else:
                    return QueryResult(
                        success=False,
                        message="SQLite不支持用户管理"
                    )
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return QueryResult(
                success=False,
                message=f"删除用户失败: {str(e)}"
            )

    def change_password(self, username: str, new_password: str,
                        host: str = "localhost") -> QueryResult:
        """修改用户密码"""
        try:
            with self.connection_context() as cursor:
                if self.db_manager.db_type == DatabaseType.MYSQL:
                    cursor.execute(f"ALTER USER '{username}'@'{host}' IDENTIFIED BY '{new_password}'")
                    return QueryResult(
                        success=True,
                        message=f"MySQL用户 {username} 密码修改成功"
                    )

                elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    cursor.execute(f"ALTER USER {username} WITH PASSWORD '{new_password}'")
                    return QueryResult(
                        success=True,
                        message=f"PostgreSQL用户 {username} 密码修改成功"
                    )

                else:
                    return QueryResult(
                        success=False,
                        message="SQLite不支持用户管理"
                    )
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            return QueryResult(
                success=False,
                message=f"修改密码失败: {str(e)}"
            )

    def get_user_privileges(self, username: str, host: str = "localhost") -> QueryResult:
        """查询用户权限"""
        try:
            with self.connection_context() as cursor:
                if self.db_manager.db_type == DatabaseType.MYSQL:
                    cursor.execute(f"SHOW GRANTS FOR '{username}'@'{host}'")
                    rows = cursor.fetchall()
                    privileges = [row[0] for row in rows]

                    return QueryResult(
                        success=True,
                        data=[{"privileges": privileges}],
                        message=f"MySQL用户 {username} 权限查询成功"
                    )

                elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    cursor.execute(f"""
                        SELECT rolname, rolcreatedb, rolcreaterole, rolsuper 
                        FROM pg_roles 
                        WHERE rolname = '{username}'
                    """)
                    rows = cursor.fetchall()
                    column_names = ["rolname", "rolcreatedb", "rolcreaterole", "rolsuper"]
                    data = []
                    for row in rows:
                        data.append(dict(zip(column_names, row)))

                    return QueryResult(
                        success=True,
                        data=data,
                        message=f"PostgreSQL用户 {username} 权限查询成功"
                    )

                else:
                    return QueryResult(
                        success=False,
                        message="SQLite不支持用户管理"
                    )
        except Exception as e:
            logger.error(f"查询用户权限失败: {e}")
            return QueryResult(
                success=False,
                message=f"查询用户权限失败: {str(e)}"
            )

    def grant_privileges(self, username: str, privileges: List[str],
                         database: str = "*", table: str = "*",
                         host: str = "localhost") -> QueryResult:
        """授予用户权限"""
        try:
            with self.connection_context() as cursor:
                if self.db_manager.db_type == DatabaseType.MYSQL:
                    priv_str = ', '.join(privileges)
                    cursor.execute(f"GRANT {priv_str} ON {database}.{table} TO '{username}'@'{host}'")
                    cursor.execute("FLUSH PRIVILEGES")

                    return QueryResult(
                        success=True,
                        message=f"已为MySQL用户 {username} 授予权限: {priv_str}"
                    )

                elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    # PostgreSQL权限授予需要更复杂的处理
                    return QueryResult(
                        success=False,
                        message="PostgreSQL权限授予功能待实现"
                    )

                else:
                    return QueryResult(
                        success=False,
                        message="SQLite不支持用户权限管理"
                    )
        except Exception as e:
            logger.error(f"授予权限失败: {e}")
            return QueryResult(
                success=False,
                message=f"授予权限失败: {str(e)}"
            )

