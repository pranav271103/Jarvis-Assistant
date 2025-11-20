#!/usr/bin/env python3
"""
Jarvis AI Assistant - Live Voice Chat Edition

A voice-controlled AI assistant with continuous conversation mode
"""

import os
import sys
import logging
import argparse
import time
import threading
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.absolute()))

# Import local modules
from config import Config
from utils.speech_utils import speak, listen, SpeechSynthesizer, SpeechRecognizer
from commands.command_handler_new import command_handler
from llm.gemini_integration import chat_instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class JarvisAssistant:
    def __init__(self, text_mode=False):
        """Initialize the Jarvis assistant with live chat capabilities."""
        self.text_mode = text_mode
        self.running = True
        self.voice_enabled = not text_mode
        self.live_chat_mode = False
        self.continuous_listening = False
        
        # Initialize speech components
        self.speech_synthesizer = SpeechSynthesizer()
        self.speech_recognizer = SpeechRecognizer()
        
        # Set voice mode in command handler
        if command_handler:
            command_handler.voice_enabled = self.voice_enabled
            command_handler.llm_chat = chat_instance
    
    def say(self, message: str, important: bool = False, interrupt: bool = False):
        """Speak a message if voice is enabled."""
        print(f"Jarvis: {message}")
        if self.voice_enabled or important:
            speak(message)
    
    def get_user_input(self, timeout: int = None) -> str:
        """Get input from the user with optional timeout."""
        if self.text_mode:
            return input("\nYou: ").strip()
        else:
            try:
                if timeout:
                    print(f"\nListening... (timeout: {timeout}s)")
                else:
                    print("\nListening...")
                
                user_input = listen()
                
                if user_input is None or user_input.strip() == '':
                    return None
                
                print(f"You: {user_input}")
                return user_input
                
            except Exception as e:
                logger.error(f"Error getting user input: {e}")
                return None
    
    def check_for_command_keywords(self, text: str) -> tuple:
        """Check if text contains command keywords and extract them."""
        if not text:
            return False, None
        
        text_lower = text.lower()
        
        # Command keywords that indicate user wants to execute something
        command_keywords = [
            'open', 'launch', 'start', 'search', 'find', 'look up',
            'shutdown', 'restart', 'sleep', 'lock', 'hibernate',
            'what time', 'what date', 'system info', 'processes'
        ]
        
        for keyword in command_keywords:
            if keyword in text_lower:
                return True, text
        
        # Mode switch keywords
        if any(phrase in text_lower for phrase in ['exit chat', 'stop chatting', 'command mode']):
            return True, 'exit_live_chat'
        
        if any(phrase in text_lower for phrase in ['live chat', 'talk to me', 'conversation mode', "let's chat"]):
            return True, 'enter_live_chat'
        
        return False, None
    
    def live_chat_mode_handler(self):
        """Handle continuous live chat conversation mode."""
        self.live_chat_mode = True
        self.say("I'm now in live chat mode! Feel free to talk with me about anything. Say 'exit chat' to return to command mode.", important=True)
        
        consecutive_empty = 0
        max_empty = 2
        
        while self.live_chat_mode and self.running:
            try:
                # Listen for user input
                user_input = self.get_user_input(timeout=10)
                
                if user_input is None or user_input.strip() == '':
                    consecutive_empty += 1
                    if consecutive_empty >= max_empty:
                        self.say("I haven't heard from you in a while. Say something or I'll return to command mode.")
                        user_input = self.get_user_input(timeout=10)
                        if not user_input:
                            self.say("Returning to command mode.")
                            self.live_chat_mode = False
                            break
                    continue
                
                consecutive_empty = 0
                
                # Check if user wants to exit live chat
                if any(phrase in user_input.lower() for phrase in ['exit chat', 'stop chatting', 'command mode', 'goodbye', 'bye']):
                    self.say("Exiting live chat mode. I'm back to command mode now.")
                    self.live_chat_mode = False
                    break
                
                # Check if it's a command
                is_command, command_text = self.check_for_command_keywords(user_input)
                
                if is_command and command_text != user_input:
                    # Execute command
                    response = command_handler.handle_command(command_text)
                    self.say(response)
                else:
                    # Generate conversational response
                    try:
                        response = chat_instance.generate_response(
                            user_input, 
                            context="Live chat conversation",
                            mode="live_chat"
                        )
                        self.say(response)
                    except Exception as e:
                        logger.error(f"Error in live chat: {e}")
                        self.say("I'm having trouble processing that. Could you try again?")
                
            except KeyboardInterrupt:
                self.say("Exiting live chat mode.")
                self.live_chat_mode = False
                break
            except Exception as e:
                logger.error(f"Error in live chat mode: {e}")
                self.say("I encountered an error. Let's continue chatting.")
        
        self.live_chat_mode = False
    
    def process_command(self, command: str) -> bool:
        """Process a single command."""
        try:
            # Handle empty or None command
            if not command or not isinstance(command, str) or not command.strip():
                return True
            
            # Clean up the command
            command = command.strip()
            
            # Exit condition
            if command.lower() in ['exit', 'quit', 'goodbye']:
                self.say("Goodbye! Have a great day!")
                return False
            
            # Check for live chat mode activation
            command_lower = command.lower()
            if any(phrase in command_lower for phrase in ['live chat', 'talk to me', 'conversation mode', "let's chat", 'chat with me', "i'm bored"]):
                self.live_chat_mode_handler()
                return True
            
            # Check if it's a question/conversation vs command
            conversation_indicators = ['what', 'why', 'how', 'tell me', 'explain', 'who', 'when', 'where']
            is_question = any(command_lower.startswith(word) for word in conversation_indicators)
            
            # Check for command keywords
            is_command, _ = self.check_for_command_keywords(command)
            
            if is_command:
                # Execute as command
                response = command_handler.handle_command(command)
                self.say(response)
            elif is_question or len(command.split()) > 5:
                # Treat as conversational query
                try:
                    response = chat_instance.generate_response(
                        command,
                        context="Single query response",
                        mode="normal"
                    )
                    self.say(response)
                except Exception as e:
                    logger.error(f"Error generating response: {e}")
                    # Fallback to command handler
                    response = command_handler.handle_command(command)
                    self.say(response)
            else:
                # Try command first, fallback to conversation
                response = command_handler.handle_command(command)
                self.say(response)
            
            return True
            
        except KeyboardInterrupt:
            self.say("Goodbye!")
            return False
        except Exception as e:
            error_msg = f"I'm sorry, I encountered an error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.say("I'm sorry, I encountered an error. Please try again.", important=True)
            return True
    
    def show_help(self):
        """Show help information about live chat features."""
        help_text = """
Jarvis Assistant - Live Voice Chat

MODES:
1. Command Mode (default): Execute specific commands
2. Live Chat Mode: Have continuous conversations

ACTIVATING LIVE CHAT:
Say: "live chat", "talk to me", "let's chat", or "I'm bored"

IN LIVE CHAT MODE:
- Just talk naturally about anything
- I'll remember the conversation context
- I can still execute commands when you ask
- Say "exit chat" to return to command mode

EXAMPLE USAGE:
You: "I'm bored"
Jarvis: "I'm now in live chat mode! What would you like to talk about?"
You: "Tell me about space"
Jarvis: [Provides information about space]
You: "Open YouTube"
Jarvis: [Opens YouTube while staying in chat mode]
You: "Exit chat"
Jarvis: "Exiting live chat mode."

TIPS:
- Live chat is great for casual conversations
- I remember context during the chat session
- Command mode is faster for specific tasks
- You can switch between modes anytime
"""
        print(help_text)
        if self.voice_enabled:
            self.say("I've displayed the help information. Live chat mode lets us have continuous conversations. Just say 'live chat' to start!")
    
    def run(self):
        """Run the main interaction loop."""
        welcome_message = "Hello! I'm Jarvis, your AI assistant. I can execute commands and chat with you. Say 'live chat' for conversation mode, or give me a command. Say 'help' for more information."
        self.say(welcome_message, important=True)
        
        try:
            while self.running:
                try:
                    user_input = self.get_user_input()
                    
                    if user_input and 'help' in user_input.lower() and 'live' in user_input.lower():
                        self.show_help()
                        continue
                    
                    self.running = self.process_command(user_input)
                    
                except KeyboardInterrupt:
                    self.say("Goodbye!")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error: {e}", exc_info=True)
                    self.say("An unexpected error occurred. Please try again.", important=True)
                    time.sleep(1)
                    
        except Exception as e:
            logger.critical(f"Critical error: {e}", exc_info=True)
            self.say("A critical error occurred. Please restart the application.", important=True)
            return False
        
        return True


