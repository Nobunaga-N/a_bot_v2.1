import os
import sys
import json
import logging


def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for development and frozen executables.

    Args:
        relative_path: Path relative to the script or executable

    Returns:
        Absolute path to the resource
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Config:
    """Configuration manager for the application."""

    # Default configuration
    DEFAULT_CONFIG = {
        "adb": {
            "path": "adb.exe" if os.name == "nt" else "adb",
        },
        "bot": {
            "battle_timeout": 120,
            "max_refresh_attempts": 3,
            "check_interval": 3,
            "debug_mode": False,  # Выключен режим отладки
        },
        "license": {
            "directory": os.path.join(os.path.expanduser("~"), ".AOM_Bot"),
        },
        "ui": {
            "theme": "dark",
            "log_level": "INFO",  # Изменен уровень логирования на INFO
        }
    }

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)

                # Update config with loaded values, preserving defaults for missing keys
                self._update_dict(self.config, loaded_config)

                logging.info(f"Configuration loaded from {self.config_file}")
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")

    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)

            logging.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            return False

    def get(self, section, key=None, default=None):
        """
        Get a configuration value.

        Args:
            section: Configuration section
            key: Configuration key (optional)
            default: Default value if key doesn't exist

        Returns:
            Configuration value or entire section if key is None
        """
        if section not in self.config:
            return default

        if key is None:
            return self.config[section]

        return self.config[section].get(key, default)

    def set(self, section, key, value):
        """
        Set a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value
        return True

    def _update_dict(self, target, source):
        """
        Recursively update a dictionary with values from another dictionary.

        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value


# Global configuration instance
config = Config()