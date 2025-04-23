import sys
import logging
import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QStatusBar, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap, QAction

from config import config
from gui.styles import Styles
from gui.widgets.sidebar_menu import SidebarMenu
from gui.widgets.log_widget import LogWidget


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

        # Подключение сигналов между виджетами
        self.connect_widget_signals()

    def init_ui(self):
        """Инициализация компонентов интерфейса."""
        self.setWindowTitle("Age of Magic Бот v2.0")
        self.setMinimumSize(1000, 800)

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

        # Добавление меню
        self.create_menu()

    def create_menu(self):
        """Создание меню приложения."""
        menu_bar = self.menuBar()

        # Меню "Файл"
        file_menu = menu_bar.addMenu("Файл")

        # Пункт "Экспорт статистики"
        export_action = QAction("Экспорт статистики", self)
        export_action.triggered.connect(self.export_statistics)
        file_menu.addAction(export_action)

        # Разделитель
        file_menu.addSeparator()

        # Пункт "Выход"
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Справка"
        help_menu = menu_bar.addMenu("Справка")

        # Пункт "О программе"
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_pages(self):
        """Инициализация страниц приложения."""
        # Импортируем все необходимые страницы
        from gui.widgets.home_widget import HomeWidget
        from gui.widgets.stats_widget import StatsWidget
        from gui.widgets.settings_widget import SettingsWidget
        from gui.widgets.license_widget import LicenseWidget
        from gui.widgets.log_widget import LogWidget

        # Создаём экземпляры страниц
        self.home_widget = HomeWidget(self.bot_engine, self.signals)
        self.stats_widget = StatsWidget(self.bot_engine)
        self.log_widget = LogWidget()
        self.settings_widget = SettingsWidget(self.bot_engine)
        self.license_widget = LicenseWidget(self.license_validator)

        # Добавляем страницы в стек
        self.stack.addWidget(self.home_widget)
        self.stack.addWidget(self.stats_widget)
        self.stack.addWidget(self.log_widget)
        self.stack.addWidget(self.settings_widget)
        self.stack.addWidget(self.license_widget)

        # Словарь для отображения ID страниц в индексы стека
        self.page_indices = {
            "home": 0,
            "stats": 1,
            "logs": 2,
            "settings": 3,
            "license": 4
        }

    def connect_widget_signals(self):
        """Подключение сигналов между виджетами."""
        # Подключаем сигнал изменения цели по ключам от настроек к домашнему экрану
        self.settings_widget.target_keys_changed.connect(self.home_widget.set_target_keys)

        # Загружаем начальное значение цели из конфигурации
        target_keys = config.get("bot", "target_keys", 1000)
        self.home_widget.set_target_keys(target_keys)

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
        # Передаем сообщение в лог на главной странице и в виджет логов
        self.home_widget.append_log(level, message)
        self.log_widget.append_log(level, message)

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

    def export_statistics(self):
        """Экспортирует статистику в CSV файл."""
        # Проверяем, доступен ли stats_manager
        if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
            QMessageBox.warning(self, "Экспорт невозможен", "Статистика недоступна для экспорта.")
            return

        # Запрашиваем имя файла для сохранения
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт статистики",
            f"AoM_Bot_Stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not filename:
            return  # Пользователь отменил сохранение

        try:
            # Получаем данные для экспорта
            daily_stats = self.bot_engine.stats_manager.get_daily_stats(30)  # Берем статистику за 30 дней
            total_stats = self.bot_engine.stats_manager.get_total_stats()

            # Создаем CSV файл
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Записываем заголовок
                writer.writerow([
                    "Дата", "Боёв", "Победы", "Поражения", "% побед",
                    "Ключей собрано", "Ключей за победу", "Потери связи", "Ошибки"
                ])

                # Записываем ежедневную статистику
                for day in daily_stats:
                    battles = day["stats"]["victories"] + day["stats"]["defeats"]
                    win_rate = day.get("win_rate", 0)
                    keys_per_victory = day.get("keys_per_victory", 0)

                    writer.writerow([
                        day["date"],
                        battles,
                        day["stats"]["victories"],
                        day["stats"]["defeats"],
                        f"{win_rate:.1f}",
                        day["stats"]["keys_collected"],
                        f"{keys_per_victory:.1f}",
                        day["stats"]["connection_losses"],
                        day["stats"]["errors"]
                    ])

                # Пустая строка-разделитель
                writer.writerow([])

                # Записываем итоговую статистику
                writer.writerow(["ИТОГО:"])
                battles_total = total_stats["victories"] + total_stats["defeats"]
                win_rate_total = (total_stats["victories"] / battles_total) * 100 if battles_total > 0 else 0
                keys_per_victory_total = (total_stats["keys_collected"] / total_stats["victories"]) if total_stats[
                                                                                                           "victories"] > 0 else 0

                writer.writerow([
                    "Всего",
                    battles_total,
                    total_stats["victories"],
                    total_stats["defeats"],
                    f"{win_rate_total:.1f}",
                    total_stats["keys_collected"],
                    f"{keys_per_victory_total:.1f}",
                    total_stats["connection_losses"],
                    total_stats["errors"]
                ])

            QMessageBox.information(
                self,
                "Экспорт завершен",
                f"Статистика успешно экспортирована в файл:\n{filename}"
            )

        except Exception as e:
            self._py_logger.error(f"Ошибка при экспорте статистики: {e}")
            import traceback
            self._py_logger.error(traceback.format_exc())

            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось экспортировать статистику: {str(e)}"
            )

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

    def show_about(self):
        """Показывает диалог с информацией о программе."""
        QMessageBox.about(
            self,
            "О программе",
            f"""<h2>Age of Magic Bot v2.0</h2>
            <p>Бот для автоматизации боев в игре Age of Magic</p>
            <p>© 2025</p>
            <p>Все права защищены.</p>
            <p><b>Технологии:</b> Python, PyQt6, OpenCV</p>"""
        )

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