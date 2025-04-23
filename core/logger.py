import os
import logging
import time
from logging.handlers import RotatingFileHandler
from PyQt6.QtCore import QObject, pyqtSignal


class LogSignals(QObject):
    """Signal emitter for log messages to update UI."""
    new_log = pyqtSignal(str, str)  # (log_level, message)


class BotLogger:
    """Centralized logging system for the bot application."""

    def __init__(self, log_file="bot_log.txt", max_bytes=500000, backup_count=3, log_level=logging.INFO):
        self.logger = logging.getLogger("BotLogger")
        self.logger.setLevel(log_level)

        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Set up file handler with rotation
        log_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(log_level)
        self.logger.addHandler(file_handler)

        # PyQt signal for UI updates
        self.signals = LogSignals()

        # Create a custom handler that emits signals
        self.qt_handler = self.QtLogHandler(self.signals)
        self.qt_handler.setFormatter(log_formatter)
        self.qt_handler.setLevel(log_level)
        self.logger.addHandler(self.qt_handler)

        # Also add console handler by default
        console = logging.StreamHandler()
        console.setLevel(log_level)
        console.setFormatter(log_formatter)
        self.logger.addHandler(console)

    class QtLogHandler(logging.Handler):
        """Custom log handler that emits Qt signals."""

        def __init__(self, signals):
            super().__init__()
            self.signals = signals

        def emit(self, record):
            log_level = record.levelname.lower()
            log_msg = self.format(record)
            self.signals.new_log.emit(log_level, log_msg)

    def info(self, message):
        """Log an info message and print to console."""
        self.logger.info(message)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] {message}")

    def warning(self, message):
        """Log a warning message and print to console."""
        self.logger.warning(message)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [WARNING] {message}")

    def error(self, message, exc_info=None):
        """
        Log an error message and print to console.

        Args:
            message: The error message
            exc_info: Optional exception info tuple (type, value, traceback)
        """
        if exc_info:
            self.logger.error(message, exc_info=exc_info)
            # Print simplified version to console
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {message}: {exc_info[1]}")
        else:
            self.logger.error(message)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {message}")

    def debug(self, message):
        """Log a debug message and print to console."""
        self.logger.debug(message)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [DEBUG] {message}")

    def configure_console_output(self, enabled=True, level=logging.INFO):
        """Configure whether logs should also be output to console."""
        # Remove existing console handlers
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)

        # Add a new console handler if enabled
        if enabled:
            console = logging.StreamHandler()
            console.setLevel(level)
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            console.setFormatter(formatter)
            self.logger.addHandler(console)