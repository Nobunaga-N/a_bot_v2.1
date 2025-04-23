from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from gui.styles import Styles
from gui.components.stat_card import StatCard
from gui.components.styled_table import StyledTable


class StatsWidget(QWidget):
    """Страница статистики и аналитики."""

    def __init__(self, bot_engine, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine

        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса страницы статистики."""
        # Основной лэйаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Заголовок и выбор периода в одной строке
        header_layout = QHBoxLayout()

        # Заголовок страницы
        title_layout = QVBoxLayout()

        title_label = QLabel("Статистика и аналитика")
        title_label.setObjectName("title")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {Styles.COLORS['text_primary']};
        """)
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("Детальная статистика работы бота")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setStyleSheet(f"""
            font-size: 14px;
            color: {Styles.COLORS['text_secondary']};
        """)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)

        # Выбор периода (справа)
        period_layout = QHBoxLayout()
        period_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        period_label = QLabel("Период:")
        period_label.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        period_layout.addWidget(period_label)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Сегодня", "Неделя", "Месяц", "Все время"])
        self.period_combo.setFixedWidth(150)
        self.period_combo.currentIndexChanged.connect(self.update_stats_period)
        period_layout.addWidget(self.period_combo)

        header_layout.addLayout(period_layout)

        layout.addLayout(header_layout)

        # Создаем область прокрутки для содержимого
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Контейнер для содержимого с прокруткой
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)

        # Основные показатели (4 карточки)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Карточка с общим количеством боев
        self.total_battles_card = StatCard(
            "Всего боёв",
            "0",
            Styles.COLORS["primary"],
            "battle"
        )
        stats_layout.addWidget(self.total_battles_card)

        # Карточка с процентом побед
        self.win_rate_card = StatCard(
            "Процент побед",
            "0%",
            Styles.COLORS["secondary"],
            "victory_rate"
        )
        stats_layout.addWidget(self.win_rate_card)

        # Карточка с ключами
        self.total_keys_card = StatCard(
            "Всего ключей",
            "0",
            Styles.COLORS["warning"],
            "key"
        )
        stats_layout.addWidget(self.total_keys_card)

        # Карточка с общим временем игры
        self.total_time_card = StatCard(
            "Общее время игры",
            "0 ч",
            Styles.COLORS["primary"],
            "time"
        )
        stats_layout.addWidget(self.total_time_card)

        scroll_layout.addLayout(stats_layout)

        # Графики трендов (2 секции в ряд)
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)

        # График тренда побед и поражений
        battles_chart_frame = QFrame()
        battles_chart_frame.setObjectName("section_box")
        battles_chart_layout = QVBoxLayout(battles_chart_frame)
        battles_chart_layout.setContentsMargins(0, 0, 0, 0)
        battles_chart_layout.setSpacing(0)

        battles_chart_header = QLabel("Тренд побед и поражений (7 дней)")
        battles_chart_header.setObjectName("header")
        battles_chart_layout.addWidget(battles_chart_header)

        # Место для графика побед и поражений
        self.battles_chart_placeholder = QLabel("График будет отображен при наличии данных")
        self.battles_chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.battles_chart_placeholder.setFixedHeight(200)
        self.battles_chart_placeholder.setStyleSheet(f"""
            background-color: {Styles.COLORS['background_medium']};
            color: {Styles.COLORS['text_secondary']};
            border-radius: 4px;
        """)
        battles_chart_layout.addWidget(self.battles_chart_placeholder)

        # Легенда для графика
        chart_legend_layout = QHBoxLayout()
        chart_legend_layout.setContentsMargins(15, 10, 15, 15)

        victory_legend = QLabel("● Победы")
        victory_legend.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        chart_legend_layout.addWidget(victory_legend)

        defeat_legend = QLabel("● Поражения")
        defeat_legend.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        chart_legend_layout.addWidget(defeat_legend)

        chart_legend_layout.addStretch()

        battles_chart_layout.addLayout(chart_legend_layout)

        charts_layout.addWidget(battles_chart_frame)

        # График сбора ключей
        keys_chart_frame = QFrame()
        keys_chart_frame.setObjectName("section_box")
        keys_chart_layout = QVBoxLayout(keys_chart_frame)
        keys_chart_layout.setContentsMargins(0, 0, 0, 0)
        keys_chart_layout.setSpacing(0)

        keys_chart_header = QLabel("Сбор ключей (7 дней)")
        keys_chart_header.setObjectName("header")
        keys_chart_layout.addWidget(keys_chart_header)

        # Место для графика ключей
        self.keys_chart_placeholder = QLabel("График будет отображен при наличии данных")
        self.keys_chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keys_chart_placeholder.setFixedHeight(200)
        self.keys_chart_placeholder.setStyleSheet(f"""
            background-color: {Styles.COLORS['background_medium']};
            color: {Styles.COLORS['text_secondary']};
            border-radius: 4px;
        """)
        keys_chart_layout.addWidget(self.keys_chart_placeholder)

        # Легенда для графика ключей
        keys_legend_layout = QHBoxLayout()
        keys_legend_layout.setContentsMargins(15, 10, 15, 15)

        keys_legend = QLabel("● Собрано ключей")
        keys_legend.setStyleSheet(f"color: {Styles.COLORS['warning']};")
        keys_legend_layout.addWidget(keys_legend)

        keys_legend_layout.addStretch()

        keys_chart_layout.addLayout(keys_legend_layout)

        charts_layout.addWidget(keys_chart_frame)

        scroll_layout.addLayout(charts_layout)

        # Таблица ежедневной статистики
        daily_stats_frame = QFrame()
        daily_stats_frame.setObjectName("section_box")
        daily_stats_layout = QVBoxLayout(daily_stats_frame)
        daily_stats_layout.setContentsMargins(0, 0, 0, 0)
        daily_stats_layout.setSpacing(0)

        daily_stats_header = QLabel("Ежедневная статистика (7 дней)")
        daily_stats_header.setObjectName("header")
        daily_stats_layout.addWidget(daily_stats_header)

        # Таблица статистики
        self.daily_stats_table = StyledTable()
        self.daily_stats_table.setColumnCount(8)
        self.daily_stats_table.setHorizontalHeaderLabels([
            "Дата", "Боёв", "Победы", "Поражения",
            "% побед", "Ключей", "Ключей/победа", "Потерь связи"
        ])

        daily_stats_layout.addWidget(self.daily_stats_table)

        scroll_layout.addWidget(daily_stats_frame)

        # Устанавливаем виджет содержимого в область прокрутки
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Инициализация данных
        self.refresh_statistics()

    def update_stats_period(self):
        """Обновляет статистику на основе выбранного периода."""
        self.refresh_statistics()

    def refresh_statistics(self):
        """Обновляет все отображения статистики."""
        # Проверяем, доступен ли stats_manager
        if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
            return

        try:
            # Получаем выбранный период
            period_index = self.period_combo.currentIndex()
            period_mapping = {
                0: "day",
                1: "week",
                2: "month",
                3: "all"
            }
            period = period_mapping.get(period_index, "all")

            # Получаем статистику для выбранного периода
            stats_data = self.bot_engine.stats_manager.get_stats_by_period(period)

            # Обновляем карточки с основными показателями
            total_battles = stats_data["stats"]["victories"] + stats_data["stats"]["defeats"]
            self.total_battles_card.set_value(str(total_battles))

            win_rate = stats_data.get("win_rate", 0)
            self.win_rate_card.set_value(f"{win_rate:.1f}%")

            self.total_keys_card.set_value(str(stats_data["stats"]["keys_collected"]))
            self.total_time_card.set_value(f"{stats_data.get('total_duration_hours', 0):.1f} ч")

            # Обновляем графики трендов
            self.update_trend_charts()

            # Обновляем таблицу ежедневной статистики
            self.update_daily_stats_table()

        except Exception as e:
            print(f"Ошибка при обновлении статистики: {e}")
            import traceback
            print(traceback.format_exc())

    def update_trend_charts(self):
        """Обновляет графики трендов с последними данными."""
        try:
            # Проверяем, доступен ли stats_manager
            if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
                return

            # Получаем данные трендов
            trend_data = self.bot_engine.stats_manager.get_trend_data()

            # Проверяем, достаточно ли данных для отображения
            if not trend_data or len(trend_data.get("dates", [])) <= 1:
                return

            # Обновляем графики
            # В реальной реализации здесь должен быть код для создания графиков
            # Для сейчас просто обновим текст в заполнителях

            battles_text = "График побед и поражений:\n"
            for i, date in enumerate(trend_data["dates"]):
                battles_text += f"{date}: Победы: {trend_data['victories'][i]}, Поражения: {trend_data['defeats'][i]}\n"
            self.battles_chart_placeholder.setText(battles_text)

            keys_text = "График собранных ключей:\n"
            for i, date in enumerate(trend_data["dates"]):
                keys_text += f"{date}: Ключей: {trend_data['keys_collected'][i]}\n"
            self.keys_chart_placeholder.setText(keys_text)

        except Exception as e:
            print(f"Ошибка при обновлении графиков: {e}")

    def update_daily_stats_table(self):
        """Обновляет таблицу ежедневной статистики."""
        try:
            # Получаем ежедневную статистику
            daily_stats = self.bot_engine.stats_manager.get_daily_stats(7)

            # Очищаем существующие строки
            self.daily_stats_table.setRowCount(0)

            # Заполняем таблицу данными
            for row, day in enumerate(daily_stats):
                self.daily_stats_table.insertRow(row)

                # Дата
                self.daily_stats_table.setItem(row, 0, QTableWidgetItem(day["display_date"]))

                # Подсчитываем бои
                battles = day["stats"]["victories"] + day["stats"]["defeats"]
                self.daily_stats_table.setItem(row, 1, QTableWidgetItem(str(battles)))

                # Победы
                self.daily_stats_table.setItem(row, 2, QTableWidgetItem(str(day["stats"]["victories"])))

                # Поражения
                self.daily_stats_table.setItem(row, 3, QTableWidgetItem(str(day["stats"]["defeats"])))

                # Процент побед
                win_rate = day.get("win_rate", 0)
                self.daily_stats_table.setItem(row, 4, QTableWidgetItem(f"{win_rate:.1f}%"))

                # Собрано ключей
                self.daily_stats_table.setItem(row, 5, QTableWidgetItem(str(day["stats"]["keys_collected"])))

                # Ключей за победу
                keys_per_victory = day.get("keys_per_victory", 0)
                self.daily_stats_table.setItem(row, 6, QTableWidgetItem(f"{keys_per_victory:.1f}"))

                # Потери связи
                self.daily_stats_table.setItem(row, 7, QTableWidgetItem(str(day["stats"]["connection_losses"])))

        except Exception as e:
            print(f"Ошибка при обновлении таблицы ежедневной статистики: {e}")