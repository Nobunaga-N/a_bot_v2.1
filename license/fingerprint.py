import uuid
import hashlib
import logging


class MachineFingerprint:
    """Generates a unique machine fingerprint for license validation."""

    def __init__(self, salt="static_salt_value_123"):
        self.salt = salt
        self.logger = logging.getLogger("BotLogger")

    def generate(self):
        """
        Generates a unique machine fingerprint based on hardware information.

        Returns:
            str: Hexadecimal string representing the machine fingerprint
        """
        try:
            # Get the MAC address
            mac = uuid.getnode()
            mac_str = f"{mac:012x}"

            # Combine with salt
            unique_data = mac_str + self.salt

            # Generate hash
            fingerprint = hashlib.sha256(unique_data.encode()).hexdigest()

            return fingerprint
        except Exception as e:
            self.logger.error(f"Error generating machine fingerprint: {e}")
            return None