import subprocess
import os
import logging

# Get module-specific logger
logger = logging.getLogger("AstraVoice.AppLauncher")

class AppLauncher:
    """
    AppLauncher manages launching standard system applications
    (Chrome, Notepad, Calculator) on Windows using subprocesses.
    It includes error handling for cases where paths or executables are invalid.
    """
    def __init__(self) -> None:
        """
        Initializes the application maps with candidate paths.
        """
        # Map friendly app names to lists of potential executable paths/names
        self.app_map: dict[str, list[str]] = {
            'chrome': [
                'chrome.exe',
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
            ],
            'notepad': [
                'notepad.exe'
            ],
            'calculator': [
                'calc.exe'
            ]
        }
        logger.info("AppLauncher initialized successfully.")

    def launch_app(self, app_name: str) -> bool:
        """
        Attempts to launch the requested application.

        Args:
            app_name (str): Friendly name of the app ('chrome', 'notepad', 'calculator').

        Returns:
            bool: True if launched successfully, False otherwise.
        """
        clean_name = app_name.lower().strip()
        if clean_name not in self.app_map:
            logger.warning(f"AppLauncher: Attempted to launch unsupported app: '{app_name}'")
            return False

        paths = self.app_map[clean_name]
        
        for path in paths:
            try:
                logger.info(f"AppLauncher: Attempting to spawn process for '{clean_name}' using path: {path}")
                
                # Using os.startfile on Windows is safe and avoids shell/cmd injection risks
                if hasattr(os, 'startfile'):
                    os.startfile(path)
                    logger.info(f"AppLauncher: Successfully spawned process via startfile for '{clean_name}' using path: {path}")
                else:
                    proc = subprocess.Popen([path])
                    logger.info(f"AppLauncher: Successfully spawned process (PID: {proc.pid}) for '{clean_name}' using path: {path}")
                
                return True
                
            except FileNotFoundError:
                logger.debug(f"AppLauncher: Path candidate not found: '{path}'. Trying next path.")
                continue
            except PermissionError as e:
                print(f"AppLauncher Error: Insufficient permissions to launch {path}. Details: {e}")
                logger.error(f"AppLauncher: Permission error while attempting to execute '{path}': {e}")
                return False
            except Exception as e:
                print(f"AppLauncher Error: Unexpected error while executing {path}. Details: {e}")
                logger.error(f"AppLauncher: Unexpected exception executing '{path}': {e}")
                return False
                
        logger.error(f"AppLauncher: All path candidates for application '{clean_name}' failed to launch.")
        return False

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Testing AppLauncher...")
    launcher = AppLauncher()
    launcher.launch_app("notepad")
