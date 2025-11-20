"""
Jarvis AI Assistant

A voice-controlled AI assistant powered by Gemini 1.5 Pro
"""

import os
import sys
import logging
import argparse
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.absolute()))

# Import local modules
from config import Config
from utils.speech_utils import speak, listen
from commands.command_handler_new import command_handler

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
        """Initialize the Jarvis assistant."""
        self.text_mode = text_mode
        self.running = True
        self.voice_enabled = not text_mode
        
        # Set voice mode in command handler
        if command_handler:
            command_handler.voice_enabled = self.voice_enabled
    
    def say(self, message: str, important: bool = False):
        """Speak a message if voice is enabled."""
        print(f"Jarvis: {message}")
        if self.voice_enabled or important:
            speak(message)
    
    def get_user_input(self) -> str:
        """Get input from the user."""
        if self.text_mode:
            return input("\nYou: ").strip()
        else:
            max_attempts = 3
            attempts = 0
            
            while attempts < max_attempts:
                try:
                    print("\nListening... (say 'exit' to quit or 'help' for commands)")
                    user_input = listen()
                    
                    if user_input is None or user_input.strip() == '':
                        print("I didn't catch that. Please try again.")
                        attempts += 1
                        continue
                    
                    print(f"You: {user_input}")
                    return user_input
                    
                except Exception as e:
                    logger.error(f"Error getting user input: {e}")
                    print("I'm having trouble with the microphone. Please check your audio settings.")
                    attempts += 1
            
            # If we get here, all attempts failed
            if not self.text_mode:
                print("Switching to text input mode due to audio issues...")
                self.text_mode = True
                return self.get_user_input()
            
            return ""
    
    def process_command(self, command: str) -> bool:
        """Process a single command."""
        try:
            # Handle empty or None command
            if not command or not isinstance(command, str) or not command.strip():
                if not self.text_mode:
                    self.say("I didn't catch that. Please try again.")
                return True
            
            # Clean up the command
            command = command.strip()
            
            # Exit condition
            if command.lower() in ['exit', 'quit', 'goodbye']:
                self.say("Goodbye! Have a great day!")
                return False
            
            # Process the command using the full input
            if not command_handler:
                self.say("Command handler is not available.", important=True)
                return True
            
            response = command_handler.handle_command(command)
            
            # Handle the response
            if response:
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
    
    def run(self):
        """Run the main interaction loop."""
        welcome_message = "Hello! I'm Jarvis, your AI assistant. How can I help you today?"
        self.say(welcome_message, important=True)
        
        try:
            while self.running:
                try:
                    user_input = self.get_user_input()
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
    parser = argparse.ArgumentParser(description='Jarvis AI Assistant')
    parser.add_argument('--text', action='store_true', help='Run in text-only mode')
    parser.add_argument('--voice-off', action='store_true', help='Disable voice output')
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