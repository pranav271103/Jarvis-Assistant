import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Speech settings
    VOICE_ID = 0  # 0 for male, 1 for female voice
    SPEECH_RATE = 180  # Words per minute
    
    # Application settings
    APP_NAME = "Jarvis AI Assistant"
    VERSION = "2.0.0"
    
    # Paths
    LOG_DIR = "logs"
    CACHE_DIR = ".cache"
    
    # LLM Settings
    GENERATION_CONFIG = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }
    
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
        },
    ]

# Create necessary directories
os.makedirs(Config.LOG_DIR, exist_ok=True)
os.makedirs(Config.CACHE_DIR, exist_ok=True)
