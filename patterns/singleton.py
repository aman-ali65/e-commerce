import os
from datetime import datetime


class Logger:
    """Singleton Logger — only one instance ever exists."""

    _instance = None
    LOG_FILE = "data/app.log"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        os.makedirs("data", exist_ok=True)

    def _write(self, level: str, msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level:<7}] {msg}"
        print(line)
        with open(self.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def info(self, msg: str):
        self._write("INFO", msg)

    def warning(self, msg: str):
        self._write("WARNING", msg)

    def error(self, msg: str):
        self._write("ERROR", msg)

    def success(self, msg: str):
        self._write("SUCCESS", msg)
