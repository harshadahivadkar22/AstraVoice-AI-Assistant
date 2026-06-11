import customtkinter
import ui.theme as theme
from datetime import datetime
from typing import Optional
import math
import random
from services.models import WeatherData, NewsArticle, Reminder, HistoryRecord

class StatusPanel(customtkinter.CTkFrame):
    """
    StatusPanel displays the current AI status, system clock,
    microphone status, session stats, and a light/dark mode switch.
    """
    def __init__(self, master, toggle_theme_callback=None, **kwargs) -> None:
        super().__init__(master, fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER, border_width=1, **kwargs)
        
        # Track clock task ID for cleanup
        self._clock_job = None
        
        # Grid Configuration (6 columns)
        self.grid_columnconfigure(0, weight=2) # Name
        self.grid_columnconfigure(1, weight=1) # Stats
        self.grid_columnconfigure(2, weight=1) # Clock
        self.grid_columnconfigure(3, weight=1) # Mic status
        self.grid_columnconfigure(4, weight=1) # Status label
        self.grid_columnconfigure(5, weight=1) # Theme switch
        
        # 1. Assistant Name Label
        self.name_label = customtkinter.CTkLabel(
            self, text="🤖 ASTRAVOICE AI", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_ACCENT
        )
        self.name_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # 2. Session Stats Label
        self.stats_label = customtkinter.CTkLabel(
            self, text="📊 Commands: 0", font=theme.FONT_BODY_BOLD, text_color=theme.TEXT_MAIN
        )
        self.stats_label.grid(row=0, column=1, padx=15, pady=10, sticky="")
        
        # 3. Dynamic Clock Widget
        self.clock_label = customtkinter.CTkLabel(
            self, text="", font=theme.FONT_BODY_BOLD, text_color=theme.TEXT_MUTED
        )
        self.clock_label.grid(row=0, column=2, padx=15, pady=10, sticky="")
        self._update_clock()
        
        # 4. Microphone Status Widget
        self.mic_status_label = customtkinter.CTkLabel(
            self, text="🎤 Mic: Ready", font=theme.FONT_BODY_BOLD, text_color=theme.TEXT_MUTED
        )
        self.mic_status_label.grid(row=0, column=3, padx=15, pady=10, sticky="")
        
        # 5. Status Indicator
        self.status_label = customtkinter.CTkLabel(
            self, text="● IDLE", font=theme.FONT_BODY_BOLD, text_color=theme.COLOR_IDLE
        )
        self.status_label.grid(row=0, column=4, padx=15, pady=10, sticky="")
        
        # 6. Theme Toggle Switch
        self.toggle_theme_callback = toggle_theme_callback
        self.theme_switch = customtkinter.CTkSwitch(
            self, text="Dark HUD", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MAIN,
            command=self._toggle_theme
        )
        self.theme_switch.select() # Selected (Dark mode) by default
        self.theme_switch.grid(row=0, column=5, padx=15, pady=10, sticky="e")

    def _update_clock(self) -> None:
        """
        Updates the clock display every second.
        """
        if not self.winfo_exists():
            return
        now_str = datetime.now().strftime("%I:%M:%S %p")
        self.clock_label.configure(text=f"🕒 {now_str}")
        self._clock_job = self.after(1000, self._update_clock)

    def set_status(self, status: str) -> None:
        """
        Modifies the status text and accent color in real-time.
        """
        clean_status = status.lower().strip()
        
        if clean_status == "listening":
            self.status_label.configure(text="● LISTENING...", text_color=theme.COLOR_LISTENING)
            self.mic_status_label.configure(text="🎤 Mic: Capturing", text_color=theme.COLOR_LISTENING)
        elif clean_status == "processing":
            self.status_label.configure(text="● PROCESSING...", text_color=theme.COLOR_PROCESSING)
            self.mic_status_label.configure(text="🎤 Mic: Processing", text_color=theme.COLOR_PROCESSING)
        elif clean_status == "speaking":
            self.status_label.configure(text="● SPEAKING...", text_color=theme.COLOR_SPEAKING)
            self.mic_status_label.configure(text="🎤 Mic: Standby", text_color=theme.COLOR_SPEAKING)
        elif clean_status == "error":
            self.status_label.configure(text="● ALERT ERROR", text_color="#ff3333")
            self.mic_status_label.configure(text="🎤 Mic: Fault", text_color="#ff3333")
        else:
            self.status_label.configure(text="● IDLE", text_color=theme.COLOR_IDLE)
            self.mic_status_label.configure(text="🎤 Mic: Ready", text_color=theme.TEXT_MUTED)

    def update_stats(self, count: int) -> None:
        """
        Updates the command count statistics indicator.
        """
        self.stats_label.configure(text=f"📊 Commands: {count}")

    def _toggle_theme(self) -> None:
        """
        Switches appearance mode between light and dark.
        """
        if self.theme_switch.get() == 1:
            customtkinter.set_appearance_mode("Dark")
            self.theme_switch.configure(text="Dark HUD")
        else:
            customtkinter.set_appearance_mode("Light")
            self.theme_switch.configure(text="Light HUD")
            
        if self.toggle_theme_callback:
            self.toggle_theme_callback()


