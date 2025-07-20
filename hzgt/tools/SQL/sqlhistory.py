import json
import pickle
from dataclasses import dataclass, asdict
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Dict, Optional, Any, List

from .sqlcore import SQLExecutionStatus


@dataclass
class SQLHistoryRecord:
    """SQL历史记录数据类"""
    id: int  # 记录ID
    sql: str  # SQL语句
    params: Optional[Any]  # 参数
    execution_time: datetime  # 执行时间
    duration: float  # 执行耗时(秒)
    status: SQLExecutionStatus  # 执行状态
    affected_rows: Optional[int]  # 影响行数
    result_count: Optional[int]  # 结果行数
    error_message: Optional[str]  # 错误信息
    database: Optional[str]  # 数据库名
    table: Optional[str]  # 表名
    operation_type: str  # 操作类型 (SELECT, INSERT, UPDATE, DELETE, etc.)
    user_tag: Optional[str]  # 用户标签

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['execution_time'] = self.execution_time.isoformat()
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SQLHistoryRecord':
        """从字典创建实例"""
        data = data.copy()
        data['execution_time'] = datetime.fromisoformat(data['execution_time'])
        data['status'] = SQLExecutionStatus(data['status'])
        return cls(**data)

    def get_sql_preview(self, max_length: int = 100) -> str:
        """获取SQL预览（截断长SQL）"""
        if len(self.sql) <= max_length:
            return self.sql
        return self.sql[:max_length] + "..."

    def is_query_operation(self) -> bool:
        """判断是否为查询操作"""
        return self.operation_type.upper() in ('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')

    def is_modification_operation(self) -> bool:
        """判断是否为修改操作"""
        return self.operation_type.upper() in ('INSERT', 'UPDATE', 'DELETE', 'REPLACE')


