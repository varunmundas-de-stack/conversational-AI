"""
Base Connector Interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Result from executing a query"""
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    sql_query: str


class BaseConnector(ABC):
    """Abstract base class for database connectors"""

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def execute(self, sql: str) -> QueryResult:
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        pass

    @abstractmethod
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        pass
