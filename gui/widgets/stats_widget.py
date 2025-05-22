from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QSizePolicy,
    QTabWidget, QPushButton, QApplication, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import logging
from functools import wraps

from gui.styles import Styles
from gui.components.stat_card import StatCard
from gui.components.styled_table import StyledTable
from gui.widgets.chart_widgets import BattlesChartWidget, KeysChartWidget, SilverChartWidget


def handle_stats_errors(default_return=None):
    """Декоратор для обработки ошибок в методах статистики."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self._py_logger.error(f"Ошибка в {func.__name__}: {e}")
                import traceback
                self._py_logger.error(traceback.format_exc())
                return default_return

        return wrapper

    return decorator


class StatsDataProvider:
    """Централизованный провайдер данных статистики."""

    PERIOD_MAPPING = {0: "day", 1: "week", 2: "month", 3: "all"}

    def __init__(self, bot_engine, period_combo, logger):
        self.bot_engine = bot_engine
        self.period_combo = period_combo
        self._py_logger = logger

    @property
    def stats_manager(self):
        """Безопасный доступ к stats_manager."""
        if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
            return None
        return self.bot_engine.stats_manager

    @property
    def current_period(self):
        """Получить текущий выбранный период."""
        return self.PERIOD_MAPPING.get(self.period_combo.currentIndex(), "all")

    @property
    def current_session_stats(self):
        """Получить статистику текущей сессии если нужно."""
        if not self.bot_engine.running.is_set():
            return None
        if getattr(self.bot_engine, 'session_stats_registered', False):
            return None
        return self.bot_engine.stats

    @handle_stats_errors(default_return={})
    def get_period_stats(self, include_current_session=True):
        """Получить статистику за период."""
        if not self.stats_manager:
            return {}

        # Принудительно загружаем свежие данные
        self.stats_manager.load_stats()

        current_stats = self.current_session_stats if include_current_session else None
        return self.stats_manager.get_stats_by_period_with_current_session(
            self.current_period, current_stats
        )

    @handle_stats_errors(default_return={})
    def get_trend_data(self, include_current_session=True):
        """Получить данные трендов."""
        if not self.stats_manager:
            return {}

        current_stats = self.current_session_stats if include_current_session else None
        return self.stats_manager.get_trend_data_with_current_session(current_stats)

    @handle_stats_errors(default_return=[])
    def get_daily_stats(self, days=7, include_current_session=True):
        """Получить ежедневную статистику."""
        if not self.stats_manager:
            return []

        current_stats = self.current_session_stats if include_current_session else None
        return self.stats_manager.get_daily_stats_with_current_session(days, current_stats)


class ComponentUpdater:
    """Универсальный обновлятор компонентов интерфейса."""

    def __init__(self, stats_widget, data_provider, logger):
        self.widget = stats_widget
        self.data_provider = data_provider
        self._py_logger = logger

    @handle_stats_errors()
    def update_stats_cards(self, stats_data=None):
        """Обновляет карточки с основными показателями."""
        if stats_data is None:
            stats_data = self.data_provider.get_period_stats()

        if not stats_data.get("stats"):
            return

        stats = stats_data["stats"]
        victories = stats.get("victories", 0)
        defeats = stats.get("defeats", 0)

        # Обновляем карточки
        self.widget.total_battles_card.set_value(str(victories + defeats))
        self.widget.win_rate_card.set_value(f"{stats_data.get('win_rate', 0):.1f}%")
        self.widget.total_keys_card.set_value(str(stats.get("keys_collected", 0)))

        # Безопасное обновление серебра
        try:
            silver_formatted = Styles.format_silver(stats.get("silver_collected", 0))
            self.widget.total_silver_card.set_value(silver_formatted)
        except Exception as e:
            self._py_logger.error(f"Ошибка при форматировании серебра: {e}")
            self.widget.total_silver_card.set_value("0K")

    @handle_stats_errors()
    def update_trend_charts(self, trend_data=None, allow_animation=False):
        """Обновляет графики трендов."""
        if trend_data is None:
            trend_data = self.data_provider.get_trend_data()

        if not trend_data or len(trend_data.get("dates", [])) < 1:
            self._py_logger.warning("Недостаточно данных для отображения графиков")
            self._clear_all_charts()
            return

        force_no_animation = not allow_animation

        # Обновляем все графики
        chart_configs = [
            (self.widget.battles_chart_widget, "график боев"),
            (self.widget.keys_chart_widget, "график ключей"),
            (self.widget.silver_chart_widget, "график серебра")
        ]

        for chart_widget, chart_name in chart_configs:
            try:
                chart_widget.update_chart(trend_data, force_no_animation=force_no_animation)
                self._py_logger.debug(f"Обновлен {chart_name}: {len(trend_data['dates'])} точек")
            except Exception as e:
                self._py_logger.error(f"Ошибка при обновлении {chart_name}: {e}")

    @handle_stats_errors()
    def update_daily_stats_table(self, daily_stats=None):
        """Обновляет таблицу ежедневной статистики."""
        if daily_stats is None:
            daily_stats = self.data_provider.get_daily_stats()

        table = self.widget.daily_stats_table
        table.setRowCount(0)

        for row, day in enumerate(daily_stats):
            table.insertRow(row)
            stats = day["stats"]

            # Заполняем строку данными
            table.setItem(row, 0, QTableWidgetItem(day["display_date"]))
            table.setItem(row, 1, QTableWidgetItem(str(stats["victories"] + stats["defeats"])))
            table.setItem(row, 2, QTableWidgetItem(str(stats["victories"])))
            table.setItem(row, 3, QTableWidgetItem(str(stats["defeats"])))
            table.setItem(row, 4, QTableWidgetItem(f"{day.get('win_rate', 0):.1f}%"))
            table.setItem(row, 5, QTableWidgetItem(str(stats["keys_collected"])))
            table.setItem(row, 6, QTableWidgetItem(f"{day.get('keys_per_victory', 0):.1f}"))

            # Безопасное форматирование серебра
            try:
                silver_formatted = Styles.format_silver(stats.get("silver_collected", 0))
                table.setItem(row, 7, QTableWidgetItem(silver_formatted))
            except Exception as e:
                self._py_logger.error(f"Ошибка при форматировании серебра для таблицы: {e}")
                table.setItem(row, 7, QTableWidgetItem("0K"))

            table.setItem(row, 8, QTableWidgetItem(str(stats["connection_losses"])))

        table.customize_cell_colors()

    def _clear_all_charts(self):
        """Очищает все графики."""
        for chart in [self.widget.battles_chart_widget, self.widget.keys_chart_widget,
                      self.widget.silver_chart_widget]:
            chart.clear()


class StatsWidget(QWidget):
    """Страница статистики и аналитики."""

    request_refresh = pyqtSignal()

    def __init__(self, bot_engine, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine
        self._py_logger = logging.getLogger("BotLogger")

        # Инициализация провайдеров
        self.data_provider = None  # Будет инициализирован после создания UI
        self.updater = None

        # Инициализация UI
        self.init_ui()

        # Создаем провайдеры после инициализации UI
        self.data_provider = StatsDataProvider(self.bot_engine, self.period_combo, self._py_logger)
        self.updater = ComponentUpdater(self, self.data_provider, self._py_logger)

        # Подключаем таймер автоматического обновления
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.auto_refresh_statistics)
        self.update_timer.start(3000)

    def init_ui(self):
        """Инициализация интерфейса страницы статистики."""
        # Основной лэйаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Заголовок и выбор периода
        self._create_header(layout)

        # Создаем виджет с вкладками
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet("QTabBar::tab { padding: 8px 16px; font-size: 14px; }")

        # Создаем вкладки
        self.overview_tab = QWidget()
        self.daily_stats_tab = QWidget()

        self._setup_overview_tab()
        self._setup_daily_stats_tab()

        self.tab_widget.addTab(self.overview_tab, "Обзор")
        self.tab_widget.addTab(self.daily_stats_tab, "Ежедневная статистика")

        layout.addWidget(self.tab_widget)

        # Инициализация данных
        self.refresh_statistics()

    def _create_header(self, layout):
        """Создает заголовок страницы."""
        header_layout = QHBoxLayout()

        # Заголовок
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

        # Выбор периода
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

    def _setup_overview_tab(self):
        """Настройка вкладки с обзором статистики."""
        overview_layout = QVBoxLayout(self.overview_tab)
        overview_layout.setContentsMargins(0, 10, 0, 0)
        overview_layout.setSpacing(20)

        # Кнопки управления
        self._create_control_buttons(overview_layout)

        # Область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)

        # Карточки статистики
        self._create_stats_cards(scroll_layout)

        # Графики
        self._create_charts(scroll_layout)

        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        overview_layout.addWidget(scroll_area)

    def _create_control_buttons(self, layout):
        """Создает кнопки управления."""
        refresh_button_layout = QHBoxLayout()
        refresh_button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.auto_refresh_checkbox = QCheckBox("Автоматическое обновление")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        refresh_button_layout.addWidget(self.auto_refresh_checkbox)

        refresh_button_layout.addStretch()

        self.refresh_stats_button = QPushButton("🔄 Обновить статистику")
        self.refresh_stats_button.setObjectName("primary")
        self.refresh_stats_button.setFixedWidth(200)
        self.refresh_stats_button.setMinimumHeight(30)
        self.refresh_stats_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_stats_button.clicked.connect(self.refresh_statistics)
        refresh_button_layout.addWidget(self.refresh_stats_button)

        layout.addLayout(refresh_button_layout)

    def _create_stats_cards(self, layout):
        """Создает карточки со статистикой."""
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Карточки
        card_configs = [
            ("total_battles_card", "Всего боёв", "0", Styles.COLORS["primary"]),
            ("win_rate_card", "Процент побед", "0%", Styles.COLORS["secondary"]),
            ("total_keys_card", "Всего ключей", "0", Styles.COLORS["warning"]),
            ("total_silver_card", "Всего серебра", "0K", Styles.COLORS["primary"])
        ]

        for attr_name, title, value, color in card_configs:
            card = StatCard(title, value, color)
            setattr(self, attr_name, card)
            stats_layout.addWidget(card)

        stats_container = QWidget()
        stats_container.setLayout(stats_layout)
        stats_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout.addWidget(stats_container)

    def _create_charts(self, layout):
        """Создает графики."""
        # Первый ряд графиков
        charts_layout1 = QHBoxLayout()
        charts_layout1.setSpacing(15)

        self.battles_chart_widget = BattlesChartWidget()
        self.silver_chart_widget = SilverChartWidget()

        for chart_widget in [self.battles_chart_widget, self.silver_chart_widget]:
            chart_frame = QFrame()
            chart_frame.setObjectName("section_box")
            chart_layout = QVBoxLayout(chart_frame)
            chart_layout.setContentsMargins(0, 0, 0, 0)
            chart_layout.addWidget(chart_widget)
            charts_layout1.addWidget(chart_frame)

        layout.addLayout(charts_layout1)

        # Второй ряд - график ключей
        keys_chart_layout = QHBoxLayout()
        keys_chart_layout.setSpacing(15)

        self.keys_chart_widget = KeysChartWidget()
        keys_chart_frame = QFrame()
        keys_chart_frame.setObjectName("section_box")
        keys_layout = QVBoxLayout(keys_chart_frame)
        keys_layout.setContentsMargins(0, 0, 0, 0)
        keys_layout.addWidget(self.keys_chart_widget)

        keys_chart_layout.addWidget(keys_chart_frame)
        layout.addLayout(keys_chart_layout)

    def _setup_daily_stats_tab(self):
        """Настройка вкладки с ежедневной статистикой."""
        daily_stats_layout = QVBoxLayout(self.daily_stats_tab)
        daily_stats_layout.setContentsMargins(0, 10, 0, 0)
        daily_stats_layout.setSpacing(15)

        # Заголовок и кнопка
        top_layout = QHBoxLayout()

        description_label = QLabel("Показатели за последние 7 дней с детализацией по дням")
        description_label.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        top_layout.addWidget(description_label)
        top_layout.addStretch(1)

        self.refresh_daily_stats_button = QPushButton("🔄 Обновить статистику")
        self.refresh_daily_stats_button.setObjectName("primary")
        self.refresh_daily_stats_button.setFixedWidth(200)
        self.refresh_daily_stats_button.setMinimumHeight(30)
        self.refresh_daily_stats_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_daily_stats_button.clicked.connect(self.refresh_statistics)
        top_layout.addWidget(self.refresh_daily_stats_button)

        daily_stats_layout.addLayout(top_layout)

        # Таблица
        daily_stats_frame = QFrame()
        daily_stats_frame.setObjectName("section_box")
        daily_stats_layout_frame = QVBoxLayout(daily_stats_frame)
        daily_stats_layout_frame.setContentsMargins(0, 0, 0, 0)

        daily_stats_header = QLabel("Ежедневная статистика (7 дней)")
        daily_stats_header.setObjectName("header")
        daily_stats_layout_frame.addWidget(daily_stats_header)

        self.daily_stats_table = StyledTable()
        self.daily_stats_table.setColumnCount(9)
        self.daily_stats_table.setHorizontalHeaderLabels([
            "Дата", "Боёв", "Победы", "Поражения",
            "% побед", "Ключей", "Ключей/победа", "Серебро", "Потерь связи"
        ])
        self.daily_stats_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.daily_stats_table.setMinimumHeight(300)

        daily_stats_layout_frame.addWidget(self.daily_stats_table, 1)
        daily_stats_layout.addWidget(daily_stats_frame, 1)

        # Индикатор автообновления
        self.auto_refresh_indicator = QLabel("Статистика обновляется автоматически")
        self.auto_refresh_indicator.setStyleSheet(f"""
            color: {Styles.COLORS['secondary']};
            font-style: italic;
            padding: 5px;
        """)
        self.auto_refresh_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        daily_stats_layout.addWidget(self.auto_refresh_indicator)

    def toggle_auto_refresh(self, state):
        """Включает/выключает автоматическое обновление статистики."""
        if state:
            self.update_timer.start(3000)
            self.auto_refresh_indicator.setText("Статистика обновляется автоматически")
            self.auto_refresh_indicator.setStyleSheet(
                f"color: {Styles.COLORS['secondary']}; font-style: italic; padding: 5px;")
        else:
            self.update_timer.stop()
            self.auto_refresh_indicator.setText("Автообновление отключено. Используйте кнопку обновления")
            self.auto_refresh_indicator.setStyleSheet(
                f"color: {Styles.COLORS['accent']}; font-style: italic; padding: 5px;")

    def auto_refresh_statistics(self):
        """Автоматически обновляет статистику с текущей сессией."""
        if not self.bot_engine.running.is_set():
            return

        if getattr(self.bot_engine, 'session_stats_registered', False):
            # Сессия зарегистрирована - обновляем без текущих данных
            try:
                self.data_provider.stats_manager.load_stats()
                self.updater.update_stats_cards()
                self.updater.update_trend_charts()
                self.updater.update_daily_stats_table()
            except Exception as e:
                self._py_logger.error(f"Ошибка при обновлении исторической статистики: {e}")
        else:
            # Сессия не зарегистрирована - полное обновление
            self.refresh_statistics(show_message=False, loading_animation=False)

    def update_stats_period(self):
        """Обновляет статистику на основе выбранного периода."""
        self._py_logger.info(f"Изменение периода статистики на: {self.data_provider.current_period}")
        self.refresh_statistics(show_message=True)

    @handle_stats_errors()
    def refresh_statistics(self, show_message=True, loading_animation=True):
        """Обновляет все отображения статистики."""
        if not self.data_provider.stats_manager:
            self._py_logger.warning("StatsManager недоступен")
            return

        if loading_animation:
            # Управление состоянием кнопок
            self._set_loading_state(True)

        try:
            if show_message:
                self._py_logger.debug("Обновление статистики запущено...")

            # Обновляем все компоненты через единый интерфейс
            self.updater.update_stats_cards()
            self.updater.update_trend_charts(allow_animation=True)
            self.updater.update_daily_stats_table()

            if show_message:
                self._py_logger.debug("Обновление статистики завершено успешно")
                self._show_update_success_message()

            self.request_refresh.emit()

        finally:
            if loading_animation:
                self._set_loading_state(False)

    def _set_loading_state(self, loading):
        """Управляет состоянием кнопок во время загрузки."""
        buttons = [self.refresh_stats_button]
        if hasattr(self, 'refresh_daily_stats_button'):
            buttons.append(self.refresh_daily_stats_button)

        for button in buttons:
            if loading:
                button.setEnabled(False)
                if not hasattr(button, '_original_text'):
                    button._original_text = button.text()
                button.setText("⏳ Обновление...")
            else:
                button.setEnabled(True)
                if hasattr(button, '_original_text'):
                    button.setText(button._original_text)

        if loading:
            QApplication.processEvents()

    def _show_update_success_message(self):
        """Показывает сообщение об успешном обновлении."""
        try:
            success_label = QLabel("✓ Данные успешно обновлены", self)
            success_label.setStyleSheet(f"""
                background-color: {Styles.COLORS['secondary']};
                color: {Styles.COLORS['background_dark']};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            """)
            success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            success_label.adjustSize()
            success_label.move(self.width() - success_label.width() - 20, 20)
            success_label.show()

            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, success_label.deleteLater)
        except Exception as e:
            self._py_logger.error(f"Ошибка при показе сообщения: {e}")

    # Методы совместимости для внешнего API
    def update_stats_cards(self):
        """Публичный метод для обновления карточек."""
        if self.updater:
            self.updater.update_stats_cards()

    def update_trend_charts(self, trend_data=None, allow_animation=False):
        """Публичный метод для обновления графиков."""
        if self.updater:
            self.updater.update_trend_charts(trend_data, allow_animation)

    def update_daily_stats_table(self, daily_stats=None):
        """Публичный метод для обновления таблицы."""
        if self.updater:
            self.updater.update_daily_stats_table(daily_stats)

    def showEvent(self, event):
        """Обработчик события показа виджета статистики."""
        super().showEvent(event)
        # Настройка анимации для графиков
        for chart_widget in [self.battles_chart_widget, self.keys_chart_widget, self.silver_chart_widget]:
            if hasattr(chart_widget, 'should_animate_next'):
                chart_widget.should_animate_next = True
                chart_widget.has_animated_since_show = False
        self._py_logger.debug("Вкладка статистики показана")

    def hideEvent(self, event):
        """Обработчик события скрытия виджета."""
        super().hideEvent(event)
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()