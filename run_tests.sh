#!/bin/bash

# Script to run tests with the virtual environment

echo "🐍 Activating virtual environment..."
source venv/bin/activate

echo "🧪 Running tests..."
python3 -m pytest tests/ -v

echo "✅ Tests completed!"
