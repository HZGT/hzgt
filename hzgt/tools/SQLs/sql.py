from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union

from sqlalchemy import (
    create_engine, MetaData, Column, text, inspect,
    and_, select, update, delete, insert, Table,
    Integer, String, Text, Float, DateTime, Boolean, DECIMAL,
    Engine
)
from sqlalchemy.dialects.mysql import TINYINT, MEDIUMINT, BIGINT
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from hzgt import set_log

# 设置日志
logger = set_log("testSQLs")

Base = declarative_base()


class DatabaseType(Enum):
    """数据库类型枚举"""
    MYSQL = "mysql"
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


@dataclass
class QueryResult:
    """查询结果封装类"""
    success: bool
    data: List[Dict] = None
    message: str = ""
    rowcount: int = 0

    def __post_init__(self):
        if self.data is None:
            self.data = []


class DatabaseManager:
    """数据库管理器，负责管理数据库连接参数和引擎创建"""

    def __init__(
            self,
            db_type: DatabaseType,
            host: str = None,
            port: int = None,
            user: str = None,
            passwd: str = None,
            database: str = None,
            charset: str = "utf8",
            **kwargs
    ):
        """
        初始化数据库管理器

        Args:
            db_type: 数据库类型
            host: 主机地址（SQLite不需要）
            port: 端口（SQLite不需要）
            user: 用户名（SQLite不需要）
            passwd: 密码（SQLite不需要）
            database: 数据库名（SQLite为文件路径）
            charset: 字符集
            **kwargs: 其他数据库特定参数
        """
        self.db_type = db_type
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.database = database
        self.charset = charset
        self.kwargs = kwargs

        # SQLAlchemy引擎和会话
        self.engine: Optional[Engine] = None
        self.SessionLocal = None
        self.Base = Base

    def create_connection_string(self) -> str:
        """创建数据库连接字符串"""
        if self.db_type == DatabaseType.SQLITE:
            # SQLite连接字符串
            if self.database.startswith(":memory:"):
                return f"sqlite:///{self.database}"
            return f"sqlite:///{self.database}"

        elif self.db_type == DatabaseType.MYSQL:
            # MySQL连接字符串
            return (
                f"mysql+pymysql://{self.user}:{self.passwd}@"
                f"{self.host}:{self.port}/{self.database}?"
                f"charset={self.charset}"
            )

        elif self.db_type == DatabaseType.POSTGRESQL:
            # PostgreSQL连接字符串
            return (
                f"postgresql://{self.user}:{self.passwd}@"
                f"{self.host}:{self.port}/{self.database}"
            )

        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

    def get_engine(self) -> Engine:
        """获取或创建数据库引擎"""
        if self.engine is None:
            connection_string = self.create_connection_string()
            try:
                # 根据不同数据库设置不同参数
                engine_kwargs = {}

                if self.db_type == DatabaseType.SQLITE:
                    # SQLite特定配置
                    engine_kwargs.update({
                        "connect_args": {"check_same_thread": False},
                        "pool_pre_ping": False,
                        "echo": False  # 设置为True可查看SQL语句
                    })
                elif self.db_type == DatabaseType.MYSQL:
                    # MySQL特定配置
                    engine_kwargs.update({
                        "pool_pre_ping": True,
                        "pool_recycle": 3600,
                        "echo": False
                    })
                elif self.db_type == DatabaseType.POSTGRESQL:
                    # PostgreSQL特定配置
                    engine_kwargs.update({
                        "pool_pre_ping": True,
                        "pool_recycle": 3600,
                        "echo": False
                    })

                # 合并额外参数
                engine_kwargs.update(self.kwargs)

                self.engine = create_engine(
                    connection_string,
                    **engine_kwargs
                )

                # 创建会话工厂
                self.SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )

                logger.info(f"数据库引擎创建成功: {self.db_type.value}")

            except Exception as e:
                logger.error(f"创建数据库引擎失败: {e}")
                raise

        return self.engine

    def connect(self):
        """显式连接数据库"""
        return self.get_engine()

    def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
            logger.info("数据库连接已关闭")

    def create_all_tables(self):
        """创建所有已定义的模型表"""
        try:
            self.Base.metadata.create_all(bind=self.engine)
            logger.info("所有表创建成功")
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            raise