def main():
    """Main function to run the Jarvis assistant."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Jarvis AI Assistant - Live Voice Chat')
    parser.add_argument('--text', action='store_true', help='Run in text-only mode')
    parser.add_argument('--voice-off', action='store_true', help='Disable voice output')
    parser.add_argument('--live', action='store_true', help='Start directly in live chat mode')
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.getenv('GEMINI_API_KEY'):
        logger.error("GEMINI_API_KEY not found in environment variables.")
        print("Error: GEMINI_API_KEY environment variable is required.")
        print("Please create a .env file with your Gemini API key.")
        print("Example: GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Initialize and run the assistant
    assistant = JarvisAssistant(text_mode=args.text)
    
    if args.voice_off:
        assistant.voice_enabled = False
        if command_handler:
            command_handler.voice_enabled = False
    
    try:
        if args.live:
            print("Starting in live chat mode...")
            assistant.live_chat_mode_handler()
        
        success = assistant.run()
        if not success:
            logger.error("Assistant encountered an error during execution")
            return 1
        return 0
        
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        error_msg = f"A fatal error occurred: {e}"
        print(f"\n{error_msg}")
        try:
            speak("I'm sorry, I encountered a critical error and need to shut down.")
        except:
            pass
        return 1
    finally:
        logger.info("Jarvis has been shut down.")
        print("\nGoodbye!")


if __name__ == "__main__":
    sys.exit(main())