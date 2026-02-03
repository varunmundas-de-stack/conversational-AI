"""
LLM-based Intent Parser
Uses local Ollama to understand user questions and map to semantic layer
"""
import json
import re
from typing import Dict, List, Optional
import ollama
from semantic_layer.models import QueryIntent
from semantic_layer.semantic_layer import SemanticLayer


class IntentParser:
    """
    Parse user questions into structured query intents
    Uses LLM for understanding, NOT for SQL generation
    """

    def __init__(self, semantic_layer: SemanticLayer, model: str = "llama3.2:3b"):
        self.semantic_layer = semantic_layer
        self.model = model

    def parse(self, question: str) -> QueryIntent:
        """
        Parse user question into QueryIntent
        LLM maps natural language -> semantic concepts, NOT to SQL
        """
        # Get available metrics and dimensions
        metrics_info = self.semantic_layer.list_available_metrics()
        dimensions_info = self.semantic_layer.list_available_dimensions()

        # Build prompt for LLM
        prompt = self._build_prompt(question, metrics_info, dimensions_info)

        # Call local LLM
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a data analyst assistant. Parse user questions into structured query components. Respond ONLY with valid JSON.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.1,  # Low temperature for consistent parsing
                    'num_predict': 500
                }
            )

            # Parse LLM response
            intent_data = self._extract_json(response['message']['content'])

            # Create QueryIntent
            intent = QueryIntent(
                metrics=intent_data.get('metrics', []),
                dimensions=intent_data.get('dimensions', []),
                filters=intent_data.get('filters', []),
                group_by=intent_data.get('group_by', []),
                time_period=intent_data.get('time_period'),
                limit=intent_data.get('limit'),
                original_question=question
            )

            return intent

        except Exception as e:
            print(f"Error parsing intent with LLM: {e}")
            # Fallback to keyword-based parsing
            return self._fallback_parse(question)

    def _build_prompt(self, question: str, metrics: List[Dict], dimensions: List[Dict]) -> str:
        """Build prompt for LLM intent parsing"""
        metrics_str = "\n".join([f"- {m['name']}: {m['description']}" for m in metrics])
        dimensions_str = "\n".join([f"- {d['name']}: {', '.join(d['attributes'])}" for d in dimensions])

        prompt = f"""Parse this user question into structured query components.

Question: "{question}"

Available Metrics:
{metrics_str}

Available Dimensions:
{dimensions_str}

IMPORTANT: Map the question to the available metrics and dimensions. Do NOT generate SQL.

Return a JSON object with:
- "metrics": list of metric names to calculate (e.g., ["total_transactions", "transaction_volume"])
- "group_by": list of dimension names to group by (e.g., ["month_name", "customer_segment"])
- "filters": list of SQL filter conditions (e.g., ["region = 'North'"])
- "time_period": SQL condition for time filtering (e.g., "year = 2024") or null
- "limit": maximum number of rows (integer) or null

Example:
Question: "What is the total transaction volume by month this year?"
Response:
{{
  "metrics": ["transaction_volume"],
  "group_by": ["month_name"],
  "filters": [],
  "time_period": "year = YEAR(CURRENT_DATE)",
  "limit": null
}}

Now parse the user's question and respond ONLY with the JSON object:"""

        return prompt

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # If no valid JSON found, return empty structure
        return {
            'metrics': [],
            'group_by': [],
            'filters': [],
            'time_period': None,
            'limit': None
        }

    def _fallback_parse(self, question: str) -> QueryIntent:
        """
        Fallback keyword-based parsing if LLM fails
        Simple pattern matching approach
        """
        question_lower = question.lower()

        # Detect metrics using keywords
        metrics = []
        if any(word in question_lower for word in ['transaction', 'volume', 'sales']):
            metrics.append('transaction_volume')
        if any(word in question_lower for word in ['count', 'number of', 'how many']):
            metrics.append('total_transactions')
        if 'deposit' in question_lower:
            metrics.append('total_deposits')
        if 'withdrawal' in question_lower:
            metrics.append('total_withdrawals')
        if 'loan' in question_lower:
            metrics.append('total_loan_amount')
        if 'customer' in question_lower and 'count' in question_lower:
            metrics.append('active_customers')

        # Detect grouping dimensions
        group_by = []
        if any(word in question_lower for word in ['by month', 'monthly', 'per month']):
            group_by.append('month_name')
        if any(word in question_lower for word in ['by year', 'yearly', 'annually']):
            group_by.append('year')
        if any(word in question_lower for word in ['by region', 'per region']):
            group_by.append('region')
        if any(word in question_lower for word in ['by customer', 'per customer']):
            group_by.append('customer_segment')
        if any(word in question_lower for word in ['by account type', 'per account']):
            group_by.append('account_type')

        # Detect time period
        time_period = None
        if 'this year' in question_lower:
            time_period = "d_date.year = YEAR(CURRENT_DATE)"
        elif 'last year' in question_lower:
            time_period = "d_date.year = YEAR(CURRENT_DATE) - 1"
        elif 'this month' in question_lower:
            time_period = "d_date.month = MONTH(CURRENT_DATE) AND d_date.year = YEAR(CURRENT_DATE)"

        # Detect limit
        limit = None
        limit_match = re.search(r'top (\d+)', question_lower)
        if limit_match:
            limit = int(limit_match.group(1))

        return QueryIntent(
            metrics=metrics if metrics else ['total_transactions'],
            dimensions=[],
            filters=[],
            group_by=group_by,
            time_period=time_period,
            limit=limit,
            original_question=question
        )

    def generate_natural_response(self, question: str, results: List[Dict], sql_query: str) -> str:
        """
        Generate natural language response from query results
        Uses LLM to format the answer naturally
        """
        if not results:
            return "I couldn't find any data matching your question."

        # Prepare results summary
        results_summary = self._summarize_results(results)

        prompt = f"""User asked: "{question}"

Query Results (showing top {min(len(results), 10)} rows):
{results_summary}

Total rows returned: {len(results)}

Generate a concise, natural language response to the user's question based on these results.
Include key insights and specific numbers. Keep it under 100 words."""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful data analyst. Provide clear, concise answers with specific numbers from the data.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,
                    'num_predict': 200
                }
            )

            return response['message']['content'].strip()

        except Exception as e:
            print(f"Error generating response: {e}")
            # Fallback to simple summary
            return self._simple_summary(results)

    def _summarize_results(self, results: List[Dict], max_rows: int = 10) -> str:
        """Create a text summary of results"""
        if not results:
            return "No data"

        summary_lines = []
        for i, row in enumerate(results[:max_rows], 1):
            row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
            summary_lines.append(f"{i}. {row_str}")

        return "\n".join(summary_lines)

    def _simple_summary(self, results: List[Dict]) -> str:
        """Generate simple summary without LLM"""
        if not results:
            return "No data found."

        summary = f"Found {len(results)} result(s). "

        if results:
            first_row = results[0]
            summary += "Sample: " + ", ".join([f"{k}={v}" for k, v in first_row.items()])

        return summary
