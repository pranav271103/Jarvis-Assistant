"""
Test suite for Jarvis AI Assistant
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

# Import modules to test
from utils.speech_utils import SpeechRecognizer, SpeechSynthesizer
from llm.gemini_integration import GeminiChat
from commands.command_handler import CommandHandler

class TestSpeechUtils(unittest.TestCase):
    """Test cases for speech utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.recognizer = SpeechRecognizer()
        self.synthesizer = SpeechSynthesizer()
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_listen_success(self, mock_mic, mock_recognizer):
        """Test successful speech recognition."""
        # Mock the recognizer and microphone
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.return_value = "test text"
        
        # Create a mock context manager for the microphone
        mock_mic.return_value.__enter__.return_value = 'audio_source'
        
        recognizer = SpeechRecognizer()
        result = recognizer.listen()
        self.assertEqual(result, "test text")
    
    def test_synthesizer_initialization(self):
        """Test speech synthesizer initialization."""
        self.assertIsNotNone(self.synthesizer.engine)
        self.assertEqual(self.synthesizer.engine.getProperty('rate'), 180)

class TestGeminiIntegration(unittest.TestCase):
    """Test cases for Gemini LLM integration."""
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_chat(self, mock_model, mock_configure):
        """Test Gemini chat initialization and response generation."""
        # Mock the model response
        mock_chat = MagicMock()
        mock_model.return_value.start_chat.return_value = mock_chat
        
        # Mock the response object with a text attribute
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_chat.send_message.return_value = mock_response
        
        # Test initialization and response
        chat = GeminiChat(api_key="test_key")
        response = chat.generate_response("Test prompt")
        
        # Verify the response
        self.assertEqual(response, "Test response")
        mock_chat.send_message.assert_called_once()
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_chat_error_handling(self, mock_model, mock_configure):
        """Test Gemini chat error handling."""
        # Mock an API error
        mock_chat = MagicMock()
        mock_model.return_value.start_chat.return_value = mock_chat
        mock_chat.send_message.side_effect = Exception("API Error")
        
        # Test error handling
        chat = GeminiChat(api_key="test_key")
        response = chat.generate_response("Test prompt")
        
        # Verify error message is returned
        self.assertIn("I apologize, but I encountered an error", response)

class TestCommandHandler(unittest.TestCase):
    """Test cases for command handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = CommandHandler()
    
    @patch('commands.command_handler.datetime.datetime')
    def test_time_command(self, mock_datetime):
        """Test time command handling."""
        # Create a mock datetime object
        mock_now = MagicMock()
        mock_now.strftime.return_value = "12:00 PM"
        mock_datetime.now.return_value = mock_now
        
        # Call the method directly
        response = self.handler._get_current_time()
        
        # Verify the response contains the expected time
        self.assertEqual(response, "The current time is 12:00 PM")
        
        # Verify the mock was called with the correct format
        mock_now.strftime.assert_called_once_with("%I:%M %p")
    
    @patch('commands.command_handler.get_chat_response')
    def test_unknown_command(self, mock_chat):
        """Test handling of unknown commands."""
        # Mock the chat response
        mock_chat.return_value = "I'm not sure how to help with that."
        
        response = self.handler.handle_command("some unknown command")
        self.assertEqual(response, "I'm not sure how to help with that.")

if __name__ == '__main__':
    unittest.main()
