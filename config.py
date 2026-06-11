import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and configuration settings
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_openweathermap_api_key_here")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Mumbai")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "your_newsapi_key_here")

# Ensure logs directory exists
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Set up logging configuration (outputs to logs/astra_voice.log only)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "astra_voice.log"), encoding="utf-8")
    ]
)

# Root logger for the application
logger = logging.getLogger("AstraVoice")
logger.info("AstraVoice logger initialized.")
