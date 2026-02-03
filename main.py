#!/usr/bin/env python3
"""
Conversational AI over SQL (BFSI Domain)
Main CLI Application

Architecture:
User Question → LLM (Intent) → Semantic Layer → SQL → DuckDB → Results → LLM (Response)
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from semantic_layer.semantic_layer import SemanticLayer
from llm.intent_parser import IntentParser
from query_engine.executor import QueryExecutor


class ConversationalAI:
    """Main Conversational AI Application"""

    def __init__(self):
        self.console = Console()
        self.semantic_layer = None
        self.intent_parser = None
        self.query_executor = None

    def initialize(self):
        """Initialize all components"""
        self.console.print("\n[bold blue]Initializing Conversational AI System...[/bold blue]\n")

        try:
            # Initialize semantic layer
            self.console.print("Loading semantic layer...")
            config_path = Path(__file__).parent / "semantic_layer" / "config.yaml"
            self.semantic_layer = SemanticLayer(str(config_path))
            self.console.print("[green]✓[/green] Semantic layer loaded")

            # Initialize query executor
            self.console.print("Connecting to database...")
            db_path = Path(__file__).parent / "database" / "bfsi_olap.duckdb"

            if not db_path.exists():
                self.console.print("[yellow]Database not found. Run setup first![/yellow]")
                self.console.print("Run: python database/generate_sample_data.py")
                return False

            self.query_executor = QueryExecutor(str(db_path))
            self.query_executor.connect()
            self.console.print("[green]✓[/green] Database connected")

            # Initialize LLM intent parser
            self.console.print("Loading local LLM (Ollama)...")
            self.intent_parser = IntentParser(self.semantic_layer)
            self.console.print("[green]✓[/green] LLM ready")

            self.console.print("\n[bold green]System ready![/bold green]\n")
            return True

        except Exception as e:
            self.console.print(f"[bold red]Initialization failed:[/bold red] {str(e)}")
            return False

    def process_question(self, question: str):
        """Process user question and return answer"""
        try:
            # Step 1: Parse intent using LLM
            self.console.print(f"\n[dim]Parsing question...[/dim]")
            intent = self.intent_parser.parse(question)

            # Step 2: Convert intent to SQL using semantic layer
            self.console.print(f"[dim]Generating query via semantic layer...[/dim]")
            sql_query = self.semantic_layer.intent_to_sql(intent)

            # Step 3: Execute SQL
            self.console.print(f"[dim]Executing query...[/dim]")
            results = self.query_executor.execute(sql_query.sql)

            # Step 4: Display results
            self.display_results(results, sql_query)

            # Step 5: Generate natural language response
            self.console.print(f"\n[dim]Generating response...[/dim]")
            response = self.intent_parser.generate_natural_response(
                question, results.data, sql_query.sql
            )

            self.console.print(f"\n[bold cyan]Answer:[/bold cyan]")
            self.console.print(Panel(response, border_style="cyan"))

        except Exception as e:
            self.console.print(f"\n[bold red]Error:[/bold red] {str(e)}")

    def display_results(self, results, sql_query):
        """Display query results in a nice table"""
        # Show SQL query
        self.console.print("\n[bold]Generated SQL:[/bold]")
        self.console.print(Panel(sql_query.sql, border_style="blue"))

        # Show execution info
        self.console.print(
            f"\n[dim]Execution time: {results.execution_time_ms}ms | "
            f"Rows: {results.row_count}[/dim]"
        )

        # Show data table
        if results.data:
            table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)

            # Add columns
            for col in results.columns:
                table.add_column(col)

            # Add rows (limit to 20 for display)
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
# Conversational AI Help

## Architecture
```
Question → LLM (Intent) → Semantic Layer → SQL → DuckDB → Results → LLM (Response)
```

**Key Point**: The LLM does NOT generate SQL. It only:
1. Understands your question and maps it to semantic concepts
2. Formats the results into natural language

The Semantic Layer handles all SQL generation based on predefined metrics and dimensions.

## Example Questions

**Transactions:**
- What is the total transaction volume?
- How many transactions happened this year?
- Show me transaction volume by month
- What are the total deposits and withdrawals?

**Customers:**
- How many active customers do we have?
- What is the average credit score?
- Show customer distribution by segment

**Loans:**
- What is the total loan amount?
- Show me the loan default rate
- What is the outstanding loan balance?

**Aggregations:**
- Show transaction volume by region
- What is the average transaction amount by account type?
- Top 10 customers by transaction volume

## Available Commands
- `help` - Show this help
- `metrics` - List all available metrics
- `dimensions` - List all available dimensions
- `tables` - Show database tables
- `quit` or `exit` - Exit the application

## Tips
- Be specific about what you want to measure
- Mention time periods (this year, last month, etc.)
- Use business terms - the system understands synonyms
"""
        self.console.print(Markdown(help_text))

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
        tables = self.query_executor.list_tables()

        table = Table(title="Database Tables", show_header=True, header_style="bold magenta")
        table.add_column("Table Name", style="cyan")
        table.add_column("Row Count", style="white")

        for table_name in tables:
            info = self.query_executor.get_table_info(table_name)
            table.add_row(table_name, str(info['row_count']))

        self.console.print(table)

    def run(self):
        """Main application loop"""
        # Show welcome message
        welcome = """
# 🏦 Conversational AI over SQL (BFSI Domain)

A proof-of-concept system that uses:
- **Local LLM** (Ollama) for intent understanding
- **Semantic Layer** for SQL generation (NOT LLM)
- **DuckDB** for OLAP queries

Type your questions in natural language or use commands like:
- `help` - Show help
- `metrics` - List available metrics
- `dimensions` - List available dimensions
- `quit` - Exit
"""
        self.console.print(Markdown(welcome))

        # Initialize system
        if not self.initialize():
            return

        # Main loop
        while True:
            try:
                # Get user input
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
                else:
                    # Process as a question
                    self.process_question(question)

            except KeyboardInterrupt:
                self.console.print("\n\n[bold]Goodbye![/bold]\n")
                break
            except Exception as e:
                self.console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")

        # Cleanup
        if self.query_executor:
            self.query_executor.disconnect()


def main():
    """Entry point"""
    app = ConversationalAI()
    app.run()


if __name__ == '__main__':
    main()
