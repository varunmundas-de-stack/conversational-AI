# System Architecture

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                            USER                                     │
│                "What is the total transaction volume by month?"     │
└───────────────────────────────┬────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                       CLI INTERFACE (Rich)                          │
│                         main.py                                     │
└───────────────────────────────┬────────────────────────────────────┘
                                │
                                ▼
        ╔═══════════════════════════════════════════════════╗
        ║         INTENT PARSER (LLM Integration)           ║
        ║              llm/intent_parser.py                 ║
        ║                                                   ║
        ║  ┌─────────────────────────────────────────┐     ║
        ║  │   Ollama (Local LLM)                    │     ║
        ║  │   Model: Llama 3.2 (3B)                 │     ║
        ║  │                                         │     ║
        ║  │   Purpose:                              │     ║
        ║  │   - Parse natural language              │     ║
        ║  │   - Extract semantic concepts           │     ║
        ║  │   - Map to metrics/dimensions           │     ║
        ║  │   - Format responses                    │     ║
        ║  │                                         │     ║
        ║  │   NOT USED FOR:                         │     ║
        ║  │   ❌ SQL Generation                     │     ║
        ║  └─────────────────────────────────────────┘     ║
        ╚═══════════════════════════════════════════════════╝
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Query Intent        │
                    ├───────────────────────┤
                    │ metrics:              │
                    │ - transaction_volume  │
                    │ group_by:             │
                    │ - month_name          │
                    │ filters: []           │
                    └───────────┬───────────┘
                                │
                                ▼
        ╔═══════════════════════════════════════════════════╗
        ║            SEMANTIC LAYER ⭐ CORE                 ║
        ║       semantic_layer/semantic_layer.py            ║
        ║                                                   ║
        ║  ┌─────────────────────────────────────────┐     ║
        ║  │  Configuration (YAML)                   │     ║
        ║  │  semantic_layer/config.yaml             │     ║
        ║  │                                         │     ║
        ║  │  Metrics:                               │     ║
        ║  │    transaction_volume:                  │     ║
        ║  │      sql: SUM(transaction_amount)       │     ║
        ║  │      table: fact_transactions           │     ║
        ║  │                                         │     ║
        ║  │  Dimensions:                            │     ║
        ║  │    date:                                │     ║
        ║  │      attributes:                        │     ║
        ║  │        month_name: "month_name"         │     ║
        ║  │                                         │     ║
        ║  │  Business Terms:                        │     ║
        ║  │    revenue → transaction_volume         │     ║
        ║  └─────────────────────────────────────────┘     ║
        ║                                                   ║
        ║  Function: intent_to_sql()                        ║
        ║  - Deterministic SQL generation                   ║
        ║  - No LLM involved                                ║
        ║  - Rule-based mapping                             ║
        ╚═══════════════════════════════════════════════════╝
                                │
                                ▼
                    ┌───────────────────────┐
                    │   SQL Query           │
                    ├───────────────────────┤
                    │ SELECT                │
                    │   month_name,         │
                    │   SUM(amount)         │
                    │ FROM fact_trans       │
                    │ JOIN dim_date         │
                    │ GROUP BY month_name   │
                    └───────────┬───────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────┐
        │           QUERY EXECUTOR                          │
        │         query_engine/executor.py                  │
        │                                                   │
        │   ┌───────────────────────────────────────┐      │
        │   │    DuckDB (OLAP Database)             │      │
        │   │    database/bfsi_olap.duckdb          │      │
        │   │                                       │      │
        │   │    Fact Tables:                       │      │
        │   │    - fact_transactions (50K rows)     │      │
        │   │    - fact_loans (500 rows)            │      │
        │   │    - fact_account_balances            │      │
        │   │    - fact_investments                 │      │
        │   │                                       │      │
        │   │    Dimension Tables:                  │      │
        │   │    - dim_date (365 days)              │      │
        │   │    - dim_customer (1K)                │      │
        │   │    - dim_account (1.5K)               │      │
        │   │    - dim_product (13)                 │      │
        │   │    - dim_transaction_type (10)        │      │
        │   └───────────────────────────────────────┘      │
        └───────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Query Results       │
                    ├───────────────────────┤
                    │ month_name | volume   │
                    │ January    | 1.2M     │
                    │ February   | 1.5M     │
                    │ March      | 1.8M     │
                    │ ...                   │
                    └───────────┬───────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────┐
        │      RESPONSE GENERATOR (LLM)                     │
        │         llm/intent_parser.py                      │
        │                                                   │
        │   Takes: Results + Original Question              │
        │   Returns: Natural language answer                │
        │                                                   │
        │   "The total transaction volume shows seasonal    │
        │    variation with peaks in March ($1.8M) and      │
        │    December ($2.1M). Average monthly volume       │
        │    is $1.5M."                                     │
        └───────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Display Results     │
                    │   - SQL Query         │
                    │   - Data Table        │
                    │   - Natural Answer    │
                    └───────────────────────┘
