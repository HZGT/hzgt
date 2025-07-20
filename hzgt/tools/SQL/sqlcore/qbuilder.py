from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List, Tuple, Union, TypeVar

from .common import JoinType

T = TypeVar('T')  # 用于表示查询结果的类型


class QueryBuilder(ABC):
    """
    SQL查询构建器抽象类，用于构建不同数据库系统的SQL语句
    """

    @abstractmethod
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
        pass

    @abstractmethod
    def build_insert(self,
                     tablename: str,
                     data: Union[Dict[str, Any], List[Dict[str, Any]]],
                     **kwargs) -> Tuple[str, List]:
        """构建INSERT语句"""
        pass

    @abstractmethod
    def build_update(self,
                     tablename: str,
                     update_values: Dict[str, Any],
                     conditions: Optional[Dict] = None,
                     **kwargs) -> Tuple[str, List]:
        """构建UPDATE语句"""
        pass

    @abstractmethod
    def build_delete(self,
                     tablename: str,
                     conditions: Optional[Dict] = None,
                     **kwargs) -> Tuple[str, List]:
        """构建DELETE语句"""
        pass

    @abstractmethod
    def build_create_table(self,
                           tablename: str,
                           schema: Dict[str, Any],
                           primary_key: Optional[List[str]] = None,
                           if_not_exists: bool = True,
                           **kwargs) -> str:
        """构建CREATE TABLE语句"""
        pass

    @abstractmethod
    def build_drop_table(self,
                         tablename: str,
                         if_exists: bool = True) -> str:
        """构建DROP TABLE语句"""
        pass

    @abstractmethod
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
        pass