class DynamicTable:
    """动态表模型基类"""
    __table_args__ = {'extend_existing': True}

    @classmethod
    def create_dynamic_model(cls, table_name, columns_dict, metadata):
        """动态创建表模型"""
        attrs = {'__tablename__': table_name, '__table_args__': {'extend_existing': True}}

        # 将列定义字典转换为SQLAlchemy列对象
        for col_name, col_def in columns_dict.items():
            attrs[col_name] = cls._parse_column_definition(col_def)

        # 动态创建模型类
        return type(f'Dynamic{table_name.capitalize()}', (Base,), attrs)

    @staticmethod
    def _parse_column_definition(col_def: str):
        """解析列定义字符串为SQLAlchemy列对象"""
        col_def_lower = col_def.lower()

        # 解析约束
        constraints = {}
        if 'primary key' in col_def_lower:
            constraints['primary_key'] = True
        if 'autoincrement' in col_def_lower or 'auto_increment' in col_def_lower:
            constraints['autoincrement'] = True
        if 'not null' in col_def_lower:
            constraints['nullable'] = False
        if 'unique' in col_def_lower:
            constraints['unique'] = True

        # 解析类型
        if 'int' in col_def_lower:
            if 'bigint' in col_def_lower:
                return Column(BIGINT, **constraints)
            elif 'mediumint' in col_def_lower:
                return Column(MEDIUMINT, **constraints)
            elif 'tinyint' in col_def_lower:
                return Column(TINYINT, **constraints)
            else:
                return Column(Integer, **constraints)
        elif 'varchar' in col_def_lower or 'char' in col_def_lower:
            # 提取长度
            import re
            match = re.search(r'\((\d+)\)', col_def)
            length = int(match.group(1)) if match else 255
            return Column(String(length), **constraints)
        elif 'text' in col_def_lower:
            return Column(Text, **constraints)
        elif 'decimal' in col_def_lower or 'numeric' in col_def_lower:
            # 提取精度和小数位
            import re
            match = re.search(r'\((\d+),\s*(\d+)\)', col_def)
            if match:
                precision = int(match.group(1))
                scale = int(match.group(2))
                return Column(DECIMAL(precision=precision, scale=scale), **constraints)
            else:
                return Column(DECIMAL, **constraints)
        elif 'float' in col_def_lower or 'double' in col_def_lower:
            return Column(Float, **constraints)
        elif 'datetime' in col_def_lower:
            return Column(DateTime, **constraints)
        elif 'timestamp' in col_def_lower:
            return Column(DateTime, **constraints)
        elif 'bool' in col_def_lower or 'boolean' in col_def_lower:
            return Column(Boolean, **constraints)
        elif 'json' in col_def_lower:
            return Column(JSONB if 'postgresql' in str(col_def).lower() else Text, **constraints)
        else:
            # 默认使用Text类型
            return Column(Text, **constraints)


