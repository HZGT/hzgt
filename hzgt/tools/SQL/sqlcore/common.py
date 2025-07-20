from enum import Enum


class JoinType(Enum):
    """连接类型枚举"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL JOIN"


class SQLExecutionStatus(Enum):
    """SQL执行状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

