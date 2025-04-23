import sys
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap

from gui.styles import Styles
from gui.widgets.sidebar_menu import SidebarMenu


class BotSignals(QObject):
    """Сигналы для операций бота и обновлений UI."""
    state_changed = pyqtSignal(str)
    log_message = pyqtSignal(str, str)  # level, message
    error = pyqtSignal(str)
    stats_updated = pyqtSignal(dict)


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self, bot_engine, license_validator):
        super().__init__()

        self.bot_engine = bot_engine
        self.license_validator = license_validator

        # Получаем ссылку на логгер
        self._py_logger = logging.getLogger("BotLogger")

        # Создание и подключение сигналов
        self.signals = BotSignals()
        self.signals.state_changed.connect(self.update_bot_state)
        self.signals.log_message.connect(self.append_log)
        self.signals.error.connect(self.show_error)
        self.signals.stats_updated.connect(self.update_stats)

        # Установка сигналов бота
        self.bot_engine.set_signals(self.signals)

        # Инициализация UI
        self.init_ui()

        # Таймер для обновления времени работы
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_runtime)
        self.stats_timer.start(1000)  # Обновление каждую секунду

        # Таймер для автоматического обновления статистики
        self.stats_update_timer = QTimer(self)
        self.stats_update_timer.timeout.connect(self.auto_update_statistics)
        self.stats_update_timer.start(5000)  # Обновление каждые 5 секунд

        # Переменная для отслеживания изменений в статистике
        self.last_stats_hash = ""

        # Время начала работы бота
        self.start_time = None

    def init_ui(self):
        """Инициализация компонентов интерфейса."""
        self.setWindowTitle("Age of Magic Бот v2.0")
        self.setMinimumSize(1200, 830)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной лейаут
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Боковое меню
        self.sidebar = SidebarMenu()
        self.sidebar.page_changed.connect(self.change_page)
        main_layout.addWidget(self.sidebar)

        # Основная область содержимого
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(self.content_widget)

        # Стек виджетов для отображения разных страниц
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        # Инициализация страниц
        self.init_pages()

        # Статус-бар
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Готово")

        # Обновление информации о лицензии в статус-баре
        self.update_license_status()

    def init_pages(self):
        """Инициализация страниц приложения."""
        # Импортируем все необходимые страницы
        from gui.widgets.home_widget import HomeWidget
        from gui.widgets.stats_widget import StatsWidget
        from gui.widgets.settings_widget import SettingsWidget
        from gui.widgets.license_widget import LicenseWidget

        # Создаём экземпляры страниц
        self.home_widget = HomeWidget(self.bot_engine, self.signals)
        self.stats_widget = StatsWidget(self.bot_engine)
        self.settings_widget = SettingsWidget(self.bot_engine)
        self.license_widget = LicenseWidget(self.license_validator)

        # Добавляем страницы в стек
        self.stack.addWidget(self.home_widget)
        self.stack.addWidget(self.stats_widget)
        self.stack.addWidget(self.settings_widget)
        self.stack.addWidget(self.license_widget)

        # Словарь для отображения ID страниц в индексы стека
        self.page_indices = {
            "home": 0,
            "stats": 1,
            "settings": 2,
            "license": 3
        }

    def change_page(self, page_id):
        """
        Изменяет отображаемую страницу.

        Args:
            page_id (str): ID страницы для отображения
        """
        if page_id in self.page_indices:
            self.stack.setCurrentIndex(self.page_indices[page_id])

            # Обновляем статистику при переходе на страницу статистики
            if page_id == "stats":
                self.refresh_statistics()
                # Более частое обновление на странице статистики
                self.stats_update_timer.stop()
                self.stats_update_timer.setInterval(1000)
                self.stats_update_timer.start()
            else:
                # Стандартный интервал обновления для других страниц
                self.stats_update_timer.stop()
                self.stats_update_timer.setInterval(5000)
                self.stats_update_timer.start()

    def update_bot_state(self, state):
        """
        Обновляет UI для отображения текущего состояния бота.

        Args:
            state (str): Состояние бота
        """
        # Обновление состояния на главной странице
        self.home_widget.update_bot_state(state)

    def append_log(self, level, message):
        """
        Добавляет сообщение в лог.

        Args:
            level (str): Уровень сообщения
            message (str): Текст сообщения
        """
        # Передаем сообщение в лог на главной странице
        self.home_widget.append_log(level, message)

    def update_stats(self, stats):
        """
        Обновляет отображение статистики.

        Args:
            stats (dict): Статистика бота
        """
        # Обновляем статистику на главной странице
        self.home_widget.update_stats(stats)

    def update_runtime(self):
        """Обновляет отображение времени работы."""
        if self.start_time:
            # Обновление времени работы на главной странице
            self.home_widget.update_runtime()

            # Также обновляем статистику от движка бота
            self.update_stats(self.bot_engine.stats)

    def refresh_statistics(self):
        """Обновляет все отображения статистики."""
        # Проверяем, доступен ли stats_manager
        if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
            return

        # Обновляем статистику на странице статистики
        self.stats_widget.refresh_statistics()

    def auto_update_statistics(self):
        """Автоматически обновляет статистику если данные изменились."""
        # Проверяем, доступен ли stats_manager
        if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
            return

        # Обновляем только если мы на вкладке статистики
        if self.stack.currentIndex() == self.page_indices.get("stats", -1):
            # Если бот запущен, проверяем изменение статистики
            if self.bot_engine.running.is_set():
                current_stats = self.bot_engine.stats
                current_hash = hash(frozenset(current_stats.items()))

                if str(current_hash) != self.last_stats_hash:
                    self.last_stats_hash = str(current_hash)
                    self.refresh_statistics()
                    self._py_logger.debug("Автоматическое обновление статистики выполнено (бот запущен)")
            else:
                # Если бот не запущен, обновляем реже
                import time
                current_time = time.time()
                if not hasattr(self, '_last_stats_update') or (
                        current_time - getattr(self, '_last_stats_update', 0)) > 15:
                    self._last_stats_update = current_time
                    self.refresh_statistics()
                    self._py_logger.debug("Автоматическое обновление статистики выполнено (бот остановлен)")

    def show_error(self, message):
        """
        Показывает сообщение об ошибке.

        Args:
            message (str): Текст сообщения об ошибке
        """
        QMessageBox.critical(self, "Ошибка", message)

    def update_license_status(self):
        """Обновляет статус лицензии в статус-баре."""
        if self.license_validator.is_license_valid():
            license_info = self.license_validator.get_license_info()
            days_left = license_info.get("days_left", 0)
            self.statusBar().showMessage(f"Лицензия: Действительна (осталось {days_left} дней)")
        else:
            self.statusBar().showMessage("Лицензия: Недействительна или истекла")

    def closeEvent(self, event):
        """Обработка события закрытия окна."""
        if self.bot_engine.running.is_set():
            reply = QMessageBox.question(
                self,
                "Подтверждение выхода",
                "Бот всё ещё работает. Вы уверены, что хотите выйти?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.bot_engine.stop()
                # Гарантируем сохранение статистики
                if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager is not None:
                    self.bot_engine.stats_manager.save_stats()
                event.accept()
            else:
                event.ignore()
        else:
            # Сохраняем статистику даже если бот не запущен
            if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager is not None:
                self.bot_engine.stats_manager.save_stats()
            event.accept()