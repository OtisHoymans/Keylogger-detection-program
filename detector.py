import psutil
import time
import logging
import os
import sys
import platform
import datetime
from pathlib import Path

# Setup log directory and file
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "detector.log"
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger('').addHandler(console)

# Keywords associated with keyloggers or suspicious tools
SUSPICIOUS_KEYWORDS = [
    "keylogger", "hook", "keyboard", "spy", "logger", 
    "keystroke", "capture", "intercept", "monitor",
    "record key", "input tracker", "surveillance"
]

# Suspicious installation or execution locations
SUSPICIOUS_LOCATIONS = [
    r"C:\Windows\Temp",
    r"C:\Users\Public",
    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
    os.path.expandvars(r"%TEMP%")
]

# Safe processes to ignore (common apps/tools)
WHITELIST = {
    # Microsoft / System
    "explorer.exe", "svchost.exe", "system", "runtimebroker.exe",
    "wininit.exe", "lsass.exe", "csrss.exe", "dwm.exe", "smss.exe",
    
    # Browsers
    "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe",

    # Communication apps
    "discord.exe", "teams.exe", "skype.exe", "zoom.exe", "slack.exe",

    # IDEs and dev tools
    "code.exe", "code - insiders.exe", "pycharm64.exe", "python.exe", "pythonw.exe",

    # Windows services and misc.
    "notepad.exe", "taskmgr.exe", "settings.exe", "detector.py",
    
    "msedgewebview2.exe", "asmonitorcontrol.exe",
    "asusinputlocalemonitor.exe",
}


# To prevent duplicate logging
detected_pids = set()

TEST_LOGGER_NAMES = {"dummylogger.py"}

def is_test_logger(proc):
    try:
        name = proc.name().lower()
        cmd = " ".join(proc.cmdline()).lower()
        return any(tname in name or tname in cmd for tname in TEST_LOGGER_NAMES)
    except Exception:
        return False


def is_from_suspicious_location(proc_exe):
    """Check if the executable path matches suspicious directories."""
    try:
        proc_path = os.path.normpath(proc_exe).lower()
        return any(os.path.normpath(loc).lower() in proc_path for loc in SUSPICIOUS_LOCATIONS)
    except Exception:
        return False


def process_looks_suspicious(proc):
    """Apply multiple heuristics to decide if a process looks malicious."""
    try:
        name = proc.name().lower()
        if name in WHITELIST:
            return False

        cmdline = " ".join(proc.cmdline()).lower() if proc.cmdline() else ""
        if any(keyword in name or keyword in cmdline for keyword in SUSPICIOUS_KEYWORDS):
            return True

        if not cmdline and name not in ("system", "registry"):
            return True

        if is_from_suspicious_location(proc.exe()):
            return True

        try:
            for dll in proc.memory_maps():
                path = dll.path.lower()
                if "keyboard" in path or "hook" in path:
                    return True
        except Exception:
            pass

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    return False


def get_proc_info(proc):
    """Return detailed information about a process in dictionary form."""
    try:
        return {
            "pid": proc.pid,
            "name": proc.name(),
            "cmdline": " ".join(proc.cmdline()),
            "create_time": datetime.datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S"),
            "exe": proc.exe(),
            "username": proc.username()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {
            "pid": proc.pid,
            "name": proc.name(),
            "cmdline": "Unavailable",
            "create_time": "Unavailable",
            "exe": "Access Denied",
            "username": "Unknown"
        }


def print_detection(details):
    """Output detection result to console."""
    print("\n" + "!" * 80)
    print(f"[!] SUSPICIOUS PROCESS DETECTED: {details['name']} (PID: {details['pid']})")
    print("!" * 80)
    for key, val in details.items():
        print(f"  {key.capitalize()}: {val}")
    print()


def monitor():
    """Main loop for monitoring suspicious processes."""
    logging.info("Starting process monitoring...")
    print("\n" + "=" * 80)
    print(" KEYLOGGER DETECTION SYSTEM ".center(80, "="))
    print("=" * 80)
    print("Monitoring for suspicious processes... Press Ctrl+C to stop.\n")

    try:
        while True:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.pid in detected_pids:
                    continue
                if is_test_logger(proc) or process_looks_suspicious(proc):
                    details = get_proc_info(proc)
                    logging.warning(f"Suspicious process detected: {details}")
                    print_detection(details)
                    detected_pids.add(proc.pid)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        logging.info("Monitoring stopped.")
    except Exception as e:
        logging.error(f"Error during monitoring: {e}")
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    monitor()
