# Jarvis AI Assistant

A powerful voice and text-controlled AI assistant with system control capabilities. Built with Python and Google's Gemini 1.5 Flash model, Jarvis helps you be more productive by automating tasks through natural language commands.

## Key Features

### System Control
- Power Management: Shutdown, restart, sleep, hibernate, or lock your computer
- Process Control: View and manage running applications and processes
- System Monitoring: Check CPU, memory, and disk usage in real-time
- Application Control: Launch applications and websites with voice commands
- User Session Management: Lock screen or log out users

### Productivity Tools
- Web Search: Get instant web search results
- Email Integration: Compose and send emails (basic implementation)
- Time and Date: Get current time, date, and set reminders
- File Operations: Basic file system interactions
- Clipboard Management: Copy and paste text programmatically

### Voice and Text Interface
- Natural language processing for intuitive commands
- Voice recognition with speech-to-text conversion
- Text-to-speech responses with adjustable settings
- Multi-language support (depends on system configuration)
- Background listening mode for always-on assistance

### Customization and Extensibility
- Modular command system for easy expansion
- Custom command aliases and shortcuts
- Configurable hotkeys and triggers
- Plugin architecture for additional features
- Cross-platform compatibility (Windows, macOS, Linux)

## Prerequisites

- Python 3.8 or higher
- Internet connection (for web search and AI features)
- Google Gemini API key (get one from Google AI Studio)
- Microphone (for voice input)
- Speakers or headphones (for voice output)
- 500MB free disk space
- 4GB RAM minimum (8GB recommended)

## Installation Guide

1. Clone the repository:
   ```bash
   git clone https://github.com/pranav271103/Jarvis-Assistant.git
   cd Jarvis-Assistant
   ```

2. Set up a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

## Getting Started

### Basic Usage

Start Jarvis in voice mode:
```bash
python main.py
```

Start in text-only mode:
```bash
python main.py --text
```

Disable voice output (useful for quiet environments):
```bash
python main.py --voice-off
```

## Complete Command Reference

### System Commands
- `system [action]` - Control system power states (shutdown, restart, etc.)
- `processes` - List all running processes with PIDs
- `kill [pid]` - Terminate a process by its ID
- `system_info` - Display detailed system information
- `cpu_usage` - Show current CPU usage
- `memory_usage` - Display memory usage statistics
- `disk_space` - Check available disk space
- `network_info` - Show network configuration
- `battery_status` - Check battery level (laptops)
- `screenshot` - Take a screenshot

### File Operations
- `open [file/folder]` - Open files or folders
- `search_files [query]` - Search for files
- `create_file [name]` - Create a new file
- `create_folder [name]` - Create a new directory
- `delete [path]` - Delete files or folders
- `copy [src] [dest]` - Copy files
- `move [src] [dest]` - Move or rename files

### Web and Applications
- `search [query]` - Web search
- `open [app/website]` - Launch applications or websites
- `email [recipient] [subject] [message]` - Send emails
- `browse [url]` - Open a specific URL
- `download [url]` - Download files from the web

### Productivity
- `time` - Current time
- `date` - Today's date
- `calendar` - Show calendar
- `set_timer [minutes]` - Set a countdown timer
- `stopwatch` - Start/stop a stopwatch
- `remind [time] [message]` - Set reminders
- `note [text]` - Take quick notes
- `todo [add/remove/list]` - Manage to-do list

### Voice and Settings
- `voice [on/off]` - Toggle voice responses
- `listen` - Start listening for commands
- `stop listening` - Stop listening
- `configure` - Change settings
- `update` - Check for updates
- `help` - Show command reference

## Voice Command Examples

### System Control
- "Lock my computer"
- "Put the system to sleep"
- "Show me running processes"
- "What's my CPU usage?"
- "Take a screenshot"

### Productivity
- "Open Visual Studio Code"
- "Search for Python tutorials"
- "Set a timer for 25 minutes"
- "Create a new file called notes.txt"
- "Remind me to call John at 3 PM"

### Information
- "What time is it?"
- "What's today's date?"
- "How much disk space do I have left?"
- "What's my IP address?"
- "Show system information"

## Project Structure

```
Jarvis-Assistant/
├── .env                    # Environment variables
├── .gitignore             # Git ignore file
├── README.md              # This file
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── main.py                # Main application entry point
├── commands/              # Command handlers
│   └── command_handler.py
│
├── llm/                   # LLM integration
│   └── gemini_integration.py
│
├── utils/                 # Utility functions
│   ├── speech_utils.py    # Voice I/O
│   ├── system_utils.py    # System operations
│   └── file_utils.py      # File management
└── tests/                 # Test suite
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Gemini for the powerful language model
- PyAudio and SpeechRecognition for voice processing
- All open-source contributors

---

