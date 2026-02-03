# 🚀 START HERE - Conversational AI over SQL

## Welcome!

This is a complete implementation of **Conversational AI over SQL (OLAP schema)** for the BFSI domain, using a **semantic layer approach** (NOT LLM-to-SQL generation).

## 🎯 What You Have

A fully functional, local-only Conversational AI system that:
- ✅ Runs entirely on your MacBook (no cloud needed)
- ✅ Uses semantic layer for SQL generation (NOT LLM)
- ✅ Includes BFSI sample data (banking, loans, transactions)
- ✅ Free and open source (zero cost)
- ✅ Complete documentation

## 🏗️ Architecture (Key Innovation)

```
User Question → LLM (understands intent) → Semantic Layer (generates SQL) → Database → Results
```

**Important**: The LLM does NOT generate SQL. The semantic layer does.

## 📋 Quick Start (2 Options)

### Option 1: Automated (Recommended)
```bash
cd /Users/varunmundas/Desktop/Conversation_AI_Project
./quickstart.sh
```

### Option 2: Manual
Follow the [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)

## 📚 Documentation Guide

Read in this order:

### 1. First-Time Setup
- **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)** ⭐ START HERE for step-by-step setup
  - Installation instructions
  - Troubleshooting
  - Verification steps

### 2. Understanding the System
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - High-level overview
  - What is this?
  - Why semantic layer?
  - Key components

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture
  - Data flow diagrams
  - Component interactions
  - Semantic layer details

### 3. Complete Documentation
- **[README.md](README.md)** - Full documentation
  - Setup instructions
  - Example queries
  - How to use

- **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - Detailed setup
  - Prerequisites
  - Installation steps

### 4. Validation
- **[CHECKLIST.md](CHECKLIST.md)** - Verification checklist
  - Setup checklist
  - Testing checklist
  - Demo preparation

## ⚡ Quick Setup Summary

### Prerequisites
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Ollama
brew install ollama
```

### Setup (5 minutes)
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Setup and run
cd /Users/varunmundas/Desktop/Conversation_AI_Project
ollama pull llama3.2:3b
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python database/generate_sample_data.py
python main.py
```

## 💬 Try These Questions

Once running:
```
What is the total transaction volume?
How many active customers do we have?
Show me transaction volume by month
What is the loan default rate?
metrics
dimensions
help
```

## 🗂️ File Structure

```
Conversation_AI_Project/
│
├── START_HERE.md                ← You are here
├── EXECUTION_GUIDE.md           ← Step-by-step setup
├── README.md                    ← Complete documentation
├── PROJECT_SUMMARY.md           ← High-level overview
├── ARCHITECTURE.md              ← Technical architecture
├── CHECKLIST.md                 ← Verification checklist
│
├── main.py                      ← Run this to start
├── quickstart.sh                ← Or run this script
│
├── semantic_layer/
│   ├── config.yaml              ⭐ Metric definitions
│   ├── semantic_layer.py        ⭐ SQL generation
│   └── models.py
│
├── database/
│   ├── schema.sql               ← OLAP schema
│   ├── generate_sample_data.py  ← Data generator
│   └── bfsi_olap.duckdb         ← Database (generated)
│
├── llm/
│   └── intent_parser.py         ← LLM integration
│
└── query_engine/
    └── executor.py              ← Query execution
```

## 🎓 Key Concepts

### Semantic Layer (The Innovation)
Instead of letting LLM generate SQL (risky, inconsistent), we:
1. Define metrics in YAML: `transaction_volume = SUM(transaction_amount)`
2. LLM maps question to metric: "sales" → "transaction_volume"
3. Semantic layer generates SQL from metric definition

**Benefits:**
- ✅ Consistent SQL for same questions
- ✅ Data governance (controlled metrics)
- ✅ No SQL injection risk
- ✅ Auditable and maintainable

### Components
1. **DuckDB** - Local OLAP database (fast, embedded)
2. **Ollama** - Local LLM runtime (free, no API keys)
3. **Semantic Layer** - Metric definitions (YAML config)
4. **Python** - Orchestration layer

## 🔍 What Makes This Different?

| Traditional Approach | This Solution |
|---------------------|---------------|
| LLM generates SQL | Semantic layer generates SQL |
| Different SQL each time | Consistent SQL |
| Hallucination risk | Predefined metrics |
| SQL injection possible | Parameterized queries |
| No governance | Full control |
| Cloud-dependent | Local-only |

## ⏱️ Time Estimates

- **First-time setup**: 15-30 minutes
- **Model download**: 5-10 minutes (one-time)
- **Data generation**: 1-2 minutes
- **Daily usage**: < 1 minute to start

## 🎯 Next Steps

### If This Is Your First Time:
1. **Read**: [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md) for detailed setup
2. **Run**: `./quickstart.sh` or follow manual steps
3. **Test**: Try the sample questions
4. **Explore**: Check `semantic_layer/config.yaml` to see metric definitions

### If You Want to Understand Architecture:
1. **Read**: [ARCHITECTURE.md](ARCHITECTURE.md) for visual diagrams
2. **Run**: `python test_semantic_layer.py` to see semantic layer in action
3. **Review**: `semantic_layer/semantic_layer.py` for SQL generation logic

### If You Want to Demo:
1. **Read**: [CHECKLIST.md](CHECKLIST.md) - Demo preparation section
2. **Prepare**: Sample questions
3. **Practice**: Run through the flow

## 🐛 Common Issues

### "ollama: command not found"
```bash
brew install ollama
```

### "Failed to connect to Ollama"
Start Ollama in another terminal:
```bash
ollama serve
```

### "Database not found"
Generate the database:
```bash
python database/generate_sample_data.py
```

See [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md) for complete troubleshooting.

## 💡 Key Files to Explore

1. **`semantic_layer/config.yaml`** - See all metric definitions
2. **`database/schema.sql`** - See OLAP schema
3. **`main.py`** - See how it all connects
4. **`test_semantic_layer.py`** - See semantic layer in isolation

## 📊 What's Inside the Database?

- **1,000** customers with demographics
- **1,500** accounts across different types
- **50,000** transactions over 1 year
- **500** loans with varying status
- **365** days in date dimension

All synthetic BFSI data for demonstration.

## ✅ Verification

System is working when:
- ✓ Ollama starts without errors
- ✓ Application initializes successfully
- ✓ Questions return SQL and results
- ✓ Natural language responses generated

## 🎉 You're Ready!

Choose your path:
- **Just want to run it?** → [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)
- **Want to understand it?** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Need complete details?** → [README.md](README.md)

---

**Questions?** Check the documentation files or see [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md) troubleshooting section.

**Ready to start?** Run: `./quickstart.sh`

**Built with**: Python, DuckDB, Ollama (Llama 3.2), Semantic Layer approach

**Domain**: Banking, Financial Services, Insurance (BFSI)

**Cost**: $0 (completely free, no cloud services)
