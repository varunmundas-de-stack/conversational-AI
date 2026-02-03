#!/bin/bash
# Quick start script for Conversational AI PoC

set -e

echo "=========================================="
echo "Conversational AI over SQL - Quick Start"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
echo -n "Checking Python installation... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC}"
    echo "Python 3 is not installed. Please install Python 3.9+ first."
    echo "Run: brew install python@3.11"
    exit 1
fi

# Check if Ollama is installed
echo -n "Checking Ollama installation... "
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama installed"
else
    echo -e "${RED}✗${NC}"
    echo "Ollama is not installed. Please install it first."
    echo "Run: brew install ollama"
    exit 1
fi

# Check if Ollama is running
echo -n "Checking Ollama service... "
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama is running"
else
    echo -e "${YELLOW}!${NC} Ollama is not running"
    echo "Please start Ollama in another terminal:"
    echo "  ollama serve"
    echo ""
    read -p "Press Enter once Ollama is running... "
fi

# Check if llama model is available
echo -n "Checking Llama model... "
if ollama list | grep -q "llama3.2:3b"; then
    echo -e "${GREEN}✓${NC} Llama 3.2 model available"
else
    echo -e "${YELLOW}!${NC} Llama 3.2 model not found"
    echo "Downloading Llama 3.2 (3B) model... (this may take a few minutes)"
    ollama pull llama3.2:3b
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -n "Creating virtual environment... "
    python3 -m venv venv
    echo -e "${GREEN}✓${NC}"
fi

# Activate virtual environment
echo -n "Activating virtual environment... "
source venv/bin/activate
echo -e "${GREEN}✓${NC}"

# Install dependencies
echo -n "Installing Python dependencies... "
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓${NC}"

# Check if database exists
if [ ! -f "database/bfsi_olap.duckdb" ]; then
    echo ""
    echo "Database not found. Generating sample BFSI data..."
    echo ""
    python database/generate_sample_data.py
else
    echo -e "Database: ${GREEN}✓${NC} Found"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Starting Conversational AI..."
echo ""

# Run the application
python main.py
