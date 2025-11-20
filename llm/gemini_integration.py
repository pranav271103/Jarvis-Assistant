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
        """Initialize the Gemini chat model with system awareness."""
        self.api_key = api_key or Config.GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # System context for awareness
        self.system_context = self._build_system_context()
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-live-001",
            generation_config=Config.GENERATION_CONFIG,
            safety_settings=Config.SAFETY_SETTINGS,
            system_instruction=self.system_context
        )
        
        self.chat = self.model.start_chat(history=[])
        self.conversation_history = []
        self.conversation_mode = "normal"  # normal, live_chat, command
    
    def _build_system_context(self) -> str:
        """Build comprehensive system context for Gemini awareness."""
        return """You are Jarvis, an intelligent AI voice assistant with full system control capabilities.

CORE IDENTITY:
- You are a helpful, friendly, and proactive assistant
- You can control the computer, search the web, and have natural conversations
- You remember context from previous messages in the conversation
- You provide concise but informative responses suitable for voice output

YOUR CAPABILITIES:
1. SYSTEM CONTROL:
   - Shutdown, restart, sleep, lock, hibernate the computer
   - List and manage running processes
   - Get system information (CPU, memory, disk usage)
   
2. WEB & APPLICATIONS:
   - Search the web for any topic
   - Open websites (YouTube, Google, GitHub, etc.)
   - Launch system applications (Notepad, Calculator, etc.)
   
3. TIME & DATE:
   - Tell current time and date
   - Help with time-based queries
   
4. CONVERSATION:
   - Answer questions naturally
   - Have casual conversations
   - Remember conversation context
   - Provide helpful information

INTERACTION STYLE:
- Keep responses conversational and natural for voice
- Be concise but informative
- Ask clarifying questions when needed
- Suggest relevant actions proactively
- Use friendly, professional tone

COMMAND EXECUTION:
When users ask you to perform actions, you should:
- Acknowledge the request naturally
- Confirm what you're about to do
- Execute through the command system
- Report the result clearly

Example interactions:
User: "I'm bored"
You: "I understand! Would you like me to suggest some interesting websites to visit, play some music on YouTube, or we could just chat about something you find interesting. What sounds good?"

User: "What can you do?"
You: "I can help you in many ways! I can search the web, open applications, control your computer (shutdown, restart, etc.), tell you the time and date, answer questions, and just chat with you. What would you like help with?"

User: "Shut down my computer"
You: "Sure, I'll shut down your computer now. Goodbye!"

Remember: Be helpful, conversational, and proactive in your assistance."""

    def generate_response(self, prompt: str, context: str = None, mode: str = "normal") -> str:
        """Generate a response using the Gemini model with system awareness."""
        try:
            self.conversation_mode = mode
            
            # Build enhanced prompt with context
            full_prompt = self._build_prompt(prompt, context, mode)
            
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
                context=context,
                mode=mode
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error processing your request. Could you try rephrasing that?"
    
    def _build_prompt(self, prompt: str, context: str = None, mode: str = "normal") -> str:
        """Build an enhanced prompt with context and mode awareness."""
        prompt_parts = []
        
        # Add conversation mode context
        if mode == "live_chat":
            prompt_parts.append("[LIVE CHAT MODE - User is having a casual conversation]")
        elif mode == "command":
            prompt_parts.append("[COMMAND MODE - User wants to execute a specific action]")
        
        # Add provided context
        if context:
            prompt_parts.append(f"Context: {context}")
        
        # Add user prompt
        prompt_parts.append(f"User: {prompt}")
        
        return "\n".join(prompt_parts)
    
    def generate_streaming_response(self, prompt: str, context: str = None):
        """Generate a streaming response for live chat mode."""
        try:
            full_prompt = self._build_prompt(prompt, context, "live_chat")
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=Config.GENERATION_CONFIG,
                safety_settings=Config.SAFETY_SETTINGS,
                stream=True
            )
            
            full_text = ""
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    yield chunk.text
            
            # Update history after streaming completes
            self._update_conversation_history(
                user_message=prompt,
                ai_response=full_text,
                context=context,
                mode="live_chat"
            )
            
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield "I'm having trouble processing that. Could you try again?"
    
    def _update_conversation_history(self, user_message: str, ai_response: str, 
                                    context: str = None, mode: str = "normal"):
        """Update the conversation history with the latest exchange."""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'context': context,
            'mode': mode
        })
        
        # Keep only last 50 messages to prevent memory issues
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
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
    
    def get_conversation_summary(self) -> str:
        """Get a summary of recent conversation."""
        if not self.conversation_history:
            return "No conversation history yet."
        
        recent = self.conversation_history[-5:]
        summary = "Recent conversation:\n"
        for entry in recent:
            summary += f"You: {entry['user_message'][:50]}...\n"
            summary += f"Jarvis: {entry['ai_response'][:50]}...\n\n"
        
        return summary


# Initialize the chat instance
chat_instance = GeminiChat()


def get_chat_response(prompt: str, context: str = None, mode: str = "normal") -> str:
    """Get a response from the Gemini chat model."""
    return chat_instance.generate_response(prompt, context, mode)


def get_streaming_response(prompt: str, context: str = None):
    """Get a streaming response for live chat."""
    return chat_instance.generate_streaming_response(prompt, context)


def clear_chat_history():
    """Clear the chat history."""
    chat_instance.clear_conversation()


def get_conversation_summary() -> str:
    """Get conversation summary."""
    return chat_instance.get_conversation_summary()