import sys
import logging
import time
import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QStatusBar, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap, QAction
from functools import wraps

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
    license_updated = pyqtSignal()


def safe_stats_operation(default_return=None):
    """Декоратор для безопасных операций со статистикой."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
                self._py_logger.warning(f"StatsManager недоступен для {func.__name__}")
                return default_return
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self._py_logger.error(f"Ошибка в {func.__name__}: {e}")
                return default_return

        return wrapper

    return decorator


class OptimizedTimerManager:
    """Оптимизированный менеджер таймеров."""

    def __init__(self, main_window):
        self.main_window = main_window
        self._py_logger = main_window._py_logger

        # Основные таймеры
        self.runtime_timer = QTimer(main_window)
        self.stats_update_timer = QTimer(main_window)

        # Настройка таймеров
        self.runtime_timer.timeout.connect(main_window.update_runtime)
        self.stats_update_timer.timeout.connect(main_window.auto_update_statistics)

        self._py_logger.debug("OptimizedTimerManager инициализирован")

    def start_timers(self):
        """Запускает все таймеры."""
        self.runtime_timer.start(1000)  # Обновление времени каждую секунду
        self.stats_update_timer.start(8000)  # УВЕЛИЧИЛИ интервал до 8 секунд
        self._py_logger.debug("Таймеры запущены")

    def adjust_for_page(self, page_id: str):
        """Настраивает таймеры в зависимости от активной страницы."""
        if page_id == "stats":
            # Более частое обновление на странице статистики
            self.stats_update_timer.setInterval(5000)  # Каждые 5 секунд
        else:
            # Стандартная частота для других страниц
            self.stats_update_timer.setInterval(8000)  # Каждые 8 секунд


class OptimizedUpdateManager:
    """Оптимизированный менеджер обновлений."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.bot_engine = main_window.bot_engine
        self._py_logger = main_window._py_logger

        # Кэш последнего хеша статистики для избежания лишних обновлений
        self.last_stats_hash = ""

    def should_update_stats(self):
        """Проверяет, нужно ли обновлять статистику."""
        if not self.bot_engine.running.is_set():
            return False

        is_registered = getattr(self.bot_engine, 'session_stats_registered', False)
        if is_registered:
            return False

        # Проверяем изменения в статистике
        current_stats = self.bot_engine.stats
        current_hash = hash(frozenset(current_stats.items()))

        if str(current_hash) != self.last_stats_hash:
            self.last_stats_hash = str(current_hash)
            return True

        return False

    @safe_stats_operation()
    def update_stats_if_changed(self):
        """Обновляет статистику если данные изменились."""
        if not self.should_update_stats():
            return

        # Обновляем только карточки и таблицы, не графики
        if hasattr(self.main_window, 'stats_widget') and self.main_window.stats_widget._is_currently_visible:
            self.main_window.stats_widget.update_stats_cards()
            self.main_window.stats_widget.update_daily_stats_table()
            self._py_logger.debug("Статистика обновлена (изменения обнаружены)")

    @safe_stats_operation()
    def update_progress_if_needed(self):
        """Обновляет прогресс-бар если необходимо."""
        # Только для главной страницы
        if self.main_window.stack.currentIndex() != self.main_window.page_indices.get("home", -1):
            return

        home_widget = self.main_window.home_widget
        if hasattr(home_widget, 'update_stats'):
            home_widget.update_stats(self.bot_engine.stats)


