import shutil
import os

src = r"C:\Users\user\.gemini\antigravity-ide\brain\166a57d2-0da0-4f93-ae65-a813a6683d53\astra_voice_banner_1781208419203.png"
dst = r"c:\AstraVoice AI Assistant\assets\banner.png"

try:
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
        print("Success: Copied banner image to assets/banner.png")
    else:
        print(f"Error: Source image not found at {src}")
except Exception as e:
    print(f"Error: {e}")
