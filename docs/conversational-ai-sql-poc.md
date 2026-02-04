# Conversational AI over SQL Data: Production-Ready PoC

**A Semantic Layer + AST Approach (No LLM-Generated SQL)**

---

## Table of Contents

1. [Summary](#executive-summary)
2. [Why NOT Use LLMs for SQL Generation?](#why-not-use-llms-for-sql-generation)
3. [Solution Architecture](#solution-architecture)
4. [Core Components](#core-components)
5. [Implementation Guide](#implementation-guide)
6. [Complete Working Code](#complete-working-code)
7. [Testing & Validation](#testing--validation)
8. [Production Deployment](#production-deployment)
9. [Alternative: BFSI Implementation](#alternative-bfsi-implementation)

---

## Executive Summary

This document presents a **production-ready approach** for building Conversational AI systems over SQL/OLAP databases **without using LLMs to generate SQL queries**. 

### Key Principles

✅ **LLMs for Intent Understanding** - Extract metrics, dimensions, filters  
✅ **Semantic Layer** - Business logic, metadata catalog, validation  
✅ **AST-based Query Builder** - Deterministic, safe SQL generation  
✅ **Type-Safe** - Structured intermediate representations  
❌ **NO LLM-Generated SQL** - Eliminates hallucination, injection risks

### Architecture Flow

```
User Question
    ↓
LLM Intent Recognition (JSON Output)
    ↓
Semantic Layer Validation
    ↓
AST Query Builder
    ↓
SQL Execution
    ↓
LLM Response Formatting
```

---

## Why NOT Use LLMs for SQL Generation?

### Critical Problems with LLM-Generated SQL

| Issue | Impact | Example |
|-------|--------|---------|
| **SQL Injection Risk** | Security vulnerability | `'; DROP TABLE users; --` |
| **Schema Hallucination** | Wrong column/table names | `SELECT non_existent_column` |
| **Join Logic Errors** | Incorrect results | Missing/wrong foreign keys |
| **Performance Issues** | Unoptimized queries | Missing indexes, cartesian joins |
| **Business Logic Bypass** | Wrong calculations | Ignoring metric definitions |
| **Non-Deterministic** | Same question → different SQL | Inconsistent results |

### Our Approach: Structured Pipeline

```python
# ❌ BAD: LLM directly generates SQL
user_query = "Show me sales by region"
sql = llm.generate(f"Convert to SQL: {user_query}")  # Dangerous!

# ✅ GOOD: Structured semantic approach
intent = llm.extract_intent(user_query)  # Returns JSON
validated_intent = semantic_layer.validate(intent)
ast = query_builder.build_ast(validated_intent)
sql = ast.to_sql()  # Deterministic, safe
```

---

## Solution Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                  1. USER INTERACTION LAYER                   │
│  Natural Language: "Show me top 10 products by revenue      │
│                     in California last quarter"              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              2. INTENT RECOGNITION (LLM)                     │
│  Input: Natural language                                    │
│  Output: Structured JSON (IntentObject)                     │
│  {                                                           │
│    "metrics": ["revenue"],                                  │
│    "dimensions": ["product_name"],                          │
│    "filters": [{"dimension": "state", "value": "CA"}],     │
│    "time_range": {"relative": "last_quarter"},             │
│    "limit": 10                                              │
│  }                                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              3. SEMANTIC LAYER                               │
│  - Validates intent against schema                          │
│  - Resolves synonyms (revenue → total_sales)               │
│  - Applies business rules                                   │
│  - Determines required tables/joins                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              4. QUERY BUILDER (AST)                          │
│  - Builds Abstract Syntax Tree                              │
│  - Applies aggregations, filters, joins                     │
│  - Generates optimized SQL                                  │
│  SELECT p.product_name, SUM(f.sales_amount) as revenue      │
│  FROM fact_sales f                                           │
│  JOIN dim_product p ON f.product_id = p.product_id         │
│  JOIN dim_store s ON f.store_id = s.store_id               │
│  WHERE s.state = 'CA' AND f.date BETWEEN ... AND ...       │
│  GROUP BY p.product_name                                     │
│  ORDER BY revenue DESC LIMIT 10                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              5. QUERY EXECUTION                              │
│  - Execute against database                                 │
│  - Return structured results                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              6. RESPONSE GENERATION (LLM)                    │
│  - Format results in natural language                       │
│  - Generate insights/summaries                              │
│  - Suggest follow-up questions                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### Component 1: Data Models & Schemas

```python
# semantic_schema.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from enum import Enum

class AggregationType(Enum):
    """Supported aggregation functions"""
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"
    COUNT_DISTINCT = "COUNT_DISTINCT"

class DataType(Enum):
    """Supported data types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"

class JoinType(Enum):
    """SQL join types"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"

@dataclass
class Dimension:
    """Represents a dimension in the semantic model"""
    name: str                          # Internal identifier
    display_name: str                  # User-friendly name
    column: str                        # Physical column name
    table: str                         # Physical table name
    data_type: DataType
    description: str
    synonyms: List[str] = field(default_factory=list)
    hierarchy: Optional[str] = None    # e.g., "geography"
    is_temporal: bool = False          # For date dimensions
    
    def __post_init__(self):
        """Normalize synonyms to lowercase for matching"""
        self.synonyms = [s.lower() for s in self.synonyms]

@dataclass
class Metric:
    """Represents a business metric/measure"""
    name: str                          # Internal identifier
    display_name: str                  # User-friendly name
    expression: str                    # SQL expression
    aggregation: AggregationType
    description: str
    data_type: DataType
    synonyms: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Required tables
    format_string: Optional[str] = None  # e.g., "${:,.2f}" for currency
    
    def __post_init__(self):
        self.synonyms = [s.lower() for s in self.synonyms]

@dataclass
class Relationship:
    """Defines FK relationships between tables"""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: Literal["one_to_one", "one_to_many", "many_to_one"]
    join_type: JoinType = JoinType.INNER

@dataclass
class SemanticModel:
    """Complete semantic model definition"""
    name: str
    dimensions: Dict[str, Dimension]
    metrics: Dict[str, Metric]
    relationships: List[Relationship]
    fact_table: str
    dimension_tables: List[str]
    
    def get_dimension_by_name_or_synonym(self, query: str) -> Optional[Dimension]:
        """Resolve dimension by name or synonym"""
        query_lower = query.lower()
        for dim in self.dimensions.values():
            if dim.name.lower() == query_lower or query_lower in dim.synonyms:
                return dim
        return None
    
    def get_metric_by_name_or_synonym(self, query: str) -> Optional[Metric]:
        """Resolve metric by name or synonym"""
        query_lower = query.lower()
        for metric in self.metrics.values():
            if metric.name.lower() == query_lower or query_lower in metric.synonyms:
                return metric
        return None
    
    def get_join_path(self, from_table: str, to_table: str) -> List[Relationship]:
        """Find join path between two tables"""
        # Simple implementation - can be enhanced with graph traversal
        relevant_joins = []
        for rel in self.relationships:
            if (rel.from_table == from_table and rel.to_table == to_table) or \
               (rel.to_table == from_table and rel.from_table == to_table):
                relevant_joins.append(rel)
        return relevant_joins
```

### Component 2: Intent Schema (LLM Output)

```python
# intent_schema.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import date, datetime

class Filter(BaseModel):
    """Represents a filter condition"""
    dimension: str
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "IN", "NOT IN", "LIKE", "BETWEEN", "IS NULL", "IS NOT NULL"]
    value: Optional[str | int | float | List[str]] = None
    
    @validator('value')
    def validate_value(cls, v, values):
        """Ensure value matches operator"""
        if values.get('operator') in ['IS NULL', 'IS NOT NULL']:
            return None
        if values.get('operator') in ['IN', 'NOT IN'] and not isinstance(v, list):
            raise ValueError(f"Operator {values.get('operator')} requires a list value")
        return v

class TimeRange(BaseModel):
    """Represents time-based filtering"""
    dimension: str = "date"  # Default date dimension
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    relative: Optional[str] = None  # e.g., "last_7_days", "this_month", "last_quarter", "ytd"
    
    @validator('relative')
    def validate_relative(cls, v):
        """Validate relative time expressions"""
        valid_relative = [
            "today", "yesterday",
            "this_week", "last_week",
            "this_month", "last_month",
            "this_quarter", "last_quarter",
            "this_year", "last_year", "ytd",
            "last_7_days", "last_30_days", "last_90_days"
        ]
        if v and v.lower() not in valid_relative:
            raise ValueError(f"Invalid relative time: {v}")
        return v.lower() if v else None

class SortBy(BaseModel):
    """Represents sorting specification"""
    field: str  # Metric or dimension name
    direction: Literal["ASC", "DESC"] = "DESC"

class IntentObject(BaseModel):
    """Structured output from LLM intent recognition"""
    metrics: List[str] = Field(
        description="List of metrics to calculate (e.g., ['revenue', 'quantity'])"
    )
    dimensions: List[str] = Field(
        default_factory=list,
        description="Dimensions for grouping (e.g., ['region', 'product_category'])"
    )
    filters: List[Filter] = Field(
        default_factory=list,
        description="Filter conditions"
    )
    time_range: Optional[TimeRange] = Field(
        default=None,
        description="Time-based filtering"
    )
    sort_by: List[SortBy] = Field(
        default_factory=list,
        description="Sorting specification"
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=1000,
        description="Maximum number of rows to return"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": ["total_sales", "profit"],
                "dimensions": ["region", "product_category"],
                "filters": [
                    {"dimension": "state", "operator": "IN", "value": ["CA", "NY"]},
                    {"dimension": "sales_amount", "operator": ">", "value": 1000}
                ],
                "time_range": {
                    "dimension": "order_date",
                    "relative": "last_quarter"
                },
                "sort_by": [{"field": "total_sales", "direction": "DESC"}],
                "limit": 10
            }
        }
```

### Component 3: Retail Sales Semantic Model

```python
# retail_semantic_model.py
from semantic_schema import *

def create_retail_semantic_model() -> SemanticModel:
    """Creates the semantic model for retail sales"""
    
    return SemanticModel(
        name="retail_sales_analytics",
        fact_table="fact_sales",
        dimension_tables=["dim_date", "dim_product", "dim_store", "dim_customer"],
        
        # ============== DIMENSIONS ==============
        dimensions={
            # Date Dimensions
            "date": Dimension(
                name="date",
                display_name="Date",
                column="date",
                table="dim_date",
                data_type=DataType.DATE,
                description="Transaction date",
                synonyms=["day", "transaction date", "sale date", "order date"],
                is_temporal=True
            ),
            "year": Dimension(
                name="year",
                display_name="Year",
                column="year",
                table="dim_date",
                data_type=DataType.INTEGER,
                description="Year",
                synonyms=["yr", "fiscal year"],
                hierarchy="time",
                is_temporal=True
            ),
            "quarter": Dimension(
                name="quarter",
                display_name="Quarter",
                column="quarter",
                table="dim_date",
                data_type=DataType.INTEGER,
                description="Quarter (1-4)",
                synonyms=["qtr", "q"],
                hierarchy="time",
                is_temporal=True
            ),
            "month": Dimension(
                name="month",
                display_name="Month",
                column="month",
                table="dim_date",
                data_type=DataType.INTEGER,
                description="Month (1-12)",
                synonyms=["mon", "month number"],
                hierarchy="time",
                is_temporal=True
            ),
            "week": Dimension(
                name="week",
                display_name="Week",
                column="week",
                table="dim_date",
                data_type=DataType.INTEGER,
                description="Week of year",
                synonyms=["week number", "wk"],
                hierarchy="time",
                is_temporal=True
            ),
            "day_of_week": Dimension(
                name="day_of_week",
                display_name="Day of Week",
                column="day_of_week",
                table="dim_date",
                data_type=DataType.STRING,
                description="Day name (Monday, Tuesday, etc.)",
                synonyms=["weekday", "dow"],
                hierarchy="time",
                is_temporal=True
            ),
            
            # Product Dimensions
            "product_name": Dimension(
                name="product_name",
                display_name="Product Name",
                column="product_name",
                table="dim_product",
                data_type=DataType.STRING,
                description="Product name",
                synonyms=["product", "item", "sku name"]
            ),
            "category": Dimension(
                name="category",
                display_name="Product Category",
                column="category",
                table="dim_product",
                data_type=DataType.STRING,
                description="Product category",
                synonyms=["product category", "dept", "department"],
                hierarchy="product"
            ),
            "subcategory": Dimension(
                name="subcategory",
                display_name="Product Subcategory",
                column="subcategory",
                table="dim_product",
                data_type=DataType.STRING,
                description="Product subcategory",
                synonyms=["sub category", "sub-category"],
                hierarchy="product"
            ),
            "brand": Dimension(
                name="brand",
                display_name="Brand",
                column="brand",
                table="dim_product",
                data_type=DataType.STRING,
                description="Product brand",
                synonyms=["manufacturer", "make"],
                hierarchy="product"
            ),
            
            # Store/Geography Dimensions
            "store_name": Dimension(
                name="store_name",
                display_name="Store Name",
                column="store_name",
                table="dim_store",
                data_type=DataType.STRING,
                description="Store name",
                synonyms=["store", "outlet", "location name"]
            ),
            "region": Dimension(
                name="region",
                display_name="Region",
                column="region",
                table="dim_store",
                data_type=DataType.STRING,
                description="Geographic region",
                synonyms=["area", "territory", "zone"],
                hierarchy="geography"
            ),
            "state": Dimension(
                name="state",
                display_name="State",
                column="state",
                table="dim_store",
                data_type=DataType.STRING,
                description="State/Province",
                synonyms=["province"],
                hierarchy="geography"
            ),
            "city": Dimension(
                name="city",
                display_name="City",
                column="city",
                table="dim_store",
                data_type=DataType.STRING,
                description="City",
                synonyms=["town", "municipality"],
                hierarchy="geography"
            ),
            
            # Customer Dimensions
            "customer_segment": Dimension(
                name="customer_segment",
                display_name="Customer Segment",
                column="customer_segment",
                table="dim_customer",
                data_type=DataType.STRING,
                description="Customer segment (e.g., Enterprise, SMB, Consumer)",
                synonyms=["segment", "customer type"]
            ),
        },
        
        # ============== METRICS ==============
        metrics={
            "total_sales": Metric(
                name="total_sales",
                display_name="Total Sales",
                expression="sales_amount",
                aggregation=AggregationType.SUM,
                data_type=DataType.DECIMAL,
                description="Total sales revenue",
                synonyms=["revenue", "sales", "sales revenue", "total revenue"],
                dependencies=["fact_sales"],
                format_string="${:,.2f}"
            ),
            "quantity": Metric(
                name="quantity",
                display_name="Quantity Sold",
                expression="quantity",
                aggregation=AggregationType.SUM,
                data_type=DataType.INTEGER,
                description="Total quantity sold",
                synonyms=["units", "volume", "units sold", "quantity sold"],
                dependencies=["fact_sales"],
                format_string="{:,}"
            ),
            "profit": Metric(
                name="profit",
                display_name="Profit",
                expression="sales_amount - cost_amount",
                aggregation=AggregationType.SUM,
                data_type=DataType.DECIMAL,
                description="Total profit (sales - cost)",
                synonyms=["gross profit", "margin amount"],
                dependencies=["fact_sales"],
                format_string="${:,.2f}"
            ),
            "avg_unit_price": Metric(
                name="avg_unit_price",
                display_name="Average Unit Price",
                expression="unit_price",
                aggregation=AggregationType.AVG,
                data_type=DataType.DECIMAL,
                description="Average unit price",
                synonyms=["average price", "mean price"],
                dependencies=["fact_sales"],
                format_string="${:.2f}"
            ),
            "total_discount": Metric(
                name="total_discount",
                display_name="Total Discount",
                expression="discount_amount",
                aggregation=AggregationType.SUM,
                data_type=DataType.DECIMAL,
                description="Total discount amount",
                synonyms=["discount", "discounts", "total discounts"],
                dependencies=["fact_sales"],
                format_string="${:,.2f}"
            ),
            "transaction_count": Metric(
                name="transaction_count",
                display_name="Transaction Count",
                expression="sale_id",
                aggregation=AggregationType.COUNT_DISTINCT,
                data_type=DataType.INTEGER,
                description="Number of transactions",
                synonyms=["number of transactions", "txn count", "sales count", "order count"],
                dependencies=["fact_sales"],
                format_string="{:,}"
            ),
            "avg_transaction_value": Metric(
                name="avg_transaction_value",
                display_name="Average Transaction Value",
                expression="sales_amount",
                aggregation=AggregationType.AVG,
                data_type=DataType.DECIMAL,
                description="Average transaction value",
                synonyms=["avg order value", "average basket", "avg sale"],
                dependencies=["fact_sales"],
                format_string="${:,.2f}"
            ),
        },
        
        # ============== RELATIONSHIPS ==============
        relationships=[
            Relationship(
                from_table="fact_sales",
                from_column="date_id",
                to_table="dim_date",
                to_column="date_id",
                relationship_type="many_to_one",
                join_type=JoinType.INNER
            ),
            Relationship(
                from_table="fact_sales",
                from_column="product_id",
                to_table="dim_product",
                to_column="product_id",
                relationship_type="many_to_one",
                join_type=JoinType.INNER
            ),
            Relationship(
                from_table="fact_sales",
                from_column="store_id",
                to_table="dim_store",
                to_column="store_id",
                relationship_type="many_to_one",
                join_type=JoinType.INNER
            ),
            Relationship(
                from_table="fact_sales",
                from_column="customer_id",
                to_table="dim_customer",
                to_column="customer_id",
                relationship_type="many_to_one",
                join_type=JoinType.LEFT
            ),
        ]
    )
```

### Component 4: Semantic Layer Validator

```python
# semantic_validator.py
from typing import Tuple, List
from intent_schema import IntentObject, Filter, TimeRange
from semantic_schema import SemanticModel
from datetime import datetime, timedelta

class ValidationError(Exception):
    """Custom exception for semantic validation errors"""
    pass

class SemanticValidator:
    """Validates and resolves intent against semantic model"""
    
    def __init__(self, semantic_model: SemanticModel):
        self.model = semantic_model
    
    def validate_and_resolve(self, intent: IntentObject) -> Tuple[IntentObject, List[str]]:
        """
        Validates intent and resolves all names to canonical form.
        Returns: (resolved_intent, required_tables)
        """
        resolved_intent = IntentObject(
            metrics=[],
            dimensions=[],
            filters=[],
            time_range=intent.time_range,
            sort_by=intent.sort_by,
            limit=intent.limit
        )
        
        required_tables = {self.model.fact_table}
        
        # Validate and resolve metrics
        for metric_name in intent.metrics:
            metric = self.model.get_metric_by_name_or_synonym(metric_name)
            if not metric:
                raise ValidationError(f"Unknown metric: '{metric_name}'")
            resolved_intent.metrics.append(metric.name)
            required_tables.update(metric.dependencies)
        
        # Validate and resolve dimensions
        for dim_name in intent.dimensions:
            dim = self.model.get_dimension_by_name_or_synonym(dim_name)
            if not dim:
                raise ValidationError(f"Unknown dimension: '{dim_name}'")
            resolved_intent.dimensions.append(dim.name)
            required_tables.add(dim.table)
        
        # Validate and resolve filters
        for filter_obj in intent.filters:
            dim = self.model.get_dimension_by_name_or_synonym(filter_obj.dimension)
            if not dim:
                raise ValidationError(f"Unknown dimension in filter: '{filter_obj.dimension}'")
            
            # Update filter with resolved dimension name
            resolved_filter = Filter(
                dimension=dim.name,
                operator=filter_obj.operator,
                value=filter_obj.value
            )
            resolved_intent.filters.append(resolved_filter)
            required_tables.add(dim.table)
        
        # Validate time range dimension
        if intent.time_range:
            time_dim = self.model.get_dimension_by_name_or_synonym(
                intent.time_range.dimension
            )
            if not time_dim:
                raise ValidationError(
                    f"Unknown time dimension: '{intent.time_range.dimension}'"
                )
            if not time_dim.is_temporal:
                raise ValidationError(
                    f"Dimension '{time_dim.name}' is not a temporal dimension"
                )
            resolved_intent.time_range.dimension = time_dim.name
            required_tables.add(time_dim.table)
        
        # Validate sort_by fields
        for sort_spec in resolved_intent.sort_by:
            # Check if it's a metric or dimension
            metric = self.model.get_metric_by_name_or_synonym(sort_spec.field)
            dim = self.model.get_dimension_by_name_or_synonym(sort_spec.field)
            
            if not metric and not dim:
                raise ValidationError(f"Unknown field in sort_by: '{sort_spec.field}'")
            
            # Resolve to canonical name
            if metric:
                sort_spec.field = metric.name
            else:
                sort_spec.field = dim.name
        
        return resolved_intent, list(required_tables)
    
    def resolve_time_range(self, time_range: TimeRange) -> Tuple[datetime, datetime]:
        """Converts relative time expressions to absolute dates"""
        if time_range.start_date and time_range.end_date:
            return (
                datetime.combine(time_range.start_date, datetime.min.time()),
                datetime.combine(time_range.end_date, datetime.max.time())
            )
        
        if not time_range.relative:
            raise ValidationError("Either specify dates or a relative time range")
        
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Relative time calculations
        time_map = {
            "today": (today, now),
            "yesterday": (today - timedelta(days=1), today - timedelta(seconds=1)),
            "this_week": (today - timedelta(days=today.weekday()), now),
            "last_week": (
                today - timedelta(days=today.weekday() + 7),
                today - timedelta(days=today.weekday() + 1)
            ),
            "this_month": (today.replace(day=1), now),
            "last_month": self._get_last_month_range(today),
            "this_quarter": self._get_current_quarter_range(today, now),
            "last_quarter": self._get_last_quarter_range(today),
            "this_year": (today.replace(month=1, day=1), now),
            "last_year": (
                today.replace(year=today.year - 1, month=1, day=1),
                today.replace(year=today.year - 1, month=12, day=31, hour=23, minute=59, second=59)
            ),
            "ytd": (today.replace(month=1, day=1), now),
            "last_7_days": (today - timedelta(days=7), now),
            "last_30_days": (today - timedelta(days=30), now),
            "last_90_days": (today - timedelta(days=90), now),
        }
        
        if time_range.relative not in time_map:
            raise ValidationError(f"Unsupported relative time: '{time_range.relative}'")
        
        return time_map[time_range.relative]
    
    def _get_last_month_range(self, today: datetime) -> Tuple[datetime, datetime]:
        """Calculate last month date range"""
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(seconds=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0)
        return (last_month_start, last_month_end)
    
    def _get_current_quarter_range(self, today: datetime, now: datetime) -> Tuple[datetime, datetime]:
        """Calculate current quarter date range"""
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        quarter_start = today.replace(month=quarter_month, day=1)
        return (quarter_start, now)
    
    def _get_last_quarter_range(self, today: datetime) -> Tuple[datetime, datetime]:
        """Calculate last quarter date range"""
        current_quarter_month = ((today.month - 1) // 3) * 3 + 1
        if current_quarter_month == 1:
            last_quarter_start = today.replace(year=today.year - 1, month=10, day=1)
        else:
            last_quarter_start = today.replace(month=current_quarter_month - 3, day=1)
        
        last_quarter_end = today.replace(month=current_quarter_month, day=1) - timedelta(seconds=1)
        return (last_quarter_start, last_quarter_end)
```

### Component 5: AST Query Builder

```python
# ast_query_builder.py
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from intent_schema import IntentObject, Filter
from semantic_schema import SemanticModel, Metric, Dimension, Relationship, JoinType
from semantic_validator import SemanticValidator

@dataclass
class SelectColumn:
    """Represents a column in SELECT clause"""
    expression: str
    alias: str
    table: Optional[str] = None
    is_aggregate: bool = False

@dataclass
class JoinClause:
    """Represents a JOIN clause"""
    join_type: JoinType
    table: str
    alias: str
    on_condition: str

@dataclass
class WhereCondition:
    """Represents a WHERE condition"""
    condition: str

@dataclass
class GroupByColumn:
    """Represents a column in GROUP BY clause"""
    expression: str
    table: Optional[str] = None

@dataclass
class OrderByColumn:
    """Represents a column in ORDER BY clause"""
    expression: str
    direction: str  # ASC or DESC

class QueryAST:
    """Abstract Syntax Tree for SQL Query"""
    
    def __init__(self):
        self.select_columns: List[SelectColumn] = []
        self.from_table: str = ""
        self.from_alias: str = "f"
        self.joins: List[JoinClause] = []
        self.where_conditions: List[WhereCondition] = []
        self.group_by_columns: List[GroupByColumn] = []
        self.order_by_columns: List[OrderByColumn] = []
        self.limit: Optional[int] = None
    
    def to_sql(self) -> str:
        """Converts AST to SQL string"""
        sql_parts = []
        
        # SELECT clause
        select_exprs = [
            f"{col.expression} AS {col.alias}" for col in self.select_columns
        ]
        sql_parts.append(f"SELECT {', '.join(select_exprs)}")
        
        # FROM clause
        sql_parts.append(f"FROM {self.from_table} {self.from_alias}")
        
        # JOIN clauses
        for join in self.joins:
            sql_parts.append(
                f"{join.join_type.value} {join.table} {join.alias} ON {join.on_condition}"
            )
        
        # WHERE clause
        if self.where_conditions:
            conditions = [wc.condition for wc in self.where_conditions]
            sql_parts.append(f"WHERE {' AND '.join(conditions)}")
        
        # GROUP BY clause
        if self.group_by_columns:
            group_exprs = [col.expression for col in self.group_by_columns]
            sql_parts.append(f"GROUP BY {', '.join(group_exprs)}")
        
        # ORDER BY clause
        if self.order_by_columns:
            order_exprs = [
                f"{col.expression} {col.direction}" for col in self.order_by_columns
            ]
            sql_parts.append(f"ORDER BY {', '.join(order_exprs)}")
        
        # LIMIT clause
        if self.limit:
            sql_parts.append(f"LIMIT {self.limit}")
        
        return "\n".join(sql_parts)


class ASTQueryBuilder:
    """Builds SQL query from validated intent using AST"""
    
    def __init__(self, semantic_model: SemanticModel):
        self.model = semantic_model
        self.validator = SemanticValidator(semantic_model)
        self.table_aliases: Dict[str, str] = {}
    
    def build_query(self, intent: IntentObject) -> str:
        """Main entry point - builds SQL from intent"""
        # Step 1: Validate and resolve intent
        resolved_intent, required_tables = self.validator.validate_and_resolve(intent)
        
        # Step 2: Initialize AST
        ast = QueryAST()
        ast.from_table = self.model.fact_table
        ast.from_alias = "f"
        self.table_aliases = {self.model.fact_table: "f"}
        
        # Step 3: Build JOIN clauses
        self._build_joins(ast, required_tables)
        
        # Step 4: Build SELECT clause (metrics and dimensions)
        self._build_select(ast, resolved_intent)
        
        # Step 5: Build WHERE clause (filters and time range)
        self._build_where(ast, resolved_intent)
        
        # Step 6: Build GROUP BY clause
        self._build_group_by(ast, resolved_intent)
        
        # Step 7: Build ORDER BY clause
        self._build_order_by(ast, resolved_intent)
        
        # Step 8: Apply LIMIT
        ast.limit = resolved_intent.limit
        
        # Step 9: Generate SQL
        return ast.to_sql()
    
    def _build_joins(self, ast: QueryAST, required_tables: List[str]):
        """Builds JOIN clauses for all required tables"""
        # Assign aliases to dimension tables
        alias_counter = ord('a')
        for table in required_tables:
            if table != self.model.fact_table and table not in self.table_aliases:
                self.table_aliases[table] = chr(alias_counter)
                alias_counter += 1
        
        # Build JOIN clauses
        joined_tables = {self.model.fact_table}
        
        for table in required_tables:
            if table == self.model.fact_table:
                continue
            
            # Find relationship
            relationships = self.model.get_join_path(self.model.fact_table, table)
            
            if not relationships:
                raise ValueError(f"No join path found from {self.model.fact_table} to {table}")
            
            rel = relationships[0]  # Use first relationship
            
            # Determine join direction
            if rel.from_table == self.model.fact_table:
                from_alias = self.table_aliases[rel.from_table]
                to_alias = self.table_aliases[rel.to_table]
                join_condition = f"{from_alias}.{rel.from_column} = {to_alias}.{rel.to_column}"
            else:
                from_alias = self.table_aliases[rel.to_table]
                to_alias = self.table_aliases[rel.from_table]
                join_condition = f"{from_alias}.{rel.to_column} = {to_alias}.{rel.from_column}"
            
            ast.joins.append(JoinClause(
                join_type=rel.join_type,
                table=table,
                alias=self.table_aliases[table],
                on_condition=join_condition
            ))
            
            joined_tables.add(table)
    
    def _build_select(self, ast: QueryAST, intent: IntentObject):
        """Builds SELECT clause with metrics and dimensions"""
        # Add dimensions
        for dim_name in intent.dimensions:
            dim = self.model.dimensions[dim_name]
            table_alias = self.table_aliases[dim.table]
            
            ast.select_columns.append(SelectColumn(
                expression=f"{table_alias}.{dim.column}",
                alias=dim_name,
                table=dim.table,
                is_aggregate=False
            ))
        
        # Add metrics
        for metric_name in intent.metrics:
            metric = self.model.metrics[metric_name]
            
            # Build metric expression with table alias
            if '.' not in metric.expression:
                # Simple column reference
                fact_alias = self.table_aliases[self.model.fact_table]
                column_expr = f"{fact_alias}.{metric.expression}"
            else:
                # Complex expression - replace table references with aliases
                column_expr = metric.expression
                for table, alias in self.table_aliases.items():
                    column_expr = column_expr.replace(f"{table}.", f"{alias}.")
            
            # Apply aggregation
            agg_expr = f"{metric.aggregation.value}({column_expr})"
            
            ast.select_columns.append(SelectColumn(
                expression=agg_expr,
                alias=metric_name,
                is_aggregate=True
            ))
    
    def _build_where(self, ast: QueryAST, intent: IntentObject):
        """Builds WHERE clause with filters and time ranges"""
        # Add dimension filters
        for filter_obj in intent.filters:
            dim = self.model.dimensions[filter_obj.dimension]
            table_alias = self.table_aliases[dim.table]
            column_ref = f"{table_alias}.{dim.column}"
            
            condition = self._build_filter_condition(column_ref, filter_obj, dim.data_type)
            ast.where_conditions.append(WhereCondition(condition=condition))
        
        # Add time range filter
        if intent.time_range:
            time_dim = self.model.dimensions[intent.time_range.dimension]
            table_alias = self.table_aliases[time_dim.table]
            column_ref = f"{table_alias}.{time_dim.column}"
            
            start_date, end_date = self.validator.resolve_time_range(intent.time_range)
            
            condition = f"{column_ref} BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'"
            ast.where_conditions.append(WhereCondition(condition=condition))
    
    def _build_filter_condition(self, column_ref: str, filter_obj: Filter, data_type) -> str:
        """Builds a single filter condition"""
        from semantic_schema import DataType
        
        operator = filter_obj.operator
        value = filter_obj.value
        
        # Handle NULL checks
        if operator in ["IS NULL", "IS NOT NULL"]:
            return f"{column_ref} {operator}"
        
        # Handle IN/NOT IN
        if operator in ["IN", "NOT IN"]:
            if data_type in [DataType.STRING, DataType.DATE]:
                value_list = "', '".join(str(v) for v in value)
                return f"{column_ref} {operator} ('{value_list}')"
            else:
                value_list = ", ".join(str(v) for v in value)
                return f"{column_ref} {operator} ({value_list})"
        
        # Handle LIKE
        if operator == "LIKE":
            return f"{column_ref} LIKE '{value}'"
        
        # Handle BETWEEN
        if operator == "BETWEEN":
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("BETWEEN operator requires a list of 2 values")
            if data_type in [DataType.STRING, DataType.DATE]:
                return f"{column_ref} BETWEEN '{value[0]}' AND '{value[1]}'"
            else:
                return f"{column_ref} BETWEEN {value[0]} AND {value[1]}"
        
        # Handle standard comparisons
        if data_type in [DataType.STRING, DataType.DATE]:
            return f"{column_ref} {operator} '{value}'"
        else:
            return f"{column_ref} {operator} {value}"
    
    def _build_group_by(self, ast: QueryAST, intent: IntentObject):
        """Builds GROUP BY clause"""
        # Only add GROUP BY if we have aggregations
        if intent.metrics:
            for dim_name in intent.dimensions:
                dim = self.model.dimensions[dim_name]
                table_alias = self.table_aliases[dim.table]
                
                ast.group_by_columns.append(GroupByColumn(
                    expression=f"{table_alias}.{dim.column}",
                    table=dim.table
                ))
    
    def _build_order_by(self, ast: QueryAST, intent: IntentObject):
        """Builds ORDER BY clause"""
        for sort_spec in intent.sort_by:
            # Check if it's a metric or dimension
            if sort_spec.field in self.model.metrics:
                # It's a metric - use the alias
                ast.order_by_columns.append(OrderByColumn(
                    expression=sort_spec.field,
                    direction=sort_spec.direction
                ))
            elif sort_spec.field in self.model.dimensions:
                # It's a dimension - use the alias
                ast.order_by_columns.append(OrderByColumn(
                    expression=sort_spec.field,
                    direction=sort_spec.direction
                ))
```

### Component 6: Intent Recognition (LLM Integration)

```python
# intent_recognizer.py
import anthropic
import json
from typing import Optional
from intent_schema import IntentObject
from pydantic import ValidationError

class IntentRecognizer:
    """Uses Claude to extract structured intent from natural language"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def extract_intent(self, user_query: str, conversation_history: Optional[list] = None) -> IntentObject:
        """
        Extracts structured intent from natural language query.
        Returns IntentObject with metrics, dimensions, filters, etc.
        """
        
        system_prompt = self._build_system_prompt()
        
        # Build messages
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({
            "role": "user",
            "content": user_query
        })
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0,  # Deterministic for extraction
                system=system_prompt,
                messages=messages
            )
            
            # Extract JSON from response
            response_text = response.content[0].text
            
            # Parse JSON
            try:
                intent_dict = json.loads(response_text)
                intent = IntentObject(**intent_dict)
                return intent
            except (json.JSONDecodeError, ValidationError) as e:
                # Try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                    intent_dict = json.loads(json_str)
                    intent = IntentObject(**intent_dict)
                    return intent
                else:
                    raise ValueError(f"Failed to parse intent: {e}\nResponse: {response_text}")
        
        except Exception as e:
            raise RuntimeError(f"Intent recognition failed: {e}")
    
    def _build_system_prompt(self) -> str:
        """Builds the system prompt for intent extraction"""
        return """You are an expert at extracting structured analytics intent from natural language queries about retail sales data.

Your task is to analyze user questions and extract a structured JSON object representing their analytical intent.

Available Metrics:
- total_sales (synonyms: revenue, sales, sales revenue)
- quantity (synonyms: units, volume, units sold)
- profit (synonyms: gross profit, margin amount)
- avg_unit_price (synonyms: average price)
- total_discount (synonyms: discount, discounts)
- transaction_count (synonyms: number of transactions, txn count, order count)
- avg_transaction_value (synonyms: avg order value, average basket)

Available Dimensions:
Time: date, year, quarter, month, week, day_of_week
Product: product_name, category, subcategory, brand
Geography: store_name, region, state, city
Customer: customer_segment

Filter Operators: =, !=, >, <, >=, <=, IN, NOT IN, LIKE, BETWEEN, IS NULL, IS NOT NULL

Relative Time Expressions:
- today, yesterday
- this_week, last_week
- this_month, last_month
- this_quarter, last_quarter
- this_year, last_year, ytd
- last_7_days, last_30_days, last_90_days

IMPORTANT RULES:
1. Return ONLY valid JSON matching the IntentObject schema
2. Use canonical metric/dimension names (not synonyms) in your output
3. For time-based queries, use the time_range field with relative expressions when possible
4. Default sort_by to the first metric in DESC order if user wants "top" or "highest"
5. If user asks for specific number (e.g., "top 10"), set limit accordingly
6. Be precise with filter operators (IN for multiple values, = for single value)

Output Format:
{
  "metrics": ["total_sales", "profit"],
  "dimensions": ["region", "category"],
  "filters": [
    {"dimension": "state", "operator": "IN", "value": ["CA", "NY"]},
    {"dimension": "total_sales", "operator": ">", "value": 10000}
  ],
  "time_range": {
    "dimension": "date",
    "relative": "last_quarter"
  },
  "sort_by": [
    {"field": "total_sales", "direction": "DESC"}
  ],
  "limit": 10
}

Examples:

User: "Show me top 10 products by revenue in California last quarter"
Output:
{
  "metrics": ["total_sales"],
  "dimensions": ["product_name"],
  "filters": [{"dimension": "state", "operator": "=", "value": "CA"}],
  "time_range": {"dimension": "date", "relative": "last_quarter"},
  "sort_by": [{"field": "total_sales", "direction": "DESC"}],
  "limit": 10
}

User: "What were total sales and profit by region and category this year?"
Output:
{
  "metrics": ["total_sales", "profit"],
  "dimensions": ["region", "category"],
  "time_range": {"dimension": "date", "relative": "this_year"}
}

User: "Compare Electronics vs Clothing sales in the West region"
Output:
{
  "metrics": ["total_sales"],
  "dimensions": ["category"],
  "filters": [
    {"dimension": "category", "operator": "IN", "value": ["Electronics", "Clothing"]},
    {"dimension": "region", "operator": "=", "value": "West"}
  ]
}

Now extract the intent from the user's query. Return ONLY the JSON object, no other text."""


class ResponseGenerator:
    """Uses Claude to generate natural language responses from query results"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate_response(
        self, 
        user_query: str, 
        sql_query: str, 
        results: list,
        intent: IntentObject
    ) -> str:
        """Generates natural language response from query results"""
        
        system_prompt = """You are a data analyst presenting insights from a retail sales database.

Your task is to:
1. Present the query results in a clear, natural language format
2. Highlight key insights and patterns
3. Use proper number formatting (commas for thousands, $ for currency)
4. Be concise but informative
5. Suggest relevant follow-up questions if appropriate

Format guidelines:
- Use markdown tables for structured data
- Bold important numbers
- Use bullet points for key insights
- Keep tone professional but conversational"""
        
        # Build context
        context = f"""User Question: {user_query}

SQL Query Executed:
```sql
{sql_query}
```

Query Results ({len(results)} rows):
```json
{json.dumps(results[:50], indent=2, default=str)}  # Limit to first 50 rows
```

Extracted Intent:
- Metrics: {', '.join(intent.metrics)}
- Dimensions: {', '.join(intent.dimensions)}
- Filters: {len(intent.filters)} applied
- Time Range: {intent.time_range.relative if intent.time_range else 'None'}
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )
            
            return response.content[0].text
        
        except Exception as e:
            return f"Error generating response: {e}"
```

### Component 7: Main Orchestrator

```python
# conversational_sql.py
import sqlite3
from typing import List, Dict
from intent_recognizer import IntentRecognizer, ResponseGenerator
from ast_query_builder import ASTQueryBuilder
from retail_semantic_model import create_retail_semantic_model

class ConversationalSQL:
    """Main orchestrator for conversational SQL system"""
    
    def __init__(self, db_path: str, claude_api_key: str):
        """
        Initialize the conversational SQL system.
        
        Args:
            db_path: Path to SQLite database
            claude_api_key: Anthropic API key for Claude
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        # Initialize components
        self.semantic_model = create_retail_semantic_model()
        self.query_builder = ASTQueryBuilder(self.semantic_model)
        self.intent_recognizer = IntentRecognizer(claude_api_key)
        self.response_generator = ResponseGenerator(claude_api_key)
        
        self.conversation_history = []
    
    def ask(self, question: str, verbose: bool = False) -> Dict:
        """
        Main entry point - ask a question and get results.
        
        Args:
            question: Natural language question
            verbose: If True, returns detailed execution info
        
        Returns:
            Dictionary with results, SQL, intent, and response
        """
        try:
            # Step 1: Extract intent using LLM
            if verbose:
                print(f"\n{'='*60}")
                print(f"USER QUESTION: {question}")
                print(f"{'='*60}\n")
                print("Step 1: Extracting intent...")
            
            intent = self.intent_recognizer.extract_intent(
                question, 
                self.conversation_history
            )
            
            if verbose:
                print(f"✓ Intent extracted:")
                print(f"  Metrics: {intent.metrics}")
                print(f"  Dimensions: {intent.dimensions}")
                print(f"  Filters: {len(intent.filters)}")
                if intent.time_range:
                    print(f"  Time Range: {intent.time_range.relative or 'custom dates'}")
            
            # Step 2: Build SQL query (no LLM involved!)
            if verbose:
                print("\nStep 2: Building SQL query (deterministic)...")
            
            sql_query = self.query_builder.build_query(intent)
            
            if verbose:
                print(f"✓ SQL generated:\n{sql_query}\n")
            
            # Step 3: Execute query
            if verbose:
                print("Step 3: Executing query...")
            
            cursor = self.conn.cursor()
            cursor.execute(sql_query)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            
            if verbose:
                print(f"✓ Query executed: {len(results)} rows returned\n")
            
            # Step 4: Generate natural language response
            if verbose:
                print("Step 4: Generating response...")
            
            response_text = self.response_generator.generate_response(
                question,
                sql_query,
                results,
                intent
            )
            
            if verbose:
                print(f"✓ Response generated\n")
                print(f"{'='*60}")
                print("RESPONSE:")
                print(f"{'='*60}\n")
                print(response_text)
                print(f"\n{'='*60}\n")
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": question
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return {
                "success": True,
                "question": question,
                "intent": intent.dict(),
                "sql": sql_query,
                "results": results,
                "response": response_text,
                "row_count": len(results)
            }
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if verbose:
                print(f"\n❌ {error_msg}\n")
            
            return {
                "success": False,
                "question": question,
                "error": error_msg
            }
    
    def reset_conversation(self):
        """Clears conversation history"""
        self.conversation_history = []
    
    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
```

### Component 8: Sample Data Generator

```python
# generate_sample_data.py
import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

def create_database(db_path: str = "retail_sales.db"):
    """Creates and populates sample retail sales database"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS fact_sales")
    cursor.execute("DROP TABLE IF EXISTS dim_date")
    cursor.execute("DROP TABLE IF EXISTS dim_product")
    cursor.execute("DROP TABLE IF EXISTS dim_store")
    cursor.execute("DROP TABLE IF EXISTS dim_customer")
    
    # Create dim_date
    print("Creating dim_date...")
    cursor.execute("""
        CREATE TABLE dim_date (
            date_id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            month INTEGER NOT NULL,
            week INTEGER NOT NULL,
            day_of_week VARCHAR(20) NOT NULL
        )
    """)
    
    # Populate dim_date (2 years of data)
    start_date = datetime(2024, 1, 1)
    dates = []
    for i in range(730):  # 2 years
        current_date = start_date + timedelta(days=i)
        dates.append((
            int(current_date.strftime('%Y%m%d')),
            current_date.strftime('%Y-%m-%d'),
            current_date.year,
            (current_date.month - 1) // 3 + 1,
            current_date.month,
            current_date.isocalendar()[1],
            current_date.strftime('%A')
        ))
    
    cursor.executemany("""
        INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?, ?)
    """, dates)
    
    # Create dim_product
    print("Creating dim_product...")
    cursor.execute("""
        CREATE TABLE dim_product (
            product_id INTEGER PRIMARY KEY,
            product_name VARCHAR(200) NOT NULL,
            category VARCHAR(100) NOT NULL,
            subcategory VARCHAR(100) NOT NULL,
            brand VARCHAR(100) NOT NULL
        )
    """)
    
    # Populate dim_product
    categories = {
        'Electronics': {
            'subcategories': ['Laptops', 'Smartphones', 'Tablets', 'Accessories'],
            'brands': ['Apple', 'Samsung', 'Dell', 'HP', 'Lenovo']
        },
        'Clothing': {
            'subcategories': ['Men', 'Women', 'Kids', 'Accessories'],
            'brands': ['Nike', 'Adidas', 'Levi\'s', 'Gap', 'H&M']
        },
        'Home & Garden': {
            'subcategories': ['Furniture', 'Decor', 'Kitchen', 'Outdoor'],
            'brands': ['IKEA', 'Wayfair', 'Home Depot', 'Lowe\'s']
        },
        'Sports': {
            'subcategories': ['Equipment', 'Apparel', 'Footwear', 'Accessories'],
            'brands': ['Nike', 'Under Armour', 'Wilson', 'Spalding']
        },
        'Books': {
            'subcategories': ['Fiction', 'Non-Fiction', 'Children', 'Educational'],
            'brands': ['Penguin', 'Harper Collins', 'Random House', 'Scholastic']
        }
    }
    
    products = []
    product_id = 1
    for category, details in categories.items():
        for subcategory in details['subcategories']:
            for brand in details['brands']:
                for i in range(5):  # 5 products per brand/subcategory
                    product_name = f"{brand} {subcategory} {fake.word().title()} {i+1}"
                    products.append((
                        product_id,
                        product_name,
                        category,
                        subcategory,
                        brand
                    ))
                    product_id += 1
    
    cursor.executemany("""
        INSERT INTO dim_product VALUES (?, ?, ?, ?, ?)
    """, products)
    
    # Create dim_store
    print("Creating dim_store...")
    cursor.execute("""
        CREATE TABLE dim_store (
            store_id INTEGER PRIMARY KEY,
            store_name VARCHAR(200) NOT NULL,
            region VARCHAR(100) NOT NULL,
            state VARCHAR(100) NOT NULL,
            city VARCHAR(100) NOT NULL
        )
    """)
    
    # Populate dim_store
    regions = {
        'West': ['CA', 'WA', 'OR', 'NV', 'AZ'],
        'East': ['NY', 'MA', 'PA', 'NJ', 'FL'],
        'Central': ['TX', 'IL', 'OH', 'MI', 'MO'],
        'South': ['GA', 'NC', 'VA', 'TN', 'LA']
    }
    
    stores = []
    store_id = 1
    for region, states in regions.items():
        for state in states:
            for i in range(3):  # 3 stores per state
                city = fake.city()
                stores.append((
                    store_id,
                    f"Store {store_id} - {city}",
                    region,
                    state,
                    city
                ))
                store_id += 1
    
    cursor.executemany("""
        INSERT INTO dim_store VALUES (?, ?, ?, ?, ?)
    """, stores)
    
    # Create dim_customer
    print("Creating dim_customer...")
    cursor.execute("""
        CREATE TABLE dim_customer (
            customer_id INTEGER PRIMARY KEY,
            customer_segment VARCHAR(50) NOT NULL,
            customer_type VARCHAR(50) NOT NULL
        )
    """)
    
    # Populate dim_customer
    customers = []
    segments = ['Enterprise', 'SMB', 'Consumer']
    types = ['New', 'Returning', 'VIP']
    
    for customer_id in range(1, 1001):  # 1000 customers
        customers.append((
            customer_id,
            random.choice(segments),
            random.choice(types)
        ))
    
    cursor.executemany("""
        INSERT INTO dim_customer VALUES (?, ?, ?)
    """, customers)
    
    # Create fact_sales
    print("Creating fact_sales...")
    cursor.execute("""
        CREATE TABLE fact_sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            discount_amount DECIMAL(10,2) NOT NULL,
            sales_amount DECIMAL(10,2) NOT NULL,
            cost_amount DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
            FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
            FOREIGN KEY (store_id) REFERENCES dim_store(store_id),
            FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id)
        )
    """)
    
    # Populate fact_sales (100,000 transactions)
    print("Populating fact_sales (this may take a minute)...")
    
    # Get valid IDs
    cursor.execute("SELECT date_id FROM dim_date")
    date_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT product_id FROM dim_product")
    product_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT store_id FROM dim_store")
    store_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT customer_id FROM dim_customer")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    sales = []
    for _ in range(100000):
        quantity = random.randint(1, 10)
        unit_price = round(random.uniform(10, 500), 2)
        discount_pct = random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20])  # Most sales have no discount
        discount_amount = round(unit_price * quantity * discount_pct, 2)
        sales_amount = round(unit_price * quantity - discount_amount, 2)
        cost_amount = round(sales_amount * random.uniform(0.4, 0.7), 2)  # 30-60% margin
        
        sales.append((
            random.choice(date_ids),
            random.choice(product_ids),
            random.choice(store_ids),
            random.choice(customer_ids),
            quantity,
            unit_price,
            discount_amount,
            sales_amount,
            cost_amount
        ))
    
    cursor.executemany("""
        INSERT INTO fact_sales (date_id, product_id, store_id, customer_id, quantity, 
                               unit_price, discount_amount, sales_amount, cost_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sales)
    
    conn.commit()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("DATABASE CREATED SUCCESSFULLY")
    print("="*60)
    
    cursor.execute("SELECT COUNT(*) FROM dim_date")
    print(f"dim_date: {cursor.fetchone()[0]:,} rows")
    
    cursor.execute("SELECT COUNT(*) FROM dim_product")
    print(f"dim_product: {cursor.fetchone()[0]:,} rows")
    
    cursor.execute("SELECT COUNT(*) FROM dim_store")
    print(f"dim_store: {cursor.fetchone()[0]:,} rows")
    
    cursor.execute("SELECT COUNT(*) FROM dim_customer")
    print(f"dim_customer: {cursor.fetchone()[0]:,} rows")
    
    cursor.execute("SELECT COUNT(*) FROM fact_sales")
    print(f"fact_sales: {cursor.fetchone()[0]:,} rows")
    
    cursor.execute("SELECT SUM(sales_amount) FROM fact_sales")
    total_sales = cursor.fetchone()[0]
    print(f"\nTotal Sales: ${total_sales:,.2f}")
    
    print("="*60 + "\n")
    
    conn.close()

if __name__ == "__main__":
    create_database("retail_sales.db")
```

---

## Complete Working Code

### Demo Script

```python
# demo.py
"""
Conversational AI over SQL - Complete Demo
No LLM-generated SQL - Uses Semantic Layer + AST approach
"""

from conversational_sql import ConversationalSQL
from generate_sample_data import create_database
import os

def main():
    """Main demo function"""
    
    # Setup
    db_path = "retail_sales.db"
    
    # Get Claude API key
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not claude_api_key:
        print("ERROR: Please set ANTHROPIC_API_KEY environment variable")
        return
    
    # Create sample database if it doesn't exist
    if not os.path.exists(db_path):
        print("Creating sample database...")
        create_database(db_path)
    else:
        print(f"Using existing database: {db_path}")
    
    # Initialize conversational SQL system
    print("\nInitializing Conversational SQL system...")
    chatbot = ConversationalSQL(db_path, claude_api_key)
    print("✓ System ready!\n")
    
    # Test queries
    test_queries = [
        "Show me top 10 products by revenue in California last quarter",
        "What were total sales and profit by region this year?",
        "Compare Electronics vs Clothing sales in the West region",
        "Which states had the highest average transaction value last month?",
        "Show me sales trend by month for the last 6 months",
        "What are the top 5 brands by profit in Q4 2024?",
        "How many transactions did we have in Texas last week?",
        "Show me total sales by customer segment and product category",
    ]
    
    print("="*70)
    print("RUNNING TEST QUERIES")
    print("="*70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'='*70}")
        print(f"TEST QUERY #{i}")
        print(f"{'='*70}")
        
        result = chatbot.ask(query, verbose=True)
        
        if not result['success']:
            print(f"\n❌ Query failed: {result['error']}")
        
        # Optional: wait for user input between queries
        if i < len(test_queries):
            input("\nPress Enter to continue to next query...")
    
    print("\n\n" + "="*70)
    print("DEMO COMPLETED")
    print("="*70)

if __name__ == "__main__":
    main()
```

### Installation Requirements

```python
# requirements.txt
anthropic>=0.40.0
pydantic>=2.0.0
faker>=20.0.0
```

### Setup Instructions

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Claude API key
export ANTHROPIC_API_KEY="your-api-key-here"

# 3. Run the demo
python demo.py
```

---

## Testing & Validation

### Unit Tests

```python
# test_semantic_layer.py
import unittest
from intent_schema import IntentObject, Filter, TimeRange
from retail_semantic_model import create_retail_semantic_model
from semantic_validator import SemanticValidator

class TestSemanticValidator(unittest.TestCase):
    
    def setUp(self):
        self.model = create_retail_semantic_model()
        self.validator = SemanticValidator(self.model)
    
    def test_metric_resolution(self):
        """Test metric synonym resolution"""
        intent = IntentObject(
            metrics=["revenue", "units"],  # Synonyms
            dimensions=["region"]
        )
        
        resolved, tables = self.validator.validate_and_resolve(intent)
        
        self.assertIn("total_sales", resolved.metrics)
        self.assertIn("quantity", resolved.metrics)
    
    def test_dimension_resolution(self):
        """Test dimension synonym resolution"""
        intent = IntentObject(
            metrics=["total_sales"],
            dimensions=["area"]  # Synonym for region
        )
        
        resolved, tables = self.validator.validate_and_resolve(intent)
        
        self.assertIn("region", resolved.dimensions)
    
    def test_invalid_metric(self):
        """Test validation error for invalid metric"""
        intent = IntentObject(
            metrics=["invalid_metric"],
            dimensions=["region"]
        )
        
        with self.assertRaises(Exception):
            self.validator.validate_and_resolve(intent)
    
    def test_time_range_resolution(self):
        """Test relative time range resolution"""
        from datetime import datetime
        
        time_range = TimeRange(
            dimension="date",
            relative="last_7_days"
        )
        
        start, end = self.validator.resolve_time_range(time_range)
        
        self.assertIsInstance(start, datetime)
        self.assertIsInstance(end, datetime)
        self.assertLess(start, end)

if __name__ == "__main__":
    unittest.main()
```

### Integration Tests

```python
# test_query_builder.py
import unittest
from intent_schema import IntentObject, Filter, TimeRange, SortBy
from ast_query_builder import ASTQueryBuilder
from retail_semantic_model import create_retail_semantic_model

class TestQueryBuilder(unittest.TestCase):
    
    def setUp(self):
        self.model = create_retail_semantic_model()
        self.builder = ASTQueryBuilder(self.model)
    
    def test_simple_aggregation(self):
        """Test simple metric aggregation"""
        intent = IntentObject(
            metrics=["total_sales"],
            dimensions=["region"]
        )
        
        sql = self.builder.build_query(intent)
        
        self.assertIn("SUM(f.sales_amount)", sql)
        self.assertIn("GROUP BY", sql)
        self.assertIn("dim_store", sql)
    
    def test_multiple_dimensions(self):
        """Test query with multiple dimensions"""
        intent = IntentObject(
            metrics=["total_sales", "quantity"],
            dimensions=["region", "category"]
        )
        
        sql = self.builder.build_query(intent)
        
        self.assertIn("dim_store", sql)
        self.assertIn("dim_product", sql)
        self.assertEqual(sql.count("JOIN"), 2)
    
    def test_filters(self):
        """Test WHERE clause generation"""
        intent = IntentObject(
            metrics=["total_sales"],
            dimensions=["region"],
            filters=[
                Filter(dimension="state", operator="=", value="CA")
            ]
        )
        
        sql = self.builder.build_query(intent)
        
        self.assertIn("WHERE", sql)
        self.assertIn("'CA'", sql)
    
    def test_time_range(self):
        """Test time range filtering"""
        intent = IntentObject(
            metrics=["total_sales"],
            dimensions=["region"],
            time_range=TimeRange(
                dimension="date",
                relative="last_quarter"
            )
        )
        
        sql = self.builder.build_query(intent)
        
        self.assertIn("BETWEEN", sql)
        self.assertIn("dim_date", sql)
    
    def test_ordering_and_limit(self):
        """Test ORDER BY and LIMIT"""
        intent = IntentObject(
            metrics=["total_sales"],
            dimensions=["region"],
            sort_by=[SortBy(field="total_sales", direction="DESC")],
            limit=10
        )
        
        sql = self.builder.build_query(intent)
        
        self.assertIn("ORDER BY", sql)
        self.assertIn("DESC", sql)
        self.assertIn("LIMIT 10", sql)

if __name__ == "__main__":
    unittest.main()
```

---

## Production Deployment

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                        │
│  - Web UI (React/Vue)                                    │
│  - Mobile App (React Native)                             │
│  - Teams/Slack Bot                                       │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTPS/WebSocket
                     ▼
┌──────────────────────────────────────────────────────────┐
│                     API GATEWAY                           │
│  - Authentication (JWT/OAuth)                            │
│  - Rate Limiting                                          │
│  - Request Routing                                        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│               CONVERSATIONAL SQL ENGINE                   │
│  ┌────────────────────────────────────────────────┐      │
│  │ Intent Recognizer (Claude API)                │      │
│  │ - Caching layer                                │      │
│  │ - Retry logic                                  │      │
│  └────────────────┬───────────────────────────────┘      │
│                   │                                       │
│  ┌────────────────┴───────────────────────────────┐      │
│  │ Semantic Validator                            │      │
│  │ - Schema validation                            │      │
│  │ - Permission checks                            │      │
│  └────────────────┬───────────────────────────────┘      │
│                   │                                       │
│  ┌────────────────┴───────────────────────────────┐      │
│  │ Query Builder (AST)                            │      │
│  │ - SQL generation                               │      │
│  │ - Query optimization                           │      │
│  └────────────────┬───────────────────────────────┘      │
│                   │                                       │
│  ┌────────────────┴───────────────────────────────┐      │
│  │ Response Generator (Claude API)                │      │
│  │ - Natural language formatting                  │      │
│  │ - Visualization hints                          │      │
│  └────────────────────────────────────────────────┘      │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                     DATA LAYER                            │
│  - Redshift/Snowflake (OLAP)                             │
│  - Connection Pooling                                     │
│  - Query Result Caching (Redis)                          │
└──────────────────────────────────────────────────────────┘
```

### FastAPI Production Server

```python
# app.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from conversational_sql import ConversationalSQL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Conversational SQL API",
    description="Natural language to SQL conversion API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance (consider using dependency injection for scalability)
chatbot: Optional[ConversationalSQL] = None

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    global chatbot
    db_path = os.getenv("DATABASE_PATH", "retail_sales.db")
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not claude_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")
    
    chatbot = ConversationalSQL(db_path, claude_api_key)
    logger.info("Conversational SQL system initialized")

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    verbose: bool = False
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    question: str
    intent: Optional[dict] = None
    sql: Optional[str] = None
    results: Optional[list] = None
    response: Optional[str] = None
    row_count: Optional[int] = None
    error: Optional[str] = None

# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "conversational-sql"}

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute natural language query
    
    Args:
        request: QueryRequest containing the question
    
    Returns:
        QueryResponse with results and metadata
    """
    try:
        logger.info(f"Received query: {request.question}")
        
        result = chatbot.ask(request.question, verbose=request.verbose)
        
        return QueryResponse(**result)
    
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset_conversation():
    """Reset conversation history"""
    chatbot.reset_conversation()
    return {"status": "conversation reset"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_PATH=/data/retail_sales.db
    volumes:
      - ./data:/data
    restart: unless-stopped
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

### Security Considerations

```python
# security_middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import time

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for API protection"""
    
    def __init__(self, app, api_keys: set):
        super().__init__(app)
        self.api_keys = api_keys
        self.rate_limits = {}  # IP -> (count, timestamp)
    
    async def dispatch(self, request: Request, call_next):
        # 1. API Key validation
        api_key = request.headers.get("X-API-Key")
        if api_key not in self.api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # 2. Rate limiting (simple implementation)
        client_ip = request.client.host
        current_time = time.time()
        
        if client_ip in self.rate_limits:
            count, timestamp = self.rate_limits[client_ip]
            if current_time - timestamp < 60:  # 1 minute window
                if count >= 60:  # 60 requests per minute
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                self.rate_limits[client_ip] = (count + 1, timestamp)
            else:
                self.rate_limits[client_ip] = (1, current_time)
        else:
            self.rate_limits[client_ip] = (1, current_time)
        
        # 3. SQL injection prevention (handled by parameterized queries)
        # Our AST builder uses parameterized queries, preventing SQL injection
        
        response = await call_next(request)
        return response
```

---

## Alternative: BFSI Implementation

### Banking Domain Semantic Model

```python
# bfsi_semantic_model.py
"""
BFSI (Banking, Financial Services, Insurance) Semantic Model
Example: Credit Card Transaction Analytics
"""

from semantic_schema import *

def create_bfsi_semantic_model() -> SemanticModel:
    """Creates semantic model for credit card transactions"""
    
    return SemanticModel(
        name="credit_card_analytics",
        fact_table="fact_transactions",
        dimension_tables=["dim_date", "dim_card", "dim_merchant", "dim_customer", "dim_location"],
        
        dimensions={
            # Time dimensions
            "transaction_date": Dimension(
                name="transaction_date",
                display_name="Transaction Date",
                column="transaction_date",
                table="dim_date",
                data_type=DataType.DATE,
                description="Date of transaction",
                synonyms=["date", "txn date"],
                is_temporal=True
            ),
            
            # Card dimensions
            "card_type": Dimension(
                name="card_type",
                display_name="Card Type",
                column="card_type",
                table="dim_card",
                data_type=DataType.STRING,
                description="Type of card (Credit, Debit, Prepaid)",
                synonyms=["type"]
            ),
            "card_tier": Dimension(
                name="card_tier",
                display_name="Card Tier",
                column="card_tier",
                table="dim_card",
                data_type=DataType.STRING,
                description="Card tier (Platinum, Gold, Silver, Basic)",
                synonyms=["tier", "card level"]
            ),
            
            # Merchant dimensions
            "merchant_category": Dimension(
                name="merchant_category",
                display_name="Merchant Category",
                column="merchant_category",
                table="dim_merchant",
                data_type=DataType.STRING,
                description="MCC category",
                synonyms=["mcc", "category", "merchant type"]
            ),
            "merchant_name": Dimension(
                name="merchant_name",
                display_name="Merchant Name",
                column="merchant_name",
                table="dim_merchant",
                data_type=DataType.STRING,
                description="Merchant name",
                synonyms=["merchant", "vendor"]
            ),
            
            # Customer dimensions
            "customer_segment": Dimension(
                name="customer_segment",
                display_name="Customer Segment",
                column="customer_segment",
                table="dim_customer",
                data_type=DataType.STRING,
                description="Customer segment (Premium, Regular, New)",
                synonyms=["segment"]
            ),
            "age_group": Dimension(
                name="age_group",
                display_name="Age Group",
                column="age_group",
                table="dim_customer",
                data_type=DataType.STRING,
                description="Customer age group",
                synonyms=["age bracket", "age range"]
            ),
            
            # Location dimensions
            "country": Dimension(
                name="country",
                display_name="Country",
                column="country",
                table="dim_location",
                data_type=DataType.STRING,
                description="Transaction country",
                synonyms=[]
            ),
            "city": Dimension(
                name="city",
                display_name="City",
                column="city",
                table="dim_location",
                data_type=DataType.STRING,
                description="Transaction city",
                synonyms=[]
            ),
        },
        
        metrics={
            "transaction_amount": Metric(
                name="transaction_amount",
                display_name="Transaction Amount",
                expression="transaction_amount",
                aggregation=AggregationType.SUM,
                data_type=DataType.DECIMAL,
                description="Total transaction amount",
                synonyms=["spend", "amount", "volume"],
                dependencies=["fact_transactions"],
                format_string="${:,.2f}"
            ),
            "transaction_count": Metric(
                name="transaction_count",
                display_name="Transaction Count",
                expression="transaction_id",
                aggregation=AggregationType.COUNT_DISTINCT,
                data_type=DataType.INTEGER,
                description="Number of transactions",
                synonyms=["txn count", "number of transactions"],
                dependencies=["fact_transactions"],
                format_string="{:,}"
            ),
            "avg_transaction_value": Metric(
                name="avg_transaction_value",
                display_name="Average Transaction Value",
                expression="transaction_amount",
                aggregation=AggregationType.AVG,
                data_type=DataType.DECIMAL,
                description="Average transaction value",
                synonyms=["avg txn", "average spend"],
                dependencies=["fact_transactions"],
                format_string="${:,.2f}"
            ),
            "approval_rate": Metric(
                name="approval_rate",
                display_name="Approval Rate",
                expression="CASE WHEN status = 'Approved' THEN 1.0 ELSE 0.0 END",
                aggregation=AggregationType.AVG,
                data_type=DataType.FLOAT,
                description="Transaction approval rate",
                synonyms=["success rate"],
                dependencies=["fact_transactions"],
                format_string="{:.1%}"
            ),
            "fraud_rate": Metric(
                name="fraud_rate",
                display_name="Fraud Rate",
                expression="CASE WHEN is_fraud = 1 THEN 1.0 ELSE 0.0 END",
                aggregation=AggregationType.AVG,
                data_type=DataType.FLOAT,
                description="Fraud transaction rate",
                synonyms=["fraudulent rate"],
                dependencies=["fact_transactions"],
                format_string="{:.2%}"
            ),
        },
        
        relationships=[
            Relationship(
                from_table="fact_transactions",
                from_column="date_id",
                to_table="dim_date",
                to_column="date_id",
                relationship_type="many_to_one"
            ),
            Relationship(
                from_table="fact_transactions",
                from_column="card_id",
                to_table="dim_card",
                to_column="card_id",
                relationship_type="many_to_one"
            ),
            Relationship(
                from_table="fact_transactions",
                from_column="merchant_id",
                to_table="dim_merchant",
                to_column="merchant_id",
                relationship_type="many_to_one"
            ),
            Relationship(
                from_table="fact_transactions",
                from_column="customer_id",
                to_table="dim_customer",
                to_column="customer_id",
                relationship_type="many_to_one"
            ),
            Relationship(
                from_table="fact_transactions",
                from_column="location_id",
                to_table="dim_location",
                to_column="location_id",
                relationship_type="many_to_one"
            ),
        ]
    )
```

### BFSI Example Queries

```python
# Example queries for BFSI domain
bfsi_queries = [
    "What was total credit card spend last month?",
    "Show me fraud rate by merchant category",
    "Which age groups have the highest average transaction value?",
    "Compare Platinum vs Gold card usage this quarter",
    "What's the approval rate for international transactions?",
    "Show me top 10 merchants by transaction volume",
    "What percentage of transactions were declined in New York last week?",
    "How does customer spending vary by segment and card type?",
]
```

---

## Conclusion

### Key Advantages of This Approach

✅ **Security** - No SQL injection risks  
✅ **Accuracy** - No schema hallucinations  
✅ **Performance** - Optimized, deterministic queries  
✅ **Maintainability** - Business logic in semantic layer  
✅ **Scalability** - Caching, optimization opportunities  
✅ **Auditability** - Full query logging and lineage  

### Production Checklist

- [ ] Implement comprehensive logging
- [ ] Add query result caching (Redis)
- [ ] Set up monitoring and alerts
- [ ] Implement proper authentication/authorization
- [ ] Add rate limiting
- [ ] Create data governance policies
- [ ] Set up CI/CD pipeline
- [ ] Write comprehensive tests
- [ ] Document semantic model changes
- [ ] Train users on supported queries

### Next Steps

1. **Enhance Semantic Model** - Add more metrics, dimensions, calculated fields
2. **Add Visualization** - Integrate with charting libraries
3. **Multi-tenant Support** - Add org-level isolation
4. **Advanced Analytics** - Time series forecasting, anomaly detection
5. **Voice Interface** - Add speech-to-text integration
6. **Mobile Apps** - Build iOS/Android apps

---

**Created by:** Varun (Senior Data Engineer)  
**Last Updated:** February 2026  
**License:** MIT  
**Repository:** [GitHub Link]