class ExportManager:
    """Менеджер экспорта данных."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.bot_engine = main_window.bot_engine
        self._py_logger = main_window._py_logger

    @safe_stats_operation()
    def export_statistics(self):
        """Экспортирует статистику в CSV файл."""
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Экспорт статистики",
            f"AoM_Bot_Stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not filename:
            return

        try:
            # Получаем данные
            daily_stats = self.bot_engine.stats_manager.get_daily_stats(30)
            total_stats = self.bot_engine.stats_manager.get_total_stats()

            # Экспортируем в CSV
            self._write_csv_file(filename, daily_stats, total_stats)

            QMessageBox.information(
                self.main_window,
                "Экспорт завершен",
                f"Статистика успешно экспортирована в файл:\n{filename}"
            )

        except Exception as e:
            self._py_logger.error(f"Ошибка при экспорте статистики: {e}")
            QMessageBox.critical(
                self.main_window,
                "Ошибка экспорта",
                f"Не удалось экспортировать статистику: {str(e)}"
            )

    def _write_csv_file(self, filename, daily_stats, total_stats):
        """Записывает данные в CSV файл."""
        import csv

        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Заголовок
            writer.writerow([
                "Дата", "Боёв", "Победы", "Поражения", "% побед",
                "Ключей собрано", "Ключей за победу", "Серебра собрано", "Потери связи", "Ошибки"
            ])

            # Ежедневные данные
            for day in daily_stats:
                battles = day["stats"]["victories"] + day["stats"]["defeats"]
                win_rate = day.get("win_rate", 0)
                keys_per_victory = day.get("keys_per_victory", 0)
                silver_collected = day["stats"].get("silver_collected", 0)
                silver_formatted = f"{silver_collected:.1f}K" if silver_collected > 0 else "0K"

                writer.writerow([
                    day["date"], battles, day["stats"]["victories"], day["stats"]["defeats"],
                    f"{win_rate:.1f}", day["stats"]["keys_collected"], f"{keys_per_victory:.1f}",
                    silver_formatted, day["stats"]["connection_losses"], day["stats"]["errors"]
                ])

            # Разделитель и итоги
            writer.writerow([])
            writer.writerow(["ИТОГО:"])

            battles_total = total_stats["victories"] + total_stats["defeats"]
            win_rate_total = (total_stats["victories"] / battles_total) * 100 if battles_total > 0 else 0
            keys_per_victory_total = (total_stats["keys_collected"] / total_stats["victories"]) if total_stats[
                                                                                                       "victories"] > 0 else 0
            silver_total = total_stats.get("silver_collected", 0)
            silver_total_formatted = f"{silver_total:.1f}K" if silver_total > 0 else "0K"

            writer.writerow([
                "Всего", battles_total, total_stats["victories"], total_stats["defeats"],
                f"{win_rate_total:.1f}", total_stats["keys_collected"], f"{keys_per_victory_total:.1f}",
                silver_total_formatted, total_stats["connection_losses"], total_stats["errors"]
            ])


class MainWindow(QMainWindow):
    """Оптимизированное главное окно приложения."""

    def __init__(self, bot_engine, license_validator):
        super().__init__()

        self.bot_engine = bot_engine
        self.license_validator = license_validator
        self._py_logger = logging.getLogger("BotLogger")

        # Флаги для предотвращения множественных операций
        self._page_switching = False
        self._stats_animation_pending = False

        # Создание сигналов
        self.signals = BotSignals()
        self._connect_signals()

        # Установка сигналов бота
        self.bot_engine.set_signals(self.signals)

        # Инициализация менеджеров
        self.timer_manager = OptimizedTimerManager(self)
        self.update_manager = OptimizedUpdateManager(self)
        self.export_manager = ExportManager(self)

        # Инициализация UI
        self.init_ui()

        # Подключение сигналов между виджетами
        self.connect_widget_signals()

        # Запуск таймеров
        self.timer_manager.start_timers()

    def _connect_signals(self):
        """Подключает сигналы."""
        self.signals.state_changed.connect(self.update_bot_state)
        self.signals.log_message.connect(self.append_log)
        self.signals.error.connect(self.show_error)
        self.signals.stats_updated.connect(self.update_stats)
        self.signals.license_updated.connect(self.on_license_updated)

    def init_ui(self):
        """Инициализация компонентов интерфейса."""
        self.setWindowTitle("Age of Magic Бот v2.0")
        self.setMinimumSize(1000, 800)

        # Центральный виджет и основной лейаут
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

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

        # Стек виджетов для разных страниц
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        # Инициализация страниц
        self.init_pages()

        # Статус-бар и меню
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Готово")
        self.update_license_status()
        self.create_menu()

        # Устанавливаем главную страницу
        self.stack.setCurrentIndex(self.page_indices.get("home", 0))

    def create_menu(self):
        """Создание меню приложения."""
        menu_bar = self.menuBar()

        # Меню "Файл"
        file_menu = menu_bar.addMenu("Файл")

        export_action = QAction("Экспорт статистики", self)
        export_action.triggered.connect(self.export_manager.export_statistics)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Справка"
        help_menu = menu_bar.addMenu("Справка")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_pages(self):
        """Инициализация страниц приложения."""
        from gui.widgets.home_widget import HomeWidget
        from gui.widgets.stats_widget import StatsWidget
        from gui.widgets.settings_widget import SettingsWidget
        from gui.widgets.license_widget import LicenseWidget

        # Создаём страницы
        self.home_widget = HomeWidget(self.bot_engine, self.signals,
                                      license_validator=self.license_validator, parent=self)
        self.stats_widget = StatsWidget(self.bot_engine)
        self.log_widget = LogWidget()
        self.settings_widget = SettingsWidget(self.bot_engine)
        self.license_widget = LicenseWidget(self.license_validator)

        # Добавляем в стек
        pages = [
            (self.home_widget, "home"),
            (self.stats_widget, "stats"),
            (self.log_widget, "logs"),
            (self.settings_widget, "settings"),
            (self.license_widget, "license")
        ]

        self.page_indices = {}
        for i, (widget, page_id) in enumerate(pages):
            self.stack.addWidget(widget)
            self.page_indices[page_id] = i

    def connect_widget_signals(self):
        """Подключение сигналов между виджетами."""
        self.settings_widget.target_keys_changed.connect(self.home_widget.set_target_keys)

        # Загружаем начальное значение цели
        target_keys = config.get("bot", "target_keys", 1000)
        self.home_widget.set_target_keys(target_keys)

    def change_page(self, page_id):
        """Изменяет отображаемую страницу с оптимизированной логикой."""
        if page_id not in self.page_indices or self._page_switching:
            return

        old_page_index = self.stack.currentIndex()
        new_page_index = self.page_indices[page_id]

        if old_page_index == new_page_index:
            return

        self._page_switching = True

        try:
            # Устанавливаем страницу
            self.stack.setCurrentIndex(new_page_index)

            # Синхронизируем боковое меню
            if hasattr(self, 'sidebar'):
                self.sidebar.active_page = page_id
                buttons = getattr(self.sidebar, 'buttons', {})
                for p, button in buttons.items():
                    button.setChecked(p == page_id)

            if page_id == "stats":
                self._py_logger.debug("Переход на страницу статистики")
                # УМЕНЬШИЛИ задержку до 50ms для более быстрой анимации
                QTimer.singleShot(50, self._prepare_stats_animation)
            else:
                # Для других страниц помечаем статистику как невидимую
                if hasattr(self.stats_widget, '_is_currently_visible'):
                    self.stats_widget._is_currently_visible = False

            # Настраиваем частоту обновлений
            self.timer_manager.adjust_for_page(page_id)

        finally:
            self._page_switching = False

    def _prepare_stats_animation(self):
        """Подготавливает и запускает анимацию графиков статистики."""
        if self._stats_animation_pending:
            self._py_logger.debug("Анимация статистики уже ожидает выполнения, пропускаем")
            return

        try:
            self._stats_animation_pending = True

            if hasattr(self, 'stats_widget') and self.stats_widget:
                # ИСПРАВЛЕНО: Подготавливаем графики для анимации
                self.stats_widget.prepare_for_animation()

                # ИСПРАВЛЕНО: Выполняем анимацию БЕЗ принудительной перезагрузки данных
                QTimer.singleShot(100, self._execute_stats_animation)

                self._py_logger.debug("Анимация статистики подготовлена")

        except Exception as e:
            self._py_logger.error(f"Ошибка при подготовке анимации статистики: {e}")
            self._stats_animation_pending = False

    def _execute_stats_animation(self):
        """Выполняет отложенную анимацию статистики."""
        try:
            if hasattr(self, 'stats_widget') and self.stats_widget:
                # ВАЖНО: Выполняем только анимацию, без дополнительных обновлений
                self.stats_widget.updater.update_trend_charts(enable_animation=True, force_reload=False)
                self._py_logger.debug("Анимация статистики выполнена")

        except Exception as e:
            self._py_logger.error(f"Ошибка при выполнении анимации статистики: {e}")
        finally:
            self._stats_animation_pending = False

    # Обработчики событий
    def update_bot_state(self, state):
        """Обновляет UI для отображения состояния бота."""
        self.home_widget.update_bot_state(state)

    def append_log(self, level, message):
        """Добавляет сообщение в лог."""
        self.log_widget.append_log(level, message)

    def update_stats(self, stats):
        """Обновляет отображение статистики."""
        self.home_widget.update_stats(stats)

    def update_runtime(self):
        """Обновляет отображение времени работы бота."""
        if self.bot_engine.running.is_set():
            if self.home_widget.start_time is None:
                self.home_widget.start_time = time.time()

            self.home_widget.update_runtime()
            self.update_stats(self.bot_engine.stats)
        else:
            if hasattr(self.home_widget, 'start_time') and self.home_widget.start_time is not None:
                self.home_widget.start_time = None
                self.home_widget.update_runtime()

    def auto_update_statistics(self):
        """Автоматическое обновление статистики."""
        # ИСПРАВЛЕНО: Пропускаем обновление если происходит переключение страниц или анимация
        if self._page_switching or self._stats_animation_pending:
            return

        # Используем оптимизированный менеджер обновлений
        self.update_manager.update_stats_if_changed()
        self.update_manager.update_progress_if_needed()

    def show_error(self, message):
        """Показывает сообщение об ошибке."""
        QMessageBox.critical(self, "Ошибка", message)

    def on_license_updated(self):
        """Обработчик обновления лицензии."""
        self.update_license_status()

        if hasattr(self, 'home_widget'):
            self.home_widget.update_license_status()

        if hasattr(self, 'license_widget'):
            self.license_widget.update_license_info()

        self._py_logger.debug("Статус лицензии обновлен")

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
                try:
                    self.bot_engine.stop()
                    self._py_logger.info("Бот остановлен при закрытии программы")
                    event.accept()
                except Exception as e:
                    self._py_logger.error(f"Ошибка при остановке бота: {e}")
                    event.accept()
            else:
                event.ignore()
        else:
            # Сохраняем несохраненные данные если есть
            if (hasattr(self.bot_engine, 'stats') and
                    any(val > 0 for val in self.bot_engine.stats.values()) and
                    not getattr(self.bot_engine, 'session_stats_registered', False)):
                try:
                    if self.bot_engine.stats_manager:
                        self.bot_engine.notify_stats_manager_session_ended()
                        self._py_logger.info("Статистика сохранена при закрытии")
                except Exception as e:
                    self._py_logger.error(f"Ошибка при сохранении данных: {e}")

            event.accept()