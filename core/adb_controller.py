import os
import subprocess
import random
import logging
from typing import Tuple, Optional


class AdbController:
    """Handles communication with the Android device via ADB."""

    def __init__(self, adb_path: str):
        self.adb_path = adb_path
        self.logger = logging.getLogger("BotLogger")

        # Set creation flags based on OS
        self.creation_flags = 0
        if os.name == 'nt':
            self.creation_flags = subprocess.CREATE_NO_WINDOW

    def check_connection(self) -> bool:
        """Checks if ADB is connected to a device."""
        try:
            self.logger.info(f"Проверка соединения ADB. Путь к ADB: {self.adb_path}")

            result = subprocess.run(
                [self.adb_path, "devices"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=5, creationflags=self.creation_flags
            )
            output = result.stdout.decode("utf-8")
            error = result.stderr.decode("utf-8") if result.stderr else ""

            self.logger.info(f"ADB devices вывод: {output}")
            if error:
                self.logger.warning(f"ADB devices ошибка: {error}")

            if "device" in output and "List of devices" in output:
                # Check if any actual device is listed
                lines = output.strip().split('\n')
                if len(lines) > 1:  # More than just the header line
                    self.logger.info("✅ ADB подключение успешно. Устройство найдено.")
                    return True
                else:
                    self.logger.info("🚨 ADB запущен, но устройства не обнаружены.")
            else:
                self.logger.info("🚨 ADB не обнаружил устройство.")
        except Exception as e:
            self.logger.error(f"🚨 Ошибка при проверке подключения adb: {e}")
        return False

    def tap(self, x: int, y: int, add_randomness: bool = True) -> bool:
        """
        Send a tap command to the device.

        Args:
            x: X coordinate
            y: Y coordinate
            add_randomness: If True, adds small random offsets to coordinates

        Returns:
            True if tap was successful, False otherwise
        """
        if add_randomness:
            x_offset = random.randint(-5, 5)
            y_offset = random.randint(-5, 5)
            x += x_offset
            y += y_offset

        try:
            subprocess.run(
                [self.adb_path, "shell", "input", "tap", str(x), str(y)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=True, timeout=5, creationflags=self.creation_flags
            )
            self.logger.info(f"Нажатие отправлено на координаты ({x}, {y})")
            return True
        except subprocess.TimeoutExpired:
            self.logger.error("🚨 Таймаут ADB нажатия: Команда не завершилась вовремя")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"🚨 Ошибка ADB нажатия: {e}")
        except Exception as e:
            self.logger.error(f"🚨 Непредвиденная ошибка при нажатии: {e}")
        return False

    def capture_screen(self) -> Optional[bytes]:
        """
        Captures the current screen via ADB.

        Returns:
            Raw screen data as bytes or None if failed
        """
        for attempt in range(3):
            try:
                self.logger.debug(f"Попытка захвата экрана #{attempt + 1}")

                process = subprocess.Popen(
                    [self.adb_path, "shell", "screencap", "-p"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    creationflags=self.creation_flags
                )

                try:
                    screen_data, stderr = process.communicate(timeout=5)

                    if stderr:
                        stderr_text = stderr.decode('utf-8', errors='ignore')
                        self.logger.warning(f"Предупреждение при захвате экрана: {stderr_text}")

                    if not screen_data or len(screen_data) < 100:  # Слишком маленький размер для валидного изображения
                        self.logger.error(
                            f"Получены некорректные данные экрана, размер: {len(screen_data) if screen_data else 0} байт")
                        continue

                except subprocess.TimeoutExpired:
                    process.kill()
                    screen_data, stderr = process.communicate()
                    self.logger.error(f"🚨 Таймаут при захвате экрана (попытка {attempt + 1})")
                    continue

                screen_data = screen_data.replace(b'\r\n', b'\n')

                self.logger.debug(f"Захват экрана успешен, размер данных: {len(screen_data)} байт")
                return screen_data

            except Exception as e:
                self.logger.error(f"🚨 Ошибка при захвате экрана (попытка {attempt + 1}): {e}")

            # Небольшая задержка перед следующей попыткой
            import time
            time.sleep(1)

        self.logger.error("🚨 Ошибка: Не удалось загрузить изображение из ADB после нескольких попыток.")
        return None