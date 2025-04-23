import time
import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTextEdit, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QColor, QFont

from gui.styles import Styles
from gui.components.stat_card import StatCard
from gui.components.log_viewer import LogViewer


class HomeWidget(QWidget):
    """Главная страница с управлением ботом и основной статистикой."""

    def __init__(self, bot_engine, signals, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine
        self.signals = signals

        # Время начала работы бота
        self.start_time = None

        # Инициализация UI
        self.init_ui()

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
        control_layout.setSpacing(10)

        # Кнопка запуска
        self.start_button = QPushButton("▶ Запустить")
        self.start_button.setObjectName("success")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.start_bot)
        control_layout.addWidget(self.start_button)

        # Кнопка остановки
        self.stop_button = QPushButton("⛔ Остановить")
        self.stop_button.setObjectName("danger")
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

        # Карточка с количеством боев
        self.battles_card = StatCard(
            "Боёв начато",
            "0",
            Styles.COLORS["primary"],
            "battle"
        )
        stats_layout.addWidget(self.battles_card)

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

        # Карточка с ключами
        self.keys_card = StatCard(
            "Ключей собрано",
            "0",
            Styles.COLORS["warning"],
            "key"
        )
        stats_layout.addWidget(self.keys_card)

        # Устанавливаем фиксированную высоту для контейнера карточек
        stats_container = QWidget()
        stats_container.setLayout(stats_layout)
        stats_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout.addWidget(stats_container)

        # Журнал активности и показатели производительности в две колонки
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)

        # Журнал активности
        log_frame = QFrame()
        log_frame.setObjectName("section_box")
        log_frame_layout = QVBoxLayout(log_frame)
        log_frame_layout.setContentsMargins(0, 0, 0, 0)
        log_frame_layout.setSpacing(0)

        # Заголовок журнала
        log_header = QLabel("Журнал активности")
        log_header.setObjectName("header")
        log_frame_layout.addWidget(log_header)

        # Компонент просмотра логов
        self.log_viewer = LogViewer()
        self.log_viewer.setFixedHeight(300)
        log_frame_layout.addWidget(self.log_viewer)

        # Кнопка очистки журнала
        clear_button_layout = QHBoxLayout()
        clear_button_layout.setContentsMargins(15, 10, 15, 15)

        clear_log_button = QPushButton("Очистить журнал")
        clear_log_button.clicked.connect(self.clear_log)
        clear_button_layout.addWidget(clear_log_button)

        log_frame_layout.addLayout(clear_button_layout)

        # Добавляем журнал в нижний лейаут (занимает 2/3 ширины)
        bottom_layout.addWidget(log_frame, 2)

        # Показатели производительности
        metrics_frame = QFrame()
        metrics_frame.setObjectName("section_box")
        metrics_layout = QVBoxLayout(metrics_frame)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(0)

        # Заголовок показателей
        metrics_header = QLabel("Показатели производительности")
        metrics_header.setObjectName("header")
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

        # Ключей за победу
        metrics_content_layout.addWidget(QLabel("Ключей за победу:"), 1, 0)
        self.keys_per_victory_label = QLabel("0")
        self.keys_per_victory_label.setStyleSheet(f"color: {Styles.COLORS['warning']};")
        metrics_content_layout.addWidget(self.keys_per_victory_label, 1, 1)

        # Успешность
        metrics_content_layout.addWidget(QLabel("Успешность:"), 2, 0)
        self.success_rate_label = QLabel("0%")
        self.success_rate_label.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        metrics_content_layout.addWidget(self.success_rate_label, 2, 1)

        # Потери соединения
        metrics_content_layout.addWidget(QLabel("Потери соединения:"), 3, 0)
        self.connection_losses_label = QLabel("0")
        self.connection_losses_label.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        metrics_content_layout.addWidget(self.connection_losses_label, 3, 1)

        metrics_layout.addWidget(metrics_content)

        # Добавляем показатели в нижний лейаут (занимает 1/3 ширины)
        bottom_layout.addWidget(metrics_frame, 1)

        layout.addLayout(bottom_layout)

    def start_bot(self):
        """Запуск бота."""
        if self.bot_engine.start():
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.start_time = time.time()
            self.update_runtime()

            # Добавляем запись в журнал
            self.append_log("info", "Бот запущен")

    def stop_bot(self):
        """Остановка бота."""
        if self.bot_engine.stop():
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.start_time = None

            # Добавляем запись в журнал
            self.append_log("info", "Бот остановлен")

            # Обновляем статистику
            self.update_stats(self.bot_engine.stats)

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
        self.battles_card.set_value(str(stats.get("battles_started", 0)))
        self.victories_card.set_value(str(stats.get("victories", 0)))
        self.defeats_card.set_value(str(stats.get("defeats", 0)))
        self.keys_card.set_value(str(stats.get("keys_collected", 0)))

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
            else:
                self.keys_per_victory_label.setText("0")
        else:
            self.success_rate_label.setText("0%")
            self.keys_per_victory_label.setText("0")

    def update_runtime(self):
        """Обновляет отображение времени работы бота."""
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.runtime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def append_log(self, level, message):
        """
        Добавляет сообщение в журнал.

        Args:
            level (str): Уровень сообщения
            message (str): Текст сообщения
        """
        self.log_viewer.append_log(level, message)

    def clear_log(self):
        """Очищает журнал."""
        self.log_viewer.clear()