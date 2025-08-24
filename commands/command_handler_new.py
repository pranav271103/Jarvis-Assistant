"""
Command handler for processing and executing user commands.

This module provides a command processing system with security checks,
error handling, and integration with system utilities and LLM services.
"""
import webbrowser
import os
import sys
import json
import logging
import datetime
from typing import Dict, Callable, List, Optional, Tuple, Union, Any, TypeVar, Type
from pathlib import Path
from urllib.parse import quote

# Import utilities with proper error handling
try:
    from utils.speech_utils import SpeechSynthesizer, SpeechRecognizer
    from llm.gemini_integration import GeminiChat
    from utils.system_utils import SystemController, SystemCommandError
    from config import Config
    from utils.exceptions import (
        CommandExecutionError,
        CommandValidationError,
        ResourceUnavailableError
    )
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    raise

# Type variable for command handler methods
T = TypeVar('T', bound='CommandHandler')

logger = logging.getLogger(__name__)

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

class CommandHandler:
    """Handles command processing and execution with security and error handling."""
    
    def __init__(self, 
                 system_controller: Optional[SystemController] = None,
                 llm_chat: Optional[GeminiChat] = None,
                 speech_synthesizer: Optional[SpeechSynthesizer] = None,
                 speech_recognizer: Optional[SpeechRecognizer] = None):
        """
        Initialize the command handler with required services.
        
        Args:
            system_controller: System controller instance
            llm_chat: LLM chat instance for natural language processing
            speech_synthesizer: Text-to-speech service
            speech_recognizer: Speech recognition service
        """
        self.system_controller = system_controller or SystemController()
        self.llm_chat = llm_chat
        self.speech_synthesizer = speech_synthesizer
        self.speech_recognizer = speech_recognizer
        
        # Initialize state
        self.voice_enabled = True
        self.command_history: List[Dict[str, Any]] = []
        
        # Initialize command registry
        self._register_commands()
        
        # Initialize voice command mappings and application mappings
        self.voice_commands = self._initialize_voice_commands()
        self.web_apps, self.system_apps = self._initialize_application_mappings()
    
    def _register_commands(self):
        """Register all available commands with their handlers and metadata."""
        self.commands: Dict[str, Dict[str, Any]] = {
            # Basic commands
            'time': {
                'handler': self._get_current_time,
                'description': 'Get the current time',
                'usage': 'time',
                'needs_voice': False
            },
            'date': {
                'handler': self._get_current_date,
                'description': 'Get the current date',
                'usage': 'date',
                'needs_voice': False
            },
            'search': {
                'handler': self._search_web,
                'description': 'Search the web',
                'usage': 'search [query]',
                'needs_voice': False
            },
            'open': {
                'handler': self._open_application,
                'description': 'Open an application or website',
                'usage': 'open [app/url]',
                'needs_voice': False
            },
            'clear': {
                'handler': self._clear_chat,
                'description': 'Clear the chat history',
                'usage': 'clear',
                'needs_voice': False
            },
            'help': {
                'handler': self._show_help,
                'description': 'Show help information',
                'usage': 'help [command]',
                'needs_voice': False
            },
            'exit': {
                'handler': self._exit_application,
                'description': 'Exit the application',
                'usage': 'exit',
                'needs_voice': False
            },
            
            # System control commands
            'system': {
                'handler': self._system_control,
                'description': 'Control system operations',
                'usage': 'system [shutdown|restart|sleep|lock|hibernate|logout]',
                'needs_voice': False,
                'requires_admin': True
            },
            'processes': {
                'handler': self._list_processes,
                'description': 'List running processes',
                'usage': 'processes',
                'needs_voice': False,
                'requires_admin': True
            },
            'kill': {
                'handler': self._kill_process,
                'description': 'Terminate a process by ID',
                'usage': 'kill [pid]',
                'needs_voice': False,
                'requires_admin': True
            },
            'system_info': {
                'handler': self._get_system_info,
                'description': 'Show system information',
                'usage': 'system_info',
                'needs_voice': False
            },
            
            # Voice control commands
            'voice': {
                'handler': self._toggle_voice,
                'description': 'Toggle voice control',
                'usage': 'voice [on/off]',
                'needs_voice': False
            },
            'listen': {
                'handler': self._listen_command,
                'description': 'Listen for a voice command',
                'usage': 'listen',
                'needs_voice': True
            }
        }
    
    def _initialize_voice_commands(self) -> Dict[str, str]:
        """Initialize and return the voice command mappings."""
        return {
            # Time and date
            'what time is it': 'time',
            'what is the time': 'time',
            'current time': 'time',
            'tell me the time': 'time',
            'what is today': 'date',
            'what is the date': 'date',
            'current date': 'date',
            "what's the date": 'date',
            
            # Web and applications
            'search the web for': 'search',
            'search for': 'search',
            'look up': 'search',
            'google': 'search',
            'open': 'open',
            'launch': 'open',
            'start': 'open',
            'send an email': 'email',
            'compose email': 'email',
            
            # System controls
            'shutdown': 'system shutdown',
            'shut down': 'system shutdown',
            'turn off': 'system shutdown',
            'power off': 'system shutdown',
            'restart': 'system restart',
            'reboot': 'system restart',
            'sleep': 'system sleep',
            'lock': 'system lock',
            'lock computer': 'system lock',
            'lock my computer': 'system lock',
            'hibernate': 'system hibernate',
            'log out': 'system logout',
            'sign out': 'system logout',
            'log off': 'system logout',
            
            # System info
            'list processes': 'processes',
            'show processes': 'processes',
            'running processes': 'processes',
            'system info': 'system_info',
            'system information': 'system_info',
            'computer info': 'system_info',
            
            # General
            'clear the chat': 'clear',
            'clear chat': 'clear',
            'help me': 'help',
            'show help': 'help',
            'goodbye': 'exit',
            'exit': 'exit',
            'quit': 'exit'
        }
    
    def _initialize_application_mappings(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Initialize and return web and system application mappings."""
        web_apps = {
            'youtube': 'https://youtube.com',
            'google': 'https://google.com',
            'github': 'https://github.com',
            'stackoverflow': 'https://stackoverflow.com',
            'reddit': 'https://reddit.com',
            'twitter': 'https://twitter.com',
            'facebook': 'https://facebook.com',
            'instagram': 'https://instagram.com',
            'linkedin': 'https://linkedin.com',
            'netflix': 'https://netflix.com',
            'amazon': 'https://amazon.com',
            'wikipedia': 'https://wikipedia.org',
        }
        
        system_apps = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'paint': 'mspaint.exe',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'powerpoint': 'powerpnt.exe',
        }
        
        return web_apps, system_apps
    
    def _get_suggestions(self, target: str) -> List[str]:
        """
        Get suggested commands similar to the target.
        
        Args:
            target: The input string to find suggestions for
            
        Returns:
            List of suggested commands/applications
        """
        if not target or not isinstance(target, str):
            return []
            
        try:
            suggestions = []
            target_lower = target.lower()
            
            # Check for partial matches in web apps
            if hasattr(self, 'web_apps'):
                suggestions.extend(
                    app for app in self.web_apps
                    if target_lower in app.lower()
                )
            
            # Check for partial matches in system apps
            if hasattr(self, 'system_apps'):
                suggestions.extend(
                    app for app in self.system_apps
                    if target_lower in app.lower()
                )
            
            # Check for partial matches in commands
            if hasattr(self, 'commands'):
                for cmd in self.commands:
                    if target_lower in cmd.lower():
                        suggestions.append(cmd)
            
            # Remove duplicates and limit the number of suggestions
            return list(dict.fromkeys(suggestions))[:5]
            
        except Exception as e:
            logger.error(f"Error getting suggestions for '{target}': {e}")
            return []
    
    def _match_command(self, command: str) -> Tuple[str, List[str]]:
        """
        Match a voice command to the best fitting command.
        
        Args:
            command: The voice command to match
            
        Returns:
            Tuple of (matched_command, arguments) or (None, []) if no match
        """
        if not command or not isinstance(command, str):
            return None, []
            
        command = command.lower().strip()
        
        # Try exact match first
        if command in self.voice_commands:
            return self.voice_commands[command], []
        
        # Try partial matches
        for voice_cmd, cmd in self.voice_commands.items():
            if command.startswith(voice_cmd):
                args = command[len(voice_cmd):].strip().split()
                return cmd, args
        
        # No match found
        return None, []
    
    def handle_command(self, command: str, *args) -> str:
        """
        Handle a command with its arguments.
        
        Args:
            command: The command to execute
            *args: Arguments for the command
            
        Returns:
            str: The command response
            
        Raises:
            CommandError: If the command execution fails
        """
        if not command or not isinstance(command, str):
            raise CommandValidationError("No command provided")
        
        command = command.lower().strip()
        
        # Log the command
        logger.info(f"Processing command: {command} with args: {args}")
        
        # Try direct command execution first
        if command in self.commands:
            try:
                cmd_info = self.commands[command]
                handler = cmd_info.get('handler')
                
                if not handler or not callable(handler):
                    raise CommandExecutionError(f"Invalid handler for command: {command}")
                
                # Execute the command handler
                result = handler(*args)
                
                # Log successful command execution
                self.command_history.append({
                    'command': command,
                    'args': args,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'success': True
                })
                
                return result
                
            except Exception as e:
                # Log command failure
                self.command_history.append({
                    'command': command,
                    'args': args,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
                
                # Re-raise the exception with additional context
                if not isinstance(e, CommandError):
                    raise CommandExecutionError(
                        f"Error executing command '{command}': {str(e)}",
                        details={'command': command, 'args': args}
                    ) from e
                raise
        
        # Try to match voice command patterns
        matched_cmd, cmd_args = self._match_command(command)
        if matched_cmd and matched_cmd in self.commands:
            return self.handle_command(matched_cmd, *cmd_args, *args)
        
        # No command matched
        suggestions = self._get_suggestions(command)
        suggestion_text = f"\n\nSimilar commands: {', '.join(suggestions)}" if suggestions else ""
        raise CommandValidationError(
            f"Unknown command: {command}" + suggestion_text,
            details={'command': command, 'suggestions': suggestions}
        )
    
    # Command implementations
    
    def _get_current_time(self, *args) -> str:
        """
        Get the current time.
        
        Returns:
            str: Formatted current time
        """
        try:
            current_time = datetime.datetime.now().strftime('%I:%M %p')
            return f"The current time is {current_time}"
        except Exception as e:
            logger.error(f"Error getting current time: {e}")
            return "I couldn't get the current time. Please try again later."
    
    def _get_current_date(self, *args) -> str:
        """
        Get the current date.
        
        Returns:
            str: Formatted current date
        """
        try:
            current_date = datetime.datetime.now().strftime('%A, %B %d, %Y')
            return f"Today is {current_date}"
        except Exception as e:
            logger.error(f"Error getting current date: {e}")
            return "I couldn't get the current date. Please try again later."
    
    def _search_web(self, *args) -> str:
        """
        Search the web using the default browser.
        
        Args:
            *args: Search query terms
            
        Returns:
            str: Status message
            
        Raises:
            CommandValidationError: If the search query is invalid
            CommandExecutionError: If the search fails
        """
        try:
            if not args:
                raise CommandValidationError("Please specify what you'd like to search for.")
            
            # Sanitize query to prevent injection
            query = ' '.join(args).strip()
            if not query:
                raise CommandValidationError("Search query cannot be empty.")
                
            # URL encode the query
            encoded_query = quote(query)
            
            # Construct and open the search URL
            search_url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(search_url)
            
            return f"Searching the web for: {query}"
            
        except webbrowser.Error as e:
            error_msg = f"Failed to open web browser: {e}"
            logger.error(error_msg)
            raise CommandExecutionError("I couldn't open the web browser.") from e
            
        except Exception as e:
            error_msg = f"Error performing web search: {e}"
            logger.error(error_msg)
            raise CommandExecutionError("I encountered an error while searching the web.") from e
    
    def _open_application(self, *args) -> str:
        """
        Open an application or website.
        
        Args:
            *args: Application/website name or path
            
        Returns:
            str: Status message
            
        Raises:
            CommandValidationError: If no target is specified
            CommandExecutionError: If the application/website cannot be opened
        """
        try:
            if not args:
                raise CommandValidationError("Please specify an application or website to open.")
            
            target = args[0].lower().strip()
            if not target:
                raise CommandValidationError("Application/website name cannot be empty.")
            
            # Check if it's a web app
            if target in self.web_apps:
                url = self.web_apps[target]
                try:
                    webbrowser.open(url)
                    return f"Opening {target} in your browser."
                except webbrowser.Error as e:
                    raise CommandExecutionError(
                        f"I couldn't open {target} in your browser.",
                        details={'error': str(e), 'url': url}
                    ) from e
            
            # Check if it's a system app
            if target in self.system_apps:
                app_path = self.system_apps[target]
                try:
                    os.startfile(app_path)
                    return f"Opening {target}..."
                except OSError as e:
                    raise CommandExecutionError(
                        f"I couldn't open {target}.",
                        details={'error': str(e), 'app': target, 'path': app_path}
                    ) from e
            
            # If not found in either, try to open as URL or file path
            try:
                # Check if it looks like a URL
                if any(target.startswith(prefix) for prefix in ('http://', 'https://', 'www.')):
                    url = target if target.startswith('http') else f'https://{target}'
                    webbrowser.open(url)
                    return f"Opening {url} in your browser."
                
                # Try as a file path
                path = Path(target).expanduser().resolve()
                if path.exists():
                    os.startfile(str(path))
                    return f"Opening {path.name}..."
                
                # If we get here, we couldn't identify the target
                suggestions = self._get_suggestions(target)
                if suggestions:
                    suggestion_text = ". Try one of these: " + ", ".join(suggestions)
                else:
                    suggestion_text = ""
                    
                raise CommandValidationError(
                    f"I don't know how to open '{target}'." + suggestion_text,
                    details={'target': target, 'suggestions': suggestions}
                )
                
            except (OSError, webbrowser.Error) as e:
                raise CommandExecutionError(
                    f"I couldn't open '{target}'.",
                    details={'error': str(e), 'target': target}
                ) from e
                
        except Exception as e:
            if not isinstance(e, (CommandValidationError, CommandExecutionError)):
                logger.exception("Unexpected error in _open_application")
                raise CommandExecutionError(
                    "An unexpected error occurred while trying to open that.",
                    details={'error': str(e), 'target': target}
                ) from e
            raise
    
    def _clear_chat(self, *args) -> str:
        """
        Clear the chat history.
        
        Returns:
            str: Confirmation message
            
        Raises:
            CommandExecutionError: If clearing the chat fails
        """
        try:
            if not hasattr(self, 'llm_chat') or not self.llm_chat:
                raise ResourceUnavailableError("Chat functionality is not available.")
                
            if hasattr(self.llm_chat, 'clear_history'):
                self.llm_chat.clear_history()
                return "Chat history cleared."
            return "Chat history clearing is not supported by the current chat instance."
            
        except Exception as e:
            error_msg = f"Failed to clear chat history: {e}"
            logger.error(error_msg)
            raise CommandExecutionError(
                "I couldn't clear the chat history.",
                details={'error': str(e)}
            ) from e
    
    def _show_help(self, *args) -> str:
        """
        Show available commands or help for a specific command.
        
        Args:
            *args: Optional command name to get help for
            
        Returns:
            str: Help message
        """
        if args and args[0]:
            # Show help for a specific command
            cmd = args[0].lower()
            if cmd in self.commands:
                cmd_info = self.commands[cmd]
                help_text = [
                    f"Command: {cmd}",
                    f"Description: {cmd_info.get('description', 'No description available')}",
                    f"Usage: {cmd_info.get('usage', cmd)}"
                ]
                return "\n".join(help_text)
            return f"No help available for unknown command: {cmd}"
        
        # Show all available commands
        help_text = ["Available commands:", ""]
        for cmd, info in sorted(self.commands.items()):
            if not info.get('needs_voice', False):  # Skip voice-only commands
                help_text.append(f"{cmd}: {info.get('description', 'No description')}")
        
        return "\n".join(help_text)
    
    def _system_control(self, action: str = None) -> str:
        """
        Handle system control commands.
        
        Args:
            action: The system action to perform (shutdown, restart, etc.)
            
        Returns:
            str: Status message
            
        Raises:
            CommandValidationError: If the action is not supported
            CommandExecutionError: If the system command fails
        """
        if not action:
            raise CommandValidationError("Please specify a system action (shutdown, restart, etc.)")
        
        action = action.lower()
        
        try:
            if action == 'shutdown':
                self.system_controller.shutdown()
                return "System is shutting down..."
            elif action == 'restart':
                self.system_controller.restart()
                return "System is restarting..."
            elif action == 'sleep':
                self.system_controller.sleep()
                return "System is going to sleep..."
            elif action == 'lock':
                self.system_controller.lock()
                return "System is locked."
            elif action == 'hibernate':
                self.system_controller.hibernate()
                return "System is hibernating..."
            elif action == 'logout':
                self.system_controller.logout()
                return "Logging out..."
            else:
                raise CommandValidationError(
                    f"Unsupported system action: {action}",
                    details={'valid_actions': ['shutdown', 'restart', 'sleep', 'lock', 'hibernate', 'logout']}
                )
                
        except SystemCommandError as e:
            raise CommandExecutionError(
                f"Failed to execute system command: {e}",
                details={'action': action, 'error': str(e)}
            ) from e
        except Exception as e:
            logger.exception("Unexpected error in system control")
            raise CommandExecutionError(
                f"An unexpected error occurred while trying to {action} the system.",
                details={'action': action, 'error': str(e)}
            ) from e
    
    def _list_processes(self, *args) -> str:
        """
        List running processes.
        
        Returns:
            str: Formatted list of processes
            
        Raises:
            CommandExecutionError: If process listing fails
        """
        try:
            processes = self.system_controller.get_processes()
            if not processes:
                return "No processes found."
                
            # Format the process list
            process_list = ["Running processes:", "PID\tName"]
            for pid, name in processes[:10]:  # Show first 10 processes
                process_list.append(f"{pid}\t{name}")
                
            if len(processes) > 10:
                process_list.append(f"... and {len(processes) - 10} more processes")
                
            return "\n".join(process_list)
            
        except SystemCommandError as e:
            raise CommandExecutionError(
                "Failed to list processes.",
                details={'error': str(e)}
            ) from e
        except Exception as e:
            logger.exception("Error listing processes")
            raise CommandExecutionError(
                "An error occurred while listing processes.",
                details={'error': str(e)}
            ) from e
    
    def _kill_process(self, pid: str = None) -> str:
        """
        Terminate a process by PID.
        
        Args:
            pid: Process ID to terminate
            
        Returns:
            str: Status message
            
        Raises:
            CommandValidationError: If PID is not provided or invalid
            CommandExecutionError: If process termination fails
        """
        if not pid:
            raise CommandValidationError("Please specify a process ID to terminate.")
            
        try:
            pid_int = int(pid)
            if pid_int <= 0:
                raise CommandValidationError("Process ID must be a positive number.")
                
            success = self.system_controller.terminate_process(pid_int)
            if success:
                return f"Process {pid} terminated successfully."
            return f"Failed to terminate process {pid}."
            
        except ValueError:
            raise CommandValidationError("Process ID must be a number.")
        except SystemCommandError as e:
            raise CommandExecutionError(
                f"Failed to terminate process {pid}.",
                details={'pid': pid, 'error': str(e)}
            ) from e
        except Exception as e:
            logger.exception(f"Error terminating process {pid}")
            raise CommandExecutionError(
                f"An error occurred while terminating process {pid}.",
                details={'pid': pid, 'error': str(e)}
            ) from e
    
    def _get_system_info(self, *args) -> str:
        """
        Get system information.
        
        Returns:
            str: Formatted system information
            
        Raises:
            CommandExecutionError: If system info retrieval fails
        """
        try:
            info = self.system_controller.get_system_info()
            if not info:
                return "No system information available."
                
            # Format the system info
            info_lines = ["System Information:"]
            for key, value in info.items():
                info_lines.append(f"{key.replace('_', ' ').title()}: {value}")
                
            return "\n".join(info_lines)
            
        except SystemCommandError as e:
            raise CommandExecutionError(
                "Failed to retrieve system information.",
                details={'error': str(e)}
            ) from e
        except Exception as e:
            logger.exception("Error getting system info")
            raise CommandExecutionError(
                "An error occurred while retrieving system information.",
                details={'error': str(e)}
            ) from e
    
    def _toggle_voice(self, state: str = None) -> str:
        """
        Toggle voice control on/off.
        
        Args:
            state: Optional state to set ('on' or 'off')
            
        Returns:
            str: Status message
        """
        if state:
            state = state.lower()
            if state in ('on', 'enable', 'yes', 'true'):
                self.voice_enabled = True
                return "Voice control enabled."
            elif state in ('off', 'disable', 'no', 'false'):
                self.voice_enabled = False
                return "Voice control disabled."
            else:
                return f"Invalid state: {state}. Use 'on' or 'off'."
        
        # Toggle current state
        self.voice_enabled = not self.voice_enabled
        status = "enabled" if self.voice_enabled else "disabled"
        return f"Voice control {status}."
    
    def _listen_command(self, *args) -> str:
        """
        Listen for a voice command.
        
        Returns:
            str: Status message or command response
            
        Raises:
            ResourceUnavailableError: If speech recognition is not available
        """
        if not self.voice_enabled:
            return "Voice control is currently disabled. Say 'voice on' to enable it."
            
        if not self.speech_recognizer:
            raise ResourceUnavailableError("Speech recognition is not available.")
            
        try:
            # Listen for a voice command
            text = self.speech_recognizer.listen()
            if not text or not text.strip():
                return "I didn't catch that. Please try again."
                
            # Process the recognized command
            return f"You said: {text}\n{self.handle_command(text)}"
            
        except Exception as e:
            logger.error(f"Error in voice recognition: {e}")
            return "I'm having trouble with voice recognition. Please try again or use text input."
    
    def _exit_application(self, *args) -> str:
        """
        Exit the application.
        
        Returns:
            str: Farewell message
        """
        # Clean up resources
        if hasattr(self, 'llm_chat') and self.llm_chat:
            try:
                self.llm_chat.close()
            except Exception as e:
                logger.error(f"Error closing LLM chat: {e}")
        
        # Exit the application
        sys.exit(0)
        return "Goodbye!"

# Initialize command handler
command_handler = CommandHandler()

def process_command(command: str) -> str:
    """
    Process a command string and return the response.
    
    Args:
        command: The command string to process
        
    Returns:
        str: The command response
    """
    if not command or not command.strip():
        return "Please provide a command."
        
    # Split the command into parts
    parts = command.strip().split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    try:
        return command_handler.handle_command(cmd, *args)
    except CommandError as e:
        return f"Error: {e.message}"
    except Exception as e:
        logger.exception(f"Unexpected error processing command: {command}")
        return f"An unexpected error occurred: {str(e)}"
