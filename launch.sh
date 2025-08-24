#!/bin/bash
# Unix/Linux launcher for Jarvis AI Assistant

echo "Starting Jarvis AI Assistant..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or later"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]]; then
    echo "Error: Python 3.8 or later is required"
    echo "Current version: $(python3 --version)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    python3 setup.py
    if [ $? -ne 0 ]; then
        echo "Setup failed. Please check the error messages above."
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

# Run Jarvis with command line arguments
python3 main.py "$@"

# If there was an error, wait for user input
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Jarvis exited with error code $exit_code"
    read -p "Press Enter to continue..."
fi
