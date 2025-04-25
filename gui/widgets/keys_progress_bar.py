from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QRect
from PyQt6.QtGui import QFont, QPainter, QColor, QLinearGradient, QPaintEvent, QBrush, QPen

from gui.styles import Styles


class AnimatedProgressBar(QProgressBar):
    """Прогресс-бар с постоянной анимацией заполнения."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(24)

        # Смещение для анимированного градиента
        self.offset = 0

        # Настройка таймера для анимации
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.updateAnimation)
        self.animation_timer.start(60)  # Обновление каждые 60мс

        # Устанавливаем кастомное отображение
        self.setStyleSheet("""
            QProgressBar {
                background-color: transparent;
                border: none;
            }

            QProgressBar::chunk {
                background-color: transparent;
            }
        """)

    def updateAnimation(self):
        """Обновляет состояние анимации."""
        self.offset = (self.offset + 3) % 150  # Скорость движения градиента
        self.update()  # Перерисовываем

    def paintEvent(self, event: QPaintEvent):
        """Переопределенный метод отрисовки для создания эффекта движущегося градиента."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Определяем размеры и позиции
        width = self.width()
        height = self.height()

        # Максимальное значение
        maximum = self.maximum() if self.maximum() > 0 else 1
        # Текущее значение (с учетом ограничений)
        value = min(self.value(), maximum)

        # Размер заполненной части
        filled_width = int((width * value) / maximum)

        # Рисуем фон с одинаковыми параметрами скругления как у заполненной части
        background_color = QColor(Styles.COLORS['background_medium'])
        border_color = QColor(Styles.COLORS['border'])

        # Сначала рисуем фон со скругленными краями
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(background_color))
        painter.drawRoundedRect(0, 0, width, height, height // 2, height // 2)

        # Рисуем рамку со скругленными краями
        border_pen = QPen(border_color)
        border_pen.setWidth(1)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, width, height, height // 2, height // 2)

        # Если есть заполненная часть, рисуем с анимированным градиентом
        if filled_width > 0:
            # Создаем клип-маску для заполненной части, чтобы не выходить за пределы скругленных краев
            painter.setClipRect(0, 0, filled_width, height)

            # Создаем градиент с анимацией
            gradient = QLinearGradient(self.offset, 0, self.offset + 150, 0)

            # Цвета из темы с учетом смещения и повторения
            warning_color = QColor(Styles.COLORS['warning'])
            warning_light = QColor(Styles.COLORS['warning_light'])
            warning_dark = QColor(Styles.COLORS['warning_dark'])

            # Добавляем точки градиента для создания эффекта "волны"
            gradient.setColorAt(0, warning_dark)
            gradient.setColorAt(0.25, warning_color)
            gradient.setColorAt(0.5, warning_light)
            gradient.setColorAt(0.75, warning_color)
            gradient.setColorAt(1, warning_dark)

            # Включаем повторение градиента
            gradient.setSpread(QLinearGradient.Spread.RepeatSpread)

            # Рисуем заполненную часть с градиентом с точно таким же скруглением как у фона
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(0, 0, width, height, height // 2, height // 2)

            # Добавляем эффект блика
            highlight = QLinearGradient(0, 0, 0, height)
            highlight.setColorAt(0, QColor(255, 255, 255, 70))  # Полупрозрачный белый сверху
            highlight.setColorAt(0.5, QColor(255, 255, 255, 10))  # Почти прозрачный в середине
            highlight.setColorAt(1, QColor(0, 0, 0, 5))  # Почти прозрачный внизу

            painter.setBrush(QBrush(highlight))
            painter.drawRoundedRect(0, 0, width, height, height // 2, height // 2)

            # Сбрасываем клип-маску
            painter.setClipping(False)

        painter.end()


class KeysProgressBar(QWidget):
    """Виджет для отображения прогресса сбора ключей."""

    # Сигнал сбрасывания прогресса
    progress_reset = pyqtSignal()

    def __init__(self, target=1000, current=0, parent=None):
        """
        Инициализирует прогресс-бар с целью и текущим значением.

        Args:
            target (int): Целевое количество ключей (по умолчанию 1000)
            current (int): Текущее количество собранных ключей (по умолчанию 0)
            parent (QWidget): Родительский виджет
        """
        super().__init__(parent)

        # Логирование для отладки
        import logging
        self.logger = logging.getLogger("BotLogger")
        self.logger.debug(f"Инициализация KeysProgressBar: target={target}, current={current}")

        # Приведение значений к целым числам для безопасности
        try:
            self.target = int(target)
            if self.target <= 0:
                self.logger.warning(f"Некорректное значение target={target}, установлено 1000")
                self.target = 1000
        except (TypeError, ValueError):
            self.logger.warning(f"Ошибка преобразования target={target} в int, установлено 1000")
            self.target = 1000

        try:
            self.current = int(current)
            if self.current < 0:
                self.logger.warning(f"Отрицательное значение current={current}, установлено 0")
                self.current = 0
        except (TypeError, ValueError):
            self.logger.warning(f"Ошибка преобразования current={current} в int, установлено 0")
            self.current = 0

        # Настройка лейаута
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        # Заголовок и кнопка сброса в одной строке
        header_layout = QHBoxLayout()

        # Заголовок
        self.title_label = QLabel("Прогресс сбора ключей")
        self.title_label.setStyleSheet(f"""
            color: {Styles.COLORS['text_primary']};
            font-weight: bold;
            font-size: 14px;
            background-color: transparent;
        """)
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Кнопка сброса
        self.reset_button = QPushButton("Очистить")
        self.reset_button.setObjectName("danger")
        self.reset_button.setFixedWidth(100)
        self.reset_button.clicked.connect(self.reset_progress)
        header_layout.addWidget(self.reset_button)

        self.layout.addLayout(header_layout)

        # Описание
        self.description_label = QLabel("Количество собранных ключей от цели")
        self.description_label.setStyleSheet(f"""
            color: {Styles.COLORS['text_secondary']};
            background-color: transparent;
        """)
        self.layout.addWidget(self.description_label)

        # Улучшенный прогресс-бар с анимацией
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setRange(0, self.target)
        self.progress_bar.setValue(min(self.current, self.target))  # Защита от перевыполнения
        self.layout.addWidget(self.progress_bar)

        # Анимация для изменения значения прогресс-бара
        self.value_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.value_animation.setDuration(800)  # 800 мс
        self.value_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Статистика в виде текста
        stats_layout = QHBoxLayout()

        # Собрано
        collected_layout = QVBoxLayout()
        collected_title = QLabel("Собрано")
        collected_title.setStyleSheet(f"""
            color: {Styles.COLORS['text_secondary']}; 
            font-size: 12px;
            background-color: transparent;
        """)
        collected_layout.addWidget(collected_title)

        self.collected_value = QLabel(str(self.current))
        self.collected_value.setStyleSheet(f"""
            color: {Styles.COLORS['warning']}; 
            font-weight: bold; 
            font-size: 16px;
            background-color: transparent;
        """)
        collected_layout.addWidget(self.collected_value)

        stats_layout.addLayout(collected_layout)

        # Цель
        target_layout = QVBoxLayout()
        target_title = QLabel("Цель")
        target_title.setStyleSheet(f"""
            color: {Styles.COLORS['text_secondary']}; 
            font-size: 12px;
            background-color: transparent;
        """)
        target_layout.addWidget(target_title)

        self.target_value = QLabel(str(self.target))
        self.target_value.setStyleSheet(f"""
            color: {Styles.COLORS['text_primary']}; 
            font-weight: bold; 
            font-size: 16px;
            background-color: transparent;
        """)
        target_layout.addWidget(self.target_value)

        stats_layout.addLayout(target_layout)

        # Осталось
        remaining_layout = QVBoxLayout()
        remaining_title = QLabel("Осталось")
        remaining_title.setStyleSheet(f"""
            color: {Styles.COLORS['text_secondary']}; 
            font-size: 12px;
            background-color: transparent;
        """)
        remaining_layout.addWidget(remaining_title)

        # Осталось (не меньше нуля)
        remaining = max(0, self.target - self.current)
        self.remaining_value = QLabel(str(remaining))
        self.remaining_value.setStyleSheet(f"""
            color: {Styles.COLORS['primary']}; 
            font-weight: bold; 
            font-size: 16px;
            background-color: transparent;
        """)
        remaining_layout.addWidget(self.remaining_value)

        stats_layout.addLayout(remaining_layout)

        # Процент выполнения
        percent_layout = QVBoxLayout()
        percent_title = QLabel("Прогресс")
        percent_title.setStyleSheet(f"""
            color: {Styles.COLORS['text_secondary']}; 
            font-size: 12px;
            background-color: transparent;
        """)
        percent_layout.addWidget(percent_title)

        # Процент (максимум 100%, если больше - показываем с плюсом)
        percent = self._calculate_percent_display(self.current, self.target)
        self.percent_value = QLabel(percent)
        self.percent_value.setStyleSheet(f"""
            color: {Styles.COLORS['secondary']}; 
            font-weight: bold; 
            font-size: 16px;
            background-color: transparent;
        """)
        percent_layout.addWidget(self.percent_value)

        stats_layout.addLayout(percent_layout)

        self.layout.addLayout(stats_layout)

        # Финальный лог об успешной инициализации
        self.logger.debug(f"KeysProgressBar успешно инициализирован: {self.current}/{self.target} ({percent})")

    def _calculate_percent_display(self, current, target):
        """
        Вычисляет отображаемый процент выполнения.

        Если процент > 100%, показывает "100%+".
        В противном случае показывает точный процент.
        """
        if target <= 0:
            return "0%"

        raw_percent = (current / target) * 100

        if raw_percent > 100:
            return "100%+"
        else:
            return f"{int(raw_percent)}%"

    def update_values(self, current, target=None):
        """Обновляет значения прогресса."""
        # Сохраняем предыдущее значение для логирования при существенных изменениях
        old_current = self.current
        old_value = self.progress_bar.value()

        # Обновляем значения
        self.current = current

        if target is not None:
            self.target = target
            self.progress_bar.setRange(0, self.target)
            self.target_value.setText(str(self.target))

        # Настраиваем и запускаем анимацию для прогресс-бара
        # Ограничиваем значение прогресс-бара целью
        progress_value = min(self.current, self.target)

        self.value_animation.setStartValue(old_value)
        self.value_animation.setEndValue(progress_value)
        self.value_animation.start()

        # Обновляем отображение
        self.collected_value.setText(str(self.current))

        # Вычисляем оставшееся количество (не меньше 0)
        remaining = max(0, self.target - self.current)
        self.remaining_value.setText(str(remaining))

        # Вычисляем процент выполнения с использованием вспомогательного метода
        percent = self._calculate_percent_display(self.current, self.target)
        self.percent_value.setText(percent)

        # Логируем существенные изменения в прогрессе (более 5 ключей)
        if abs(old_current - self.current) > 5:
            import logging
            logger = logging.getLogger("BotLogger")
            logger.debug(f"Обновлен прогресс ключей: {old_current} -> {self.current} ({percent})")

    def reset_progress(self):
        """Сбрасывает прогресс сбора ключей."""
        # Показываем диалог подтверждения
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Сброс прогресса",
            "Вы уверены, что хотите сбросить прогресс сбора ключей?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Сбрасываем прогресс
            self.update_values(0)
            # Отправляем сигнал о сбросе
            self.progress_reset.emit()