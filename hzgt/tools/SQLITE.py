import logging
import sqlite3
import os
import csv
from typing import List, Dict, Optional, Any

from ..log import set_log


class SQLiteop:
    """
    SQLite 数据库操作类，提供连接、表操作、数据增删改查等功能。

    :param db_name: 数据库文件名
    :param logger: 日志记录器，如果未提供则自动创建
    """

    def __init__(self, db_name: str, logger: Optional[logging.Logger] = None):
        self.db_name = db_name
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

        # 初始化日志记录器
        if logger is None:
            self.__logger = set_log("hzgt.sqlite", os.path.join("logs", "sqlite.log"), level=2)
        else:
            self.__logger = logger

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self):
        self.connect()

    def connect(self) -> None:
        """
        连接到 SQLite 数据库。

        :raises sqlite3.Error: 如果连接失败
        """
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self.__logger.info(f"已连接到 {self.db_name}")
        except sqlite3.Error as e:
            self.__logger.error(f"连接到 {self.db_name} 失败: {e}")
            raise

    def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """
        创建表。

        :param table_name: 表名
        :param columns: 列名和类型的字典，例如 {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}
        :raises sqlite3.Error: 如果创建表失败
        """
        try:
            columns_with_types = ', '.join([f"{col} {dtype}" for col, dtype in columns.items()])
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_with_types})"
            self.cursor.execute(create_table_query)
            self.conn.commit()
            self.__logger.info(f"已创建表 {table_name}")
        except sqlite3.Error as e:
            self.__logger.error(f"创建表 {table_name} 失败: {e}")
            raise

    def insert(self, table_name: str, data: Dict[str, Any]) -> None:
        """
        插入单条数据。

        :param table_name: 表名
        :param data: 数据的字典，例如 {"name": "Alice", "age": 25}
        :raises sqlite3.Error: 如果插入数据失败
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(insert_query, tuple(data.values()))
            self.conn.commit()
            self.__logger.info(f"已插入数据到 {table_name}")
        except sqlite3.Error as e:
            self.__logger.error(f"插入数据到 {table_name} 失败: {e}")
            raise

    def insert_many(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        """
        批量插入数据。

        :param table_name: 表名
        :param data: 数据的字典列表，例如 [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
        :raises sqlite3.Error: 如果插入数据失败
        """
        try:
            if not data:
                return

            columns = ', '.join(data[0].keys())
            placeholders = ', '.join(['?'] * len(data[0]))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            self.cursor.executemany(insert_query, [tuple(item.values()) for item in data])
            self.conn.commit()
            self.__logger.info(f"已批量插入 {len(data)} 条数据到 {table_name}")
        except sqlite3.Error as e:
            self.__logger.error(f"批量插入数据到 {table_name} 失败: {e}")
            raise

    def select(self, table_name: str, columns: str = "*", condition: Optional[str] = None) -> List[tuple]:
        """
        查询数据。

        :param table_name: 表名
        :param columns: 要查询的列，默认为所有列
        :param condition: 查询条件，例如 "age > 20"
        :return: 查询结果的列表
        :raises sqlite3.Error: 如果查询失败
        """
        try:
            select_query = f"SELECT {columns} FROM {table_name}"
            if condition:
                select_query += f" WHERE {condition}"
            self.cursor.execute(select_query)
            rows = self.cursor.fetchall()
            self.__logger.info(f"已从 {table_name} 查询到 {len(rows)} 条数据")
            return rows
        except sqlite3.Error as e:
            self.__logger.error(f"查询数据从 {table_name} 失败: {e}")
            raise

    def update(self, table_name: str, data: Dict[str, Any], condition: str) -> None:
        """
        更新数据。

        :param table_name: 表名
        :param data: 要更新的数据的字典，例如 {"age": 26}
        :param condition: 更新条件，例如 "name = 'Alice'"
        :raises sqlite3.Error: 如果更新失败
        """
        try:
            set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
            update_query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
            self.cursor.execute(update_query, tuple(data.values()))
            self.conn.commit()
            self.__logger.info(f"已更新数据到 {table_name}")
        except sqlite3.Error as e:
            self.__logger.error(f"更新数据到 {table_name} 失败: {e}")
            raise

    def delete(self, table_name: str, condition: str) -> None:
        """
        删除数据。

        :param table_name: 表名
        :param condition: 删除条件，例如 "name = 'Alice'"
        :raises sqlite3.Error: 如果删除失败
        """
        try:
            delete_query = f"DELETE FROM {table_name} WHERE {condition}"
            self.cursor.execute(delete_query)
            self.conn.commit()
            self.__logger.info(f"已删除数据从 {table_name}")
        except sqlite3.Error as e:
            self.__logger.error(f"删除数据从 {table_name} 失败: {e}")
            raise

    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在。

        :param table_name: 表名
        :return: 如果表存在返回 True，否则返回 False
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        self.cursor.execute(query, (table_name,))
        return self.cursor.fetchone() is not None

    def begin_transaction(self) -> None:
        """
        开始事务。
        """
        self.cursor.execute("BEGIN")
        self.__logger.info("事务已开始")

    def commit_transaction(self) -> None:
        """
        提交事务。
        """
        self.conn.commit()
        self.__logger.info("事务已提交")

    def rollback_transaction(self) -> None:
        """
        回滚事务。
        """
        self.conn.rollback()
        self.__logger.info("事务已回滚")

    def close(self) -> None:
        """
        关闭数据库连接。
        """
        if self.conn:
            self.conn.close()
            self.__logger.info("已关闭数据库连接")

    def backup_db(self, target_db: str) -> None:
        """
        备份数据库。

        :param target_db: 目标数据库文件名
        :raises sqlite3.Error: 如果备份失败
        """
        try:
            target_conn = sqlite3.connect(target_db)
            with target_conn:
                self.conn.backup(target_conn)
            target_conn.close()
            self.__logger.info(f"数据库已备份到 {target_db}")
        except sqlite3.Error as e:
            self.__logger.error(f"备份数据库失败: {e}")
            raise

    def execute_sql_script(self, script_path: str) -> None:
        """
        执行 SQL 脚本文件。

        :param script_path: SQL 脚本文件路径
        :raises sqlite3.Error: 如果执行脚本失败
        """
        try:
            with open(script_path, 'r') as f:
                sql_script = f.read()
            self.cursor.executescript(sql_script)
            self.__logger.info(f"已执行 SQL 脚本: {script_path}")
        except sqlite3.Error as e:
            self.__logger.error(f"执行 SQL 脚本失败: {e}")
            raise

    def export_to_csv(self, table_name: str, csv_path: str) -> None:
        """
        将表数据导出到 CSV 文件。

        :param table_name: 表名
        :param csv_path: CSV 文件路径
        :raises sqlite3.Error: 如果导出失败
        """
        try:
            rows = self.select(table_name)
            columns = [description[0] for description in self.cursor.description]

            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(columns)  # 写入列名
                writer.writerows(rows)  # 写入数据
            self.__logger.info(f"数据已导出到 {csv_path}")
        except sqlite3.Error as e:
            self.__logger.error(f"导出数据失败: {e}")
            raise

    def import_from_csv(self, table_name: str, csv_path: str) -> None:
        """
        从 CSV 文件导入数据到表。

        :param table_name: 表名
        :param csv_path: CSV 文件路径
        :raises sqlite3.Error: 如果导入失败
        """
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                columns = next(reader)  # 读取列名
                placeholders = ', '.join(['?'] * len(columns))
                insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                for row in reader:
                    self.cursor.execute(insert_query, row)
            self.conn.commit()
            self.__logger.info(f"数据已从 {csv_path} 导入到 {table_name}")
        except sqlite3.Error as e:
            self.__logger.error(f"导入数据失败: {e}")
            raise

    def enable_wal_mode(self) -> None:
        """
        启用 WAL 模式（Write-Ahead Logging），提高并发性能。
        """
        try:
            self.cursor.execute("PRAGMA journal_mode=WAL")
            self.__logger.info("已启用 WAL 模式")
        except sqlite3.Error as e:
            self.__logger.error(f"启用 WAL 模式失败: {e}")
            raise

    def migrate_db(self, table_name: str, new_columns: Dict[str, str]) -> None:
        """
        数据库迁移：添加新列。

        :param table_name: 表名
        :param new_columns: 新列名和类型的字典，例如 {"email": "TEXT"}
        :raises sqlite3.Error: 如果迁移失败
        """
        try:
            for col, dtype in new_columns.items():
                if not self.column_exists(table_name, col):
                    self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {dtype}")
                    self.__logger.info(f"已添加列 {col} 到表 {table_name}")
            self.conn.commit()
        except sqlite3.Error as e:
            self.__logger.error(f"数据库迁移失败: {e}")
            raise

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """
        检查表中是否存在某列。

        :param table_name: 表名
        :param column_name: 列名
        :return: 如果列存在返回 True，否则返回 False
        """
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in self.cursor.fetchall()]
        return column_name in columns
