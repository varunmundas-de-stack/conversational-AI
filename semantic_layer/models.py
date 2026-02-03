"""
Data models for semantic layer using Pydantic
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Metric(BaseModel):
    """Represents a business metric"""
    name: str
    description: str
    sql: str
    table: str
    aggregation: str
    format: Optional[str] = "number"


class Dimension(BaseModel):
    """Represents a dimension for grouping/filtering"""
    name: str
    table: str
    key: str
    attributes: Dict[str, str]


class QueryIntent(BaseModel):
    """Represents the parsed user intent"""
    metrics: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    filters: List[str] = Field(default_factory=list)
    group_by: List[str] = Field(default_factory=list)
    time_period: Optional[str] = None
    limit: Optional[int] = None
    original_question: str


class SQLQuery(BaseModel):
    """Represents the generated SQL query"""
    sql: str
    intent: QueryIntent
    explanation: str


class QueryResult(BaseModel):
    """Represents query execution results"""
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    sql_query: str
    execution_time_ms: float
