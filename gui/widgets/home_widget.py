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


class HomeWidget(QWidget):
    """Главная страница с управлением ботом и основной статистикой."""

    # Целевое количество ключей по умолчанию
    DEFAULT_TARGET_KEYS = 1000

    def __init__(self, bot_engine, signals, license_validator=None, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine
        self.signals = signals
        self.license_validator = license_validator  # Добавляем валидатор лицензии

        # Добавляем логгер
        import logging
        self._py_logger = logging.getLogger("BotLogger")

        # Время начала работы бота
        self.start_time = None

        # Цель по количеству ключей (можно изменить через настройки)
        self.target_keys = self.DEFAULT_TARGET_KEYS

        # Инициализация значений для прогресс-бара (чтобы сразу отобразить его корректно)
        self.current_progress = 0

        # Безопасная загрузка целевого значения из конфигурации или stats_manager
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
                    # Если атрибута нет, инициализируем его
                    self.bot_engine.stats_manager.keys_target = self.target_keys

                # Загружаем текущий прогресс для быстрой инициализации
                if hasattr(self.bot_engine.stats_manager, 'keys_current'):
                    self.current_progress = self.bot_engine.stats_manager.keys_current
                    self._py_logger.info(f"Быстрая инициализация прогресс-бара со значением: {self.current_progress}")
                else:
                    # Если атрибута нет, инициализируем его
                    self.bot_engine.stats_manager.keys_current = 0
                    self.current_progress = 0
        except Exception as e:
            self._py_logger.warning(f"Не удалось загрузить значения для прогресс-бара: {e}")

        # Инициализация UI с предзагруженными значениями
        self.init_ui()

    def start_bot(self):
        """Запуск бота."""
        # Проверяем лицензию перед запуском, если валидатор доступен
        try:
            if self.license_validator:
                self._py_logger.info("Проверка лицензии перед запуском бота...")
                if not self.license_validator.is_license_valid():
                    self._py_logger.warning("Лицензия недействительна, запуск бота невозможен")
                    # Показываем сообщение о необходимости активации лицензии
                    from PyQt6.QtWidgets import QMessageBox
                    result = QMessageBox.warning(
                        self,
                        "Требуется активация лицензии",
                        "Для запуска бота необходимо активировать лицензию. "
                        "Перейти на страницу активации лицензии?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if result == QMessageBox.StandardButton.Yes:
                        # Попробуем найти родительское окно и переключиться на страницу лицензии
                        from gui.main_window import MainWindow
                        parent = self.parent()
                        while parent:
                            if isinstance(parent, MainWindow):
                                parent.change_page("license")
                                break
                            parent = parent.parent()

                    return False
                else:
                    self._py_logger.info("Лицензия действительна, запуск бота разрешен")
            else:
                self._py_logger.warning("Валидатор лицензии не доступен!")
        except Exception as e:
            self._py_logger.error(f"Ошибка при проверке лицензии: {e}")

        # Если лицензия валидна или не требуется проверка, запускаем бота
        if self.bot_engine.start():
            # ВАЖНОЕ ИЗМЕНЕНИЕ: Сохраняем текущее состояние прогресс-бара перед сбросом счетчика
            self._py_logger.info("Обновление статистики на основе сохраненных данных")

            # Сохраняем текущее значение общего прогресса для информации
            if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
                if hasattr(self.bot_engine.stats_manager, 'keys_current'):
                    current_progress = self.bot_engine.stats_manager.keys_current
                    self._py_logger.info(f"Текущий общий прогресс ключей: {current_progress}")

            # При запуске бота ВСЕГДА сбрасываем счетчики текущей сессии
            self.bot_engine.stats["keys_collected"] = 0
            self.bot_engine.stats["silver_collected"] = 0

            # Обновляем отображение с нулевыми значениями для текущей сессии
            self.keys_card.set_value("0")
            self.silver_card.set_value("0K")

            # Обновляем остальные элементы интерфейса
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.start_time = time.time()
            self.update_runtime()

            # Важно: обновляем статистику, чтобы прогресс-бар показывал правильное значение
            # (общий прогресс + 0 ключей текущей сессии)
            self.update_stats(self.bot_engine.stats)

            return True

        return False

    def init_ui(self):
        """Инициализация интерфейса главной страницы."""
        # Основной лэйаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Заголовок и статус
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

        # Кнопки управления
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)

        # Кнопка запуска
        self.start_button = QPushButton("▶ Запустить")
        self.start_button.setObjectName("action_button_success")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.start_bot)
        control_layout.addWidget(self.start_button)

        # Кнопка остановки
        self.stop_button = QPushButton("⛔ Остановить")
        self.stop_button.setObjectName("action_button_danger")
        self.stop_button.setFixedHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_bot)
        control_layout.addWidget(self.stop_button)

        # Добавляем растягивающийся элемент для выравнивания кнопок по левому краю
        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        layout.addLayout(control_layout)

        # Карточки со статистикой (4 карточки в ряд)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        stats_layout.setContentsMargins(0, 0, 0, 0)  # Убираем внутренние отступы

        # Карточка с серебром (заменяем карточку с количеством боев)
        self.silver_card = StatCard(
            "Серебро собрано",
            "0K",
            Styles.COLORS["primary"],
            "silver"
        )
        stats_layout.addWidget(self.silver_card)

        # Карточка с победами
        self.victories_card = StatCard(
            "Победы",
            "0",
            Styles.COLORS["secondary"],
            "victory"
        )
        stats_layout.addWidget(self.victories_card)

        # Карточка с поражениями
        self.defeats_card = StatCard(
            "Поражения",
            "0",
            Styles.COLORS["accent"],
            "defeat"
        )
        stats_layout.addWidget(self.defeats_card)

        # Карточка с ключами - всегда начинается с 0 для текущей сессии
        keys_collected = 0
        self.keys_card = StatCard(
            "Ключей собрано",
            str(keys_collected),
            Styles.COLORS["warning"],
            "key"
        )
        stats_layout.addWidget(self.keys_card)

        # Устанавливаем фиксированную высоту для контейнера карточек
        stats_container = QWidget()
        stats_container.setLayout(stats_layout)
        stats_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        stats_container.setContentsMargins(0, 0, 0, 0)  # Убираем отступы контейнера

        layout.addWidget(stats_container)

        # Прогресс сбора ключей
        keys_progress_frame = QFrame()
        keys_progress_frame.setObjectName("section_box")
        keys_progress_layout = QVBoxLayout(keys_progress_frame)
        keys_progress_layout.setContentsMargins(0, 0, 0, 0)
        keys_progress_layout.setSpacing(0)

        # Создаем виджет прогресса ключей
        # ВАЖНО: Используем предзагруженное значение self.current_progress для быстрой инициализации
        self._py_logger.info(f"Инициализация прогресс-бара со значением: {self.current_progress}/{self.target_keys}")
        self.keys_progress_bar = KeysProgressBar(target=self.target_keys, current=self.current_progress)
        self.keys_progress_bar.progress_reset.connect(self.reset_keys_progress)
        keys_progress_layout.addWidget(self.keys_progress_bar)

        layout.addWidget(keys_progress_frame)

        # Показатели производительности
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
        metrics_content = QWidget()
        metrics_content_layout = QGridLayout(metrics_content)
        metrics_content_layout.setContentsMargins(15, 15, 15, 15)

        # Время работы
        metrics_content_layout.addWidget(QLabel("Время работы:"), 0, 0)
        self.runtime_label = QLabel("00:00:00")
        self.runtime_label.setStyleSheet(f"color: {Styles.COLORS['primary']};")
        metrics_content_layout.addWidget(self.runtime_label, 0, 1)

        # Количество боев (перенесено из карточки)
        metrics_content_layout.addWidget(QLabel("Боёв начато:"), 1, 0)
        self.battles_label = QLabel("0")
        self.battles_label.setStyleSheet(f"color: {Styles.COLORS['primary']};")
        metrics_content_layout.addWidget(self.battles_label, 1, 1)

        # Ключей за победу
        metrics_content_layout.addWidget(QLabel("Ключей за победу:"), 2, 0)
        self.keys_per_victory_label = QLabel("0")
        self.keys_per_victory_label.setStyleSheet(f"color: {Styles.COLORS['warning']};")
        metrics_content_layout.addWidget(self.keys_per_victory_label, 2, 1)

        # Серебра за победу (новый показатель)
        metrics_content_layout.addWidget(QLabel("Серебра за победу:"), 3, 0)
        self.silver_per_victory_label = QLabel("0K")
        self.silver_per_victory_label.setStyleSheet(f"color: {Styles.COLORS['primary']};")
        metrics_content_layout.addWidget(self.silver_per_victory_label, 3, 1)

        # Успешность
        metrics_content_layout.addWidget(QLabel("Успешность:"), 4, 0)
        self.success_rate_label = QLabel("0%")
        self.success_rate_label.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        metrics_content_layout.addWidget(self.success_rate_label, 4, 1)

        # Потери соединения
        metrics_content_layout.addWidget(QLabel("Потери соединения:"), 5, 0)
        self.connection_losses_label = QLabel("0")
        self.connection_losses_label.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        metrics_content_layout.addWidget(self.connection_losses_label, 5, 1)

        # Ключей в час
        metrics_content_layout.addWidget(QLabel("Ключей в час:"), 6, 0)
        self.keys_per_hour_label = QLabel("0")
        self.keys_per_hour_label.setStyleSheet(f"color: {Styles.COLORS['warning']};")
        metrics_content_layout.addWidget(self.keys_per_hour_label, 6, 1)

        # Серебра в час (новый показатель)
        metrics_content_layout.addWidget(QLabel("Серебра в час:"), 7, 0)
        self.silver_per_hour_label = QLabel("0K")
        self.silver_per_hour_label.setStyleSheet(f"color: {Styles.COLORS['primary']};")
        metrics_content_layout.addWidget(self.silver_per_hour_label, 7, 1)

        # Растягиваем сетку показателей вниз
        metrics_content_layout.setRowStretch(8, 1)

        metrics_layout.addWidget(metrics_content, 1)
        layout.addWidget(metrics_frame, 1)

    def stop_bot(self):
        """Остановка бота."""
        # Даже при остановке проверяем лицензию для согласованности
        if self.license_validator and not self.license_validator.is_license_valid():
            self._py_logger.warning("Попытка остановить бота с недействительной лицензией")
            # Останавливаем в любом случае, но логируем

        if self.bot_engine.stop():
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.start_time = None

            # Обновляем статистику, но НЕ сбрасываем прогресс-бар
            # Это критично, так как прогресс должен сохраняться между сессиями
            current_progress = 0
            if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
                if hasattr(self.bot_engine.stats_manager, 'keys_current'):
                    current_progress = self.bot_engine.stats_manager.keys_current
                    self._py_logger.info(f"Сохранение общего прогресса ключей: {current_progress}")

            # Обновляем статистику с учетом сохраненного прогресса
            self.update_stats(self.bot_engine.stats)
            return True

        return False

    def update_bot_state(self, state):
        """
        Обновляет отображение текущего состояния бота.

        Args:
            state (str): Состояние бота
        """
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
        if state == "IDLE":
            self.status_label.setStyleSheet(f"color: {Styles.COLORS['text_secondary']}; font-size: 14px;")
        elif state in ["STARTING", "RECONNECTING"]:
            self.status_label.setStyleSheet(f"color: {Styles.COLORS['warning']}; font-size: 14px;")
        elif state in ["ERROR", "CONNECTION_LOST"]:
            self.status_label.setStyleSheet(f"color: {Styles.COLORS['accent']}; font-size: 14px;")
        else:
            self.status_label.setStyleSheet(f"color: {Styles.COLORS['secondary']}; font-size: 14px;")

    def update_stats(self, stats):
        """
        Обновляет отображение статистики.

        Args:
            stats (dict): Статистика бота
        """
        # Обновляем карточки
        self.battles_label.setText(str(stats.get("battles_started", 0)))

        # Форматируем значение серебра для карточки с использованием нового метода
        # Учитываем, что значение уже в тысячах (K)
        silver_value = stats.get("silver_collected", 0)
        silver_formatted = Styles.format_silver(silver_value)
        self.silver_card.set_value(silver_formatted)

        self.victories_card.set_value(str(stats.get("victories", 0)))
        self.defeats_card.set_value(str(stats.get("defeats", 0)))
        self.keys_card.set_value(str(stats.get("keys_collected", 0)))

        # ВАЖНОЕ ИЗМЕНЕНИЕ: Обновляем прогресс-бар правильным образом, учитывая общий прогресс
        # Получаем текущий прогресс из stats_manager плюс ключи текущей сессии
        if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
            total_progress = 0
            if hasattr(self.bot_engine.stats_manager, 'keys_current'):
                # Используем общий прогресс из stats_manager
                total_progress = self.bot_engine.stats_manager.keys_current

            # Добавляем ключи текущей сессии к общему прогрессу для отображения
            # Важно: это только для отображения, фактическое добавление происходит при остановке бота
            total_progress_with_session = total_progress + stats.get("keys_collected", 0)

            # Обновляем прогресс-бар общим значением
            self.keys_progress_bar.update_values(total_progress_with_session, target=self.target_keys)
        else:
            # Если stats_manager недоступен, используем только ключи текущей сессии
            self.keys_progress_bar.update_values(stats.get("keys_collected", 0), target=self.target_keys)

        # Обновляем показатели
        self.connection_losses_label.setText(str(stats.get("connection_losses", 0)))

        # Вычисляем процент успешности
        battles = stats.get("victories", 0) + stats.get("defeats", 0)
        if battles > 0:
            success_rate = (stats.get("victories", 0) / battles) * 100
            self.success_rate_label.setText(f"{success_rate:.1f}%")

            # Вычисляем количество ключей за победу
            victories = stats.get("victories", 0)
            if victories > 0:
                keys_per_victory = stats.get("keys_collected", 0) / victories
                self.keys_per_victory_label.setText(f"{keys_per_victory:.1f}")

                # Вычисляем количество серебра за победу - тоже уже в K
                silver_per_victory = stats.get("silver_collected", 0) / victories
                self.silver_per_victory_label.setText(Styles.format_silver(silver_per_victory))
            else:
                self.keys_per_victory_label.setText("0")
                self.silver_per_victory_label.setText("0K")
        else:
            self.success_rate_label.setText("0%")
            self.keys_per_victory_label.setText("0")
            self.silver_per_victory_label.setText("0K")

        # Вычисляем количество ключей и серебра в час
        if self.start_time:
            elapsed_hours = (time.time() - self.start_time) / 3600
            if elapsed_hours > 0:
                keys_per_hour = stats.get("keys_collected", 0) / elapsed_hours
                self.keys_per_hour_label.setText(f"{keys_per_hour:.1f}")

                # Используем format_silver для серебра в час
                silver_per_hour = stats.get("silver_collected", 0) / elapsed_hours
                self.silver_per_hour_label.setText(Styles.format_silver(silver_per_hour))
            else:
                self.keys_per_hour_label.setText("0")
                self.silver_per_hour_label.setText("0K")
        else:
            self.keys_per_hour_label.setText("0")
            self.silver_per_hour_label.setText("0K")

    def update_runtime(self):
        """Обновляет отображение времени работы бота."""
        if self.start_time:
            try:
                elapsed = int(time.time() - self.start_time)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                seconds = elapsed % 60
                self.runtime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

                # Обновляем ключей в час при наличии прошедшего времени
                if elapsed > 0:
                    keys_collected = self.bot_engine.stats.get("keys_collected", 0)
                    elapsed_hours = elapsed / 3600.0
                    keys_per_hour = keys_collected / elapsed_hours if elapsed_hours > 0 else 0
                    self.keys_per_hour_label.setText(f"{keys_per_hour:.1f}")
            except Exception as e:
                print(f"Ошибка при обновлении времени: {e}")
        else:
            # Если бот не запущен, показываем нули
            self.runtime_label.setText("00:00:00")
            self.keys_per_hour_label.setText("0")

    def set_target_keys(self, target):
        """
        Устанавливает цель по количеству ключей.

        Args:
            target (int): Целевое количество ключей
        """
        self.target_keys = target

        # Обновляем цель в менеджере статистики
        if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
            self.bot_engine.stats_manager.update_keys_target(target)

        # Обновляем отображение прогресса
        self.keys_progress_bar.update_values(
            self.bot_engine.stats.get("keys_collected", 0),
            target=self.target_keys
        )

    def reset_keys_progress(self):
        """Сбрасывает прогресс сбора ключей."""
        # Проверяем наличие stats_manager
        if hasattr(self.bot_engine, 'stats_manager') and self.bot_engine.stats_manager:
            # Проверяем наличие метода reset_keys_progress
            if hasattr(self.bot_engine.stats_manager, 'reset_keys_progress'):
                # Сбрасываем прогресс в менеджере статистики
                self.bot_engine.stats_manager.reset_keys_progress()
            else:
                # Если метода нет, сбрасываем общий прогресс ключей вручную
                self.bot_engine.stats_manager.keys_current = 0
                if hasattr(self.bot_engine.stats_manager, 'save_keys_progress'):
                    self.bot_engine.stats_manager.save_keys_progress()
                else:
                    self.bot_engine.stats_manager.save_stats()  # Используем обычный метод сохранения

            # Сбрасываем счетчик ключей в статистике текущей сессии
            self.bot_engine.stats["keys_collected"] = 0

            # Обновляем отображение статистики
            self.update_stats(self.bot_engine.stats)
        else:
            # Если stats_manager недоступен, просто обнуляем статистику текущей сессии
            self.bot_engine.stats["keys_collected"] = 0
            self.update_stats(self.bot_engine.stats)

    def update_license_status(self):
        """Обновляет элементы интерфейса в зависимости от статуса лицензии."""
        if not self.license_validator:
            return

        is_valid = self.license_validator.is_license_valid()

        # Обновление состояния кнопки запуска бота
        self.start_button.setEnabled(not self.bot_engine.running.is_set())

        # Логирование обновления статуса лицензии
        self._py_logger.debug(
            f"Обновление статуса лицензии в HomeWidget: {'действительна' if is_valid else 'недействительна'}")

        # Если нужно, можно добавить визуальные индикаторы статуса лицензии
        # Например, изменить текст подсказки для кнопки запуска
        if is_valid:
            self.start_button.setToolTip("Запустить бота")
        else:
            self.start_button.setToolTip("Для запуска бота требуется активировать лицензию")