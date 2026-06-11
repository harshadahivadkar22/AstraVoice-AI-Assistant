import logging
import requests
import config
from typing import Optional
from services.models import WeatherData

# Get module-specific logger
logger = logging.getLogger("AstraVoice.WeatherService")

class WeatherService:
    """
    WeatherService integrates with the OpenWeatherMap API to fetch real-time
    weather conditions (temperature, humidity, wind speed, condition) for a city.
    If the API key is not configured, it falls back to a realistic mocked data source.
    """
    def __init__(self) -> None:
        """
        Initializes the weather service with settings from config.py.
        """
        self.api_key: str = config.OPENWEATHER_API_KEY
        self.base_url: str = "https://api.openweathermap.org/data/2.5/weather"
        logger.info("WeatherService initialized.")

    def is_api_key_configured(self) -> bool:
        """
        Checks if the configured API key is valid (not the placeholder).

        Returns:
            bool: True if key is set and is not the default placeholder.
        """
        is_configured = bool(self.api_key and self.api_key != "your_openweathermap_api_key_here")
        logger.info(f"WeatherService: API Key configured checks returned: {is_configured}")
        return is_configured

    def get_weather(self, city_name: str) -> Optional[dict]:
        """
        Fetches the current weather for the specified city.

        Args:
            city_name (str): Name of the city.

        Returns:
            Optional[dict]: Structured weather data dict if successful, None otherwise.
        """
        # Sanitize city_name: limit to 50 characters, only allow letters, numbers, spaces, commas, and hyphens.
        import re
        sanitized_city = re.sub(r'[^a-zA-Z0-9\s,\-]', '', city_name).strip()[:50]
        if not sanitized_city:
            logger.warning(f"WeatherService: Invalid/empty city name query: '{city_name}'")
            return None

        # If API key is not set, run in mock fallback mode
        if not self.is_api_key_configured():
            logger.info(f"Weather API Key is placeholder. Falling back to mock weather for '{sanitized_city}'.")
            return self._get_mock_weather(sanitized_city)

        try:
            params = {
                'q': sanitized_city,
                'appid': self.api_key,
                'units': 'metric'  # Celsius temperature, m/s wind speed
            }
            
            logger.info(f"Sending current weather query to OpenWeatherMap API for city: '{sanitized_city}'.")
            response = requests.get(self.base_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                main_data = data.get('main', {})
                wind_data = data.get('wind', {})
                weather_list = data.get('weather', [{}])
                
                weather_info = WeatherData(
                    city=data.get('name', sanitized_city),
                    temp=round(main_data.get('temp', 0)) if main_data.get('temp') is not None else 0,
                    humidity=main_data.get('humidity', 0),
                    wind_speed=wind_data.get('speed', 0.0),
                    condition=weather_list[0].get('description', 'unknown')
                )
                logger.info(f"Successfully retrieved weather info for '{sanitized_city}': {weather_info}")
                return weather_info
            elif response.status_code == 404:
                print(f"Weather API Error: City '{sanitized_city}' not found.")
                logger.warning(f"Weather query failed: City '{sanitized_city}' was not found by OpenWeatherMap API.")
                return None
            elif response.status_code == 401:
                print("Weather API Error: Invalid API Key. Falling back to mock data.")
                logger.error("Weather query failed: Invalid OpenWeatherMap API Key. Falling back to mock values.")
                return self._get_mock_weather(sanitized_city)
            else:
                print(f"Weather API Error: Received status code {response.status_code}.")
                logger.error(f"Weather query failed: API returned status {response.status_code}.")
                return None
                
        except requests.RequestException as e:
            # Redact API key if it is leaked in exception details or URLs
            err_str = str(e)
            if self.api_key and self.api_key in err_str:
                err_str = err_str.replace(self.api_key, "[REDACTED_API_KEY]")
            print(f"Weather API connection error. (Details suppressed for security)")
            logger.error(f"Weather query failed due to network exception: {err_str}")
            return None

    def _get_mock_weather(self, city_name: str) -> dict:
        """
        Generates realistic mock weather data for testing purposes.

        Args:
            city_name (str): Name of the city.

        Returns:
            dict: Mocked weather details.
        """
        city_clean = city_name.strip().title()
        
        # Realistic defaults per city
        mock_database = {
            "Mumbai": {
                "temp": 31,
                "humidity": 78,
                "wind_speed": 4.2,
                "condition": "scattered clouds"
            },
            "Pune": {
                "temp": 28,
                "humidity": 64,
                "wind_speed": 3.8,
                "condition": "clear sky"
            },
            "Delhi": {
                "temp": 35,
                "humidity": 45,
                "wind_speed": 5.0,
                "condition": "haze"
            },
            "Bangalore": {
                "temp": 26,
                "humidity": 70,
                "wind_speed": 5.5,
                "condition": "moderate rain"
            }
        }
        
        # Fallback for other cities
        default_mock = {
            "temp": 24,
            "humidity": 60,
            "wind_speed": 3.0,
            "condition": "clear sky"
        }
        
        result = mock_database.get(city_clean, default_mock)
        
        # Print offline warning
        print(f"[OFFLINE/MOCK MODE] Synthesizing mock weather data for '{city_clean}'...")
        logger.info(f"Synthesizing offline mock weather metrics for target city: '{city_clean}'")
        
        return WeatherData(
            city=city_clean,
            temp=result['temp'],
            humidity=result['humidity'],
            wind_speed=result['wind_speed'],
            condition=result['condition']
        )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Testing WeatherService...")
    service = WeatherService()
    print(service.get_weather("Mumbai"))
