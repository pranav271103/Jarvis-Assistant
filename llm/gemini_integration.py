import os
import google.generativeai as genai
from typing import Dict, List, Optional, Union
import logging
from pathlib import Path
import json
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

class GeminiChat:
    def __init__(self, api_key: str = None):
        """Initialize the Gemini chat model."""
        self.api_key = api_key or Config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest",
            generation_config=Config.GENERATION_CONFIG,
            safety_settings=Config.SAFETY_SETTINGS
        )
        self.chat = self.model.start_chat(history=[])
        self.conversation_history = []
        
    def generate_response(self, prompt: str, context: str = None) -> str:
        """Generate a response using the Gemini model."""
        try:
            # Add context if provided
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            # Generate response
            response = self.chat.send_message(
                full_prompt,
                generation_config=Config.GENERATION_CONFIG,
                safety_settings=Config.SAFETY_SETTINGS
            )
            
            # Update conversation history
            self._update_conversation_history(
                user_message=prompt,
                ai_response=response.text,
                context=context
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error processing your request."
    
    def _update_conversation_history(self, user_message: str, ai_response: str, context: str = None):
        """Update the conversation history with the latest exchange."""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'context': context
        })
        self._save_conversation_history()
    
    def _save_conversation_history(self):
        """Save the conversation history to a JSON file."""
        try:
            history_file = Path("conversation_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
    
    def load_conversation_history(self, filepath: str = None):
        """Load conversation history from a JSON file."""
        try:
            history_file = Path(filepath or "conversation_history.json")
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.conversation_history = json.load(f)
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            return False
    
    def clear_conversation(self):
        """Clear the current conversation history."""
        self.conversation_history = []
        self.chat = self.model.start_chat(history=[])

# Initialize the chat instance
chat_instance = GeminiChat()

def get_chat_response(prompt: str, context: str = None) -> str:
    """Get a response from the Gemini chat model."""
    return chat_instance.generate_response(prompt, context)

def clear_chat_history():
    """Clear the chat history."""
    chat_instance.clear_conversation()
