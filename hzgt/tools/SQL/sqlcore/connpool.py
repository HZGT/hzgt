# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar('T')  # 用于表示查询结果的类型


class ConnectionPool(ABC):
    """数据库连接池抽象类"""

    @abstractmethod
    def get_connection(self) -> Any:
        """获取连接"""
        pass

    @abstractmethod
    def release_connection(self, connection: Any):
        """释放连接"""
        pass

    @abstractmethod
    def close_all(self):
        """关闭所有连接"""
        pass