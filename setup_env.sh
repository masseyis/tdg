#!/bin/bash

# Script to set up the development environment

echo "🐍 Setting up Python virtual environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.13 or later."
    exit 1
fi

# Create virtual environment
python3 -m venv venv

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests, use:"
echo "  ./run_tests.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate && python3 -m pytest tests/ -v"
