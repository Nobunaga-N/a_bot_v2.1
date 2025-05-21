from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QSizePolicy,
    QTabWidget, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from gui.styles import Styles
from gui.components.stat_card import StatCard
from gui.components.styled_table import StyledTable
from gui.widgets.chart_widgets import BattlesChartWidget, KeysChartWidget, SilverChartWidget


class StatsWidget(QWidget):
    """Страница статистики и аналитики."""

    # Сигнал для запроса полного обновления
    request_refresh = pyqtSignal()

    def __init__(self, bot_engine, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine

        # Добавляем логгер для отладки
        import logging
        self._py_logger = logging.getLogger("BotLogger")

        # Инициализация UI
        self.init_ui()

        # Подключаем таймер автоматического обновления
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.auto_refresh_statistics)
        self.update_timer.start(3000)  # Обновление каждые 3 секунды

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

        # Добавляем кнопку обновления статистики
        refresh_button_layout = QHBoxLayout()
        refresh_button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.refresh_stats_button = QPushButton("🔄 Обновить статистику")
        self.refresh_stats_button.setObjectName("primary")
        self.refresh_stats_button.setFixedWidth(200)
        self.refresh_stats_button.setMinimumHeight(30)
        self.refresh_stats_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_stats_button.clicked.connect(self.refresh_statistics)
        refresh_button_layout.addWidget(self.refresh_stats_button)

        # Добавим чекбокс для автообновления
        self.auto_refresh_checkbox = QCheckBox("Автоматическое обновление")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        refresh_button_layout.insertWidget(0, self.auto_refresh_checkbox)
        refresh_button_layout.insertStretch(1)

        overview_layout.addLayout(refresh_button_layout)

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

        # Карточка с серебром
        self.total_silver_card = StatCard(
            "Всего серебра",
            "0K",
            Styles.COLORS["primary"],
            "silver"
        )
        stats_layout.addWidget(self.total_silver_card)

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
        self.silver_chart_widget = SilverChartWidget()

        # Добавляем виджеты графиков в лейаут
        battles_chart_frame = QFrame()
        battles_chart_frame.setObjectName("section_box")
        battles_chart_layout = QVBoxLayout(battles_chart_frame)
        battles_chart_layout.setContentsMargins(0, 0, 0, 0)
        battles_chart_layout.setSpacing(0)
        battles_chart_layout.addWidget(self.battles_chart_widget)
        charts_layout.addWidget(battles_chart_frame)

        silver_chart_frame = QFrame()
        silver_chart_frame.setObjectName("section_box")
        silver_chart_layout = QVBoxLayout(silver_chart_frame)
        silver_chart_layout.setContentsMargins(0, 0, 0, 0)
        silver_chart_layout.setSpacing(0)
        silver_chart_layout.addWidget(self.silver_chart_widget)
        charts_layout.addWidget(silver_chart_frame)

        scroll_layout.addLayout(charts_layout)

        # Добавляем еще один ряд для графика ключей
        keys_chart_layout = QHBoxLayout()
        keys_chart_layout.setSpacing(15)
        keys_chart_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем и добавляем виджет графика ключей
        self.keys_chart_widget = KeysChartWidget()

        keys_chart_frame = QFrame()
        keys_chart_frame.setObjectName("section_box")
        keys_chart_box_layout = QVBoxLayout(keys_chart_frame)
        keys_chart_box_layout.setContentsMargins(0, 0, 0, 0)
        keys_chart_box_layout.setSpacing(0)
        keys_chart_box_layout.addWidget(self.keys_chart_widget)

        keys_chart_layout.addWidget(keys_chart_frame)

        scroll_layout.addLayout(keys_chart_layout)

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

        # Создаем блок с кнопкой и описанием
        top_layout = QHBoxLayout()

        # Описание таблицы
        description_label = QLabel("Показатели за последние 7 дней с детализацией по дням")
        description_label.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        top_layout.addWidget(description_label)

        top_layout.addStretch(1)

        # Кнопка обновления статистики
        self.refresh_daily_stats_button = QPushButton("🔄 Обновить статистику")
        self.refresh_daily_stats_button.setObjectName("primary")
        self.refresh_daily_stats_button.setFixedWidth(200)
        self.refresh_daily_stats_button.setMinimumHeight(30)
        self.refresh_daily_stats_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_daily_stats_button.clicked.connect(self.refresh_statistics)
        top_layout.addWidget(self.refresh_daily_stats_button)

        daily_stats_layout.addLayout(top_layout)

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
        self.daily_stats_table.setColumnCount(9)  # Увеличиваем количество столбцов для серебра
        self.daily_stats_table.setHorizontalHeaderLabels([
            "Дата", "Боёв", "Победы", "Поражения",
            "% побед", "Ключей", "Ключей/победа", "Серебро", "Потерь связи"
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

        silver_legend = QLabel("● Серебро")
        silver_legend.setStyleSheet(f"color: {Styles.COLORS['primary']};")
        legend_layout.addWidget(silver_legend)

        connection_legend = QLabel("● Потери связи")
        connection_legend.setStyleSheet(f"color: {Styles.COLORS['accent']};")
        legend_layout.addWidget(connection_legend)

        legend_layout.addStretch()

        daily_stats_layout.addWidget(legend_frame)

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
        # Проверяем, запущен ли бот
        if not self.bot_engine.running.is_set():
            # Если бот не запущен, неважно обновлять статистику
            return

        # Проверяем, не была ли сессия уже зарегистрирована
        if getattr(self.bot_engine, 'session_stats_registered', False):
            self._py_logger.debug("Сессия уже зарегистрирована, обновляем без добавления данных текущей сессии")

            # Вместо вызова полного обновления с текущей сессией, загружаем только историческую статистику
            try:
                # Принудительно загружаем свежие данные из файла
                self.bot_engine.stats_manager.load_stats()

                # Обновляем элементы интерфейса только историческими данными без учета текущей сессии
                period_index = self.period_combo.currentIndex()
                period_mapping = {0: "day", 1: "week", 2: "month", 3: "all"}
                period = period_mapping.get(period_index, "all")

                # Получаем статистику без учета текущей сессии
                stats_data = self.bot_engine.stats_manager.get_stats_by_period(period)
                trend_data = self.bot_engine.stats_manager.get_trend_data()
                daily_stats = self.bot_engine.stats_manager.get_daily_stats(7)

                # Обновляем интерфейс
                self.update_stats_cards(stats_data)
                self.update_trend_charts(trend_data)
                self.update_daily_stats_table(daily_stats)
            except Exception as e:
                self._py_logger.error(f"Ошибка при обновлении исторической статистики: {e}")

            return

        # Если сессия не зарегистрирована, обновляем с учетом текущей сессии
        self.refresh_statistics(show_message=False, loading_animation=False)

    def update_stats_period(self):
        """Обновляет статистику на основе выбранного периода."""
        try:
            # Получаем текущий выбранный период
            period_index = self.period_combo.currentIndex()
            period_mapping = {
                0: "day",
                1: "week",
                2: "month",
                3: "all"
            }
            period = period_mapping.get(period_index, "all")

            self._py_logger.info(f"Изменение периода статистики на: {period}")

            # Очищаем кэш графиков для принудительного обновления
            if hasattr(self, 'battles_chart_widget'):
                self.battles_chart_widget.clear_cache()
            if hasattr(self, 'keys_chart_widget'):
                self.keys_chart_widget.clear_cache()
            if hasattr(self, 'silver_chart_widget'):
                self.silver_chart_widget.clear_cache()

            # Обновляем все элементы статистики
            self.refresh_statistics(show_message=True)

            self._py_logger.info(f"Статистика обновлена для периода: {period}")
        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении периода статистики: {e}")
            import traceback
            self._py_logger.error(traceback.format_exc())

    def refresh_statistics(self, show_message=True, loading_animation=True):
        """
        Обновляет все отображения статистики с учетом текущей сессии.

        Args:
            show_message (bool): Показывать ли сообщение об успешном обновлении
            loading_animation (bool): Показывать ли анимацию загрузки
        """
        # Проверяем, доступен ли stats_manager
        if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
            self._py_logger.warning("StatsManager недоступен, невозможно обновить статистику")
            return

        try:
            if loading_animation:
                # Отключаем кнопки обновления на время операции
                self.refresh_stats_button.setEnabled(False)
                if hasattr(self, 'refresh_daily_stats_button'):
                    self.refresh_daily_stats_button.setEnabled(False)

                # Добавляем текст "Обновление..." на кнопки
                original_text = self.refresh_stats_button.text()
                self.refresh_stats_button.setText("⏳ Обновление...")
                if hasattr(self, 'refresh_daily_stats_button'):
                    self.refresh_daily_stats_button.setText("⏳ Обновление...")

                # Обновляем интерфейс, чтобы изменения стали видны
                QApplication.processEvents()

            # Логируем начало обновления
            if show_message:
                self._py_logger.info("Обновление статистики запущено...")

            # Принудительно загружаем свежие данные из файла
            self.bot_engine.stats_manager.load_stats()

            # Получаем статистику текущей сессии только если бот запущен и сессия не зарегистрирована
            current_session_stats = None
            if self.bot_engine.running.is_set() and not getattr(self.bot_engine, 'session_stats_registered', False):
                current_session_stats = self.bot_engine.stats
                self._py_logger.debug("Используем статистику текущей сессии для обновления")
            else:
                self._py_logger.debug(
                    "Не используем статистику текущей сессии (бот остановлен или сессия уже зарегистрирована)")

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
            stats_data = self.bot_engine.stats_manager.get_stats_by_period_with_current_session(
                period, current_session_stats
            )

            # Обновляем карточки с основными показателями
            self.update_stats_cards(stats_data)

            # Получаем данные трендов
            trend_data = self.bot_engine.stats_manager.get_trend_data_with_current_session(
                current_session_stats
            )

            # Обновляем графики трендов
            self.update_trend_charts(trend_data)

            # Получаем ежедневную статистику
            daily_stats = self.bot_engine.stats_manager.get_daily_stats_with_current_session(
                7, current_session_stats
            )

            # Обновляем таблицу ежедневной статистики
            self.update_daily_stats_table(daily_stats)

            if show_message:
                self._py_logger.info("Обновление статистики завершено успешно")

            if loading_animation:
                # Восстанавливаем текст и доступность кнопок
                self.refresh_stats_button.setText(original_text)
                self.refresh_stats_button.setEnabled(True)
                if hasattr(self, 'refresh_daily_stats_button'):
                    self.refresh_daily_stats_button.setText(original_text)
                    self.refresh_daily_stats_button.setEnabled(True)

            # Показываем сообщение об успешном обновлении
            if show_message:
                self.show_update_success_message()

            # Отправляем сигнал о завершении обновления
            if hasattr(self, 'request_refresh'):
                self.request_refresh.emit()

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении статистики: {e}")
            import traceback
            self._py_logger.error(traceback.format_exc())

            if loading_animation:
                # Восстанавливаем текст и доступность кнопок в случае ошибки
                self.refresh_stats_button.setText(
                    original_text if 'original_text' in locals() else "🔄 Обновить статистику")
                self.refresh_stats_button.setEnabled(True)
                if hasattr(self, 'refresh_daily_stats_button'):
                    self.refresh_daily_stats_button.setText(
                        original_text if 'original_text' in locals() else "🔄 Обновить статистику")
                    self.refresh_daily_stats_button.setEnabled(True)

    def update_trend_charts(self, trend_data=None):
        """
        Обновляет графики трендов с последними данными.

        Args:
            trend_data: Готовые данные для графиков (если None, будут загружены)
        """
        try:
            # Если данные не переданы, получаем их
            if trend_data is None:
                # Проверяем, доступен ли stats_manager
                if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
                    self._py_logger.warning("StatsManager недоступен, невозможно обновить графики")
                    return

                # Получаем статистику текущей сессии только если бот запущен и сессия не зарегистрирована
                current_session_stats = None
                if self.bot_engine.running.is_set() and not getattr(self.bot_engine, 'session_stats_registered', False):
                    current_session_stats = self.bot_engine.stats

                # Получаем данные трендов
                trend_data = self.bot_engine.stats_manager.get_trend_data_with_current_session(
                    current_session_stats
                )

            # Проверяем, достаточно ли данных для отображения
            if not trend_data or len(trend_data.get("dates", [])) < 1:
                self._py_logger.warning("Недостаточно данных для отображения графиков")
                # Недостаточно данных - очищаем графики
                self.battles_chart_widget.clear()
                self.keys_chart_widget.clear()
                self.silver_chart_widget.clear()
                return

            # Обновляем каждый график отдельно для более надежной работы
            try:
                self.battles_chart_widget.update_chart(trend_data)
            except Exception as e:
                self._py_logger.error(f"Ошибка при обновлении графика боев: {e}")

            try:
                self.keys_chart_widget.update_chart(trend_data)
            except Exception as e:
                self._py_logger.error(f"Ошибка при обновлении графика ключей: {e}")

            try:
                self.silver_chart_widget.update_chart(trend_data)
            except Exception as e:
                self._py_logger.error(f"Ошибка при обновлении графика серебра: {e}")

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении графиков: {e}")
            import traceback
            self._py_logger.error(traceback.format_exc())

    def update_stats_cards(self, stats_data=None):
        """Обновляет карточки с основными показателями."""
        if stats_data is None:
            # Если данные не переданы, пытаемся получить их
            if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
                self._py_logger.warning("StatsManager недоступен, невозможно обновить карточки статистики")
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

            # Получаем статистику с учетом текущей сессии
            stats_data = self.bot_engine.stats_manager.get_stats_by_period_with_current_session(
                period, self.bot_engine.stats
            )

        # Проверяем наличие всех нужных данных
        if "stats" not in stats_data:
            self._py_logger.error("В данных статистики отсутствует ключ 'stats'")
            return

        # Безопасно получаем данные из статистики
        victories = stats_data["stats"].get("victories", 0)
        defeats = stats_data["stats"].get("defeats", 0)
        keys_collected = stats_data["stats"].get("keys_collected", 0)

        # Обновляем карточки с основными показателями
        total_battles = victories + defeats
        self.total_battles_card.set_value(str(total_battles))

        win_rate = stats_data.get("win_rate", 0)
        self.win_rate_card.set_value(f"{win_rate:.1f}%")

        self.total_keys_card.set_value(str(keys_collected))

        # Форматируем значение серебра с надежной обработкой
        try:
            # Безопасное получение данных о серебре
            silver_collected = stats_data["stats"].get("silver_collected", 0)

            # Форматирование значения
            silver_formatted = Styles.format_silver(silver_collected)

            # Обновляем карточку
            self.total_silver_card.set_value(silver_formatted)

        except Exception as e:
            self._py_logger.error(f"Ошибка при форматировании серебра: {e}")
            # Устанавливаем безопасное значение по умолчанию
            self.total_silver_card.set_value("0K")

    def update_daily_stats_table(self, daily_stats=None):
        """
        Обновляет таблицу ежедневной статистики.

        Args:
            daily_stats: Готовые данные ежедневной статистики (если None, будут загружены)
        """
        try:
            # Если данные не переданы, получаем их
            if daily_stats is None:
                # Проверяем, доступен ли stats_manager
                if not hasattr(self.bot_engine, 'stats_manager') or self.bot_engine.stats_manager is None:
                    self._py_logger.warning("StatsManager недоступен, невозможно обновить таблицу статистики")
                    return

                # Получаем ежедневную статистику, включая текущую сессию
                daily_stats = self.bot_engine.stats_manager.get_daily_stats_with_current_session(
                    7, self.bot_engine.stats
                )

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

                # Собрано серебра - с безопасной обработкой
                try:
                    silver_collected = day["stats"].get("silver_collected", 0)
                    silver_formatted = Styles.format_silver(silver_collected)
                    self.daily_stats_table.setItem(row, 7, QTableWidgetItem(silver_formatted))
                except Exception as e:
                    self._py_logger.error(f"Ошибка при форматировании серебра для таблицы: {e}")
                    self.daily_stats_table.setItem(row, 7, QTableWidgetItem("0K"))

                # Потери связи
                self.daily_stats_table.setItem(row, 8, QTableWidgetItem(str(day["stats"]["connection_losses"])))

            # Настройка цветовой индикации
            self.daily_stats_table.customize_cell_colors()

        except Exception as e:
            self._py_logger.error(f"Ошибка при обновлении таблицы ежедневной статистики: {e}")
            import traceback
            self._py_logger.error(traceback.format_exc())

    def show_update_success_message(self):
        """Показывает временное сообщение об успешном обновлении."""
        try:
            from PyQt6.QtWidgets import QLabel
            from PyQt6.QtCore import QTimer, Qt

            # Создаем временную метку
            success_label = QLabel("✓ Данные успешно обновлены", self)
            success_label.setStyleSheet(f"""
                background-color: {Styles.COLORS['secondary']};
                color: {Styles.COLORS['background_dark']};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            """)
            success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            success_label.adjustSize()  # Подгоняем размер под текст

            # Позиционируем метку в верхнем правом углу
            success_label.move(self.width() - success_label.width() - 20, 20)
            success_label.show()

            # Удаляем метку через 3 секунды
            QTimer.singleShot(3000, success_label.deleteLater)
        except Exception as e:
            self._py_logger.error(f"Ошибка при показе сообщения об успешном обновлении: {e}")

    def showEvent(self, event):
        """Обработчик события показа виджета."""
        super().showEvent(event)
        # При показе виджета запускаем таймер автообновления
        if hasattr(self, 'update_timer') and self.auto_refresh_checkbox.isChecked():
            self.update_timer.start(3000)

    def hideEvent(self, event):
        """Обработчик события скрытия виджета."""
        super().hideEvent(event)
        # При скрытии виджета останавливаем таймер для экономии ресурсов
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()


from PyQt6.QtWidgets import QCheckBox  # Нужен импорт для чекбокса