class JarvisAvatar(customtkinter.CTkFrame):
    """
    JarvisAvatar draws an animated, rotating Jarvis Arc Reactor and
    an oscilloscope voice waveform visualizer using a Tkinter Canvas.
    """
    def __init__(self, master, click_callback=None, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.click_callback = click_callback
        
        # Dimensions
        self.width = 300
        self.height = 300
        self.cx = self.width // 2
        self.cy = self.height // 2
        
        # Track animation task ID for cleanup
        self._animate_job = None
        
        # Canvas creation
        self.canvas = customtkinter.CTkCanvas(
            self, width=self.width, height=self.height, bg="#080b10",
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill="both")
        
        # Bind click callback to canvas
        if self.click_callback:
            self.canvas.bind("<Button-1>", lambda e: self.click_callback())
            
        # Bind dynamic resize configure event for full responsiveness
        self.canvas.bind("<Configure>", self._on_resize)
        
        # Animation parameters
        self.state = "idle"
        self.angle = 0.0
        self.pulse_val = 0.0
        self.pulse_dir = 1
        self.waveform_phase = 0.0
        self.scan_angle = 0.0
        
        # Mode state caching to eliminate CPU rendering bottlenecks
        self.last_mode = None
        
        # Start animation loops
        self._animate_tick()

    def _on_resize(self, event) -> None:
        """
        Triggered dynamically when the frames stretch, scaling vector dimensions.
        """
        self.width = event.width
        self.height = event.height
        self.cx = self.width // 2
        self.cy = self.height // 2

    def update_canvas_bg(self) -> None:
        """
        Adapts the canvas background to match Light or Dark modes only on transition.
        """
        mode = customtkinter.get_appearance_mode()
        if mode != self.last_mode:
            self.last_mode = mode
            bg_col = "#080b10" if mode.lower() == "dark" else "#f4f6f9"
            self.canvas.configure(bg=bg_col)

    def set_state(self, state: str) -> None:
        """
        Updates the internal state to change colors/speed: 'idle', 'listening', 'processing', 'speaking', 'error'.
        """
        self.state = state.lower().strip()

    def _animate_tick(self) -> None:
        """
        Primary update scheduler running at ~25 FPS.
        """
        if self.winfo_exists():
            self.update_canvas_bg()
            self._draw_avatar()
            self._animate_job = self.after(40, self._animate_tick)

    def cleanup(self) -> None:
        """
        Cancels all pending after animation tasks.
        """
        if hasattr(self, "_animate_job") and self._animate_job:
            try:
                self.after_cancel(self._animate_job)
            except Exception:
                pass
            self._animate_job = None

    def _draw_avatar(self) -> None:
        """
        Draws the vector rings, glowing core, rotor blades, scan sweeps,
        telemetry overlays, and oscilloscope graphs. All dimensions scale dynamically.
        """
        self.canvas.delete("all")
        
        # 1. Determine active color scheme based on state
        mode = customtkinter.get_appearance_mode().lower()
        is_dark = (mode == "dark")
        
        if self.state == "listening":
            color = theme.COLOR_LISTENING[1] if is_dark else theme.COLOR_LISTENING[0]
        elif self.state == "processing":
            color = theme.COLOR_PROCESSING[1] if is_dark else theme.COLOR_PROCESSING[0]
        elif self.state == "speaking":
            color = theme.COLOR_SPEAKING[1] if is_dark else theme.COLOR_SPEAKING[0]
        elif self.state == "error":
            color = "#ff3333" # Telemetry error alert color
        else: # idle
            color = theme.COLOR_IDLE[1] if is_dark else theme.COLOR_IDLE[0]
            
        # Proportional vector scale calculation based on dimensions
        scale = min(self.width, self.height) / 300.0
        r_out = int(90 * scale)
        r_diag = int(75 * scale)
        r_core_base = 25 * scale
        r_core_range = 8 * scale
        r_in = int(38 * scale)
        r_ext = int(55 * scale)
        r_ticks = int(98 * scale)
        
        # 2. Draw rotating outer segment rings
        if self.state == "processing":
            self.angle += 6.0
        elif self.state == "listening":
            self.angle += 1.5
        elif self.state == "speaking":
            self.angle += 3.0
        elif self.state == "error":
            self.angle += 0.3 # Slow error rotation
        else:
            self.angle += 0.6
            
        # Draw 8 rotating segment arcs
        for i in range(8):
            start = self.angle + i * 45
            self.canvas.create_arc(
                self.cx - r_out, self.cy - r_out,
                self.cx + r_out, self.cy + r_out,
                start=start, extent=20, style="arc",
                outline=color, width=2
            )
            
        # 3. Draw diagnostic circles (dashed rings)
        self.canvas.create_oval(
            self.cx - r_diag, self.cy - r_diag,
            self.cx + r_diag, self.cy + r_diag,
            outline=color, width=1, dash=(6, 4)
        )
        
        # 4. Core breathing calculations
        if self.state == "listening":
            self.pulse_val += 0.12 * self.pulse_dir
        elif self.state == "error":
            self.pulse_val += 0.18 * self.pulse_dir # Flashing speed
        else:
            self.pulse_val += 0.03 * self.pulse_dir
            
        if self.pulse_val >= 1.0 or self.pulse_val <= 0.0:
            self.pulse_dir *= -1
            self.pulse_val = max(0.0, min(1.0, self.pulse_val))
            
        r_core = r_core_base + r_core_range * self.pulse_val
        
        # Draw central glow ring
        self.canvas.create_oval(
            self.cx - r_core - 4, self.cy - r_core - 4,
            self.cx + r_core + 4, self.cy + r_core + 4,
            outline=color, width=1
        )
        
        # Inner core block fill
        self.canvas.create_oval(
            self.cx - r_core, self.cy - r_core,
            self.cx + r_core, self.cy + r_core,
            fill=color, outline=""
        )
        
        # 5. Draw Iron Man Arc Reactor triangular rotor blades
        for i in range(6):
            ang_rad = math.radians(self.angle * 1.3 + i * 60)
            x1 = self.cx + r_in * math.cos(ang_rad)
            y1 = self.cy + r_in * math.sin(ang_rad)
            x2 = self.cx + r_ext * math.cos(ang_rad)
            y2 = self.cy + r_ext * math.sin(ang_rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)
            
        # 6. Futuristic Telemetry Ticks (HUD indicators)
        for i in range(12):
            ang_rad = math.radians(i * 30 + self.angle * 0.2)
            x1 = self.cx + r_ticks * math.cos(ang_rad)
            y1 = self.cy + r_ticks * math.sin(ang_rad)
            x2 = self.cx + (r_ticks + int(4 * scale)) * math.cos(ang_rad)
            y2 = self.cy + (r_ticks + int(4 * scale)) * math.sin(ang_rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1)
            
        # 7. Radar sweeping scanline
        self.scan_angle = (self.scan_angle + 2.5) % 360
        scan_rad = math.radians(self.scan_angle)
        x_scan = self.cx + r_out * math.cos(scan_rad)
        y_scan = self.cy + r_out * math.sin(scan_rad)
        self.canvas.create_line(self.cx, self.cy, x_scan, y_scan, fill=color, width=1, dash=(3, 3))
        
        # 8. Corner Diagnostic Text Feeds (Consolas font)
        dim_color = "#337788" if mode == "light" else "#008899"
        if self.state == "listening":
            dim_color = "#990044" if mode == "light" else "#cc0066"
        elif self.state == "processing":
            dim_color = "#aa5500" if mode == "light" else "#dd7700"
        elif self.state == "speaking":
            dim_color = "#226622" if mode == "light" else "#00aa44"
        elif self.state == "error":
            dim_color = "#bb0000" if mode == "light" else "#ff3333"
            
        try:
            cmd_cnt = self.master.master.master.session_commands
        except AttributeError:
            cmd_cnt = 0
            
        # Position telemetry relative to scaled coordinates
        self.canvas.create_text(25, 20, text="SYS_STATE // ACTV", fill=dim_color, font=("Consolas", 8), anchor="w")
        self.canvas.create_text(self.width - 25, 20, text="CORE_TEMP // 36.8C", fill=dim_color, font=("Consolas", 8), anchor="e")
        self.canvas.create_text(25, self.height - 20, text=f"CMD_LOGS // 0{cmd_cnt}" if cmd_cnt < 10 else f"CMD_LOGS // {cmd_cnt}", fill=dim_color, font=("Consolas", 8), anchor="w")
        
        if self.state == "listening":
            sig_gain = "SIG_GAIN // 1.25x"
        elif self.state == "error":
            sig_gain = "SIG_GAIN // FAULT"
        else:
            sig_gain = "SIG_GAIN // STBY"
            
        self.canvas.create_text(self.width - 25, self.height - 20, text=sig_gain, fill=dim_color, font=("Consolas", 8), anchor="e")

        # 9. Draw sound waveform visualizer at bottom (only in listening or speaking states)
        if self.state in ("listening", "speaking"):
            self.waveform_phase += 0.22
            amp = 24.0 * scale if self.state == "listening" else 14.0 * scale
            
            # Generate 3 overlapping waves with offset phases for depth
            for offset, opacity_ratio, w_width in [(0.0, 1.0, 3), (1.8, 0.6, 1), (3.6, 0.4, 2)]:
                points = []
                wave_y = self.height - 35
                
                for x in range(15, self.width - 15, 6):
                    rad = (x * 0.045) + self.waveform_phase + offset
                    window_multiplier = math.sin(((x - 15) / (self.width - 30)) * math.pi)
                    
                    jitter = random.uniform(0.7, 1.3) if self.state == "listening" else 1.0
                    y = wave_y + amp * math.sin(rad) * window_multiplier * jitter
                    points.append((x, y))
                    
                # Render lines
                for j in range(len(points) - 1):
                    self.canvas.create_line(
                        points[j][0], points[j][1],
                        points[j+1][0], points[j+1][1],
                        fill=color, width=w_width
                    )


class WeatherPanel(customtkinter.CTkFrame):
    """
    WeatherPanel displays weather indicators: Temperature,
    humidity, wind speed, and conditions.
    """
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER, border_width=1, **kwargs)
        
        # Title Container for title and status badge
        title_container = customtkinter.CTkFrame(self, fg_color="transparent")
        title_container.pack(fill="x", padx=15, pady=(12, 8))
        
        self.title_label = customtkinter.CTkLabel(
            title_container, text="🌤️ WEATHER MONITOR", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_ACCENT
        )
        self.title_label.pack(side="left")
        
        self.status_badge = customtkinter.CTkLabel(
            title_container, text="[ MOCK ]", font=theme.FONT_BODY_BOLD, text_color="#ffaa00"
        )
        self.status_badge.pack(side="right")
        
        # Data Grid Container
        self.grid_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=15, pady=(0, 12))
        
        # Initialize Labels
        self.temp_label = customtkinter.CTkLabel(self.grid_frame, text="--°C", font=theme.FONT_HERO, text_color=theme.TEXT_MAIN)
        self.temp_label.grid(row=0, column=0, rowspan=2, padx=(0, 15), sticky="w")
        
        self.city_label = customtkinter.CTkLabel(self.grid_frame, text="No Location Query", font=theme.FONT_BODY_BOLD, text_color=theme.TEXT_MAIN)
        self.city_label.grid(row=0, column=1, sticky="w")
        
        self.condition_label = customtkinter.CTkLabel(self.grid_frame, text="Condition: --", font=theme.FONT_BODY, text_color=theme.TEXT_MUTED)
        self.condition_label.grid(row=1, column=1, sticky="w")
        
        # Humidity & Wind
        self.metrics_label = customtkinter.CTkLabel(
            self.grid_frame, text="Humidity: -- %  |  Wind: -- m/s", font=theme.FONT_BODY, text_color=theme.TEXT_MUTED
        )
        self.metrics_label.grid(row=2, column=0, columnspan=2, pady=(8, 0), sticky="w")

    def update_weather(self, weather_info: WeatherData, is_mock: bool = True) -> None:
        """
        Updates the panel text fields with weather service data.
        """
        if not weather_info:
            return
        
        if is_mock:
            self.status_badge.configure(text="[ MOCKED ]", text_color="#ffaa00")
        else:
            self.status_badge.configure(text="[ LIVE ]", text_color="#00ff66")
            
        cond = weather_info.condition.lower()
        icon = "☀️"
        if "cloud" in cond:
            icon = "☁️"
        elif "rain" in cond or "drizzle" in cond:
            icon = "🌧️"
        elif "snow" in cond:
            icon = "❄️"
        elif "clear" in cond:
            icon = "☀️"
        elif "haze" in cond or "mist" in cond or "fog" in cond:
            icon = "🌫️"
        elif "storm" in cond or "thunder" in cond:
            icon = "⛈️"
            
        self.temp_label.configure(text=f"{icon} {weather_info.temp}°C")
        self.city_label.configure(text=weather_info.city.upper())
        self.condition_label.configure(text=f"COND // {weather_info.condition.upper()}")
        self.metrics_label.configure(
            text=f"💧 HUMIDITY: {weather_info.humidity}%  |  💨 WIND: {weather_info.wind_speed} M/S"
        )


