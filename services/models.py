from dataclasses import dataclass

@dataclass
class WeatherData:
    """
    WeatherData represents structured meteorological reports parsed from weather API.
    """
    city: str
    temp: int
    humidity: int
    wind_speed: float
    condition: str

@dataclass
class NewsArticle:
    """
    NewsArticle represents structured news article headlines with publisher details.
    """
    title: str
    source: str

@dataclass
class Reminder:
    """
    Reminder holds configuration, trigger flags, and execution metrics for chron schedules.
    """
    id: str
    message: str
    target_timestamp: float
    target_time_str: str
    triggered: bool

    def to_dict(self) -> dict:
        """
        Converts properties to database-serializable dictionary.
        """
        return {
            'id': self.id,
            'message': self.message,
            'target_timestamp': self.target_timestamp,
            'target_time_str': self.target_time_str,
            'triggered': self.triggered
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Reminder':
        """
        Deserializes database record dictionary into typed Reminder instance.
        """
        return cls(
            id=d['id'],
            message=d['message'],
            target_timestamp=d['target_timestamp'],
            target_time_str=d['target_time_str'],
            triggered=d.get('triggered', False)
        )

@dataclass
class HistoryRecord:
    """
    HistoryRecord defines typed objects for voice queries logged inside command databases.
    """
    command: str
    timestamp: str

    def to_dict(self) -> dict:
        """
        Converts properties to database-serializable dictionary.
        """
        return {
            'command': self.command,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'HistoryRecord':
        """
        Deserializes database record dictionary into typed HistoryRecord instance.
        """
        return cls(
            command=d['command'],
            timestamp=d['timestamp']
        )
