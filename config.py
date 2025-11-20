"""
Configuration file for Jarvis AI Assistant
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for Jarvis Assistant."""
    
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Gemini Model Configuration
    GENERATION_CONFIG = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }
    
    # Safety Settings
    SAFETY_SETTINGS = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
    
    # Speech Recognition Settings
    SPEECH_RECOGNITION_CONFIG = {
        "energy_threshold": 300,
        "pause_threshold": 0.8,
        "dynamic_energy_threshold": True,
        "timeout": 5,
        "phrase_time_limit": 10
    }
    
    # Text-to-Speech Settings
    TTS_CONFIG = {
        "voice_id": 0,
        "rate": 180,
        "volume": 1.0
    }
    
    # Live Chat Settings
    LIVE_CHAT_CONFIG = {
        "max_empty_responses": 2,
        "listening_timeout": 10,
        "conversation_history_limit": 50,
        "enable_streaming": True
    }
    
    # Logging Configuration
    LOG_CONFIG = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "jarvis.log"
    }