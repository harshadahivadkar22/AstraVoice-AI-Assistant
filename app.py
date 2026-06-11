import sys
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

import config
from services.speech_service import SpeechService
from services.tts_service import TTSService
from services.weather_service import WeatherService
from services.news_service import NewsService
from services.reminder_service import ReminderService
from services.app_launcher import AppLauncher
from services.history_service import HistoryService

# Get app-specific logger
logger = logging.getLogger("AstraVoice.Main")

def parse_reminder(command_clean: str) -> Tuple[Optional[str], Optional[datetime]]:
    """
    Parses reminder commands into a structured message and target datetime.
    Supported formats:
    - "remind me in <X> seconds/minutes/hours [to/about/that] <message>"
    - "remind me at <time> [to/about/that] <message>"

    Args:
        command_clean (str): Cleaned, lowercase user command.

    Returns:
        Tuple[Optional[str], Optional[datetime]]: A tuple containing:
            - message (Optional[str]): The message text.
            - target_datetime (Optional[datetime]): Calculated trigger time, or None if parsing fails.
    """
    message: str = "Reminder Alert!"
    target_dt: Optional[datetime] = None
    
    # 1. Parse relative duration reminders
    relative_match = re.match(
        r"^remind me in (\d+)\s*(second|minute|hour)s?(?:\s+(?:to|about|that)?\s*(.+))?$",
        command_clean
    )
    
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2).lower()
        custom_message = relative_match.group(3)
        
        if custom_message:
            message = custom_message.replace("?", "").replace(".", "").replace("!", "").strip().title()
            
        now = datetime.now()
        if "second" in unit:
            target_dt = now + timedelta(seconds=amount)
        elif "minute" in unit:
            target_dt = now + timedelta(minutes=amount)
        elif "hour" in unit:
            target_dt = now + timedelta(hours=amount)
            
        logger.info(f"parse_reminder: Parsed relative duration reminder: amount={amount}, unit={unit}, message_len={len(message)}")
        return message, target_dt

    # 2. Parse absolute time reminders
    absolute_match = re.match(
        r"^remind me at (\d{1,2}(?::\d{2})?\s*(?:am|pm)?)(?:\s+(?:to|about|that)?\s*(.+))?$",
        command_clean
    )
    
    if absolute_match:
        time_str = absolute_match.group(1).strip().upper()
        custom_message = absolute_match.group(2)
        
        if custom_message:
            message = custom_message.replace("?", "").replace(".", "").replace("!", "").strip().title()
            
        parsed_time = None
        # Evaluate standard formats
        for fmt in ("%I:%M %p", "%I %p", "%H:%M", "%H"):
            try:
                parsed_time = datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                continue
                
        if parsed_time:
            now = datetime.now()
            target_dt = datetime.combine(now.date(), parsed_time)
            
            # If target time has passed today, assume tomorrow
            if target_dt < now:
                target_dt += timedelta(days=1)
                
            logger.info(f"parse_reminder: Parsed absolute time reminder: time={time_str}, message_len={len(message)}, target={target_dt}")
            return message, target_dt
            
    logger.debug(f"parse_reminder: Command pattern did not match reminder expressions (command length: {len(command_clean)})")
    return None, None

