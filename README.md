# Conversational AI over SQL (BFSI Domain) - PoC

A proof-of-concept implementation demonstrating conversational AI over OLAP data using a **semantic layer approach** instead of direct LLM-to-SQL generation.

## 🎯 Problem Statement

Build a Conversational AI system over SQL data (OLAP schema) for BFSI domain that:
- Does NOT use LLM for SQL generation (as per requirements)
- Uses a semantic layer to map business concepts to SQL
- Runs completely locally on MacBook (no cloud dependencies)
- Provides natural language querying over banking/financial data

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Question                            │
│              "What is the total transaction volume?"             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Intent Parser (Ollama)                    │
│  Maps natural language → semantic concepts (metrics/dimensions)  │
│           NOT used for SQL generation!                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │  Query Intent   │
                   │  - metrics      │
                   │  - dimensions   │
                   │  - filters      │
                   └────────┬────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Semantic Layer                              │
│    Maps business concepts → SQL using predefined rules          │
│    - Metric definitions                                         │
│    - Dimension mappings                                         │
│    - Business terminology                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │  SQL Query   │
                      └──────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DuckDB (OLAP Database)                        │
│              Execute query on BFSI data                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   Results    │
                      └──────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LLM Response Generator (Ollama)                  │
│         Format results as natural language answer               │
└─────────────────────────────────────────────────────────────────┘
```

## 🔑 Key Components

### 1. **Semantic Layer** (Core Innovation)
- **NOT** LLM-based SQL generation
- Predefined metric definitions in YAML
- Business terminology mappings
- Dimension and fact table relationships
- Ensures data governance and consistency

### 2. **Local LLM (Ollama)**
- Runs Llama 3.2 (3B) model locally
- Used ONLY for:
  - Understanding user intent
  - Mapping questions to semantic concepts
  - Formatting results as natural language
- Never generates SQL directly

### 3. **DuckDB (Embedded OLAP)**
- In-process analytical database
- Star schema with fact and dimension tables
- BFSI sample data (customers, accounts, transactions, loans)

### 4. **CLI Interface**
- Rich terminal UI with tables and formatting
- Interactive query interface
- Real-time feedback

## 📊 Database Schema (BFSI Domain)

### Dimension Tables
- `dim_date` - Date dimension (365 days)
- `dim_customer` - Customer demographics (1,000 customers)
- `dim_account` - Account information (1,500 accounts)
- `dim_product` - Banking products (loans, investments, insurance)
- `dim_transaction_type` - Transaction categories

### Fact Tables
- `fact_transactions` - Transaction history (50,000 records)
- `fact_loans` - Loan portfolio (500 records)
- `fact_account_balances` - Daily account snapshots
- `fact_investments` - Investment portfolio

## 🚀 Setup Instructions

### Prerequisites Check
```bash
# Check if Homebrew is installed
brew --version

# Check Python version (should be 3.11+)
python3 --version
```

### Step 1: Install Dependencies

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Ollama
brew install ollama
```

### Step 2: Start Ollama and Download Model

```bash
# Start Ollama service (keep this terminal open)
ollama serve
```

In a **NEW terminal window**:
```bash
# Download Llama 3.2 (3B) model (~2GB download)
ollama pull llama3.2:3b
```

### Step 3: Set Up Python Environment

```bash
# Navigate to project directory
cd /Users/varunmundas/Desktop/Conversation_AI_Project

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Generate Sample Data

```bash
# Generate BFSI OLAP database with sample data
python database/generate_sample_data.py
```

Expected output:
```
Creating database at: database/bfsi_olap.duckdb
Creating schema...
Generating date dimension...
  Generated 365 date records
Generating customer dimension...
  Generated 1,000 customer records
...
Database created successfully!
```

### Step 5: Run the Application

```bash
# Make sure Ollama is running in another terminal
# ollama serve

