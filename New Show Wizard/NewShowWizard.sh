#!/bin/bash
# New Show Wizard Launcher Script for Unix-based systems
# This script launches the New Show Database Wizard

# Set the working directory to the script's location
cd "$(dirname "$0")"

# Optional: activate virtual environment if you use one
# Uncomment the line below if you have a virtual environment
# source venv/bin/activate

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if psycopg2 is installed
if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "Warning: psycopg2 is not installed"
    echo "Installing psycopg2-binary..."
    pip3 install psycopg2-binary
fi

# Run the New Show Wizard
echo "Starting New Show Database Wizard..."
python3 ChangeDBscript.py

# Exit status
exit $?
