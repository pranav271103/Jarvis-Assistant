#!/usr/bin/env python3
"""
Setup script for Jarvis AI Assistant
"""
import os
import sys
import platform
import subprocess
import venv
from pathlib import Path
from setuptools import setup, find_packages

def print_header():
    """Print the setup header."""
    print("\n" + "="*50)
    print("Jarvis AI Assistant - Setup")
    print("="*50)

def check_python_version():
    """Check if the Python version is compatible."""
    required_version = (3, 8)
    if sys.version_info < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]}+ is required.")
        print(f"You are using Python {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)

def create_virtual_environment():
    """Create a Python virtual environment."""
    venv_dir = Path("venv")
    if not venv_dir.exists():
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    else:
        print("Virtual environment already exists.")
    
    # Get the correct pip path based on the OS
    if platform.system() == "Windows":
        pip_path = venv_dir / "Scripts" / "pip"
        python_path = venv_dir / "Scripts" / "python"
    else:
        pip_path = venv_dir / "bin" / "pip"
        python_path = venv_dir / "bin" / "python"
    
    return {
        'pip': str(pip_path),
        'python': str(python_path),
        'venv_dir': str(venv_dir)
    }

def install_dependencies(pip_path):
    """Install required Python packages."""
    print("\nInstalling dependencies...")
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("Error: requirements.txt not found!")
        sys.exit(1)
    
    cmd = [pip_path, "install", "-r", str(requirements_file)]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def setup_environment():
    """Set up the environment variables."""
    env_file = Path(".env")
    if not env_file.exists():
        print("\nSetting up environment variables...")
        api_key = input("Enter your Gemini API key (or press Enter to skip for now): ")
        
        with open(env_file, 'w') as f:
            if api_key:
                f.write(f"GEMINI_API_KEY={api_key}\n")
            else:
                f.write("# GEMINI_API_KEY=your_api_key_here\n")
        
        if not api_key:
            print("\nWARNING: No API key provided.")
            print("Please add your Gemini API key to the .env file before running Jarvis.")
    else:
        print("\nEnvironment file already exists.")

def main():
    """Main setup function."""
    print_header()
    check_python_version()
    
    # Create and activate virtual environment
    paths = create_virtual_environment()
    
    # Install dependencies
    install_dependencies(paths['pip'])
    
    # Set up environment
    setup_environment()
    
    print("\n" + "="*50)
    print("Setup completed successfully!")
    print("="*50)
    print("\nTo activate the virtual environment:")
    if platform.system() == "Windows":
        print("  .\\venv\\Scripts\\activate")
    else:
        print("  source venv/bin/activate")
    
    print("\nTo run Jarvis:")
    print("  python main.py           # Voice mode (default)")
    print("  python main.py --text    # Text mode")
    print("\nFor help, type 'help' or 'what can you do' when Jarvis is running.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(1)
