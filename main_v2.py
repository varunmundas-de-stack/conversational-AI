#!/usr/bin/env python3
"""
Conversational AI v2 - True Multi-Turn Conversations
With conversation memory, follow-ups, context awareness, and remote DB support

Architecture:
User Question → Context Check → LLM (Intent) → Semantic Layer → SQL → DB → Results → LLM (Response)
"""
import sys
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.models import QueryIntent
from llm.intent_parser import IntentParser
from conversation.memory import ConversationMemory


class DatabaseManager:
    """Manages database connections - supports DuckDB and PostgreSQL"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.connector = None
        self.db_type = None

    def _load_config(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return {'active': 'local'}

    def connect(self) -> bool:
        """Connect to the configured database"""
        active = self.config.get('active', 'local')

        if active == 'local':
            return self._connect_duckdb()
        elif active == 'postgres':
            return self._connect_postgres()
        else:
            print(f"Unknown database type: {active}")
            return False

    def _connect_duckdb(self) -> bool:
        """Connect to local DuckDB"""
        from connectors.duckdb_connector import DuckDBConnector

        local_config = self.config.get('local', {})
        db_path = local_config.get('path', 'database/bfsi_olap.duckdb')

        # Resolve relative path
        full_path = Path(__file__).parent / db_path

        if not full_path.exists():
            print(f"Database not found: {full_path}")
            return False

        self.connector = DuckDBConnector(str(full_path))
        self.db_type = 'duckdb'
        return self.connector.connect()

    def _connect_postgres(self) -> bool:
        """Connect to remote PostgreSQL"""
        from connectors.postgres_connector import PostgreSQLConnector

        pg_config = self.config.get('postgres', {})

        # Check for connection string first
        conn_string = pg_config.get('connection_string')
        if conn_string:
            self.connector = PostgreSQLConnector.from_connection_string(conn_string)
        else:
            self.connector = PostgreSQLConnector(
                host=pg_config.get('host', 'localhost'),
                port=pg_config.get('port', 5432),
                database=pg_config.get('database', 'postgres'),
                user=pg_config.get('user', 'postgres'),
                password=pg_config.get('password', ''),
                ssl=pg_config.get('ssl', True)
            )

        self.db_type = 'postgresql'
        return self.connector.connect()

    def execute(self, sql: str):
        """Execute SQL query"""
        return self.connector.execute(sql)

    def list_tables(self):
        """List all tables"""
        return self.connector.list_tables()

    def get_table_info(self, table_name: str):
        """Get table info"""
        return self.connector.get_table_info(table_name)

    def disconnect(self):
        """Disconnect from database"""
        if self.connector:
            self.connector.disconnect()


class ConversationalAI_V2:
    """
    Enhanced Conversational AI with Memory & Multi-DB Support
    - Remembers previous questions
    - Handles follow-ups like "show me by month" or "what about last year"
    - Maintains context across turns
    - Supports local DuckDB and remote PostgreSQL
    """

    def __init__(self):
        self.console = Console()
        self.semantic_layer = None
        self.intent_parser = None
        self.db_manager = None
        self.memory = ConversationMemory(
            max_turns=10,
            persist_file=str(Path(__file__).parent / "conversation_history.json")
        )

    def initialize(self):
        """Initialize all components"""
        self.console.print("\n[bold blue]Initializing Conversational AI v2...[/bold blue]\n")

        try:
            # Initialize semantic layer
            self.console.print("Loading semantic layer...")
            config_path = Path(__file__).parent / "semantic_layer" / "config.yaml"
            self.semantic_layer = SemanticLayer(str(config_path))
            self.console.print("[green]✓[/green] Semantic layer loaded")

            # Initialize database manager
            self.console.print("Connecting to database...")
            db_config_path = Path(__file__).parent / "db_config.yaml"
            self.db_manager = DatabaseManager(str(db_config_path))

            if not self.db_manager.connect():
                self.console.print("[yellow]Database connection failed![/yellow]")
                self.console.print("Check db_config.yaml or run: python database/generate_sample_data.py")
                return False

            self.console.print(f"[green]✓[/green] Connected to {self.db_manager.db_type}")

            # Initialize LLM intent parser
            self.console.print("Loading local LLM (Ollama)...")
            self.intent_parser = IntentParser(self.semantic_layer)
            self.console.print("[green]✓[/green] LLM ready")

            # Show memory status
            if self.memory.history:
                self.console.print(f"[green]✓[/green] Loaded {len(self.memory.history)} previous turns")
            else:
                self.console.print("[green]✓[/green] Conversation memory initialized")

            self.console.print("\n[bold green]System ready! (v2 with conversation memory)[/bold green]\n")
            return True

        except Exception as e:
            self.console.print(f"[bold red]Initialization failed:[/bold red] {str(e)}")
            return False

    def process_question(self, question: str):
        """Process user question with context awareness"""
        try:
            # Check if this is a follow-up question
            is_follow_up = self.memory.is_follow_up(question)

            if is_follow_up:
                self.console.print(f"\n[dim]Detected follow-up question...[/dim]")
                context_intent = self.memory.resolve_follow_up(question)
                self.console.print(f"[dim]Using context from previous query[/dim]")
            else:
                context_intent = None

            # Step 1: Parse intent using LLM (with context)
            self.console.print(f"[dim]Parsing question...[/dim]")

            if is_follow_up and context_intent:
                intent = self._build_contextual_intent(question, context_intent)
            else:
                intent = self.intent_parser.parse(question)

            # Step 2: Convert intent to SQL using semantic layer
            self.console.print(f"[dim]Generating query via semantic layer...[/dim]")
            sql_query = self.semantic_layer.intent_to_sql(intent)

            # Step 3: Execute SQL
            self.console.print(f"[dim]Executing query on {self.db_manager.db_type}...[/dim]")
            results = self.db_manager.execute(sql_query.sql)

            # Step 4: Display results
            self.display_results(results, sql_query, is_follow_up)

            # Step 5: Generate natural language response
            self.console.print(f"\n[dim]Generating response...[/dim]")

            context_for_response = ""
            if is_follow_up:
                context_for_response = f"(Follow-up to: {self.memory.current_context.get('last_question', '')})"

            response = self.intent_parser.generate_natural_response(
                f"{question} {context_for_response}",
                results.data,
                sql_query.sql
            )

            self.console.print(f"\n[bold cyan]Answer:[/bold cyan]")
            self.console.print(Panel(response, border_style="cyan"))

            # Step 6: Save to memory
            self.memory.add_turn(
                user_question=question,
                parsed_intent=intent.__dict__ if hasattr(intent, '__dict__') else {},
                sql_query=sql_query.sql,
                results=results.data,
                response=response
            )

        except Exception as e:
            self.console.print(f"\n[bold red]Error:[/bold red] {str(e)}")

    def _build_contextual_intent(self, question: str, context: dict) -> QueryIntent:
        """Build intent using context from previous query"""
        metrics = context.get('metrics', [])
        group_by = context.get('group_by', [])
        filters = context.get('filters', [])
        time_period = context.get('time_period')

        question_lower = question.lower()

        # Detect metric changes
        if 'deposit' in question_lower:
            metrics = ['total_deposits']
        elif 'withdrawal' in question_lower:
            metrics = ['total_withdrawals']
        elif 'loan' in question_lower:
            metrics = ['total_loan_amount']
        elif 'customer' in question_lower:
            metrics = ['active_customers']

        # Detect grouping changes
        if 'by month' in question_lower:
            group_by = ['month_name']
        elif 'by year' in question_lower:
            group_by = ['year']
        elif 'by region' in question_lower:
            group_by = ['region']
        elif 'by segment' in question_lower or 'by customer' in question_lower:
            group_by = ['customer_segment']
        elif 'by account' in question_lower:
            group_by = ['account_type']

        # Detect time period changes
        if 'last year' in question_lower:
            time_period = "d_date.year = YEAR(CURRENT_DATE) - 1"
        elif 'this year' in question_lower:
            time_period = "d_date.year = YEAR(CURRENT_DATE)"
        elif 'last month' in question_lower:
            time_period = "d_date.month = MONTH(CURRENT_DATE) - 1"

        # Detect filter additions
        if 'premium' in question_lower:
            filters = ["d_customer.customer_segment = 'Premium'"]
        elif 'gold' in question_lower:
            filters = ["d_customer.customer_segment = 'Gold'"]

        if not metrics:
            metrics = context.get('metrics', ['total_transactions'])

        return QueryIntent(
            metrics=metrics,
            dimensions=[],
            filters=filters,
            group_by=group_by,
            time_period=time_period,
            limit=None,
            original_question=question
        )

    def display_results(self, results, sql_query, is_follow_up=False):
        """Display query results with context indicator"""
        if is_follow_up:
            self.console.print("\n[yellow]📝 Follow-up query (using previous context)[/yellow]")

        self.console.print("\n[bold]Generated SQL:[/bold]")
        self.console.print(Panel(sql_query.sql, border_style="blue"))

        self.console.print(
            f"\n[dim]Execution time: {results.execution_time_ms}ms | "
            f"Rows: {results.row_count} | Source: {self.db_manager.db_type}[/dim]"
        )

        if results.data:
            table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)

            for col in results.columns:
                table.add_column(col)

            for row in results.data[:20]:
                table.add_row(*[str(row.get(col, '')) for col in results.columns])

            if results.row_count > 20:
                self.console.print(f"\n[dim]Showing first 20 of {results.row_count} rows[/dim]")

            self.console.print(table)
        else:
            self.console.print("[yellow]No data returned[/yellow]")

    def show_help(self):
        """Show help information"""
        help_text = """
