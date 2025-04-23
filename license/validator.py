import os
import base64
import datetime
import logging
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

from .fingerprint import MachineFingerprint
from .storage import LicenseStorage


class LicenseValidator:
    """Validates license information for the application."""

    def __init__(self, storage, fingerprint, public_key_path):
        self.storage = storage
        self.fingerprint = fingerprint
        self.public_key_path = public_key_path
        self.logger = logging.getLogger("BotLogger")

    def check_local_time_tampering(self):
        """
        Check if the local time has been tampered with.

        Returns:
            bool: True if no tampering detected, False otherwise
        """
        now_utc = datetime.datetime.utcnow()
        last_run_time = self.storage.get_last_run_time()

        if last_run_time is not None and now_utc < last_run_time:
            self.logger.warning("Системное время было отмотано назад! Блокировка операции.")
            return False

        return True

    def verify_license(self, compact_key):
        """
        Verify a license key.

        Args:
            compact_key (str): Base64-encoded license key

        Returns:
            bool: True if license is valid, False otherwise
        """
        try:
            # Check for time tampering
            if not self.check_local_time_tampering():
                return False

            # Decode license data
            decoded = base64.b64decode(compact_key).decode()
            parts = decoded.split("|", 1)
            if len(parts) != 2:
                self.logger.error("Неверный формат лицензии")
                return False

            exp_str, sig_b64 = parts[0], parts[1]

            # Check expiration date
            now_utc = datetime.datetime.utcnow()
            exp_date = datetime.datetime.fromisoformat(exp_str)
            if now_utc > exp_date:
                self.logger.warning("Срок действия лицензии истек")
                return False

            # Verify signature
            user_fingerprint = self.fingerprint.generate()
            message = user_fingerprint + "|" + exp_str
            h = SHA256.new(message.encode())

            # Load public key
            with open(self.public_key_path, "rb") as f:
                public_key = RSA.import_key(f.read())

            # Decode signature
            signature = base64.b64decode(sig_b64)

            # Verify signature
            pkcs1_15.new(public_key).verify(h, signature)

            # Update last run time
            self.storage.update_last_run_time()

            return True
        except Exception as e:
            self.logger.error(f"Ошибка проверки лицензии: {e}")
            return False

    def is_license_valid(self):
        """
        Check if the stored license is valid.

        Returns:
            bool: True if license is valid, False otherwise
        """
        compact_key = self.storage.load_license()
        if compact_key and self.verify_license(compact_key):
            return True
        return False

    def get_license_info(self):
        """
        Get information about the current license.

        Returns:
            dict: License information
        """
        compact_key = self.storage.load_license()
        if not compact_key:
            return {
                "status": "missing",
                "expiration": None,
                "days_left": 0
            }

        try:
            # Decode license data
            decoded = base64.b64decode(compact_key).decode()
            parts = decoded.split("|", 1)
            if len(parts) != 2:
                return {
                    "status": "invalid",
                    "expiration": None,
                    "days_left": 0
                }

            exp_str = parts[0]
            exp_date = datetime.datetime.fromisoformat(exp_str)
            now_utc = datetime.datetime.utcnow()

            days_left = (exp_date - now_utc).days

            if now_utc > exp_date:
                return {
                    "status": "expired",
                    "expiration": exp_date,
                    "days_left": 0
                }

            if self.verify_license(compact_key):
                return {
                    "status": "valid",
                    "expiration": exp_date,
                    "days_left": days_left
                }
            else:
                return {
                    "status": "invalid",
                    "expiration": exp_date,
                    "days_left": days_left
                }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о лицензии: {e}")
            return {
                "status": "error",
                "expiration": None,
                "days_left": 0
            }