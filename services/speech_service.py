import sys
import logging
from typing import Optional
import speech_recognition as sr

# Get module-specific logger
logger = logging.getLogger("AstraVoice.SpeechService")

class SpeechService:
    """
    SpeechService handles speech-to-text conversion using the SpeechRecognition library.
    It reads input from the default microphone, performs ambient noise adjustment,
    displays status logs on stdout, and handles exceptions.
    """
    def __init__(self) -> None:
        """
        Initializes the SpeechRecognition Recognizer instance with optimized settings.
        """
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300       # Solid default initial baseline
        self.recognizer.pause_threshold = 1.2          # Natural pauses without early cut-offs
        self.recognizer.operation_timeout = 6.0        # Timeout for API requests to Google
        logger.info("SpeechService initialized successfully with calibrated parameters.")

    def listen_and_recognize(self, max_retries: int = 2) -> Optional[str]:
        """
        Listens to microphone input, converts the speech to text,
        and returns the recognized text. Includes an automatic retry mechanism.

        Args:
            max_retries (int): Maximum capture attempts. Default is 2.

        Returns:
            Optional[str]: The recognized text string if successful, None otherwise.
        """
        for attempt in range(1, max_retries + 1):
            try:
                # Set up default microphone source
                with sr.Microphone() as source:
                    logger.info(f"Accessing default microphone (Attempt {attempt}/{max_retries}).")
                    
                    # Calibrate ambient noise: longer on retry, swift on first attempt
                    if attempt > 1:
                        logger.info("Unintelligible capture on previous attempt. Recalibrating acoustics...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=1.2)
                    else:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                    
                    # Show status: Listening...
                    print("Listening...")
                    sys.stdout.flush()
                    
                    # Listen to user's speech input
                    audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
                    logger.info("Audio capture complete.")
                    
                    # Show status: Processing...
                    print("Processing...")
                    sys.stdout.flush()
                    
                    # Convert speech to text
                    recognized_text = self.recognizer.recognize_google(audio)
                    
                    # Show status: Command Recognized
                    print("Command Recognized")
                    sys.stdout.flush()
                    
                    # Log metadata (length/word count) instead of the raw transcription string to protect user privacy
                    word_count = len(recognized_text.split())
                    logger.info(f"Google Speech Recognition transcription successful (length: {word_count} words)")
                    return recognized_text
                    
            except sr.WaitTimeoutError:
                print(f"Warning: Silent timeout on attempt {attempt}.")
                sys.stdout.flush()
                logger.warning(f"Audio capture timed out (Attempt {attempt}).")
                if attempt == max_retries:
                    return None
                    
            except sr.UnknownValueError:
                print(f"Warning: Unintelligible speech on attempt {attempt}.")
                sys.stdout.flush()
                logger.warning(f"Speech was unintelligible (Attempt {attempt}).")
                if attempt == max_retries:
                    return None
                    
            except sr.RequestError as e:
                print(f"\nError: Could not request results from Google Speech Recognition service; {e}")
                sys.stdout.flush()
                logger.error(f"Speech recognition service request error: {e}")
                return None
                
            except OSError as e:
                print(f"\nError: Microphone error. Details: {e}")
                sys.stdout.flush()
                logger.error(f"Microphone access error: {e}")
                return None
                
            except Exception as e:
                print(f"\nAn unexpected error occurred in speech service: {e}")
                sys.stdout.flush()
                logger.error(f"Unexpected error in SpeechService: {e}")
                return None

if __name__ == '__main__':
    # Standalone verification block
    logging.basicConfig(level=logging.INFO)
    print("=== AstraVoice Speech Service Test ===")
    print("Press Ctrl+C to exit.")
    service = SpeechService()
    try:
        while True:
            print("\n--- Start Speaking ---")
            txt = service.listen_and_recognize()
            print(f"Result: {txt}")
    except KeyboardInterrupt:
        print("\nExiting.")
