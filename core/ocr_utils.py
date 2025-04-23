import os
import sys
import logging
import numpy as np
import cv2
from PIL import Image
import pytesseract
from pathlib import Path


class OCRHelper:
    """Класс-помощник для работы с OCR."""

    def __init__(self):
        self.logger = logging.getLogger("BotLogger")

        # Пытаемся найти Tesseract
        self.tesseract_path = self._find_tesseract()
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            self.logger.info(f"✅ Tesseract OCR найден: {self.tesseract_path}")
            self.ocr_available = True
        else:
            self.logger.warning("⚠ Tesseract OCR не найден. Будет использоваться приблизительное определение.")
            self.ocr_available = False

    def _find_tesseract(self):
        """Поиск исполняемого файла Tesseract OCR."""
        # Проверяем, запущены ли мы из PyInstaller
        if getattr(sys, 'frozen', False):
            # Если запущены из PyInstaller, ищем в папке рядом с исполняемым файлом
            base_path = Path(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable))
            tesseract_path = base_path / "tesseract" / "tesseract.exe"

            if tesseract_path.exists():
                return str(tesseract_path)

            # Если не нашли в _MEIPASS, проверяем рядом с исполняемым файлом
            app_dir = Path(os.path.dirname(sys.executable))
            tesseract_path = app_dir / "tesseract" / "tesseract.exe"

            if tesseract_path.exists():
                return str(tesseract_path)

        # Стандартные пути установки Tesseract
        standard_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract"
        ]

        # Проверяем стандартные пути
        for path in standard_paths:
            if os.path.isfile(path):
                return path

        # Проверяем наличие в PATH
        try:
            import shutil
            tesseract_path = shutil.which("tesseract")
            if tesseract_path:
                return tesseract_path
        except:
            pass

        return None

    def recognize_number(self, image, min_val=10, max_val=99, default_val=12):
        """
        Распознает число на изображении с помощью OCR.

        Args:
            image: Изображение для распознавания (numpy array)
            min_val: Минимальное допустимое значение
            max_val: Максимальное допустимое значение
            default_val: Значение по умолчанию, если распознавание не удалось

        Returns:
            Распознанное число или значение по умолчанию
        """
        if not self.ocr_available:
            return default_val

        try:
            # Предварительная обработка изображения для лучшего распознавания
            # Увеличиваем размер для лучшего распознавания
            height, width = image.shape[:2]
            image = cv2.resize(image, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)

            # Конвертируем в оттенки серого, если изображение цветное
            if len(image.shape) > 2:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Бинаризация для улучшения распознавания цифр
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Используем morph close для соединения частей символов
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # Конвертируем в PIL Image для pytesseract
            pil_img = Image.fromarray(thresh)

            # Настраиваем Tesseract для распознавания только цифр
            custom_config = r'--oem 3 --psm 6 outputbase digits'

            # Распознавание текста
            result = pytesseract.image_to_string(pil_img, config=custom_config).strip()
            self.logger.debug(f"OCR результат: '{result}'")

            # Извлекаем первое найденное число
            import re
            numbers = re.findall(r'\d+', result)

            if numbers:
                recognized_number = int(numbers[0])
                # Проверяем, находится ли число в допустимых пределах
                if min_val <= recognized_number <= max_val:
                    return recognized_number
                else:
                    self.logger.warning(
                        f"⚠ Распознанное число {recognized_number} вне допустимых пределов [{min_val},{max_val}]")
            else:
                self.logger.warning("⚠ OCR не смог распознать число")

        except Exception as e:
            self.logger.error(f"🚨 Ошибка при OCR-распознавании: {e}")

        # Если что-то пошло не так, возвращаем значение по умолчанию
        return default_val