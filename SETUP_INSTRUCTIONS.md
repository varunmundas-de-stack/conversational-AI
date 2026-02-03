# Conversational AI over SQL (BFSI Domain) - Setup Guide

## Architecture Overview

This solution uses a **semantic layer approach** (NOT direct LLM-to-SQL):
```
User Question → LLM (Intent Understanding) → Semantic Layer Mapper → SQL Generator → DuckDB → Results → LLM (Natural Response)
```

**Key Components:**
- **DuckDB**: Local OLAP database (free, embedded)
- **Ollama**: Local LLM runtime (free, runs Llama models)
- **Semantic Layer**: Custom-built metric definitions and mappings
- **Python**: Orchestration layer

---

## STEP 1: Install Homebrew (if not already installed)

Open Terminal and run:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## STEP 2: Install Python 3.11

```bash
brew install python@3.11
```

Verify installation:
```bash
python3 --version
```

## STEP 3: Install Ollama (Local LLM Runtime)

```bash
brew install ollama
```

Start Ollama service:
```bash
ollama serve
```

In a NEW terminal window, pull a model (Llama 3.2 - 3B, lightweight):
```bash
ollama pull llama3.2:3b
```

## STEP 4: Create Virtual Environment

Navigate to project directory:
```bash
cd /Users/varunmundas/Desktop/Conversation_AI_Project
```

Create virtual environment:
```bash
python3 -m venv venv
```

Activate virtual environment:
```bash
source venv/bin/activate
```

## STEP 5: Install Python Dependencies

```bash
pip install --upgrade pip
pip install duckdb ollama pydantic pyyaml rich
```

**Dependencies explained:**
- `duckdb`: Embedded OLAP database
- `ollama`: Python client for local LLM
- `pydantic`: Data validation for semantic layer
- `pyyaml`: Configuration management
- `rich`: Beautiful CLI interface

---

## Next Steps

After completing the above setup, proceed to running the application (instructions will be provided in README.md)
