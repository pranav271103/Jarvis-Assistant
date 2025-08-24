@echo off
:: Windows launcher for Jarvis AI Assistant

echo Starting Jarvis AI Assistant...

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Running setup...
    python setup.py
    if %ERRORLEVEL% neq 0 (
        echo Setup failed. Please check the error messages above.
        pause
        exit /b 1
    )
)

:: Activate virtual environment and run Jarvis
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

:: Run Jarvis with command line arguments
python main.py %*

:: Pause to see any error messages
if %ERRORLEVEL% neq 0 pause
