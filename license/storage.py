import os
import logging
import datetime


class LicenseStorage:
    """Handles storage and retrieval of license information."""

    def __init__(self, base_dir):
        self.logger = logging.getLogger("BotLogger")

        # Create license directory if it doesn't exist
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)

        # Define file paths
        self.license_file = os.path.join(self.base_dir, "license.txt")
        self.last_run_file = os.path.join(self.base_dir, "last_run.txt")

    def save_license(self, license_data):
        """
        Save license data to the license file.

        Args:
            license_data (str): License data to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.license_file, "w", encoding="utf-8") as f:
                f.write(license_data)
            return True
        except Exception as e:
            self.logger.error(f"Error saving license data: {e}")
            return False

    def load_license(self):
        """
        Load license data from the license file.

        Returns:
            str or None: License data if available, None otherwise
        """
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.error(f"Error loading license data: {e}")
        return None

    def update_last_run_time(self):
        """
        Update the last run time to the current UTC time.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            now_utc = datetime.datetime.utcnow()
            with open(self.last_run_file, "w", encoding="utf-8") as f:
                f.write(now_utc.isoformat())
            return True
        except Exception as e:
            self.logger.error(f"Error updating last run time: {e}")
            return False

    def get_last_run_time(self):
        """
        Get the last run time from the last run file.

        Returns:
            datetime or None: Last run time if available, None otherwise
        """
        if os.path.exists(self.last_run_file):
            try:
                with open(self.last_run_file, "r", encoding="utf-8") as f:
                    last_run_str = f.read().strip()
                return datetime.datetime.fromisoformat(last_run_str)
            except Exception as e:
                self.logger.error(f"Error getting last run time: {e}")
        return None