def process_command(
    command_text: str, 
    weather_service: WeatherService, 
    news_service: NewsService, 
    reminder_service: ReminderService, 
    app_launcher: AppLauncher, 
    history_service: HistoryService, 
    tts_service: TTSService
) -> bool:
    """
    Parses the recognized voice command text and routes it to the corresponding service.

    Args:
        command_text (str): The raw transcribed speech command.
        weather_service (WeatherService): Weather service instance.
        news_service (NewsService): News service instance.
        reminder_service (ReminderService): Reminder service instance.
        app_launcher (AppLauncher): Application launcher instance.
        history_service (HistoryService): Command history service instance.
        tts_service (TTSService): TTS service instance.

    Returns:
        bool: True if a supported command intent was matched and executed, False otherwise.
    """
    if not command_text:
        return False
        
    command_clean = command_text.lower().strip()
    word_count = len(command_clean.split())
    logger.info(f"Processing command of length {word_count} words")
    
    try:
        # 1. History Controls Intent Recognition
        if command_clean in ("view history", "show history"):
            logger.info("Executing View History intent.")
            history_list = history_service.get_history()
            
            if not history_list:
                feedback = "Your command history is empty."
                print(f"Assistant: {feedback}")
                tts_service.speak(feedback)
            else:
                total_records = len(history_list)
                intro_msg = f"You have {total_records} command{'s' if total_records != 1 else ''} in your history."
                print(f"\nAssistant: {intro_msg} Listing all entries:")
                
                # Print full history on terminal
                for idx, rec in enumerate(history_list, 1):
                    print(f"  {idx}. [{rec.timestamp}] {rec.command}")
                    
                # Speak only the last 3 entries to avoid blocking TTS
                recent_count = min(3, total_records)
                recent_items = history_list[-recent_count:]
                recent_phrases = []
                for i, rec in enumerate(recent_items, 1):
                    recent_phrases.append(f"Number {total_records - recent_count + i}: {rec.command}")
                    
                speak_text = f"{intro_msg}. Here are the most recent commands: {', '.join(recent_phrases)}."
                tts_service.speak(speak_text)
            return True

        elif command_clean in ("clear history", "delete history"):
            logger.info("Executing Clear History intent.")
            history_service.clear_history()
            feedback = "Command history cleared successfully."
            print(f"Assistant: {feedback}")
            tts_service.speak(feedback)
            return True
        
        # 2. Reminder Intent Recognition
        if command_clean.startswith("remind me"):
            logger.info("Executing Reminder scheduling intent.")
            message, target_dt = parse_reminder(command_clean)
            
            if target_dt:
                reminder_service.add_reminder(message, target_dt)
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
                    if not time_desc:
                        time_desc = "immediate"
                    
                    feedback = f"Reminder set for: {message}, in {time_desc}."
                else:
                    time_str = target_dt.strftime("%I:%M %p")
                    feedback = f"Reminder set for: {message}, at {time_str}."
                    
                print(f"Assistant: {feedback}")
                tts_service.speak(feedback)
            else:
                err_feedback = "Sorry, I could not understand the reminder time. Please say something like, remind me in 5 minutes to study, or, remind me at 5 PM to call mom."
                print(f"Assistant: {err_feedback}")
                tts_service.speak(err_feedback)
            return True
        
        # 3. Weather Intent Recognition
        is_weather_query = False
        city = None
        
        if "weather in " in command_clean:
            is_weather_query = True
            idx = command_clean.find("weather in ") + len("weather in ")
            city = command_clean[idx:]
        elif "temperature in " in command_clean:
            is_weather_query = True
            idx = command_clean.find("temperature in ") + len("temperature in ")
            city = command_clean[idx:]
        elif "weather" in command_clean or "temperature" in command_clean:
            is_weather_query = True
            city = config.DEFAULT_CITY

        if is_weather_query:
            logger.info(f"Executing Weather query intent for city: '{city}'.")
            if city:
                city = city.replace("?", "").replace(".", "").replace("!", "").strip().title()
            
            weather_info = weather_service.get_weather(city)
            if weather_info:
                response = (
                    f"The current weather in {weather_info.city} is {weather_info.condition}. "
                    f"The temperature is {weather_info.temp} degrees Celsius, "
                    f"humidity is {weather_info.humidity} percent, "
                    f"and wind speed is {weather_info.wind_speed} meters per second."
                )
                print(f"Assistant: {response}")
                tts_service.speak(response)
            else:
                response = f"Sorry, I could not retrieve the weather details for {city}."
                print(f"Assistant: {response}")
                tts_service.speak(response)
            return True

        # 4. News Intent Recognition
        is_news_query = False
        news_category = "general"
        
        if "news" in command_clean or "headlines" in command_clean:
            is_news_query = True
            if "technology" in command_clean or "tech" in command_clean:
                news_category = "technology"
            elif "business" in command_clean:
                news_category = "business"
            elif "sports" in command_clean or "sport" in command_clean:
                news_category = "sports"

        if is_news_query:
            logger.info(f"Executing News headlines intent for category: '{news_category}'.")
            headlines = news_service.get_top_headlines(category=news_category, limit=5)
            
            if headlines:
                intro_msg = f"Here are the top headlines in {news_category}."
                print(f"\nAssistant: {intro_msg}")
                tts_service.speak(intro_msg)
                
                for idx, art in enumerate(headlines, 1):
                    title = art.title
                    source = art.source
                    print(f"  {idx}. {title} [{source}]")
                    speak_text = f"Headline {idx}: {title}, from {source}."
                    tts_service.speak(speak_text)
            else:
                response = f"Sorry, I was unable to retrieve the news headlines for the {news_category} category."
                print(f"Assistant: {response}")
                tts_service.speak(response)
            return True

        # 5. Application Launcher Intent Recognition
        if command_clean.startswith("open "):
            app_to_open = command_clean[5:].strip()
            logger.info(f"Executing App Launcher intent (query length: {len(app_to_open)})")
            
            resolved_app = None
            if "chrome" in app_to_open:
                resolved_app = "chrome"
            elif "notepad" in app_to_open:
                resolved_app = "notepad"
            elif "calculator" in app_to_open or "calc" in app_to_open:
                resolved_app = "calculator"
                
            if resolved_app:
                feedback = f"Opening {resolved_app.title()}."
                print(f"Assistant: {feedback}")
                tts_service.speak(feedback)
                
                success = app_launcher.launch_app(resolved_app)
                if not success:
                    err_feedback = f"Sorry, I encountered an error while trying to open {resolved_app.title()}."
                    print(f"Assistant: {err_feedback}")
                    tts_service.speak(err_feedback)
                return True
                
    except Exception as e:
        logger.error(f"Error occurred during intent processing: {e}", exc_info=True)
        fallback_err = "An error occurred while executing that command."
        print(f"Assistant: {fallback_err}")
        tts_service.speak(fallback_err)
        return True

    logger.warning(f"Intent matching skipped. Unhandled voice query (length: {len(command_clean)})")
    return False

