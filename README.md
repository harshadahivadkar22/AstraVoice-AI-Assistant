# AstraVoice AI Assistant ⚡

![AstraVoice AI Assistant Banner](assets/banner.png)

AstraVoice AI Assistant is a professional, high-performance desktop assistant built with Python. Featuring a futuristic **Jarvis-inspired HUD interface** styled in carbon-dark and neon accents, AstraVoice integrates voice control, speech synthesis, weather diagnostics, news feeds, reminder schedulers, and local application routing inside a multi-threaded asynchronous CustomTkinter core.

This project was engineered to demonstrate clean code, thread-safe asynchronous architectures, robust error handling, and cybersecurity hardening standards suitable for public portfolios and developer showcases.

---

## 🚀 Key Features

*   **Reactor Core Visualizer (Jarvis HUD)**
    *   Responsive CustomTkinter canvas drawing an animated, rotating Arc Reactor with a radar scanline.
    *   Features a real-time, triple-oscilloscope voice waveform visualization that shifts colors and frequencies dynamically based on assistant states (`Listening`, `Processing`, `Speaking`, `Idle`, `Error`).
*   **Asynchronous Multi-threaded Core**
    *   Employs non-blocking threading queues for microphone speech capture and text-to-speech rendering, preventing GUI freezes and keeping the frame rate smooth.
*   **Real-time HUD Diagnostics Log Console**
    *   A custom `HUDLogHandler` redirects standard logging streams directly into the dashboard interface logstream text box in real-time, allowing users to watch diagnostic logs scroll during execution.
*   **Robust Audio & Speech recognition Pipeline**
    *   Automatic ambient noise calibration (0.8s on initial launch, 1.2s on retries) allows PyAudio to calibrate accurately to room acoustics.
    *   Includes dynamic energy thresholds and automatic try-catch retry mechanisms to eliminate cut-offs and transcript failures.
*   **Telemetry Dashboard Widgets**
    *   **Weather Monitor**: Fetches real-time weather coordinates using the OpenWeatherMap API. Shows a neon `WEATHER API // LIVE` (neon green) or `WEATHER API // MOCKED` (neon yellow) status badge depending on API configuration.
    *   **News Headlines**: Retrieves top stories using NewsAPI and parses headlines cleanly into scrollable components using structured dataclass models.
    *   **Cron Alert System**: Schedules, stores, and triggers background reminder alerts using a thread-safe local JSON database and background daemon checking loop.
    *   **Secure System Launcher**: Launches local apps (Chrome, Notepad, Calculator) securely using Windows-native shell associations instead of insecure raw shell executions.

---

## 🔒 Security Hardening

AstraVoice has been audited and secured against common local and API vulnerabilities:
1.  **Process Injection Defense**: Avoids `shell=True` subprocess spawning. Local applications are opened via Windows-native `os.startfile` protocol resolvers, preventing shell-injection vectors.
2.  **Plaintext Logging Privacy Scrubbing**: The system log (`logs/astra_voice.log`) automatically redacts raw voice transcriptions and reminder details, saving non-sensitive transaction dimensions (word counts, string lengths) to the logs instead.
3.  **API Key Leak Prevention**: Exception logs automatically capture and replace OpenWeatherMap and NewsAPI key credentials with a generic `[REDACTED_API_KEY]` placeholder to prevent leakage in debug dumps.
4.  **Input Sanitization**: Strictly sanitizes city names, categories, command text, and reminders to block command injection patterns and database buffer bloat.
5.  **UTF-8 Encoding Checks**: All file operations explicitly enforce UTF-8 reading and writing to prevent platform-dependent encoding crashes.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **GUI Framework** | **CustomTkinter (v5.2.0+)** | Modern dark-themed styling wrapper built on top of Tkinter. |
| **Audio Capture** | **PyAudio (v0.2.14+)** | Direct binding to the system audio input interfaces. |
| **Speech recognition** | **SpeechRecognition (v3.10.0+)** | Handles Google Web Speech API transport pipelines. |
| **Speech Synthesis** | **pyttsx3 (v2.99+)** | Offline, low-latency text-to-speech engine. |
| **HTTP Transport** | **Requests** | Fetches meteorological and news feeds with active request timeouts. |
| **Configuration** | **python-dotenv** | Loads environment variables safely from external files. |
| **Data Models** | **Python Dataclasses** | Strongly typed, structural domain data models. |