# Run the conversational AI
python main.py
```

## 💬 Example Queries

Try these questions once the application is running:

### Basic Metrics
```
What is the total transaction volume?
How many transactions happened this year?
What is the average transaction amount?
```

### Aggregations
```
Show me transaction volume by month
What are total deposits by region?
Show customer distribution by segment
```

### Loans & Credit
```
What is the total loan amount?
Show me the loan default rate
What is the outstanding loan balance?
What is the average credit score?
```

### Time-based Queries
```
Show transaction volume by month this year
What were the total withdrawals last month?
How many customers joined this year?
```

### Commands
```
help - Show help and examples
metrics - List all available metrics
dimensions - List all available dimensions
tables - Show database tables and row counts
quit - Exit the application
```

## 📁 Project Structure

```
Conversation_AI_Project/
│
├── database/
│   ├── schema.sql              # OLAP schema definition
│   ├── generate_sample_data.py # Sample data generator
│   └── bfsi_olap.duckdb        # Generated database
│
├── semantic_layer/
│   ├── config.yaml             # Metric & dimension definitions
│   ├── models.py               # Pydantic data models
│   └── semantic_layer.py       # Core semantic layer logic
│
├── llm/
│   └── intent_parser.py        # LLM intent parsing
│
├── query_engine/
│   └── executor.py             # Query execution engine
│
├── main.py                     # Main CLI application
├── requirements.txt            # Python dependencies
├── SETUP_INSTRUCTIONS.md       # Detailed setup guide
└── README.md                   # This file
```

## 🧪 Testing

Test the semantic layer directly:

```python
from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.models import QueryIntent

# Initialize semantic layer
sl = SemanticLayer("semantic_layer/config.yaml")

# Create a query intent
intent = QueryIntent(
    metrics=["transaction_volume"],
    group_by=["month_name"],
    filters=[],
    time_period=None,
    limit=None,
    original_question="Show transaction volume by month"
)

# Generate SQL
sql_query = sl.intent_to_sql(intent)
print(sql_query.sql)
```

## 🎓 Key Learnings

### Why NOT Direct LLM-to-SQL?

1. **Consistency**: LLMs can generate different SQL for same question
2. **Governance**: No control over what data is accessed
3. **Security**: Risk of SQL injection or unauthorized queries
4. **Accuracy**: Business logic encoded incorrectly
5. **Performance**: No query optimization

### Why Semantic Layer?

1. **Controlled**: Predefined metrics ensure consistency
2. **Governed**: Data access rules enforced
3. **Maintainable**: Change metric definition in one place
4. **Accurate**: Business logic encoded correctly
5. **Performant**: Optimized SQL patterns

## 🔧 Troubleshooting

### Ollama Connection Error
```bash
# Make sure Ollama is running
ollama serve

# Check if model is downloaded
ollama list
```

### Database Not Found
```bash
# Regenerate database
python database/generate_sample_data.py
```

### Module Import Errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Python Version Issues
```bash
# Check Python version (needs 3.9+)
python3 --version

# Use Python 3.11 explicitly
python3.11 -m venv venv
```

## 📈 Future Enhancements

1. **Add more metrics**: Investment returns, fees, etc.
2. **Complex filters**: Date ranges, nested conditions
3. **Drill-down**: Interactive exploration
4. **Caching**: Cache query results
5. **Visualization**: Add charts and graphs
6. **Export**: CSV, Excel export functionality
7. **Multi-tenancy**: Support multiple users/databases
8. **Query history**: Save and replay queries

## 🤝 Contributing

This is a PoC. Feel free to:
- Add more BFSI metrics
- Improve intent parsing
- Add new dimensions
- Enhance UI/UX

## 📄 License

Educational/PoC project - free to use and modify.

## 🙋 Support

For questions or issues:
1. Check [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)
2. Review troubleshooting section
3. Check Ollama is running: `ollama list`

---

**Built with**: Python, DuckDB, Ollama (Llama 3.2), Rich CLI
**Architecture**: Semantic Layer over OLAP (NOT LLM-to-SQL)
**Domain**: Banking, Financial Services, Insurance (BFSI)