class SQLop:
    """SQL操作类，提供各种数据库操作"""

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化SQL操作类

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self.engine = db_manager.get_engine()
        self.SessionLocal = db_manager.SessionLocal
        self.metadata = MetaData()
        self.dynamic_models = {}  # 存储动态创建的模型

    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()

    def get_table(self, table_name: str):
        """获取表对象，如果不存在则返回None"""
        try:
            # 先尝试从动态模型中获取
            if table_name in self.dynamic_models:
                return self.dynamic_models[table_name].__table__

            # 尝试从元数据中获取
            return Table(table_name, self.metadata, autoload_with=self.engine)
        except:
            return None

    def _get_model_class(self, table_name: str):
        """获取模型类，如果不存在则创建动态模型"""
        if table_name in self.dynamic_models:
            return self.dynamic_models[table_name]
        return None

    # ==================== 数据库操作 ====================

    def create_database(self, database_name: str) -> QueryResult:
        """创建数据库（MySQL/PostgreSQL支持）"""
        if self.db_manager.db_type == DatabaseType.SQLITE:
            return QueryResult(
                success=False,
                message="SQLite不支持动态创建数据库"
            )

        try:
            # 临时连接到无数据库的实例
            temp_engine = None
            if self.db_manager.db_type == DatabaseType.MYSQL:
                temp_engine = create_engine(
                    f"mysql+pymysql://{self.db_manager.user}:{self.db_manager.passwd}@"
                    f"{self.db_manager.host}:{self.db_manager.port}/"
                )
                with temp_engine.connect() as conn:
                    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {database_name}"))

            elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                # PostgreSQL需要不同的处理
                temp_engine = create_engine(
                    f"postgresql://{self.db_manager.user}:{self.db_manager.passwd}@"
                    f"{self.db_manager.host}:{self.db_manager.port}/postgres"
                )
                with temp_engine.connect() as conn:
                    conn.execute(text(f"CREATE DATABASE {database_name}"))

            if temp_engine:
                temp_engine.dispose()

            return QueryResult(
                success=True,
                message=f"数据库 {database_name} 创建成功"
            )

        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            return QueryResult(
                success=False,
                message=f"创建数据库失败: {str(e)}"
            )

    def select_database(self, database: str) -> QueryResult:
        """切换/选择数据库"""
        if self.db_manager.db_type == DatabaseType.SQLITE:
            # SQLite: 关闭当前连接，重新连接到新文件
            old_db = self.db_manager.database
            self.db_manager.database = database
            self.db_manager.disconnect()
            self.engine = self.db_manager.get_engine()
            self.SessionLocal = self.db_manager.SessionLocal
            self.metadata = MetaData()
            self.dynamic_models.clear()
            return QueryResult(
                success=True,
                message=f"SQLite数据库已切换: {old_db} -> {database}"
            )
        else:
            # MySQL/PostgreSQL: 更新连接字符串重新连接
            old_db = self.db_manager.database
            self.db_manager.database = database
            self.db_manager.disconnect()
            self.engine = self.db_manager.get_engine()
            self.SessionLocal = self.db_manager.SessionLocal
            self.metadata = MetaData()
            self.dynamic_models.clear()
            return QueryResult(
                success=True,
                message=f"数据库已切换到: {old_db} -> {database}"
            )

    # ==================== 表操作 ====================

    def create_table(
            self,
            table_name: str,
            columns: Dict[str, str],
            if_not_exists: bool = True
    ) -> QueryResult:
        """创建表"""
        try:
            # 检查表是否已存在
            inspector = inspect(self.engine)
            if if_not_exists and inspector.has_table(table_name):
                return QueryResult(
                    success=True,
                    message=f"表 {table_name} 已存在，跳过创建"
                )

            # 动态创建模型类
            dynamic_model = DynamicTable.create_dynamic_model(table_name, columns, self.metadata)

            # 创建表
            dynamic_model.__table__.create(bind=self.engine, checkfirst=if_not_exists)

            # 存储动态模型以供后续使用
            self.dynamic_models[table_name] = dynamic_model

            logger.info(f"表 {table_name} 创建成功")
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
            # 检查表是否存在
            inspector = inspect(self.engine)
            if if_exists and not inspector.has_table(table_name):
                return QueryResult(
                    success=True,
                    message=f"表 {table_name} 不存在，无需删除"
                )

            # 获取表对象
            table_obj = self.get_table(table_name)
            if table_obj:
                table_obj.drop(bind=self.engine)

            # 从动态模型中移除
            if table_name in self.dynamic_models:
                del self.dynamic_models[table_name]

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

    def get_table_info(self, table_name: str) -> QueryResult:
        """获取表信息"""
        try:
            inspector = inspect(self.engine)

            if not inspector.has_table(table_name):
                return QueryResult(
                    success=False,
                    message=f"表 {table_name} 不存在"
                )

            # 获取列信息
            columns = inspector.get_columns(table_name)
            column_info = []

            for col in columns:
                column_info.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col.get("default"),
                    "primary_key": col.get("primary_key", False),
                    "autoincrement": col.get("autoincrement", False)
                })

            # 获取主键信息
            primary_keys = inspector.get_pk_constraint(table_name)

            # 获取外键信息
            foreign_keys = inspector.get_foreign_keys(table_name)

            # 获取索引信息
            indexes = inspector.get_indexes(table_name)

            table_info = {
                "table_name": table_name,
                "columns": column_info,
                "primary_key": primary_keys.get("constrained_columns", []),
                "foreign_keys": foreign_keys,
                "indexes": indexes
            }

            return QueryResult(
                success=True,
                data=[table_info],
                message=f"表 {table_name} 信息获取成功"
            )

        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
            return QueryResult(
                success=False,
                message=f"获取表信息失败: {str(e)}"
            )

    def rename_table(self, old_name: str, new_name: str) -> QueryResult:
        """重命名表"""
        try:
            inspector = inspect(self.engine)
            if not inspector.has_table(old_name):
                return QueryResult(
                    success=False,
                    message=f"表 {old_name} 不存在"
                )

            if inspector.has_table(new_name):
                return QueryResult(
                    success=False,
                    message=f"表 {new_name} 已存在"
                )

            with self.engine.begin() as conn:
                if self.db_manager.db_type == DatabaseType.SQLITE:
                    conn.execute(text(f"ALTER TABLE {old_name} RENAME TO {new_name}"))
                elif self.db_manager.db_type == DatabaseType.MYSQL:
                    conn.execute(text(f"RENAME TABLE {old_name} TO {new_name}"))
                elif self.db_manager.db_type == DatabaseType.POSTGRESQL:
                    conn.execute(text(f"ALTER TABLE {old_name} RENAME TO {new_name}"))

            # 更新动态模型
            if old_name in self.dynamic_models:
                model = self.dynamic_models.pop(old_name)
                model.__tablename__ = new_name
                self.dynamic_models[new_name] = model

            return QueryResult(
                success=True,
                message=f"表重命名成功: {old_name} -> {new_name}"
            )

        except Exception as e:
            logger.error(f"重命名表失败: {e}")
            return QueryResult(
                success=False,
                message=f"重命名表失败: {str(e)}"
            )

    # ==================== 数据操作 ====================

    def _build_where_clause(self, table, conditions: Dict):
        """构建WHERE子句"""
        where_clauses = []

        for column, condition in conditions.items():
            if hasattr(table.c, column):
                col = getattr(table.c, column)

                if isinstance(condition, dict):
                    for operator, value in condition.items():
                        operator = operator.lower()

                        if operator == "=":
                            where_clauses.append(col == value)
                        elif operator == "!=" or operator == "<>":
                            where_clauses.append(col != value)
                        elif operator == ">":
                            where_clauses.append(col > value)
                        elif operator == ">=":
                            where_clauses.append(col >= value)
                        elif operator == "<":
                            where_clauses.append(col < value)
                        elif operator == "<=":
                            where_clauses.append(col <= value)
                        elif operator == "like":
                            where_clauses.append(col.like(value))
                        elif operator == "in":
                            where_clauses.append(col.in_(value))
                        elif operator == "between":
                            if isinstance(value, (list, tuple)) and len(value) == 2:
                                where_clauses.append(col.between(value[0], value[1]))
                else:
                    # 默认为等于
                    where_clauses.append(col == condition)

        return where_clauses

    def insert(self, table_name: str, data: Union[Dict, List[Dict]]) -> QueryResult:
        """插入数据"""
        try:
            with self.get_session() as session:
                table = self.get_table(table_name)
                if table is None:
                    return QueryResult(
                        success=False,
                        message=f"表 {table_name} 不存在"
                    )

                if isinstance(data, dict):
                    data = [data]

                # 执行插入
                stmt = insert(table).values(data)
                result = session.execute(stmt)

                # 尝试获取插入的ID
                inserted_ids = []
                if result.inserted_primary_key:
                    if isinstance(result.inserted_primary_key, tuple):
                        inserted_ids = list(result.inserted_primary_key)
                    elif result.inserted_primary_key:
                        inserted_ids = [result.inserted_primary_key]

                return QueryResult(
                    success=True,
                    data=[{"inserted_ids": inserted_ids, "rowcount": len(data)}],
                    message=f"成功插入 {len(data)} 条数据",
                    rowcount=len(data)
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
            bool_dict: bool = False
    ) -> QueryResult:
        """查询数据"""
        try:
            with self.get_session() as session:
                table = self.get_table(table_name)
                if table is None:
                    if bool_dict:
                        return QueryResult(
                            success=False,
                            message=f"表 {table_name} 不存在"
                        )
                    else:
                        return QueryResult(
                            success=True,
                            data=[],
                            message=f"表 {table_name} 不存在"
                        )

                # 构建查询
                if columns:
                    # 选择特定列
                    selected_columns = [getattr(table.c, col) for col in columns if hasattr(table.c, col)]
                    if not selected_columns:
                        selected_columns = [table]
                    stmt = select(*selected_columns)
                else:
                    stmt = select(table)

                # 添加WHERE条件
                if conditions:
                    where_clauses = self._build_where_clause(table, conditions)
                    if where_clauses:
                        stmt = stmt.where(and_(*where_clauses))

                # 添加ORDER BY
                if order_by:
                    order_clauses = []
                    for order in order_by:
                        if order.startswith('-'):
                            col_name = order[1:]
                            if hasattr(table.c, col_name):
                                order_clauses.append(getattr(table.c, col_name).desc())
                        else:
                            if hasattr(table.c, order):
                                order_clauses.append(getattr(table.c, order).asc())
                    if order_clauses:
                        stmt = stmt.order_by(*order_clauses)

                # 添加LIMIT和OFFSET
                if limit is not None:
                    stmt = stmt.limit(limit)
                if offset is not None:
                    stmt = stmt.offset(offset)

                # 执行查询
                result = session.execute(stmt)

                # 转换为字典列表
                data = []
                for row in result:
                    if columns:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            row_dict[col] = row[i]
                    else:
                        row_dict = dict(row._mapping)
                    data.append(row_dict)

                # 如果是bool_dict模式且没有数据，返回失败
                if bool_dict and not data:
                    return QueryResult(
                        success=False,
                        data=[],
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
            with self.get_session() as session:
                table = self.get_table(table_name)
                if table is None:
                    return QueryResult(
                        success=False,
                        message=f"表 {table_name} 不存在"
                    )

                # 构建UPDATE语句
                stmt = update(table)

                # 添加SET子句
                for key, value in data.items():
                    if hasattr(table.c, key):
                        stmt = stmt.values({key: value})

                # 添加WHERE条件
                if conditions:
                    where_clauses = self._build_where_clause(table, conditions)
                    if where_clauses:
                        stmt = stmt.where(and_(*where_clauses))

                # 执行更新
                result = session.execute(stmt)

                return QueryResult(
                    success=True,
                    data=[{"rowcount": result.rowcount}],
                    message=f"成功更新 {result.rowcount} 条数据",
                    rowcount=result.rowcount
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
            with self.get_session() as session:
                table = self.get_table(table_name)
                if table is None:
                    return QueryResult(
                        success=False,
                        message=f"表 {table_name} 不存在"
                    )

                # 构建DELETE语句
                stmt = delete(table)

                # 添加WHERE条件
                if conditions:
                    where_clauses = self._build_where_clause(table, conditions)
                    if where_clauses:
                        stmt = stmt.where(and_(*where_clauses))

                # 执行删除
                result = session.execute(stmt)

                return QueryResult(
                    success=True,
                    data=[{"rowcount": result.rowcount}],
                    message=f"成功删除 {result.rowcount} 条数据",
                    rowcount=result.rowcount
                )

        except Exception as e:
            logger.error(f"删除数据失败: {e}")
            return QueryResult(
                success=False,
                message=f"删除数据失败: {str(e)}"
            )

    # ==================== 连接查询 ====================

    def left_join(
            self,
            table1_name: str,
            table2_name: str,
            on_condition: str,
            columns: List[str] = None,
            conditions: Dict = None,
            order_by: List[str] = None,
            limit: int = None
    ) -> QueryResult:
        """左连接查询"""
        try:
            with self.get_session() as session:
                table1 = self.get_table(table1_name)
                table2 = self.get_table(table2_name)

                if table1 is None or table2 is None:
                    return QueryResult(
                        success=False,
                        message=f"表 {table1_name} 或 {table2_name} 不存在"
                    )

                # 解析ON条件
                # 格式: "table1.column = table2.column"
                on_parts = on_condition.split('=')
                if len(on_parts) != 2:
                    return QueryResult(
                        success=False,
                        message="ON条件格式错误，应为 'table1.column = table2.column'"
                    )

                left_col = on_parts[0].strip()
                right_col = on_parts[1].strip()

                # 解析列名
                left_table_name, left_column_name = left_col.split('.')
                right_table_name, right_column_name = right_col.split('.')

                # 获取列对象
                left_column = getattr(table1.c, left_column_name)
                right_column = getattr(table2.c, right_column_name)

                # 构建JOIN
                join_stmt = table1.join(table2, left_column == right_column, isouter=True)

                # 构建SELECT
                if columns:
                    selected_columns = []
                    for col in columns:
                        if '.' in col:
                            table_name, col_name = col.split('.')
                            if table_name == table1_name:
                                selected_columns.append(getattr(table1.c, col_name))
                            elif table_name == table2_name:
                                selected_columns.append(getattr(table2.c, col_name))
                        else:
                            # 如果列名不包含表名，尝试从两个表中查找
                            if hasattr(table1.c, col):
                                selected_columns.append(getattr(table1.c, col))
                            elif hasattr(table2.c, col):
                                selected_columns.append(getattr(table2.c, col))

                    if not selected_columns:
                        selected_columns = [table1, table2]

                    stmt = select(*selected_columns).select_from(join_stmt)
                else:
                    stmt = select(table1, table2).select_from(join_stmt)

                # 添加WHERE条件
                if conditions:
                    # 合并两个表的列
                    combined_table = Table('dummy', self.metadata)
                    for col in table1.c:
                        combined_table.append_column(col.copy())
                    for col in table2.c:
                        combined_table.append_column(col.copy())

                    where_clauses = self._build_where_clause(combined_table, conditions)
                    if where_clauses:
                        stmt = stmt.where(and_(*where_clauses))

                # 添加ORDER BY
                if order_by:
                    order_clauses = []
                    for order in order_by:
                        if order.startswith('-'):
                            col_name = order[1:]
                            if hasattr(table1.c, col_name):
                                order_clauses.append(getattr(table1.c, col_name).desc())
                            elif hasattr(table2.c, col_name):
                                order_clauses.append(getattr(table2.c, col_name).desc())
                        else:
                            if hasattr(table1.c, order):
                                order_clauses.append(getattr(table1.c, order).asc())
                            elif hasattr(table2.c, order):
                                order_clauses.append(getattr(table2.c, order).asc())
                    if order_clauses:
                        stmt = stmt.order_by(*order_clauses)

                # 添加LIMIT
                if limit is not None:
                    stmt = stmt.limit(limit)

                # 执行查询
                result = session.execute(stmt)

                # 转换为字典列表
                data = []
                for row in result:
                    row_dict = {}
                    for key, value in row._mapping.items():
                        if hasattr(value, '__table__'):
                            # 如果是表对象，展开所有列
                            table_obj = value.__table__
                            for col in table_obj.c:
                                row_dict[f"{table_obj.name}.{col.name}"] = getattr(value, col.name)
                        else:
                            row_dict[key] = value
                    data.append(row_dict)

                return QueryResult(
                    success=True,
                    data=data,
                    message=f"左连接查询成功，找到 {len(data)} 条数据",
                    rowcount=len(data)
                )

        except Exception as e:
            logger.error(f"左连接查询失败: {e}")
            return QueryResult(
                success=False,
                message=f"左连接查询失败: {str(e)}"
            )

    # ==================== 批量操作 ====================

    def bulk_insert(self, table_name: str, data_list: List[Dict]) -> QueryResult:
        """批量插入数据"""
        return self.insert(table_name, data_list)

    def bulk_update(self, table_name: str, data_list: List[Dict], key_column: str = "id") -> QueryResult:
        """批量更新数据"""
        try:
            with self.get_session() as session:
                table = self.get_table(table_name)
                if table is None:
                    return QueryResult(
                        success=False,
                        message=f"表 {table_name} 不存在"
                    )

                updated_count = 0
                for data in data_list:
                    if key_column in data:
                        key_value = data[key_column]
                        update_data = {k: v for k, v in data.items() if k != key_column}

                        if update_data:
                            stmt = update(table).where(getattr(table.c, key_column) == key_value).values(update_data)
                            result = session.execute(stmt)
                            updated_count += result.rowcount

                session.commit()

                return QueryResult(
                    success=True,
                    data=[{"rowcount": updated_count}],
                    message=f"批量更新完成，更新了 {updated_count} 条数据",
                    rowcount=updated_count
                )

        except Exception as e:
            logger.error(f"批量更新失败: {e}")
            return QueryResult(
                success=False,
                message=f"批量更新失败: {str(e)}"
            )


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例1: SQLite数据库
    print("=" * 50)
    print("示例1: SQLite数据库操作")
    print("=" * 50)

    # 创建SQLite数据库管理器
    db_manager = DatabaseManager(
        db_type=DatabaseType.SQLITE,
        database="testsql/mydatabase.db"  # SQLite数据库文件路径
    )

    # 创建SQL操作对象
    sqlop = SQLop(db_manager)

    # 创建新表
    sqlop.create_table(
        table_name="users",
        columns={
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "email": "TEXT UNIQUE",
            "age": "INTEGER"
        }
    )

    # 插入数据
    sqlop.insert("users", {"name": "张三", "email": "zhangsan@example.com", "age": 25})
    sqlop.insert("users", {"name": "李四", "email": "lisi@example.com", "age": 30})
    sqlop.insert("users", {"name": "王五", "email": "wangwu@example.com", "age": 35})

    # 查询数据
    result = sqlop.select("users", conditions={"age": {">": 20}}, bool_dict=True)
    print("年龄大于20的用户:")
    for row in result.data:
        print(row)

    # 获取表信息
    table_info = sqlop.get_table_info("users")
    print("\n表结构信息:")
    print(table_info.data[0])

    # 更新数据
    sqlop.update("users", {"age": 26}, {"name": "张三"})

    # 查询更新后的数据
    result = sqlop.select("users", conditions={"name": "张三"})
    print("\n更新后的张三信息:")
    print(result.data)

    # 删除数据
    sqlop.delete("users", {"name": "王五"})

    # 查询所有数据
    result = sqlop.select("users")
    print("\n所有用户:")
    for row in result.data:
        print(row)

    # 切换数据库（SQLite切换文件）
    print("\n切换SQLite数据库文件...")
    sqlop.select_database("testsql/another_db.db")

    # 在新数据库中创建表
    sqlop.create_table(
        table_name="users",
        columns={
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "email": "TEXT",
            "age": "INTEGER"
        }
    )

    sqlop.insert("users", {"name": "测试用户", "email": "test@example.com", "age": 18})

    # 示例2: MySQL数据库
    print("\n" + "=" * 50)
    print("示例2: MySQL数据库操作")
    print("=" * 50)

    mysql_manager = DatabaseManager(
        db_type=DatabaseType.MYSQL,
        host="localhost",
        port=3306,
        user="root",
        passwd="v2o756n829cy636nsgd",
        # database="testdb",
        charset="utf8mb4"
    )

    mysql_op = SQLop(mysql_manager)
    mysql_op.create_database("testdb")
    mysql_op.select_database("testdb")

    # 创建表
    mysql_op.create_table(
        table_name="products",
        columns={
            "id": "INT PRIMARY KEY AUTO_INCREMENT",
            "name": "VARCHAR(100) NOT NULL",
            "price": "DECIMAL(10, 2)",
            "stock": "INT DEFAULT 0"
        }
    )

    # 批量插入数据
    products = [
        {"name": "商品A", "price": 19.99, "stock": 100},
        {"name": "商品B", "price": 29.99, "stock": 50},
        {"name": "商品C", "price": 9.99, "stock": 200}
    ]
    mysql_op.insert("products", products)

    # 复杂查询
    result = mysql_op.select(
        "products",
        columns=["name", "price"],
        conditions={
            "price": {"<": 30, ">": 10},
            "stock": {">": 0}
        },
        order_by=["price DESC"],
        limit=10
    )
    print("查询结果:")
    for row in result.data:
        print(row)

    print("\n所有操作完成!")