# Conversational AI v2 Help

## 🆕 What's New in v2?

- **Conversation Memory**: Remembers previous questions
- **Follow-up Support**: "Show me by month" works based on last query
- **Context Awareness**: "What about last year?" understands context
- **Multi-DB Support**: Local DuckDB or Remote PostgreSQL

## Database Commands
- `source` - Show current database source
- `switch local` - Switch to local DuckDB
- `switch postgres` - Switch to remote PostgreSQL

## Follow-up Examples

Start with: `What is the total transaction volume?`

Then try these follow-ups:
- `Show me by month` → Groups previous query by month
- `What about by region?` → Groups by region instead
- `Filter for Premium customers` → Adds filter
- `Compare with last year` → Changes time period

## Commands
- `help` - Show this help
- `metrics` - List all available metrics
- `dimensions` - List all available dimensions
- `tables` - Show database tables
- `history` - Show conversation history
- `clear` - Clear conversation memory
- `source` - Show current database
- `quit` or `exit` - Exit the application
"""
        self.console.print(Markdown(help_text))

    def show_source(self):
        """Show current database source"""
        self.console.print(f"\n[bold]Current Database:[/bold] {self.db_manager.db_type}")
        if self.db_manager.db_type == 'postgresql':
            self.console.print("[dim]Connected to remote PostgreSQL[/dim]")
        else:
            self.console.print("[dim]Using local DuckDB[/dim]")

    def show_history(self):
        """Show conversation history"""
        summary = self.memory.get_conversation_summary()
        self.console.print(Panel(summary, title="Conversation History", border_style="blue"))

    def clear_history(self):
        """Clear conversation memory"""
        self.memory.clear()
        self.console.print("[green]Conversation history cleared.[/green]")

    def list_metrics(self):
        """List all available metrics"""
        metrics = self.semantic_layer.list_available_metrics()

        table = Table(title="Available Metrics", show_header=True, header_style="bold magenta")
        table.add_column("Metric Name", style="cyan")
        table.add_column("Description", style="white")

        for metric in metrics:
            table.add_row(metric['name'], metric['description'])

        self.console.print(table)

    def list_dimensions(self):
        """List all available dimensions"""
        dimensions = self.semantic_layer.list_available_dimensions()

        table = Table(title="Available Dimensions", show_header=True, header_style="bold magenta")
        table.add_column("Dimension", style="cyan")
        table.add_column("Attributes", style="white")

        for dim in dimensions:
            attrs = ", ".join(dim['attributes'])
            table.add_row(dim['name'], attrs)

        self.console.print(table)

    def list_tables(self):
        """List all database tables"""
        tables = self.db_manager.list_tables()

        table = Table(title=f"Database Tables ({self.db_manager.db_type})", show_header=True, header_style="bold magenta")
        table.add_column("Table Name", style="cyan")
        table.add_column("Row Count", style="white")

        for table_name in tables:
            info = self.db_manager.get_table_info(table_name)
            table.add_row(table_name, str(info['row_count']))

        self.console.print(table)

    def run(self):
        """Main application loop"""
        welcome = """
