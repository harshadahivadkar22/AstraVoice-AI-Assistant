import sys
import os
import threading
import logging
from datetime import datetime
from typing import Optional

import customtkinter
import ui.theme as theme
from ui.components import StatusPanel, JarvisAvatar, WeatherPanel, NewsPanel, ReminderPanel, HistoryPanel
import config

# Import services
from services.speech_service import SpeechService
from services.tts_service import TTSService
from services.weather_service import WeatherService
from services.news_service import NewsService
from services.reminder_service import ReminderService
from services.app_launcher import AppLauncher
from services.history_service import HistoryService

class HUDLogHandler(logging.Handler):
    """
    HUDLogHandler redirects Python logger events to the CTkTextbox log widget.
    """
    def __init__(self, text_widget: customtkinter.CTkTextbox) -> None:
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            def append():
                if self.text_widget.winfo_exists():
                    self.text_widget.configure(state="normal")
                    self.text_widget.insert("end", msg + "\n")
                    self.text_widget.see("end")
                    self.text_widget.configure(state="disabled")
            self.text_widget.after(0, append)
        except Exception:
            self.handleError(record)

# Try to load tray dependencies
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

logger = logging.getLogger("AstraVoice.Dashboard")


class JarvisSplashScreen(customtkinter.CTk):
    """
    JarvisSplashScreen shows a holographic boot diagnostic loading screen
    before initializing the main dashboard window.
    """
    def __init__(self, on_complete_callback) -> None:
        super().__init__()
        
        self.on_complete_callback = on_complete_callback
        
        # Frameless window configuration
        self.overrideredirect(True)
        
        # Dimensions and center position calculation
        width = 500
        height = 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(fg_color="#080b10")
        
        # Grid settings
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Title
        self.grid_rowconfigure(1, weight=1) # Log message
        self.grid_rowconfigure(2, weight=1) # Progress bar
        
        # Title label
        self.title_lbl = customtkinter.CTkLabel(
            self, text="⚡ ASTRAVOICE AI CORE V3 ⚡", font=("Segoe UI", 20, "bold"), text_color="#00e5ff"
        )
        self.title_lbl.grid(row=0, column=0, pady=(40, 5), sticky="")
        
        # Diagnostic messages
        self.status_lbl = customtkinter.CTkLabel(
            self, text="ESTABLISHING CORE COGNITIVE PROTOCOLS...", font=("Consolas", 10), text_color="#8ab4f8"
        )
        self.status_lbl.grid(row=1, column=0, pady=5, sticky="")
        
        # Progress indicator
        self.progress_bar = customtkinter.CTkProgressBar(self, width=380, progress_color="#00e5ff", fg_color="#1f2833")
        self.progress_bar.grid(row=2, column=0, pady=(5, 40), sticky="")
        self.progress_bar.set(0.0)
        
        # Diagnostic stages
        self.stages = [
            (0.15, "CONNECTING SPEECH AUDIOMETRIC SENSORS..."),
            (0.35, "CALIBRATING SPATIAL AMBIENT ACOUSTICS..."),
            (0.55, "SYNCING METEOROLOGICAL & NEWS NETWORK CORES..."),
            (0.75, "ESTABLISHING REMINDER SCHEDULER SYSTEMS..."),
            (0.95, "FINALIZING NEURAL SYNAPSE ROUTINGS..."),
            (1.0, "ASTRAVOICE ONLINE. WELCOME BACK, SIR.")
        ]
        self.stage_idx = 0
        
        # Launch boot loop
        self.after(300, self._boot_loop)

    def _boot_loop(self) -> None:
        if self.stage_idx < len(self.stages):
            prog, text = self.stages[self.stage_idx]
            self.progress_bar.set(prog)
            self.status_lbl.configure(text=text)
            self.stage_idx += 1
            self.after(450, self._boot_loop)
        else:
            self.after(300, self._finish_boot)

    def _finish_boot(self) -> None:
        self.destroy()
        self.on_complete_callback()


