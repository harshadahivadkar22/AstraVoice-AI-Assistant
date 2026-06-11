import os
import json
import time
import logging
import threading
from datetime import datetime
from services.models import Reminder

# Get module-specific logger
logger = logging.getLogger("AstraVoice.ReminderService")

class ReminderService:
    """
    ReminderService manages scheduling, storing, and triggering reminders.
    It saves reminders in a JSON database ('memory/reminders.json'),
    polls for due reminders using a background daemon thread, and uses
    the TTSService to speak alerts when a reminder triggers.
    """
    def __init__(self, tts_service) -> None:
        """
        Initializes the Reminder Service.

        Args:
            tts_service (TTSService): Text-to-speech service instance to speak reminders.
        """
        self.tts_service = tts_service
        self.db_dir: str = "memory"
        self.db_name: str = "reminders.json"
        self.db_path: str = os.path.join(self.db_dir, self.db_name)
        
        # Lock to ensure thread safety when modifying the reminders list
        self.lock = threading.Lock()
        
        # Ensure database directory exists
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            logger.info(f"Created reminders database directory: '{self.db_dir}'")
            
        self.reminders: list[Reminder] = self._load_reminders()
        
        # Start the background monitoring thread as a daemon (stops when main app stops)
        self.monitor_thread = threading.Thread(target=self._check_reminders_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("ReminderService initialized. Background monitor thread started.")

    def _load_reminders(self) -> list[Reminder]:
        """
        Loads reminders from the JSON database file.

        Returns:
            list[Reminder]: List of saved reminders.
        """
        if not os.path.exists(self.db_path):
            logger.info("Reminders database file does not exist. Initializing empty list.")
            return []
        
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                reminders_data = json.loads(content)
                logger.info(f"Loaded {len(reminders_data)} reminders from database.")
                return [Reminder.from_dict(r) for r in reminders_data]
        except Exception as e:
            logger.error(f"Error loading reminders database: {e}")
            return []

    def _save_reminders(self) -> None:
        """
        Saves the current list of reminders to the JSON database file.
        """
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in self.reminders], f, indent=4)
            logger.info("Successfully wrote reminders database to disk.")
        except Exception as e:
            logger.error(f"Error saving reminders database: {e}")

    def add_reminder(self, message: str, target_time: datetime) -> Reminder:
        """
        Adds a new reminder to the list.

        Args:
            message (str): The reminder alert message.
            target_time (datetime): Datetime object representing when to trigger.

        Returns:
            Reminder: The created Reminder model instance.
        """
        with self.lock:
            # Sanitize: limit to 200 printable characters to prevent buffer/storage pollution
            sanitized_message = "".join(ch for ch in message if ch.isprintable())[:200].strip()
            if not sanitized_message:
                sanitized_message = "Reminder Alert!"

            reminder = Reminder(
                id=str(time.time_ns()),
                message=sanitized_message,
                target_timestamp=target_time.timestamp(),
                target_time_str=target_time.strftime('%Y-%m-%d %I:%M:%S %p'),
                triggered=False
            )
            self.reminders.append(reminder)
            self._save_reminders()
            
            # Log safely without leaking message details in log files
            msg_len = len(sanitized_message)
            logger.info(f"Added new reminder ID: {reminder.id} (message length: {msg_len}) target time: {reminder.target_time_str}")
            return reminder

    def _check_reminders_loop(self) -> None:
        """
        Background loop that runs continuously (every 1 second) to check
        if any active reminders have reached their target triggering times.
        """
        while True:
            time.sleep(1.0)
            
            now_ts = time.time()
            triggered_any = False
            due_reminders = []
            
            with self.lock:
                for rem in self.reminders:
                    if not rem.triggered and now_ts >= rem.target_timestamp:
                        rem.triggered = True
                        due_reminders.append(rem)
                        triggered_any = True
                
                if triggered_any:
                    self._save_reminders()
            
            # Speak and display reminders outside of the lock to prevent blocking
            for rem in due_reminders:
                message = rem.message
                alert_text = f"Reminder alert: {message}."
                print(f"\n[REMINDER TRIGGERED] {alert_text}")
                logger.info(f"Triggered reminder ID: {rem.id} (message length: {len(message)})")
                self.tts_service.speak(alert_text)
