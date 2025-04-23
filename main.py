import os
import sys
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from config import config, resource_path
from core.logger import BotLogger
from core.adb_controller import AdbController
from core.image_matcher import ImageMatcher
from core.bot_engine import BotEngine
from core.stats_manager import StatsManager
from license.fingerprint import MachineFingerprint
from license.storage import LicenseStorage
from license.validator import LicenseValidator
from gui.main_window import MainWindow
from gui.styles import Styles


def init_logging():
    """Инициализация системы логирования."""
    log_level_str = config.get("ui", "log_level", "INFO")
    log_level = getattr(logging, log_level_str)

    logger = BotLogger(
        log_file=os.path.join(config.get("license", "directory"), "bot_log.txt"),
        max_bytes=500000,
        backup_count=3,
        log_level=log_level
    )

    logging.info(f"Инициализация логгера с уровнем {log_level_str}")
    return logger


def init_license_system():
    """Инициализация системы проверки лицензий."""
    # Получаем пути
    license_dir = config.get("license", "directory")
    public_key_path = resource_path("public.pem")

    # Создаем компоненты
    fingerprint = MachineFingerprint()
    storage = LicenseStorage(license_dir)
    validator = LicenseValidator(storage, fingerprint, public_key_path)

    return validator


def init_stats_manager():
    """Инициализация менеджера статистики."""
    # Получаем каталог
    stats_dir = config.get("license", "directory")

    # Создаем менеджер статистики
    stats_manager = StatsManager(stats_dir)

    logging.info(f"Инициализация менеджера статистики. Каталог: {stats_dir}")
    return stats_manager


def init_bot_engine():
    """Инициализация движка бота."""
    # Получаем конфигурацию
    adb_path = resource_path(config.get("adb", "path", "adb.exe" if os.name == "nt" else "adb"))
    template_dir = resource_path("resources/images")

    # Отладочная информация
    logging.info(f"Путь к ADB: {adb_path}")
    logging.info(f"Шаблоны изображений: {template_dir}")
    logging.info(f"Существует ли папка с шаблонами? {os.path.exists(template_dir)}")

    # Логирование значений конфигурации
    logging.info(f"Загружена конфигурация:")
    logging.info(f"  - Время ожидания боя: {config.get('bot', 'battle_timeout', 120)} сек")
    logging.info(f"  - Макс. попыток обновления: {config.get('bot', 'max_refresh_attempts', 3)}")
    logging.info(f"  - Интервал проверки: {config.get('bot', 'check_interval', 3)} сек")

    if os.path.exists(template_dir):
        template_files = [f for f in os.listdir(template_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        logging.info(f"Найдены шаблоны: {', '.join(template_files)}")

    # Создаем компоненты
    adb_controller = AdbController(adb_path)
    image_matcher = ImageMatcher(template_dir)
    bot_engine = BotEngine(adb_controller, image_matcher)

    return bot_engine


def setup_exception_handler(logger):
    """Настройка глобального обработчика исключений для логирования необработанных исключений."""

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Не логируем прерывание клавиатуры
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error("Необработанное исключение", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


def create_resource_dirs():
    """Создает необходимые каталоги для ресурсов, если они отсутствуют."""
    # Каталоги для ресурсов
    resource_dirs = [
        "resources",
        "resources/images",
        "resources/icons"
    ]

    for dir_path in resource_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logging.info(f"Создан каталог: {dir_path}")

    # Проверка наличия README для иконок
    icons_readme = "resources/icons/README.md"
    if not os.path.exists(icons_readme):
        # Создаем базовый файл README для иконок
        try:
            with open(icons_readme, "w", encoding="utf-8") as f:
                f.write("# SVG-иконки для приложения\n\n")
                f.write("Поместите в эту папку следующие SVG-иконки:\n")
                f.write("- home.svg - Иконка главной страницы\n")
                f.write("- stats.svg - Иконка статистики\n")
                f.write("- settings.svg - Иконка настроек\n")
                f.write("- license.svg - Иконка лицензирования\n")

            logging.info(f"Создан файл с инструкциями по иконкам: {icons_readme}")
        except Exception as e:
            logging.error(f"Ошибка при создании файла README для иконок: {e}")


def main():
    """Основная точка входа в приложение."""
    # Инициализация логирования
    logger = init_logging()
    setup_exception_handler(logger)

    # Логирование запуска приложения
    logger.info("=" * 40)
    logger.info("Запуск Age of Magic Бот v2.0")
    logger.info("=" * 40)

    # Создание каталогов ресурсов
    create_resource_dirs()

    # Создание Qt приложения
    app = QApplication(sys.argv)
    app.setApplicationName("Age of Magic Бот")
    app.setApplicationVersion("2.0")

    # Установка иконки приложения
    app.setWindowIcon(QIcon(resource_path("aom.ico")))

    # Применение стилей
    app.setPalette(Styles.get_dark_palette())
    app.setStyleSheet(Styles.get_base_stylesheet())

    # Инициализация системы лицензирования
    license_validator = init_license_system()

    # Проверка валидности лицензии
    if not license_validator.is_license_valid():
        logger.warning("Лицензия недействительна или отсутствует.")
        # Лицензию теперь можно будет активировать через интерфейс,
        # не нужно блокировать запуск

    # Инициализация движка бота
    bot_engine = init_bot_engine()

    # Инициализация и подключение менеджера статистики к движку бота
    stats_manager = init_stats_manager()
    bot_engine.stats_manager = stats_manager
    bot_engine.stats = stats_manager.current_stats

    # Создание главного окна
    main_window = MainWindow(bot_engine, license_validator)

    # Подключаем сигналы логгера к интерфейсу
    logger.signals.new_log.connect(main_window.append_log)

    main_window.show()

    # Запуск цикла обработки событий приложения
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())