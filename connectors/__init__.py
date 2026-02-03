"""
Database Connectors - Support for DuckDB (local) and PostgreSQL (remote)
"""
from .base import BaseConnector, QueryResult
from .duckdb_connector import DuckDBConnector
from .postgres_connector import PostgreSQLConnector

__all__ = ['BaseConnector', 'QueryResult', 'DuckDBConnector', 'PostgreSQLConnector']