```

## Data Flow

```
1. User Question (Natural Language)
         ↓
2. LLM Parse → Extract Intent (metrics, dimensions, filters)
         ↓
3. Semantic Layer → Generate SQL (rule-based, NOT LLM)
         ↓
4. DuckDB → Execute Query
         ↓
5. Results → Format as table
         ↓
6. LLM → Generate natural language response
         ↓
7. Display to User
```

## Component Interactions

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│             │         │              │         │             │
│   Ollama    │◄────────│   Intent     │────────►│  Semantic   │
│   (LLM)     │         │   Parser     │         │   Layer     │
│             │         │              │         │             │
└─────────────┘         └──────────────┘         └──────┬──────┘
                                                         │
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │   Query     │
                                                  │   Executor  │
                                                  │             │
                                                  └──────┬──────┘
                                                         │
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │   DuckDB    │
                                                  │  (Database) │
                                                  │             │
                                                  └─────────────┘
```

## Semantic Layer Detail

```
┌───────────────────────────────────────────────────────────────┐
│                    SEMANTIC LAYER                              │
│                  (The Magic Happens Here)                      │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Input: QueryIntent                                           │
│  {                                                            │
│    metrics: ["transaction_volume"],                          │
│    group_by: ["month_name"],                                 │
│    filters: [],                                              │
│    time_period: "year = 2024"                                │
│  }                                                            │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Step 1: Resolve Metrics                             │     │
│  │                                                      │     │
│  │ transaction_volume →                                │     │
│  │   sql: SUM(transaction_amount)                      │     │
│  │   table: fact_transactions                          │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Step 2: Resolve Dimensions                          │     │
│  │                                                      │     │
│  │ month_name →                                        │     │
│  │   table: dim_date                                   │     │
│  │   key: date_key                                     │     │
│  │   attribute: month_name                             │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Step 3: Determine Fact Table                        │     │
│  │                                                      │     │
│  │ Based on metrics → fact_transactions                │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Step 4: Build JOINs                                 │     │
│  │                                                      │     │
│  │ fact_transactions ft                                │     │
│  │ LEFT JOIN dim_date d_date                           │     │
│  │   ON ft.date_key = d_date.date_key                  │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Step 5: Build SELECT                                │     │
│  │                                                      │     │
│  │ SELECT                                              │     │
│  │   d_date.month_name,                                │     │
│  │   SUM(ft.transaction_amount) AS transaction_volume  │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Step 6: Build WHERE                                 │     │
│  │                                                      │     │
│  │ WHERE d_date.year = 2024                            │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Step 7: Build GROUP BY                              │     │
│  │                                                      │     │
│  │ GROUP BY d_date.month_name                          │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  Output: SQL Query                                            │
│  SELECT                                                       │
│    d_date.month_name,                                         │
│    SUM(ft.transaction_amount) AS transaction_volume           │
│  FROM fact_transactions ft                                    │
│  LEFT JOIN dim_date d_date                                    │
│    ON ft.date_key = d_date.date_key                           │
│  WHERE d_date.year = 2024                                     │
│  GROUP BY d_date.month_name                                   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## LLM Role (Ollama)

```
┌─────────────────────────────────────────────────────────┐
│                  OLLAMA (Local LLM)                      │
│                   Llama 3.2 (3B)                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Role 1: Intent Parsing                                 │
│  ┌───────────────────────────────────────────────┐     │
│  │ Input: "Show me sales by month this year"     │     │
│  │                                               │     │
│  │ Output (JSON):                                │     │
│  │ {                                             │     │
│  │   "metrics": ["transaction_volume"],          │     │
│  │   "group_by": ["month_name"],                 │     │
│  │   "time_period": "year = YEAR(CURRENT_DATE)"  │     │
│  │ }                                             │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  Role 2: Response Generation                            │
│  ┌───────────────────────────────────────────────┐     │
│  │ Input: Query results + Original question      │     │
│  │                                               │     │
│  │ Output: Natural language answer               │     │
│  │ "Your sales this year show steady growth,     │     │
│  │  with total volume of $15.2M across all       │     │
│  │  months. Peak was in December at $2.1M."      │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  NOT USED FOR:                                          │
│  ❌ SQL Generation                                     │
│  ❌ Data Validation                                    │
│  ❌ Business Logic                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Database Schema (Star Schema)

