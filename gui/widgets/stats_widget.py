from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QSizePolicy,
    QTabWidget, QPushButton, QApplication, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import logging
import time
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
                return default_return

        return wrapper

    return decorator


class StatsDataCache:
    """Кэш данных для избежания множественных загрузок."""

    def __init__(self, logger):
        self._py_logger = logger
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_duration = 30  # Кэш действителен 30 секунд
        self._loading_flags = {}  # Флаги для предотвращения множественной загрузки

    def get_cached_or_load(self, key, load_func, force_reload=False):
        """Получает данные из кэша или загружает новые."""
        current_time = time.time()

        # Проверяем, не загружается ли уже этот ключ
        if key in self._loading_flags:
            self._py_logger.debug(f"Данные '{key}' уже загружаются, возвращаем из кэша")
            return self._cache.get(key, {})

        # Проверяем кэш
        if not force_reload and key in self._cache:
            cache_time = self._cache_timestamps.get(key, 0)
            if current_time - cache_time < self._cache_duration:
                self._py_logger.debug(f"Данные '{key}' получены из кэша")
                return self._cache[key]

        # Устанавливаем флаг загрузки
        self._loading_flags[key] = True

        try:
            # Загружаем новые данные
            data = load_func()
            self._cache[key] = data
            self._cache_timestamps[key] = current_time
            self._py_logger.debug(f"Данные '{key}' загружены и кэшированы")
            return data
        finally:
            # Убираем флаг загрузки
            self._loading_flags.pop(key, None)

    def invalidate(self, key=None):
        """Инвалидирует кэш."""
        if key:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
        self._py_logger.debug(f"Кэш {'полностью' if not key else key} инвалидирован")


class StatsDataProvider:
    """Оптимизированный провайдер данных статистики."""

    PERIOD_MAPPING = {0: "day", 1: "week", 2: "month", 3: "all"}

    def __init__(self, bot_engine, period_combo, logger):
        self.bot_engine = bot_engine
        self.period_combo = period_combo
        self._py_logger = logger
        self.cache = StatsDataCache(logger)
        self._stats_loaded = False  # Флаг для отслеживания загрузки

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

    def _ensure_stats_loaded_once(self):
        """Гарантирует, что данные загружены только один раз за сессию."""
        if not self._stats_loaded and self.stats_manager:
            self._py_logger.debug("Выполняется первоначальная загрузка статистики")
            self.stats_manager.load_stats()
            self._stats_loaded = True

    @handle_stats_errors(default_return={})
    def get_period_stats(self, include_current_session=True, force_reload=False):
        """Получить статистику за период с кэшированием."""
        if not self.stats_manager:
            return {}

        cache_key = f"period_stats_{self.current_period}_{include_current_session}"

        def load_data():
            # Загружаем данные только если еще не загружали или принудительно
            if force_reload:
                self.stats_manager.load_stats()
            else:
                self._ensure_stats_loaded_once()

            current_stats = self.current_session_stats if include_current_session else None
            return self.stats_manager.get_stats_by_period_with_current_session(
                self.current_period, current_stats
            )

        return self.cache.get_cached_or_load(cache_key, load_data, force_reload)

    @handle_stats_errors(default_return={})
    def get_trend_data(self, include_current_session=True, force_reload=False):
        """Получить данные трендов с кэшированием."""
        if not self.stats_manager:
            return {}

        cache_key = f"trend_data_{include_current_session}"

        def load_data():
            # Избегаем повторной загрузки данных
            if force_reload:
                self.stats_manager.load_stats()
            else:
                self._ensure_stats_loaded_once()

            current_stats = self.current_session_stats if include_current_session else None
            return self.stats_manager.get_trend_data_with_current_session(current_stats)

        return self.cache.get_cached_or_load(cache_key, load_data, force_reload)

    @handle_stats_errors(default_return=[])
    def get_daily_stats(self, days=7, include_current_session=True, force_reload=False):
        """Получить ежедневную статистику с кэшированием."""
        if not self.stats_manager:
            return []

        cache_key = f"daily_stats_{days}_{include_current_session}"

        def load_data():
            # Избегаем повторной загрузки данных
            if force_reload:
                self.stats_manager.load_stats()
            else:
                self._ensure_stats_loaded_once()

            current_stats = self.current_session_stats if include_current_session else None
            return self.stats_manager.get_daily_stats_with_current_session(days, current_stats)

        return self.cache.get_cached_or_load(cache_key, load_data, force_reload)

    def invalidate_cache(self):
        """Инвалидирует весь кэш."""
        self.cache.invalidate()
        self._stats_loaded = False  # Сбрасываем флаг загрузки


