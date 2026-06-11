# AstraVoice AI Assistant - Comprehensive Testing Checklist

This checklist defines manual test scenarios to verify each module of the AstraVoice AI Assistant.

---

## 📋 Pre-Test Setup
- [ ] Ensure python 3.10+ is installed on the host.
- [ ] Connect a working microphone and speakers/headset.
- [ ] Verify environment variables are configured in `.env`.
- [ ] Run dependency installation:
  ```bash
  pip install -r requirements.txt
  ```

---

## 🎙️ Module 1: Speech Recognition
- [ ] Launch `python app.py` and confirm visual startup output is printed.
- [ ] Speak clearly when the console prints `Listening...`.
- [ ] Verify that when speaking finishes, the state transitions to `Processing...`.
- [ ] Verify that transcription is processed successfully, printing `Command Recognized` and the transcribed text.
- [ ] Test silent input (remain quiet for 10 seconds):
  - Verify that the assistant handles it gracefully, printing: *"Error: Google Speech Recognition could not understand the audio."*

---

## 🔊 Module 2: Text-To-Speech (TTS)
- [ ] Verify that on startup, the assistant says: *"AstraVoice AI Assistant is ready. Speak into your microphone."*
- [ ] Speak a command that is not supported (e.g. *"Hello world"*).
  - Verify that the speaker speaks back: *"I heard you say: hello world. However, that command is not supported yet."*
- [ ] Test voice rate and volume:
  - Run `python services/tts_service.py` to trigger the standalone rate and volume tests. Confirm that voice output speed and levels change as logged.

---

## 🌤️ Module 3: Weather Assistant
- [ ] **Test default city lookup**:
  - Speak: *"What is the weather today?"* or *"weather"*
  - Verify that the assistant prints and speaks details for the default city (`Mumbai`).
- [ ] **Test specific city weather**:
  - Speak: *"Weather in Pune"*
  - Verify that weather details (temperature, humidity, wind speed, sky conditions) are printed and spoken.
- [ ] **Test temperature query**:
  - Speak: *"Temperature in Delhi"*
  - Verify that details are parsed and read aloud.
- [ ] **Test invalid city query** (requires active OpenWeatherMap API key):
  - Speak: *"Weather in Atlantis"*
  - Verify that the assistant handles the error and speaks: *"Sorry, I could not retrieve the weather details for Atlantis."*

---

## 📰 Module 4: News Reader
- [ ] **Test general news**:
  - Speak: *"Read the news"*
  - Verify that 5 general headlines and their sources are printed on screen and read aloud sequentially.
- [ ] **Test Technology news**:
  - Speak: *"Technology news"* or *"news in technology"*
  - Verify that technology-related headlines (e.g., TechCrunch, Wired) are displayed and read.
- [ ] **Test Sports news**:
  - Speak: *"Read sports news"*
  - Verify that sports headlines are displayed and read.
- [ ] **Test Business news**:
  - Speak: *"Give me business news"*
  - Verify that business headlines are displayed and read.

---

## ⏰ Module 5: Reminder System
- [ ] **Test relative reminder (seconds)**:
  - Speak: *"Remind me in 10 seconds to stretch"*
  - Verify confirmation matches target time.
  - Verify that after 10 seconds, the voice alert triggers: *"Reminder alert: Stretch."*
- [ ] **Test relative reminder (minutes)**:
  - Speak: *"Remind me in 2 minutes to drink water"*
  - Verify confirmation is spoken, and it triggers exactly after 120 seconds.
- [ ] **Test absolute reminder (clock time)**:
  - Target a time 1-2 minutes in the future (e.g., if current time is 8:45 PM, say: *"Remind me at 8:47 PM to check logs"*).
  - Verify that it registers and triggers precisely on the clock.
- [ ] **Test persistence check**:
  - Add a reminder for 1 minute in the future.
  - Close the app (`Ctrl+C`), verify `memory/reminders.json` holds the record.
  - Restart the app, verify that the reminder triggers when due.

---

## 🚀 Module 6: Application Launcher
- [ ] **Test Notepad**:
  - Speak: *"Open Notepad"*
  - Verify the console prints: *"Opening Notepad"* and the Notepad program launches.
- [ ] **Test Calculator**:
  - Speak: *"Open Calculator"*
  - Verify the Calculator application opens.
- [ ] **Test Chrome**:
  - Speak: *"Open Chrome"*
  - Verify Google Chrome launches.
- [ ] **Test error response**:
  - Speak: *"Open unknown_app"*
  - Verify that the assistant outputs the default fallback response: *"I heard you say: open unknown_app. However, that command is not supported yet."*

---

## 📜 Module 7: Command History
- [ ] **Test history logging**:
  - Speak some commands, then open `memory/command_history.json` to confirm each query is appended with its timestamp.
- [ ] **Test viewing history**:
  - Speak: *"View history"* or *"Show history"*
  - Verify that the full list is printed to the console.
  - Verify that the assistant speaks a summary and reads the 3 most recent queries aloud.
- [ ] **Test clearing history**:
  - Speak: *"Clear history"* or *"Delete history"*
  - Verify that the assistant speaks: *"Command history cleared successfully."*
  - Verify that `memory/command_history.json` is updated to `[]` (empty list).

---

## 📁 System Logs & Code Quality
- [ ] **Verify logger output**:
  - Open `logs/astra_voice.log` and verify that startup sequences, speech transcripts, API fetches, reminders, and application launch events are logged with timestamps and logger module tags.
- [ ] **Verify syntax errors**:
  - Compile the scripts to check for import or formatting issues:
    ```bash
    python -m py_compile app.py services/*.py
    ```