# 🏦 Conversational AI v2 - With Memory & Multi-DB!

**Features:**
- 💬 **Conversation Memory** - Remembers previous questions
- 🔄 **Follow-ups** - "Show me by month", "What about last year?"
- 🧠 **Context Aware** - Understands references to previous queries
- 🗄️ **Multi-DB** - Local DuckDB or Remote PostgreSQL

**Try this flow:**
1. Ask: `What is the total transaction volume?`
2. Follow up: `Show me by month`
3. Follow up: `What about by region?`

**Commands:** `help`, `history`, `clear`, `source`, `metrics`, `quit`
"""
        self.console.print(Markdown(welcome))

        if not self.initialize():
            return

        while True:
            try:
                if self.memory.history:
                    last_q = self.memory.current_context.get('last_question', '')
                    if last_q:
                        self.console.print(f"\n[dim]Last: {last_q[:50]}...[/dim]")

                self.console.print("\n[bold green]Ask a question:[/bold green]", end=" ")
                question = input().strip()

                if not question:
                    continue

                # Handle commands
                if question.lower() in ['quit', 'exit', 'q']:
                    self.console.print("\n[bold]Goodbye![/bold]\n")
                    break
                elif question.lower() == 'help':
                    self.show_help()
                elif question.lower() == 'metrics':
                    self.list_metrics()
                elif question.lower() == 'dimensions':
                    self.list_dimensions()
                elif question.lower() == 'tables':
                    self.list_tables()
                elif question.lower() == 'history':
                    self.show_history()
                elif question.lower() == 'clear':
                    self.clear_history()
                elif question.lower() == 'source':
                    self.show_source()
                else:
                    self.process_question(question)

            except KeyboardInterrupt:
                self.console.print("\n\n[bold]Goodbye![/bold]\n")
                break
            except Exception as e:
                self.console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")

        if self.db_manager:
            self.db_manager.disconnect()


def main():
    """Entry point"""
    app = ConversationalAI_V2()
    app.run()


if __name__ == '__main__':
    main()
