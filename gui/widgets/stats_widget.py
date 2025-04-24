from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QSizePolicy,
    QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from gui.styles import Styles
from gui.components.stat_card import StatCard
from gui.components.styled_table import StyledTable
from gui.widgets.chart_widgets import BattlesChartWidget, KeysChartWidget


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

        # Создаем виджет с вкладками
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)  # Более современный вид вкладок
        self.tab_widget.setStyleSheet(f"""
            QTabBar::tab {{
                padding: 8px 16px;
                font-size: 14px;
            }}
        """)

        # Создаем первую вкладку для обзора (графики и основные показатели)
        self.overview_tab = QWidget()
        self.setup_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "Обзор")

        # Создаем вторую вкладку для ежедневной статистики
        self.daily_stats_tab = QWidget()
        self.setup_daily_stats_tab()
        self.tab_widget.addTab(self.daily_stats_tab, "Ежедневная статистика")

        # Добавляем виджет с вкладками в основной лейаут
        layout.addWidget(self.tab_widget)

        # Инициализация данных
        self.refresh_statistics()

    def setup_overview_tab(self):
        """Настройка вкладки с обзором статистики."""
        overview_layout = QVBoxLayout(self.overview_tab)
        overview_layout.setContentsMargins(0, 10, 0, 0)
        overview_layout.setSpacing(20)

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
        stats_layout.setContentsMargins(0, 0, 0, 0)  # Убираем внутренние отступы

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

        # Устанавливаем фиксированную высоту для контейнера карточек
        stats_container = QWidget()
        stats_container.setLayout(stats_layout)
        stats_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        stats_container.setContentsMargins(0, 0, 0, 0)  # Убираем отступы контейнера

        scroll_layout.addWidget(stats_container)

        # Графики трендов (2 секции в ряд)
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)
        charts_layout.setContentsMargins(0, 0, 0, 0)  # Убираем внутренние отступы

        # Создаем виджеты графиков
        self.battles_chart_widget = BattlesChartWidget()
        self.keys_chart_widget = KeysChartWidget()

        # Добавляем виджеты графиков в лейаут
        battles_chart_frame = QFrame()
        battles_chart_frame.setObjectName("section_box")
        battles_chart_layout = QVBoxLayout(battles_chart_frame)
        battles_chart_layout.setContentsMargins(0, 0, 0, 0)
        battles_chart_layout.setSpacing(0)
        battles_chart_layout.addWidget(self.battles_chart_widget)
        charts_layout.addWidget(battles_chart_frame)

        keys_chart_frame = QFrame()
        keys_chart_frame.setObjectName("section_box")
        keys_chart_layout = QVBoxLayout(keys_chart_frame)
        keys_chart_layout.setContentsMargins(0, 0, 0, 0)
        keys_chart_layout.setSpacing(0)
        keys_chart_layout.addWidget(self.keys_chart_widget)
        charts_layout.addWidget(keys_chart_frame)

        scroll_layout.addLayout(charts_layout)

        # Добавляем растяжку внизу для лучшего отображения на разных разрешениях
        scroll_layout.addStretch(1)

        # Устанавливаем виджет содержимого в область прокрутки
        scroll_area.setWidget(scroll_content)
        overview_layout.addWidget(scroll_area)

    def setup_daily_stats_tab(self):
        """Настройка вкладки с ежедневной статистикой."""
        daily_stats_layout = QVBoxLayout(self.daily_stats_tab)
        daily_stats_layout.setContentsMargins(0, 10, 0, 0)
        daily_stats_layout.setSpacing(15)

        # Описание таблицы
        description_label = QLabel("Показатели за последние 7 дней с детализацией по дням")
        description_label.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        daily_stats_layout.addWidget(description_label)

        # Таблица ежедневной статистики в рамке с заголовком
        daily_stats_frame = QFrame()
        daily_stats_frame.setObjectName("section_box")
        daily_stats_layout_frame = QVBoxLayout(daily_stats_frame)
        daily_stats_layout_frame.setContentsMargins(0, 0, 0, 0)
        daily_stats_layout_frame.setSpacing(0)

        # Заголовок таблицы
        daily_stats_header = QLabel("Ежедневная статистика (7 дней)")
        daily_stats_header.setObjectName("header")
        daily_stats_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        daily_stats_layout_frame.addWidget(daily_stats_header)

        # Таблица статистики
        self.daily_stats_table = StyledTable()
        self.daily_stats_table.setColumnCount(8)
        self.daily_stats_table.setHorizontalHeaderLabels([
            "Дата", "Боёв", "Победы", "Поражения",
            "% побед", "Ключей", "Ключей/победа", "Потерь связи"
        ])

        # Устанавливаем растяжение для стилизованной таблицы
        self.daily_stats_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.daily_stats_table.setMinimumHeight(300)  # Минимальная высота для удобства просмотра

        daily_stats_layout_frame.addWidget(self.daily_stats_table, 1)
        daily_stats_layout.addWidget(daily_stats_frame, 1)

        # Легенда для таблицы
        legend_frame = QFrame()
        legend_frame.setStyleSheet(f"background-color: {Styles.COLORS['background_light']}; border-radius: 8px;")
        legend_layout = QHBoxLayout(legend_frame)

        legend_title = QLabel("Цветовые обозначения:")
        legend_title.setStyleSheet("font-weight: bold;")
        legend_layout.addWidget(legend_title)

        victory_legend = QLabel("● Победы")
        victory_legend.setStyleSheet(f"color: {Styles.COLORS['secondary']};")
        legend_layout.addWidget(victory_legend)

        defeat_legend = QLabel("● Поражения")
        defeat_legend.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        legend_layout.addWidget(defeat_legend)

        key_legend = QLabel("● Ключи")
        key_legend.setStyleSheet(f"color: {Styles.COLORS['warning']};")
        legend_layout.addWidget(key_legend)

        connection_legend = QLabel("● Потери связи")
        connection_legend.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        legend_layout.addWidget(connection_legend)

        legend_layout.addStretch()

        daily_stats_layout.addWidget(legend_frame)

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
            self.update_stats_cards(stats_data)

            # Обновляем графики трендов
            self.update_trend_charts()

            # Обновляем таблицу ежедневной статистики
            self.update_daily_stats_table()

        except Exception as e:
            import logging
            logging.error(f"Ошибка при обновлении статистики: {e}")
            import traceback
            logging.error(traceback.format_exc())

    def update_stats_cards(self, stats_data=None):
        """Обновляет карточки с основными показателями."""
        if stats_data is None:
            # Если данные не переданы, пытаемся получить их
            if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
                return

            # Получаем выбранный период
            period_index = self.period_combo.currentIndex()
            period_mapping = {
                0: "day",
                1: "week",
                2: "month",
                3: "all"
            }
            period = period_mapping.get(period_index, "all")

            stats_data = self.bot_engine.stats_manager.get_stats_by_period(period)

        # Обновляем карточки с основными показателями
        total_battles = stats_data["stats"]["victories"] + stats_data["stats"]["defeats"]
        self.total_battles_card.set_value(str(total_battles))

        win_rate = stats_data.get("win_rate", 0)
        self.win_rate_card.set_value(f"{win_rate:.1f}%")

        self.total_keys_card.set_value(str(stats_data["stats"]["keys_collected"]))
        self.total_time_card.set_value(f"{stats_data.get('total_duration_hours', 0):.1f} ч")

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
                # Недостаточно данных - очищаем графики
                self.battles_chart_widget.clear()
                self.keys_chart_widget.clear()
                return

            # Обновляем графики (без частой перезагрузки кэша)
            if not hasattr(self, '_last_chart_update') or trend_data != self._last_chart_update:
                self._last_chart_update = trend_data
                # Обновляем графики только если данные изменились
                self.battles_chart_widget.update_chart(trend_data)
                self.keys_chart_widget.update_chart(trend_data)

        except Exception as e:
            import logging
            logging.error(f"Ошибка при обновлении графиков: {e}")
            import traceback
            logging.error(traceback.format_exc())

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

            # Настройка цветовой индикации
            self.daily_stats_table.customize_cell_colors()

        except Exception as e:
            import logging
            logging.error(f"Ошибка при обновлении таблицы ежедневной статистики: {e}")
            import traceback
            logging.error(traceback.format_exc())