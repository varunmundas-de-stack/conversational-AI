# Step-by-Step Execution Guide

Follow these exact steps to run the Conversational AI system on your MacBook.

## 🚀 Quick Start (Recommended)

### Option 1: Automated Setup

```bash
cd /Users/varunmundas/Desktop/Conversation_AI_Project
./quickstart.sh
```

This will:
1. Check all prerequisites
2. Install dependencies
3. Generate sample data
4. Start the application

---

## 📋 Manual Step-by-Step (If Quick Start Fails)

### Step 1: Install Homebrew

```bash
# Check if Homebrew is installed
brew --version

# If not installed, install it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Python 3.11

```bash
# Install Python
brew install python@3.11

# Verify installation
python3 --version
# Should show: Python 3.11.x or higher
```

### Step 3: Install and Setup Ollama

```bash
# Install Ollama
brew install ollama

# Start Ollama service (keep this terminal open)
ollama serve
```

**Open a NEW terminal window** and continue:

```bash
# Download Llama 3.2 model (3GB download, takes 5-10 minutes)
ollama pull llama3.2:3b

# Verify model is downloaded
ollama list
# Should show llama3.2:3b in the list
```

**Keep the Ollama server running** (the terminal with `ollama serve`). You'll need it running whenever you use the application.

### Step 4: Setup Python Virtual Environment

Open a NEW terminal (or use the one where you downloaded the model):

```bash
# Navigate to project
cd /Users/varunmundas/Desktop/Conversation_AI_Project

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv) at the beginning

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

Expected output:
```
Successfully installed duckdb-X.X.X ollama-X.X.X pydantic-X.X.X ...
```

### Step 5: Generate Sample Data

```bash
# Still in the activated virtual environment
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
Generating account dimension...
  Generated 1,500 account records
...
Database created successfully!

Table counts:
  dim_date: 365 records
  dim_customer: 1,000 records
  dim_account: 1,500 records
  dim_product: 13 records
  dim_transaction_type: 10 records
  fact_transactions: 50,000 records
  fact_loans: 499 records
```

### Step 6: Test Semantic Layer (Optional but Recommended)

```bash
# Test that semantic layer works without LLM
python test_semantic_layer.py
```

This will show you how the semantic layer generates SQL from intents.

### Step 7: Run the Application

```bash
# Make sure Ollama is running in another terminal!
# If not, open a terminal and run: ollama serve

# Run the main application
python main.py
```

Expected startup:
```
🏦 Conversational AI over SQL (BFSI Domain)

Initializing Conversational AI System...

Loading semantic layer...
✓ Semantic layer loaded
Connecting to database...
✓ Database connected
Loading local LLM (Ollama)...
✓ LLM ready

System ready!

Ask a question:
```

### Step 8: Try Sample Questions

Type these questions one at a time:

```
What is the total transaction volume?

How many active customers do we have?

Show me transaction volume by month

What is the loan default rate?

metrics

dimensions

help

quit
```

---

## 🔍 Verification Checklist

Before running, verify:

- [ ] Homebrew installed: `brew --version`
- [ ] Python 3.9+ installed: `python3 --version`
- [ ] Ollama installed: `ollama --version`
- [ ] Ollama running: Check terminal with `ollama serve`
- [ ] Llama model downloaded: `ollama list` shows `llama3.2:3b`
- [ ] Virtual environment activated: See `(venv)` in prompt
- [ ] Dependencies installed: `pip list | grep duckdb`
- [ ] Database exists: `ls -lh database/bfsi_olap.duckdb`

---

## 🐛 Troubleshooting

### Problem: "ollama: command not found"

**Solution:**
```bash
brew install ollama
```

### Problem: "Failed to connect to Ollama"

**Solution:**
Make sure Ollama is running in another terminal:
```bash
ollama serve
```

### Problem: "No module named 'duckdb'"

**Solution:**
Activate virtual environment and reinstall:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: "Database not found"

**Solution:**
Generate the database:
```bash
python database/generate_sample_data.py
```

### Problem: "Python version too old"

**Solution:**
Install Python 3.11:
```bash
brew install python@3.11
# Then use python3.11 instead of python3
python3.11 -m venv venv
```

### Problem: Ollama downloads model but can't find it

**Solution:**
```bash
# List available models
ollama list

# If llama3.2:3b not shown, download again
ollama pull llama3.2:3b
```

---

## 📁 Expected File Structure

After setup, you should have:

```
Conversation_AI_Project/
├── venv/                       # Virtual environment (created)
├── database/
│   ├── schema.sql
│   ├── generate_sample_data.py
│   └── bfsi_olap.duckdb       # Generated database file
├── semantic_layer/
│   ├── config.yaml
│   ├── models.py
│   └── semantic_layer.py
├── llm/
│   ├── __init__.py
│   └── intent_parser.py
├── query_engine/
│   ├── __init__.py
│   └── executor.py
├── main.py
├── test_semantic_layer.py
├── quickstart.sh
├── requirements.txt
├── README.md
├── SETUP_INSTRUCTIONS.md
└── EXECUTION_GUIDE.md         # This file
```

---

## 🎯 What Happens When You Run It?

1. **Initialization**: Loads semantic layer, connects to DuckDB, initializes Ollama
2. **User Input**: You type a question
3. **Intent Parsing**: Ollama (LLM) understands your question and maps to semantic concepts
4. **SQL Generation**: Semantic layer (NOT LLM) converts concepts to SQL
5. **Execution**: DuckDB executes the SQL query
6. **Response**: Ollama formats results as natural language

**Key Point**: The LLM never generates SQL. It only understands intent and formats responses.

---

## 🔄 Daily Usage (After Initial Setup)

Every time you want to use the system:

```bash
# Terminal 1: Start Ollama (if not running)
ollama serve

# Terminal 2: Run the application
cd /Users/varunmundas/Desktop/Conversation_AI_Project
source venv/bin/activate
python main.py
```

---

## 📊 Understanding the Output

When you ask a question, you'll see:

1. **Generated SQL**: Shows the actual SQL query (created by semantic layer)
2. **Execution Info**: Query execution time and row count
3. **Results Table**: Formatted data table
4. **Natural Answer**: LLM's natural language summary

Example:
```
Ask a question: What is the total transaction volume?

Parsing question...
Generating query via semantic layer...
Executing query...

Generated SQL:
┌─────────────────────────────────────────────┐
│ SELECT                                       │
│   SUM(transaction_amount) AS transaction... │
│ FROM fact_transactions ft                    │
└─────────────────────────────────────────────┘

Execution time: 23.45ms | Rows: 1

┌──────────────────────┐
│ transaction_volume   │
├──────────────────────┤
│ 15,234,567.89       │
└──────────────────────┘

Answer:
┌─────────────────────────────────────────────┐
│ The total transaction volume is $15.23M     │
│ across all transactions in the database.    │
└─────────────────────────────────────────────┘
```

---

## ✅ Success Indicators

You'll know it's working when:
- System starts without errors
- You can type questions and get answers
- SQL queries are generated and executed
- Results are displayed in tables
- Natural language responses are shown

---

## 🎓 Next Steps

Once running successfully:

1. Try the example questions in [README.md](README.md)
2. Type `help` to see all available commands
3. Type `metrics` to see what you can query
4. Type `dimensions` to see how you can group data
5. Experiment with your own questions

---

## 💡 Tips

- Start with simple questions and build up
- Use the `metrics` and `dimensions` commands to understand what's available
- Look at the generated SQL to understand how semantic layer works
- Try combining different metrics and dimensions
- The system works offline - no internet needed after setup!

---

**Questions?** Check [README.md](README.md) for more details or review [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md).
