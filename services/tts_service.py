import logging
import pyttsx3
import threading

# Get module-specific logger
logger = logging.getLogger("AstraVoice.TTSService")

class TTSService:
    """
    TTSService handles converting text strings into spoken audio (Text-to-Speech)
    using the offline pyttsx3 library.
    It supports adjustments for speech rate, volume, and voice selection.
    """
    def __init__(self, rate: int = 185, volume: float = 1.0) -> None:
        """
        Initializes the TTS engine.

        Args:
            rate (int): The speaking speed (words per minute). Default is 185.
            volume (float): The speaking volume (0.0 to 1.0). Default is 1.0.
        """
        # Thread lock to serialize access to the non-thread-safe pyttsx3 engine
        self.lock = threading.Lock()
        
        try:
            self.engine = pyttsx3.init()
            logger.info("TTSService: pyttsx3 engine initialized.")
            
            # Set default speech rate and volume
            self.set_rate(rate)
            self.set_volume(volume)
        except Exception as e:
            logger.error(f"TTSService failed to initialize: {e}")

    def speak(self, text: str) -> None:
        """
        Synthesizes the given text to speech and plays it back synchronously.

        Args:
            text (str): The text message to speak.
        """
        if not text or not text.strip():
            return
        
        with self.lock:
            try:
                logger.info(f"Synthesizing speech: '{text}'")
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"Error during Text-to-Speech playback: {e}")

    def set_rate(self, rate: int) -> None:
        """
        Adjusts the speaking speed.

        Args:
            rate (int): Words per minute (typically between 100 and 300).
        """
        try:
            self.engine.setProperty('rate', rate)
            logger.info(f"TTSService: Speech rate set to {rate} WPM.")
        except Exception as e:
            logger.error(f"Error setting speech rate: {e}")

    def set_volume(self, volume: float) -> None:
        """
        Adjusts the volume level.

        Args:
            volume (float): Float value between 0.0 (silent) and 1.0 (maximum).
        """
        try:
            # Keep volume in the range [0.0, 1.0]
            volume = max(0.0, min(1.0, volume))
            self.engine.setProperty('volume', volume)
            logger.info(f"TTSService: Speech volume set to {volume}.")
        except Exception as e:
            logger.error(f"Error setting volume: {e}")

    def set_voice_by_gender(self, gender: str = 'female') -> bool:
        """
        Adjusts the voice profile to male or female based on system-available voices.

        Args:
            gender (str): 'male' or 'female'. Default is 'female'.

        Returns:
            bool: True if voice profile switched successfully, False otherwise.
        """
        try:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                voice_gender = voice.gender if hasattr(voice, 'gender') else ''
                voice_name = voice.name.lower()
                
                if gender.lower() == 'female' and ('female' in voice_gender.lower() or 'zira' in voice_name or 'hazel' in voice_name):
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"TTSService: Voice profile set to female (ID: {voice.id}).")
                    return True
                elif gender.lower() == 'male' and ('male' in voice_gender.lower() or 'david' in voice_name):
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"TTSService: Voice profile set to male (ID: {voice.id}).")
                    return True
            
            # Fallback if specific gender not found: use the first available voice
            if voices:
                self.engine.setProperty('voice', voices[0].id)
                logger.warning(f"TTSService: Preferred gender '{gender}' not found. Fallback to voice: {voices[0].name}.")
                return True
        except Exception as e:
            logger.error(f"Error setting voice gender: {e}")
        return False

# Top-level standalone helper function as requested
def speak(text: str, rate: int = 185, volume: float = 1.0) -> None:
    """
    Convenience standalone function to quickly speak text using a temporary TTSService instance.

    Args:
        text (str): The text message to speak.
        rate (int): Words per minute.
        volume (float): Speaking volume.
    """
    tts = TTSService(rate=rate, volume=volume)
    tts.speak(text)

if __name__ == '__main__':
    print("Testing TTSService...")
    tts = TTSService()
    tts.speak("Testing standalone text to speech service.")