class NewsPanel(customtkinter.CTkFrame):
    """
    NewsPanel lists top headlines in a scrollable frame.
    """
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER, border_width=1, **kwargs)
        
        # Title Container for title and status badge
        title_container = customtkinter.CTkFrame(self, fg_color="transparent")
        title_container.pack(fill="x", padx=15, pady=(12, 8))
        
        self.title_label = customtkinter.CTkLabel(
            title_container, text="📰 TELEMETRY HEADLINES", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_ACCENT
        )
        self.title_label.pack(side="left")
        
        self.status_badge = customtkinter.CTkLabel(
            title_container, text="[ MOCK ]", font=theme.FONT_BODY_BOLD, text_color="#ffaa00"
        )
        self.status_badge.pack(side="right")
        
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self, fg_color="transparent", height=120
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.empty_label = customtkinter.CTkLabel(
            self.scroll_frame, text="No headlines requested yet. Say, 'Read the news' or 'Technology news'.",
            font=theme.FONT_BODY, text_color=theme.TEXT_MUTED, wraplength=230, justify="left"
        )
        self.empty_label.pack(padx=10, pady=10, fill="x")

    def update_news(self, headlines: list[NewsArticle], is_mock: bool = True) -> None:
        """
        Updates the headlines display list.
        """
        if is_mock:
            self.status_badge.configure(text="[ MOCKED ]", text_color="#ffaa00")
        else:
            self.status_badge.configure(text="[ LIVE ]", text_color="#00ff66")
            
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not headlines:
            self.empty_label = customtkinter.CTkLabel(
                self.scroll_frame, text="No headlines retrieved.", font=theme.FONT_BODY, text_color=theme.TEXT_MUTED
            )
            self.empty_label.pack(padx=10, pady=10)
            return

        for idx, art in enumerate(headlines, 1):
            title = art.title
            source = art.source
            
            item_frame = customtkinter.CTkFrame(self.scroll_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=4)
            
            lbl = customtkinter.CTkLabel(
                item_frame, text=f"🤖 [0{idx}] {title.upper()}", font=theme.FONT_BODY, text_color=theme.TEXT_MAIN,
                wraplength=230, justify="left", anchor="w"
            )
            lbl.pack(fill="x", anchor="w")
            
            src_lbl = customtkinter.CTkLabel(
                item_frame, text=f"   FEED_SRC // {source.upper()}", font=theme.FONT_BODY, text_color=theme.TEXT_MUTED,
                anchor="w"
            )
            src_lbl.pack(fill="x", anchor="w")


