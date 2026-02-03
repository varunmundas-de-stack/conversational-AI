"""
DuckDB Connector - For local DuckDB databases
"""
import time
from pathlib import Path
from typing import List, Dict, Any
import duckdb
from .base import BaseConnector, QueryResult


class DuckDBConnector(BaseConnector):
    """Connector for local DuckDB databases"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn = None

    def connect(self) -> bool:
        try:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database not found: {self.db_path}")
            self.conn = duckdb.connect(str(self.db_path), read_only=True)
            return True
        except Exception as e:
            print(f"DuckDB connection error: {e}")
            return False

    def disconnect(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, sql: str) -> QueryResult:
        if not self.conn:
            self.connect()

        start_time = time.time()
        result = self.conn.execute(sql)
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description]
        data = [dict(zip(columns, row)) for row in rows]
        execution_time = (time.time() - start_time) * 1000

        return QueryResult(
            data=data,
            columns=columns,
            row_count=len(data),
            execution_time_ms=round(execution_time, 2),
            sql_query=sql
        )

    def list_tables(self) -> List[str]:
        if not self.conn:
            self.connect()
        result = self.conn.execute("SHOW TABLES").fetchall()
        return [row[0] for row in result]

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        if not self.conn:
            self.connect()
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        return {'table_name': table_name, 'row_count': count}

    def test_connection(self) -> bool:
        try:
            if not self.conn:
                self.connect()
            self.conn.execute("SELECT 1").fetchone()
            return True
        except:
            return False
