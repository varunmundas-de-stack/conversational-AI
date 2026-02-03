"""
PostgreSQL Connector - For remote PostgreSQL databases (Supabase, Neon, AWS RDS, etc.)
"""
import time
import os
from typing import List, Dict, Any
from .base import BaseConnector, QueryResult


class PostgreSQLConnector(BaseConnector):
    """
    Connector for PostgreSQL databases
    Works with: Supabase, Neon, AWS RDS, Heroku, Azure, etc.
    """

    def __init__(self, host: str, port: int, database: str, user: str, password: str, ssl: bool = True):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.ssl = ssl
        self.conn = None

    @classmethod
    def from_connection_string(cls, conn_string: str) -> 'PostgreSQLConnector':
        """
        Create connector from connection string
        Format: postgresql://user:password@host:port/database
        """
        import re
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, conn_string)
        if not match:
            raise ValueError("Invalid connection string format")

        user, password, host, port, database = match.groups()
        return cls(host=host, port=int(port), database=database, user=user, password=password)

    @classmethod
    def from_env(cls) -> 'PostgreSQLConnector':
        """Create connector from environment variables"""
        return cls(
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            port=int(os.environ.get('POSTGRES_PORT', '5432')),
            database=os.environ.get('POSTGRES_DB', 'postgres'),
            user=os.environ.get('POSTGRES_USER', 'postgres'),
            password=os.environ.get('POSTGRES_PASSWORD', ''),
            ssl=os.environ.get('POSTGRES_SSL', 'true').lower() == 'true'
        )

    def connect(self) -> bool:
        try:
            import psycopg2

            conn_params = {
                'host': self.host,
                'port': self.port,
                'dbname': self.database,
                'user': self.user,
                'password': self.password,
            }

            if self.ssl:
                conn_params['sslmode'] = 'require'

            self.conn = psycopg2.connect(**conn_params)
            return True

        except ImportError:
            print("psycopg2 not installed. Run: pip install psycopg2-binary")
            return False
        except Exception as e:
            print(f"PostgreSQL connection error: {e}")
            return False

    def disconnect(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, sql: str) -> QueryResult:
        if not self.conn:
            self.connect()

        from psycopg2.extras import RealDictCursor

        start_time = time.time()

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

        data = [dict(row) for row in rows]
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

        sql = """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql)
            return [row[0] for row in cursor.fetchall()]

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]

        return {'table_name': table_name, 'row_count': count}

    def test_connection(self) -> bool:
        try:
            if not self.conn:
                self.connect()
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except:
            return False