class ReminderPanel(customtkinter.CTkFrame):
    """
    ReminderPanel lists active and scheduled reminders managed by ReminderService.
    """
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER, border_width=1, **kwargs)
        
        self.title_label = customtkinter.CTkLabel(
            self, text="⏰ CRON ALERT PROTOCOLS", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_ACCENT
        )
        self.title_label.pack(anchor="w", padx=15, pady=(12, 8))
        
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self, fg_color="transparent", height=110
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.empty_label = customtkinter.CTkLabel(
            self.scroll_frame, text="No active reminders. Say, 'Remind me in 5 minutes to stretch'.",
            font=theme.FONT_BODY, text_color=theme.TEXT_MUTED, wraplength=230, justify="left"
        )
        self.empty_label.pack(padx=10, pady=15)

    def update_reminders(self, reminders: list[Reminder]) -> None:
        """
        Refreshes active scheduled list items.
        """
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        active_rems = [r for r in reminders if not r.triggered]
        
        if not active_rems:
            self.empty_label = customtkinter.CTkLabel(
                self.scroll_frame, text="No active reminders scheduled.", font=theme.FONT_BODY, text_color=theme.TEXT_MUTED
            )
            self.empty_label.pack(padx=10, pady=15)
            return

        for idx, rem in enumerate(active_rems, 1):
            msg = rem.message
            time_str = rem.target_time_str
            
            try:
                parts = time_str.split(" ")
                t_desc = parts[1] + " " + parts[2]
            except Exception:
                t_desc = time_str
                
            item_frame = customtkinter.CTkFrame(self.scroll_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            
            lbl = customtkinter.CTkLabel(
                item_frame, text=f"⏳ [SCHED: {t_desc}] {msg.upper()}", font=theme.FONT_BODY, text_color=theme.TEXT_MAIN,
                wraplength=230, justify="left", anchor="w"
            )
            lbl.pack(fill="x", anchor="w")


class HistoryPanel(customtkinter.CTkFrame):
    """
    HistoryPanel displays the list of user queries.
    """
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER, border_width=1, **kwargs)
        
        self.title_label = customtkinter.CTkLabel(
            self, text="📜 INCOMING REQUEST STREAMS", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_ACCENT
        )
        self.title_label.pack(anchor="w", padx=15, pady=(12, 8))
        
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self, fg_color="transparent", height=110
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.empty_label = customtkinter.CTkLabel(
            self.scroll_frame, text="History logs will appear here.",
            font=theme.FONT_BODY, text_color=theme.TEXT_MUTED
        )
        self.empty_label.pack(padx=10, pady=15)

    def update_history(self, history: list[HistoryRecord]) -> None:
        """
        Updates the query list display. Shows up to 15 entries.
        """
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not history:
            self.empty_label = customtkinter.CTkLabel(
                self.scroll_frame, text="History database is empty.", font=theme.FONT_BODY, text_color=theme.TEXT_MUTED
            )
            self.empty_label.pack(padx=10, pady=15)
            return

        # Show logs in reverse order (newest first)
        for idx, rec in enumerate(reversed(history[-15:]), 1):
            cmd = rec.command
            
            try:
                parts = rec.timestamp.split(" ")
                t_str = parts[1] + " " + parts[2]
            except Exception:
                t_str = rec.timestamp
            
            lbl = customtkinter.CTkLabel(
                self.scroll_frame, text=f"⚡ [{t_str}] CMD // {cmd.upper()}", font=theme.FONT_BODY, text_color=theme.TEXT_MAIN,
                wraplength=230, justify="left", anchor="w"
            )
            lbl.pack(fill="x", pady=2, anchor="w")