---

## 📂 Folder Structure

```
AstraVoice AI Assistant/
│
├── app.py                 # CLI Core Entrypoint & Command Intent Routing
├── dashboard.py           # GUI Core Entrypoint (Splash screen & Main HUD)
├── config.py              # Configuration Loader & Logger Initializer
├── requirements.txt       # Project Dependencies
├── copy_asset.py          # Post-setup Asset Helper Script
├── .env                   # Local Environment Variables (Git ignored)
├── .gitignore             # Git Ignore Specifications
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
├── logs/                  # Log outputs directory (Git ignored)
│   └── astra_voice.log    # Sanitized transaction logs
│
└── memory/                # Persistent JSON databases (Git ignored)
    ├── command_history.json
    └── reminders.json
```

---

## 💻 Setup & Installation

### Prerequisites
*   Python 3.10 or higher installed.
*   A working microphone and speakers/headset connected.
*   On Windows, PyAudio may require C++ Build Tools or precompiled wheels.

### Installation Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/harshadahivadkar22/AstraVoice-AI-Assistant.git
    cd AstraVoice-AI-Assistant
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    python -m venv venv
    # Windows Command Prompt / PowerShell:
    venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a file named `.env` in the root directory:
    ```env
    # OpenWeatherMap API Key (Get one from https://openweathermap.org/)
    OPENWEATHER_API_KEY=your_openweathermap_api_key_here

    # NewsAPI Key (Get one from https://newsapi.org/)
    NEWS_API_KEY=your_newsapi_key_here

    # Default city for meteorological queries
    DEFAULT_CITY=Mumbai
    ```

5.  **Initialize Project Assets**
    Run the asset helper script to copy the visual banner to your assets directory:
    ```bash
    python copy_asset.py
    ```

---

## 🎮 Usage Instructions

### Starting the HUD Dashboard (GUI)
Launch the main dashboard to view the high-tech UI:
```bash
python dashboard.py
```
*   **Startup Loader**: Displays a holographic diagnostic splash screen while initializing speech and data connections.
*   **Voice Control**: Click the rotating **Arc Reactor Core** or press `Ctrl + Space` to start listening.
*   **Manual Control**: Use the **START LISTENING** and **STOP LISTENING** buttons to control voice captures.
*   **Minimizing**: The application automatically minimizes to the system tray (if dependencies are present) to run in the background.

### Starting the Assistant Console (CLI)
For a lightweight terminal-only session:
```bash
python app.py
```

### Supported Voice Commands
*   **Weather Details**: *"What is the weather in London?"* or *"Temperature in Tokyo"*.
*   **News Feeds**: *"Read the news"*, *"Headlines"*, or *"Technology headlines"*.
*   **Reminders**: *"Remind me in 5 minutes to take a break"* or *"Remind me at 6:30 PM to log out"*.
*   **App Launching**: *"Open Notepad"*, *"Open Chrome"*, or *"Open Calculator"*.
*   **Command History**: *"Show history"* or *"Clear history"*.

---

## 🖼️ UI/UX Design Showcase

| Widget Panel | Design Specifications |
| :--- | :--- |
| **Jarvis Arc Reactor Core** | Animated vector ring, rotating blades, radar sweep scanline, and dynamic signal gain metrics. |
| **Sound Oscilloscope** | Tri-layer overlapping sine-wave generator using canvas line renderings with random jitter. |
| **Logstream Terminal** | Scrolling Consolas font window streaming system actions. |

---

## 🔮 Future Enhancements

*   **SQLite DB Migration**: Transition storage from simple JSON databases to thread-safe local SQLite transactions.
*   **NLU Routing Registry**: Replace sequential `if-elif` intent routes with a decorator-based command registry router.
*   **LLM Integration**: Connect the backend speech pipeline to a local Ollama instance or external Gemini API for natural, context-aware conversations.

---

## ✍️ Author Information

*   **Developer**: Harshada Hivadkar
*   **GitHub**: [@harshadahivadkar22](https://github.com/harshadahivadkar22)
*   **Repository URL**: [AstraVoice-AI-Assistant](https://github.com/harshadahivadkar22/AstraVoice-AI-Assistant)
