"""
System utilities for controlling the computer and getting system information.

This module provides system-level operations with proper security measures and error handling.
"""

import os
import platform
import subprocess
import shlex
import psutil
import logging
from typing import Dict, Tuple, Optional, List, Union, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemCommandError(Exception):
    """Exception raised for errors in system command execution."""
    
    def __init__(self, message: str, returncode: Optional[int] = None, stderr: Optional[str] = None):
        self.message = message
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(self.message)


class SystemController:
    """Handles system control operations with security and error handling."""
    
    def __init__(self):
        """Initialize the system controller with platform-specific settings."""
        self.platform = platform.system().lower()
        self.safe_commands = self._get_safe_commands()
    
    def _get_safe_commands(self) -> Dict[str, List[str]]:
        """Define a whitelist of safe commands and their allowed arguments."""
        return {
            'shutdown': ['/s', '/r', '/h', '/l'],
            'systeminfo': [],
            'tasklist': [],
            'ps': ['aux', '-ef'],
            'kill': [],
        }
    
    def _validate_command(self, command: str) -> Tuple[str, List[str]]:
        """Validate and parse a command to prevent injection attacks."""
        if not command or not isinstance(command, str):
            raise ValueError("Command must be a non-empty string")
        
        parts = shlex.split(command)
        if not parts:
            raise ValueError("Empty command")
        
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd not in self.safe_commands:
            raise ValueError(f"Command not allowed: {cmd}")
        
        allowed_args = self.safe_commands[cmd]
        if allowed_args and args and args[0] not in allowed_args:
            raise ValueError(f"Invalid arguments for {cmd}")
        
        if cmd == 'kill' and args:
            try:
                pid = int(args[0])
                if pid <= 0:
                    raise ValueError("PID must be a positive integer")
            except ValueError as e:
                raise ValueError("Invalid PID") from e
        
        return cmd, args
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Get comprehensive system information.
        
        Returns:
            Dict containing system information or error details.
        """
        try:
            system_info = {
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'cpu_usage': f"{psutil.cpu_percent()}%",
                'memory_usage': f"{psutil.virtual_memory().percent}%",
                'disk_usage': self._get_disk_usage(),
                'python_version': platform.python_version(),
                'boot_time': self._format_timestamp(psutil.boot_time())
            }
            return system_info
        except Exception as e:
            logger.exception("Failed to get system info")
            return {'error': str(e), 'type': type(e).__name__}
    
    def _get_disk_usage(self) -> Dict[str, str]:
        """Get disk usage information."""
        try:
            partitions = psutil.disk_partitions()
            usage = {}
            for part in partitions:
                try:
                    usage[part.mountpoint] = f"{psutil.disk_usage(part.mountpoint).percent}%"
                except Exception as e:
                    logger.warning(f"Could not get disk usage for {part.mountpoint}: {e}")
            return usage
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {'error': str(e)}
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format a timestamp to a human-readable string."""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def execute_system_command(self, command: str) -> Tuple[bool, str]:
        """
        Execute a system command with security checks.
        
        Args:
            command: The command to execute (will be validated)
            
        Returns:
            Tuple of (success, result)
            
        Raises:
            SystemCommandError: If command execution fails
        """
        try:
            cmd, args = self._validate_command(command)
            
            result = subprocess.run(
                [cmd] + args,
                shell=False,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SystemCommandError(
                    f"Command failed with code {result.returncode}",
                    returncode=result.returncode,
                    stderr=result.stderr
                )
            
            return True, result.stdout.strip()
            
        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after {e.timeout} seconds"
            logger.error(error_msg)
            raise SystemCommandError(error_msg) from e
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e}"
            logger.error(error_msg)
            raise SystemCommandError(
                error_msg,
                returncode=e.returncode,
                stderr=e.stderr
            ) from e
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.exception(error_msg)
            raise SystemCommandError(error_msg) from e
    
    def system_control(self, action: str) -> Tuple[bool, str]:
        """Perform system control actions."""
        actions = {
            'shutdown': self.shutdown,
            'restart': self.restart,
            'sleep': self.sleep,
            'lock': self.lock,
            'hibernate': self.hibernate,
            'logout': self.logout
        }
        
        action = action.lower()
        if action in actions:
            return actions[action]()
        return False, f"Unknown system action: {action}"
    
    def shutdown(self) -> Tuple[bool, str]:
        """Shutdown the system."""
        try:
            if platform.system() == "Windows":
                os.system("shutdown /s /t 1")
            else:
                os.system("shutdown -h now")
            return True, "System is shutting down..."
        except Exception as e:
            return False, f"Failed to shutdown: {str(e)}"
    
    def restart(self) -> Tuple[bool, str]:
        """Restart the system."""
        try:
            if platform.system() == "Windows":
                os.system("shutdown /r /t 1")
            else:
                os.system("shutdown -r now")
            return True, "System is restarting..."
        except Exception as e:
            return False, f"Failed to restart: {str(e)}"
    
    def sleep(self) -> Tuple[bool, str]:
        """Put the system to sleep."""
        try:
            if platform.system() == "Windows":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            else:
                os.system("systemctl suspend")
            return True, "System is going to sleep..."
        except Exception as e:
            return False, f"Failed to sleep: {str(e)}"
    
    def lock(self) -> Tuple[bool, str]:
        """Lock the system."""
        try:
            if platform.system() == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif platform.system() == "Darwin":
                os.system("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend")
            else:
                os.system("gnome-screensaver-command -l")
            return True, "System is locked."
        except Exception as e:
            return False, f"Failed to lock: {str(e)}"
    
    def hibernate(self) -> Tuple[bool, str]:
        """Hibernate the system."""
        try:
            if platform.system() == "Windows":
                os.system("shutdown /h")
            else:
                os.system("systemctl hibernate")
            return True, "System is hibernating..."
        except Exception as e:
            return False, f"Failed to hibernate: {str(e)}"
    
    def logout(self) -> Tuple[bool, str]:
        """Log out the current user."""
        try:
            if platform.system() == "Windows":
                os.system("shutdown /l")
            else:
                os.system("gnome-session-quit --no-prompt")
            return True, "Logging out..."
        except Exception as e:
            return False, f"Failed to logout: {str(e)}"
    
    def get_running_processes(self) -> list:
        """Get list of running processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return processes
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            return []
    
    def kill_process(self, pid: int) -> Tuple[bool, str]:
        """Kill a running process by PID."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            return True, f"Process {pid} terminated successfully"
        except psutil.NoSuchProcess:
            return False, f"No process found with PID {pid}"
        except Exception as e:
            return False, f"Error killing process {pid}: {e}"


# Initialize system controller
system_controller = SystemController()


def get_system_info() -> Dict[str, str]:
    """Get system information."""
    return system_controller.get_system_info()


def control_system(action: str) -> Tuple[bool, str]:
    """Control system actions."""
    return system_controller.system_control(action)


def get_processes() -> list:
    """Get list of running processes."""
    return system_controller.get_running_processes()


def terminate_process(pid: int) -> Tuple[bool, str]:
    """Terminate a process by PID."""
    return system_controller.kill_process(pid)