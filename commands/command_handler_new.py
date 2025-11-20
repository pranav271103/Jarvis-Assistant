import webbrowser
import os
import sys
import json
import logging
import datetime
import re
from typing import Dict, Callable, List, Optional, Tuple, Union, Any, TypeVar
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
    
    def _parse_command(self, user_input: str) -> Tuple[str, str]:
        """
        Parse natural language input to extract command and arguments.
        
        Args:
            user_input: The raw user input string
            
        Returns:
            Tuple of (command, arguments_string)
        """
        if not user_input or not isinstance(user_input, str):
            return None, ""
        
        user_input = user_input.strip().lower()
        
        # Check for exact command matches first
        if user_input in self.commands:
            return user_input, ""
        
        # Try to match voice commands
        for voice_cmd, mapped_cmd in self.voice_commands.items():
            if user_input.startswith(voice_cmd):
                args = user_input[len(voice_cmd):].strip()
                return mapped_cmd, args
        
        # Parse system commands with actions
        system_actions = ['shutdown', 'restart', 'sleep', 'lock', 'hibernate', 'logout']
        for action in system_actions:
            if action in user_input:
                return 'system', action
        
        # Check if user input starts with any registered command
        parts = user_input.split(maxsplit=1)
        if parts:
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd in self.commands:
                return cmd, args
            
            # Check for partial command matches
            for registered_cmd in self.commands.keys():
                if cmd.startswith(registered_cmd) or registered_cmd.startswith(cmd):
                    return registered_cmd, args
        
        # If no command found, check if it looks like a search query
        search_keywords = ['search', 'find', 'look up', 'google']
        for keyword in search_keywords:
            if keyword in user_input:
                query = user_input.replace(keyword, '').strip()
                return 'search', query
        
        # Default: treat as LLM query if LLM is available
        return None, user_input
    
    def handle_command(self, user_input: str) -> str:
        """
        Handle a command with intelligent parsing and error handling.
        
        Args:
            user_input: The complete user input string
            
        Returns:
            str: Response from command execution
        """
        if not user_input or not isinstance(user_input, str) or not user_input.strip():
            return "Please provide a command."
        
        try:
            # Parse the command and arguments
            command, args_string = self._parse_command(user_input)
            
            # Log the parsed command
            logger.info(f"Parsed command: '{command}' with args: '{args_string}'")
            
            # If no command found, use LLM for general conversation
            if not command:
                if self.llm_chat:
                    try:
                        return self.llm_chat.generate_response(user_input)
                    except Exception as e:
                        logger.error(f"LLM error: {e}")
                        return "I'm not sure how to help with that. Try 'help' to see available commands."
                else:
                    return "I'm not sure how to help with that. Try 'help' to see available commands."
            
            # Handle 'system' command specially to extract action from args
            if command == 'system':
                if not args_string:
                    return "Please specify a system action: shutdown, restart, sleep, lock, hibernate, or logout."
                return self._system_control(args_string)
            
            # Get the command handler
            if command not in self.commands:
                suggestions = self._get_suggestions(command)
                if suggestions:
                    return f"Unknown command: '{command}'. Did you mean: {', '.join(suggestions)}?"
                return f"Unknown command: '{command}'. Type 'help' for available commands."
            
            cmd_info = self.commands[command]
            handler = cmd_info['handler']
            
            # Check if voice is required but not enabled
            if cmd_info.get('needs_voice', False) and not self.voice_enabled:
                return "Voice control is disabled. Enable it with 'voice on'."
            
            # Execute the command with arguments
            if args_string:
                # Split args into list for multi-argument commands
                args_list = args_string.split()
                result = handler(*args_list)
            else:
                result = handler()
            
            # Add to command history
            self.command_history.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'command': command,
                'args': args_string,
                'success': True
            })
            
            return result if result else "Command executed successfully."
            
        except CommandValidationError as e:
            logger.error(f"Validation error: {e.message}")
            return e.message
        except CommandExecutionError as e:
            logger.error(f"Execution error: {e.message}")
            return e.message
        except ResourceUnavailableError as e:
            logger.error(f"Resource error: {e.message}")
            return e.message
        except Exception as e:
            logger.exception(f"Unexpected error handling command: {user_input}")
            return f"An unexpected error occurred: {str(e)}"
    
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
            
            # Check for partial matches in commands
            for cmd in self.commands.keys():
                if target_lower in cmd.lower() or cmd.lower() in target_lower:
                    suggestions.append(cmd)
            
            # Check for partial matches in web apps
            for app in self.web_apps.keys():
                if target_lower in app.lower():
                    suggestions.append(f"open {app}")
            
            # Remove duplicates and limit
            return list(dict.fromkeys(suggestions))[:5]
            
        except Exception as e:
            logger.error(f"Error getting suggestions for '{target}': {e}")
            return []
    
    # Command implementations
    def _get_current_time(self, *args) -> str:
        """Get the current time."""
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}"
    
    def _get_current_date(self, *args) -> str:
        """Get the current date."""
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}"
    
    def _search_web(self, *args) -> str:
        """
        Search the web using the default browser.
        
        Args:
            *args: Search query terms
            
        Returns:
            str: Status message
        """
        try:
            if not args or not any(args):
                raise CommandValidationError("Please specify what you'd like to search for.")
            
            query = ' '.join(args).strip()
            if not query:
                raise CommandValidationError("Please specify what you'd like to search for.")
            
            search_url = f"https://www.google.com/search?q={quote(query)}"
            webbrowser.open(search_url)
            logger.info(f"Searching for: {query}")
            return f"Searching for '{query}'"
            
        except CommandValidationError:
            raise
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            raise CommandExecutionError("I encountered an error while searching the web.") from e
    
    def _open_application(self, *args) -> str:
        """
        Open an application or website.
        
        Args:
            *args: Application name or URL
            
        Returns:
            str: Status message
        """
        try:
            if not args or not any(args):
                raise CommandValidationError("Please specify what you'd like to open.")
            
            target = ' '.join(args).strip().lower()
            if not target:
                raise CommandValidationError("Please specify what you'd like to open.")
            
            # Check if it's a URL
            if target.startswith(('http://', 'https://', 'www.')):
                webbrowser.open(target if target.startswith('http') else f'https://{target}')
                return f"Opening {target}"
            
            # Check web apps
            if target in self.web_apps:
                webbrowser.open(self.web_apps[target])
                return f"Opening {target}"
            
            # Check system apps
            if target in self.system_apps:
                try:
                    os.startfile(self.system_apps[target])
                    return f"Opening {target}"
                except Exception as e:
                    logger.error(f"Failed to open {target}: {e}")
                    raise CommandExecutionError(f"Failed to open {target}")
            
            # Try to open as a system command
            try:
                os.startfile(target)
                return f"Opening {target}"
            except:
                suggestions = self._get_suggestions(target)
                if suggestions:
                    return f"I couldn't find '{target}'. Did you mean: {', '.join(suggestions)}?"
                return f"I couldn't find '{target}'. Try 'help' for available options."
                
        except CommandValidationError:
            raise
        except CommandExecutionError:
            raise
        except Exception as e:
            logger.error(f"Error opening application: {e}")
            raise CommandExecutionError(f"Failed to open application: {str(e)}") from e
    
    def _clear_chat(self, *args) -> str:
        """Clear the chat history."""
        try:
            if self.llm_chat:
                self.llm_chat.clear_conversation()
            self.command_history.clear()
            return "Chat history cleared."
        except Exception as e:
            logger.error(f"Error clearing chat: {e}")
            return "Failed to clear chat history."
    
    def _show_help(self, *args) -> str:
        """
        Show help information.
        
        Args:
            *args: Optional specific command to get help for
            
        Returns:
            str: Help information
        """
        if args and args[0]:
            cmd = args[0].lower()
            if cmd in self.commands:
                info = self.commands[cmd]
                return f"{cmd}: {info.get('description', 'No description')}\nUsage: {info.get('usage', cmd)}"
            return f"Unknown command: {cmd}"
        
        # Show all available commands
        help_text = ["Available commands:", ""]
        for cmd, info in sorted(self.commands.items()):
            if not info.get('needs_voice', False):
                help_text.append(f"  {cmd}: {info.get('description', 'No description')}")
        
        help_text.append("\nYou can also:")
        help_text.append("  - Ask questions naturally")
        help_text.append("  - Say 'search [query]' to search the web")
        help_text.append("  - Say 'open [app/website]' to open applications")
        
        return "\n".join(help_text)
    
    def _system_control(self, action: str = None) -> str:
        """
        Handle system control commands.
        
        Args:
            action: The system action to perform
            
        Returns:
            str: Status message
        """
        if not action:
            raise CommandValidationError(
                "Please specify a system action: shutdown, restart, sleep, lock, hibernate, or logout."
            )
        
        action = action.lower().strip()
        
        try:
            success, message = self.system_controller.system_control(action)
            if success:
                return message
            else:
                raise CommandExecutionError(message)
                
        except SystemCommandError as e:
            raise CommandExecutionError(f"Failed to execute system command: {e}") from e
        except Exception as e:
            logger.exception("Unexpected error in system control")
            raise CommandExecutionError(f"An unexpected error occurred: {str(e)}") from e
    
    def _list_processes(self, *args) -> str:
        """List running processes."""
        try:
            processes = self.system_controller.get_running_processes()
            if not processes:
                return "No processes found."
            
            process_list = ["Running processes (top 20):", "PID    Name"]
            for proc in processes[:20]:
                pid = proc.get('pid', 'N/A')
                name = proc.get('name', 'Unknown')
                process_list.append(f"{pid:<6} {name}")
            
            if len(processes) > 20:
                process_list.append(f"\n... and {len(processes) - 20} more processes")
            
            return "\n".join(process_list)
            
        except Exception as e:
            logger.exception("Error listing processes")
            raise CommandExecutionError("Failed to list processes.") from e
    
    def _kill_process(self, *args) -> str:
        """
        Terminate a process by PID.
        
        Args:
            *args: Process ID to terminate
            
        Returns:
            str: Status message
        """
        if not args or not args[0]:
            raise CommandValidationError("Please specify a process ID to terminate.")
        
        try:
            pid = int(args[0])
            if pid <= 0:
                raise CommandValidationError("Process ID must be a positive number.")
            
            success, message = self.system_controller.kill_process(pid)
            if success:
                return message
            else:
                raise CommandExecutionError(message)
                
        except ValueError:
            raise CommandValidationError("Process ID must be a number.")
        except Exception as e:
            logger.exception(f"Error terminating process")
            raise CommandExecutionError(f"Failed to terminate process: {str(e)}") from e
    
    def _get_system_info(self, *args) -> str:
        """Get system information."""
        try:
            info = self.system_controller.get_system_info()
            if not info:
                return "No system information available."
            
            info_lines = ["System Information:", ""]
            for key, value in info.items():
                if key != 'disk_usage':
                    info_lines.append(f"{key.replace('_', ' ').title()}: {value}")
            
            # Handle disk usage separately
            if 'disk_usage' in info and isinstance(info['disk_usage'], dict):
                info_lines.append("\nDisk Usage:")
                for mount, usage in info['disk_usage'].items():
                    info_lines.append(f"  {mount}: {usage}")
            
            return "\n".join(info_lines)
            
        except Exception as e:
            logger.exception("Error getting system info")
            raise CommandExecutionError("Failed to retrieve system information.") from e
    
    def _toggle_voice(self, *args) -> str:
        """Toggle voice control on/off."""
        if args and args[0]:
            state = args[0].lower()
            if state in ('on', 'enable', 'yes', 'true'):
                self.voice_enabled = True
                return "Voice control enabled."
            elif state in ('off', 'disable', 'no', 'false'):
                self.voice_enabled = False
                return "Voice control disabled."
            else:
                return f"Invalid state: {state}. Use 'on' or 'off'."
        
        self.voice_enabled = not self.voice_enabled
        status = "enabled" if self.voice_enabled else "disabled"
        return f"Voice control {status}."
    
    def _listen_command(self, *args) -> str:
        """Listen for a voice command."""
        if not self.voice_enabled:
            return "Voice control is currently disabled. Say 'voice on' to enable it."
        
        if not self.speech_recognizer:
            raise ResourceUnavailableError("Speech recognition is not available.")
        
        try:
            text = self.speech_recognizer.listen()
            if not text or not text.strip():
                return "I didn't catch that. Please try again."
            
            return f"You said: {text}\n{self.handle_command(text)}"
            
        except Exception as e:
            logger.error(f"Error in voice recognition: {e}")
            return "I'm having trouble with voice recognition. Please try again or use text input."
    
    def _exit_application(self, *args) -> str:
        """Exit the application."""
        if hasattr(self, 'llm_chat') and self.llm_chat:
            try:
                self.llm_chat.clear_conversation()
            except Exception as e:
                logger.error(f"Error closing LLM chat: {e}")
        
        sys.exit(0)


# Initialize command handler
try:
    command_handler = CommandHandler()
except Exception as e:
    logger.error(f"Failed to initialize command handler: {e}")
    command_handler = None


def process_command(command: str) -> str:
    """
    Process a command string and return the response.
    
    Args:
        command: The command string to process
        
    Returns:
        str: The command response
    """
    if not command_handler:
        return "Command handler is not initialized."
    
    if not command or not command.strip():
        return "Please provide a command."
    
    try:
        return command_handler.handle_command(command)
    except Exception as e:
        logger.exception(f"Unexpected error processing command: {command}")
        return f"An unexpected error occurred: {str(e)}"