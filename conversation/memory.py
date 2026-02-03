"""
Conversation Memory - Enables multi-turn conversations
Remembers context, handles follow-ups, resolves pronouns
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    turn_id: int
    timestamp: str
    user_question: str
    parsed_intent: Dict[str, Any]
    sql_query: str
    results_summary: str
    full_response: str
    row_count: int


class ConversationMemory:
    """
    Manages conversation history and context
    Enables follow-up questions and pronoun resolution
    """

    def __init__(self, max_turns: int = 10, persist_file: str = None):
        self.max_turns = max_turns
        self.history: List[ConversationTurn] = []
        self.current_context: Dict[str, Any] = {}
        self.persist_file = persist_file
        self.turn_counter = 0

        # Load previous session if exists
        if persist_file:
            self._load_history()

    def add_turn(
        self,
        user_question: str,
        parsed_intent: Dict[str, Any],
        sql_query: str,
        results: List[Dict],
        response: str
    ) -> ConversationTurn:
        """Add a new conversation turn"""
        self.turn_counter += 1

        # Create summary of results
        results_summary = self._summarize_results(results)

        turn = ConversationTurn(
            turn_id=self.turn_counter,
            timestamp=datetime.now().isoformat(),
            user_question=user_question,
            parsed_intent=parsed_intent,
            sql_query=sql_query,
            results_summary=results_summary,
            full_response=response,
            row_count=len(results)
        )

        self.history.append(turn)

        # Update current context
        self._update_context(turn, results)

        # Trim old history
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

        # Persist if enabled
        if self.persist_file:
            self._save_history()

        return turn

    def _summarize_results(self, results: List[Dict]) -> str:
        """Create a brief summary of results"""
        if not results:
            return "No results"

        if len(results) == 1:
            return str(results[0])

        return f"{len(results)} rows returned. First: {results[0]}"

    def _update_context(self, turn: ConversationTurn, results: List[Dict]):
        """Update current context based on latest turn"""
        self.current_context = {
            'last_metrics': turn.parsed_intent.get('metrics', []),
            'last_dimensions': turn.parsed_intent.get('group_by', []),
            'last_filters': turn.parsed_intent.get('filters', []),
            'last_time_period': turn.parsed_intent.get('time_period'),
            'last_sql': turn.sql_query,
            'last_results': results[:10] if results else [],  # Keep first 10
            'last_row_count': len(results),
            'last_question': turn.user_question
        }

    def get_context_for_llm(self) -> str:
        """Get formatted context for LLM prompt"""
        if not self.history:
            return "No previous conversation."

        context_parts = ["Previous conversation:"]

        for turn in self.history[-5:]:  # Last 5 turns
            context_parts.append(f"\nUser: {turn.user_question}")
            context_parts.append(f"Result: {turn.results_summary}")

        if self.current_context:
            context_parts.append(f"\nCurrent context:")
            context_parts.append(f"- Last metrics: {self.current_context.get('last_metrics', [])}")
            context_parts.append(f"- Last grouping: {self.current_context.get('last_dimensions', [])}")
            if self.current_context.get('last_filters'):
                context_parts.append(f"- Active filters: {self.current_context.get('last_filters')}")

        return "\n".join(context_parts)

    def get_last_intent(self) -> Optional[Dict[str, Any]]:
        """Get the intent from the last turn"""
        if self.history:
            return self.history[-1].parsed_intent
        return None

    def get_last_results(self) -> List[Dict]:
        """Get results from last query"""
        return self.current_context.get('last_results', [])

    def is_follow_up(self, question: str) -> bool:
        """Detect if this is a follow-up question"""
        if not self.history:
            return False

        follow_up_indicators = [
            'show me more', 'more details', 'what about',
            'instead', 'also', 'and what', 'how about',
            'the same', 'that', 'this', 'it', 'those',
            'break it down', 'drill down', 'filter',
            'last year', 'this year', 'by month', 'by region',
            'top', 'highest', 'lowest', 'compare',
            'why', 'which one', 'who'
        ]

        question_lower = question.lower()
        return any(indicator in question_lower for indicator in follow_up_indicators)

    def resolve_follow_up(self, question: str) -> Dict[str, Any]:
        """
        Resolve follow-up question using context
        Returns modified intent based on previous context
        """
        if not self.history:
            return {}

        last_intent = self.get_last_intent()
        if not last_intent:
            return {}

        resolved = {
            'metrics': last_intent.get('metrics', []).copy(),
            'dimensions': last_intent.get('dimensions', []).copy(),
            'group_by': last_intent.get('group_by', []).copy(),
            'filters': last_intent.get('filters', []).copy(),
            'time_period': last_intent.get('time_period'),
            'is_follow_up': True,
            'base_question': self.current_context.get('last_question', '')
        }

        question_lower = question.lower()

        # Handle "by month" / "by region" modifications
        if 'by month' in question_lower:
            resolved['group_by'] = ['month_name']
        elif 'by year' in question_lower:
            resolved['group_by'] = ['year']
        elif 'by region' in question_lower:
            resolved['group_by'] = ['region']
        elif 'by customer' in question_lower or 'by segment' in question_lower:
            resolved['group_by'] = ['customer_segment']

        # Handle time period changes
        if 'last year' in question_lower:
            resolved['time_period'] = "d_date.year = YEAR(CURRENT_DATE) - 1"
        elif 'this year' in question_lower:
            resolved['time_period'] = "d_date.year = YEAR(CURRENT_DATE)"
        elif 'last month' in question_lower:
            resolved['time_period'] = "d_date.month = MONTH(CURRENT_DATE) - 1"

        # Handle filter additions
        if 'premium' in question_lower:
            resolved['filters'].append("customer_segment = 'Premium'")
        elif 'gold' in question_lower:
            resolved['filters'].append("customer_segment = 'Gold'")

        return resolved

    def clear(self):
        """Clear conversation history"""
        self.history = []
        self.current_context = {}
        self.turn_counter = 0

        if self.persist_file:
            self._save_history()

    def _save_history(self):
        """Save history to file"""
        if not self.persist_file:
            return

        path = Path(self.persist_file)
        data = {
            'turns': [asdict(t) for t in self.history],
            'context': self.current_context,
            'turn_counter': self.turn_counter
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_history(self):
        """Load history from file"""
        if not self.persist_file:
            return

        path = Path(self.persist_file)
        if not path.exists():
            return

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            self.history = [
                ConversationTurn(**t) for t in data.get('turns', [])
            ]
            self.current_context = data.get('context', {})
            self.turn_counter = data.get('turn_counter', 0)
        except Exception as e:
            print(f"Could not load history: {e}")

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation for display"""
        if not self.history:
            return "No conversation history"

        lines = [f"Conversation ({len(self.history)} turns):"]
        for turn in self.history[-5:]:
            lines.append(f"  [{turn.turn_id}] Q: {turn.user_question[:50]}...")
            lines.append(f"      → {turn.row_count} results")

        return "\n".join(lines)