class ComponentUpdater:
    """Обновлятор компонентов интерфейса."""

    def __init__(self, stats_widget, data_provider, logger):
        self.widget = stats_widget
        self.data_provider = data_provider
        self._py_logger = logger

    @handle_stats_errors()
    def update_stats_cards(self, stats_data=None, force_reload=False):
        """Обновляет карточки с основными показателями."""
        if stats_data is None:
            stats_data = self.data_provider.get_period_stats(force_reload=force_reload)

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
    def update_trend_charts(self, trend_data=None, enable_animation=False, force_reload=False):
        """Обновляет графики трендов."""
        if trend_data is None:
            trend_data = self.data_provider.get_trend_data(force_reload=force_reload)

        if not trend_data or len(trend_data.get("dates", [])) < 1:
            self._py_logger.warning("Недостаточно данных для отображения графиков")
            self._clear_all_charts()
            return

        chart_configs = [
            (self.widget.battles_chart_widget, "график боев"),
            (self.widget.keys_chart_widget, "график ключей"),
            (self.widget.silver_chart_widget, "график серебра")
        ]

        for chart_widget, chart_name in chart_configs:
            try:
                if not chart_widget.isVisible():
                    continue

                if enable_animation:
                    chart_widget.set_should_animate_once()

                chart_widget.update_chart(trend_data, force_no_animation=not enable_animation)
                self._py_logger.debug(f"Обновлен {chart_name}: {len(trend_data['dates'])} точек")

            except Exception as e:
                self._py_logger.error(f"Ошибка при обновлении {chart_name}: {e}")

    @handle_stats_errors()
    def update_chart_data_only(self, trend_data=None):
        """Обновляет только данные в графиках для тултипов."""
        if trend_data is None:
            trend_data = self.data_provider.get_trend_data(include_current_session=True, force_reload=False)

        if not trend_data or len(trend_data.get("dates", [])) < 1:
            return

        charts = [
            self.widget.battles_chart_widget,
            self.widget.keys_chart_widget,
            self.widget.silver_chart_widget
        ]

        for chart_widget in charts:
            try:
                if chart_widget.isVisible():
                    chart_widget.update_data_only(trend_data)
            except Exception as e:
                self._py_logger.error(f"Ошибка при обновлении данных графика: {e}")

    @handle_stats_errors()
    def update_daily_stats_table(self, daily_stats=None, force_reload=False):
        """Обновляет таблицу ежедневной статистики."""
        if daily_stats is None:
            daily_stats = self.data_provider.get_daily_stats(force_reload=force_reload)

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
    """Оптимизированная страница статистики и аналитики."""

    request_refresh = pyqtSignal()

    def __init__(self, bot_engine, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine
        self._py_logger = logging.getLogger("BotLogger")

        # Провайдеры и обновлятор
        self.data_provider = None
        self.updater = None

        # Состояние виджета
        self._is_currently_visible = False
        self._charts_initialized = False
        self._pending_animation = False  # НОВЫЙ ФЛАГ для предотвращения множественных анимаций
        self._initialization_complete = False  # Флаг завершения инициализации

        # Инициализация UI
        self.init_ui()

        # Создаем провайдеры после инициализации UI
        self.data_provider = StatsDataProvider(self.bot_engine, self.period_combo, self._py_logger)
        self.updater = ComponentUpdater(self, self.data_provider, self._py_logger)

        # Таймер для автоматического обновления тултипов
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.timeout.connect(self.update_tooltips_only)
        self.tooltip_timer.start(3000)  # Обновление тултипов каждые 3 секунды

        # Таймер для обновления карточек и таблиц
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.auto_refresh_statistics)
        self.update_timer.start(8000)  # УВЕЛИЧИЛИ интервал до 8 секунд

        # Инициализация данных БЕЗ принудительной перезагрузки
        self.refresh_statistics(force_reload=False)
        self._initialization_complete = True

    def init_ui(self):
        """Инициализация интерфейса страницы статистики."""
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

        # Заголовок
        description_label = QLabel("Показатели за последние 7 дней с детализацией по дням")
        description_label.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        daily_stats_layout.addWidget(description_label)

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

    def prepare_for_animation(self):
        """Подготавливает графики для анимации при следующем обновлении."""
        if not self._is_currently_visible or self._pending_animation:
            return

        try:
            self._pending_animation = True

            charts = [
                self.battles_chart_widget,
                self.keys_chart_widget,
                self.silver_chart_widget
            ]

            # НОВОЕ: Подготавливаем оси с пустыми данными вместо полной очистки
            for chart in charts:
                chart.prepare_axes_for_animation()  # Отрисовываем оси
                chart.set_should_animate_once()  # Устанавливаем флаг анимации

            self._py_logger.debug("Графики подготовлены: оси отрисованы, готовы к анимации столбцов")

        except Exception as e:
            self._py_logger.error(f"Ошибка при подготовке анимации: {e}")

    def execute_pending_animation(self):
        """Выполняет отложенную анимацию."""
        if not self._pending_animation:
            return

        try:
            # Обновляем графики с анимацией БЕЗ принудительной перезагрузки данных
            self.updater.update_trend_charts(enable_animation=True, force_reload=False)
            self._py_logger.debug("Анимация графиков выполнена")

        except Exception as e:
            self._py_logger.error(f"Ошибка при выполнении анимации: {e}")
        finally:
            self._pending_animation = False  # Сбрасываем флаг

    def update_tooltips_only(self):
        """Обновляет только тултипы в графиках."""
        if not self.bot_engine.running.is_set() or not self._is_currently_visible:
            return

        try:
            self.updater.update_chart_data_only()
        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении тултипов: {e}")

    def auto_refresh_statistics(self):
        """Автоматически обновляет статистику."""
        if not self._is_currently_visible or not self._initialization_complete:
            return

        try:
            # Обновляем карточки и таблицы без перезагрузки данных
            self.updater.update_stats_cards(force_reload=False)
            self.updater.update_daily_stats_table(force_reload=False)

        except Exception as e:
            self._py_logger.error(f"Ошибка при автоматическом обновлении: {e}")

    def update_stats_period(self):
        """Обновляет статистику на основе выбранного периода."""
        self._py_logger.info(f"Изменение периода статистики на: {self.data_provider.current_period}")
        # Инвалидируем кэш при смене периода
        self.data_provider.invalidate_cache()
        self.refresh_statistics(force_reload=True, enable_animation=False)

    @handle_stats_errors()
    def refresh_statistics(self, show_message=False, enable_animation=None, force_reload=False):
        """Обновляет все отображения статистики."""
        if not self.data_provider.stats_manager:
            self._py_logger.warning("StatsManager недоступен")
            return

        try:
            if show_message:
                self._py_logger.debug("Обновление статистики запущено...")

            # ИСПРАВЛЕНО: инвалидируем кэш только при явном запросе
            if force_reload:
                self.data_provider.invalidate_cache()

            should_animate = enable_animation is True

            # Обновляем компоненты
            self.updater.update_stats_cards(force_reload=force_reload)
            self.updater.update_trend_charts(
                enable_animation=should_animate,
                force_reload=force_reload
            )
            self.updater.update_daily_stats_table(force_reload=force_reload)

            if show_message:
                animation_status = "с анимацией" if should_animate else "без анимации"
                self._py_logger.debug(f"Обновление статистики завершено {animation_status}")

            self.request_refresh.emit()

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении статистики: {e}")

    # Публичные методы для совместимости
    def update_stats_cards(self):
        """Публичный метод для обновления карточек."""
        if self.updater:
            self.updater.update_stats_cards(force_reload=False)

    def update_trend_charts(self, trend_data=None, allow_animation=False):
        """Публичный метод для обновления графиков."""
        if self.updater:
            self.updater.update_trend_charts(trend_data, enable_animation=allow_animation, force_reload=False)

    def update_daily_stats_table(self, daily_stats=None):
        """Публичный метод для обновления таблицы."""
        if self.updater:
            self.updater.update_daily_stats_table(daily_stats, force_reload=False)

    def showEvent(self, event):
        """Обработчик события показа виджета статистики."""
        super().showEvent(event)
        self._is_currently_visible = True
        self._py_logger.debug("Страница статистики показана")

    def hideEvent(self, event):
        """Обработчик события скрытия виджета."""
        super().hideEvent(event)
        self._is_currently_visible = False
        self._pending_animation = False

        # Очищаем графики при выходе со страницы
        try:
            charts = [
                self.battles_chart_widget,
                self.keys_chart_widget,
                self.silver_chart_widget
            ]

            for chart in charts:
                chart.clear()  # Полная очистка при выходе

            self._py_logger.debug("Графики полностью очищены при скрытии страницы")
        except Exception as e:
            self._py_logger.error(f"Ошибка при очистке графиков: {e}")

        self._py_logger.debug("Страница статистики скрыта")