class SQLHistory:
    """SQL历史记录管理类"""

    def __init__(self, max_records: int = 100, auto_save: bool = False,
                 save_path: Optional[str] = None, logger: Optional[Logger] = None):
        """
        初始化SQL历史记录管理器

        Args:
            max_records: 最大记录数，超过时自动清理旧记录
            auto_save: 是否自动保存到文件
            save_path: 保存文件路径
            logger: 日志记录器
        """
        self.max_records = max_records
        self.auto_save = auto_save
        self.save_path = save_path
        self.logger = logger
        self._records: List[SQLHistoryRecord] = []
        self._next_id = 1

        # 如果指定了保存路径且文件存在，则加载历史记录
        if self.save_path and Path(self.save_path).exists():
            self.load_from_file()

    def add_record(self, sql: str, params: Optional[Any] = None,
                   duration: float = 0.0, status: SQLExecutionStatus = SQLExecutionStatus.SUCCESS,
                   affected_rows: Optional[int] = None, result_count: Optional[int] = None,
                   error_message: Optional[str] = None, database: Optional[str] = None,
                   table: Optional[str] = None, user_tag: Optional[str] = None) -> SQLHistoryRecord:
        """
        添加历史记录

        Args:
            sql: SQL语句
            params: 参数
            duration: 执行耗时
            status: 执行状态
            affected_rows: 影响行数
            result_count: 结果行数
            error_message: 错误信息
            database: 数据库名
            table: 表名
            user_tag: 用户标签

        Returns:
            创建的历史记录
        """
        # 解析操作类型
        operation_type = self._parse_operation_type(sql)

        record = SQLHistoryRecord(
            id=self._next_id,
            sql=sql.strip(),
            params=params,
            execution_time=datetime.now(),
            duration=duration,
            status=status,
            affected_rows=affected_rows,
            result_count=result_count,
            error_message=error_message,
            database=database,
            table=table,
            operation_type=operation_type,
            user_tag=user_tag
        )

        self._records.append(record)
        self._next_id += 1

        # 检查是否超过最大记录数
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]

        # 自动保存
        if self.auto_save and self.save_path:
            self.save_to_file()

        if self.logger:
            self.logger.debug(f"添加SQL历史记录: {record.get_sql_preview()}")

        return record

    def _parse_operation_type(self, sql: str) -> str:
        """解析SQL操作类型"""
        sql_upper = sql.strip().upper()
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('CREATE'):
            return 'CREATE'
        elif sql_upper.startswith('DROP'):
            return 'DROP'
        elif sql_upper.startswith('ALTER'):
            return 'ALTER'
        elif sql_upper.startswith('SHOW'):
            return 'SHOW'
        elif sql_upper.startswith('DESCRIBE') or sql_upper.startswith('DESC'):
            return 'DESCRIBE'
        elif sql_upper.startswith('EXPLAIN'):
            return 'EXPLAIN'
        elif sql_upper.startswith('TRUNCATE'):
            return 'TRUNCATE'
        elif sql_upper.startswith('REPLACE'):
            return 'REPLACE'
        else:
            return 'OTHER'

    def get_all_records(self) -> List[SQLHistoryRecord]:
        """获取所有历史记录"""
        return self._records.copy()

    def get_recent_records(self, count: int = 10) -> List[SQLHistoryRecord]:
        """获取最近的N条记录"""
        return self._records[-count:] if count <= len(self._records) else self._records.copy()

    def get_records_by_time_range(self, start_time: datetime,
                                  end_time: Optional[datetime] = None) -> List[SQLHistoryRecord]:
        """
        按时间范围获取记录

        Args:
            start_time: 开始时间
            end_time: 结束时间，默认为当前时间

        Returns:
            符合条件的记录列表
        """
        if end_time is None:
            end_time = datetime.now()

        return [record for record in self._records
                if start_time <= record.execution_time <= end_time]

    def get_records_by_operation(self, operation_type: str) -> List[SQLHistoryRecord]:
        """按操作类型获取记录"""
        operation_type = operation_type.upper()
        return [record for record in self._records
                if record.operation_type.upper() == operation_type]

    def get_records_by_status(self, status: SQLExecutionStatus) -> List[SQLHistoryRecord]:
        """按执行状态获取记录"""
        return [record for record in self._records if record.status == status]

    def get_records_by_database(self, database: str) -> List[SQLHistoryRecord]:
        """按数据库获取记录"""
        return [record for record in self._records
                if record.database == database]

    def get_records_by_table(self, table: str) -> List[SQLHistoryRecord]:
        """按表名获取记录"""
        return [record for record in self._records
                if record.table == table]

    def search_records(self, keyword: str, case_sensitive: bool = False) -> List[SQLHistoryRecord]:
        """
        搜索包含关键词的记录

        Args:
            keyword: 搜索关键词
            case_sensitive: 是否区分大小写

        Returns:
            匹配的记录列表
        """
        if not case_sensitive:
            keyword = keyword.lower()

        results = []
        for record in self._records:
            search_text = record.sql if case_sensitive else record.sql.lower()
            if keyword in search_text:
                results.append(record)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        if not self._records:
            return {
                'total_records': 0,
                'operation_stats': {},
                'status_stats': {},
                'avg_duration': 0,
                'total_duration': 0,
                'date_range': None
            }

        # 操作类型统计
        operation_stats = {}
        status_stats = {}
        total_duration = 0

        for record in self._records:
            # 操作类型统计
            op_type = record.operation_type
            operation_stats[op_type] = operation_stats.get(op_type, 0) + 1

            # 状态统计
            status = record.status.value
            status_stats[status] = status_stats.get(status, 0) + 1

            # 耗时统计
            total_duration += record.duration

        # 时间范围
        earliest = min(record.execution_time for record in self._records)
        latest = max(record.execution_time for record in self._records)

        return {
            'total_records': len(self._records),
            'operation_stats': operation_stats,
            'status_stats': status_stats,
            'avg_duration': total_duration / len(self._records),
            'total_duration': total_duration,
            'date_range': {
                'earliest': earliest.isoformat(),
                'latest': latest.isoformat()
            }
        }

    def get_slow_queries(self, threshold: float = 1.0) -> List[SQLHistoryRecord]:
        """
        获取慢查询记录

        Args:
            threshold: 慢查询阈值(秒)

        Returns:
            慢查询记录列表
        """
        return [record for record in self._records
                if record.duration >= threshold]

    def get_failed_queries(self) -> List[SQLHistoryRecord]:
        """获取失败的查询记录"""
        return self.get_records_by_status(SQLExecutionStatus.ERROR)

    def clear_records(self, keep_recent: int = 0):
        """
        清空历史记录

        Args:
            keep_recent: 保留最近N条记录
        """
        if keep_recent > 0:
            self._records = self._records[-keep_recent:]
        else:
            self._records.clear()

        if self.logger:
            self.logger.info(f"清空SQL历史记录，保留最近{keep_recent}条")

    def export_to_dict(self) -> List[Dict[str, Any]]:
        """导出为字典列表"""
        return [record.to_dict() for record in self._records]

    def import_from_dict(self, data: List[Dict[str, Any]]):
        """从字典列表导入"""
        self._records = [SQLHistoryRecord.from_dict(item) for item in data]
        if self._records:
            self._next_id = max(record.id for record in self._records) + 1
        else:
            self._next_id = 1

    def save_to_file(self, file_path: Optional[str] = None):
        """
        保存历史记录到文件

        Args:
            file_path: 文件路径，默认使用初始化时的路径
        """
        file_path = file_path or self.save_path
        if not file_path:
            raise ValueError("未指定保存文件路径")

        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # 根据文件扩展名选择保存格式
            if path.suffix.lower() == '.json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.export_to_dict(), f, ensure_ascii=False, indent=2)
            else:
                # 默认使用pickle格式
                with open(file_path, 'wb') as f:
                    pickle.dump(self._records, f)

            if self.logger:
                self.logger.debug(f"SQL历史记录已保存到: {file_path}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"保存SQL历史记录失败: {e}")
            raise

    def load_from_file(self, file_path: Optional[str] = None):
        """
        从文件加载历史记录

        Args:
            file_path: 文件路径，默认使用初始化时的路径
        """
        file_path = file_path or self.save_path
        if not file_path or not Path(file_path).exists():
            return

        try:
            path = Path(file_path)

            # 根据文件扩展名选择加载格式
            if path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.import_from_dict(data)
            else:
                # 默认使用pickle格式
                with open(file_path, 'rb') as f:
                    self._records = pickle.load(f)
                    if self._records:
                        self._next_id = max(record.id for record in self._records) + 1

            if self.logger:
                self.logger.debug(f"从文件加载SQL历史记录: {file_path}, 共{len(self._records)}条")
        except Exception as e:
            if self.logger:
                self.logger.error(f"加载SQL历史记录失败: {e}")
            # 加载失败时不抛出异常，继续使用空的历史记录
