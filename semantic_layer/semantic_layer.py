"""
Core Semantic Layer Implementation
Translates business intent to SQL queries
"""
import yaml
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from .models import Metric, Dimension, QueryIntent, SQLQuery


class SemanticLayer:
    """
    Semantic layer that maps business concepts to database schema
    This is the key component that avoids direct LLM->SQL generation
    """

    def __init__(self, config_path: str):
        """Initialize semantic layer with configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.metrics = self._parse_metrics()
        self.dimensions = self._parse_dimensions()
        self.business_terms = self.config.get('business_terms', {})

    def _load_config(self) -> Dict:
        """Load semantic layer configuration"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _parse_metrics(self) -> Dict[str, Metric]:
        """Parse metrics from configuration"""
        metrics = {}
        for name, config in self.config.get('metrics', {}).items():
            metrics[name] = Metric(
                name=name,
                description=config['description'],
                sql=config['sql'],
                table=config['table'],
                aggregation=config['aggregation'],
                format=config.get('format', 'number')
            )
        return metrics

    def _parse_dimensions(self) -> Dict[str, Dimension]:
        """Parse dimensions from configuration"""
        dimensions = {}
        for name, config in self.config.get('dimensions', {}).items():
            dimensions[name] = Dimension(
                name=name,
                table=config['table'],
                key=config['key'],
                attributes=config['attributes']
            )
        return dimensions

    def get_metric(self, metric_name: str) -> Optional[Metric]:
        """Get metric by name or synonym"""
        # Direct lookup
        if metric_name in self.metrics:
            return self.metrics[metric_name]

        # Check business terms synonyms
        if metric_name in self.business_terms:
            actual_name = self.business_terms[metric_name]
            if actual_name in self.metrics:
                return self.metrics[actual_name]

        return None

    def get_dimension(self, dim_name: str) -> Optional[Dimension]:
        """Get dimension by name or synonym"""
        # Direct lookup
        if dim_name in self.dimensions:
            return self.dimensions[dim_name]

        # Check business terms synonyms
        if dim_name in self.business_terms:
            actual_name = self.business_terms[dim_name]
            if actual_name in self.dimensions:
                return self.dimensions[actual_name]

        return None

    def search_metrics(self, keywords: List[str]) -> List[Metric]:
        """Search for metrics matching keywords"""
        matches = []
        for metric in self.metrics.values():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if (keyword_lower in metric.name.lower() or
                    keyword_lower in metric.description.lower()):
                    matches.append(metric)
                    break
        return matches

    def search_dimensions(self, keywords: List[str]) -> List[Dimension]:
        """Search for dimensions matching keywords"""
        matches = []
        for dimension in self.dimensions.values():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if (keyword_lower in dimension.name.lower() or
                    any(keyword_lower in attr.lower() for attr in dimension.attributes.keys())):
                    matches.append(dimension)
                    break
        return matches

    def intent_to_sql(self, intent: QueryIntent) -> SQLQuery:
        """
        Convert query intent to SQL
        This is where semantic layer translates to SQL, NOT the LLM
        """
        # Build SELECT clause
        select_parts = []

        # Add dimensions to SELECT
        for dim_name in intent.group_by:
            dim = self.get_dimension(dim_name)
            if dim:
                # Use the first attribute or a default one
                attr_name = list(dim.attributes.keys())[0] if dim.attributes else dim_name
                attr_sql = dim.attributes.get(attr_name, attr_name)
                select_parts.append(f"{attr_sql} AS {attr_name}")

        # Add metrics to SELECT
        for metric_name in intent.metrics:
            metric = self.get_metric(metric_name)
            if metric:
                select_parts.append(f"{metric.sql} AS {metric_name}")

        # Build FROM clause
        # Determine which fact table to use based on metrics
        from_table = self._determine_fact_table(intent)

        # Build JOIN clauses
        joins = self._build_joins(intent, from_table)

        # Build WHERE clause
        where_clauses = []
        if intent.filters:
            where_clauses.extend(intent.filters)
        if intent.time_period:
            where_clauses.append(intent.time_period)

        # Build GROUP BY clause
        group_by_parts = []
        for i, dim_name in enumerate(intent.group_by, 1):
            dim = self.get_dimension(dim_name)
            if dim:
                attr_name = list(dim.attributes.keys())[0] if dim.attributes else dim_name
                attr_sql = dim.attributes.get(attr_name, attr_name)
                group_by_parts.append(attr_sql)

        # Construct SQL
        sql_parts = []
        sql_parts.append("SELECT")
        sql_parts.append("  " + ",\n  ".join(select_parts) if select_parts else "  *")
        sql_parts.append(f"FROM {from_table}")

        if joins:
            sql_parts.extend(joins)

        if where_clauses:
            sql_parts.append("WHERE " + " AND ".join(where_clauses))

        if group_by_parts:
            sql_parts.append("GROUP BY " + ", ".join(group_by_parts))

        if intent.limit:
            sql_parts.append(f"LIMIT {intent.limit}")

        sql = "\n".join(sql_parts)

        # Generate explanation
        explanation = self._generate_explanation(intent)

        return SQLQuery(
            sql=sql,
            intent=intent,
            explanation=explanation
        )

    def _determine_fact_table(self, intent: QueryIntent) -> str:
        """Determine which fact table to query based on metrics"""
        # Default to transactions
        fact_table = "fact_transactions ft"

        # Check which metrics are requested
        for metric_name in intent.metrics:
            metric = self.get_metric(metric_name)
            if metric:
                if 'loan' in metric.table.lower():
                    return "fact_loans fl"
                elif 'investment' in metric.table.lower():
                    return "fact_investments fi"

        return fact_table

    def _build_joins(self, intent: QueryIntent, from_table: str) -> List[str]:
        """Build JOIN clauses based on dimensions needed"""
        joins = []
        joined_tables = set()

        # Extract fact table alias
        fact_alias = from_table.split()[-1] if ' ' in from_table else from_table

        # Add joins for dimensions
        for dim_name in intent.group_by + intent.dimensions:
            dim = self.get_dimension(dim_name)
            if dim and dim.table not in joined_tables:
                alias = dim.table.replace('dim_', 'd_')
                joins.append(
                    f"LEFT JOIN {dim.table} {alias} "
                    f"ON {fact_alias}.{dim.key} = {alias}.{dim.key}"
                )
                joined_tables.add(dim.table)

        # Add join for transaction_type if needed for deposits/withdrawals
        if any('deposit' in m or 'withdrawal' in m for m in intent.metrics):
            if 'dim_transaction_type' not in joined_tables:
                joins.append(
                    f"LEFT JOIN dim_transaction_type tt "
                    f"ON {fact_alias}.transaction_type_key = tt.transaction_type_key"
                )

        return joins

    def _generate_explanation(self, intent: QueryIntent) -> str:
        """Generate human-readable explanation of the query"""
        parts = []

        if intent.metrics:
            metrics_str = ", ".join(intent.metrics)
            parts.append(f"Calculating: {metrics_str}")

        if intent.group_by:
            group_str = ", ".join(intent.group_by)
            parts.append(f"Grouped by: {group_str}")

        if intent.filters:
            parts.append(f"Filters applied: {len(intent.filters)}")

        if intent.time_period:
            parts.append(f"Time period: {intent.time_period}")

        return " | ".join(parts) if parts else "Simple query"

    def list_available_metrics(self) -> List[Dict[str, str]]:
        """List all available metrics"""
        return [
            {"name": m.name, "description": m.description}
            for m in self.metrics.values()
        ]

    def list_available_dimensions(self) -> List[Dict[str, str]]:
        """List all available dimensions"""
        return [
            {"name": d.name, "table": d.table, "attributes": list(d.attributes.keys())}
            for d in self.dimensions.values()
        ]
