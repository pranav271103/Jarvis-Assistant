"""
Custom exceptions for the Jarvis Assistant application.

This module defines custom exceptions used throughout the application
for better error handling and debugging.
"""

from typing import Optional, Dict, Any


class CommandError(Exception):
    """Base exception for command-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class CommandExecutionError(CommandError):
    """Raised when a command fails to execute."""
    pass


class CommandValidationError(CommandError):
    """Raised when command validation fails."""
    pass


class ResourceUnavailableError(CommandError):
    """Raised when a required resource is unavailable."""
    pass