class AstraVoiceDashboard(customtkinter.CTk):
    """
    AstraVoiceDashboard represents the central Jarvis HUD control station
    integrating animations, system trays, and non-blocking speech routing.
    """
    def __init__(self) -> None:
        super().__init__()
        
        # Setup Window Properties
        self.title("AstraVoice AI Assistant - Desktop Dashboard")
        self.geometry("1020x750")
        self.minsize(980, 700)
        self.configure(fg_color=theme.BG_COLOR)
        
        # Track pending reminders polling loop
        self._reminders_job = None
        
        # Control flag to avoid dispatching after-jobs on destroyed widgets
        self.running: bool = True
        
        # Initialize Core Services
        logger.info("Initializing services in dashboard...")
        self.speech_service = SpeechService()
        self.tts_service = TTSService(rate=185, volume=1.0)
        self.weather_service = WeatherService()
        self.news_service = NewsService()
        self.reminder_service = ReminderService(self.tts_service)
        self.app_launcher = AppLauncher()
        self.history_service = HistoryService()
        
        # UI Voice profile setting
        self.tts_service.set_voice_by_gender('female')
        
        # State Control Flags
        self.is_listening: bool = False
        self.current_status: str = "idle"
        self.session_commands: int = 0
        self.worker_thread: Optional[threading.Thread] = None
        
        # Construct GUI Widgets
        self._build_gui()
        
        # Bind keyboard shortcuts for accessibility
        self.bind("<Control-space>", lambda event: self.toggle_listening())
        
        # Setup log handler for HUD Console
        hud_handler = HUDLogHandler(self.hud_log_txt)
        hud_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
        hud_handler.setLevel(logging.INFO)
        logging.getLogger("AstraVoice").addHandler(hud_handler)
        
        # Load initial values
        self._refresh_history_display()
        self._refresh_reminders()
        
        # Tray setup
        self.tray_icon = None
        if TRAY_AVAILABLE:
            self._setup_tray()
            
        # Protocol handling
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("AstraVoice Dashboard UI loaded.")

    def _build_gui(self) -> None:
        """
        Creates responsive grids and packs panels.
        """
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=1)
        
        # 1. Header Status Panel (With Theme Switch & Session Stats)
        self.status_bar = StatusPanel(self, toggle_theme_callback=self._on_theme_toggled)
        self.status_bar.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="ew")
        
        # 2. Main Center/Left Column Panel (Avatar & Waveforms)
        self.center_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, padx=(15, 8), pady=5, sticky="nsew")
        
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=4)  # Avatar frame
        self.center_frame.grid_rowconfigure(1, weight=1)  # Controls buttons
        
        # 2a. Avatar Ring Visualizer Container
        self.mic_frame = customtkinter.CTkFrame(
            self.center_frame, fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER, border_width=1
        )
        self.mic_frame.grid(row=0, column=0, pady=(0, 8), sticky="nsew")
        
        # Animated canvas reactor avatar (Clicking toggles listening loops)
        self.avatar_widget = JarvisAvatar(self.mic_frame, click_callback=self.toggle_listening)
        self.avatar_widget.pack(expand=True, fill="both", pady=15)
        
        self.mic_label = customtkinter.CTkLabel(
            self.mic_frame, text="Click reactor core or press START below", font=theme.FONT_BODY, text_color=theme.TEXT_MUTED
        )
        self.mic_label.pack(pady=(0, 15))
        
        # 2b. Control Buttons Sub-Frame
        self.controls_frame = customtkinter.CTkFrame(self.center_frame, fg_color="transparent")
        self.controls_frame.grid(row=1, column=0, pady=0, sticky="ew")
        
        self.controls_frame.grid_columnconfigure(0, weight=1)
        self.controls_frame.grid_columnconfigure(1, weight=1)
        
        self.start_btn = customtkinter.CTkButton(
            self.controls_frame, text="START LISTENING", font=theme.FONT_BODY_BOLD, fg_color=theme.BTN_PRIMARY,
            text_color="#121214", hover_color=theme.BTN_PRIMARY_HOVER, height=45, command=self.start_listening
        )
        self.start_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        
        self.stop_btn = customtkinter.CTkButton(
            self.controls_frame, text="STOP LISTENING", font=theme.FONT_BODY_BOLD, fg_color=theme.BTN_SECONDARY,
            text_color=theme.TEXT_MAIN, hover_color=theme.BTN_SECONDARY_HOVER, height=45, state="disabled",
            command=self.stop_listening
        )
        self.stop_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        
        # 3. Right Column Side Panel (Widgets)
        self.right_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=1, column=1, padx=(8, 15), pady=5, sticky="nsew")
        
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)  # Weather Panel
        self.right_frame.grid_rowconfigure(1, weight=2)  # News Panel
        self.right_frame.grid_rowconfigure(2, weight=2)  # Reminders Panel
        self.right_frame.grid_rowconfigure(3, weight=2)  # History Panel
        
        # 3a. Weather widget
        self.weather_panel = WeatherPanel(self.right_frame)
        self.weather_panel.grid(row=0, column=0, pady=(0, 8), sticky="nsew")
        
        # 3b. News widget
        self.news_panel = NewsPanel(self.right_frame)
        self.news_panel.grid(row=1, column=0, pady=(0, 8), sticky="nsew")
        
        # 3c. Reminders card
        self.reminder_panel = ReminderPanel(self.right_frame)
        self.reminder_panel.grid(row=2, column=0, pady=(0, 8), sticky="nsew")
        
        # 3d. Command history widget
        self.history_panel = HistoryPanel(self.right_frame)
        self.history_panel.grid(row=3, column=0, pady=0, sticky="nsew")
        
        # 4. Bottom Transcript Section (spans across both columns)
        self.bottom_frame = customtkinter.CTkFrame(
            self, fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER, border_width=1
        )
        self.bottom_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(5, 15), sticky="nsew")
        
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        
        # User Speech Output Display (Left)
        user_container = customtkinter.CTkFrame(self.bottom_frame, fg_color="transparent")
        user_container.grid(row=0, column=0, padx=(15, 6), pady=12, sticky="nsew")
        user_container.grid_columnconfigure(0, weight=1)
        user_container.grid_rowconfigure(1, weight=1)
        
        user_lbl = customtkinter.CTkLabel(user_container, text="🎤 USER SPEECH TRANSCRIPT", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_ACCENT, anchor="w")
        user_lbl.grid(row=0, column=0, pady=(0, 5), sticky="w")
        
        self.user_txt = customtkinter.CTkTextbox(
            user_container, font=theme.FONT_BODY, fg_color=theme.ENTRY_BG, border_color=theme.CARD_BORDER, border_width=1, height=80
        )
        self.user_txt.grid(row=1, column=0, sticky="nsew")
        self.user_txt.insert("0.0", "User speech transcript will appear here...")
        self.user_txt.configure(state="disabled")
        
        # Assistant Verbal Response Display (Middle)
        assistant_container = customtkinter.CTkFrame(self.bottom_frame, fg_color="transparent")
        assistant_container.grid(row=0, column=1, padx=(6, 6), pady=12, sticky="nsew")
        assistant_container.grid_columnconfigure(0, weight=1)
        assistant_container.grid_rowconfigure(1, weight=1)
        
        assistant_lbl = customtkinter.CTkLabel(assistant_container, text="🤖 ASSISTANT RESPONSE", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_ACCENT, anchor="w")
        assistant_lbl.grid(row=0, column=0, pady=(0, 5), sticky="w")
        
        self.assistant_txt = customtkinter.CTkTextbox(
            assistant_container, font=theme.FONT_BODY, fg_color=theme.ENTRY_BG, border_color=theme.CARD_BORDER, border_width=1, height=80
        )
        self.assistant_txt.grid(row=1, column=0, sticky="nsew")
        self.assistant_txt.insert("0.0", "Assistant response will appear here...")
        self.assistant_txt.configure(state="disabled")

        # Real-time System Log Console Display (Right)
        log_container = customtkinter.CTkFrame(self.bottom_frame, fg_color="transparent")
        log_container.grid(row=0, column=2, padx=(6, 15), pady=12, sticky="nsew")
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(1, weight=1)
        
        log_lbl = customtkinter.CTkLabel(log_container, text="📡 SYSTEM LOGSTREAM", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_ACCENT, anchor="w")
        log_lbl.grid(row=0, column=0, pady=(0, 5), sticky="w")
        
        self.hud_log_txt = customtkinter.CTkTextbox(
            log_container, font=("Consolas", 10), fg_color=theme.ENTRY_BG, border_color=theme.CARD_BORDER, border_width=1, height=80
        )
        self.hud_log_txt.grid(row=1, column=0, sticky="nsew")
        self.hud_log_txt.insert("0.0", "System logstream online...")
        self.hud_log_txt.configure(state="disabled")

    # ==========================================
    # Dynamic Update Thread-safe Helpers
    # ==========================================
    def safe_ui_update(self, func, *args) -> None:
        """
        Safely schedules a GUI update on the main Tkinter thread.
        """
        if hasattr(self, "running") and self.running and self.winfo_exists():
            try:
                self.after(0, lambda: self._dispatch_safe(func, *args))
            except Exception:
                pass

    def _dispatch_safe(self, func, *args) -> None:
        """
        Guards callback dispatch executions after window closing.
        """
        if hasattr(self, "running") and self.running and self.winfo_exists():
            try:
                func(*args)
            except Exception:
                pass

    def _set_status_ui(self, status: str, glow_color: str, label_text: str) -> None:
        """
        Modifies status indicators and updates the Jarvis Arc Reactor animation state.
        """
        self.current_status = status.lower().strip()
        self.status_bar.set_status(status)
        self.avatar_widget.set_state(self.current_status)
        self.mic_label.configure(text=label_text)

    def _update_transcript_ui(self, user_phrase: str, assistant_phrase: str) -> None:
        """
        Updates the read-only transcript fields on the GUI main thread.
        """
        # User Box
        self.user_txt.configure(state="normal")
        self.user_txt.delete("0.0", "end")
        self.user_txt.insert("0.0", user_phrase)
        self.user_txt.configure(state="disabled")
        
        # Assistant Box
        self.assistant_txt.configure(state="normal")
        self.assistant_txt.delete("0.0", "end")
        self.assistant_txt.insert("0.0", assistant_phrase)
        self.assistant_txt.configure(state="disabled")

    def _refresh_history_display(self) -> None:
        """
        Loads and populates list records inside the history side panel.
        """
        history = self.history_service.get_history()
        self.history_panel.update_history(history)

    def _refresh_reminders(self) -> None:
        """
        Polls reminders and updates the reminder panel list.
        """
        if not (hasattr(self, "running") and self.running and self.winfo_exists()):
            return
            
        if hasattr(self, "reminder_service"):
            reminders = self.reminder_service.reminders
            self.reminder_panel.update_reminders(reminders)
            
        # Poll again in 3 seconds, storing the job identifier
        self._reminders_job = self.after(3000, self._refresh_reminders)

    def _on_theme_toggled(self) -> None:
        """
        Triggered when light/dark HUD toggle flips, adjusting Canvas elements.
        """
        self.avatar_widget.update_canvas_bg()

    # ==========================================
    # Loop and Thread Controls
    # ==========================================
    def toggle_listening(self) -> None:
        """
        Toggles voice loop threads on/off.
        """
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self) -> None:
        """
        Starts the background daemon listening thread.
        """
        if self.is_listening:
            return
            
        self.is_listening = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal", fg_color="#ff0055", hover_color="#cc0044")
        
        logger.info("Launching daemon listening worker thread...")
        self.worker_thread = threading.Thread(target=self._voice_loop, daemon=True)
        self.worker_thread.start()

    def stop_listening(self) -> None:
        """
        Signals the voice loop thread to stop execution.
        """
        if not self.is_listening:
            return
            
        self.is_listening = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled", fg_color=theme.BTN_SECONDARY, hover_color=theme.BTN_SECONDARY_HOVER)
        self.safe_ui_update(self._set_status_ui, "idle", theme.COLOR_IDLE, "Click reactor core or press START below")
        logger.info("Listening loop signal stop received.")

    def _voice_loop(self) -> None:
        """
        Continually monitors microphone input while listening flag is set.
        """
        while self.is_listening:
            self.safe_ui_update(
                self._set_status_ui, "listening", theme.COLOR_LISTENING, "Listening for speech..."
            )
            
            recognized_text = self.speech_service.listen_and_recognize()
            
            if not self.is_listening:
                break
                
            if recognized_text:
                self.safe_ui_update(
                    self._set_status_ui, "processing", theme.COLOR_PROCESSING, "Processing intent..."
                )
                
                # Log command
                self.history_service.add_command(recognized_text)
                self.session_commands += 1
                self.safe_ui_update(self.status_bar.update_stats, self.session_commands)
                self.safe_ui_update(self._refresh_history_display)
                
                # Process intent routing
                self._handle_command(recognized_text)
            else:
                if self.is_listening:
                    err_msg = "Sorry, I did not catch that. Please speak again."
                    self.safe_ui_update(
                        self._update_transcript_ui, "...", err_msg
                    )
                    
                    # Highlight error crimson state visually
                    self.safe_ui_update(
                        self._set_status_ui, "error", "#ff3333", "Audio captures failed..."
                    )
                    threading.Event().wait(1.2) # Allow red flash duration
                    
                    if not self.is_listening:
                        break
                        
                    self.safe_ui_update(
                        self._set_status_ui, "speaking", theme.COLOR_SPEAKING, "Synthesizing vocal response..."
                    )
                    self.tts_service.speak(err_msg)
                    
            threading.Event().wait(1.0)
            
        logger.info("Daemon voice loop thread terminated.")

    # ==========================================
    # Intent Processing Controller
    # ==========================================
    def _handle_command(self, command_text: str) -> None:
        """
        Routes text requests to component services and speaks results.
        """
        command_clean = command_text.lower().strip()
        assistant_response = ""
        
        try:
            # A. History View/Clear
            if command_clean in ("view history", "show history"):
                history_list = self.history_service.get_history()
                total_records = len(history_list)
                assistant_response = f"You have {total_records} commands in your history."
                self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)
                
            elif command_clean in ("clear history", "delete history"):
                self.history_service.clear_history()
                self.session_commands = 0
                self.safe_ui_update(self.status_bar.update_stats, 0)
                assistant_response = "Command history cleared successfully."
                self.safe_ui_update(self._refresh_history_display)
                self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)

            # B. Reminders Intent
            elif command_clean.startswith("remind me"):
                from app import parse_reminder
                message, target_dt = parse_reminder(command_clean)
                
                if target_dt:
                    self.reminder_service.add_reminder(message, target_dt)
                    time_diff = target_dt - datetime.now()
                    total_seconds = int(time_diff.total_seconds())
                    
                    if total_seconds < 3600:
                        minutes = total_seconds // 60
                        seconds = total_seconds % 60
                        time_desc = ""
                        if minutes > 0:
                            time_desc += f"{minutes} minute{'s' if minutes != 1 else ''}"
                        if seconds > 0:
                            if time_desc:
                                time_desc += " and "
                            time_desc += f"{seconds} second{'s' if seconds != 1 else ''}"
                        assistant_response = f"Reminder set for {message} in {time_desc}."
                    else:
                        time_str = target_dt.strftime("%I:%M %p")
                        assistant_response = f"Reminder set for {message} at {time_str}."
                    # Sync UI immediately
                    self.safe_ui_update(self._refresh_reminders)
                else:
                    assistant_response = "Sorry, I could not resolve the reminder time."
                    
                self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)

            # C. Weather Intent
            elif any(pat in command_clean for pat in ("weather", "temperature")):
                is_weather = False
                city = ""
                
                if "weather in " in command_clean:
                    is_weather = True
                    idx = command_clean.find("weather in ") + len("weather in ")
                    city = command_clean[idx:]
                elif "temperature in " in command_clean:
                    is_weather = True
                    idx = command_clean.find("temperature in ") + len("temperature in ")
                    city = command_clean[idx:]
                elif "weather" in command_clean or "temperature" in command_clean:
                    is_weather = True
                    city = config.DEFAULT_CITY
                    
                if is_weather:
                    city = city.replace("?", "").replace(".", "").replace("!", "").strip().title()
                    weather_info = self.weather_service.get_weather(city)
                    
                    if weather_info:
                        is_mock = not self.weather_service.is_api_key_configured()
                        self.safe_ui_update(self.weather_panel.update_weather, weather_info, is_mock)
                        assistant_response = (
                            f"The current weather in {weather_info.city} is {weather_info.condition}. "
                            f"The temperature is {weather_info.temp} degrees, humidity is {weather_info.humidity} percent, "
                            f"and wind speed is {weather_info.wind_speed} meters per second."
                        )
                    else:
                        assistant_response = f"Sorry, I could not retrieve weather details for {city}."
                self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)

            # D. News Intent
            elif any(pat in command_clean for pat in ("news", "headlines")):
                category = "general"
                if "technology" in command_clean or "tech" in command_clean:
                    category = "technology"
                elif "business" in command_clean:
                    category = "business"
                elif "sports" in command_clean or "sport" in command_clean:
                    category = "sports"
                    
                headlines = self.news_service.get_top_headlines(category=category, limit=5)
                
                if headlines:
                    is_mock = not self.news_service.is_api_key_configured()
                    self.safe_ui_update(self.news_panel.update_news, headlines, is_mock)
                    assistant_response = f"Here are the top headlines in {category}. " + ". ".join([art.title for art in headlines[:3]])
                else:
                    assistant_response = f"Sorry, I could not retrieve the headlines for the {category} category."
                self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)

            # E. Application Launcher Intent
            elif command_clean.startswith("open "):
                app_to_open = command_clean[5:].strip()
                resolved_app = None
                
                if "chrome" in app_to_open:
                    resolved_app = "chrome"
                elif "notepad" in app_to_open:
                    resolved_app = "notepad"
                elif "calculator" in app_to_open or "calc" in app_to_open:
                    resolved_app = "calculator"
                    
                if resolved_app:
                    assistant_response = f"Opening {resolved_app.title()}."
                    self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)
                    self.app_launcher.launch_app(resolved_app)
                else:
                    assistant_response = f"Opening {app_to_open.title()} is not supported."
                    self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)
            
            # F. Unhandled Commands fallback
            else:
                assistant_response = f"I heard you say: {command_text}. That command is not supported yet."
                self.safe_ui_update(
                    self._set_status_ui, "error", "#ff3333", "Command unhandled..."
                )
                self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)
                threading.Event().wait(1.2) # Flash red warning Reactor Core

        except Exception as e:
            logger.error(f"Error handling intent in dashboard: {e}", exc_info=True)
            assistant_response = "An error occurred while executing that command."
            self.safe_ui_update(self._update_transcript_ui, command_text, assistant_response)
            
        self.safe_ui_update(
            self._set_status_ui, "speaking", theme.COLOR_SPEAKING, "Synthesizing vocal response..."
        )
        self.tts_service.speak(assistant_response)

    # ==========================================
    # System Tray Interactivity
    # ==========================================
    def _setup_tray(self) -> None:
        """
        Instantiates the background system tray process menu options.
        """
        # Create reactor core thumbnail image
        img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], outline="#00e5ff", width=6)
        draw.ellipse([24, 24, 40, 40], fill="#00e5ff")
        
        menu = pystray.Menu(
            pystray.MenuItem("Show HUD Dashboard", self.restore_from_tray, default=True),
            pystray.MenuItem("Start Listening", lambda: self.safe_ui_update(self.start_listening)),
            pystray.MenuItem("Stop Listening", lambda: self.safe_ui_update(self.stop_listening)),
            pystray.MenuItem("Exit System", self.on_closing)
        )
        
        self.tray_icon = pystray.Icon("AstraVoice", img, "AstraVoice AI", menu)
        # Spin tray in background thread to prevent GUI freezes
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
        self.bind("<Unmap>", self._on_minimize)

    def _on_minimize(self, event) -> None:
        """
        Triggered when window gets iconified. Minimizes and hides main frame.
        """
        if self.state() == "iconic":
            self.withdraw()
            logger.info("AstraVoice window withdrawn to system tray.")

    def restore_from_tray(self) -> None:
        """
        De-minimizes window and puts focus back on main panel.
        """
        self.deiconify()
        self.state("normal")
        self.focus_force()
        self.lift()
        logger.info("AstraVoice HUD deiconified from system tray.")

    def on_closing(self) -> None:
        """
        Tears down running services, system tray tasks, and destroys windows.
        """
        logger.info("Shutting down core dashboard panels...")
        
        # Stop background loop operations and dispatches instantly
        self.running = False
        self.is_listening = False
        
        # Stop pystray icon
        if self.tray_icon:
            self.tray_icon.stop()
            
        # Cancel all scheduled dashboard after loops
        if hasattr(self, "_reminders_job") and self._reminders_job:
            try:
                self.after_cancel(self._reminders_job)
            except Exception:
                pass
            self._reminders_job = None
            
        # Cancel status bar clock loop
        if hasattr(self.status_bar, "_clock_job") and self.status_bar._clock_job:
            try:
                self.after_cancel(self.status_bar._clock_job)
            except Exception:
                pass
            self.status_bar._clock_job = None
            
        # Cancel avatar canvas animation loop
        if hasattr(self, "avatar_widget") and self.avatar_widget:
            self.avatar_widget.cleanup()
            
        # Destroy window
        try:
            self.destroy()
        except Exception:
            pass


def main() -> None:
    """
    Spawns splash boot sequencer first, loading dashboard on success.
    """
    customtkinter.set_appearance_mode("Dark")
    customtkinter.set_default_color_theme("blue")
    
    def launch_dashboard():
        app = AstraVoiceDashboard()
        app.mainloop()
        sys.exit(0)
        
    splash = JarvisSplashScreen(launch_dashboard)
    try:
        splash.mainloop()
    except KeyboardInterrupt:
        print("\nStopping loader.")
        sys.exit(0)


if __name__ == '__main__':
    main()
