import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor, QFont

from gui.styles import Styles
from gui.components.stat_card import StatCard
from gui.widgets.keys_progress_bar import KeysProgressBar
from gui.components.fancy_button import FancyButton, FancyButtonGroup


class MetricsCalculator:
    """Калькулятор для расчета показателей производительности."""

    def __init__(self, logger):
        self._py_logger = logger

    def calculate_performance_metrics(self, stats, start_time=None):
        """Рассчитывает все показатели производительности."""
        battles = stats.get("battles_started", 0)
        victories = stats.get("victories", 0)
        defeats = stats.get("defeats", 0)
        keys_collected = stats.get("keys_collected", 0)
        silver_collected = stats.get("silver_collected", 0)

        # Базовые показатели
        total_battles = victories + defeats
        success_rate = (victories / total_battles * 100) if total_battles > 0 else 0
        keys_per_victory = (keys_collected / victories) if victories > 0 else 0
        silver_per_victory = (silver_collected / victories) if victories > 0 else 0

        # Временные показатели
        keys_per_hour = 0
        silver_per_hour = 0

        if start_time:
            elapsed_hours = (time.time() - start_time) / 3600
            if elapsed_hours > 0:
                keys_per_hour = keys_collected / elapsed_hours
                silver_per_hour = silver_collected / elapsed_hours

        return {
            'battles': battles,
            'victories': victories,
            'defeats': defeats,
            'total_battles': total_battles,
            'success_rate': success_rate,
            'keys_collected': keys_collected,
            'keys_per_victory': keys_per_victory,
            'keys_per_hour': keys_per_hour,
            'silver_collected': silver_collected,
            'silver_per_victory': silver_per_victory,
            'silver_per_hour': silver_per_hour,
            'connection_losses': stats.get("connection_losses", 0)
        }

    def format_runtime(self, start_time):
        """Форматирует время работы."""
        if not start_time:
            return "00:00:00"

        try:
            elapsed = int(time.time() - start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception as e:
            self._py_logger.error(f"Ошибка при форматировании времени: {e}")
            return "00:00:00"


class LicenseManager:
    """Менеджер для работы с лицензией."""

    def __init__(self, license_validator, logger):
        self.license_validator = license_validator
        self._py_logger = logger

    def check_license_for_start(self, parent_widget):
        """Проверяет лицензию перед запуском бота."""
        if not self.license_validator:
            self._py_logger.warning("Валидатор лицензии не доступен!")
            return True

        try:
            self._py_logger.info("Проверка лицензии перед запуском бота...")
            if not self.license_validator.is_license_valid():
                self._py_logger.warning("Лицензия недействительна, запуск бота невозможен")
                return self._show_license_dialog(parent_widget)
            else:
                self._py_logger.info("Лицензия действительна, запуск бота разрешен")
                return True
        except Exception as e:
            self._py_logger.error(f"Ошибка при проверке лицензии: {e}")
            return True  # В случае ошибки разрешаем запуск

    def _show_license_dialog(self, parent_widget):
        """Показывает диалог активации лицензии."""
        from PyQt6.QtWidgets import QMessageBox
        result = QMessageBox.warning(
            parent_widget,
            "Требуется активация лицензии",
            "Для запуска бота необходимо активировать лицензию. "
            "Перейти на страницу активации лицензии?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if result == QMessageBox.StandardButton.Yes:
            self._navigate_to_license_page(parent_widget)

        return False

    def _navigate_to_license_page(self, parent_widget):
        """Переходит на страницу лицензии."""
        from gui.main_window import MainWindow
        parent = parent_widget.parent()
        while parent:
            if isinstance(parent, MainWindow):
                parent.change_page("license")
                break
            parent = parent.parent()

    def get_license_status(self):
        """Возвращает статус лицензии."""
        if not self.license_validator:
            return True
        return self.license_validator.is_license_valid()


class UIBuilder:
    """Строитель UI компонентов."""

    @staticmethod
    def create_stats_cards():
        """Создает карточки статистики."""
        card_configs = [
            ("silver_card", "Серебро собрано", "0K", Styles.COLORS["primary"], "silver"),
            ("victories_card", "Победы", "0", Styles.COLORS["secondary"], "victory"),
            ("defeats_card", "Поражения", "0", Styles.COLORS["accent"], "defeat"),
            ("keys_card", "Ключей собрано", "0", Styles.COLORS["warning"], "key")
        ]

        cards = {}
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        for attr_name, title, value, color, icon in card_configs:
            card = StatCard(title, value, color, icon)
            cards[attr_name] = card
            layout.addWidget(card)

        # Устанавливаем фиксированную высоту для контейнера карточек
        stats_container = QWidget()
        stats_container.setLayout(layout)
        stats_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        stats_container.setContentsMargins(0, 0, 0, 0)

        return cards, stats_container

    @staticmethod
    def create_metrics_grid():
        """Создает сетку показателей производительности."""
        metrics_config = [
            ("runtime_label", "Время работы:", "00:00:00", Styles.COLORS['primary']),
            ("battles_label", "Боёв начато:", "0", Styles.COLORS['primary']),
            ("keys_per_victory_label", "Ключей за победу:", "0", Styles.COLORS['warning']),
            ("silver_per_victory_label", "Серебра за победу:", "0K", Styles.COLORS['primary']),
            ("success_rate_label", "Успешность:", "0%", Styles.COLORS['secondary']),
            ("connection_losses_label", "Потери соединения:", "0", Styles.COLORS['accent']),
            ("keys_per_hour_label", "Ключей в час:", "0", Styles.COLORS['warning']),
            ("silver_per_hour_label", "Серебра в час:", "0K", Styles.COLORS['primary'])
        ]

        metrics_content = QWidget()
        metrics_content_layout = QGridLayout(metrics_content)
        metrics_content_layout.setContentsMargins(15, 15, 15, 15)

        labels = {}
        for i, (attr_name, label_text, default_value, color) in enumerate(metrics_config):
            # Создаем метку
            metrics_content_layout.addWidget(QLabel(label_text), i, 0)

            # Создаем значение
            value_label = QLabel(default_value)
            value_label.setStyleSheet(f"color: {color};")
            labels[attr_name] = value_label
            metrics_content_layout.addWidget(value_label, i, 1)

        # Растягиваем сетку показателей вниз
        metrics_content_layout.setRowStretch(len(metrics_config), 1)

        return labels, metrics_content


class HomeWidget(QWidget):
    """Главная страница с управлением ботом и основной статистикой."""

    # Целевое количество ключей по умолчанию
    DEFAULT_TARGET_KEYS = 1000

    def __init__(self, bot_engine, signals, license_validator=None, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine
        self.signals = signals

        # Добавляем логгер
        import logging
        self._py_logger = logging.getLogger("BotLogger")

        # Инициализируем менеджеры
        self.metrics_calculator = MetricsCalculator(self._py_logger)
        self.license_manager = LicenseManager(license_validator, self._py_logger)

        # Время начала работы бота
        self.start_time = None

        # Цель по количеству ключей (можно изменить через настройки)
        self.target_keys = self.DEFAULT_TARGET_KEYS

        # Инициализация значений для прогресс-бара
        self.current_progress = 0

        # Безопасная загрузка целевого значения из конфигурации или stats_manager
        self._load_initial_values()

        # Инициализация UI с предзагруженными значениями
        self.init_ui()

    def _load_initial_values(self):
        """Загружает начальные значения из конфигурации и stats_manager."""
        from config import config
        try:
            # Сначала пробуем загрузить из конфигурации
            self.target_keys = config.get("bot", "target_keys", self.DEFAULT_TARGET_KEYS)

            # Затем, если доступен stats_manager, получаем текущие значения
            if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
                # Загружаем цель из stats_manager
                if hasattr(self.bot_engine.stats_manager, 'keys_target'):
                    self.target_keys = self.bot_engine.stats_manager.keys_target
                else:
                    self.bot_engine.stats_manager.keys_target = self.target_keys

                # Загружаем текущий прогресс для быстрой инициализации
                if hasattr(self.bot_engine.stats_manager, 'keys_current'):
                    self.current_progress = self.bot_engine.stats_manager.keys_current
                    self._py_logger.info(f"Быстрая инициализация прогресс-бара со значением: {self.current_progress}")
                else:
                    self.bot_engine.stats_manager.keys_current = 0
                    self.current_progress = 0
        except Exception as e:
            self._py_logger.warning(f"Не удалось загрузить значения для прогресс-бара: {e}")

    def start_bot(self):
        """Запуск бота."""
        # Проверяем лицензию перед запуском
        if not self.license_manager.check_license_for_start(self):
            return False

        # Если лицензия валидна, запускаем бота
        if self.bot_engine.start():
            self._update_button_states(bot_running=True)
            self.start_time = time.time()
            self.update_runtime()
            self.update_stats(self.bot_engine.stats)
            return True

        return False

    def stop_bot(self):
        """Остановка бота."""
        if self.bot_engine.stop():
            self._update_button_states(bot_running=False)
            self.start_time = None
            self.update_runtime()
            return True
        return False

    def _update_button_states(self, bot_running):
        """Обновляет состояние кнопок в зависимости от состояния бота."""
        self.start_button.setEnabled(not bot_running)
        self.stop_button.setEnabled(bot_running)

        if bot_running:
            # Запустить становится серой, остановить - красной
            self.start_button.setActive(True)
            self.stop_button.setActive(False)
        else:
            # Запустить становится зеленой, остановить - серой
            self.start_button.setActive(False)
            self.stop_button.setActive(True)

    def init_ui(self):
        """Инициализация интерфейса главной страницы."""
        # Основной лэйаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Заголовок и статус
        self._create_header(layout)

        # Кнопки управления
        self._create_control_buttons(layout)

        # Карточки со статистикой
        self._create_stats_section(layout)

        # Прогресс сбора ключей
        self._create_progress_section(layout)

        # Показатели производительности
        self._create_metrics_section(layout)

    def _create_header(self, layout):
        """Создает заголовок страницы."""
        header_layout = QVBoxLayout()

        # Заголовок страницы
        title_label = QLabel("Age of Magic Бот")
        title_label.setObjectName("title")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {Styles.COLORS['text_primary']};
        """)
        header_layout.addWidget(title_label)

        # Статус бота
        self.status_label = QLabel("Статус: Ожидание")
        self.status_label.setObjectName("subtitle")
        self.status_label.setStyleSheet(f"""
            font-size: 14px;
            color: {Styles.COLORS['text_secondary']};
        """)
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

    def _create_control_buttons(self, layout):
        """Создает кнопки управления."""
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)

        # Создаем группу для кнопок с эффектом переключения
        self.button_group = FancyButtonGroup()

        # Кнопка запуска
        self.start_button = FancyButton("▶ Запустить", self, success=True)
        self.start_button.clicked.connect(self.start_bot)
        self.button_group.addButton(self.start_button)
        control_layout.addWidget(self.start_button)

        # Кнопка остановки
        self.stop_button = FancyButton("⛔ Остановить", self, success=False)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_bot)
        self.button_group.addButton(self.stop_button)
        control_layout.addWidget(self.stop_button)

        # Кнопка остановки должна быть серой по умолчанию
        self.stop_button.setActive(True)

        # Добавляем растягивающийся элемент для выравнивания кнопок по левому краю
        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        layout.addLayout(control_layout)

    def _create_stats_section(self, layout):
        """Создает секцию с карточками статистики."""
        self.stats_cards, stats_container = UIBuilder.create_stats_cards()
        layout.addWidget(stats_container)

    def _create_progress_section(self, layout):
        """Создает секцию прогресса ключей."""
        keys_progress_frame = QFrame()
        keys_progress_frame.setObjectName("section_box")
        keys_progress_layout = QVBoxLayout(keys_progress_frame)
        keys_progress_layout.setContentsMargins(0, 0, 0, 0)
        keys_progress_layout.setSpacing(0)

        # Создаем виджет прогресса ключей
        self._py_logger.info(f"Инициализация прогресс-бара со значением: {self.current_progress}/{self.target_keys}")
        self.keys_progress_bar = KeysProgressBar(target=self.target_keys, current=self.current_progress)
        self.keys_progress_bar.progress_reset.connect(self.reset_keys_progress)
        keys_progress_layout.addWidget(self.keys_progress_bar)

        layout.addWidget(keys_progress_frame)

    def _create_metrics_section(self, layout):
        """Создает секцию показателей производительности."""
        metrics_frame = QFrame()
        metrics_frame.setObjectName("section_box")
        metrics_layout = QVBoxLayout(metrics_frame)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(0)

        # Заголовок показателей
        metrics_header = QLabel("Показатели производительности")
        metrics_header.setObjectName("header")
        metrics_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        metrics_layout.addWidget(metrics_header)

        # Содержимое показателей
        self.metrics_labels, metrics_content = UIBuilder.create_metrics_grid()
        metrics_layout.addWidget(metrics_content, 1)
        layout.addWidget(metrics_frame, 1)

    def update_bot_state(self, state):
        """Обновляет отображение текущего состояния бота."""
        state_translations = {
            "IDLE": "Ожидание",
            "STARTING": "Запуск",
            "SELECTING_BATTLE": "Выбор боя",
            "CONFIRMING_BATTLE": "Подтверждение боя",
            "IN_BATTLE": "В бою",
            "BATTLE_ENDED": "Бой завершен",
            "CONNECTION_LOST": "Соединение потеряно",
            "RECONNECTING": "Переподключение",
            "ERROR": "Ошибка"
        }

        translated_state = state_translations.get(state, state)
        self.status_label.setText(f"Статус: {translated_state}")

        # Разные цвета в зависимости от состояния
        color_map = {
            "IDLE": Styles.COLORS['text_secondary'],
            "STARTING": Styles.COLORS['warning'],
            "RECONNECTING": Styles.COLORS['warning'],
            "ERROR": Styles.COLORS['accent'],
            "CONNECTION_LOST": Styles.COLORS['accent']
        }

        color = color_map.get(state, Styles.COLORS['secondary'])
        self.status_label.setStyleSheet(f"color: {color}; font-size: 14px;")

    def update_stats(self, stats):
        """Обновляет отображение статистики текущей сессии."""
        # Рассчитываем все показатели через калькулятор
        metrics = self.metrics_calculator.calculate_performance_metrics(stats, self.start_time)

        # Обновляем карточки
        self.stats_cards["battles_label"] = self.metrics_labels["battles_label"]
        self.metrics_labels["battles_label"].setText(str(metrics['battles']))

        # Форматируем значение серебра для карточки
        silver_formatted = Styles.format_silver(metrics['silver_collected'])
        self.stats_cards["silver_card"].set_value(silver_formatted)

        self.stats_cards["victories_card"].set_value(str(metrics['victories']))
        self.stats_cards["defeats_card"].set_value(str(metrics['defeats']))
        self.stats_cards["keys_card"].set_value(str(metrics['keys_collected']))

        # Обновляем показатели производительности
        self._update_metrics_display(metrics)

        # Обновляем прогресс-бар
        self._update_progress_bar(stats)

    def _update_metrics_display(self, metrics):
        """Обновляет отображение показателей производительности."""
        # Обновляем значения в интерфейсе
        updates = {
            "success_rate_label": f"{metrics['success_rate']:.1f}%",
            "keys_per_victory_label": f"{metrics['keys_per_victory']:.1f}",
            "silver_per_victory_label": Styles.format_silver(metrics['silver_per_victory']),
            "connection_losses_label": str(metrics['connection_losses']),
            "keys_per_hour_label": f"{metrics['keys_per_hour']:.1f}",
            "silver_per_hour_label": Styles.format_silver(metrics['silver_per_hour'])
        }

        for label_name, value in updates.items():
            if label_name in self.metrics_labels:
                self.metrics_labels[label_name].setText(value)

    def _update_progress_bar(self, stats):
        """Обновляет прогресс-бар с использованием данных из StatsManager."""
        if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
            # Получаем информацию о прогрессе из StatsManager
            progress_info = self.bot_engine.stats_manager.get_keys_progress()

            # Проверяем, была ли статистика сессии уже зарегистрирована
            is_registered = getattr(self.bot_engine, 'session_stats_registered', False)

            if is_registered:
                total_progress = progress_info["current"]
                self._py_logger.debug(
                    f"Прогресс-бар: сессия уже зарегистрирована, отображаем только общий прогресс {total_progress}")
            else:
                total_progress = progress_info["current"] + stats.get("keys_collected", 0)
                self._py_logger.debug(
                    f"Прогресс-бар: добавляем ключи текущей сессии {stats.get('keys_collected', 0)} к общему прогрессу {progress_info['current']}")

            # Обновляем прогресс-бар
            self.keys_progress_bar.update_values(total_progress, target=progress_info["target"])

            # Обновляем целевое значение, если оно изменилось
            if self.target_keys != progress_info["target"]:
                self.target_keys = progress_info["target"]
        else:
            # Если StatsManager недоступен, используем только ключи текущей сессии
            self.keys_progress_bar.update_values(stats.get("keys_collected", 0), target=self.target_keys)

    def update_runtime(self):
        """Обновляет отображение времени работы бота."""
        runtime_text = self.metrics_calculator.format_runtime(self.start_time)
        self.metrics_labels["runtime_label"].setText(runtime_text)

    def set_target_keys(self, target):
        """Устанавливает цель по количеству ключей."""
        self.target_keys = target

        # Обновляем цель в менеджере статистики
        if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
            self.bot_engine.stats_manager.update_keys_target(target)

            # Обновляем прогресс-бар с новой целью
            progress_info = self.bot_engine.stats_manager.get_keys_progress()
            self.keys_progress_bar.update_values(
                progress_info["current"] + self.bot_engine.stats.get("keys_collected", 0),
                target=target
            )
        else:
            # Если StatsManager недоступен, просто обновляем прогресс-бар
            self.keys_progress_bar.update_values(
                self.bot_engine.stats.get("keys_collected", 0),
                target=target
            )

    def reset_keys_progress(self):
        """Сбрасывает прогресс сбора ключей."""
        # Сбрасываем прогресс, используя StatsManager
        if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
            # Сбрасываем прогресс в StatsManager
            self.bot_engine.stats_manager.reset_keys_progress()

            # Обновляем интерфейс
            progress_info = self.bot_engine.stats_manager.get_keys_progress()
            self.keys_progress_bar.update_values(
                progress_info["current"] + self.bot_engine.stats.get("keys_collected", 0),
                target=progress_info["target"]
            )

            self._py_logger.info("Прогресс ключей сброшен через StatsManager")
        else:
            # Если StatsManager недоступен, просто обновляем прогресс-бар
            self.keys_progress_bar.update_values(0, target=self.target_keys)
            self._py_logger.warning("StatsManager недоступен, сброс выполнен только в UI")

    def update_license_status(self):
        """Обновляет элементы интерфейса в зависимости от статуса лицензии."""
        is_valid = self.license_manager.get_license_status()

        # Обновление состояния кнопки запуска бота
        self.start_button.setEnabled(not self.bot_engine.running.is_set())

        # Логирование обновления статуса лицензии
        self._py_logger.debug(
            f"Обновление статуса лицензии в HomeWidget: {'действительна' if is_valid else 'недействительна'}")

        # Обновляем подсказки для кнопок
        if is_valid:
            self.start_button.setToolTip("Запустить бота")
        else:
            self.start_button.setToolTip("Для запуска бота требуется активировать лицензию")