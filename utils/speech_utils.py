import pyttsx3
import speech_recognition as sr
from typing import Optional
import logging
from pathlib import Path
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    def __init__(self, energy_threshold=300, pause_threshold=0.8, dynamic_energy_threshold=True):
        """Initialize the speech recognizer with custom settings."""
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy_threshold
    
    def listen(self) -> Optional[str]:
        """Listen to microphone input and return recognized text."""
        with sr.Microphone() as source:
            logger.info("Listening...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Recognized: {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                logger.warning("Listening timed out")
                return None
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Could not request results; {e}")
                return None
            except Exception as e:
                logger.error(f"Error in speech recognition: {e}")
                return None


class SpeechSynthesizer:
    def __init__(self, voice_id=0, rate=180, volume=1.0):
        """Initialize the text-to-speech engine."""
        self.engine = pyttsx3.init()
        self.set_voice(voice_id)
        self.set_rate(rate)
        self.set_volume(volume)
    
    def set_voice(self, voice_id=0):
        """Set the voice for text-to-speech."""
        voices = self.engine.getProperty('voices')
        if voice_id < len(voices):
            self.engine.setProperty('voice', voices[voice_id].id)
    
    def set_rate(self, rate):
        """Set the speech rate."""
        self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume):
        """Set the volume level (0.0 to 1.0)."""
        self.engine.setProperty('volume', volume)
    
    def speak(self, text: str, save_audio: bool = False) -> None:
        """Convert text to speech and optionally save to file."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            
            if save_audio:
                self._save_audio(text)
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
    
    def _save_audio(self, text: str) -> str:
        """Save the speech output to a WAV file."""
        try:
            # Create output directory if it doesn't exist
            output_dir = Path("output/audio")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"speech_{timestamp}.wav"
            
            # Save to file
            self.engine.save_to_file(text, str(filename))
            self.engine.runAndWait()
            
            logger.info(f"Saved speech to {filename}")
            return str(filename)
        except Exception as e:
            logger.error(f"Failed to save speech: {e}")
            return ""


# Initialize speech components
recognizer = SpeechRecognizer()
synthesizer = SpeechSynthesizer()


def speak(text: str, save_audio: bool = False) -> None:
    """Speak the given text."""
    synthesizer.speak(text, save_audio)


def listen() -> Optional[str]:
    """Listen for speech input and return recognized text."""
    return recognizer.listen()