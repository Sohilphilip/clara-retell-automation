import os
from datetime import datetime

# Get log path from environment variable or default
LOG_PATH = os.getenv("LOG_PATH", "./logs")

# Ensure logs directory exists
os.makedirs(LOG_PATH, exist_ok=True)

# Log file name (daily log file)
LOG_FILE = os.path.join(
    LOG_PATH,
    f"log_{datetime.now().strftime('%Y-%m-%d')}.txt"
)


def log(message: str):
    """
    Writes a timestamped log message to the log file.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted_message)

    print(formatted_message.strip())