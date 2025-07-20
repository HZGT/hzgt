from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, TypeVar, Generic

T = TypeVar('T')  # 用于表示查询结果的类型


class DBAdapter(Generic[T], ABC):
    """
    数据库适配器抽象类，用于适配不同的数据库系统
    T是适配的目标数据库连接类型
    """

    @abstractmethod
    def get_connection(self, **kwargs) -> T:
        """获取数据库连接"""
        pass

    @abstractmethod
    def close_connection(self, connection: T):
        """关闭数据库连接"""
        pass

    @abstractmethod
    def execute_query(self, connection: T, sql: str, params: Any = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        执行查询并返回结果

        Args:
            connection: 数据库连接
            sql: SQL语句
            params: 参数

        Returns:
            (结果集, 影响行数)
        """
        pass

    @abstractmethod
    def get_last_insert_id(self, connection: T, table_name: str = None) -> Any:
        """获取最后插入的ID"""
        pass

    @abstractmethod
    def get_placeholder_style(self) -> str:
        """获取参数占位符样式"""
        pass

    @abstractmethod
    def format_table_creation(self,
                              tablename: str,
                              columns: Dict[str, Dict[str, str]],
                              primary_keys: List[str],
                              **kwargs) -> str:
        """格式化建表语句"""
        pass
