from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from gui.styles import Styles


class KeysProgressBar(QWidget):
    """Виджет для отображения прогресса сбора ключей."""

    # Сигнал сбрасывания прогресса
    progress_reset = pyqtSignal()

    def __init__(self, target=1000, current=0, parent=None):
        super().__init__(parent)

        self.target = target
        self.current = current

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
        self.description_label.setStyleSheet(f"color: {Styles.COLORS['text_secondary']};")
        self.layout.addWidget(self.description_label)

        # Прогресс-бар с улучшенным стилем
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.target)
        self.progress_bar.setValue(min(self.current, self.target))  # Защита от перевыполнения
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Styles.COLORS['background_medium']};
                border-radius: 10px;
                text-align: center;
            }}

            QProgressBar::chunk {{
                background-color: {Styles.COLORS['warning']};
                border-radius: 10px;
            }}
        """)
        self.layout.addWidget(self.progress_bar)

        # Статистика в виде текста
        stats_layout = QHBoxLayout()

        # Собрано
        collected_layout = QVBoxLayout()
        collected_title = QLabel("Собрано")
        collected_title.setStyleSheet(f"color: {Styles.COLORS['text_secondary']}; font-size: 12px;")
        collected_layout.addWidget(collected_title)

        self.collected_value = QLabel(str(self.current))
        self.collected_value.setStyleSheet(f"color: {Styles.COLORS['warning']}; font-weight: bold; font-size: 16px;")
        collected_layout.addWidget(self.collected_value)

        stats_layout.addLayout(collected_layout)

        # Цель
        target_layout = QVBoxLayout()
        target_title = QLabel("Цель")
        target_title.setStyleSheet(f"color: {Styles.COLORS['text_secondary']}; font-size: 12px;")
        target_layout.addWidget(target_title)

        self.target_value = QLabel(str(self.target))
        self.target_value.setStyleSheet(f"color: {Styles.COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        target_layout.addWidget(self.target_value)

        stats_layout.addLayout(target_layout)

        # Осталось
        remaining_layout = QVBoxLayout()
        remaining_title = QLabel("Осталось")
        remaining_title.setStyleSheet(f"color: {Styles.COLORS['text_secondary']}; font-size: 12px;")
        remaining_layout.addWidget(remaining_title)

        # Осталось (не меньше нуля)
        remaining = max(0, self.target - self.current)
        self.remaining_value = QLabel(str(remaining))
        self.remaining_value.setStyleSheet(f"color: {Styles.COLORS['primary']}; font-weight: bold; font-size: 16px;")
        remaining_layout.addWidget(self.remaining_value)

        stats_layout.addLayout(remaining_layout)

        # Процент выполнения
        percent_layout = QVBoxLayout()
        percent_title = QLabel("Прогресс")
        percent_title.setStyleSheet(f"color: {Styles.COLORS['text_secondary']}; font-size: 12px;")
        percent_layout.addWidget(percent_title)

        # Процент (не более 999%)
        percent = min(int((self.current / self.target) * 100) if self.target > 0 else 0, 999)
        self.percent_value = QLabel(f"{percent}%")
        self.percent_value.setStyleSheet(f"color: {Styles.COLORS['secondary']}; font-weight: bold; font-size: 16px;")
        percent_layout.addWidget(self.percent_value)

        stats_layout.addLayout(percent_layout)

        self.layout.addLayout(stats_layout)

    def update_values(self, current, target=None):
        """Обновляет значения прогресса."""
        self.current = current

        if target is not None:
            self.target = target
            self.progress_bar.setRange(0, self.target)
            self.target_value.setText(str(self.target))

        # Обновляем отображение
        self.progress_bar.setValue(min(self.current, self.target))  # Ограничиваем значение прогресс-бара целью
        self.collected_value.setText(str(self.current))

        # Вычисляем оставшееся количество (не меньше 0)
        remaining = max(0, self.target - self.current)
        self.remaining_value.setText(str(remaining))

        # Вычисляем процент выполнения (ограничиваем 999%)
        percent = min(int((self.current / self.target) * 100) if self.target > 0 else 0, 999)
        self.percent_value.setText(f"{percent}%")

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