```
                    ┌──────────────┐
                    │   dim_date   │
                    ├──────────────┤
                    │ date_key PK  │
                    │ date         │
                    │ year         │
                    │ quarter      │
                    │ month        │
                    │ month_name   │
                    └──────┬───────┘
                           │
                           │
┌────────────┐            │            ┌──────────────┐
│dim_customer│            │            │ dim_account  │
├────────────┤            │            ├──────────────┤
│cust_key PK │            │            │ acc_key PK   │
│customer_id │            │            │ account_id   │
│name        │            │            │ account_type │
│segment     │            │            │ branch       │
│city        │            │            │ region       │
└─────┬──────┘            │            └──────┬───────┘
      │                   │                   │
      │                   │                   │
      │         ┌─────────▼─────────┐         │
      │         │ fact_transactions │         │
      │         ├───────────────────┤         │
      └────────►│ transaction_key PK├─────────┘
                │ date_key FK       │
                │ customer_key FK   │
                │ account_key FK    │
                │ trans_type_key FK │
                │ amount            │
                │ balance           │
                │ fee               │
                └─────────┬─────────┘
                          │
                          │
                 ┌────────▼─────────┐
                 │dim_trans_type    │
                 ├──────────────────┤
                 │ trans_type_key PK│
                 │ transaction_type │
                 │ category         │
                 │ is_debit         │
                 │ is_credit        │
                 └──────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ CLI Interface│  │ Intent Parser│  │Query Executor│  │
│  │   (Rich)     │  │  (Ollama)    │  │  (DuckDB)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Semantic Layer                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Config (YAML)│  │ Models       │  │ SQL Builder  │  │
│  │              │  │ (Pydantic)   │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                           │
│                                                          │
│  ┌──────────────┐                  ┌──────────────┐     │
│  │   DuckDB     │                  │   Ollama     │     │
│  │ (OLAP Store) │                  │ (LLM Runtime)│     │
│  └──────────────┘                  └──────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Deployment Architecture (Local MacBook)

```
┌─────────────────────────────────────────────────────────┐
│                    MacBook (Local)                       │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Terminal 1: Ollama Server                     │     │
│  │  $ ollama serve                                │     │
│  │  Listening on http://localhost:11434           │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Terminal 2: Python Application                │     │
│  │  $ source venv/bin/activate                    │     │
│  │  $ python main.py                              │     │
│  │                                                │     │
│  │  ┌──────────────────────────────────────┐     │     │
│  │  │  Python Process                      │     │     │
│  │  │                                      │     │     │
│  │  │  ┌────────────────┐                  │     │     │
│  │  │  │  DuckDB        │ (Embedded)       │     │     │
│  │  │  │  In-process    │                  │     │     │
│  │  │  └────────────────┘                  │     │     │
│  │  │                                      │     │     │
│  │  │  ┌────────────────┐                  │     │     │
│  │  │  │  Ollama Client │ → HTTP → Ollama  │     │     │
│  │  │  └────────────────┘                  │     │     │
│  │  │                                      │     │     │
│  │  │  ┌────────────────┐                  │     │     │
│  │  │  │ Semantic Layer │ (Python)         │     │     │
│  │  │  └────────────────┘                  │     │     │
│  │  └──────────────────────────────────────┘     │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  File System:                                            │
│  /Users/varunmundas/Desktop/Conversation_AI_Project/     │
│  ├── database/bfsi_olap.duckdb (50MB)                    │
│  └── semantic_layer/config.yaml (10KB)                   │
│                                                          │
└─────────────────────────────────────────────────────────┘

No Internet Required After Setup!
```

## Security & Governance

```
┌─────────────────────────────────────────────────────────┐
│                  Security Layers                         │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │ User Question (Natural Language)                │     │
│  └────────────────────┬───────────────────────────┘     │
│                       │                                  │
│                       ▼                                  │
│  ┌────────────────────────────────────────────────┐     │
│  │ Intent Parser (Maps to allowed concepts)       │     │
│  │ ✓ Only predefined metrics                      │     │
│  │ ✓ Only predefined dimensions                   │     │
│  │ ❌ Cannot request arbitrary data               │     │
│  └────────────────────┬───────────────────────────┘     │
│                       │                                  │
│                       ▼                                  │
│  ┌────────────────────────────────────────────────┐     │
│  │ Semantic Layer (Controlled SQL generation)     │     │
│  │ ✓ Parameterized queries                        │     │
│  │ ✓ No user input in SQL                         │     │
│  │ ✓ Predefined table access                      │     │
│  │ ❌ No SQL injection possible                   │     │
│  └────────────────────┬───────────────────────────┘     │
│                       │                                  │
│                       ▼                                  │
│  ┌────────────────────────────────────────────────┐     │
│  │ Query Executor (Read-only access)              │     │
│  │ ✓ Read-only connection                         │     │
│  │ ✓ No DDL/DML allowed                           │     │
│  │ ❌ Cannot modify data                          │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

This architecture ensures:
- ✅ LLM understands intent, doesn't generate SQL
- ✅ Semantic layer provides governance
- ✅ No SQL injection risk
- ✅ Consistent, auditable queries
- ✅ Runs completely offline/local
- ✅ Free and open source
