# -*- coding: utf-8 -*-
import re
from abc import ABC, abstractmethod
from contextlib import contextmanager
from logging import Logger
from typing import Dict, Optional, Any, List, Tuple, Union, TypeVar

from .common import JoinType

T = TypeVar('T')  # 用于表示查询结果的类型


class SQLutilop(ABC):
    """
    SQL操作工具抽象基类

    设计为可扩展到多种数据库的通用SQL接口，子类需要实现特定数据库的具体逻辑
    """

    def __init__(self, logger: Optional[Logger] = None):
        """
        初始化SQL工具基类

        Args:
            logger: 日志记录器，如果为None则创建默认的记录器
        """
        # 日志配置
        self.logger = logger or self._create_default_logger()
        self._connection = None
        self._cursor = None
        self._transaction_level = 0

    @abstractmethod
    def _create_default_logger(self) -> Logger:
        """
        创建默认日志记录器

        Returns:
            Logger: 日志记录器实例
        """
        pass

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type is not None:
            self.logger.error(f"发生异常: {exc_val}")
            self.rollback()
        else:
            self.commit()
        self.close()
        return False  # 允许异常向上传播

    @abstractmethod
    def connect(self):
        """建立数据库连接"""
        pass

    @abstractmethod
    def close(self):
        """关闭数据库连接"""
        pass

    @abstractmethod
    def commit(self):
        """提交事务"""
        pass

    @abstractmethod
    def rollback(self):
        """回滚事务"""
        pass

    @contextmanager
    def transaction(self):
        """
        事务上下文管理器

        用法:
        with db.transaction():
            db.execute(sql1)
            db.execute(sql2)
        """
        self._begin_transaction()
        try:
            yield
            self._end_transaction(commit=True)
        except Exception as e:
            self._end_transaction(commit=False)
            raise e

    @abstractmethod
    def _begin_transaction(self):
        """开始事务（具体实现由子类提供）"""
        pass

    @abstractmethod
    def _end_transaction(self, commit: bool = True):
        """
        结束事务

        Args:
            commit: 是否提交事务，False表示回滚
        """
        pass

    @abstractmethod
    def create_table(self,
                     tablename: str,
                     schema: Union[Dict[str, str], Dict[str, Dict]],
                     primary_key: Optional[List[str]] = None,
                     if_not_exists: bool = True,
                     **kwargs) -> bool:
        """
        创建表

        Args:
            tablename: 表名
            schema: 表结构，可以是{列名:类型}或{列名:{type:类型,constraint:约束}}
            primary_key: 主键列表
            if_not_exists: 是否添加IF NOT EXISTS子句
            **kwargs: 额外参数，如索引定义等

        Returns:
            是否成功创建表
        """
        pass

    @abstractmethod
    def insert(self,
               tablename: str,
               record: Union[Dict[str, Any], List[Dict[str, Any]]],
               return_id: bool = False,
               **kwargs) -> Union[int, List[int], None]:
        """
        插入数据

        Args:
            tablename: 表名
            record: 要插入的记录或记录列表
            return_id: 是否返回插入的ID
            **kwargs: 数据库特定选项

        Returns:
            如果return_id为True，返回插入的ID或ID列表；否则返回None
        """
        pass

    @abstractmethod
    def select(self,
               tablename: str,
               conditions: Optional[Dict] = None,
               order: Optional[Dict[str, bool]] = None,  # True升序，False降序
               fields: Optional[List[str]] = None,
               limit: Optional[int] = None,
               offset: Optional[int] = None,
               group_by: Optional[List[str]] = None,
               having: Optional[Dict] = None,
               **kwargs) -> List[Dict[str, Any]]:
        """
        查询数据

        Args:
            tablename: 表名
            conditions: 查询条件
            order: 排序条件，{列名:是否升序}
            fields: 要获取的字段列表
            limit: 限制返回记录数
            offset: 跳过前N条记录
            group_by: 分组字段
            having: 分组筛选条件
            **kwargs: 数据库特定选项

        Returns:
            查询结果列表
        """
        pass

    @abstractmethod
    def update(self,
               tablename: str,
               update_values: Dict[str, Any],
               conditions: Optional[Dict] = None,
               **kwargs) -> int:
        """
        更新数据

        Args:
            tablename: 表名
            update_values: 要更新的值
            conditions: 更新条件
            **kwargs: 数据库特定选项

        Returns:
            更新的记录数
        """
        pass

    @abstractmethod
    def delete(self,
               tablename: str,
               conditions: Optional[Dict] = None,
               **kwargs) -> int:
        """
        删除数据

        Args:
            tablename: 表名
            conditions: 删除条件
            **kwargs: 数据库特定选项

        Returns:
            删除的记录数
        """
        pass

    @abstractmethod
    def drop_table(self,
                   tablename: str,
                   if_exists: bool = True) -> bool:
        """
        删除表

        Args:
            tablename: 表名
            if_exists: 是否添加IF EXISTS子句

        Returns:
            是否成功删除表
        """
        pass

    @abstractmethod
    def table_exists(self, tablename: str) -> bool:
        """
        检查表是否存在

        Args:
            tablename: 表名

        Returns:
            表是否存在
        """
        pass

    @abstractmethod
    def get_columns(self, tablename: str) -> List[str]:
        """
        获取表的列名列表

        Args:
            tablename: 表名

        Returns:
            列名列表
        """
        pass

    @abstractmethod
    def join(self,
             main_table: str,
             joins: List[Tuple[str, str, JoinType, Dict[str, str]]],
             conditions: Optional[Dict] = None,
             fields: Optional[Dict[str, List[str]]] = None,
             order: Optional[Dict[str, bool]] = None,
             limit: Optional[int] = None,
             offset: Optional[int] = None,
             **kwargs) -> List[Dict[str, Any]]:
        """
        执行连接查询

        Args:
            main_table: 主表名
            joins: 连接定义列表，每项为(表名, 别名, 连接类型, {主表字段:连接表字段})
            conditions: 查询条件
            fields: 要获取的字段，格式为{表名或别名:[字段列表]}
            order: 排序条件，{列名:是否升序}
            limit: 限制返回记录数
            offset: 跳过前N条记录
            **kwargs: 数据库特定选项

        Returns:
            查询结果列表
        """
        pass

    def batch_insert(self,
                     tablename: str,
                     records: List[Dict[str, Any]],
                     batch_size: int = 1000,
                     **kwargs) -> int:
        """
        批量插入数据，自动分批

        Args:
            tablename: 表名
            records: 记录列表
            batch_size: 每批记录数
            **kwargs: 传递给insert方法的额外参数

        Returns:
            插入记录总数
        """
        total = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            self.insert(tablename, batch, **kwargs)
            total += len(batch)
        return total

    def upsert(self,
               tablename: str,
               record: Dict[str, Any],
               unique_fields: List[str],
               **kwargs) -> bool:
        """
        更新插入操作(若存在则更新，不存在则插入)
        默认实现，子类可能有更高效的原生实现

        Args:
            tablename: 表名
            record: 记录
            unique_fields: 唯一标识字段列表
            **kwargs: 数据库特定选项

        Returns:
            操作是否成功
        """
        # 构建查询条件
        conditions = {field: record[field] for field in unique_fields if field in record}
        if not conditions:
            raise ValueError("必须提供至少一个唯一字段进行upsert操作")

        # 查询记录是否存在
        exists = self.select(tablename, conditions, limit=1)

        if exists:
            # 更新现有记录
            update_values = {k: v for k, v in record.items() if k not in unique_fields}
            if update_values:
                return self.update(tablename, update_values, conditions, **kwargs) > 0
            return True
        else:
            # 插入新记录
            return self.insert(tablename, record, **kwargs) is not None

    @staticmethod
    def _escape_identifier(identifier: str) -> str:
        """
        转义标识符(表名、列名)，防止SQL注入和关键字冲突

        Args:
            identifier: 需要转义的标识符

        Returns:
            转义后的标识符
        """
        # 具体实现因数据库而异，这是通用模式
        return '`' + identifier.replace('`', '``') + '`'

    def _build_where_clause(self,
                            conditions: Dict,
                            param_style: str = '%s') -> Tuple[str, List]:
        """
        构建WHERE子句和参数列表(支持复杂条件)

        Args:
            conditions: 条件字典
            param_style: 参数占位符样式(%s, :param, ?, 等)

        Returns:
            (where_clause_str, parameter_list): 条件子句和参数列表
        """
        if not conditions:
            return "", []

        where_parts = []
        params = []

        # 定义可用操作符映射
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

        if '$or' in conditions or '$and' in conditions:
            # 处理OR/AND逻辑组合
            if '$or' in conditions:
                subclauses = []
                for subcond in conditions['$or']:
                    subwhere, subparams = self._build_where_clause(subcond, param_style)
                    if subwhere:
                        subclauses.append(f"({subwhere})")
                        params.extend(subparams)
                if subclauses:
                    where_parts.append(f"({' OR '.join(subclauses)})")

            if '$and' in conditions:
                subclauses = []
                for subcond in conditions['$and']:
                    subwhere, subparams = self._build_where_clause(subcond, param_style)
                    if subwhere:
                        subclauses.append(f"({subwhere})")
                        params.extend(subparams)
                if subclauses:
                    where_parts.append(f"({' AND '.join(subclauses)})")

            # 处理其余普通条件
            other_conditions = {k: v for k, v in conditions.items()
                                if k not in ('$or', '$and')}
            if other_conditions:
                subwhere, subparams = self._build_where_clause(other_conditions, param_style)
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
                safe_col = self._escape_identifier(column.strip())

                if isinstance(value, dict):
                    # 处理操作符条件
                    for op_symbol, op_value in value.items():
                        op = AVAILABLE_OPERATORS.get(
                            op_symbol.upper() if op_symbol.startswith('$') else op_symbol
                        )
                        if not op:
                            raise ValueError(f"无效操作符: {op_symbol}")

                        if op in ('BETWEEN', 'NOT BETWEEN'):
                            if not isinstance(op_value, (list, tuple)) or len(op_value) != 2:
                                raise ValueError(f"{op} 需要两个值的列表")
                            where_parts.append(f"{safe_col} {op} {param_style} AND {param_style}")
                            params.extend(op_value)
                        elif op in ('IN', 'NOT IN'):
                            if not isinstance(op_value, (list, tuple)):
                                raise ValueError(f"{op} 需要列表或元组")
                            placeholders = ', '.join([param_style] * len(op_value))
                            where_parts.append(f"{safe_col} {op} ({placeholders})")
                            params.extend(op_value)
                        elif op in ('IS', 'IS NOT'):
                            # IS NULL 和 IS NOT NULL 不需要参数
                            where_parts.append(f"{safe_col} {op} NULL"
                                               if op_value is None else f"{safe_col} {op} {param_style}")
                            if op_value is not None:
                                params.append(op_value)
                        else:
                            where_parts.append(f"{safe_col} {op} {param_style}")
                            params.append(op_value)
                else:
                    # 简单等值条件
                    if value is None:
                        where_parts.append(f"{safe_col} IS NULL")
                    else:
                        where_parts.append(f"{safe_col} = {param_style}")
                        params.append(value)

        return (" AND ".join(where_parts), params) if where_parts else ("", [])

    def _validate_table_name(self, tablename: str) -> bool:
        """
        验证表名有效性

        Args:
            tablename: 表名

        Returns:
            表名是否有效

        Raises:
            ValueError: 表名无效时抛出
        """
        if not tablename or not isinstance(tablename, str):
            self.logger.error("表名不能为空且必须是字符串")
            raise ValueError("表名不能为空且必须是字符串")

        if not re.match(r'^[a-zA-Z0-9_]+$', tablename):
            self.logger.error("表名无效，只能包含字母、数字和下划线")
            raise ValueError("表名只能包含字母、数字和下划线")

        return True

    @staticmethod
    def _validate_fields(fields: List[str], available_fields: Optional[List[str]] = None) -> List[str]:
        """
        验证字段列表有效性

        Args:
            fields: 字段列表
            available_fields: 可用字段列表，如果提供则进行验证

        Returns:
            验证后的字段列表

        Raises:
            ValueError: 字段无效时抛出
        """
        if not fields:
            return []

        validated_fields = []
        for field in fields:
            if not isinstance(field, str) or not field.strip():
                raise ValueError(f"字段名必须是非空字符串: {field}")

            field = field.strip()
            if available_fields and field not in available_fields:
                raise ValueError(f"字段不存在: {field}")

            validated_fields.append(field)

        return validated_fields