def main() -> None:
    """
    Main entry point for AstraVoice AI Assistant.
    Coordinates all modules (STT, TTS, Weather, News, Reminders, Launcher, and History).
    """
    print("==================================================")
    print("   Welcome to AstraVoice AI Assistant")
    print("==================================================")
    logger.info("AstraVoice Application booted.")
    
    # Initialize services
    speech_service = SpeechService()
    tts_service = TTSService(rate=185, volume=1.0)
    weather_service = WeatherService()
    news_service = NewsService()
    reminder_service = ReminderService(tts_service)
    app_launcher = AppLauncher()
    history_service = HistoryService()
    
    # Configure assistant voice profile
    tts_service.set_voice_by_gender('female')
    
    start_message = "AstraVoice AI Assistant is ready. Speak into your microphone."
    print(start_message)
    tts_service.speak(start_message)
    
    print("Press Ctrl+C to terminate the assistant.")
    
    try:
        while True:
            print("\nReady for command...")
            recognized_text = speech_service.listen_and_recognize()
            
            if recognized_text:
                # Automatically log the recognized query to history database
                history_service.add_command(recognized_text)
                
                was_handled = process_command(
                    recognized_text, 
                    weather_service, 
                    news_service, 
                    reminder_service, 
                    app_launcher, 
                    history_service, 
                    tts_service
                )
                
                if not was_handled:
                    response = f"I heard you say: {recognized_text}. However, that command is not supported yet."
                    print(f"Assistant: {response}")
                    tts_service.speak(response)
            else:
                response = "Sorry, I did not catch that. Please try again."
                print(f"Assistant: {response}")
                
    except KeyboardInterrupt:
        goodbye_message = "Stopping AstraVoice AI Assistant. Goodbye!"
        print(f"\n{goodbye_message}")
        tts_service.speak(goodbye_message)
        logger.info("AstraVoice application terminated by user interrupt.")
        sys.exit(0)

if __name__ == '__main__':
    main()
