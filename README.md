# AstraVoice AI Assistant ⚡

AstraVoice AI Assistant is a professional, high-performance desktop assistant built with Python. Featuring a futuristic **Jarvis-inspired HUD interface** styled in carbon and neon accents, AstraVoice integrates voice control, speech synthesis, weather diagnostics, news feeds, reminder schedulers, and local application routing inside a multi-threaded asynchronous CustomTkinter core.

Developed to showcase robust, secure, and production-ready Python engineering patterns.

---

## Core Features

- **Reactor Core Voice Visualizer**: Responsive CustomTkinter canvas drawing an animated Arc Reactor with a radar sweeper scanline. Renders a dynamic, real-time waveform visualizer while recording.
- **Asynchronous Multithreaded Core**: Employs non-blocking threading queues for microphone speech capture and text-to-speech rendering, preventing GUI freezes.
- **HUD Log Console**: Real-time diagnostic logging handler piped directly into the dashboard interface to capture service events as they occur.
- **Robust Speech Pipeline**: Ambient noise calibration, dynamic energy threshold adjustments, and an intelligent retry mechanism.
- **Integrations**:
  - **Weather Monitor**: Live OpenWeatherMap API updates (with graceful simulated mock database fallbacks).
  - **Telemetry Headlines**: Live NewsAPI top headlines parsed with structural data models.
  - **Cron Alert System**: Thread-safe reminders database scheduler with daemon-checking threads.
  - **Secure System Launcher**: Secure local application launcher executing protocols without vulnerable shell execution commands.

---

## 🔒 Security Hardening Design

AstraVoice has been audited and secured against common local and API vulnerabilities:
1. **Subprocess Injection Defense**: Avoids `shell=True` subprocess spawning. Local programs are opened via Windows-native `os.startfile` protocol resolvers.
2. **Log Privacy Redactions**: Diagnostic stdout logger files redact raw transcribed speech commands and reminder text fields. Logs record transaction metadata (lengths, word counts, and event flags) instead.
3. **API Key Leak Prevention**: Exception logs automatically scrub credentials and print sanitized string metrics instead of requests details that echo token parameters.
4. **Input Sanitization**: Strictly sanitizes city names, categories, command text, and reminders to block command injection patterns and database buffer bloat.
5. **UTF-8 Encoding Checks**: All file operations explicitly enforce UTF-8 reading and writing to prevent platform-dependent encoding crashes.

---

## 🛠️ Technology Stack

- **GUI System**: [CustomTkinter](https://customtkinter.tomburnell.dev/) (Tkinter wrapping styling wrapper)
- **Audio Capture**: [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/)
- **Speech recognition**: [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) (leveraging Google Web Speech APIs)
- **Text-to-Speech**: [pyttsx3](https://pypi.org/project/pyttsx3/) (offline Speech engine)
- **APIs & Transport**: [Requests](https://requests.readthedocs.io/) (with HTTP TLS transports)
- **Settings Loader**: [python-dotenv](https://github.com/theofidry/django-dotenv)

---

## 📂 Project Structure

```
AstraVoice AI Assistant/
│
├── app.py                 # CLI Core Entrypoint & Command Intent Routing
├── dashboard.py           # GUI Core Entrypoint (Splash screen & Main HUD)
├── config.py              # Configuration Loader & Logger Initializer
├── requirements.txt       # Project Dependencies
│
├── services/
│   ├── models.py          # Type-Safe Data Models (Dataclasses)
│   ├── app_launcher.py    # Windows Process Spawner (os.startfile)
│   ├── history_service.py # Command Log DB Management (JSON)
│   ├── news_service.py    # News Headlines Fetcher
│   ├── reminder_service.py# Reminder Daemon & Scheduler
│   ├── speech_service.py  # Microphone STT Pipeline
│   ├── tts_service.py     # Voice Synthesis Engine
│   └── weather_service.py # Meteorological Data Fetcher
│
├── ui/
│   ├── components.py      # Custom Widgets, Arc Reactor Canvas, Panels
│   └── theme.py           # Futuristic HSL Hex Color Palettes
│
└── memory/
    ├── command_history.json
    └── reminders.json
```

---

## 💻 Setup & Installation

### Prerequisites
* Python 3.10 or higher.
* PyAudio requires C++ build tools or precompiled wheels on some Windows installations.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AstraVoice.git
   cd AstraVoice
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables: Create a `.env` file in the root directory:
   ```env
   OPENWEATHER_API_KEY=your_openweathermap_api_key_here
   NEWS_API_KEY=your_newsapi_key_here
   DEFAULT_CITY=Mumbai
   ```

### Execution
* **Launch GUI Dashboard**:
  ```bash
  python dashboard.py
  ```
* **Launch CLI Interface**:
  ```bash
  python app.py
  ```
