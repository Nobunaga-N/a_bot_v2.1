import os
import cv2
import numpy as np
import logging
import time
from typing import Tuple, Optional, List, Dict, Union, Callable


class ImageMatcher:
    """Handles image recognition for game elements."""

    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.logger = logging.getLogger("BotLogger")

        # Cache for loaded templates
        self.templates: Dict[str, np.ndarray] = {}

    def load_template(self, template_name: str) -> Optional[np.ndarray]:
        """
        Loads a template image from the template directory.

        Args:
            template_name: Name of the template file (e.g., "victory.png")

        Returns:
            Loaded template as NumPy array or None if failed
        """
        if template_name in self.templates:
            self.logger.debug(f"Использую кешированный шаблон: {template_name}")
            return self.templates[template_name]

        template_path = os.path.join(self.template_dir, template_name)
        self.logger.debug(f"Загрузка шаблона из: {template_path}")

        if not os.path.exists(template_path):
            self.logger.error(f"🚨 Файл шаблона не найден: {template_path}")
            return None

        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            self.logger.error(f"🚨 Не удалось загрузить шаблон: {template_path}")
            return None

        self.templates[template_name] = template
        self.logger.debug(f"Шаблон {template_name} загружен успешно, размер: {template.shape}")
        return template

    def find_in_screen(self,
                   screen_data: bytes,
                   template_name: str,
                   threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Searches for a template in the screen data.

        Args:
            screen_data: Raw screen capture data
            template_name: Name of the template to find
            threshold: Matching threshold (0-1)

        Returns:
            (x, y) coordinates of the top-left corner of the match or None if not found
        """
        # Convert screen data to OpenCV format
        try:
            screen_array = np.frombuffer(screen_data, dtype=np.uint8)
            screen_img = cv2.imdecode(screen_array, cv2.IMREAD_COLOR)
            if screen_img is None:
                self.logger.error("🚨 Не удалось декодировать изображение экрана")
                return None

            self.logger.debug(f"Размеры скриншота: {screen_img.shape}")
        except Exception as e:
            self.logger.error(f"🚨 Ошибка при обработке данных экрана: {e}")
            return None

        # Load template
        template = self.load_template(template_name)
        if template is None:
            self.logger.error(f"🚨 Не удалось загрузить шаблон: {template_name}")
            return None

        # Perform template matching
        try:
            self.logger.debug(f"Поиск шаблона {template_name} с порогом {threshold}")
            result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            self.logger.debug(f"Результат поиска шаблона {template_name}: max_val={max_val:.2f}, max_loc={max_loc}")

            if max_val >= threshold:
                self.logger.info(
                    f"✅ Найдено изображение ({template_name}) с точностью {max_val:.2f} на координатах {max_loc}")
                return max_loc
            else:
                self.logger.debug(
                    f"❌ Шаблон {template_name} не найден (max_val={max_val:.2f} < threshold={threshold:.2f})")
                return None
        except Exception as e:
            self.logger.error(f"🚨 Ошибка при сопоставлении шаблона: {e}")
            return None

    def wait_for_images(self,
                    screen_provider: Callable[[], Optional[bytes]],
                    image_list: List[str],
                    timeout: int = 90,
                    check_interval: float = 3) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
        """
        Waits for one of the specified images to appear on screen.

        Args:
            screen_provider: Function that returns fresh screen data
            image_list: List of template names to look for
            timeout: Maximum wait time in seconds
            check_interval: Time between checks in seconds

        Returns:
            (image_name, location) of the first matched image or (None, None) if timeout
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            screen_data = screen_provider()
            if screen_data is None:
                time.sleep(check_interval)
                continue

            for image_name in image_list:
                match_location = self.find_in_screen(screen_data, image_name)
                if match_location:
                    self.logger.info(f"🏆 Изображение найдено: {image_name}")
                    return image_name, match_location

            time.sleep(check_interval)

        self.logger.warning("⚠ Таймаут ожидания изображений")
        return None, None

    def detect_keys(self, screen_data: bytes) -> int:
        """
        Детектирует количество ключей, отображаемых на экране победы.

        Args:
            screen_data: Данные снимка экрана

        Returns:
            Количество обнаруженных ключей или 0, если ничего не найдено
        """
        try:
            # Импортируем OCRHelper
            from core.ocr_utils import OCRHelper

            # Создаем OCR Helper при первом использовании
            if not hasattr(self, 'ocr_helper'):
                self.ocr_helper = OCRHelper()

            # Конвертация данных экрана в формат OpenCV
            screen_array = np.frombuffer(screen_data, dtype=np.uint8)
            screen_img = cv2.imdecode(screen_array, cv2.IMREAD_COLOR)
            if screen_img is None:
                self.logger.error("🚨 Не удалось декодировать изображение экрана")
                return 0

            # Сначала находим иконку ключа
            key_icon = self.load_template("key_icon.png")
            if key_icon is None:
                self.logger.warning("⚠ Не найден шаблон ключа (key_icon.png)")
                return 12  # Возвращаем значение по умолчанию

            # Поиск иконки ключа на экране
            result = cv2.matchTemplate(screen_img, key_icon, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            # Если иконка ключа найдена с достаточной уверенностью
            if max_val >= 0.7:
                key_x, key_y = max_loc
                key_width, key_height = key_icon.shape[1], key_icon.shape[0]

                # Определяем область под ключом, где отображается число
                # Делаем область немного шире для лучшего захвата
                number_region_x = max(0, key_x - 10)
                number_region_y = key_y + key_height
                number_region_width = min(key_width + 20, screen_img.shape[1] - number_region_x)
                number_region_height = key_height  # Примерная высота числа

                # Извлекаем область, где должно быть число
                if (number_region_y + number_region_height <= screen_img.shape[0] and
                        number_region_x + number_region_width <= screen_img.shape[1]):
                    number_region = screen_img[
                                    number_region_y:number_region_y + number_region_height,
                                    number_region_x:number_region_x + number_region_width
                                    ]

                    # Используем OCR для распознавания числа
                    keys_count = self.ocr_helper.recognize_number(number_region, default_val=12)
                    return keys_count

                # Если извлечение области не удалось, возвращаем значение по умолчанию
                self.logger.warning("⚠ Не удалось извлечь область с числом ключей")
                return 12  # Разумное значение по умолчанию

            self.logger.debug(f"❌ Иконка ключа не найдена на экране (max_val={max_val:.2f})")
            return 0

        except Exception as e:
            self.logger.error(f"🚨 Ошибка при распознавании количества ключей: {e}")
            return 12  # Возвращаем значение по умолчанию в случае ошибки

    def _estimate_digit(self, contour):
        """
        Simple estimation of a digit based on contour properties.

        Args:
            contour: Contour to analyze

        Returns:
            Estimated digit (0-9)
        """
        # This is a very simplified approach - in practice, you'd want a more robust method
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        # Simple heuristic: ratio of area to perimeter can help distinguish digits
        ratio = area / perimeter if perimeter > 0 else 0

        # Very basic digit estimation
        if ratio < 4:
            return 1  # Likely a thin digit like 1
        elif ratio > 8:
            return 0  # Likely a round digit like 0 or 8
        elif 4 <= ratio < 6:
            return 7  # Could be 7 or 4
        else:
            return 5  # Default to something in the middle

    def _match_digit(self, digit_img, templates):
        """
        Match a digit image against templates.

        Args:
            digit_img: Image of the digit to match
            templates: Dictionary of digit templates

        Returns:
            The best matching digit, or None if no good match found
        """
        best_match = None
        best_score = 0

        for digit, template in templates.items():
            # Resize template to match digit size
            if digit_img.shape[0] > 0 and digit_img.shape[1] > 0:
                resized_template = cv2.resize(template, (digit_img.shape[1], digit_img.shape[0]))

                # Compare the images
                result = cv2.matchTemplate(digit_img, resized_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)

                if max_val > best_score:
                    best_score = max_val
                    best_match = digit

        # Only return a match if the confidence is high enough
        return best_match if best_score > 0.5 else None