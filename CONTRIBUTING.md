# Contributing to Jarvis AI Assistant

Thank you for your interest in contributing to the Jarvis AI Assistant project! We welcome contributions from everyone.

## How to Contribute

1. **Fork** the repository on GitHub
2. **Clone** the project to your own machine
3. **Commit** changes to your own branch
4. **Push** your work back up to your fork
5. Submit a **Pull Request** so we can review your changes

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep lines under 100 characters

## Testing

Run tests using:
```bash
pytest
```

## Submitting Changes

1. Write clear, concise commit messages
2. Reference any related issues in your PR
3. Ensure all tests pass
4. Update documentation as needed

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.
