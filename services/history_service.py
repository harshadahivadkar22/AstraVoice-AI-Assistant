import os
import json
import logging
from datetime import datetime
from services.models import HistoryRecord

# Get module-specific logger
logger = logging.getLogger("AstraVoice.HistoryService")

class HistoryService:
    """
    HistoryService logs all voice commands recognized by AstraVoice AI Assistant.
    It saves logs with timestamps into a JSON database ('memory/command_history.json')
    and provides routines to retrieve or clear records.
    """
    def __init__(self) -> None:
        """
        Initializes the History Service.
        """
        self.db_dir: str = "memory"
        self.db_name: str = "command_history.json"
        self.db_path: str = os.path.join(self.db_dir, self.db_name)
        
        # Ensure database directory exists
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            logger.info(f"Created command history directory: '{self.db_dir}'")
            
        self.history: list[HistoryRecord] = self._load_history()
        logger.info("HistoryService initialized.")

    def _load_history(self) -> list[HistoryRecord]:
        """
        Loads the command history records from the JSON database file.

        Returns:
            list[HistoryRecord]: List of history logs.
        """
        if not os.path.exists(self.db_path):
            logger.info("Command history database file does not exist. Initializing empty list.")
            return []
            
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                records = json.loads(content)
                logger.info(f"Loaded {len(records)} history records from database.")
                return [HistoryRecord.from_dict(h) for h in records]
        except Exception as e:
            logger.error(f"Failed to load history database: {e}")
            return []

    def _save_history(self) -> None:
        """
        Saves the command history list to the JSON database file.
        """
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump([h.to_dict() for h in self.history], f, indent=4)
            logger.info("Successfully wrote command history database to disk.")
        except Exception as e:
            logger.error(f"Failed to save history database: {e}")

    def add_command(self, command_text: str) -> None:
        """
        Appends a voice command to the history list with a timestamp.

        Args:
            command_text (str): The voice query command text.
        """
        if not command_text or not command_text.strip():
            return

        # Sanitize: limit to 200 printable characters to prevent buffer/storage pollution
        sanitized_text = "".join(ch for ch in command_text if ch.isprintable())[:200].strip()
        if not sanitized_text:
            return

        record = HistoryRecord(
            command=sanitized_text,
            timestamp=datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        )
        self.history.append(record)
        self._save_history()
        
        # Log metadata (length/word count) to prevent plaintext transcription leaks in diagnostic log files
        word_count = len(sanitized_text.split())
        logger.info(f"Logged voice command of length {word_count} words to history database at {record.timestamp}")

    def get_history(self) -> list[HistoryRecord]:
        """
        Retrieves the complete command history.

        Returns:
            list[HistoryRecord]: List of history records.
        """
        return self.history

    def clear_history(self) -> None:
        """
        Clears all history logs and updates the JSON database.
        """
        self.history = []
        self._save_history()
        logger.info("Command history database cleared.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Testing HistoryService...")
    service = HistoryService()
    service.add_command("test code quality")
    print(service.get_history())
